"""
语音文本解析服务 — 规则 + 关键词 + DeepSeek 兜底
对应 docs/09_语音智能记账模块设计说明书
"""
from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from datetime import date, timedelta
from decimal import Decimal, InvalidOperation
from typing import TYPE_CHECKING, Any, Optional

from django.conf import settings
from finance.exceptions import ExternalServiceException, ValidationException, VoiceParseException
from finance.models_voice import CategoryKeyword, VoiceParseLog
from finance.services.asr_adapter import AsrAdapter, get_asr_adapter
from finance.services.llm_client import LlmClient, get_llm_client

if TYPE_CHECKING:
    from finance.models import Category, User

logger = logging.getLogger(__name__)

# ---------- 内置关键词（DB 无数据时降级） ----------
_BUILTIN_KEYWORDS: dict[str, list[tuple[str, int]]] = {
    '餐饮': [('吃饭', 8), ('聚餐', 8), ('下馆子', 8), ('饭店', 8), ('请客', 6)],
    '交通': [('出行', 8), ('通勤', 6), ('交通工具', 6)],
    '购物': [('买了', 8), ('购物', 8), ('买衣服', 8), ('淘宝', 6), ('京东', 6), ('拼多多', 6)],
    '娱乐': [('KTV', 8), ('门票', 8)],
    '住房': [('装修', 6)],
    '医疗': [('挂号', 8)],
    '教育': [('书本', 6), ('课程', 6)],
    '工资': [('发工资', 12)],
    '奖金': [],
}

_INCOME_KEYWORDS = {'工资', '收入', '收到', '到账', '奖金', '薪水', '发工资'}
_EXPENSE_KEYWORDS = {'花了', '支出', '付款', '消费', '买了', '付了', '充值'}

_AMOUNT_PATTERNS = [
    re.compile(r'(\d+(?:\.\d{1,2})?)\s*(?:元|块|块钱|圆)'),
    re.compile(r'花了\s*(\d+(?:\.\d{1,2})?)'),
    re.compile(r'(\d+(?:\.\d{1,2})?)\s*$'),
    re.compile(r'([一二三四五六七八九十百千万两零壹贰叁肆伍陆柒捌玖拾佰仟]+)\s*(?:元|块)'),
]

_CN_NUM = {
    '零': 0, '一': 1, '二': 2, '两': 2, '三': 3, '四': 4, '五': 5,
    '六': 6, '七': 7, '八': 8, '九': 9, '十': 10, '百': 100, '千': 1000, '万': 10000,
}


@dataclass
class CategoryMatch:
    category_id: int
    category_name: str
    category_icon: str
    score: float
    match_method: str


@dataclass
class ParseResult:
    log_id: int
    parsed_type: str
    category_id: int
    category_name: str
    category_icon: str
    amount: Optional[Decimal]
    expense_date: date
    description: str
    confidence: float
    match_method: str
    raw_text: str
    alternatives: list[dict] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            'log_id': self.log_id,
            'type': self.parsed_type,
            'category_id': self.category_id,
            'category_name': self.category_name,
            'category_icon': self.category_icon,
            'amount': float(self.amount) if self.amount is not None else None,
            'expense_date': self.expense_date.isoformat(),
            'description': self.description,
            'confidence': round(self.confidence, 2),
            'match_method': self.match_method,
            'alternatives': self.alternatives,
            'raw_text': self.raw_text,
        }


class VoiceService:
    def __init__(
        self,
        llm_client: LlmClient | None = None,
        asr_adapter: AsrAdapter | None = None,
    ):
        self.llm = llm_client or get_llm_client()
        self.asr = asr_adapter or get_asr_adapter()

    # ------------------------------------------------------------------ public

    def parse_text(
        self,
        text: str,
        user: 'User',
        reference_date: date | None = None,
    ) -> ParseResult:
        """清洗 → 金额/日期/收支 → 关键词 → 可选 LLM → 写日志"""
        ref = reference_date or date.today()
        raw = (text or '').strip()
        if not raw:
            raise ValidationException('语音文本不能为空')
        if len(raw) > 500:
            raise ValidationException('文本长度不能超过 500 字')

        normalized = self._normalize_text(raw)
        amount = self._extract_amount(normalized)
        expense_date = self._extract_date(normalized, ref)
        parsed_type = self._extract_type(normalized)

        match, alternatives = self._match_category(normalized, parsed_type)
        description = self._build_description(normalized, match.category_name)

        confidence = min(1.0, match.score / 30.0) if match.score else 0.3
        match_method = match.match_method

        threshold = float(getattr(settings, 'VOICE_CONFIDENCE_THRESHOLD', 0.6))
        use_llm = getattr(settings, 'VOICE_LLM_FALLBACK', True)

        if confidence < threshold and use_llm:
            llm_data = self._llm_structured_parse(normalized, ref, parsed_type)
            if llm_data:
                merged = self._merge_llm_result(
                    llm_data, parsed_type, amount, expense_date, description, match
                )
                parsed_type = merged['parsed_type']
                amount = merged.get('amount', amount)
                expense_date = merged.get('expense_date', expense_date)
                description = merged.get('description', description)
                match = merged['match']
                alternatives = merged.get('alternatives', alternatives)
                confidence = merged['confidence']
                match_method = VoiceParseLog.MATCH_LLM

        if amount is None:
            # 无金额：仍写日志，抛业务异常供视图返回 40002
            result = self._save_log(
                user=user,
                raw_text=raw,
                parsed_type=parsed_type,
                category_id=match.category_id,
                amount=None,
                expense_date=expense_date,
                description=description,
                confidence=confidence,
                match_method=match_method,
                alternatives=alternatives,
            )
            raise VoiceParseException(
                '未识别到金额，请补充',
                data=result.to_dict(),
            )

        result = self._save_log(
            user=user,
            raw_text=raw,
            parsed_type=parsed_type,
            category_id=match.category_id,
            amount=amount,
            expense_date=expense_date,
            description=description,
            confidence=confidence,
            match_method=match_method,
            alternatives=alternatives,
        )
        return result

    def transcribe_and_parse(
        self,
        audio_bytes: bytes,
        fmt: str,
        user: 'User',
        lang: str = 'zh-CN',
        reference_date: date | None = None,
    ) -> tuple[str, ParseResult]:
        """ASR → parse_text"""
        text = self.asr.transcribe(audio_bytes, fmt=fmt, lang=lang)
        return text, self.parse_text(text, user, reference_date)

    def confirm_log(self, log_id: int, expense_id: int, user: 'User') -> None:
        """确认入账后更新日志"""
        updated = VoiceParseLog.objects.filter(
            pk=log_id, user_id=user.id,
        ).update(is_confirmed=True, expense_id=expense_id)
        if not updated:
            raise ValidationException('语音日志不存在或无权访问')

    # ------------------------------------------------------------------ pipeline

    def _normalize_text(self, text: str) -> str:
        text = text.replace('，', ',').replace('。', '.').replace('　', ' ')
        text = re.sub(r'\s+', '', text)
        return text

    def _extract_amount(self, text: str) -> Optional[Decimal]:
        for pat in _AMOUNT_PATTERNS:
            m = pat.search(text)
            if not m:
                continue
            raw_val = m.group(1)
            if re.match(r'^[\d.]+$', raw_val):
                try:
                    return Decimal(raw_val).quantize(Decimal('0.01'))
                except InvalidOperation:
                    continue
            cn_val = self._chinese_to_number(raw_val)
            if cn_val is not None:
                return Decimal(str(cn_val)).quantize(Decimal('0.01'))
        return None

    def _chinese_to_number(self, s: str) -> Optional[int]:
        """简易中文数字：三十五、两千"""
        if not s:
            return None
        if s.isdigit():
            return int(s)
        total = 0
        current = 0
        for ch in s:
            if ch not in _CN_NUM:
                return None
            n = _CN_NUM[ch]
            if n == 10000:
                total = (total + current) * 10000
                current = 0
            elif n == 1000:
                current = (current or 1) * 1000
            elif n == 100:
                current = (current or 1) * 100
            elif n == 10:
                current = (current or 1) * 10
            else:
                current += n
        return total + current

    def _extract_date(self, text: str, ref: date) -> date:
        if any(k in text for k in ('今天', '今早', '今晚', '今早', '刚才')):
            return ref
        if '昨天' in text:
            return ref - timedelta(days=1)
        if '前天' in text:
            return ref - timedelta(days=2)
        m = re.search(r'(\d{1,2})月(\d{1,2})日', text)
        if m:
            month, day = int(m.group(1)), int(m.group(2))
            try:
                return date(ref.year, month, day)
            except ValueError:
                pass
        m = re.search(r'(\d{2})-(\d{2})', text)
        if m:
            month, day = int(m.group(1)), int(m.group(2))
            try:
                return date(ref.year, month, day)
            except ValueError:
                pass
        return ref

    def _extract_type(self, text: str) -> str:
        if any(k in text for k in _INCOME_KEYWORDS):
            return 'income'
        if any(k in text for k in _EXPENSE_KEYWORDS):
            return 'expense'
        return 'expense'

    def _match_category(
        self,
        text: str,
        parsed_type: str,
    ) -> tuple[CategoryMatch, list[dict]]:
        from finance.models import Category

        categories = list(
            Category.objects.filter(type=parsed_type).order_by('sort_order', 'id')
        )
        if not categories:
            categories = list(Category.objects.filter(type='expense').order_by('sort_order', 'id'))

        name_to_cat = {c.name: c for c in categories}
        scores: dict[int, float] = {}
        method_flags: dict[int, str] = {}

        # DB 关键词
        kw_qs = CategoryKeyword.objects.select_related('category').filter(
            category__type=parsed_type,
        )
        for kw in kw_qs:
            if kw.keyword in text:
                scores[kw.category_id] = scores.get(kw.category_id, 0) + kw.weight
                method_flags[kw.category_id] = VoiceParseLog.MATCH_KEYWORD

        # 内置关键词
        for cat_name, kws in _BUILTIN_KEYWORDS.items():
            cat = name_to_cat.get(cat_name)
            if not cat or cat.type != parsed_type:
                continue
            for word, weight in kws:
                if word in text:
                    scores[cat.id] = scores.get(cat.id, 0) + weight
                    method_flags.setdefault(cat.id, VoiceParseLog.MATCH_KEYWORD)

        # 排序取 top
        ranked = sorted(scores.items(), key=lambda x: (-x[1], x[0]))
        alternatives = []
        for cid, sc in ranked[1:4]:
            cat = next((c for c in categories if c.id == cid), None)
            if cat:
                alternatives.append({
                    'category_id': cat.id,
                    'category_name': cat.name,
                    'score': round(min(1.0, sc / 30.0), 2),
                })

        if ranked:
            top_id, top_score = ranked[0]
            cat = next(c for c in categories if c.id == top_id)
            return (
                CategoryMatch(
                    category_id=cat.id,
                    category_name=cat.name,
                    category_icon=cat.icon,
                    score=top_score,
                    match_method=method_flags.get(top_id, VoiceParseLog.MATCH_KEYWORD),
                ),
                alternatives,
            )

        # 兜底
        default_name = '其他收入' if parsed_type == 'income' else '其他支出'
        fallback = name_to_cat.get(default_name) or categories[-1]
        return (
            CategoryMatch(
                category_id=fallback.id,
                category_name=fallback.name,
                category_icon=fallback.icon,
                score=3.0,
                match_method='rule',
            ),
            alternatives,
        )

    def _build_description(self, text: str, category_name: str) -> str:
        desc = text[:200]
        return desc or category_name

    def _llm_structured_parse(
        self,
        text: str,
        ref: date,
        parsed_type: str,
    ) -> Optional[dict]:
        expense_cats = '餐饮、交通、购物、娱乐、住房、医疗、教育、其他支出'
        income_cats = '工资、奖金、其他收入'
        cat_hint = income_cats if parsed_type == 'income' else expense_cats

        prompt = f"""你是记账助手。根据用户口述，从下列分类中选择最合适的一项，并提取金额和日期。
分类列表（支出）：{expense_cats}
分类列表（收入）：{income_cats}
今天日期：{ref.isoformat()}

用户说：「{text}」

请仅返回 JSON，不要其他文字：
{{
  "type": "expense|income",
  "category_name": "",
  "amount": 0.00,
  "expense_date": "YYYY-MM-DD",
  "description": ""
}}"""

        messages = [
            {'role': 'system', 'content': '你只输出合法 JSON，用于家庭记账字段抽取。'},
            {'role': 'user', 'content': prompt},
        ]

        try:
            content, _ = self.llm.chat_completion(messages, temperature=0.1, max_tokens=256)
            return self.llm.parse_json_from_content(content)
        except ExternalServiceException:
            logger.warning('LLM fallback failed for voice parse')
            return None

    def _merge_llm_result(
        self,
        llm_data: dict,
        parsed_type: str,
        amount: Optional[Decimal],
        expense_date: date,
        description: str,
        fallback_match: CategoryMatch,
    ) -> dict:
        from finance.models import Category

        llm_type = llm_data.get('type', parsed_type)
        if llm_type not in ('expense', 'income'):
            llm_type = parsed_type

        cat_name = (llm_data.get('category_name') or '').strip()
        cat = Category.objects.filter(name=cat_name, type=llm_type).first()
        if not cat:
            default_name = '其他收入' if llm_type == 'income' else '其他支出'
            cat = Category.objects.filter(name=default_name, type=llm_type).first()
        if not cat:
            cat = Category.objects.filter(pk=fallback_match.category_id).first()

        llm_amount = llm_data.get('amount')
        if amount is None and llm_amount is not None:
            try:
                amount = Decimal(str(llm_amount)).quantize(Decimal('0.01'))
            except (InvalidOperation, TypeError):
                pass

        llm_date = llm_data.get('expense_date')
        if llm_date:
            try:
                expense_date = date.fromisoformat(str(llm_date)[:10])
            except ValueError:
                pass

        desc = (llm_data.get('description') or description)[:200]

        match = CategoryMatch(
            category_id=cat.id,
            category_name=cat.name,
            category_icon=cat.icon,
            score=24.0,
            match_method=VoiceParseLog.MATCH_LLM,
        )
        return {
            'parsed_type': llm_type,
            'amount': amount,
            'expense_date': expense_date,
            'description': desc,
            'match': match,
            'confidence': 0.75,
            'alternatives': [],
        }

    def _save_log(
        self,
        user: 'User',
        raw_text: str,
        parsed_type: str,
        category_id: int,
        amount: Optional[Decimal],
        expense_date: date,
        description: str,
        confidence: float,
        match_method: str,
        alternatives: list[dict],
    ) -> ParseResult:
        from finance.models import Category

        cat = Category.objects.get(pk=category_id)
        payload = {
            'type': parsed_type,
            'category_id': category_id,
            'category_name': cat.name,
            'amount': float(amount) if amount is not None else None,
            'expense_date': expense_date.isoformat(),
            'description': description,
            'confidence': round(confidence, 2),
            'match_method': match_method,
            'alternatives': alternatives,
            'raw_text': raw_text,
        }

        log = VoiceParseLog.objects.create(
            user=user,
            raw_text=raw_text,
            parsed_type=parsed_type,
            category_id=category_id,
            amount=amount,
            expense_date=expense_date,
            description=description,
            confidence=confidence,
            match_method=match_method or VoiceParseLog.MATCH_KEYWORD,
            parsed_json=payload,
        )

        return ParseResult(
            log_id=log.id,
            parsed_type=parsed_type,
            category_id=category_id,
            category_name=cat.name,
            category_icon=cat.icon,
            amount=amount,
            expense_date=expense_date,
            description=description,
            confidence=confidence,
            match_method=match_method,
            raw_text=raw_text,
            alternatives=alternatives,
        )
