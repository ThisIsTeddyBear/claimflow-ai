from datetime import date

from app.config import get_settings
from app.db import SessionLocal, init_db
from app.models.claim import ClaimCase
from app.services.workflow_service import WorkflowService


def test_run_claim_recovers_from_stale_in_progress_status() -> None:
    init_db()
    settings = get_settings()

    with SessionLocal() as db:
        claim = ClaimCase(
            claim_number="INT-RECOVERY-0001",
            domain="auto",
            subtype="own_damage",
            status="under_extraction",
            incident_or_service_date=date(2026, 1, 15),
            policy_or_member_id="AUTO-1001",
            claimant_name="Ava Carter",
            estimated_amount=1200,
            claim_payload={"injury_involved": False, "use_type": "personal"},
        )
        db.add(claim)
        db.commit()
        db.refresh(claim)

        # No documents means intake should pend, but rerun should not fail on transition.
        decision = WorkflowService(db, settings).run_claim(claim.id)
        assert decision["decision"] == "pend"
