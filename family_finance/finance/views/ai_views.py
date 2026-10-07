from rest_framework.response import Response
from rest_framework.views import APIView

from finance.response import ok
from finance.services.ai_service import AiService
from finance.utils import get_request_user


class AiChatView(APIView):
    def post(self, request):
        question = request.data.get('question', '').strip()
        if not question:
            return Response({'code': 40001, 'message': '问题不能为空', 'data': None}, status=400)
        user = get_request_user(request)
        return ok(AiService().chat(user, question))


class AiAdviceView(APIView):
    def post(self, request):
        user = get_request_user(request)
        return ok(AiService().advice(user))


class AiHistoryView(APIView):
    def get(self, request):
        user = get_request_user(request)
        page = int(request.query_params.get('page', 1))
        size = min(int(request.query_params.get('page_size', 20)), 100)
        items = AiService().history(user, page, size)
        return ok({'count': len(items), 'results': items})
