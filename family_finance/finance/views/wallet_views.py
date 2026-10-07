from rest_framework.response import Response
from rest_framework.views import APIView

from finance.models import Wallet
from finance.response import ok
from finance.utils import get_request_user

ICONS = {'wechat': '💚', 'alipay': '💙', 'cash': '💵', 'bank_card': '💳', 'credit_card': '💎', 'other': '💰'}


class WalletView(APIView):
    def get(self, request):
        user = get_request_user(request)
        wallets = []
        for code, label in Wallet.METHOD_CHOICES:
            w, _ = Wallet.objects.get_or_create(user=user, method=code, defaults={'balance': 0})
            wallets.append({
                'id': w.id, 'method': code, 'label': label,
                'icon': ICONS.get(code, '💰'), 'balance': float(w.balance),
            })
        total = sum(w['balance'] for w in wallets)
        return ok({'items': wallets, 'total': total})

    def patch(self, request):
        user = get_request_user(request)
        method = request.data.get('method')
        balance = request.data.get('balance')
        if not method or balance is None:
            return Response({'code': 40001, 'message': '缺少 method 或 balance'}, status=400)
        try:
            balance = float(balance)
        except (TypeError, ValueError):
            return Response({'code': 40001, 'message': '余额格式错误'}, status=400)

        w, _ = Wallet.objects.update_or_create(
            user=user, method=method, defaults={'balance': balance},
        )
        return ok({
            'id': w.id, 'method': w.method, 'label': w.get_method_display(),
            'icon': ICONS.get(w.method, '💰'), 'balance': float(w.balance),
        })
