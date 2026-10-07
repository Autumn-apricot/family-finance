from calendar import monthrange
from datetime import date, timedelta

from rest_framework.response import Response
from rest_framework.views import APIView

from finance.models import Category, Expense, RecurringBill
from finance.response import created, ok
from finance.serializers.common_serializers import ExpenseCreateSerializer
from finance.utils import get_request_user


def _next_date(current: date, cycle: str) -> date:
    """计算下一个周期日期（日历月/年，避免30天漂移）"""
    if cycle == 'daily':
        return current + timedelta(days=1)
    elif cycle == 'weekly':
        return current + timedelta(days=7)
    elif cycle == 'monthly':
        yr, mo = current.year, current.month
        mo += 1
        if mo > 12:
            mo = 1
            yr += 1
        day = min(current.day, monthrange(yr, mo)[1])
        return date(yr, mo, day)
    elif cycle == 'yearly':
        yr = current.year + 1
        return date(yr, current.month, min(current.day, monthrange(yr, current.month)[1]))
    return current + timedelta(days=30)


def _to_dict(r):
    nd = r.next_date
    if hasattr(nd, 'isoformat'):
        nd = nd.isoformat()
    else:
        nd = str(nd)
    return {
        'id': r.id, 'category': r.category_id, 'category_name': r.category.name,
        'category_icon': r.category.icon, 'amount': float(r.amount),
        'description': r.description, 'payment_method': r.payment_method,
        'cycle': r.cycle, 'next_date': nd,
        'is_active': r.is_active,
    }


class RecurringListView(APIView):
    def get(self, request):
        user = get_request_user(request)
        qs = RecurringBill.objects.select_related('category').filter(user=user).order_by('next_date')
        return ok([_to_dict(r) for r in qs])

    def post(self, request):
        user = get_request_user(request)
        data = request.data
        try:
            r = RecurringBill.objects.create(
                user=user, category_id=int(data['category']), amount=data['amount'],
                description=data.get('description', ''), payment_method=data.get('payment_method', 'wechat'),
                cycle=data.get('cycle', 'monthly'), next_date=data['next_date'],
            )
            return created(_to_dict(r))
        except Exception as e:
            return Response({'code': 40001, 'message': str(e), 'data': None}, status=400)


class RecurringDetailView(APIView):
    def patch(self, request, pk):
        r = RecurringBill.objects.get(pk=pk, user=get_request_user(request))
        for f in ['amount', 'description', 'payment_method', 'cycle', 'next_date', 'is_active']:
            if f in request.data:
                setattr(r, f, request.data[f])
        if 'category' in request.data:
            r.category_id = request.data['category']
        r.save()
        return ok(_to_dict(r))

    def delete(self, request, pk):
        r = RecurringBill.objects.get(pk=pk, user=get_request_user(request))
        r.delete()
        return ok(None, '已删除')


class RecurringGenerateView(APIView):
    def post(self, request):
        user = get_request_user(request)
        today = date.today()
        qs = RecurringBill.objects.select_related('category').filter(
            user=user, is_active=True, next_date__lte=today,
        )
        generated = 0
        for r in qs:
            cat_type = r.category.type
            ser = ExpenseCreateSerializer(data={
                'category': r.category_id, 'amount': r.amount,
                'description': r.description or f'周期账单',
                'expense_date': today.isoformat(), 'payment_method': r.payment_method,
                'source': 'manual',
            })
            if ser.is_valid():
                ser.save(user=user)
                r.next_date = _next_date(today, r.cycle)
                r.save(update_fields=['next_date'])
                generated += 1
        return ok({'generated': generated})
