from rest_framework import serializers

from finance.models import AiChatHistory, Budget, Category, Expense


class SubCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name', 'icon', 'sort_order']


class CategorySerializer(serializers.ModelSerializer):
    children = SubCategorySerializer(many=True, read_only=True)
    parent_id = serializers.IntegerField(source='parent.id', read_only=True, allow_null=True)

    class Meta:
        model = Category
        fields = ['id', 'name', 'icon', 'type', 'sort_order', 'is_system',
                  'parent_id', 'children', 'created_at']
        read_only_fields = ['id', 'created_at']


class ExpenseSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True)
    category_icon = serializers.CharField(source='category.icon', read_only=True)
    category_type = serializers.CharField(source='category.type', read_only=True)
    parent_category_name = serializers.SerializerMethodField()
    parent_category_icon = serializers.SerializerMethodField()
    user_nickname = serializers.CharField(source='user.nickname', read_only=True)
    payment_method_display = serializers.SerializerMethodField()
    payment_method_icon = serializers.SerializerMethodField()

    class Meta:
        model = Expense
        fields = [
            'id', 'user', 'user_nickname', 'category', 'category_name', 'category_icon',
            'parent_category_name', 'parent_category_icon',
            'category_type', 'amount', 'description', 'expense_date', 'source',
            'payment_method', 'payment_method_display', 'payment_method_icon',
            'voice_log', 'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'user', 'created_at', 'updated_at', 'source', 'voice_log']

    def get_parent_category_name(self, obj):
        return obj.category.parent.name if obj.category.parent else None

    def get_parent_category_icon(self, obj):
        return obj.category.parent.icon if obj.category.parent else None

    def get_payment_method_display(self, obj):
        return dict(Expense.PAYMENT_CHOICES).get(obj.payment_method, '')

    def get_payment_method_icon(self, obj):
        icons = {
            'wechat': '💚', 'alipay': '💙', 'cash': '💵',
            'bank_card': '💳', 'credit_card': '💎', 'other': '💰',
        }
        return icons.get(obj.payment_method, '💰')

    def validate_amount(self, value):
        if value <= 0:
            raise serializers.ValidationError('金额必须大于 0')
        return value


class ExpenseCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Expense
        fields = ['category', 'amount', 'description', 'expense_date', 'source', 'payment_method']

    def validate_amount(self, value):
        if value <= 0:
            raise serializers.ValidationError('金额必须大于 0')
        return value


class BudgetSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True)

    class Meta:
        model = Budget
        fields = ['id', 'user', 'category', 'category_name', 'amount', 'month', 'created_at', 'updated_at']
        read_only_fields = ['id', 'user', 'created_at', 'updated_at']


class AiChatSerializer(serializers.ModelSerializer):
    class Meta:
        model = AiChatHistory
        fields = ['id', 'chat_type', 'question', 'answer', 'tokens_used', 'created_at']
        read_only_fields = fields
