from __future__ import annotations

from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app.models.audit_event import AuditEvent


class AuditRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def log(self, claim_id: str, event_type: str, actor_type: str, actor_id: str, payload: dict | None = None) -> AuditEvent:
        event = AuditEvent(
            claim_id=claim_id,
            event_type=event_type,
            actor_type=actor_type,
            actor_id=actor_id,
            payload=payload or {},
        )
        self.db.add(event)
        self.db.commit()
        self.db.refresh(event)
        return event

    def list_for_claim(self, claim_id: str) -> list[AuditEvent]:
        stmt = select(AuditEvent).where(AuditEvent.claim_id == claim_id).order_by(desc(AuditEvent.timestamp))
        return list(self.db.scalars(stmt).all())