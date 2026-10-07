from datetime import date

from django.db.models import Q, Sum
from rest_framework.response import Response
from rest_framework.views import APIView

from finance.models import Category, Expense, Loan, User
from finance.response import created, ok
from finance.serializers.loan_serializers import LoanCreateSerializer, LoanSerializer, RepaySerializer
from finance.utils import get_request_user


def _get_loan_category(direction):
    """获取借贷对应的分类：借出→其他支出，借入→其他收入"""
    if direction == Loan.DIRECTION_LEND:
        return Category.objects.filter(type=Category.TYPE_EXPENSE, name='其他支出').first()
    return Category.objects.filter(type=Category.TYPE_INCOME, name='其他收入').first()


def _get_repay_category(direction):
    """获取还款对应的分类：借出还款（收钱）→其他收入，借入还款（付钱）→其他支出"""
    if direction == Loan.DIRECTION_LEND:
        return Category.objects.filter(type=Category.TYPE_INCOME, name='其他收入').first()
    return Category.objects.filter(type=Category.TYPE_EXPENSE, name='其他支出').first()


def _create_expense_for_loan(user, loan, category, amount, desc):
    """为借贷操作创建对应的账单记录"""
    try:
        Expense.objects.create(
            user=user,
            category=category,
            amount=amount,
            description=desc,
            expense_date=date.today(),
            source=Expense.SOURCE_LOAN,
            payment_method=Expense.PAYMENT_OTHER,
        )
    except Exception:
        pass  # 账单创建失败不影响借贷操作


class LoanListCreateView(APIView):
    def get(self, request):
        user = get_request_user(request)
        qs = Loan.objects.select_related('user').filter(user=user)

        direction = request.query_params.get('direction')
        if direction:
            qs = qs.filter(direction=direction)
        status = request.query_params.get('status')
        if status:
            qs = qs.filter(status=status)
        cp = request.query_params.get('counterparty')
        if cp:
            qs = qs.filter(counterparty__icontains=cp)

        # 自动更新逾期状态
        self._check_overdue(qs)

        page = int(request.query_params.get('page', 1))
        size = min(int(request.query_params.get('page_size', 50)), 100)
        start = (page - 1) * size
        total = qs.count()
        items = qs.order_by('-loan_date', '-id')[start:start + size]
        return ok({
            'count': total,
            'results': LoanSerializer(items, many=True).data,
        })

    def post(self, request):
        user = get_request_user(request)
        ser = LoanCreateSerializer(data=request.data)
        if not ser.is_valid():
            return Response({'code': 40001, 'message': str(ser.errors), 'data': None}, status=400)
        loan = ser.save(user=user)

        # 同步生成账单流水记录
        cat = _get_loan_category(loan.direction)
        if cat:
            if loan.direction == Loan.DIRECTION_LEND:
                desc = f'借给{loan.counterparty} {loan.amount}元'
            else:
                desc = f'向{loan.counterparty}借款 {loan.amount}元'
            _create_expense_for_loan(user, loan, cat, loan.amount, desc)

        return created(LoanSerializer(loan).data)

    def _check_overdue(self, qs):
        today = date.today()
        overdue = qs.filter(
            status__in=['pending', 'partial'], due_date__isnull=False, due_date__lt=today
        )
        if overdue.exists():
            overdue.update(status=Loan.STATUS_OVERDUE)


class LoanDetailView(APIView):
    def get(self, request, pk):
        loan = Loan.objects.select_related('user').get(pk=pk, user=get_request_user(request))
        return ok(LoanSerializer(loan).data)

    def patch(self, request, pk):
        loan = Loan.objects.get(pk=pk, user=get_request_user(request))
        ser = LoanSerializer(loan, data=request.data, partial=True)
        if not ser.is_valid():
            return Response({'code': 40001, 'message': str(ser.errors), 'data': None}, status=400)
        loan = ser.save()
        loan.update_status()
        return ok(LoanSerializer(loan).data)

    def delete(self, request, pk):
        loan = Loan.objects.get(pk=pk, user=get_request_user(request))
        loan.delete()
        return ok(None, '已删除')


class LoanRepayView(APIView):
    def post(self, request, pk):
        loan = Loan.objects.get(pk=pk, user=get_request_user(request))
        if loan.status == Loan.STATUS_SETTLED:
            return Response({'code': 40001, 'message': '该笔已结清', 'data': None}, status=400)

        ser = RepaySerializer(data=request.data)
        if not ser.is_valid():
            return Response({'code': 40001, 'message': str(ser.errors), 'data': None}, status=400)

        repay = ser.validated_data['amount']
        loan.repaid_amount += repay
        if loan.repaid_amount > loan.amount:
            return Response({'code': 40001, 'message': '还款金额超过剩余欠款', 'data': None}, status=400)

        loan.save(update_fields=['repaid_amount'])
        loan.update_status()

        # 同步生成还款账单流水
        cat = _get_repay_category(loan.direction)
        if cat:
            if loan.direction == Loan.DIRECTION_LEND:
                desc = f'{loan.counterparty}还款 {repay}元'
            else:
                desc = f'还给{loan.counterparty} {repay}元'
            _create_expense_for_loan(get_request_user(request), loan, cat, repay, desc)

        return ok(LoanSerializer(loan).data)


class LoanSummaryView(APIView):
    def get(self, request):
        user = get_request_user(request)
        qs = Loan.objects.filter(user=user)
        self._check_overdue(qs)

        lend_qs = qs.filter(direction=Loan.DIRECTION_LEND)
        borrow_qs = qs.filter(direction=Loan.DIRECTION_BORROW)

        total_lend = lend_qs.aggregate(s=Sum('amount'))['s'] or 0
        total_borrow = borrow_qs.aggregate(s=Sum('amount'))['s'] or 0
        outstanding_lend = sum((r.remaining for r in lend_qs.filter(~Q(status=Loan.STATUS_SETTLED))), 0)
        outstanding_borrow = sum((r.remaining for r in borrow_qs.filter(~Q(status=Loan.STATUS_SETTLED))), 0)
        overdue_count = qs.filter(status=Loan.STATUS_OVERDUE).count()

        return ok({
            'total_lend': float(total_lend),
            'total_borrow': float(total_borrow),
            'outstanding_lend': float(outstanding_lend),
            'outstanding_borrow': float(outstanding_borrow),
            'net': float(outstanding_lend - outstanding_borrow),
            'overdue_count': overdue_count,
        })

    def _check_overdue(self, qs):
        today = date.today()
        overdue = qs.filter(
            status__in=['pending', 'partial'], due_date__isnull=False, due_date__lt=today
        )
        if overdue.exists():
            overdue.update(status=Loan.STATUS_OVERDUE)
