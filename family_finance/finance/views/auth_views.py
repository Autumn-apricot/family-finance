from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken

from finance.models import User
from finance.response import created, ok
from finance.serializers.user_serializers import LoginSerializer, RegisterSerializer, UserSerializer


def _tokens_for_user(user: User) -> dict:
    refresh = RefreshToken()
    refresh['user_id'] = user.id
    access = refresh.access_token
    access['user_id'] = user.id
    return {
        'access': str(access),
        'refresh': str(refresh),
        'user': UserSerializer(user).data,
    }


def _bad_request(message):
    return Response({'code': 40001, 'message': message, 'data': None}, status=400)


class RegisterView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        ser = RegisterSerializer(data=request.data)
        if not ser.is_valid():
            return _bad_request(str(ser.errors))
        user = ser.save()
        return created(_tokens_for_user(user))


class LoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        ser = LoginSerializer(data=request.data)
        if not ser.is_valid():
            return _bad_request(str(ser.errors))
        try:
            user = User.objects.get(username=ser.validated_data['username'], is_active=True)
        except User.DoesNotExist:
            return Response(
                {'code': 40101, 'message': '用户名或密码错误', 'data': None}, status=401
            )
        if not user.check_password(ser.validated_data['password']):
            return Response(
                {'code': 40101, 'message': '用户名或密码错误', 'data': None}, status=401
            )
        return ok(_tokens_for_user(user))


class RefreshView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        refresh_str = request.data.get('refresh')
        if not refresh_str:
            return _bad_request('缺少 refresh')
        try:
            refresh = RefreshToken(refresh_str)
            return ok({'access': str(refresh.access_token)})
        except TokenError:
            return Response(
                {'code': 40101, 'message': 'refresh 无效', 'data': None}, status=401
            )


class LogoutView(APIView):
    def post(self, request):
        return ok(None, '已登出')
