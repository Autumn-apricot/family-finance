from rest_framework import serializers

from finance.models import Loan


class LoanSerializer(serializers.ModelSerializer):
    user_nickname = serializers.CharField(source='user.nickname', read_only=True)
    remaining = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)

    class Meta:
        model = Loan
        fields = [
            'id', 'user', 'user_nickname', 'counterparty', 'direction', 'amount',
            'repaid_amount', 'remaining', 'loan_date', 'due_date', 'status',
            'description', 'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'user', 'repaid_amount', 'status', 'created_at', 'updated_at']


class LoanCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Loan
        fields = ['counterparty', 'direction', 'amount', 'loan_date', 'due_date', 'description']


class RepaySerializer(serializers.Serializer):
    amount = serializers.DecimalField(max_digits=10, decimal_places=2, min_value=0.01)
