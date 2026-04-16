from __future__ import annotations

import json
from collections import defaultdict

from app.schemas.agent_outputs import ContradictionAgentOutput, ContradictionIssue
from app.services.llm_client import LLMClient
from app.services.prompt_registry import PromptRegistry


class ContradictionAgent:
    def __init__(
        self,
        llm_client: LLMClient | None = None,
        prompt_registry: PromptRegistry | None = None,
        prompt_version: str = "v1",
    ) -> None:
        self.llm_client = llm_client
        self.prompt_registry = prompt_registry
        self.prompt_version = prompt_version

    def run(self, fact_rows: list[dict]) -> ContradictionAgentOutput:
        deterministic = self._run_deterministic(fact_rows)
        llm_output = self._run_llm(fact_rows)
        if llm_output is None:
            return deterministic

        merged_issues = list(deterministic.issues)
        existing_keys = {f"{issue.category}:{issue.description}" for issue in merged_issues}
        for issue in llm_output.issues:
            key = f"{issue.category}:{issue.description}"
            if key not in existing_keys:
                merged_issues.append(issue)
                existing_keys.add(key)

        return ContradictionAgentOutput(
            issues=merged_issues,
            requires_human_review=deterministic.requires_human_review or llm_output.requires_human_review,
            confidence=max(deterministic.confidence, llm_output.confidence),
        )

    def _run_deterministic(self, fact_rows: list[dict]) -> ContradictionAgentOutput:
        grouped: dict[str, list[dict]] = defaultdict(list)
        for fact in fact_rows:
            grouped[fact["key"]].append(fact)

        issues: list[ContradictionIssue] = []
        for key, values in grouped.items():
            unique_values = {self._normalize_value(v["value"]) for v in values if v.get("value") is not None}
            if len(unique_values) <= 1:
                continue

            severity = "high" if key in {"incident_date", "date_of_service", "member_id", "driver_name", "billed_amount"} else "medium"
            category = self._infer_category(key)
            issue = ContradictionIssue(
                category=category,
                description=f"Conflicting values for {key}: {sorted(unique_values)}",
                severity=severity,
                source_document_ids=[v.get("source_document_id") for v in values if v.get("source_document_id")],
                resolvable_with_more_docs=True,
                confidence=0.82,
            )
            issues.append(issue)

        requires_human = any(issue.severity in {"high", "critical"} for issue in issues)
        confidence = 0.88 if issues else 0.93
        return ContradictionAgentOutput(issues=issues, requires_human_review=requires_human, confidence=confidence)

    def _run_llm(self, fact_rows: list[dict]) -> ContradictionAgentOutput | None:
        if not self.llm_client or not self.prompt_registry:
            return None

        try:
            prompt = self.prompt_registry.load("contradiction_agent", self.prompt_version)
        except FileNotFoundError:
            return None

        user_payload = {
            "facts": fact_rows,
            "contract": prompt.get("contract", {}),
        }
        user_prompt = (
            "Analyze these extracted facts for contradictions across documents. Return only JSON matching the contract.\n"
            f"{json.dumps(user_payload, ensure_ascii=True)}"
        )
        return self.llm_client.generate_structured(system=prompt["system"], user=user_prompt, schema=ContradictionAgentOutput)

    @staticmethod
    def _normalize_value(value: object) -> str:
        if isinstance(value, (list, tuple, set)):
            return ",".join(sorted(str(v) for v in value))
        return str(value).strip().lower()

    @staticmethod
    def _infer_category(key: str) -> str:
        if "date" in key:
            return "date_mismatch"
        if any(token in key for token in {"amount", "billed", "estimate"}):
            return "amount_conflict"
        if any(token in key for token in {"member", "driver", "claimant", "provider"}):
            return "identity_mismatch"
        if "narrative" in key:
            return "narrative_conflict"
        return "other"
