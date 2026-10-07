import random
import string

from rest_framework.response import Response
from rest_framework.views import APIView

from finance.models import Family, User
from finance.response import created, ok
from finance.utils import get_request_user


def _gen_code():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))


class FamilyView(APIView):
    def get(self, request):
        """查看我的家庭信息"""
        user = get_request_user(request)
        if not user.family:
            return ok({'has_family': False})
        members = User.objects.filter(family=user.family, is_active=True).values('id', 'nickname', 'username', 'role')
        return ok({
            'has_family': True,
            'family': {'id': user.family.id, 'name': user.family.name, 'invite_code': user.family.invite_code},
            'members': list(members),
        })

    def post(self, request):
        """创建家庭"""
        user = get_request_user(request)
        if user.family:
            return Response({'code': 40001, 'message': '已有所属家庭，请先退出'}, status=400)
        name = request.data.get('name', '').strip()
        if not name:
            return Response({'code': 40001, 'message': '请输入家庭名'}, status=400)
        code = _gen_code()
        while Family.objects.filter(invite_code=code).exists():
            code = _gen_code()
        fam = Family.objects.create(name=name, invite_code=code, created_by=user)
        user.family = fam
        user.save()
        return created({'id': fam.id, 'name': fam.name, 'invite_code': fam.invite_code})


class FamilyJoinView(APIView):
    def post(self, request):
        """加入家庭"""
        user = get_request_user(request)
        if user.family:
            return Response({'code': 40001, 'message': '已有所属家庭，请先退出'}, status=400)
        code = request.data.get('code', '').strip().upper()
        try:
            fam = Family.objects.get(invite_code=code)
        except Family.DoesNotExist:
            return Response({'code': 40401, 'message': '邀请码无效'}, status=400)
        user.family = fam
        user.save()
        return ok({'id': fam.id, 'name': fam.name})


class FamilyLeaveView(APIView):
    def post(self, request):
        """退出家庭"""
        user = get_request_user(request)
        if not user.family:
            return Response({'code': 40001, 'message': '未加入家庭'}, status=400)
        user.family = None
        user.save()
        return ok(None, '已退出家庭')
