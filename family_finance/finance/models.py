"""
ORM 模型 — 对应 docs/04 数据库设计说明书 v3.0
"""
from datetime import date

from django.contrib.auth.hashers import check_password, make_password
from django.db import models

from finance.models_voice import CategoryKeyword, VoiceParseLog  # noqa: F401


class Family(models.Model):
    """家庭群组"""
    name = models.CharField(max_length=50, verbose_name='家庭名')
    invite_code = models.CharField(max_length=8, unique=True, verbose_name='邀请码')
    created_by = models.ForeignKey('User', on_delete=models.PROTECT, related_name='created_families')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'families'
        verbose_name = '家庭'
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.name


class User(models.Model):
    ROLE_ADMIN = 'admin'
    ROLE_MEMBER = 'member'
    ROLE_CHOICES = [(ROLE_ADMIN, '管理员'), (ROLE_MEMBER, '成员')]

    username = models.CharField(max_length=50, unique=True, verbose_name='登录名')
    password = models.CharField(max_length=255, verbose_name='密码哈希')
    nickname = models.CharField(max_length=50, blank=True, default='', verbose_name='昵称')
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default=ROLE_MEMBER)
    avatar_url = models.CharField(max_length=500, blank=True, default='')
    is_active = models.BooleanField(default=True, verbose_name='是否启用')
    hide_total_amount = models.BooleanField(default=False, verbose_name='隐藏首页总金额')
    family = models.ForeignKey(Family, null=True, blank=True, on_delete=models.SET_NULL, related_name='members', verbose_name='所属家庭')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'users'
        verbose_name = '用户'
        verbose_name_plural = verbose_name
        indexes = [models.Index(fields=['role', 'is_active'], name='idx_role_active')]

    def set_password(self, raw: str):
        self.password = make_password(raw)

    def check_password(self, raw: str) -> bool:
        return check_password(raw, self.password)

    @property
    def is_authenticated(self):
        return True

    @property
    def is_anonymous(self):
        return False

    def __str__(self):
        return self.username


class Category(models.Model):
    TYPE_EXPENSE = 'expense'
    TYPE_INCOME = 'income'
    TYPE_CHOICES = [(TYPE_EXPENSE, '支出'), (TYPE_INCOME, '收入')]

    name = models.CharField(max_length=50, verbose_name='分类名')
    icon = models.CharField(max_length=50, default='💰')
    type = models.CharField(max_length=10, choices=TYPE_CHOICES, default=TYPE_EXPENSE)
    sort_order = models.IntegerField(default=0)
    is_system = models.BooleanField(default=True)
    parent = models.ForeignKey(
        'self', null=True, blank=True, on_delete=models.CASCADE,
        related_name='children', verbose_name='父分类',
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'categories'
        verbose_name = '分类'
        verbose_name_plural = verbose_name
        ordering = ['sort_order', 'id']
        indexes = [models.Index(fields=['type', 'sort_order'], name='idx_type_sort')]

    def __str__(self):
        if self.parent:
            return f'{self.parent.name} > {self.name}'
        return self.name


class Expense(models.Model):
    SOURCE_MANUAL = 'manual'
    SOURCE_VOICE = 'voice'
    SOURCE_LOAN = 'loan'
    SOURCE_CHOICES = [(SOURCE_MANUAL, '手动'), (SOURCE_VOICE, '语音'), (SOURCE_LOAN, '借贷')]

    PAYMENT_WECHAT = 'wechat'
    PAYMENT_ALIPAY = 'alipay'
    PAYMENT_CASH = 'cash'
    PAYMENT_BANK = 'bank_card'
    PAYMENT_CREDIT = 'credit_card'
    PAYMENT_OTHER = 'other'
    PAYMENT_CHOICES = [
        (PAYMENT_WECHAT, '微信'),
        (PAYMENT_ALIPAY, '支付宝'),
        (PAYMENT_CASH, '现金'),
        (PAYMENT_BANK, '银行卡'),
        (PAYMENT_CREDIT, '信用卡'),
        (PAYMENT_OTHER, '其他'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='expenses')
    category = models.ForeignKey(Category, on_delete=models.PROTECT, related_name='expenses')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.CharField(max_length=200, blank=True, default='')
    expense_date = models.DateField(verbose_name='消费日期')
    source = models.CharField(max_length=10, choices=SOURCE_CHOICES, default=SOURCE_MANUAL)
    payment_method = models.CharField(
        max_length=20, choices=PAYMENT_CHOICES, default=PAYMENT_WECHAT,
        blank=True, verbose_name='支付方式',
    )
    voice_log = models.ForeignKey(
        VoiceParseLog,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='linked_expense',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'expenses'
        verbose_name = '账单'
        verbose_name_plural = verbose_name
        ordering = ['-expense_date', '-id']
        indexes = [
            models.Index(fields=['expense_date', 'user'], name='idx_exp_date_user'),
            models.Index(fields=['category', 'expense_date'], name='idx_exp_cat_date'),
        ]

    def __str__(self):
        return f'Expense#{self.id} {self.amount}'


class Budget(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='budgets')
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='budgets')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    month = models.CharField(max_length=7, verbose_name='月份 YYYY-MM')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'budgets'
        verbose_name = '预算'
        verbose_name_plural = verbose_name
        unique_together = [['user', 'category', 'month']]

    def __str__(self):
        return f'Budget {self.user_id} {self.month}'


class AiChatHistory(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='ai_chats')
    chat_type = models.CharField(max_length=20, default='chat')
    question = models.TextField()
    answer = models.TextField()
    tokens_used = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'ai_chat_history'
        verbose_name = 'AI对话'
        verbose_name_plural = verbose_name
        ordering = ['-created_at']


class Loan(models.Model):
    """借贷记录 — 借出/借入、还款追踪"""
    DIRECTION_LEND = 'lend'
    DIRECTION_BORROW = 'borrow'
    DIRECTION_CHOICES = [(DIRECTION_LEND, '我借出'), (DIRECTION_BORROW, '我借入')]

    STATUS_PENDING = 'pending'
    STATUS_PARTIAL = 'partial'
    STATUS_SETTLED = 'settled'
    STATUS_OVERDUE = 'overdue'
    STATUS_CHOICES = [
        (STATUS_PENDING, '待还'), (STATUS_PARTIAL, '部分还'),
        (STATUS_SETTLED, '已结清'), (STATUS_OVERDUE, '逾期'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='loans')
    counterparty = models.CharField(max_length=50, verbose_name='对方')
    direction = models.CharField(max_length=10, choices=DIRECTION_CHOICES, default=DIRECTION_LEND)
    amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='借贷金额')
    repaid_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name='已还金额')
    loan_date = models.DateField(verbose_name='借贷日期')
    due_date = models.DateField(null=True, blank=True, verbose_name='还款日期')
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default=STATUS_PENDING)
    description = models.CharField(max_length=200, blank=True, default='', verbose_name='备注')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'loans'
        verbose_name = '借贷'
        verbose_name_plural = verbose_name
        ordering = ['-loan_date', '-id']
        indexes = [
            models.Index(fields=['user', 'status'], name='idx_loan_user_status'),
            models.Index(fields=['direction', 'status'], name='idx_loan_dir_status'),
        ]

    def __str__(self):
        return f'Loan#{self.id} {self.direction} {self.amount}'

    @property
    def remaining(self):
        return self.amount - self.repaid_amount

    def update_status(self):
        if self.repaid_amount >= self.amount:
            self.status = self.STATUS_SETTLED
        elif self.repaid_amount > 0:
            self.status = self.STATUS_PARTIAL
        elif self.due_date and self.due_date < date.today():
            self.status = self.STATUS_OVERDUE
        else:
            self.status = self.STATUS_PENDING
        self.save(update_fields=['status'])


class Wallet(models.Model):
    """用户钱包 — 各支付方式余额"""
    METHOD_CHOICES = Expense.PAYMENT_CHOICES

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='wallets')
    method = models.CharField(max_length=20, choices=METHOD_CHOICES)
    balance = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name='余额')
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'wallets'
        verbose_name = '钱包'
        verbose_name_plural = verbose_name
        unique_together = [['user', 'method']]

    def __str__(self):
        return f'{self.user.username} {self.get_method_display()} ¥{self.balance}'


class RecurringBill(models.Model):
    """周期账单 — 房租、订阅等自动到期生成"""
    CYCLE_DAILY = 'daily'
    CYCLE_WEEKLY = 'weekly'
    CYCLE_MONTHLY = 'monthly'
    CYCLE_YEARLY = 'yearly'
    CYCLE_CHOICES = [
        (CYCLE_DAILY, '每天'), (CYCLE_WEEKLY, '每周'),
        (CYCLE_MONTHLY, '每月'), (CYCLE_YEARLY, '每年'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='recurring_bills')
    category = models.ForeignKey(Category, on_delete=models.PROTECT)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.CharField(max_length=200, blank=True, default='')
    payment_method = models.CharField(max_length=20, choices=Expense.PAYMENT_CHOICES, default=Expense.PAYMENT_WECHAT)
    cycle = models.CharField(max_length=10, choices=CYCLE_CHOICES, default=CYCLE_MONTHLY)
    next_date = models.DateField(verbose_name='下次生成日期')
    is_active = models.BooleanField(default=True, verbose_name='启用')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'recurring_bills'
        verbose_name = '周期账单'
        verbose_name_plural = verbose_name
        ordering = ['next_date', '-id']

    def __str__(self):
        return f'{self.user.username} {self.description} ¥{self.amount} {self.get_cycle_display()}'


class SystemConfig(models.Model):
    config_key = models.CharField(max_length=100, unique=True)
    config_value = models.TextField(blank=True, default='')
    value_type = models.CharField(max_length=20, default='string')
    description = models.CharField(max_length=200, blank=True, default='')
    is_secret = models.BooleanField(default=False)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'system_config'
        verbose_name = '系统配置'
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.config_key
