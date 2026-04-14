from __future__ import annotations

from datetime import datetime
from uuid import uuid4

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, JSON, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


class CoverageResult(Base):
    __tablename__ = "coverage_results"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    claim_id: Mapped[str] = mapped_column(String(36), ForeignKey("claims.id"), index=True)
    is_covered: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    coverage_type: Mapped[str | None] = mapped_column(String(64), nullable=True)
    hard_fail: Mapped[bool] = mapped_column(Boolean, default=False)
    reasons: Mapped[list] = mapped_column(JSON, default=list)
    deductible: Mapped[float | None] = mapped_column(Float, nullable=True)
    benefit_notes: Mapped[list] = mapped_column(JSON, default=list)
    confidence: Mapped[float] = mapped_column(Float)
    evaluator_version: Mapped[str] = mapped_column(String(32), default="v1")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)

    claim = relationship("ClaimCase", back_populates="coverage_results")