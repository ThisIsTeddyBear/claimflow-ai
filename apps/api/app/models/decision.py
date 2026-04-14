from __future__ import annotations

from datetime import datetime
from uuid import uuid4

from sqlalchemy import DateTime, Float, ForeignKey, JSON, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


class ClaimDecision(Base):
    __tablename__ = "claim_decisions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    claim_id: Mapped[str] = mapped_column(String(36), ForeignKey("claims.id"), index=True)
    decision: Mapped[str] = mapped_column(String(16), index=True)
    reasons: Mapped[list] = mapped_column(JSON, default=list)
    evidence_refs: Mapped[list] = mapped_column(JSON, default=list)
    required_next_action: Mapped[str | None] = mapped_column(String(128), nullable=True)
    reviewer_queue: Mapped[str | None] = mapped_column(String(64), nullable=True)
    confidence: Mapped[float] = mapped_column(Float)
    rule_refs: Mapped[list] = mapped_column(JSON, default=list)
    step_ref: Mapped[str | None] = mapped_column(String(64), nullable=True)
    decided_by: Mapped[str] = mapped_column(String(16), default="system")
    decided_by_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    override_of_decision_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)

    claim = relationship("ClaimCase", foreign_keys=[claim_id], back_populates="decisions")