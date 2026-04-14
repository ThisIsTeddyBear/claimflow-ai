from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, declarative_base, sessionmaker

from .config import get_settings

settings = get_settings()
connect_args = {"check_same_thread": False} if settings.database_url.startswith("sqlite") else {}
engine = create_engine(settings.database_url, future=True, connect_args=connect_args)
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False, class_=Session)
Base = declarative_base()


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    from .models import (  # noqa: F401
        advisory_result,
        audit_event,
        claim,
        communication_draft,
        coverage_result,
        decision,
        document,
        evaluation_run,
        extracted_fact,
        fraud_result,
        validation_issue,
        workflow_step,
    )

    Base.metadata.create_all(bind=engine)