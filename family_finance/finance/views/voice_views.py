"""
语音模块 API — POST /voice/parse/、/voice/transcribe/、/voice/logs/{id}/confirm/
"""
from datetime import date

from django.conf import settings
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from finance.exceptions import (
    ExternalServiceException,
    FinanceException,
    ValidationException,
    VoiceParseException,
)
from finance.serializers.voice_serializers import VoiceConfirmSerializer, VoiceParseSerializer
from finance.services.voice_service import VoiceService
from finance.utils import get_request_user


def _ok(data, message='ok'):
    return Response({'code': 0, 'message': message, 'data': data})


def _handle_finance_exc(exc: FinanceException):
    from finance.exceptions import code_to_http_status

    return Response(
        {'code': exc.code, 'message': exc.message, 'data': exc.data},
        status=code_to_http_status(exc.code),
    )


class VoiceParseView(APIView):
    """
    POST /api/voice/parse/
    请求体: { "text": "今天中午吃饭花了35块", "reference_date": "2026-05-21" }
    """

    permission_classes = [IsAuthenticated]

    def post(self, request):
        ser = VoiceParseSerializer(data=request.data)
        if not ser.is_valid():
            return Response(
                {'code': 40001, 'message': str(ser.errors), 'data': None},
                status=400,
            )

        try:
            user = get_request_user(request)
        except PermissionError:
            return Response(
                {'code': 40101, 'message': '未登录', 'data': None},
                status=401,
            )

        ref = ser.validated_data.get('reference_date') or date.today()
        service = VoiceService()

        try:
            result = service.parse_text(
                text=ser.validated_data['text'],
                user=user,
                reference_date=ref,
            )
            return _ok(result.to_dict())
        except VoiceParseException as e:
            return _handle_finance_exc(e)
        except ValidationException as e:
            return _handle_finance_exc(e)
        except ExternalServiceException as e:
            return _handle_finance_exc(e)


class VoiceTranscribeView(APIView):
    """
    POST /api/voice/transcribe/
    multipart: file, lang(可选)
    P1 兜底：插件失败时上传音频
    """

    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request):
        upload = request.FILES.get('file')
        if not upload:
            return Response(
                {'code': 40001, 'message': '请上传音频文件', 'data': None},
                status=400,
            )

        max_mb = getattr(settings, 'MAX_UPLOAD_AUDIO_MB', 2)
        if upload.size > max_mb * 1024 * 1024:
            return Response(
                {'code': 40001, 'message': f'音频不能超过 {max_mb}MB', 'data': None},
                status=400,
            )

        try:
            user = get_request_user(request)
        except PermissionError:
            return Response(
                {'code': 40101, 'message': '未登录', 'data': None},
                status=401,
            )

        fmt = (upload.name or '').split('.')[-1].lower() or 'mp3'
        lang = request.data.get('lang', 'zh-CN')
        audio_bytes = upload.read()

        service = VoiceService()
        try:
            text = service.asr.transcribe(audio_bytes, fmt=fmt, lang=lang)
            return _ok({'text': text, 'duration_ms': None})
        except ExternalServiceException as e:
            return _handle_finance_exc(e)


class VoiceLogConfirmView(APIView):
    """POST /api/voice/logs/<id>/confirm/  body: { expense_id }"""

    permission_classes = [IsAuthenticated]

    def post(self, request, log_id):
        ser = VoiceConfirmSerializer(data=request.data)
        if not ser.is_valid():
            return Response(
                {'code': 40001, 'message': str(ser.errors), 'data': None},
                status=400,
            )

        try:
            user = get_request_user(request)
            VoiceService().confirm_log(
                log_id=int(log_id),
                expense_id=ser.validated_data['expense_id'],
                user=user,
            )
            return _ok({'log_id': int(log_id), 'expense_id': ser.validated_data['expense_id']})
        except ValidationException as e:
            return _handle_finance_exc(e)
        except PermissionError:
            return Response(
                {'code': 40101, 'message': '未登录', 'data': None},
                status=401,
            )
