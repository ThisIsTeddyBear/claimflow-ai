from __future__ import annotations

import hashlib
import re
from datetime import date, datetime
from pathlib import Path


DATE_PATTERNS = [r"\b(\d{4}-\d{2}-\d{2})\b", r"\b(\d{2}/\d{2}/\d{4})\b"]
AMOUNT_PATTERN = re.compile(r"\$?\s*((?:[0-9]{1,3}(?:,[0-9]{3})+|[0-9]+)(?:\.[0-9]{1,2})?)")


def normalize_text(text: str) -> str:
    sanitized = text.replace("\x00", " ")
    return re.sub(r"\s+", " ", sanitized).strip()


def parse_date(value: str | None) -> date | None:
    if not value:
        return None
    value = value.strip()
    for fmt in ("%Y-%m-%d", "%m/%d/%Y", "%Y/%m/%d"):
        try:
            return datetime.strptime(value, fmt).date()
        except ValueError:
            continue
    return None


def extract_first_date(text: str) -> date | None:
    for pattern in DATE_PATTERNS:
        match = re.search(pattern, text)
        if match:
            return parse_date(match.group(1))
    return None


def extract_amount(text: str) -> float | None:
    values: list[float] = []
    for match in AMOUNT_PATTERN.finditer(text):
        candidate = match.group(1)
        start, end = match.span(1)
        if _is_date_component(text, start, end):
            continue
        normalized = candidate.replace(",", "")
        try:
            values.append(float(normalized))
        except ValueError:
            continue
    if not values:
        return None
    return max(values)


def _is_date_component(text: str, start: int, end: int) -> bool:
    prev_char = text[start - 1] if start > 0 else ""
    prev_prev_char = text[start - 2] if start > 1 else ""
    next_char = text[end] if end < len(text) else ""
    next_next_char = text[end + 1] if end + 1 < len(text) else ""

    has_date_prefix = prev_char in {"-", "/"} and prev_prev_char.isdigit()
    has_date_suffix = next_char in {"-", "/"} and next_next_char.isdigit()
    return has_date_prefix or has_date_suffix


def sha256_text(content: str) -> str:
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


def sha256_file(path: str | Path) -> str:
    file_path = Path(path)
    digest = hashlib.sha256()
    with file_path.open("rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            digest.update(chunk)
    return digest.hexdigest()


def parse_key_value_lines(text: str) -> dict[str, str]:
    result: dict[str, str] = {}
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line or ":" not in line:
            continue
        key, value = line.split(":", 1)
        result[key.strip().lower().replace(" ", "_")] = value.strip()
    return result
