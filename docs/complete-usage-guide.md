# Complete Usage Guide (End-to-End)

This guide shows exactly how to run, test, and demo the full project locally with remote Ollama API integration.

## 1) Prerequisites
- Python 3.11+
- Node.js 18+ and npm
- Git

## 2) Configure Environment
From repo root, create `.env` using `.env.example`, then set values:

```env
APP_ENV=development
DATABASE_URL=sqlite:///./data/claimflow.db
UPLOAD_DIR=./data/uploads
DATA_DIR=./data
PROMPT_VERSION=v1

ENABLE_LIVE_LLM=true
LLM_PROVIDER=ollama
LLM_BASE_URL=https://ollama.com/api
LLM_API_KEY=<your_ollama_api_key>
LLM_MODEL=qwen3:8b
LLM_TIMEOUT_SECONDS=45

NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
```

Notes:
- `LLM_API_KEY` should stay in your local `.env` only.
- Final claim outcomes remain deterministic even with LLM enabled.

## 3) Start Backend
From repo root:

```bash
python -m pip install -r apps/api/requirements.txt
uvicorn app.main:app --app-dir apps/api --reload
```

Verify:
- `http://localhost:8000/health`

## 4) Start Frontend
In a second terminal:

```bash
cd apps/web
npm install
npm run dev
```

Open:
- `http://localhost:3000/claims`

## 5) Seed Demo Scenarios
Option A (UI):
- Click `Seed Demo Scenarios` in the claims page.

Option B (CLI):

```bash
python scripts/seed_demo_data.py
```

Expected:
- 7 auto and 8 healthcare synthetic claims are loaded.

## 6) Run the Full Workflow (UI Path)
1. Open any claim from queue.
2. Click `Run Workflow`.
3. Inspect each section in claim detail:
- Intake completeness
- Extracted facts
- Validation issues
- Coverage result
- Fraud/anomaly signals
- Advisory findings
- Final decision
- Workflow timeline
- Audit events
- Communication drafts

Outcomes supported:
- `approve`
- `reject`
- `pend`
- `escalate`

## 7) Manual Claim Intake (What to Fill + What to Attach)
In `New Claim Intake`, fill:
- Domain: `Auto` or `Healthcare`
- Subtype: domain-specific subtype
- Incident / Service Date
- Policy / Member ID
- Claimant Name
- Estimated Amount

Attach text documents (`.txt`) for best demo reliability.

### Auto recommended docs
- `claim_form`
- `accident_narrative`
- `repair_estimate`
- `medical_report` (if injury involved)

### Healthcare recommended docs
- `claim_form`
- `billing_statement`
- `coding_summary`
- `prior_auth` (when prior authorization is required)

You can use existing packets from:
- `data/sample_claims/auto/*`
- `data/sample_claims/healthcare/*`

## 8) API-First Execution (Optional)
### Create claim
- `POST /claims`

### Upload docs
- `POST /claims/{claim_id}/documents`

### Run orchestration
- `POST /claims/{claim_id}/run`

### Inspect workflow and decision
- `GET /claims/{claim_id}/steps`
- `GET /claims/{claim_id}/decision`
- `GET /claims/{claim_id}`

### Human override
- `POST /claims/{claim_id}/review/approve`
- `POST /claims/{claim_id}/review/reject`
- `POST /claims/{claim_id}/review/pend`
- `POST /claims/{claim_id}/review/escalate`
- `POST /claims/{claim_id}/review/override`

## 9) Confirm LLM Integration is Active
With `ENABLE_LIVE_LLM=true`, these stages use LLM-first execution with deterministic fallback:
- Intake agent
- Extraction agent
- Contradiction detection
- Advisory generation
- Communication explanation drafts

Deterministic decision safety remains in:
- rule engine
- decision policy engine

## 10) Run Tests
From repo root:

```bash
pytest apps/api/app/tests -q
```

## 11) Run Evaluation Harness
From repo root:

```bash
python scripts/run_evals.py
```

This validates extraction/decision behavior on seeded fixtures and stores eval run summaries.

## 12) Interview Demo Script (Suggested)
1. Seed scenarios.
2. Open one `approve`, one `reject`, one `pend`, one `escalate`.
3. Show step-by-step timeline and audit trail.
4. Open decision panel and explain deterministic precedence.
5. Use reviewer override to change one decision and show audit log update.
6. Run eval harness and discuss quality metrics and safeguards.

## 13) Troubleshooting
- Workflow fails immediately:
  - verify backend is running and `.env` values are loaded.
- LLM appears inactive:
  - check `ENABLE_LIVE_LLM=true`
  - check `LLM_PROVIDER=ollama`
  - verify `LLM_API_KEY` is set and valid
  - restart backend after `.env` changes
- Frontend cannot reach backend:
  - confirm `NEXT_PUBLIC_API_BASE_URL=http://localhost:8000`
- Unexpected `pend` decisions:
  - check missing required docs and validation issues in claim detail.
