from __future__ import annotations

import json
import os
from typing import Any

from providers.base import ModelResponse, ToolCall


class OpenAIProvider:
    """OpenAI Chat Completions provider with normalized tool_calls output."""

    def __init__(
        self,
        *,
        api_key_env: str = "OPENAI_API_KEY",
        base_url: str | None = None,
        default_model: str = "gpt-4o-mini",
    ) -> None:
        self.api_key_env = api_key_env
        self.base_url = base_url
        self.default_model = default_model

    def complete(
        self,
        messages: list[dict[str, str]],
        tools: list[dict[str, Any]] | None = None,
        *,
        model: str | None = None,
        temperature: float = 0.0,
        tool_choice: Any | None = None,
    ) -> ModelResponse:
        try:
            import httpx
            from openai import APIConnectionError, APITimeoutError, OpenAI
        except ImportError as exc:
            raise RuntimeError("Install live provider dependency first: pip install openai") from exc

        api_key = os.getenv(self.api_key_env)
        if not api_key:
            raise RuntimeError(f"Missing API key env var: {self.api_key_env}")

        # Use explicit connection/read limits so the web UI does not hang forever
        # on a blocked socket. The SDK retries transient connection failures.
        timeout = httpx.Timeout(connect=15.0, read=60.0, write=30.0, pool=15.0)
        client = OpenAI(
            api_key=api_key,
            base_url=self.base_url,
            timeout=timeout,
            max_retries=2,
        )
        kwargs: dict[str, Any] = {
            "model": model or self.default_model,
            "messages": messages,
            "temperature": temperature,
        }
        if tools:
            kwargs["tools"] = tools
        if tool_choice is not None:
            kwargs["tool_choice"] = tool_choice

        try:
            resp = client.chat.completions.create(**kwargs)
        except (APIConnectionError, APITimeoutError) as exc:
            endpoint = self.base_url or "https://api.openai.com/v1"
            root_cause = exc.__cause__
            detail = f" ({type(root_cause).__name__}: {root_cause})" if root_cause else ""
            raise RuntimeError(
                f"Không kết nối được tới {endpoint}{detail}. "
                "Kiểm tra mạng/firewall, rồi thử lại; API key không được ghi vào log."
            ) from exc
        msg = resp.choices[0].message
        calls: list[ToolCall] = []
        for call in msg.tool_calls or []:
            args = json.loads(call.function.arguments or "{}")
            calls.append(ToolCall(name=call.function.name, args=args))
        return ModelResponse(text=msg.content, tool_calls=calls, raw=resp)
