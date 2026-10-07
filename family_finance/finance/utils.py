"""通用工具 — 解析当前请求的 finance.User"""

from finance.models import User


def get_request_user(request):
    u = request.user
    if isinstance(u, User):
        return u
    if hasattr(u, 'finance_user'):
        return u.finance_user
    if getattr(u, 'is_authenticated', False) and getattr(u, 'pk', None):
        try:
            return User.objects.get(pk=u.pk)
        except User.DoesNotExist:
            pass
    user_id = getattr(request, 'finance_user_id', None)
    if user_id:
        return User.objects.get(pk=user_id)
    raise PermissionError('未登录或无法识别用户')


def get_family_user_ids(user):
    """家庭用户返回成员列表；管理员返回全部；普通用户返回自己"""
    if user.role == User.ROLE_ADMIN:
        return list(User.objects.filter(is_active=True).values_list('id', flat=True))
    if user.family:
        return list(User.objects.filter(family=user.family, is_active=True).values_list('id', flat=True))
    return [user.id]
