from __future__ import annotations

from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app.models.document import ClaimDocument


class DocumentRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create(self, payload: dict) -> ClaimDocument:
        document = ClaimDocument(**payload)
        self.db.add(document)
        self.db.commit()
        self.db.refresh(document)
        return document

    def list_for_claim(self, claim_id: str) -> list[ClaimDocument]:
        stmt = select(ClaimDocument).where(ClaimDocument.claim_id == claim_id).order_by(desc(ClaimDocument.uploaded_at))
        return list(self.db.scalars(stmt).all())

    def get(self, document_id: str) -> ClaimDocument | None:
        return self.db.get(ClaimDocument, document_id)