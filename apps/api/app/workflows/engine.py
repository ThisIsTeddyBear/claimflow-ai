from __future__ import annotations

from sqlalchemy.orm import Session

from app.config import Settings
from app.services.workflow_service import WorkflowService


class ClaimWorkflow:
    name = "shared_claim_workflow"

    def __init__(self, db: Session, settings: Settings) -> None:
        self.service = WorkflowService(db, settings)

    def run(self, claim_id: str) -> dict:
        return self.service.run_claim(claim_id)