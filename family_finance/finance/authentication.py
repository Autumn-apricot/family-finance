from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken

from finance.models import User


class JWTUserAuthentication(JWTAuthentication):
    """将 JWT user_id 映射到自定义 User 模型。"""

    def get_user(self, validated_token):
        try:
            user_id = validated_token['user_id']
        except KeyError as exc:
            raise InvalidToken('Token contained no recognizable user identification') from exc
        try:
            return User.objects.get(pk=user_id, is_active=True)
        except User.DoesNotExist as exc:
            raise InvalidToken('User not found') from exc
