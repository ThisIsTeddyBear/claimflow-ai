from datetime import date
from datetime import datetime, timedelta
from uuid import uuid4

from app.db import SessionLocal, init_db
from app.models.claim import ClaimCase
from app.services.duplicate_detector import DuplicateDetector


def test_duplicate_detector_flags_exact_signature() -> None:
    init_db()
    with SessionLocal() as db:
        existing = ClaimCase(
            claim_number=f"UT-1-{uuid4().hex[:6]}",
            domain="healthcare",
            subtype="professional",
            status="submitted",
            incident_or_service_date=date(2025, 4, 3),
            policy_or_member_id="HLT-2001",
            claimant_name="Emma Lewis",
            estimated_amount=320,
            claim_payload={"corrected_claim": False},
        )
        db.add(existing)
        db.flush()

        candidate = ClaimCase(
            claim_number=f"UT-2-{uuid4().hex[:6]}",
            domain="healthcare",
            subtype="professional",
            status="submitted",
            incident_or_service_date=date(2025, 4, 3),
            policy_or_member_id="HLT-2001",
            claimant_name="Emma Lewis",
            estimated_amount=320,
            claim_payload={"corrected_claim": False},
        )
        db.add(candidate)
        db.commit()
        db.refresh(candidate)

        result = DuplicateDetector(db).detect(candidate, {}, [])
        assert result["is_duplicate"] is True
        assert any(signal["code"] == "exact_claim_signature" for signal in result["signals"])


def test_duplicate_detector_ignores_future_created_claims() -> None:
    init_db()
    with SessionLocal() as db:
        current = ClaimCase(
            claim_number=f"UT-CUR-{uuid4().hex[:6]}",
            domain="healthcare",
            subtype="professional",
            status="submitted",
            incident_or_service_date=date(2025, 4, 3),
            policy_or_member_id="HLT-2001",
            claimant_name="Emma Lewis",
            estimated_amount=320,
            created_at=datetime.utcnow(),
            claim_payload={"corrected_claim": False},
        )
        db.add(current)
        db.flush()

        future = ClaimCase(
            claim_number=f"UT-FUT-{uuid4().hex[:6]}",
            domain="healthcare",
            subtype="professional",
            status="submitted",
            incident_or_service_date=date(2025, 4, 3),
            policy_or_member_id="HLT-2001",
            claimant_name="Emma Lewis",
            estimated_amount=320,
            created_at=datetime.utcnow() + timedelta(minutes=5),
            claim_payload={"corrected_claim": False},
        )
        db.add(future)
        db.commit()
        db.refresh(current)

        result = DuplicateDetector(db).detect(current, {}, [])
        assert result["is_duplicate"] is False
        assert not any(signal["code"] == "exact_claim_signature" for signal in result["signals"])
