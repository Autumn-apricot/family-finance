# Generated manually for finance app initial schema

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name='User',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('username', models.CharField(max_length=50, unique=True, verbose_name='登录名')),
                ('password', models.CharField(max_length=255, verbose_name='密码哈希')),
                ('nickname', models.CharField(blank=True, default='', max_length=50, verbose_name='昵称')),
                ('role', models.CharField(choices=[('admin', '管理员'), ('member', '成员')], default='member', max_length=10)),
                ('avatar_url', models.CharField(blank=True, default='', max_length=500)),
                ('is_active', models.BooleanField(default=True, verbose_name='是否启用')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'verbose_name': '用户',
                'verbose_name_plural': '用户',
                'db_table': 'users',
            },
        ),
        migrations.CreateModel(
            name='Category',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=50, verbose_name='分类名')),
                ('icon', models.CharField(default='💰', max_length=50)),
                ('type', models.CharField(choices=[('expense', '支出'), ('income', '收入')], default='expense', max_length=10)),
                ('sort_order', models.IntegerField(default=0)),
                ('is_system', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'verbose_name': '分类',
                'verbose_name_plural': '分类',
                'db_table': 'categories',
                'ordering': ['sort_order', 'id'],
            },
        ),
        migrations.CreateModel(
            name='SystemConfig',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('config_key', models.CharField(max_length=100, unique=True)),
                ('config_value', models.TextField(blank=True, default='')),
                ('value_type', models.CharField(default='string', max_length=20)),
                ('description', models.CharField(blank=True, default='', max_length=200)),
                ('is_secret', models.BooleanField(default=False)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'verbose_name': '系统配置',
                'verbose_name_plural': '系统配置',
                'db_table': 'system_config',
            },
        ),
        migrations.CreateModel(
            name='VoiceParseLog',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('raw_text', models.CharField(max_length=500, verbose_name='原文')),
                ('parsed_type', models.CharField(blank=True, default='expense', max_length=10, verbose_name='收支类型')),
                ('amount', models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True, verbose_name='金额')),
                ('expense_date', models.DateField(blank=True, null=True, verbose_name='消费日期')),
                ('description', models.CharField(blank=True, default='', max_length=200, verbose_name='备注')),
                ('confidence', models.FloatField(default=0.0, verbose_name='置信度')),
                ('match_method', models.CharField(blank=True, choices=[('rule', '规则'), ('keyword', '关键词'), ('llm', '大模型')], default='', max_length=20, verbose_name='匹配方式')),
                ('parsed_json', models.JSONField(blank=True, null=True, verbose_name='完整解析结果')),
                ('is_confirmed', models.BooleanField(default=False, verbose_name='是否已确认入账')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('category', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='finance.category', verbose_name='解析分类')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='voice_logs', to='finance.user', verbose_name='用户')),
            ],
            options={
                'verbose_name': '语音解析日志',
                'verbose_name_plural': '语音解析日志',
                'db_table': 'voice_parse_logs',
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='Expense',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('amount', models.DecimalField(decimal_places=2, max_digits=10)),
                ('description', models.CharField(blank=True, default='', max_length=200)),
                ('expense_date', models.DateField(verbose_name='消费日期')),
                ('source', models.CharField(choices=[('manual', '手动'), ('voice', '语音')], default='manual', max_length=10)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('category', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='expenses', to='finance.category')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='expenses', to='finance.user')),
                ('voice_log', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='linked_expense', to='finance.voiceparselog')),
            ],
            options={
                'verbose_name': '账单',
                'verbose_name_plural': '账单',
                'db_table': 'expenses',
                'ordering': ['-expense_date', '-id'],
            },
        ),
        migrations.AddField(
            model_name='voiceparselog',
            name='expense',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='confirmed_expense', to='finance.expense', verbose_name='确认入账的账单'),
        ),
        migrations.CreateModel(
            name='CategoryKeyword',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('keyword', models.CharField(max_length=50, verbose_name='关键词')),
                ('weight', models.IntegerField(default=10, verbose_name='权重')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('category', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='keywords', to='finance.category', verbose_name='分类')),
            ],
            options={
                'verbose_name': '分类关键词',
                'verbose_name_plural': '分类关键词',
                'db_table': 'category_keywords',
            },
        ),
        migrations.CreateModel(
            name='Budget',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('amount', models.DecimalField(decimal_places=2, max_digits=10)),
                ('month', models.CharField(max_length=7, verbose_name='月份 YYYY-MM')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('category', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='budgets', to='finance.category')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='budgets', to='finance.user')),
            ],
            options={
                'verbose_name': '预算',
                'verbose_name_plural': '预算',
                'db_table': 'budgets',
                'unique_together': {('user', 'category', 'month')},
            },
        ),
        migrations.CreateModel(
            name='AiChatHistory',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('chat_type', models.CharField(default='chat', max_length=20)),
                ('question', models.TextField()),
                ('answer', models.TextField()),
                ('tokens_used', models.IntegerField(default=0)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='ai_chats', to='finance.user')),
            ],
            options={
                'verbose_name': 'AI对话',
                'verbose_name_plural': 'AI对话',
                'db_table': 'ai_chat_history',
                'ordering': ['-created_at'],
            },
        ),
        migrations.AddIndex(
            model_name='user',
            index=models.Index(fields=['role', 'is_active'], name='idx_role_active'),
        ),
        migrations.AddIndex(
            model_name='category',
            index=models.Index(fields=['type', 'sort_order'], name='idx_type_sort'),
        ),
        migrations.AddIndex(
            model_name='voiceparselog',
            index=models.Index(fields=['user', 'created_at'], name='idx_voice_user_time'),
        ),
        migrations.AddIndex(
            model_name='expense',
            index=models.Index(fields=['expense_date', 'user'], name='idx_exp_date_user'),
        ),
        migrations.AddIndex(
            model_name='expense',
            index=models.Index(fields=['category', 'expense_date'], name='idx_exp_cat_date'),
        ),
        migrations.AddIndex(
            model_name='categorykeyword',
            index=models.Index(fields=['keyword'], name='idx_keyword'),
        ),
    ]
