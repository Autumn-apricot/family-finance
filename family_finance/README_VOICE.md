# 语音智能记账模块 — 集成说明

本目录为 **可拷贝到 `D:\family_finance` 项目** 的语音模块骨架，技术路线：

- **ASR**：小程序端微信同声传译插件 `WechatSI`（主路径）
- **解析**：`VoiceService` = 规则 + `category_keywords` + **DeepSeek** 低置信兜底
- **入账**：用户确认 → `POST /expenses/` + 可选 `voice/logs/{id}/confirm/`

## 一、后端集成步骤

### 1. 复制文件

将 `code/family_finance/finance/` 下以下内容合并到学生项目的 `finance/` 应用：

```
finance/
├── models_voice.py          → 合并到 models.py 或 import
├── exceptions.py            → 新建或合并
├── utils.py
├── services/
│   ├── llm_client.py
│   ├── asr_adapter.py
│   └── voice_service.py
├── serializers/voice_serializers.py
├── views/voice_views.py
└── urls_voice.py            → 合并到 urls.py
```

### 2. 扩展 Expense 模型（若尚未有）

在 `finance/models.py` 的 `Expense` 中增加：

```python
SOURCE_CHOICES = [('manual', '手动'), ('voice', '语音')]
source = models.CharField(max_length=10, choices=SOURCE_CHOICES, default='manual')
voice_log_id = models.IntegerField(null=True, blank=True)  # 或 ForeignKey VoiceParseLog
```

执行 `makemigrations` && `migrate`。

### 3. 注册模型

在 `models.py` 末尾：

```python
from .models_voice import CategoryKeyword, VoiceParseLog  # noqa: F401
```

### 4. settings.py 追加

```python
# DeepSeek / OpenAI 兼容
LLM_API_BASE = os.environ.get('LLM_API_BASE', 'https://api.deepseek.com/v1')
LLM_API_KEY = os.environ.get('LLM_API_KEY', '')
LLM_MODEL = os.environ.get('LLM_MODEL', 'deepseek-chat')
LLM_TIMEOUT = 30

VOICE_LLM_FALLBACK = True
VOICE_CONFIDENCE_THRESHOLD = 0.6
ASR_PROVIDER = 'stub'  # 端侧插件为主，云端 ASR 为 P1
MAX_UPLOAD_AUDIO_MB = 2

REST_FRAMEWORK = {
    # ...
    'EXCEPTION_HANDLER': 'finance.exceptions.custom_exception_handler',
}
```

安装依赖：`pip install httpx`

### 5. 路由

`finance/urls.py`：

```python
from django.urls import path, include
from finance.urls_voice import urlpatterns as voice_urls

urlpatterns = [
    # ... 现有路由
] + voice_urls
```

### 6. 初始化关键词

```bash
python manage.py migrate
python scripts/init_keywords.py
```

### 7. 测试

```bash
curl -X POST http://127.0.0.1:8000/api/voice/parse/ \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d "{\"text\":\"今天中午吃饭花了35块\"}"
```

期望：`category_name=餐饮`, `amount=35`, `code=0`。

## 二、小程序集成步骤

### 1. 复制目录

```
code/miniprogram/components/voice-input/  →  小程序/components/voice-input/
code/miniprogram/utils/voice.js           →  小程序/utils/voice.js
```

### 2. app.json 声明插件

```json
{
  "plugins": {
    "WechatSI": {
      "version": "0.3.5",
      "provider": "wx069ba97219f66d99"
    }
  }
}
```

### 3. 记账页引用

`pages/record/record.json`：

```json
{
  "usingComponents": {
    "voice-input": "/components/voice-input/voice-input"
  }
}
```

`record.wxml` 参考 `pages/record/record-voice-demo.wxml`。

### 4. 事件处理

- `bind:parsed` → 填充表单 + 展示预览
- `bind:error` → Toast 提示
- 确认保存 → `POST /expenses/` 带 `source: 'voice'`, `voice_log_id`

## 三、目录结构

```
code/
├── family_finance/          # Django 语音模块
│   ├── finance/services/voice_service.py
│   └── scripts/init_keywords.py
└── miniprogram/             # 小程序组件
    └── components/voice-input/
```

## 四、注意事项

1. `get_request_user()` 需与项目 JWT 认证对齐，确保 `request.user` 为 `finance.User`。
2. DeepSeek Key **禁止**写入小程序，仅配置在后端 `.env`。
3. 插件需在微信公众平台添加「同声传译」插件后方可真机调试。
