from __future__ import annotations

import json
from typing import Any, TypeVar

import requests
from pydantic import BaseModel, ValidationError

from app.config import Settings

T = TypeVar("T", bound=BaseModel)


class LLMClient:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def generate_structured(self, *, system: str, user: str, schema: type[T]) -> T | None:
        if not self.settings.enable_live_llm or not self.settings.llm_api_key:
            return None

        payload = {
            "model": self.settings.llm_model,
            "response_format": {"type": "json_object"},
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            "temperature": 0,
        }
        headers = {
            "Authorization": f"Bearer {self.settings.llm_api_key}",
            "Content-Type": "application/json",
        }

        for _ in range(2):
            response = requests.post(
                f"{self.settings.llm_base_url}/chat/completions",
                headers=headers,
                json=payload,
                timeout=self.settings.llm_timeout_seconds,
            )
            response.raise_for_status()
            parsed = self._parse_response(response.json())
            if parsed is None:
                continue
            try:
                return schema.model_validate(parsed)
            except ValidationError:
                continue
        return None

    @staticmethod
    def _parse_response(raw: dict[str, Any]) -> dict[str, Any] | None:
        content = raw.get("choices", [{}])[0].get("message", {}).get("content")
        if not content:
            return None
        if isinstance(content, dict):
            return content
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            start = content.find("{")
            end = content.rfind("}")
            if start >= 0 and end > start:
                fragment = content[start : end + 1]
                try:
                    return json.loads(fragment)
                except json.JSONDecodeError:
                    return None
        return None