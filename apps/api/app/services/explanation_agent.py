from __future__ import annotations

from app.schemas.agent_outputs import ExplanationOutput


class ExplanationAgent:
    def generate(
        self,
        *,
        audience: str,
        decision: str,
        reasons: list[str],
        next_steps: list[str],
    ) -> ExplanationOutput:
        title = self._title_for(audience, decision)
        summary = self._summary_for(audience, decision, reasons)
        return ExplanationOutput(
            title=title,
            summary=summary,
            reasons=reasons,
            next_steps=next_steps,
            tone="professional",
        )

    @staticmethod
    def _title_for(audience: str, decision: str) -> str:
        audience_title = {
            "internal": "Internal Adjudication Summary",
            "claimant": "Claim Status Update",
            "provider": "Claim Adjudication Notice",
            "adjuster": "Adjuster Handoff Note",
        }.get(audience, "Claim Update")
        return f"{audience_title}: {decision.upper()}"

    @staticmethod
    def _summary_for(audience: str, decision: str, reasons: list[str]) -> str:
        reason_line = reasons[0] if reasons else "No additional details available"
        if audience == "internal":
            return f"Deterministic decision outcome is {decision}. Primary rationale: {reason_line}."
        if audience in {"claimant", "provider"}:
            return f"Your claim status is {decision}. Main reason: {reason_line}."
        if audience == "adjuster":
            return f"Case routed with decision state {decision}. Priority reason: {reason_line}."
        return f"Decision {decision}: {reason_line}."