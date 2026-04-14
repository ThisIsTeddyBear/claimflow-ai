from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import uuid4

from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app.models.claim import ClaimCase
from app.models.decision import ClaimDecision


class ClaimRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create(self, payload: dict[str, Any]) -> ClaimCase:
        claim = ClaimCase(
            claim_number=self._generate_claim_number(),
            domain=payload["domain"],
            subtype=payload.get("subtype"),
            status="submitted",
            submitted_at=datetime.utcnow(),
            incident_or_service_date=payload.get("incident_or_service_date"),
            policy_or_member_id=payload.get("policy_or_member_id"),
            claimant_name=payload.get("claimant_name"),
            estimated_amount=payload.get("estimated_amount"),
            claim_payload=payload.get("claim_payload", {}),
            current_queue="manual_triage",
        )
        self.db.add(claim)
        self.db.commit()
        self.db.refresh(claim)
        return claim

    def list(self, domain: str | None = None, status: str | None = None, decision: str | None = None) -> list[ClaimCase]:
        stmt = select(ClaimCase).order_by(desc(ClaimCase.created_at))
        if domain:
            stmt = stmt.where(ClaimCase.domain == domain)
        if status:
            stmt = stmt.where(ClaimCase.status == status)

        claims = list(self.db.scalars(stmt).all())
        if decision:
            filtered: list[ClaimCase] = []
            for claim in claims:
                latest_decision = self.latest_decision(claim.id)
                if latest_decision and latest_decision.decision == decision:
                    filtered.append(claim)
            return filtered
        return claims

    def get(self, claim_id: str) -> ClaimCase | None:
        return self.db.get(ClaimCase, claim_id)

    def update(self, claim: ClaimCase, payload: dict[str, Any]) -> ClaimCase:
        for key, value in payload.items():
            if value is not None:
                setattr(claim, key, value)
        claim.updated_at = datetime.utcnow()
        self.db.add(claim)
        self.db.commit()
        self.db.refresh(claim)
        return claim

    def latest_decision(self, claim_id: str) -> ClaimDecision | None:
        stmt = (
            select(ClaimDecision)
            .where(ClaimDecision.claim_id == claim_id)
            .order_by(desc(ClaimDecision.created_at))
            .limit(1)
        )
        return self.db.scalar(stmt)

    @staticmethod
    def _generate_claim_number() -> str:
        return f"CLM-{uuid4().hex[:10].upper()}"