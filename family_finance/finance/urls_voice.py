"""
语音路由片段 — 合并到 finance/urls.py：

from django.urls import path
from finance.views.voice_views import VoiceParseView, VoiceTranscribeView, VoiceLogConfirmView

urlpatterns += [
    path('voice/parse/', VoiceParseView.as_view(), name='voice-parse'),
    path('voice/transcribe/', VoiceTranscribeView.as_view(), name='voice-transcribe'),
    path('voice/logs/<int:log_id>/confirm/', VoiceLogConfirmView.as_view(), name='voice-log-confirm'),
]
"""

from django.urls import path

from finance.views.voice_views import VoiceLogConfirmView, VoiceParseView, VoiceTranscribeView

urlpatterns = [
    path('voice/parse/', VoiceParseView.as_view(), name='voice-parse'),
    path('voice/transcribe/', VoiceTranscribeView.as_view(), name='voice-transcribe'),
    path('voice/logs/<int:log_id>/confirm/', VoiceLogConfirmView.as_view(), name='voice-log-confirm'),
]
