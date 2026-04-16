from __future__ import annotations

from collections import defaultdict

from app.schemas.agent_outputs import ContradictionIssue
from app.services.contradiction_agent import ContradictionAgent


class ValidationService:
    def __init__(self, contradiction_agent: ContradictionAgent | None = None) -> None:
        self.contradiction_agent = contradiction_agent or ContradictionAgent()

    def validate(self, *, domain: str, extracted_facts: list[dict], claim_payload: dict) -> list[dict]:
        issues: list[dict] = []

        contradiction_output = self.contradiction_agent.run(extracted_facts)
        issues.extend(issue.model_dump() for issue in contradiction_output.issues)

        fact_map = self._to_fact_map(extracted_facts)
        issues.extend(self._required_field_checks(domain, fact_map))
        issues.extend(self._domain_consistency_checks(domain, fact_map, claim_payload))
        return issues

    @staticmethod
    def _to_fact_map(extracted_facts: list[dict]) -> dict:
        grouped: dict[str, list[dict]] = defaultdict(list)
        for fact in extracted_facts:
            grouped[fact["key"]].append(fact)

        fact_map: dict[str, object] = {}
        for key, rows in grouped.items():
            ordered = sorted(rows, key=lambda row: row.get("confidence", 0), reverse=True)
            fact_map[key] = ordered[0]["value"]
        return fact_map

    @staticmethod
    def _required_field_checks(domain: str, fact_map: dict) -> list[dict]:
        required = {
            "auto": ["incident_date", "driver_name", "repair_estimate_amount"],
            "healthcare": ["member_id", "date_of_service", "procedure_codes"],
        }[domain]

        issues: list[dict] = []
        for field in required:
            if not fact_map.get(field):
                issues.append(
                    {
                        "category": "missing_required_field",
                        "field": field,
                        "description": f"Required field {field} was not extracted from documents.",
                        "severity": "high",
                        "source_document_ids": [],
                        "confidence": 0.95,
                        "resolvable_with_more_docs": True,
                    }
                )
        return issues

    @staticmethod
    def _domain_consistency_checks(domain: str, fact_map: dict, claim_payload: dict) -> list[dict]:
        issues: list[dict] = []

        if domain == "healthcare":
            diagnosis = fact_map.get("diagnosis_codes") or []
            procedures = fact_map.get("procedure_codes") or []
            if procedures and not diagnosis:
                issues.append(
                    {
                        "category": "coding_consistency",
                        "field": "diagnosis_codes",
                        "description": "Procedure codes present without diagnosis support.",
                        "severity": "high",
                        "source_document_ids": [],
                        "confidence": 0.88,
                        "resolvable_with_more_docs": True,
                    }
                )

        if domain == "auto":
            injury = str(fact_map.get("injury_description") or "").lower()
            estimate = fact_map.get("repair_estimate_amount")
            if isinstance(estimate, (int, float)) and estimate < 2000 and any(word in injury for word in {"severe", "hospital"}):
                issues.append(
                    {
                        "category": "narrative_conflict",
                        "field": "injury_description",
                        "description": "Claimed severe injury appears inconsistent with low vehicle damage estimate.",
                        "severity": "medium",
                        "source_document_ids": [],
                        "confidence": 0.74,
                        "resolvable_with_more_docs": True,
                    }
                )

        return issues
