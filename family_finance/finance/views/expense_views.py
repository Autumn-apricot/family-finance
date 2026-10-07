from datetime import datetime

from rest_framework.response import Response
from rest_framework.views import APIView

from finance.models import Expense, User
from finance.permissions import IsAdminUser
from finance.response import created, ok
from finance.serializers.common_serializers import ExpenseCreateSerializer, ExpenseSerializer
from finance.utils import get_family_user_ids, get_request_user


class ExpenseListCreateView(APIView):
    def get(self, request):
        user = get_request_user(request)
        family_ids = get_family_user_ids(user)
        qs = Expense.objects.select_related('category', 'user').filter(user_id__in=family_ids)

        uid = request.query_params.get('user_id')
        if uid:
            qs = qs.filter(user_id=uid)
        cat = request.query_params.get('category_id')
        if cat:
            qs = qs.filter(category_id=cat)
        cat_type = request.query_params.get('type')
        if cat_type:
            qs = qs.filter(category__type=cat_type)
        month = request.query_params.get('month')
        if month:
            y, m = map(int, month.split('-'))
            qs = qs.filter(expense_date__year=y, expense_date__month=m)
        d_from = request.query_params.get('date_from')
        d_to = request.query_params.get('date_to')
        if d_from:
            qs = qs.filter(expense_date__gte=d_from)
        if d_to:
            qs = qs.filter(expense_date__lte=d_to)
        source = request.query_params.get('source')
        if source:
            qs = qs.filter(source=source)
        payment = request.query_params.get('payment_method')
        if payment:
            qs = qs.filter(payment_method=payment)
        search = request.query_params.get('search')
        if search:
            qs = qs.filter(description__icontains=search)

        page = int(request.query_params.get('page', 1))
        size = min(int(request.query_params.get('page_size', 20)), 100)
        start = (page - 1) * size
        total = qs.count()
        items = qs.order_by('-expense_date', '-id')[start : start + size]
        return ok({
            'count': total,
            'next': f'?page={page + 1}' if start + size < total else None,
            'previous': f'?page={page - 1}' if page > 1 else None,
            'results': ExpenseSerializer(items, many=True).data,
        })

    def post(self, request):
        user = get_request_user(request)
        ser = ExpenseCreateSerializer(data=request.data)
        if not ser.is_valid():
            return Response({'code': 40001, 'message': str(ser.errors), 'data': None}, status=400)
        source = request.data.get('source', Expense.SOURCE_MANUAL)
        if source not in dict(Expense.SOURCE_CHOICES):
            source = Expense.SOURCE_MANUAL
        exp = ser.save(user=user, source=source)
        return created(ExpenseSerializer(exp).data)


class ExpenseDetailView(APIView):
    def _check_owner(self, request, exp):
        user = get_request_user(request)
        if user.role != User.ROLE_ADMIN and exp.user_id != user.id:
            return Response({'code': 40301, 'message': '无权限', 'data': None}, status=403)
        return None

    def get(self, request, pk):
        exp = Expense.objects.select_related('category', 'user').get(pk=pk)
        denied = self._check_owner(request, exp)
        if denied:
            return denied
        return ok(ExpenseSerializer(exp).data)

    def patch(self, request, pk):
        exp = Expense.objects.get(pk=pk)
        denied = self._check_owner(request, exp)
        if denied:
            return denied
        ser = ExpenseCreateSerializer(exp, data=request.data, partial=True)
        if not ser.is_valid():
            return Response({'code': 40001, 'message': str(ser.errors), 'data': None}, status=400)
        ser.save()
        return ok(ExpenseSerializer(exp).data)

    def delete(self, request, pk):
        exp = Expense.objects.get(pk=pk)
        denied = self._check_owner(request, exp)
        if denied:
            return denied
        exp.delete()
        return ok(None, '已删除')


class ExpenseBulkDeleteView(APIView):
    permission_classes = [IsAdminUser]

    def post(self, request):
        ids = request.data.get('ids', [])
        Expense.objects.filter(id__in=ids).delete()
        return ok({'deleted': len(ids)})
