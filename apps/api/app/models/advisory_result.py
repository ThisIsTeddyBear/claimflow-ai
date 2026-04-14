from __future__ import annotations

from datetime import datetime
from uuid import uuid4

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, JSON, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


class AdvisoryResult(Base):
    __tablename__ = "advisory_results"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    claim_id: Mapped[str] = mapped_column(String(36), ForeignKey("claims.id"), index=True)
    domain: Mapped[str] = mapped_column(String(32), index=True)
    findings: Mapped[list] = mapped_column(JSON, default=list)
    uncertainty_flags: Mapped[list] = mapped_column(JSON, default=list)
    escalation_recommended: Mapped[bool] = mapped_column(Boolean, default=False)
    confidence: Mapped[float] = mapped_column(Float)
    agent_version: Mapped[str] = mapped_column(String(32), default="v1")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)

    claim = relationship("ClaimCase", back_populates="advisory_results")