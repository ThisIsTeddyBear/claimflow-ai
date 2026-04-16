from pydantic import BaseModel

from app.config import get_settings
from app.schemas.agent_outputs import ExtractionAgentOutput
from app.services.llm_client import LLMClient


class ProbeSchema(BaseModel):
    ok: bool
    note: str


def test_extract_json_object_handles_markdown_fences() -> None:
    raw = """```json
{
  "ok": true,
  "note": "probe"
}
```"""
    parsed = LLMClient._extract_json_object(raw)
    assert parsed == {"ok": True, "note": "probe"}


def test_validate_with_unwrap_accepts_single_wrapper_object() -> None:
    wrapped = {"status": {"ok": True, "note": "probe"}}
    validated = LLMClient._validate_with_unwrap(schema=ProbeSchema, parsed=wrapped)
    assert validated is not None
    assert validated.ok is True
    assert validated.note == "probe"


def test_validate_with_unwrap_accepts_contract_nested_object() -> None:
    wrapped = {
        "domain": "auto",
        "contract": {
            "ok": True,
            "note": "probe",
        },
    }
    validated = LLMClient._validate_with_unwrap(schema=ProbeSchema, parsed=wrapped)
    assert validated is not None
    assert validated.ok is True
    assert validated.note == "probe"


def test_validate_with_unwrap_normalizes_list_entities_for_extraction_schema() -> None:
    parsed = {
        "contract": {
            "document_type": "claim_form",
            "entities": [
                {
                    "field": "incident_date",
                    "value": "2025-03-14",
                    "confidence": 0.95,
                    "source_excerpt": "Incident Date: 2025-03-14",
                }
            ],
            "ambiguities": [],
            "doc_summary": "summary",
            "confidence": 0.9,
        }
    }
    validated = LLMClient._validate_with_unwrap(schema=ExtractionAgentOutput, parsed=parsed)
    assert validated is not None
    assert validated.document_type == "claim_form"
    assert "incident_date" in validated.entities
    assert validated.entities["incident_date"].value == "2025-03-14"


def test_resolve_ollama_chat_url_with_api_path() -> None:
    assert LLMClient._resolve_ollama_chat_url("https://ollama.com/api") == "https://ollama.com/api/chat"


def test_generate_structured_returns_none_when_live_llm_disabled() -> None:
    settings = get_settings().model_copy(update={"enable_live_llm": False})
    result = LLMClient(settings).generate_structured(
        system="ignored",
        user='{"ok": true, "note": "probe"}',
        schema=ProbeSchema,
    )
    assert result is None
