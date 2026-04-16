from app.workflows.state_machine import ClaimStateMachine


def test_can_rerun_from_in_progress_statuses() -> None:
    sm = ClaimStateMachine()

    assert sm.can_transition("under_extraction", "intake_processing")
    assert sm.can_transition("under_validation", "intake_processing")
    assert sm.can_transition("under_coverage_review", "intake_processing")
    assert sm.can_transition("under_fraud_review", "intake_processing")
    assert sm.can_transition("under_domain_review", "intake_processing")
    assert sm.can_transition("under_decisioning", "intake_processing")
