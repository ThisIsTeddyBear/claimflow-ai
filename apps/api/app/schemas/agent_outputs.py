from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from .enums import Severity


class IntakeAgentOutput(BaseModel):
    claim_domain: str
    claim_subtype: str | None = None
    required_docs: list[str] = Field(default_factory=list)
    missing_docs: list[str] = Field(default_factory=list)
    completeness_score: float = 0.0
    intake_notes: list[str] = Field(default_factory=list)
    confidence: float = 0.0


class ExtractedEntity(BaseModel):
    value: Any
    confidence: float
    source_excerpt: str | None = None


class ExtractionAgentOutput(BaseModel):
    document_type: str
    entities: dict[str, ExtractedEntity] = Field(default_factory=dict)
    ambiguities: list[str] = Field(default_factory=list)
    doc_summary: str
    confidence: float


class ContradictionIssue(BaseModel):
    category: str
    description: str
    severity: Severity
    source_document_ids: list[str] = Field(default_factory=list)
    resolvable_with_more_docs: bool = True
    confidence: float


class ContradictionAgentOutput(BaseModel):
    issues: list[ContradictionIssue] = Field(default_factory=list)
    requires_human_review: bool = False
    confidence: float = 0.0


class AdvisoryFinding(BaseModel):
    finding: str
    confidence: float
    evidence_refs: list[str] = Field(default_factory=list)


class AdvisoryAgentOutput(BaseModel):
    claim_id: str
    domain: str
    findings: list[AdvisoryFinding] = Field(default_factory=list)
    uncertainty_flags: list[str] = Field(default_factory=list)
    escalation_recommended: bool = False
    confidence: float = 0.0


class ExplanationOutput(BaseModel):
    title: str
    summary: str
    reasons: list[str] = Field(default_factory=list)
    next_steps: list[str] = Field(default_factory=list)
    tone: str = "professional"


class StepEnvelope(BaseModel):
    run_id: str
    step_name: str
    started_at: datetime
    completed_at: datetime | None = None
    output: dict[str, Any] = Field(default_factory=dict)