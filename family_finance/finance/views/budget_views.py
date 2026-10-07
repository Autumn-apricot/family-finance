from rest_framework.response import Response
from rest_framework.views import APIView

from finance.models import Budget, User
from finance.response import created, ok
from finance.serializers.common_serializers import BudgetSerializer
from finance.utils import get_request_user


class BudgetListCreateView(APIView):
    def get(self, request):
        user = get_request_user(request)
        qs = Budget.objects.select_related('category')
        if user.role != User.ROLE_ADMIN:
            qs = qs.filter(user=user)
        else:
            uid = request.query_params.get('user_id')
            if uid:
                qs = qs.filter(user_id=uid)
        month = request.query_params.get('month')
        if month:
            qs = qs.filter(month=month)
        return ok(BudgetSerializer(qs, many=True).data)

    def post(self, request):
        user = get_request_user(request)
        ser = BudgetSerializer(data=request.data)
        if not ser.is_valid():
            return Response({'code': 40001, 'message': str(ser.errors), 'data': None}, status=400)
        try:
            row = ser.save(user=user)
        except Exception:
            return Response({'code': 40901, 'message': '同月同分类预算已存在', 'data': None}, status=409)
        return created(BudgetSerializer(row).data)


class BudgetDetailView(APIView):
    def get(self, request, pk):
        row = Budget.objects.select_related('category').get(pk=pk)
        user = get_request_user(request)
        if user.role != User.ROLE_ADMIN and row.user_id != user.id:
            return Response({'code': 40301, 'message': '无权限', 'data': None}, status=403)
        return ok(BudgetSerializer(row).data)

    def patch(self, request, pk):
        row = Budget.objects.get(pk=pk)
        user = get_request_user(request)
        if user.role != User.ROLE_ADMIN and row.user_id != user.id:
            return Response({'code': 40301, 'message': '无权限', 'data': None}, status=403)
        ser = BudgetSerializer(row, data=request.data, partial=True)
        if not ser.is_valid():
            return Response({'code': 40001, 'message': str(ser.errors), 'data': None}, status=400)
        ser.save()
        return ok(ser.data)

    def delete(self, request, pk):
        row = Budget.objects.get(pk=pk)
        user = get_request_user(request)
        if user.role != User.ROLE_ADMIN and row.user_id != user.id:
            return Response({'code': 40301, 'message': '无权限', 'data': None}, status=403)
        row.delete()
        return ok(None, '已删除')
