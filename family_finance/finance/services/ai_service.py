"""AI 理财助手 — docs/08 §9；对话前注入本地账本数据。"""
from datetime import date, timedelta

from django.db.models import Sum

from finance.exceptions import ExternalServiceException
from finance.models import AiChatHistory, Category, Expense
from finance.services.ai_data_context import (
    AiDataContextBuilder,
    try_direct_answer,
)
from finance.services.llm_client import get_llm_client


class AiService:
    def __init__(self):
        self._ctx_builder = AiDataContextBuilder()

    def _llm(self):
        return get_llm_client()

    def _llm_ready(self, client) -> bool:
        return bool(client.api_key) and not str(client.api_key).startswith('your-')

    def _system_prompt(self, data_context: str) -> str:
        return (
            '你是家庭理财助手，结合中国家庭消费习惯回答。'
            '用户问金额、月份支出、分类占比、成员消费时，必须严格依据【真实账本数据】中的数字作答，'
            '不得编造未出现在数据中的金额。若数据中没有对应月份或项目，请明确说账本中暂无记录。'
            '非账本类问题（如天气、新闻）可礼貌说明你的专长是家庭理财，并引导用户问账本相关问题。'
            '回答简洁，重要数字用元为单位。\n\n'
            + data_context
        )

    def _chat_with_llm(self, client, system: str, question: str) -> tuple[str, int]:
        return client.chat_completion(
            messages=[
                {'role': 'system', 'content': system},
                {'role': 'user', 'content': question},
            ]
        )

    def chat(self, user, question: str) -> dict:
        data_context, structured = self._ctx_builder.build(user, question)
        client = self._llm()
        answer = None
        tokens = 0

        if self._llm_ready(client):
            try:
                answer, tokens = self._chat_with_llm(
                    client, self._system_prompt(data_context), question
                )
            except ExternalServiceException:
                answer = try_direct_answer(question, structured)

        if answer is None:
            answer = try_direct_answer(question, structured)

        if answer is None:
            answer = (
                f'【演示模式·已读取本地账本】关于「{question}」：'
                f'本月家庭支出 {structured["summary"]["month_expense"]} 元。'
                '配置可用的 LLM_API_KEY 后可获得更自然的对话回复；'
                '问具体月份时请说明，如「5月份用了多少钱」。'
            )
            tokens = 0

        row = AiChatHistory.objects.create(
            user=user,
            chat_type='chat',
            question=question,
            answer=answer,
            tokens_used=tokens,
        )
        return {'id': row.id, 'answer': answer, 'tokens_used': tokens}

    def advice(self, user) -> dict:
        since = date.today() - timedelta(days=30)
        qs = Expense.objects.filter(
            expense_date__gte=since,
            category__type=Category.TYPE_EXPENSE,
        )
        by_cat = list(
            qs.values('category__name').annotate(total=Sum('amount')).order_by('-total')[:5]
        )
        summary = ', '.join(
            f"{r['category__name']}{r['total']}元" for r in by_cat
        ) or '暂无近30天支出数据'

        data_context, structured = self._ctx_builder.build(user, '近30天支出与理财建议')
        prompt = (
            f'用户近30天主要支出：{summary}。'
            f'本月家庭支出{structured["summary"]["month_expense"]}元。'
            '请给出3条可执行的家庭理财建议。'
        )
        client = self._llm()
        if self._llm_ready(client):
            try:
                answer, tokens = self._chat_with_llm(
                    client,
                    self._system_prompt(data_context),
                    prompt,
                )
            except ExternalServiceException:
                answer = (
                    '【演示模式】1. 对餐饮、购物设置月度上限；'
                    '2. 大额支出先家庭讨论；3. 每周日查看统计页复盘。'
                )
                tokens = 0
        else:
            answer = (
                '【演示模式】1. 对餐饮、购物设置月度上限；'
                '2. 大额支出先家庭讨论；3. 每周日查看统计页复盘。'
                f'（本月已记录支出 {structured["summary"]["month_expense"]} 元）'
            )
            tokens = 0

        row = AiChatHistory.objects.create(
            user=user,
            chat_type='advice',
            question='消费建议',
            answer=answer,
            tokens_used=tokens,
        )
        return {'id': row.id, 'advice': answer, 'based_on_days': 30}

    def history(self, user, page=1, page_size=20):
        qs = AiChatHistory.objects.filter(user=user).order_by('-created_at')
        start = (page - 1) * page_size
        items = qs[start : start + page_size]
        return [
            {
                'id': r.id,
                'chat_type': r.chat_type,
                'question': r.question,
                'answer': r.answer,
                'created_at': r.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            }
            for r in items
        ]
