from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import get_settings
from app.dependencies import get_db_session
from app.models.workflow_step import WorkflowStep
from app.repositories.claim_repository import ClaimRepository
from app.repositories.decision_repository import DecisionRepository
from app.schemas.claims import ClaimDecisionRead, WorkflowStepRead
from app.services.workflow_service import WorkflowService

router = APIRouter(tags=["workflow"])


@router.post("/claims/{claim_id}/run", response_model=ClaimDecisionRead)
def run_workflow(claim_id: str, db: Session = Depends(get_db_session)) -> ClaimDecisionRead:
    claim = ClaimRepository(db).get(claim_id)
    if not claim:
        raise HTTPException(status_code=404, detail="Claim not found")

    service = WorkflowService(db, get_settings())
    service.run_claim(claim_id)
    decision = DecisionRepository(db).latest_for_claim(claim_id)
    if not decision:
        raise HTTPException(status_code=500, detail="Workflow completed without decision")
    return ClaimDecisionRead.model_validate(decision)


@router.get("/claims/{claim_id}/steps", response_model=list[WorkflowStepRead])
def list_workflow_steps(claim_id: str, db: Session = Depends(get_db_session)) -> list[WorkflowStepRead]:
    if not ClaimRepository(db).get(claim_id):
        raise HTTPException(status_code=404, detail="Claim not found")
    steps = list(db.scalars(select(WorkflowStep).where(WorkflowStep.claim_id == claim_id).order_by(WorkflowStep.started_at)).all())
    return [WorkflowStepRead.model_validate(step) for step in steps]


@router.get("/claims/{claim_id}/decision", response_model=ClaimDecisionRead)
def get_claim_decision(claim_id: str, db: Session = Depends(get_db_session)) -> ClaimDecisionRead:
    decision = DecisionRepository(db).latest_for_claim(claim_id)
    if not decision:
        raise HTTPException(status_code=404, detail="No decision found")
    return ClaimDecisionRead.model_validate(decision)


@router.post("/claims/{claim_id}/rerun-step/{step_name}", response_model=ClaimDecisionRead)
def rerun_from_step(claim_id: str, step_name: str, db: Session = Depends(get_db_session)) -> ClaimDecisionRead:
    if not ClaimRepository(db).get(claim_id):
        raise HTTPException(status_code=404, detail="Claim not found")
    service = WorkflowService(db, get_settings())
    service.rerun_step(claim_id, step_name)
    decision = DecisionRepository(db).latest_for_claim(claim_id)
    if not decision:
        raise HTTPException(status_code=500, detail="Rerun completed without decision")
    return ClaimDecisionRead.model_validate(decision)