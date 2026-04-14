from __future__ import annotations

from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

from .utils import normalize_text


class ParsedDocument(BaseModel):
    text: str
    metadata: dict[str, Any] = Field(default_factory=dict)


class DocumentParser:
    def parse(self, file_path: str) -> ParsedDocument:
        path = Path(file_path)
        suffix = path.suffix.lower()

        if suffix in {".txt", ".md", ".csv", ".json"}:
            text = path.read_text(encoding="utf-8", errors="ignore")
            return ParsedDocument(text=normalize_text(text), metadata={"parser": "text", "ocr_used": False})

        if suffix == ".pdf":
            return self._parse_pdf(path)

        binary_text = path.read_bytes().decode("utf-8", errors="ignore")
        return ParsedDocument(
            text=normalize_text(binary_text),
            metadata={"parser": "binary-fallback", "warning": "Unsupported extension, used byte decode fallback"},
        )

    def _parse_pdf(self, path: Path) -> ParsedDocument:
        try:
            from pypdf import PdfReader

            reader = PdfReader(str(path))
            pages = [page.extract_text() or "" for page in reader.pages]
            text = "\n".join(pages)
            return ParsedDocument(
                text=normalize_text(text),
                metadata={"parser": "pypdf", "page_count": len(reader.pages), "ocr_used": False},
            )
        except Exception as exc:  # pragma: no cover - environment dependent
            return ParsedDocument(
                text="",
                metadata={"parser": "pdf-unavailable", "ocr_used": False, "warning": str(exc)},
            )