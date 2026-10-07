"""统一业务异常（与 docs/03 详细设计 第 7 章一致）"""


class FinanceException(Exception):
    def __init__(self, code: int, message: str, data=None):
        self.code = code
        self.message = message
        self.data = data
        super().__init__(message)


class ValidationException(FinanceException):
    def __init__(self, message: str = '参数错误', data=None):
        super().__init__(40001, message, data)


class VoiceParseException(FinanceException):
    """部分解析成功（如无金额）仍返回 data"""

    def __init__(self, message: str, data=None):
        super().__init__(40002, message, data)


class ExternalServiceException(FinanceException):
    def __init__(self, message: str = '外部服务不可用', data=None):
        super().__init__(50301, message, data)


def code_to_http_status(code: int) -> int:
    if code == 40101:
        return 401
    if code == 40301:
        return 403
    if 40001 <= code <= 40002:
        return 200 if code == 40002 else 400
    if code == 40401:
        return 404
    if code == 42901:
        return 429
    if code == 50301:
        return 503
    return 500


def custom_exception_handler(exc, context):
    """注册到 REST_FRAMEWORK['EXCEPTION_HANDLER']"""
    from rest_framework.views import exception_handler
    from rest_framework.response import Response
    from rest_framework.exceptions import ValidationError

    if isinstance(exc, FinanceException):
        status = code_to_http_status(exc.code)
        return Response(
            {'code': exc.code, 'message': exc.message, 'data': exc.data},
            status=status,
        )

    if isinstance(exc, ValidationError):
        return Response(
            {'code': 40001, 'message': str(exc.detail), 'data': None},
            status=400,
        )

    response = exception_handler(exc, context)
    if response is not None:
        return response
    return Response(
        {'code': 50001, 'message': '服务器内部错误', 'data': None},
        status=500,
    )
