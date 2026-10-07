"""
将以下配置合并到 config/settings.py
"""
import os

LLM_API_BASE = os.environ.get('LLM_API_BASE', 'https://api.deepseek.com/v1')
LLM_API_KEY = os.environ.get('LLM_API_KEY', '')
LLM_MODEL = os.environ.get('LLM_MODEL', 'deepseek-chat')
LLM_TIMEOUT = int(os.environ.get('LLM_TIMEOUT', '30'))

VOICE_LLM_FALLBACK = os.environ.get('VOICE_LLM_FALLBACK', 'true').lower() == 'true'
VOICE_CONFIDENCE_THRESHOLD = float(os.environ.get('VOICE_CONFIDENCE_THRESHOLD', '0.6'))

ASR_PROVIDER = os.environ.get('ASR_PROVIDER', 'stub')
ASR_SECRET_ID = os.environ.get('ASR_SECRET_ID', '')
ASR_SECRET_KEY = os.environ.get('ASR_SECRET_KEY', '')

MAX_UPLOAD_AUDIO_MB = int(os.environ.get('MAX_UPLOAD_AUDIO_MB', '2'))
VOICE_RATE_LIMIT_PER_MIN = int(os.environ.get('VOICE_RATE_LIMIT_PER_MIN', '20'))
