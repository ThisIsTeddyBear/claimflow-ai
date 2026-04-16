from __future__ import annotations

import json

from app.schemas.agent_outputs import ExplanationOutput
from app.services.llm_client import LLMClient
from app.services.prompt_registry import PromptRegistry


class ExplanationAgent:
    def __init__(
        self,
        llm_client: LLMClient | None = None,
        prompt_registry: PromptRegistry | None = None,
        prompt_version: str = "v1",
    ) -> None:
        self.llm_client = llm_client
        self.prompt_registry = prompt_registry
        self.prompt_version = prompt_version

    def generate(
        self,
        *,
        audience: str,
        decision: str,
        reasons: list[str],
        next_steps: list[str],
    ) -> ExplanationOutput:
        llm_output = self._run_llm(audience=audience, decision=decision, reasons=reasons, next_steps=next_steps)
        if llm_output is not None:
            return llm_output

        title = self._title_for(audience, decision)
        summary = self._summary_for(audience, decision, reasons)
        return ExplanationOutput(
            title=title,
            summary=summary,
            reasons=reasons,
            next_steps=next_steps,
            tone="professional",
        )

    def _run_llm(self, *, audience: str, decision: str, reasons: list[str], next_steps: list[str]) -> ExplanationOutput | None:
        if not self.llm_client or not self.prompt_registry:
            return None

        try:
            prompt = self.prompt_registry.load("explanation_agent", self.prompt_version)
        except FileNotFoundError:
            return None

        user_payload = {
            "audience": audience,
            "decision": decision,
            "reasons": reasons,
            "next_steps": next_steps,
            "contract": prompt.get("contract", {}),
        }
        user_prompt = (
            "Generate a concise communication draft for this claim decision. Return only JSON matching the contract.\n"
            f"{json.dumps(user_payload, ensure_ascii=True)}"
        )
        return self.llm_client.generate_structured(system=prompt["system"], user=user_prompt, schema=ExplanationOutput)

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
