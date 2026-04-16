from __future__ import annotations

import json

from pydantic import BaseModel, Field

from app.schemas.agent_outputs import AdvisoryAgentOutput, AdvisoryFinding
from app.services.llm_client import LLMClient
from app.services.prompt_registry import PromptRegistry


class AdvisoryContractOutput(BaseModel):
    findings: list[AdvisoryFinding] = Field(default_factory=list)
    uncertainty_flags: list[str] = Field(default_factory=list)
    escalation_recommended: bool = False
    confidence: float = 0.0


class AdvisoryAgent:
    def __init__(
        self,
        llm_client: LLMClient | None = None,
        prompt_registry: PromptRegistry | None = None,
        prompt_version: str = "v1",
    ) -> None:
        self.llm_client = llm_client
        self.prompt_registry = prompt_registry
        self.prompt_version = prompt_version

    def run(
        self,
        *,
        claim_id: str,
        domain: str,
        extracted_fact_map: dict,
        validation_issues: list[dict],
        estimated_amount: float | None,
    ) -> AdvisoryAgentOutput:
        deterministic = self._run_deterministic(
            claim_id=claim_id,
            domain=domain,
            extracted_fact_map=extracted_fact_map,
            validation_issues=validation_issues,
            estimated_amount=estimated_amount,
        )
        llm_output = self._run_llm(
            domain=domain,
            extracted_fact_map=extracted_fact_map,
            validation_issues=validation_issues,
            estimated_amount=estimated_amount,
        )
        if llm_output is None:
            return deterministic

        merged_findings = list(deterministic.findings)
        finding_text = {entry.finding for entry in merged_findings}
        for finding in llm_output.findings:
            if finding.finding not in finding_text:
                merged_findings.append(finding)
                finding_text.add(finding.finding)

        uncertainty = deterministic.uncertainty_flags + [
            item for item in llm_output.uncertainty_flags if item not in deterministic.uncertainty_flags
        ]
        llm_escalation_allowed = self._should_accept_llm_escalation(
            deterministic_findings=deterministic.findings,
            llm_output=llm_output,
        )
        return AdvisoryAgentOutput(
            claim_id=claim_id,
            domain=domain,
            findings=merged_findings,
            uncertainty_flags=uncertainty,
            escalation_recommended=deterministic.escalation_recommended or llm_escalation_allowed,
            confidence=max(deterministic.confidence, llm_output.confidence),
        )

    @staticmethod
    def _should_accept_llm_escalation(*, deterministic_findings: list[AdvisoryFinding], llm_output: AdvisoryContractOutput) -> bool:
        if not llm_output.escalation_recommended:
            return False
        # Guardrail: only promote an LLM-only escalation when deterministic
        # signals already indicate a non-trivial concern to corroborate.
        if not deterministic_findings:
            return False
        return any(finding.confidence >= 0.85 for finding in llm_output.findings)

    def _run_deterministic(
        self,
        *,
        claim_id: str,
        domain: str,
        extracted_fact_map: dict,
        validation_issues: list[dict],
        estimated_amount: float | None,
    ) -> AdvisoryAgentOutput:
        findings: list[AdvisoryFinding] = []
        uncertainty_flags: list[str] = []
        escalation_recommended = False

        if domain == "auto":
            findings, uncertainty_flags, escalation_recommended = self._run_auto(extracted_fact_map, validation_issues, estimated_amount)
        else:
            findings, uncertainty_flags, escalation_recommended = self._run_healthcare(extracted_fact_map, validation_issues, estimated_amount)

        confidence = 0.8 if findings else 0.67
        return AdvisoryAgentOutput(
            claim_id=claim_id,
            domain=domain,
            findings=findings,
            uncertainty_flags=uncertainty_flags,
            escalation_recommended=escalation_recommended,
            confidence=confidence,
        )

    def _run_llm(
        self,
        *,
        domain: str,
        extracted_fact_map: dict,
        validation_issues: list[dict],
        estimated_amount: float | None,
    ) -> AdvisoryContractOutput | None:
        if not self.llm_client or not self.prompt_registry:
            return None

        prompt_name = "auto_liability_advisory_agent" if domain == "auto" else "healthcare_plausibility_advisory_agent"
        try:
            prompt = self.prompt_registry.load(prompt_name, self.prompt_version)
        except FileNotFoundError:
            return None

        user_payload = {
            "domain": domain,
            "extracted_fact_map": extracted_fact_map,
            "validation_issues": validation_issues,
            "estimated_amount": estimated_amount,
            "contract": prompt.get("contract", {}),
        }
        user_prompt = (
            "Produce domain advisory findings for this claim without making final adjudication decisions. "
            "Return only JSON matching the contract.\n"
            f"{json.dumps(user_payload, ensure_ascii=True)}"
        )
        return self.llm_client.generate_structured(system=prompt["system"], user=user_prompt, schema=AdvisoryContractOutput)

    def _run_auto(self, fact_map: dict, issues: list[dict], estimated_amount: float | None) -> tuple[list[AdvisoryFinding], list[str], bool]:
        findings: list[AdvisoryFinding] = []
        uncertainty: list[str] = []
        escalate = False

        if any(issue.get("category") == "narrative_conflict" for issue in issues):
            findings.append(
                AdvisoryFinding(
                    finding="Narrative inconsistency may indicate disputed liability; adjuster review recommended.",
                    confidence=0.83,
                    evidence_refs=[issue.get("id") for issue in issues if issue.get("category") == "narrative_conflict"],
                )
            )
            escalate = True

        injury = str(fact_map.get("injury_description", "")).lower()
        if injury and any(token in injury for token in {"severe", "hospital", "surgery"}):
            findings.append(
                AdvisoryFinding(
                    finding="Injury severity appears material and may warrant specialized bodily injury review.",
                    confidence=0.79,
                    evidence_refs=["injury_description"],
                )
            )
            uncertainty.append("Medical causation cannot be determined from current packet.")
            escalate = True

        if estimated_amount and estimated_amount > 25000:
            findings.append(
                AdvisoryFinding(
                    finding="High-value loss merits manual adjuster confirmation before settlement.",
                    confidence=0.85,
                    evidence_refs=["repair_estimate_amount"],
                )
            )
            escalate = True

        return findings, uncertainty, escalate

    def _run_healthcare(self, fact_map: dict, issues: list[dict], estimated_amount: float | None) -> tuple[list[AdvisoryFinding], list[str], bool]:
        findings: list[AdvisoryFinding] = []
        uncertainty: list[str] = []
        escalate = False

        diagnosis_codes = fact_map.get("diagnosis_codes") or []
        procedure_codes = fact_map.get("procedure_codes") or []

        if procedure_codes and not diagnosis_codes:
            findings.append(
                AdvisoryFinding(
                    finding="Procedure lines are present but diagnosis support is absent or unclear.",
                    confidence=0.87,
                    evidence_refs=["procedure_codes", "diagnosis_codes"],
                )
            )
            uncertainty.append("Medical necessity cannot be established without complete diagnosis documentation.")
            escalate = True

        if any(issue.get("severity") in {"high", "critical"} for issue in issues):
            findings.append(
                AdvisoryFinding(
                    finding="High-severity coding inconsistencies suggest manual coder review.",
                    confidence=0.82,
                    evidence_refs=[issue.get("id") for issue in issues if issue.get("severity") in {"high", "critical"}],
                )
            )
            escalate = True

        if estimated_amount and estimated_amount > 18000:
            findings.append(
                AdvisoryFinding(
                    finding="High billed amount may require clinical documentation review.",
                    confidence=0.78,
                    evidence_refs=["billed_amount"],
                )
            )
            uncertainty.append("Clinical appropriateness not conclusively established from current records.")
            escalate = True

        return findings, uncertainty, escalate
