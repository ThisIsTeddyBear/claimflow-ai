from app.schemas.agent_outputs import IntakeAgentOutput
from app.services.intake_agent import IntakeAgent


class _FakePromptRegistry:
    def load(self, prompt_name: str, version: str = "v1") -> dict:
        return {"system": "stub", "contract": {}}


class _FakeLLMClient:
    def __init__(self, output: IntakeAgentOutput) -> None:
        self.output = output

    def generate_structured(self, *, system: str, user: str, schema):  # noqa: ANN001
        return self.output


def test_intake_ignores_llm_extra_required_docs_for_blocking() -> None:
    llm_output = IntakeAgentOutput(
        claim_domain="auto",
        claim_subtype="own_damage",
        required_docs=[
            "claim_form",
            "accident_narrative",
            "repair_estimate",
            "damage_photos_or_video",
            "vehicle_registration_or_title",
        ],
        missing_docs=["damage_photos_or_video", "vehicle_registration_or_title"],
        completeness_score=0.6,
        intake_notes=["LLM asked for additional packet docs."],
        confidence=0.8,
    )
    agent = IntakeAgent(
        llm_client=_FakeLLMClient(llm_output),
        prompt_registry=_FakePromptRegistry(),
        prompt_version="v1",
    )

    result = agent.run(
        domain="auto",
        subtype="own_damage",
        documents=[
            {"document_type": "claim_form", "filename": "claim_form.txt"},
            {"document_type": "accident_narrative", "filename": "accident_narrative.txt"},
            {"document_type": "repair_estimate", "filename": "repair_estimate.txt"},
        ],
        claim_payload={"injury_involved": False},
    )

    assert result.required_docs == ["claim_form", "accident_narrative", "repair_estimate"]
    assert result.missing_docs == []
    assert result.completeness_score == 1.0
    assert any("non-blocking" in note.lower() for note in result.intake_notes)
