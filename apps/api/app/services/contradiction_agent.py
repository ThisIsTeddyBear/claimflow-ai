from __future__ import annotations

from collections import defaultdict

from app.schemas.agent_outputs import ContradictionAgentOutput, ContradictionIssue


class ContradictionAgent:
    def run(self, fact_rows: list[dict]) -> ContradictionAgentOutput:
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