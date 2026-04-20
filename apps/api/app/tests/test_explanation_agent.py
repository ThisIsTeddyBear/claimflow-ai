from app.schemas.agent_outputs import ExplanationOutput
from app.services.explanation_agent import ExplanationAgent


SAMPLE_HEALTHCARE_CONTEXT = {
    "claim_number": "SCN-HEALTH01",
    "domain": "healthcare",
    "subtype": "professional",
    "claimant_name": "Emma Lewis",
    "policy_or_member_id": "HLT-2001",
    "member_id": "HLT-2001",
    "provider_id": "PRV-301",
    "incident_or_service_date": "2025-04-03",
    "date_of_service": "2025-04-03",
    "estimated_amount": 320,
    "billed_amount": 320,
    "units": 1,
    "diagnosis_codes": ["Z00.00"],
    "procedure_codes": ["99213"],
    "corrected_claim": True,
    "document_types": ["claim_form", "billing_statement", "coding_summary"],
    "reviewer_queue": None,
}


class DummyLLMClient:
    def __init__(self, output: ExplanationOutput) -> None:
        self.output = output

    def generate_structured(self, **kwargs) -> ExplanationOutput:
        return self.output


class DummyPromptRegistry:
    def load(self, name: str, version: str) -> dict:
        return {
            "system": "ignored",
            "contract": {
                "title": "string",
                "summary": "string",
                "reasons": ["string"],
                "next_steps": ["string"],
                "tone": "string",
            },
        }


def test_grounded_healthcare_approve_provider_draft_uses_claim_facts() -> None:
    draft = ExplanationAgent().generate(
        audience="provider",
        decision="approve",
        reasons=["Member active, procedure covered, and benefits checks passed."],
        next_steps=["Proceed to settlement readiness"],
        claim_context=SAMPLE_HEALTHCARE_CONTEXT,
    )

    combined = " ".join([draft.title, draft.summary, *draft.reasons, *draft.next_steps]).lower()
    assert "hlt-2001" in combined
    assert "prv-301" in combined
    assert "2025-04-03" in " ".join([draft.title, draft.summary, *draft.reasons, *draft.next_steps])
    assert "$320" in combined
    assert "99213" in combined
    assert "z00.00" in combined
    assert "corrected claim" in combined
    assert "high-value" not in combined
    assert "escalat" not in combined
    assert "settlement readiness" not in combined
    assert "[code]" not in combined


def test_pending_prior_auth_next_steps_are_specific_and_grounded() -> None:
    context = {
        **SAMPLE_HEALTHCARE_CONTEXT,
        "subtype": "outpatient",
        "billed_amount": 16000,
        "estimated_amount": 16000,
        "procedure_codes": ["29881"],
        "corrected_claim": False,
    }
    draft = ExplanationAgent().generate(
        audience="provider",
        decision="pend",
        reasons=[
            "Coverage outcome is not a deterministic rejection, but case needs additional review.",
            "Prior authorization required for 29881.",
        ],
        next_steps=["Request additional documentation"],
        claim_context=context,
    )

    assert draft.next_steps == ["Please submit prior authorization support for 29881."]


def test_llm_output_with_placeholders_falls_back_to_grounded_deterministic_copy() -> None:
    llm_output = ExplanationOutput(
        title="Claim [NUMBER]",
        summary="Use [LINK] in [SYSTEM] for the high-value review on YYYY-MM-DD.",
        reasons=["See [SECTION] and audit log XXXXX."],
        next_steps=["Open the portal at https://example.test."],
        tone="professional",
    )
    agent = ExplanationAgent(
        llm_client=DummyLLMClient(llm_output),
        prompt_registry=DummyPromptRegistry(),
    )

    draft = agent.generate(
        audience="provider",
        decision="approve",
        reasons=["Member active, procedure covered, and benefits checks passed."],
        next_steps=["Proceed to settlement readiness"],
        claim_context=SAMPLE_HEALTHCARE_CONTEXT,
    )

    combined = " ".join([draft.title, draft.summary, *draft.reasons, *draft.next_steps]).lower()
    assert "[number]" not in combined
    assert "xxxxx" not in combined
    assert "portal" not in combined
    assert "high-value" not in combined
    assert "settlement readiness" not in combined
    assert "hlt-2001" in combined
