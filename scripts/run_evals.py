from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "apps/api"))

from app.config import get_settings
from app.db import SessionLocal, init_db
from app.services.eval_service import EvalService


def main() -> None:
    init_db()
    with SessionLocal() as db:
        result = EvalService(db, get_settings()).run()
    print({"run_id": result.id, "summary": result.summary})


if __name__ == "__main__":
    main()