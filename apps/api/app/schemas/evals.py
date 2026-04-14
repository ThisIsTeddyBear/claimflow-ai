from datetime import datetime

from .base import ORMModel


class EvalRunRead(ORMModel):
    id: str
    status: str
    started_at: datetime
    completed_at: datetime | None
    summary: dict
    results: list