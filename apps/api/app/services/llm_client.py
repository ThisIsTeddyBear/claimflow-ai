from __future__ import annotations

import json
import re
from urllib.parse import urlparse
from typing import Any, Iterable, TypeVar

import requests
from requests import RequestException
from pydantic import BaseModel, ValidationError

from app.config import Settings

T = TypeVar("T", bound=BaseModel)


class LLMClient:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def generate_structured(self, *, system: str, user: str, schema: type[T]) -> T | None:
        if not self.settings.enable_live_llm:
            return None

        provider = (self.settings.llm_provider or "openai-compatible").strip().lower()
        if provider == "ollama":
            return self._generate_structured_ollama(system=system, user=user, schema=schema)
        return self._generate_structured_openai_compatible(system=system, user=user, schema=schema)

    def _generate_structured_openai_compatible(self, *, system: str, user: str, schema: type[T]) -> T | None:
        if not self.settings.llm_api_key:
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
            try:
                response = requests.post(
                    f"{self.settings.llm_base_url.rstrip('/')}/chat/completions",
                    headers=headers,
                    json=payload,
                    timeout=self.settings.llm_timeout_seconds,
                )
                response.raise_for_status()
            except RequestException:
                continue
            parsed = self._parse_openai_response(response.json())
            if parsed is None:
                continue
            validated = self._validate_with_unwrap(schema=schema, parsed=parsed)
            if validated is not None:
                return validated
            else:
                continue
        return None

    def _generate_structured_ollama(self, *, system: str, user: str, schema: type[T]) -> T | None:
        url = self._resolve_ollama_chat_url(self.settings.llm_base_url)
        headers = {"Content-Type": "application/json"}
        if self.settings.llm_api_key:
            headers["Authorization"] = f"Bearer {self.settings.llm_api_key}"

        format_variants: list[Any] = [schema.model_json_schema(), "json"]
        for format_spec in format_variants:
            payload = {
                "model": self.settings.llm_model,
                "messages": [
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
                "stream": False,
                "format": format_spec,
                "options": {"temperature": 0, "num_predict": 512},
            }

            for _ in range(2):
                try:
                    response = requests.post(
                        url,
                        headers=headers,
                        json=payload,
                        timeout=self.settings.llm_timeout_seconds,
                    )
                    response.raise_for_status()
                except RequestException:
                    continue
                parsed = self._parse_ollama_response(response.json())
                if parsed is None:
                    continue
                validated = self._validate_with_unwrap(schema=schema, parsed=parsed)
                if validated is not None:
                    return validated
                else:
                    continue
        return None

    @staticmethod
    def _parse_openai_response(raw: dict[str, Any]) -> dict[str, Any] | None:
        content = raw.get("choices", [{}])[0].get("message", {}).get("content")
        if not content:
            return None
        if isinstance(content, dict):
            return content
        return LLMClient._extract_json_object(content)

    @classmethod
    def _parse_ollama_response(cls, raw: dict[str, Any]) -> dict[str, Any] | None:
        message = raw.get("message", {})
        content = message.get("content")
        if isinstance(content, dict):
            return content
        if not content:
            return None
        return cls._extract_json_object(content)

    @staticmethod
    def _extract_json_object(content: str) -> dict[str, Any] | None:
        text = str(content).strip()
        if not text:
            return None

        text = LLMClient._strip_markdown_fences(text)
        try:
            loaded = json.loads(text)
            if isinstance(loaded, dict):
                return loaded
        except json.JSONDecodeError:
            pass

        start = text.find("{")
        end = text.rfind("}")
        if start >= 0 and end > start:
            fragment = text[start : end + 1]
            try:
                loaded = json.loads(fragment)
                if isinstance(loaded, dict):
                    return loaded
            except json.JSONDecodeError:
                return None
        return None

    @staticmethod
    def _strip_markdown_fences(text: str) -> str:
        fenced = re.match(r"^\s*```(?:json)?\s*(.*?)\s*```\s*$", text, flags=re.IGNORECASE | re.DOTALL)
        if fenced:
            return fenced.group(1).strip()
        return text

    @staticmethod
    def _candidate_payloads(parsed: dict[str, Any]) -> list[dict[str, Any]]:
        candidates: list[dict[str, Any]] = [parsed]
        if len(parsed) == 1:
            only_value = next(iter(parsed.values()))
            if isinstance(only_value, dict):
                candidates.append(only_value)
        for key in ("data", "result", "output", "response", "status", "contract"):
            nested = parsed.get(key)
            if isinstance(nested, dict):
                candidates.append(nested)
        candidates.extend(LLMClient._collect_nested_dicts(parsed, max_depth=3))
        return LLMClient._dedupe_dict_candidates(candidates)

    @staticmethod
    def _collect_nested_dicts(value: Any, *, max_depth: int) -> list[dict[str, Any]]:
        if max_depth < 0:
            return []
        collected: list[dict[str, Any]] = []
        if isinstance(value, dict):
            for child in value.values():
                if isinstance(child, dict):
                    collected.append(child)
                    collected.extend(LLMClient._collect_nested_dicts(child, max_depth=max_depth - 1))
                elif isinstance(child, list):
                    collected.extend(LLMClient._collect_nested_dicts(child, max_depth=max_depth - 1))
        elif isinstance(value, list):
            for item in value:
                if isinstance(item, dict):
                    collected.append(item)
                    collected.extend(LLMClient._collect_nested_dicts(item, max_depth=max_depth - 1))
                elif isinstance(item, list):
                    collected.extend(LLMClient._collect_nested_dicts(item, max_depth=max_depth - 1))
        return collected

    @staticmethod
    def _dedupe_dict_candidates(candidates: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
        deduped: list[dict[str, Any]] = []
        seen: set[str] = set()
        for candidate in candidates:
            try:
                key = json.dumps(candidate, sort_keys=True, default=str)
            except TypeError:
                key = str(candidate)
            if key in seen:
                continue
            seen.add(key)
            deduped.append(candidate)
        return deduped

    @staticmethod
    def _normalize_candidate(candidate: dict[str, Any]) -> dict[str, Any]:
        normalized = dict(candidate)
        entities = normalized.get("entities")
        if isinstance(entities, list):
            transformed: dict[str, dict[str, Any]] = {}
            for entry in entities:
                if not isinstance(entry, dict):
                    continue
                raw_key = entry.get("field") or entry.get("key") or entry.get("name")
                if not raw_key:
                    continue
                key = str(raw_key).strip().lower().replace(" ", "_")
                transformed[key] = {
                    "value": entry.get("value"),
                    "confidence": float(entry.get("confidence", 0.7) or 0.7),
                    "source_excerpt": entry.get("source_excerpt"),
                }
            if transformed:
                normalized["entities"] = transformed
        return normalized

    @classmethod
    def _validate_with_unwrap(cls, *, schema: type[T], parsed: dict[str, Any]) -> T | None:
        for candidate in cls._candidate_payloads(parsed):
            normalized = cls._normalize_candidate(candidate)
            try:
                return schema.model_validate(normalized)
            except ValidationError:
                continue
        return None

    @staticmethod
    def _resolve_ollama_chat_url(base_url: str) -> str:
        base = base_url.rstrip("/")
        parsed = urlparse(base)
        path = parsed.path.rstrip("/")

        if path.endswith("/api"):
            return f"{base}/chat"
        if path.endswith("/api/chat"):
            return base
        if path == "":
            return f"{base}/api/chat"
        return f"{base}/chat"
