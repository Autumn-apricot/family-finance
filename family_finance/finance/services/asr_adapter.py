"""
ASR 适配器 — P1 云端转写兜底（插件失败时 /voice/transcribe/）
"""
from __future__ import annotations

import logging
from typing import Protocol

from django.conf import settings

from finance.exceptions import ExternalServiceException

logger = logging.getLogger(__name__)


class AsrAdapter(Protocol):
    def transcribe(self, audio_bytes: bytes, fmt: str = 'mp3', lang: str = 'zh-CN') -> str: ...


class StubAsrAdapter:
    """占位：教学环境未配置云端 ASR 时提示手动输入"""

    def transcribe(self, audio_bytes: bytes, fmt: str = 'mp3', lang: str = 'zh-CN') -> str:
        raise ExternalServiceException(
            '云端 ASR 未配置，请使用微信同声传译插件或在记账页手动输入文字'
        )


class WhisperAsrAdapter:
    """本地 Whisper 语音识别（基于 openai-whisper 库，用 soundfile 读音频无需 ffmpeg）"""

    def __init__(self):
        import whisper
        self._model = None
        self._whisper = whisper

    def _get_model(self):
        if self._model is None:
            self._model = self._whisper.load_model('base')
        return self._model

    def transcribe(self, audio_bytes: bytes, fmt: str = 'mp3', lang: str = 'zh-CN') -> str:
        import io
        import numpy as np
        import soundfile as sf
        try:
            # 用 soundfile 从内存读取音频 → numpy 数组（无需 ffmpeg）
            buf = io.BytesIO(audio_bytes)
            samples, sr = sf.read(buf, dtype='float32')
            if sr != 16000:
                # 重采样到 16kHz（Whisper 要求）
                import scipy.signal
                samples = scipy.signal.resample(samples, int(len(samples) * 16000 / sr))
            # 确保单声道
            if samples.ndim > 1:
                samples = samples.mean(axis=1)
            result = self._get_model().transcribe(samples.astype(np.float32), fp16=False, language='zh')
            return result['text'].strip()
        except ImportError as e:
            raise ExternalServiceException(f'Whisper 依赖缺失: {e}。请安装: pip install soundfile numpy scipy')
        except Exception as e:
            raise ExternalServiceException(f'语音识别失败: {str(e)[:100]}')


class TencentAsrAdapter:
    """
    腾讯云 ASR 占位实现。
    生产环境在此接入官方 SDK / HTTP API，密钥仅存 settings.ASR_*。
    """

    def __init__(self, secret_id: str, secret_key: str, region: str = 'ap-guangzhou'):
        self.secret_id = secret_id
        self.secret_key = secret_key
        self.region = region

    def transcribe(self, audio_bytes: bytes, fmt: str = 'mp3', lang: str = 'zh-CN') -> str:
        if not self.secret_id:
            raise ExternalServiceException('腾讯云 ASR 密钥未配置')
        # TODO: 接入腾讯云一句话识别 / 实时识别 API
        logger.info('Tencent ASR stub: %d bytes fmt=%s', len(audio_bytes), fmt)
        raise ExternalServiceException('腾讯云 ASR 适配器待实现，请优先使用端侧 WechatSI 插件')


def get_asr_adapter(provider: str | None = None) -> AsrAdapter:
    provider = provider or getattr(settings, 'ASR_PROVIDER', 'whisper')
    if provider in ('whisper', 'local'):
        return WhisperAsrAdapter()
    if provider in ('tencent', 'tencent_asr'):
        return TencentAsrAdapter(
            secret_id=getattr(settings, 'ASR_SECRET_ID', ''),
            secret_key=getattr(settings, 'ASR_SECRET_KEY', ''),
        )
    return StubAsrAdapter()
