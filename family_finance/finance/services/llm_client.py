"""
大模型 HTTP 客户端 — OpenAI 兼容（DeepSeek / 通义 / OpenAI）
"""
from __future__ import annotations

import json
import logging
import re
from typing import Optional

import httpx
from django.conf import settings

from finance.exceptions import ExternalServiceException

logger = logging.getLogger(__name__)

_llm_singleton: Optional['LlmClient'] = None


class LlmClient:
    def __init__(
        self,
        base_url: str,
        api_key: str,
        model: str,
        timeout: int = 30,
    ):
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key
        self.model = model
        self.timeout = timeout

    def chat_completion(
        self,
        messages: list[dict],
        temperature: float = 0.3,
        max_tokens: int = 512,
    ) -> tuple[str, int]:
        """
        调用 Chat Completions，返回 (content, tokens_used)。
        失败抛出 ExternalServiceException。
        """
        if not self.api_key or self.api_key.startswith('your-'):
            raise ExternalServiceException('LLM API Key 未配置')

        url = f'{self.base_url}/chat/completions'
        payload = {
            'model': self.model,
            'messages': messages,
            'temperature': temperature,
            'max_tokens': max_tokens,
        }

        try:
            with httpx.Client(timeout=self.timeout) as client:
                resp = client.post(
                    url,
                    headers={
                        'Authorization': f'Bearer {self.api_key}',
                        'Content-Type': 'application/json',
                    },
                    json=payload,
                )
                resp.raise_for_status()
                data = resp.json()
        except httpx.TimeoutException as e:
            logger.warning('LLM timeout: %s', e)
            raise ExternalServiceException('AI 服务响应超时') from e
        except httpx.HTTPError as e:
            logger.warning('LLM http error: %s', e)
            raise ExternalServiceException('AI 服务暂时不可用') from e

        try:
            content = data['choices'][0]['message']['content']
            tokens = data.get('usage', {}).get('total_tokens', 0)
        except (KeyError, IndexError) as e:
            raise ExternalServiceException('AI 返回格式异常') from e

        return content, tokens

    def parse_json_from_content(self, content: str) -> dict:
        """从模型回复中提取 JSON 对象"""
        content = content.strip()
        # 去掉 markdown 代码块
        if '```' in content:
            m = re.search(r'```(?:json)?\s*([\s\S]*?)```', content)
            if m:
                content = m.group(1).strip()
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            # 尝试找第一个 { ... }
            m = re.search(r'\{[\s\S]*\}', content)
            if m:
                return json.loads(m.group())
            raise ExternalServiceException('AI 返回的 JSON 无法解析')


def get_llm_client() -> LlmClient:
    global _llm_singleton
    if _llm_singleton is None:
        _llm_singleton = LlmClient(
            base_url=getattr(settings, 'LLM_API_BASE', 'https://api.deepseek.com/v1'),
            api_key=getattr(settings, 'LLM_API_KEY', ''),
            model=getattr(settings, 'LLM_MODEL', 'deepseek-chat'),
            timeout=getattr(settings, 'LLM_TIMEOUT', 30),
        )
    return _llm_singleton


def reset_llm_client() -> None:
    """管理端修改配置后清除单例"""
    global _llm_singleton
    _llm_singleton = None
