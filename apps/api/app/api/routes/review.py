from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.dependencies import get_db_session
from app.repositories.claim_repository import ClaimRepository
from app.schemas.review import ReviewActionRequest
from app.services.review_service import ReviewService

router = APIRouter(tags=["review"])


def _handle_review_action(claim_id: str, action: str, payload: ReviewActionRequest, db: Session) -> dict:
    claim = ClaimRepository(db).get(claim_id)
    if not claim:
        raise HTTPException(status_code=404, detail="Claim not found")
    return ReviewService(db).apply_action(
        claim=claim,
        action=action,
        reviewer_id=payload.reviewer_id,
        notes=payload.notes,
        reviewer_queue=payload.reviewer_queue,
    )


@router.post("/claims/{claim_id}/review/approve")
def review_approve(claim_id: str, payload: ReviewActionRequest, db: Session = Depends(get_db_session)) -> dict:
    return _handle_review_action(claim_id, "approve", payload, db)


@router.post("/claims/{claim_id}/review/reject")
def review_reject(claim_id: str, payload: ReviewActionRequest, db: Session = Depends(get_db_session)) -> dict:
    return _handle_review_action(claim_id, "reject", payload, db)


@router.post("/claims/{claim_id}/review/pend")
def review_pend(claim_id: str, payload: ReviewActionRequest, db: Session = Depends(get_db_session)) -> dict:
    return _handle_review_action(claim_id, "pend", payload, db)


@router.post("/claims/{claim_id}/review/escalate")
def review_escalate(claim_id: str, payload: ReviewActionRequest, db: Session = Depends(get_db_session)) -> dict:
    return _handle_review_action(claim_id, "escalate", payload, db)


@router.post("/claims/{claim_id}/review/override")
def review_override(claim_id: str, payload: ReviewActionRequest, db: Session = Depends(get_db_session)) -> dict:
    if payload.decision is None:
        raise HTTPException(status_code=400, detail="Override requires decision in payload")
    return _handle_review_action(claim_id, payload.decision.value, payload, db)