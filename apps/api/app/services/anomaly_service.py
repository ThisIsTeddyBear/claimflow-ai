from __future__ import annotations

from app.services.duplicate_detector import DuplicateDetector
from app.services.threshold_policy import ThresholdPolicy


class AnomalyService:
    def __init__(self, threshold_policy: ThresholdPolicy) -> None:
        self.threshold_policy = threshold_policy

    def score(
        self,
        *,
        duplicate_result: dict,
        validation_issues: list[dict],
        estimated_amount: float | None,
        domain: str,
    ) -> dict:
        signals: list[dict] = []
        score = 0.0

        for signal in duplicate_result.get("signals", []):
            signals.append(signal)
            severity = signal.get("severity", "low")
            score += {"low": 0.05, "medium": 0.12, "high": 0.24, "critical": 0.35}.get(severity, 0.05)

        high_issues = [issue for issue in validation_issues if issue.get("severity") in {"high", "critical"}]
        if high_issues:
            signals.append(
                {
                    "code": "material_validation_issues",
                    "description": "High-severity validation issues detected.",
                    "severity": "high",
                    "confidence": 0.86,
                    "evidence_refs": [issue.get("id") for issue in high_issues if issue.get("id")],
                }
            )
            score += 0.22

        if self.threshold_policy.is_high_value(domain, estimated_amount):
            signals.append(
                {
                    "code": "high_value_claim",
                    "description": "Claim amount exceeds high-value threshold.",
                    "severity": "medium",
                    "confidence": 0.92,
                    "evidence_refs": [],
                }
            )
            score += 0.18

        if duplicate_result.get("is_duplicate"):
            score += 0.3

        risk_score = max(0.0, min(1.0, round(score, 3)))
        if risk_score >= self.threshold_policy.fraud_escalation_threshold:
            action = "escalate"
        elif risk_score >= 0.45:
            action = "pend"
        else:
            action = "continue"

        return {
            "risk_score": risk_score,
            "signals": signals,
            "recommended_action": action,
        }