"""DeepSeek API 客户端（OpenAI 兼容 Chat Completions，无 Qt 依赖）。"""

from __future__ import annotations

from typing import Any

import requests


class DeepSeekClient:
    """调用 DeepSeek Chat Completions。"""

    def __init__(
        self,
        api_key: str,
        base_url: str = "https://api.deepseek.com",
        model: str = "deepseek-chat",
        timeout_sec: int = 120,
    ) -> None:
        self._api_key = api_key
        self._base_url = base_url.rstrip("/")
        self._model = model
        self._timeout_sec = timeout_sec

    def chat_completion(
        self,
        messages: list[dict[str, str]],
        *,
        temperature: float = 0.3,
        response_format_json: bool = True,
        extra_body: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        if not self._api_key:
            raise ValueError("DeepSeek API Key 未配置")

        url = f"{self._base_url}/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
        }
        body: dict[str, Any] = {
            "model": self._model,
            "messages": messages,
            "temperature": temperature,
        }
        if response_format_json:
            body["response_format"] = {"type": "json_object"}
        if extra_body:
            body.update(extra_body)

        resp = requests.post(url, headers=headers, json=body, timeout=self._timeout_sec)
        resp.raise_for_status()
        return resp.json()

    @staticmethod
    def extract_message_content(data: dict[str, Any]) -> str:
        try:
            return data["choices"][0]["message"]["content"] or ""
        except (KeyError, IndexError, TypeError) as exc:
            raise ValueError(f"无法解析 DeepSeek 响应: {data!r}") from exc
