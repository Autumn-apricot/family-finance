from rest_framework.response import Response
from rest_framework.views import APIView

from finance.models import User
from finance.permissions import IsAdminUser
from finance.response import ok
from finance.serializers.user_serializers import MeUpdateSerializer, UserSerializer, UserUpdateSerializer
from finance.utils import get_request_user


class MeView(APIView):
    def get(self, request):
        user = get_request_user(request)
        return ok(UserSerializer(user).data)

    def patch(self, request):
        user = get_request_user(request)
        ser = MeUpdateSerializer(user, data=request.data, partial=True)
        if not ser.is_valid():
            return Response({'code': 40001, 'message': str(ser.errors), 'data': None}, status=400)
        ser.save()
        return ok(UserSerializer(user).data)


class UserListView(APIView):
    permission_classes = [IsAdminUser]

    def get(self, request):
        qs = User.objects.all().order_by('-created_at')
        page = int(request.query_params.get('page', 1))
        size = min(int(request.query_params.get('page_size', 20)), 100)
        start = (page - 1) * size
        items = qs[start : start + size]
        return ok({
            'count': qs.count(),
            'next': None,
            'previous': None,
            'results': UserSerializer(items, many=True).data,
        })


class UserDetailView(APIView):
    def get(self, request, pk):
        user = get_request_user(request)
        if user.role != User.ROLE_ADMIN and user.id != int(pk):
            return Response({'code': 40301, 'message': '无权限', 'data': None}, status=403)
        target = User.objects.get(pk=pk)
        return ok(UserSerializer(target).data)

    def patch(self, request, pk):
        user = get_request_user(request)
        target = User.objects.get(pk=pk)
        if user.role != User.ROLE_ADMIN and user.id != target.id:
            return Response({'code': 40301, 'message': '无权限', 'data': None}, status=403)
        ser = UserUpdateSerializer(target, data=request.data, partial=True)
        if not ser.is_valid():
            return Response({'code': 40001, 'message': str(ser.errors), 'data': None}, status=400)
        if user.role != User.ROLE_ADMIN:
            for f in ('role', 'is_active'):
                ser.validated_data.pop(f, None)
        ser.save()
        return ok(UserSerializer(target).data)

    def delete(self, request, pk):
        user = get_request_user(request)
        if user.role != User.ROLE_ADMIN:
            return Response({'code': 40301, 'message': '无权限', 'data': None}, status=403)
        target = User.objects.get(pk=pk)
        target.is_active = False
        target.save(update_fields=['is_active', 'updated_at'])
        return ok(None, '已禁用')
