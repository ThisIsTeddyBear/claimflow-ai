from __future__ import annotations

from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app.dependencies import get_db_session
from app.models.advisory_result import AdvisoryResult
from app.models.audit_event import AuditEvent
from app.models.claim import ClaimCase
from app.models.communication_draft import CommunicationDraft
from app.models.coverage_result import CoverageResult
from app.models.extracted_fact import ExtractedFact
from app.models.fraud_result import FraudResult
from app.models.validation_issue import ValidationIssue
from app.models.workflow_step import WorkflowStep
from app.repositories.claim_repository import ClaimRepository
from app.repositories.decision_repository import DecisionRepository
from app.repositories.document_repository import DocumentRepository
from app.schemas.claims import ClaimCreate, ClaimDetail, ClaimRead, ClaimSummary, ClaimUpdate

router = APIRouter(tags=["claims"])


@router.post("/claims", response_model=ClaimRead)
def create_claim(payload: ClaimCreate, db: Session = Depends(get_db_session)) -> ClaimRead:
    claim = ClaimRepository(db).create(payload.model_dump())
    return ClaimRead.model_validate(claim)


@router.get("/claims", response_model=list[ClaimSummary])
def list_claims(
    domain: str | None = Query(default=None),
    status: str | None = Query(default=None),
    decision: str | None = Query(default=None),
    db: Session = Depends(get_db_session),
) -> list[ClaimSummary]:
    claim_repo = ClaimRepository(db)
    decision_repo = DecisionRepository(db)
    claims = claim_repo.list(domain=domain, status=status, decision=decision)

    response: list[ClaimSummary] = []
    for claim in claims:
        latest_decision = decision_repo.latest_for_claim(claim.id)
        latest_fraud = db.scalar(
            select(FraudResult).where(FraudResult.claim_id == claim.id).order_by(desc(FraudResult.created_at)).limit(1)
        )
        response.append(
            ClaimSummary(
                id=claim.id,
                claim_number=claim.claim_number,
                domain=claim.domain,
                subtype=claim.subtype,
                status=claim.status,
                claimant_name=claim.claimant_name,
                policy_or_member_id=claim.policy_or_member_id,
                incident_or_service_date=claim.incident_or_service_date,
                estimated_amount=claim.estimated_amount,
                current_queue=claim.current_queue,
                latest_decision=latest_decision.decision if latest_decision else None,
                latest_decision_confidence=latest_decision.confidence if latest_decision else None,
                risk_score=latest_fraud.risk_score if latest_fraud else None,
            )
        )
    return response


@router.get("/claims/{claim_id}", response_model=ClaimDetail)
def get_claim_detail(claim_id: str, db: Session = Depends(get_db_session)) -> ClaimDetail:
    claim = ClaimRepository(db).get(claim_id)
    if not claim:
        raise HTTPException(status_code=404, detail="Claim not found")

    documents = DocumentRepository(db).list_for_claim(claim_id)
    extracted_facts = list(db.scalars(select(ExtractedFact).where(ExtractedFact.claim_id == claim_id)).all())
    validation_issues = list(
        db.scalars(select(ValidationIssue).where(ValidationIssue.claim_id == claim_id).order_by(desc(ValidationIssue.created_at))).all()
    )
    coverage_result = db.scalar(
        select(CoverageResult).where(CoverageResult.claim_id == claim_id).order_by(desc(CoverageResult.created_at)).limit(1)
    )
    fraud_result = db.scalar(select(FraudResult).where(FraudResult.claim_id == claim_id).order_by(desc(FraudResult.created_at)).limit(1))
    advisory_result = db.scalar(
        select(AdvisoryResult).where(AdvisoryResult.claim_id == claim_id).order_by(desc(AdvisoryResult.created_at)).limit(1)
    )
    decision = DecisionRepository(db).latest_for_claim(claim_id)
    steps = list(db.scalars(select(WorkflowStep).where(WorkflowStep.claim_id == claim_id).order_by(WorkflowStep.started_at)).all())
    audits = list(db.scalars(select(AuditEvent).where(AuditEvent.claim_id == claim_id).order_by(desc(AuditEvent.timestamp))).all())
    communications = list(
        db.scalars(select(CommunicationDraft).where(CommunicationDraft.claim_id == claim_id).order_by(desc(CommunicationDraft.created_at))).all()
    )

    return ClaimDetail(
        claim=ClaimRead.model_validate(claim),
        documents=[doc for doc in documents],
        extracted_facts=[fact for fact in extracted_facts],
        validation_issues=[issue for issue in validation_issues],
        coverage_result=coverage_result,
        fraud_result=fraud_result,
        advisory_result=advisory_result,
        decision=decision,
        workflow_steps=[step for step in steps],
        audit_events=[audit for audit in audits],
        communication_drafts=[draft for draft in communications],
    )


@router.patch("/claims/{claim_id}", response_model=ClaimRead)
def update_claim(claim_id: str, payload: ClaimUpdate, db: Session = Depends(get_db_session)) -> ClaimRead:
    claim_repo = ClaimRepository(db)
    claim = claim_repo.get(claim_id)
    if not claim:
        raise HTTPException(status_code=404, detail="Claim not found")

    updated = claim_repo.update(claim, payload.model_dump(exclude_unset=True))
    return ClaimRead.model_validate(updated)