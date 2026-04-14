# Progress Tracker

## Current Status
- [x] Loaded and reviewed `instructions.md` in full.
- [x] Established repository folder structure.
- [x] Created implementation plan.
- [x] Backend foundations
- [x] Frontend foundations
- [x] Workflow + agents
- [x] Deterministic rules + decision engine
- [x] Human review + audit trail
- [x] Eval harness + tests
- [x] Documentation polish

## Work Log
### 2026-04-14
- Created baseline monorepo structure under `apps/`, `data/`, `docs/`, `evals/`, and `scripts/`.
- Copied canonical `instructions.md` into repo root.
- Added milestone-driven execution plan in `docs/implementation-plan.md`.
- Built FastAPI backend with SQLAlchemy models, API routes, orchestration engine, rules engine, coverage evaluators, anomaly/duplicate detection, decision policy, and review overrides.
- Implemented versioned prompt contracts under `apps/api/app/prompts/`.
- Added synthetic reference data and 14 seeded domain scenarios (7 auto + 7 healthcare).
- Added evaluation harness (`/evals/run`, scripts, reports) and baseline tests.
- Built Next.js reviewer dashboard with claims queue, new claim intake, claim detail workspace, workflow timeline, audit trail, decision panel, and eval dashboard.
- Authored architecture, workflow, prompt, and demo documentation.
- Hardened backend test isolation in `apps/api/app/tests/conftest.py`:
  - forced dedicated temp SQLite database per test run
  - forced dedicated temp upload directory for tests
  - reset schema before every test for deterministic behavior
- Fixed amount extraction logic in `apps/api/app/services/utils.py` for plain 4+ digit values (for example `$4321`) while preserving comma/decimal support.
- Added amount extraction tests in `apps/api/app/tests/test_amount_extraction.py` covering:
  - `$4321`
  - `4,321`
  - `$4,321.75`
  - `950`
  - multiple amounts in one document
- Removed Python `__pycache__` artifacts under `apps/`.
- Expanded `.gitignore` coverage for cache/runtime/editor artifacts (`pytest-cache-files-*`, `.mypy_cache`, `.ruff_cache`, `.coverage`, `*.sqlite-journal`, logs, IDE files).
## Verification Log
- `python -m pytest apps/api/app/tests -q` -> 8 passed
- `python scripts/seed_demo_data.py` -> seeded scenarios into DB
- `python scripts/run_evals.py` -> decision accuracy 1.0 on 14 fixtures
- `npm --prefix apps/web run build` -> successful production build
- `python scripts/run_evals.py` (latest) -> 14/14 decision match, avg required-field recall 0.929
- `npm --prefix apps/web run build` -> successful (validated with escalated permissions due sandbox spawn restrictions)
- `pytest apps/api/app/tests -q` -> 13 passed
