from datetime import date

from django.db.models import Count, Sum
from django.utils import timezone

from rest_framework.response import Response
from rest_framework.views import APIView

from finance.models import Category, Expense, SystemConfig, User, VoiceParseLog
from finance.permissions import IsAdminUser
from finance.response import ok
from finance.services.stats_service import StatsService


class AdminDashboardView(APIView):
    permission_classes = [IsAdminUser]

    def get(self, request):
        today = timezone.now().date()
        month_str = today.strftime('%Y-%m')
        month_start = today.replace(day=1)
        month_qs = Expense.objects.filter(expense_date__gte=month_start, expense_date__lte=today)
        month_expense = month_qs.filter(category__type=Category.TYPE_EXPENSE).aggregate(s=Sum('amount'))['s']
        month_count = month_qs.count()
        voice_expense = month_qs.filter(source=Expense.SOURCE_VOICE).count()
        voice_ratio = round(voice_expense / month_count * 100, 1) if month_count else 0
        summary = StatsService().summary()
        monthly = StatsService().monthly(month_str)
        return ok({
            'user_count': User.objects.filter(is_active=True).count(),
            'expense_count': Expense.objects.count(),
            'today_expense_count': Expense.objects.filter(expense_date=today).count(),
            'voice_parse_count': VoiceParseLog.objects.count(),
            'month_expense': summary.get('month_expense', '0.00'),
            'month_expense_count': month_count,
            'voice_ratio_percent': voice_ratio,
            'by_category': monthly.get('by_category', []),
            'by_member': monthly.get('by_member', []),
        })


class AdminVoiceStatsView(APIView):
    """兼容 docs/08 voice-usage 与 docs/03 voice-stats"""

    permission_classes = [IsAdminUser]

    def get(self, request):
        total = VoiceParseLog.objects.count()
        confirmed = VoiceParseLog.objects.filter(is_confirmed=True).count()
        by_method = list(
            VoiceParseLog.objects.values('match_method')
            .annotate(count=Count('id'))
            .order_by('-count')
        )
        return ok({
            'total_parses': total,
            'confirmed_count': confirmed,
            'confirm_rate': round(confirmed / total * 100, 1) if total else 0,
            'by_match_method': by_method,
        })


class AdminConfigView(APIView):
    permission_classes = [IsAdminUser]

    def get(self, request):
        items = {}
        for row in SystemConfig.objects.all():
            val = '******' if row.is_secret and row.config_value else row.config_value
            items[row.config_key] = {
                'value': val,
                'value_type': row.value_type,
                'description': row.description,
                'is_secret': row.is_secret,
            }
        return ok(items)

    def put(self, request):
        data = request.data or {}
        for key, val in data.items():
            if isinstance(val, dict):
                value = val.get('value', '')
                is_secret = val.get('is_secret', False)
            else:
                value = str(val)
                is_secret = False
            SystemConfig.objects.update_or_create(
                config_key=key,
                defaults={'config_value': value, 'is_secret': is_secret},
            )
        return ok(None, '配置已更新')
