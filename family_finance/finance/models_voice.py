"""
语音模块 ORM 模型（合并到 finance/models.py 或 from .models_voice import *）
对应 docs/04_数据库设计说明书 — category_keywords、voice_parse_logs
"""
from django.db import models


class CategoryKeyword(models.Model):
    """分类关键词 — 语音子串匹配"""

    category = models.ForeignKey(
        'finance.Category',
        on_delete=models.CASCADE,
        related_name='keywords',
        verbose_name='分类',
    )
    keyword = models.CharField(max_length=50, verbose_name='关键词')
    weight = models.IntegerField(default=10, verbose_name='权重')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'category_keywords'
        verbose_name = '分类关键词'
        verbose_name_plural = verbose_name
        indexes = [
            models.Index(fields=['keyword'], name='idx_keyword'),
        ]

    def __str__(self):
        return f'{self.category_id}:{self.keyword}({self.weight})'


class VoiceParseLog(models.Model):
    """语音解析日志 — 全量审计"""

    MATCH_RULE = 'rule'
    MATCH_KEYWORD = 'keyword'
    MATCH_LLM = 'llm'
    MATCH_METHOD_CHOICES = [
        (MATCH_RULE, '规则'),
        (MATCH_KEYWORD, '关键词'),
        (MATCH_LLM, '大模型'),
    ]

    user = models.ForeignKey(
        'finance.User',
        on_delete=models.CASCADE,
        related_name='voice_logs',
        verbose_name='用户',
    )
    raw_text = models.CharField(max_length=500, verbose_name='原文')
    parsed_type = models.CharField(max_length=10, blank=True, default='expense', verbose_name='收支类型')
    category = models.ForeignKey(
        'finance.Category',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='解析分类',
    )
    amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, verbose_name='金额')
    expense_date = models.DateField(null=True, blank=True, verbose_name='消费日期')
    description = models.CharField(max_length=200, blank=True, default='', verbose_name='备注')
    confidence = models.FloatField(default=0.0, verbose_name='置信度')
    match_method = models.CharField(
        max_length=20,
        choices=MATCH_METHOD_CHOICES,
        blank=True,
        default='',
        verbose_name='匹配方式',
    )
    parsed_json = models.JSONField(null=True, blank=True, verbose_name='完整解析结果')
    is_confirmed = models.BooleanField(default=False, verbose_name='是否已确认入账')
    expense = models.ForeignKey(
        'finance.Expense',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='confirmed_expense',
        verbose_name='确认入账的账单',
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'voice_parse_logs'
        verbose_name = '语音解析日志'
        verbose_name_plural = verbose_name
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'created_at'], name='idx_voice_user_time'),
        ]

    def __str__(self):
        return f'VoiceLog#{self.id} {self.raw_text[:20]}'
