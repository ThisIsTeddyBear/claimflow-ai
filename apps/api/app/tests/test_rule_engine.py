from app.services.rule_engine import RuleEngine


def test_auto_rule_triggers_policy_inactive() -> None:
    engine = RuleEngine("./apps/api/app/rules")
    matches = engine.evaluate(domain="auto", facts={"policy_active": False, "intake": {"missing_docs_count": 0}, "anomaly": {"risk_score": 0.1}})
    assert any(match.rule_id == "auto_policy_inactive_reject" for match in matches)


def test_healthcare_rule_triggers_missing_docs() -> None:
    engine = RuleEngine("./apps/api/app/rules")
    matches = engine.evaluate(
        domain="healthcare",
        facts={"member_active_on_dos": True, "intake": {"missing_docs_count": 2}, "anomaly": {"risk_score": 0.1}},
    )
    assert any(match.rule_id == "healthcare_missing_docs_pend" for match in matches)