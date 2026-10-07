"""Django 信号 — 账单自动更新钱包余额"""
from django.db.models.signals import post_delete, post_save, pre_save
from django.dispatch import receiver

from finance.models import Expense, Wallet


def _update_wallet(user, method, delta):
    """delta > 0 加钱，< 0 扣钱"""
    if not method:
        return
    wallet, _ = Wallet.objects.get_or_create(user=user, method=method, defaults={'balance': 0})
    wallet.balance += delta
    wallet.save(update_fields=['balance'])


@receiver(pre_save, sender=Expense)
def expense_pre_save(sender, instance, **kwargs):
    """保存前记录旧值，用于计算差额"""
    if instance.pk:
        try:
            old = Expense.objects.get(pk=instance.pk)
            instance._old_payment_method = old.payment_method
            instance._old_amount = old.amount
            instance._old_category_type = old.category.type if hasattr(old, 'category') and old.category else 'expense'
        except Expense.DoesNotExist:
            pass


@receiver(post_save, sender=Expense)
def expense_post_save(sender, instance, created, **kwargs):
    """新增/修改后更新钱包"""
    cat_type = instance.category.type if instance.category else 'expense'
    method = instance.payment_method
    user = instance.user

    if created:
        delta = instance.amount if cat_type == 'income' else -instance.amount
        _update_wallet(user, method, delta)
    else:
        # 修改：先撤回旧记录，再应用新记录
        old_method = getattr(instance, '_old_payment_method', None)
        old_amount = getattr(instance, '_old_amount', None)
        old_type = getattr(instance, '_old_category_type', 'expense')
        if old_method and old_amount is not None:
            # 撤回旧
            old_delta = old_amount if old_type == 'income' else -old_amount
            _update_wallet(user, old_method, -old_delta)
        # 应用新
        new_delta = instance.amount if cat_type == 'income' else -instance.amount
        _update_wallet(user, method, new_delta)


@receiver(post_delete, sender=Expense)
def expense_post_delete(sender, instance, **kwargs):
    """删除账单，反向操作钱包"""
    cat_type = instance.category.type if instance.category else 'expense'
    delta = instance.amount if cat_type == 'income' else -instance.amount
    _update_wallet(instance.user, instance.payment_method, -delta)
