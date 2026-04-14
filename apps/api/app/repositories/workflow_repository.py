from __future__ import annotations

from datetime import datetime

from sqlalchemy import asc, desc, select
from sqlalchemy.orm import Session

from app.models.workflow_step import WorkflowStep


class WorkflowRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def start_step(self, payload: dict) -> WorkflowStep:
        step = WorkflowStep(**payload)
        self.db.add(step)
        self.db.commit()
        self.db.refresh(step)
        return step

    def complete_step(
        self,
        step: WorkflowStep,
        *,
        status: str,
        state_after: str | None,
        output: dict,
        error_message: str | None = None,
    ) -> WorkflowStep:
        step.status = status
        step.state_after = state_after
        step.output = output
        step.error_message = error_message
        step.completed_at = datetime.utcnow()
        if step.started_at and step.completed_at:
            step.latency_ms = max((step.completed_at - step.started_at).total_seconds() * 1000, 0)
        self.db.add(step)
        self.db.commit()
        self.db.refresh(step)
        return step

    def list_for_claim(self, claim_id: str) -> list[WorkflowStep]:
        stmt = select(WorkflowStep).where(WorkflowStep.claim_id == claim_id).order_by(asc(WorkflowStep.started_at))
        return list(self.db.scalars(stmt).all())

    def latest_by_name(self, claim_id: str, step_name: str) -> WorkflowStep | None:
        stmt = (
            select(WorkflowStep)
            .where(WorkflowStep.claim_id == claim_id, WorkflowStep.step_name == step_name)
            .order_by(desc(WorkflowStep.started_at))
            .limit(1)
        )
        return self.db.scalar(stmt)