"""统计聚合服务 — docs/08 §7"""
from calendar import monthrange
from datetime import date, timedelta
from decimal import Decimal

from django.db.models import Sum
from django.db.models.functions import TruncMonth

from finance.models import Budget, Category, Expense, User


def _dec(val) -> str:
    return f'{Decimal(val or 0):.2f}'


def _pct(part, total) -> float:
    if not total:
        return 0.0
    return round(float(part) / float(total) * 100, 1)


class StatsService:
    def _base_qs(self, user_id_or_ids=None):
        qs = Expense.objects.select_related('category', 'user')
        if user_id_or_ids:
            if isinstance(user_id_or_ids, list):
                qs = qs.filter(user_id__in=user_id_or_ids)
            else:
                qs = qs.filter(user_id=user_id_or_ids)
        return qs

    def summary(self, user_id_or_ids=None) -> dict:
        today = date.today()
        month_str = today.strftime('%Y-%m')
        qs = self._base_qs(user_id_or_ids)

        today_exp = qs.filter(expense_date=today, category__type=Category.TYPE_EXPENSE).aggregate(
            s=Sum('amount')
        )['s']
        today_inc = qs.filter(expense_date=today, category__type=Category.TYPE_INCOME).aggregate(
            s=Sum('amount')
        )['s']

        month_start = today.replace(day=1)
        month_qs = qs.filter(expense_date__gte=month_start, expense_date__lte=today)
        month_exp = month_qs.filter(category__type=Category.TYPE_EXPENSE).aggregate(s=Sum('amount'))['s']
        month_inc = month_qs.filter(category__type=Category.TYPE_INCOME).aggregate(s=Sum('amount'))['s']

        budget_qs = Budget.objects.filter(month=month_str)
        uid = user_id_or_ids
        if uid:
            if isinstance(uid, list):
                budget_qs = budget_qs.filter(user_id__in=uid)
            else:
                budget_qs = budget_qs.filter(user_id=uid)
        budget_total = budget_qs.aggregate(s=Sum('amount'))['s'] or 0
        # 只统计有预算的分类的支出
        budget_cat_ids = list(budget_qs.values_list('category_id', flat=True))
        if budget_cat_ids:
            budgeted_exp = month_qs.filter(category_id__in=budget_cat_ids).aggregate(s=Sum('amount'))['s'] or 0
        else:
            budgeted_exp = 0
        used_pct = _pct(budgeted_exp or 0, budget_total) if budget_total else 0.0

        return {
            'today_expense': _dec(today_exp),
            'today_income': _dec(today_inc),
            'month_expense': _dec(month_exp),
            'month_income': _dec(month_inc),
            'month_balance': _dec((month_inc or 0) - (month_exp or 0)),
            'budget_month': month_str,
            'budget_total': _dec(budget_total),
            'budget_used_percent': used_pct,
        }

    def daily(self, target_date: date, user_id=None) -> dict:
        qs = self._base_qs(user_id).filter(expense_date=target_date, category__type=Category.TYPE_EXPENSE)
        total = qs.aggregate(s=Sum('amount'))['s'] or 0
        by_cat = []
        for row in qs.values('category_id', 'category__name', 'category__icon').annotate(
            amount=Sum('amount')
        ).order_by('-amount'):
            by_cat.append({
                'category_id': row['category_id'],
                'name': row['category__name'],
                'icon': row['category__icon'],
                'amount': _dec(row['amount']),
                'percent': _pct(row['amount'], total),
            })
        inc_qs = self._base_qs(user_id).filter(expense_date=target_date, category__type=Category.TYPE_INCOME)
        inc = inc_qs.aggregate(s=Sum('amount'))['s']
        by_inc_cat = []
        for row in inc_qs.values('category_id', 'category__name', 'category__icon').annotate(
            amount=Sum('amount')
        ).order_by('-amount'):
            by_inc_cat.append({
                'category_id': row['category_id'],
                'name': row['category__name'],
                'icon': row['category__icon'],
                'amount': _dec(row['amount']),
                'percent': _pct(row['amount'], inc),
            })
        return {
            'date': target_date.isoformat(),
            'total_expense': _dec(total),
            'total_income': _dec(inc),
            'by_category': by_cat,
            'by_income_category': by_inc_cat,
        }

    def weekly(self, week_start: date, user_id=None) -> dict:
        week_end = week_start + timedelta(days=6)
        qs = self._base_qs(user_id).filter(expense_date__gte=week_start, expense_date__lte=week_end)
        exp_total = qs.filter(category__type=Category.TYPE_EXPENSE).aggregate(s=Sum('amount'))['s']
        inc_total = qs.filter(category__type=Category.TYPE_INCOME).aggregate(s=Sum('amount'))['s']

        daily_trend = []
        for i in range(7):
            d = week_start + timedelta(days=i)
            day_qs = qs.filter(expense_date=d)
            daily_trend.append({
                'date': d.isoformat(),
                'expense': _dec(
                    day_qs.filter(category__type=Category.TYPE_EXPENSE).aggregate(s=Sum('amount'))['s']
                ),
                'income': _dec(
                    day_qs.filter(category__type=Category.TYPE_INCOME).aggregate(s=Sum('amount'))['s']
                ),
            })

        ranking = []
        exp_qs = qs.filter(category__type=Category.TYPE_EXPENSE)
        for row in exp_qs.values('category_id', 'category__name').annotate(amount=Sum('amount')).order_by(
            '-amount'
        )[:10]:
            ranking.append({
                'category_id': row['category_id'],
                'name': row['category__name'],
                'amount': _dec(row['amount']),
                'percent': _pct(row['amount'], exp_total),
            })

        return {
            'week_start': week_start.isoformat(),
            'week_end': week_end.isoformat(),
            'total_expense': _dec(exp_total),
            'total_income': _dec(inc_total),
            'daily_trend': daily_trend,
            'ranking': ranking,
        }

    def monthly(self, month: str, user_id=None) -> dict:
        y, m = map(int, month.split('-'))
        start = date(y, m, 1)
        end = date(y, m, monthrange(y, m)[1])
        qs = self._base_qs(user_id).filter(expense_date__gte=start, expense_date__lte=end)
        exp = qs.filter(category__type=Category.TYPE_EXPENSE).aggregate(s=Sum('amount'))['s']
        inc = qs.filter(category__type=Category.TYPE_INCOME).aggregate(s=Sum('amount'))['s']

        by_member = []
        for u in User.objects.filter(is_active=True):
            uqs = qs.filter(user=u)
            by_member.append({
                'user_id': u.id,
                'nickname': u.nickname or u.username,
                'expense': _dec(
                    uqs.filter(category__type=Category.TYPE_EXPENSE).aggregate(s=Sum('amount'))['s']
                ),
                'income': _dec(
                    uqs.filter(category__type=Category.TYPE_INCOME).aggregate(s=Sum('amount'))['s']
                ),
            })

        by_category = []
        for row in qs.filter(category__type=Category.TYPE_EXPENSE).values(
            'category_id', 'category__name'
        ).annotate(amount=Sum('amount')).order_by('-amount'):
            by_category.append({
                'category_id': row['category_id'],
                'name': row['category__name'],
                'amount': _dec(row['amount']),
                'percent': _pct(row['amount'], exp),
            })

        # 收入分类占比
        by_income_category = []
        for row in qs.filter(category__type=Category.TYPE_INCOME).values(
            'category_id', 'category__name'
        ).annotate(amount=Sum('amount')).order_by('-amount'):
            by_income_category.append({
                'category_id': row['category_id'],
                'name': row['category__name'],
                'amount': _dec(row['amount']),
                'percent': _pct(row['amount'], inc),
            })

        return {
            'month': month,
            'total_expense': _dec(exp),
            'total_income': _dec(inc),
            'balance': _dec((inc or 0) - (exp or 0)),
            'by_member': by_member,
            'by_category': by_category,
            'by_income_category': by_income_category,
        }

    def annual(self, year: int, user_id=None) -> dict:
        start = date(year, 1, 1)
        end = date(year, 12, 31)
        qs = self._base_qs(user_id).filter(expense_date__gte=start, expense_date__lte=end)
        exp = qs.filter(category__type=Category.TYPE_EXPENSE).aggregate(s=Sum('amount'))['s']
        inc = qs.filter(category__type=Category.TYPE_INCOME).aggregate(s=Sum('amount'))['s']

        monthly_trend = []
        for m in range(1, 13):
            ms = f'{year}-{m:02d}'
            y, mo = year, m
            d1 = date(y, mo, 1)
            d2 = date(y, mo, monthrange(y, mo)[1])
            mqs = qs.filter(expense_date__gte=d1, expense_date__lte=d2)
            monthly_trend.append({
                'month': ms,
                'expense': _dec(
                    mqs.filter(category__type=Category.TYPE_EXPENSE).aggregate(s=Sum('amount'))['s']
                ),
                'income': _dec(
                    mqs.filter(category__type=Category.TYPE_INCOME).aggregate(s=Sum('amount'))['s']
                ),
            })

        top_categories = []
        for row in qs.filter(category__type=Category.TYPE_EXPENSE).values(
            'category_id', 'category__name'
        ).annotate(amount=Sum('amount')).order_by('-amount')[:5]:
            top_categories.append({
                'category_id': row['category_id'],
                'name': row['category__name'],
                'amount': _dec(row['amount']),
                'percent': _pct(row['amount'], exp),
            })

        return {
            'year': year,
            'total_expense': _dec(exp),
            'total_income': _dec(inc),
            'monthly_trend': monthly_trend,
            'top_categories': top_categories,
        }
