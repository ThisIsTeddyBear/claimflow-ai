from __future__ import annotations

import json
from datetime import date
from pathlib import Path
from typing import Any

from app.services.utils import parse_date


class CoverageService:
    def __init__(self, data_dir: str) -> None:
        self.data_dir = Path(data_dir)

    def evaluate(self, *, domain: str, claim: Any, fact_map: dict[str, Any]) -> dict[str, Any]:
        if domain == "auto":
            return self._evaluate_auto(claim, fact_map)
        return self._evaluate_healthcare(claim, fact_map)

    def _evaluate_auto(self, claim: Any, fact_map: dict[str, Any]) -> dict[str, Any]:
        policies = self._load_json(self.data_dir / "synthetic_reference" / "auto_policies" / "policies.json")
        policy_id = claim.policy_or_member_id or fact_map.get("policy_number")
        policy = next((record for record in policies if record.get("policy_number") == policy_id), None)

        if policy is None:
            return {
                "is_covered": False,
                "coverage_type": None,
                "hard_fail": True,
                "reasons": ["Policy record not found for claim."],
                "deductible": None,
                "benefit_notes": [],
                "confidence": 0.95,
            }

        incident_date = claim.incident_or_service_date or parse_date(str(fact_map.get("incident_date")))
        active_from = parse_date(policy.get("active_from"))
        active_to = parse_date(policy.get("active_to"))

        if incident_date and active_from and active_to and not (active_from <= incident_date <= active_to):
            return {
                "is_covered": False,
                "coverage_type": None,
                "hard_fail": True,
                "reasons": ["Policy inactive on incident date."],
                "deductible": policy.get("deductible"),
                "benefit_notes": [f"Policy window: {active_from} to {active_to}"],
                "confidence": 0.97,
            }

        driver_name = (fact_map.get("driver_name") or claim.claimant_name or "").strip().lower()
        excluded = [name.lower() for name in policy.get("excluded_drivers", [])]
        if driver_name and driver_name in excluded:
            return {
                "is_covered": False,
                "coverage_type": "collision",
                "hard_fail": True,
                "reasons": ["Driver is listed as excluded under policy."],
                "deductible": policy.get("deductible"),
                "benefit_notes": [],
                "confidence": 0.95,
            }

        use_type = str(fact_map.get("use_type") or claim.claim_payload.get("use_type") or "personal").lower()
        if use_type in {"rideshare", "commercial"} and use_type in set(policy.get("exclusions", [])):
            return {
                "is_covered": False,
                "coverage_type": "collision",
                "hard_fail": True,
                "reasons": [f"Excluded use type: {use_type}."],
                "deductible": policy.get("deductible"),
                "benefit_notes": [],
                "confidence": 0.94,
            }

        if not policy.get("coverages", {}).get("collision", False):
            return {
                "is_covered": False,
                "coverage_type": "collision",
                "hard_fail": True,
                "reasons": ["Collision coverage is absent for this policy."],
                "deductible": policy.get("deductible"),
                "benefit_notes": [],
                "confidence": 0.95,
            }

        return {
            "is_covered": True,
            "coverage_type": "collision",
            "hard_fail": False,
            "reasons": ["Policy active and collision coverage available."],
            "deductible": policy.get("deductible"),
            "benefit_notes": ["Proceeding within automated adjudication threshold."],
            "confidence": 0.88,
        }

    def _evaluate_healthcare(self, claim: Any, fact_map: dict[str, Any]) -> dict[str, Any]:
        members = self._load_json(self.data_dir / "synthetic_reference" / "healthcare_plans" / "members.json")
        plans = self._load_json(self.data_dir / "synthetic_reference" / "healthcare_plans" / "plans.json")
        providers = self._load_json(self.data_dir / "synthetic_reference" / "healthcare_plans" / "providers.json")

        member_id = claim.policy_or_member_id or fact_map.get("member_id")
        member = next((record for record in members if record.get("member_id") == member_id), None)
        if member is None:
            return {
                "is_covered": False,
                "coverage_type": None,
                "hard_fail": True,
                "reasons": ["Member record not found."],
                "deductible": None,
                "benefit_notes": [],
                "confidence": 0.97,
            }

        dos = claim.incident_or_service_date or parse_date(str(fact_map.get("date_of_service")))
        active_from = parse_date(member.get("active_from"))
        active_to = parse_date(member.get("active_to"))
        if dos and active_from and active_to and not (active_from <= dos <= active_to):
            return {
                "is_covered": False,
                "coverage_type": "medical",
                "hard_fail": True,
                "reasons": ["Member inactive on date of service."],
                "deductible": None,
                "benefit_notes": [f"Eligibility window: {active_from} to {active_to}"],
                "confidence": 0.98,
            }

        plan = next((record for record in plans if record.get("plan_id") == member.get("plan_id")), None)
        if plan is None:
            return {
                "is_covered": False,
                "coverage_type": "medical",
                "hard_fail": True,
                "reasons": ["Plan definition missing for member."],
                "deductible": None,
                "benefit_notes": [],
                "confidence": 0.9,
            }

        procedure_codes = fact_map.get("procedure_codes") or []
        if isinstance(procedure_codes, str):
            procedure_codes = [procedure_codes]

        excluded_match = [code for code in procedure_codes if code in plan.get("excluded_procedures", [])]
        if excluded_match:
            return {
                "is_covered": False,
                "coverage_type": "medical",
                "hard_fail": True,
                "reasons": [f"Excluded procedure code(s): {', '.join(excluded_match)}."],
                "deductible": None,
                "benefit_notes": [],
                "confidence": 0.96,
            }

        provider_id = fact_map.get("provider_id")
        provider = next((record for record in providers if record.get("provider_id") == provider_id), None)
        if provider and provider.get("network_status") == "out_of_network" and not claim.claim_payload.get("emergency_exception"):
            return {
                "is_covered": None,
                "coverage_type": "medical",
                "hard_fail": False,
                "reasons": ["Out-of-network provider without emergency exception."],
                "deductible": None,
                "benefit_notes": ["Route to reviewer for OON policy handling."],
                "confidence": 0.84,
            }

        required_pa = set(plan.get("requires_prior_auth", []))
        missing_pa_for = [code for code in procedure_codes if code in required_pa and not fact_map.get("prior_auth_number")]
        if missing_pa_for:
            return {
                "is_covered": None,
                "coverage_type": "medical",
                "hard_fail": False,
                "reasons": [f"Prior authorization required for {', '.join(missing_pa_for)}."],
                "deductible": None,
                "benefit_notes": ["Pending additional documentation."],
                "confidence": 0.9,
            }

        uncovered = [code for code in procedure_codes if code not in plan.get("covered_procedures", [])]
        if uncovered:
            return {
                "is_covered": False,
                "coverage_type": "medical",
                "hard_fail": True,
                "reasons": [f"Procedure not covered by plan: {', '.join(uncovered)}."],
                "deductible": None,
                "benefit_notes": [],
                "confidence": 0.92,
            }

        return {
            "is_covered": True,
            "coverage_type": "medical",
            "hard_fail": False,
            "reasons": ["Member active, procedure covered, and benefits checks passed."],
            "deductible": None,
            "benefit_notes": ["Auto-adjudication eligible if risk signals remain low."],
            "confidence": 0.88,
        }

    @staticmethod
    def _load_json(path: Path) -> list[dict]:
        if not path.exists():
            return []
        return json.loads(path.read_text(encoding="utf-8"))