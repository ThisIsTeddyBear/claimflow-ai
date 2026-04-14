from __future__ import annotations

from datetime import date, datetime
from uuid import uuid4

from sqlalchemy import Date, DateTime, Float, ForeignKey, JSON, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


class ClaimCase(Base):
    __tablename__ = "claims"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    claim_number: Mapped[str] = mapped_column(String(32), unique=True, index=True)
    domain: Mapped[str] = mapped_column(String(32), index=True)
    subtype: Mapped[str | None] = mapped_column(String(64), nullable=True)
    status: Mapped[str] = mapped_column(String(64), index=True, default="draft")

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)
    submitted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    incident_or_service_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    policy_or_member_id: Mapped[str | None] = mapped_column(String(64), index=True, nullable=True)
    claimant_name: Mapped[str | None] = mapped_column(String(128), nullable=True)
    priority_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    current_queue: Mapped[str | None] = mapped_column(String(64), nullable=True)
    estimated_amount: Mapped[float | None] = mapped_column(Float, nullable=True)

    final_decision_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("claim_decisions.id"), nullable=True)
    claim_payload: Mapped[dict] = mapped_column(JSON, default=dict)

    documents = relationship("ClaimDocument", back_populates="claim", cascade="all, delete-orphan")
    extracted_facts = relationship("ExtractedFact", back_populates="claim", cascade="all, delete-orphan")
    validation_issues = relationship("ValidationIssue", back_populates="claim", cascade="all, delete-orphan")
    coverage_results = relationship("CoverageResult", back_populates="claim", cascade="all, delete-orphan")
    fraud_results = relationship("FraudResult", back_populates="claim", cascade="all, delete-orphan")
    advisory_results = relationship("AdvisoryResult", back_populates="claim", cascade="all, delete-orphan")
    steps = relationship("WorkflowStep", back_populates="claim", cascade="all, delete-orphan")
    decisions = relationship("ClaimDecision", foreign_keys="ClaimDecision.claim_id", back_populates="claim", cascade="all, delete-orphan")
    final_decision = relationship("ClaimDecision", foreign_keys=[final_decision_id], post_update=True)
    audits = relationship("AuditEvent", back_populates="claim", cascade="all, delete-orphan")
    communications = relationship("CommunicationDraft", back_populates="claim", cascade="all, delete-orphan")