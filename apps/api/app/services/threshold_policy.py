from __future__ import annotations


class ThresholdPolicy:
    def __init__(
        self,
        *,
        auto_approval_ceiling: float,
        fraud_escalation_threshold: float,
        confidence_threshold: float,
        high_value_threshold_auto: float,
        high_value_threshold_healthcare: float,
    ) -> None:
        self.auto_approval_ceiling = auto_approval_ceiling
        self.fraud_escalation_threshold = fraud_escalation_threshold
        self.confidence_threshold = confidence_threshold
        self.high_value_threshold_auto = high_value_threshold_auto
        self.high_value_threshold_healthcare = high_value_threshold_healthcare

    def is_high_value(self, domain: str, amount: float | None) -> bool:
        if amount is None:
            return False
        if domain == "auto":
            return amount >= self.high_value_threshold_auto
        return amount >= self.high_value_threshold_healthcare

    def is_auto_approval_eligible(self, amount: float | None) -> bool:
        if amount is None:
            return True
        return amount <= self.auto_approval_ceiling