from rest_framework.response import Response
from rest_framework.views import APIView

from finance.models import VoiceParseLog
from finance.response import ok
from finance.utils import get_request_user


class VoiceLogListView(APIView):
    def get(self, request):
        user = get_request_user(request)
        qs = VoiceParseLog.objects.filter(user=user).select_related('category').order_by('-created_at')
        page = int(request.query_params.get('page', 1))
        size = min(int(request.query_params.get('page_size', 20)), 100)
        start = (page - 1) * size
        items = qs[start : start + size]
        results = [
            {
                'id': r.id,
                'raw_text': r.raw_text,
                'parsed_type': r.parsed_type,
                'category_id': r.category_id,
                'amount': float(r.amount) if r.amount else None,
                'expense_date': r.expense_date.isoformat() if r.expense_date else None,
                'confidence': r.confidence,
                'match_method': r.match_method,
                'is_confirmed': r.is_confirmed,
                'expense_id': r.expense_id,
                'created_at': r.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            }
            for r in items
        ]
        return ok({'count': qs.count(), 'results': results})


class VoiceLogDetailView(APIView):
    def get(self, request, log_id):
        user = get_request_user(request)
        r = VoiceParseLog.objects.select_related('category').get(pk=log_id, user=user)
        return ok({
            'id': r.id,
            'raw_text': r.raw_text,
            'parsed_type': r.parsed_type,
            'category_id': r.category_id,
            'category_name': r.category.name if r.category else None,
            'amount': float(r.amount) if r.amount else None,
            'expense_date': r.expense_date.isoformat() if r.expense_date else None,
            'description': r.description,
            'confidence': r.confidence,
            'match_method': r.match_method,
            'is_confirmed': r.is_confirmed,
            'expense_id': r.expense_id,
            'parsed_json': r.parsed_json,
            'created_at': r.created_at.strftime('%Y-%m-%d %H:%M:%S'),
        })
