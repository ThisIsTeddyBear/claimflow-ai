from app.schemas.agent_outputs import AdvisoryFinding
from app.services.advisory_agent import AdvisoryAgent, AdvisoryContractOutput


def test_llm_escalation_guardrail_blocks_without_deterministic_signal() -> None:
    llm_output = AdvisoryContractOutput(
        findings=[AdvisoryFinding(finding="Potential concern", confidence=0.93, evidence_refs=["x"])],
        uncertainty_flags=[],
        escalation_recommended=True,
        confidence=0.9,
    )
    allowed = AdvisoryAgent._should_accept_llm_escalation(deterministic_findings=[], llm_output=llm_output)
    assert allowed is False


def test_llm_escalation_guardrail_allows_when_corroborated() -> None:
    llm_output = AdvisoryContractOutput(
        findings=[AdvisoryFinding(finding="Potential concern", confidence=0.9, evidence_refs=["x"])],
        uncertainty_flags=[],
        escalation_recommended=True,
        confidence=0.9,
    )
    deterministic_findings = [AdvisoryFinding(finding="Known issue", confidence=0.8, evidence_refs=["d1"])]
    allowed = AdvisoryAgent._should_accept_llm_escalation(
        deterministic_findings=deterministic_findings,
        llm_output=llm_output,
    )
    assert allowed is True
