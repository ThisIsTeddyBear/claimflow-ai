from __future__ import annotations

from app.schemas.agent_outputs import AdvisoryAgentOutput, AdvisoryFinding


class AdvisoryAgent:
    def run(
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