from __future__ import annotations

from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app.models.decision import ClaimDecision


class DecisionRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create(self, payload: dict) -> ClaimDecision:
        decision = ClaimDecision(**payload)
        self.db.add(decision)
        self.db.commit()
        self.db.refresh(decision)
        return decision

    def latest_for_claim(self, claim_id: str) -> ClaimDecision | None:
        stmt = (
            select(ClaimDecision)
            .where(ClaimDecision.claim_id == claim_id)
            .order_by(desc(ClaimDecision.created_at))
            .limit(1)
        )
        return self.db.scalar(stmt)

    def list_for_claim(self, claim_id: str) -> list[ClaimDecision]:
        stmt = select(ClaimDecision).where(ClaimDecision.claim_id == claim_id).order_by(desc(ClaimDecision.created_at))
        return list(self.db.scalars(stmt).all())