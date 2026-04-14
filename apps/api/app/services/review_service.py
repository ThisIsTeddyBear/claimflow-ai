from __future__ import annotations

from datetime import datetime

from sqlalchemy.orm import Session

from app.models.claim import ClaimCase
from app.repositories.audit_repository import AuditRepository
from app.repositories.decision_repository import DecisionRepository


class ReviewService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.audit_repo = AuditRepository(db)
        self.decision_repo = DecisionRepository(db)

    def apply_action(
        self,
        *,
        claim: ClaimCase,
        action: str,
        reviewer_id: str,
        notes: str,
        reviewer_queue: str | None = None,
    ) -> dict:
        previous = self.decision_repo.latest_for_claim(claim.id)
        decision = self.decision_repo.create(
            {
                "claim_id": claim.id,
                "decision": action,
                "reasons": [notes],
                "evidence_refs": [],
                "required_next_action": "Human review action",
                "reviewer_queue": reviewer_queue,
                "confidence": 0.99,
                "rule_refs": [],
                "step_ref": "human_review",
                "decided_by": "human",
                "decided_by_id": reviewer_id,
                "override_of_decision_id": previous.id if previous else None,
            }
        )

        claim.final_decision_id = decision.id
        claim.status = {
            "approve": "approved",
            "reject": "rejected",
            "pend": "pended",
            "escalate": "pending_human_review",
        }[action]
        claim.current_queue = reviewer_queue
        claim.updated_at = datetime.utcnow()
        self.db.add(claim)
        self.db.commit()
        self.db.refresh(claim)

        self.audit_repo.log(
            claim_id=claim.id,
            event_type="human_review_action",
            actor_type="human",
            actor_id=reviewer_id,
            payload={
                "previous_decision": previous.decision if previous else None,
                "new_decision": action,
                "notes": notes,
                "reviewer_queue": reviewer_queue,
            },
        )

        return {
            "claim_id": claim.id,
            "decision_id": decision.id,
            "status": claim.status,
            "decision": action,
        }