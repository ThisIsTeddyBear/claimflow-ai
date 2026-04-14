from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app.config import get_settings
from app.dependencies import get_db_session
from app.models.evaluation_run import EvaluationRun
from app.schemas.evals import EvalRunRead
from app.services.eval_service import EvalService
from app.services.seed_service import DemoSeedService

router = APIRouter(tags=["evals"])


@router.post("/demo/seed")
def seed_demo_data(db: Session = Depends(get_db_session)) -> dict:
    service = DemoSeedService(db, get_settings())
    return service.seed()


@router.get("/evals", response_model=list[EvalRunRead])
def list_evaluations(db: Session = Depends(get_db_session)) -> list[EvalRunRead]:
    runs = list(db.scalars(select(EvaluationRun).order_by(desc(EvaluationRun.started_at))).all())
    return [EvalRunRead.model_validate(run) for run in runs]


@router.post("/evals/run", response_model=EvalRunRead)
def run_evals(db: Session = Depends(get_db_session)) -> EvalRunRead:
    run = EvalService(db, get_settings()).run()
    return EvalRunRead.model_validate(run)