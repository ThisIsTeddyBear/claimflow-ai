from __future__ import annotations

import os
import shutil
import tempfile
from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "apps/api"))

TEST_RUNTIME_DIR = Path(tempfile.mkdtemp(prefix="claimflow-tests-")).resolve()
TEST_DB_PATH = TEST_RUNTIME_DIR / "claimflow_test.db"

# Force a dedicated isolated runtime for tests so they never read/write the packaged demo DB.
os.environ["DATABASE_URL"] = f"sqlite:///{TEST_DB_PATH.as_posix()}"
os.environ["UPLOAD_DIR"] = (TEST_RUNTIME_DIR / "uploads").as_posix()
os.environ["ENABLE_LIVE_LLM"] = "false"


@pytest.fixture(autouse=True)
def isolated_database() -> None:
    from app.db import Base, engine, init_db

    init_db()
    with engine.begin() as connection:
        connection.exec_driver_sql("PRAGMA foreign_keys=OFF")
        for table in Base.metadata.tables.values():
            connection.execute(table.delete())
        connection.exec_driver_sql("PRAGMA foreign_keys=ON")
    yield


def pytest_sessionfinish(session: pytest.Session, exitstatus: int) -> None:
    shutil.rmtree(TEST_RUNTIME_DIR, ignore_errors=True)
