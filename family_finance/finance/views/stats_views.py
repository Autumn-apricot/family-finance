from datetime import date

from rest_framework.response import Response
from rest_framework.views import APIView

from finance.response import ok
from finance.services.stats_service import StatsService
from finance.utils import get_family_user_ids, get_request_user


def _get_family_user_ids_or_none(request):
    """家庭用户返回成员ID列表，管理员看全部，普通用户只看自己"""
    uid = request.query_params.get('user_id')
    if uid:
        return [int(uid)]
    user = get_request_user(request)
    if user.role == 'admin' and not user.family:
        return None  # 管理员看全部
    if user.family:
        return get_family_user_ids(user)
    return [user.id]  # 普通用户只看自己


class StatsSummaryView(APIView):
    def get(self, request):
        return ok(StatsService().summary(_get_family_user_ids_or_none(request)))


class StatsDailyView(APIView):
    def get(self, request):
        d = request.query_params.get('date') or date.today().isoformat()
        try:
            target = date.fromisoformat(d)
        except ValueError:
            return Response({'code': 40001, 'message': 'date 格式错误', 'data': None}, status=400)
        return ok(StatsService().daily(target, _get_family_user_ids_or_none(request)))


class StatsWeeklyView(APIView):
    def get(self, request):
        ws = request.query_params.get('week_start')
        if not ws:
            return Response({'code': 40001, 'message': '缺少 week_start', 'data': None}, status=400)
        try:
            week_start = date.fromisoformat(ws)
        except ValueError:
            return Response({'code': 40001, 'message': 'week_start 格式错误', 'data': None}, status=400)
        return ok(StatsService().weekly(week_start, _get_family_user_ids_or_none(request)))


class StatsMonthlyView(APIView):
    def get(self, request):
        month = request.query_params.get('month')
        if not month:
            return Response({'code': 40001, 'message': '缺少 month', 'data': None}, status=400)
        return ok(StatsService().monthly(month, _get_family_user_ids_or_none(request)))


class StatsAnnualView(APIView):
    def get(self, request):
        year = request.query_params.get('year')
        if not year:
            return Response({'code': 40001, 'message': '缺少 year', 'data': None}, status=400)
        return ok(StatsService().annual(int(year), _get_family_user_ids_or_none(request)))
