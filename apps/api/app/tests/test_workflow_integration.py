from datetime import date
from uuid import uuid4

from app.config import get_settings
from app.db import SessionLocal, init_db
from app.models.claim import ClaimCase
from app.models.document import ClaimDocument
from app.repositories.decision_repository import DecisionRepository
from app.services.utils import sha256_text
from app.services.workflow_service import WorkflowService


def test_workflow_auto_approve_path() -> None:
    init_db()
    settings = get_settings()

    with SessionLocal() as db:
        claim = ClaimCase(
            claim_number=f"INT-APPROVE-{uuid4().hex[:8]}",
                domain="auto",
                subtype="own_damage",
                status="submitted",
                incident_or_service_date=date(2026, 1, 15),
                policy_or_member_id="AUTO-1001",
                claimant_name="Ava Carter",
                estimated_amount=4321,
                claim_payload={"injury_involved": False, "use_type": "personal"},
            )
        db.add(claim)
        db.flush()

        docs = [
                (
                    "claim_form.txt",
                    "claim_form",
                    "Incident Date: 2026-01-15\nDriver: Ava Carter\nLocation: Sacramento, CA\nVIN: 1HGCM82633A100001\nUse Type: personal\nNarrative: Rear impact in city traffic",
                ),
                (
                    "accident_narrative.txt",
                    "accident_narrative",
                    "Incident Date: 2026-01-15\nDriver: Ava Carter\nNarrative: Rear impact in city traffic\nInjury Description: minor soreness",
                ),
                (
                    "repair_estimate.txt",
                    "repair_estimate",
                    "Estimate Number: EST-1\nTotal Estimate: $4321\nDamage Area: rear bumper",
                ),
        ]

        for filename, doc_type, content in docs:
            db.add(
                ClaimDocument(
                    claim_id=claim.id,
                    filename=filename,
                    mime_type="text/plain",
                    document_type=doc_type,
                    storage_path=f"{settings.upload_dir}/{claim.id}/{filename}",
                    ocr_text=content,
                    metadata_json={"test": True},
                    fingerprint=sha256_text(content),
                )
            )

        db.commit()
        db.refresh(claim)

        WorkflowService(db, settings).run_claim(claim.id)
        decision = DecisionRepository(db).latest_for_claim(claim.id)
        assert decision is not None
        assert decision.decision == "approve"
