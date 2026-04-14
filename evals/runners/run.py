from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "apps/api"))

from app.config import get_settings
from app.db import SessionLocal, init_db
from app.services.eval_service import EvalService


def run() -> dict:
    init_db()
    with SessionLocal() as db:
        run_obj = EvalService(db, get_settings()).run()
        return {"id": run_obj.id, "summary": run_obj.summary, "results": run_obj.results}


if __name__ == "__main__":
    print(run())