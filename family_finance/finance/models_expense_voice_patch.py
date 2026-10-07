"""
Expense 模型语音字段补丁 — 合并到 finance/models.py 的 Expense 类中
"""
# SOURCE_CHOICES = [
#     ('manual', '手动'),
#     ('voice', '语音'),
# ]
# source = models.CharField(
#     max_length=10,
#     choices=SOURCE_CHOICES,
#     default='manual',
#     verbose_name='来源',
# )
# voice_log_id = models.IntegerField(
#     null=True,
#     blank=True,
#     verbose_name='语音日志ID',
# )
#
# 或使用外键（需先迁移 voice_parse_logs）:
# voice_log = models.ForeignKey(
#     'finance.VoiceParseLog',
#     on_delete=models.SET_NULL,
#     null=True,
#     blank=True,
#     related_name='expenses',
# )
