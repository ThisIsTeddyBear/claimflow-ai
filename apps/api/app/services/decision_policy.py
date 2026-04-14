from __future__ import annotations

from app.services.rule_engine import RuleMatch
from app.services.threshold_policy import ThresholdPolicy


class DecisionPolicyEngine:
    def __init__(self, threshold_policy: ThresholdPolicy) -> None:
        self.threshold_policy = threshold_policy

    def decide(
        self,
        *,
        domain: str,
        intake: dict,
        validation_issues: list[dict],
        coverage: dict,
        anomaly: dict,
        advisory: dict,
        rule_matches: list[RuleMatch],
        overall_confidence: float,
        estimated_amount: float | None,
    ) -> dict:
        reasons: list[str] = []
        evidence_refs: list[str] = []
        rule_refs: list[str] = []

        reject_rule = next((rule for rule in rule_matches if rule.decision == "reject"), None)
        if reject_rule:
            reasons.append(reject_rule.reason)
            rule_refs.append(reject_rule.rule_id)
            return {
                "decision": "reject",
                "reasons": reasons,
                "evidence_refs": evidence_refs,
                "required_next_action": "Issue deterministic denial notice",
                "reviewer_queue": None,
                "confidence": 0.97,
                "rule_refs": rule_refs,
            }

        if coverage.get("hard_fail"):
            reasons.extend(coverage.get("reasons", ["Hard coverage failure."]))
            return {
                "decision": "reject",
                "reasons": reasons,
                "evidence_refs": evidence_refs,
                "required_next_action": "Issue deterministic denial notice",
                "reviewer_queue": None,
                "confidence": max(coverage.get("confidence", 0.9), 0.9),
                "rule_refs": rule_refs,
            }

        if intake.get("missing_docs"):
            reasons.append("Critical documents are missing for safe adjudication.")
            reasons.extend([f"Missing: {doc}" for doc in intake.get("missing_docs", [])])
            return {
                "decision": "pend",
                "reasons": reasons,
                "evidence_refs": evidence_refs,
                "required_next_action": "Request missing documents",
                "reviewer_queue": None,
                "confidence": 0.92,
                "rule_refs": rule_refs,
            }

        unresolved_critical = [
            issue for issue in validation_issues if issue.get("severity") in {"high", "critical"} and issue.get("resolvable_with_more_docs", True)
        ]
        if unresolved_critical:
            reasons.append("Material validation issues require additional evidence.")
            reasons.extend(issue.get("description", "Validation issue") for issue in unresolved_critical[:3])
            return {
                "decision": "pend",
                "reasons": reasons,
                "evidence_refs": evidence_refs,
                "required_next_action": "Request clarifying documents",
                "reviewer_queue": None,
                "confidence": 0.85,
                "rule_refs": rule_refs,
            }

        if anomaly.get("recommended_action") == "escalate" or advisory.get("escalation_recommended"):
            queue = "fraud_review" if anomaly.get("recommended_action") == "escalate" else ("auto_adjuster" if domain == "auto" else "medical_review")
            reasons.append("Risk/ambiguity threshold exceeded; routing to human review.")
            if anomaly.get("signals"):
                reasons.append(anomaly["signals"][0].get("description", "Anomaly signal triggered."))
            return {
                "decision": "escalate",
                "reasons": reasons,
                "evidence_refs": evidence_refs,
                "required_next_action": "Route to reviewer queue",
                "reviewer_queue": queue,
                "confidence": max(anomaly.get("risk_score", 0.7), 0.7),
                "rule_refs": rule_refs,
            }

        if overall_confidence < self.threshold_policy.confidence_threshold:
            reasons.append("Model confidence below automation threshold.")
            return {
                "decision": "escalate",
                "reasons": reasons,
                "evidence_refs": evidence_refs,
                "required_next_action": "Manual reviewer verification",
                "reviewer_queue": "manual_triage",
                "confidence": overall_confidence,
                "rule_refs": rule_refs,
            }

        if coverage.get("is_covered") and self.threshold_policy.is_auto_approval_eligible(estimated_amount):
            reasons.extend(coverage.get("reasons", ["Coverage checks passed."]))
            return {
                "decision": "approve",
                "reasons": reasons,
                "evidence_refs": evidence_refs,
                "required_next_action": "Proceed to settlement readiness",
                "reviewer_queue": None,
                "confidence": min(0.95, max(overall_confidence, coverage.get("confidence", 0.8))),
                "rule_refs": rule_refs,
            }

        reasons.append("Coverage outcome is not a deterministic rejection, but case needs additional review.")
        reasons.extend(coverage.get("reasons", []))
        return {
            "decision": "pend",
            "reasons": reasons,
            "evidence_refs": evidence_refs,
            "required_next_action": "Request additional documentation",
            "reviewer_queue": None,
            "confidence": 0.8,
            "rule_refs": rule_refs,
        }