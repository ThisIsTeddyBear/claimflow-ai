from app.schemas.agent_outputs import ExtractedEntity
from app.services.extraction_agent import ExtractionAgent, ExtractionLLMOutput


class _FakePromptRegistry:
    def load(self, prompt_name: str, version: str = "v1") -> dict:
        return {"system": "stub", "contract": {}}


class _FakeLLMClient:
    def __init__(self, output: dict) -> None:
        self.output = output

    def generate_structured(self, *, system: str, user: str, schema):  # noqa: ANN001
        return schema.model_validate(self.output)


def test_extraction_llm_output_without_document_type_is_normalized() -> None:
    llm_output = {
        "entities": {
            "member_id": {
                "value": "HLT-2001",
                "confidence": 0.95,
                "source_excerpt": "Member ID: HLT-2001",
            }
        },
        "ambiguities": [],
        "doc_summary": "health claim form",
        "confidence": 0.91,
    }
    agent = ExtractionAgent(
        llm_client=_FakeLLMClient(llm_output),
        prompt_registry=_FakePromptRegistry(),
        prompt_version="v1",
    )

    result = agent.run(
        domain="healthcare",
        filename="claim_form.txt",
        document_type="claim_form",
        text="Member ID: HLT-2001",
    )

    assert result.document_type == "claim_form"
    assert "member_id" in result.entities
    assert result.entities["member_id"] == ExtractedEntity(
        value="HLT-2001",
        confidence=0.95,
        source_excerpt="Member ID: HLT-2001",
    )
