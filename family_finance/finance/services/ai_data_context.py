"""
为 AI 对话注入本地账本数据上下文（RAG 式：先查库，再交给大模型组织语言）。
"""
from __future__ import annotations

import re
from datetime import date, timedelta
from typing import Optional

from finance.models import Category, Expense, User
from finance.services.stats_service import StatsService

# 中文月份
_CN_MONTH = {
    '十一': 11, '十二': 12,
    '一': 1, '二': 2, '三': 3, '四': 4, '五': 5, '六': 6,
    '七': 7, '八': 8, '九': 9, '十': 10,
}


def _parse_months_from_question(question: str, today: date) -> list[str]:
    """从用户问题中解析关心的 YYYY-MM 列表。"""
    q = question.strip()
    found: list[str] = []
    year = today.year

    for m in re.finditer(r'(\d{4})\s*年\s*(\d{1,2})\s*月', q):
        found.append(f'{int(m.group(1)):04d}-{int(m.group(2)):02d}')

    for m in re.finditer(r'(\d{1,2})\s*月份?', q):
        mo = int(m.group(1))
        if 1 <= mo <= 12:
            found.append(f'{year}-{mo:02d}')

    for cn, mo in _CN_MONTH.items():
        if cn + '月' in q or cn + '月份' in q:
            found.append(f'{year}-{mo:02d}')

    if re.search(r'本月|这个月|当月', q):
        found.append(today.strftime('%Y-%m'))
    if re.search(r'上月|上个月', q):
        first = today.replace(day=1)
        prev = first - timedelta(days=1)
        found.append(prev.strftime('%Y-%m'))
    if re.search(r'今天|今日', q):
        found.append('__daily__')
    if re.search(r'本周|这周', q):
        found.append('__weekly__')
    if re.search(r'今年', q) or re.search(rf'{year}\s*年', q):
        found.append('__annual__')

    # 去重保序
    seen = set()
    out = []
    for x in found:
        if x not in seen:
            seen.add(x)
            out.append(x)
    return out


def _fmt_categories(by_category: list, limit: int = 8) -> str:
    if not by_category:
        return '（无分类明细）'
    parts = []
    for row in by_category[:limit]:
        pct = row.get('percent', 0)
        parts.append(f"{row['name']}{row['amount']}元({pct}%)")
    return '、'.join(parts)


def _fmt_members(by_member: list) -> str:
    if not by_member:
        return '（无成员明细）'
    parts = []
    for row in by_member:
        if float(row.get('expense', 0) or 0) > 0 or float(row.get('income', 0) or 0) > 0:
            parts.append(f"{row['nickname']}支出{row['expense']}元/收入{row['income']}元")
    return '、'.join(parts) if parts else '（各成员暂无记录）'


class AiDataContextBuilder:
    def __init__(self, stats: Optional[StatsService] = None):
        self.stats = stats or StatsService()

    def build(self, user: User, question: str) -> tuple[str, dict]:
        """
        返回 (给大模型的文本上下文, 结构化数据供本地直答/降级)。
        user_id=None 表示家庭全员汇总（与统计页默认一致）。
        """
        today = date.today()
        user_id = None  # 家庭账本汇总
        data: dict = {
            'user_nickname': user.nickname or user.username,
            'today': today.isoformat(),
            'summary': self.stats.summary(user_id),
            'months': {},
            'personal_month': None,
        }

        lines = [
            '【以下为系统从本地数据库查询的真实账本，回答金额、占比、排行时必须只使用这些数据，禁止编造数字】',
            f'当前登录成员：{data["user_nickname"]}（回答可用「您家」「家庭」指全员账本）',
            f'统计截至日期：{today.isoformat()}',
        ]

        s = data['summary']
        lines.append(
            f'今日：支出{s["today_expense"]}元，收入{s["today_income"]}元'
        )
        lines.append(
            f'本月({s.get("budget_month", today.strftime("%Y-%m"))})：'
            f'支出{s["month_expense"]}元，收入{s["month_income"]}元，结余{s["month_balance"]}元；'
            f'预算{s["budget_total"]}元，已用{s["budget_used_percent"]}%'
        )

        # 近 6 个月趋势（便于回答「哪个月花得多」）
        trend_parts = []
        y, m = today.year, today.month
        for _ in range(6):
            ms = f'{y}-{m:02d}'
            monthly = self.stats.monthly(ms, user_id)
            data['months'][ms] = monthly
            trend_parts.append(f'{ms}支出{monthly["total_expense"]}元')
            m -= 1
            if m < 1:
                m = 12
                y -= 1
        lines.append('近6个月家庭支出：' + '；'.join(reversed(trend_parts)))

        # 当前成员个人本月（若有个人记账）
        pm = self.stats.monthly(today.strftime('%Y-%m'), user.id)
        data['personal_month'] = pm
        if float(pm.get('total_expense', 0) or 0) > 0:
            lines.append(
                f'您个人本月({pm["month"]})：支出{pm["total_expense"]}元，'
                f'收入{pm["total_income"]}元；分类：{_fmt_categories(pm.get("by_category", []))}'
            )

        # 根据问题补充明细
        hints = _parse_months_from_question(question, today)
        if not hints and _needs_finance_data(question):
            hints = [today.strftime('%Y-%m')]

        for hint in hints:
            if hint == '__daily__':
                daily = self.stats.daily(today, user_id)
                data['daily'] = daily
                lines.append(
                    f'今日明细：总支出{daily["total_expense"]}元；'
                    f'分类：{_fmt_categories(daily.get("by_category", []))}'
                )
            elif hint == '__weekly__':
                monday = today - timedelta(days=today.weekday())
                weekly = self.stats.weekly(monday, user_id)
                data['weekly'] = weekly
                lines.append(
                    f'本周({weekly["week_start"]}~{weekly["week_end"]})：'
                    f'支出{weekly["total_expense"]}元，收入{weekly["total_income"]}元'
                )
            elif hint == '__annual__':
                annual = self.stats.annual(today.year, user_id)
                data['annual'] = annual
                lines.append(
                    f'{today.year}年全年：支出{annual["total_expense"]}元，'
                    f'收入{annual["total_income"]}元'
                )
            elif re.match(r'^\d{4}-\d{2}$', hint):
                if hint not in data['months']:
                    data['months'][hint] = self.stats.monthly(hint, user_id)
                monthly = data['months'][hint]
                lines.append(
                    f'{hint}月家庭账本：总支出{monthly["total_expense"]}元，'
                    f'总收入{monthly["total_income"]}元，结余{monthly["balance"]}元；'
                    f'分类：{_fmt_categories(monthly.get("by_category", []))}；'
                    f'成员：{_fmt_members(monthly.get("by_member", []))}'
                )

        # 最近 5 笔支出（回答「最近买了什么」）
        if re.search(r'最近|近期|上一笔|刚', question):
            recent = (
                Expense.objects.filter(category__type=Category.TYPE_EXPENSE)
                .select_related('category', 'user')
                .order_by('-expense_date', '-id')[:5]
            )
            recent_lines = []
            for e in recent:
                who = e.user.nickname or e.user.username
                recent_lines.append(
                    f'{e.expense_date} {who} {e.category.name} {e.amount}元'
                    + (f'（{e.description}）' if e.description else '')
                )
            data['recent_expenses'] = recent_lines
            if recent_lines:
                lines.append('最近5笔支出：' + '；'.join(recent_lines))

        text = '\n'.join(lines)
        return text, data


def _needs_finance_data(question: str) -> bool:
    """是否像在问账本/金额/统计。"""
    q = question
    keys = (
        '多少钱', '花了', '支出', '收入', '结余', '预算', '账单', '记账',
        '分类', '统计', '月份', '本月', '上月', '本周', '今天', '今年',
        '餐饮', '交通', '购物', '用了', '消费',
    )
    return any(k in q for k in keys)


def try_direct_answer(question: str, data: dict) -> Optional[str]:
    """
    无大模型或 LLM 失败时，用本地数据直接回答明确的金额类问题。
    """
    if not _needs_finance_data(question):
        return None

    today = date.today()
    months_hint = _parse_months_from_question(question, today)
    s = data.get('summary') or {}

    # 本月花了多少
    if re.search(r'本月|这个月|当月', question) and re.search(
        r'多少|多少钱|花了|支出', question
    ):
        return (
            f'根据本地账本，您家本月（{s.get("budget_month", "")}）总支出 {s.get("month_expense", "0.00")} 元，'
            f'收入 {s.get("month_income", "0.00")} 元，结余 {s.get("month_balance", "0.00")} 元。'
        )

    # 今天
    if re.search(r'今天|今日', question) and re.search(r'多少|多少钱|花了|支出', question):
        return (
            f'根据本地账本，今日总支出 {s.get("today_expense", "0.00")} 元，'
            f'收入 {s.get("today_income", "0.00")} 元。'
        )

    # 指定月份
    for ms in months_hint:
        if not re.match(r'^\d{4}-\d{2}$', ms):
            continue
        monthly = (data.get('months') or {}).get(ms)
        if not monthly:
            continue
        if re.search(r'多少|多少钱|花了|支出|用了', question):
            y, m = ms.split('-')
            cat_txt = _fmt_categories(monthly.get('by_category', []))
            return (
                f'根据本地账本，{y}年{int(m)}月您家总支出 {monthly["total_expense"]} 元，'
                f'收入 {monthly["total_income"]} 元，结余 {monthly["balance"]} 元。'
                f'主要支出分类：{cat_txt}。'
            )

    # 未指定月份但问「花了多少」
    if re.search(r'多少|多少钱|花了|支出', question) and data.get('months'):
        ms = today.strftime('%Y-%m')
        monthly = data['months'].get(ms)
        if monthly:
            return (
                f'根据本地账本，本月总支出 {monthly["total_expense"]} 元。'
                f'（若您问的是其他月份，请说明如「5月份」）'
            )

    return None
