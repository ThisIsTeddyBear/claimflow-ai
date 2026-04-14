from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "apps/api"))

from app.config import get_settings
from app.db import SessionLocal, init_db
from app.services.seed_service import DemoSeedService


def main() -> None:
    init_db()
    with SessionLocal() as db:
        result = DemoSeedService(db, get_settings()).seed()
    print(result)


if __name__ == "__main__":
    main()