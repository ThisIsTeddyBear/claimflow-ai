from __future__ import annotations

from datetime import date, datetime
from typing import Any

from pydantic import Field

from .base import ORMModel
from .enums import ClaimDomain, ClaimStatus, DecisionType, Severity


class ClaimCreate(ORMModel):
    domain: ClaimDomain
    subtype: str | None = None
    incident_or_service_date: date | None = None
    policy_or_member_id: str | None = None
    claimant_name: str | None = None
    estimated_amount: float | None = None
    claim_payload: dict[str, Any] = Field(default_factory=dict)


class ClaimUpdate(ORMModel):
    subtype: str | None = None
    incident_or_service_date: date | None = None
    policy_or_member_id: str | None = None
    claimant_name: str | None = None
    estimated_amount: float | None = None
    status: ClaimStatus | None = None
    current_queue: str | None = None
    claim_payload: dict[str, Any] | None = None


class ClaimRead(ORMModel):
    id: str
    claim_number: str
    domain: ClaimDomain
    subtype: str | None
    status: ClaimStatus
    created_at: datetime
    updated_at: datetime
    submitted_at: datetime | None
    incident_or_service_date: date | None
    policy_or_member_id: str | None
    claimant_name: str | None
    priority_score: float | None
    current_queue: str | None
    estimated_amount: float | None
    claim_payload: dict[str, Any]


class ClaimSummary(ORMModel):
    id: str
    claim_number: str
    domain: ClaimDomain
    subtype: str | None
    status: ClaimStatus
    claimant_name: str | None
    policy_or_member_id: str | None
    incident_or_service_date: date | None
    estimated_amount: float | None
    current_queue: str | None
    latest_decision: DecisionType | None = None
    latest_decision_confidence: float | None = None
    risk_score: float | None = None


class ClaimDocumentRead(ORMModel):
    id: str
    claim_id: str
    filename: str
    mime_type: str
    document_type: str | None
    uploaded_at: datetime
    storage_path: str
    ocr_text: str | None
    extraction_confidence: float | None
    metadata_json: dict[str, Any]
    fingerprint: str | None


class ExtractedFactRead(ORMModel):
    id: str
    claim_id: str
    source_document_id: str | None
    key: str
    value: dict[str, Any]
    confidence: float
    normalized_value: dict[str, Any] | None
    source_excerpt: str | None
    created_at: datetime


class ValidationIssueRead(ORMModel):
    id: str
    claim_id: str
    category: str
    field: str | None
    description: str
    severity: Severity
    source_document_ids: list[str]
    confidence: float
    resolvable_with_more_docs: bool
    created_at: datetime


class CoverageResultRead(ORMModel):
    id: str
    claim_id: str
    is_covered: bool | None
    coverage_type: str | None
    hard_fail: bool
    reasons: list[str]
    deductible: float | None
    benefit_notes: list[str]
    confidence: float
    evaluator_version: str
    created_at: datetime


class FraudResultRead(ORMModel):
    id: str
    claim_id: str
    risk_score: float
    signals: list[dict[str, Any]]
    recommended_action: str
    detector_version: str
    created_at: datetime


class AdvisoryResultRead(ORMModel):
    id: str
    claim_id: str
    domain: ClaimDomain
    findings: list[dict[str, Any]]
    uncertainty_flags: list[str]
    escalation_recommended: bool
    confidence: float
    agent_version: str
    created_at: datetime


class WorkflowStepRead(ORMModel):
    id: str
    claim_id: str
    run_id: str
    step_name: str
    status: str
    state_before: str | None
    state_after: str | None
    started_at: datetime
    completed_at: datetime | None
    latency_ms: float | None
    output: dict[str, Any]
    error_message: str | None
    retry_count: int


class ClaimDecisionRead(ORMModel):
    id: str
    claim_id: str
    decision: DecisionType
    reasons: list[str]
    evidence_refs: list[str]
    required_next_action: str | None
    reviewer_queue: str | None
    confidence: float
    rule_refs: list[str]
    step_ref: str | None
    decided_by: str
    decided_by_id: str | None
    override_of_decision_id: str | None
    created_at: datetime


class AuditEventRead(ORMModel):
    id: str
    claim_id: str
    event_type: str
    actor_type: str
    actor_id: str
    timestamp: datetime
    payload: dict[str, Any]


class CommunicationDraftRead(ORMModel):
    id: str
    claim_id: str
    audience: str
    title: str
    summary: str
    reasons: list[str]
    next_steps: list[str]
    tone: str
    prompt_version: str
    created_at: datetime


class ClaimDetail(ORMModel):
    claim: ClaimRead
    documents: list[ClaimDocumentRead]
    extracted_facts: list[ExtractedFactRead]
    validation_issues: list[ValidationIssueRead]
    coverage_result: CoverageResultRead | None
    fraud_result: FraudResultRead | None
    advisory_result: AdvisoryResultRead | None
    decision: ClaimDecisionRead | None
    workflow_steps: list[WorkflowStepRead]
    audit_events: list[AuditEventRead]
    communication_drafts: list[CommunicationDraftRead]