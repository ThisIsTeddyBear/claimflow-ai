from app.services.decision_policy import DecisionPolicyEngine
from app.services.threshold_policy import ThresholdPolicy


policy = ThresholdPolicy(
    auto_approval_ceiling=12000,
    fraud_escalation_threshold=0.7,
    confidence_threshold=0.75,
    high_value_threshold_auto=20000,
    high_value_threshold_healthcare=15000,
)
engine = DecisionPolicyEngine(policy)


def test_reject_precedence_on_hard_fail() -> None:
    decision = engine.decide(
        domain="auto",
        intake={"missing_docs": []},
        validation_issues=[],
        coverage={"hard_fail": True, "reasons": ["Policy inactive"], "confidence": 0.98},
        anomaly={"recommended_action": "continue", "signals": []},
        advisory={"escalation_recommended": False},
        rule_matches=[],
        overall_confidence=0.9,
        estimated_amount=3000,
    )
    assert decision["decision"] == "reject"


def test_pend_when_missing_docs() -> None:
    decision = engine.decide(
        domain="healthcare",
        intake={"missing_docs": ["prior_auth"]},
        validation_issues=[],
        coverage={"hard_fail": False, "is_covered": None, "reasons": []},
        anomaly={"recommended_action": "continue", "signals": []},
        advisory={"escalation_recommended": False},
        rule_matches=[],
        overall_confidence=0.8,
        estimated_amount=500,
    )
    assert decision["decision"] == "pend"


def test_escalate_for_high_risk() -> None:
    decision = engine.decide(
        domain="auto",
        intake={"missing_docs": []},
        validation_issues=[],
        coverage={"hard_fail": False, "is_covered": True, "reasons": ["covered"]},
        anomaly={"recommended_action": "escalate", "signals": [{"description": "duplicate"}], "risk_score": 0.8},
        advisory={"escalation_recommended": False},
        rule_matches=[],
        overall_confidence=0.9,
        estimated_amount=1000,
    )
    assert decision["decision"] == "escalate"


def test_approve_when_clean_case() -> None:
    decision = engine.decide(
        domain="auto",
        intake={"missing_docs": []},
        validation_issues=[],
        coverage={"hard_fail": False, "is_covered": True, "reasons": ["covered"], "confidence": 0.9},
        anomaly={"recommended_action": "continue", "signals": []},
        advisory={"escalation_recommended": False},
        rule_matches=[],
        overall_confidence=0.9,
        estimated_amount=4000,
    )
    assert decision["decision"] == "approve"