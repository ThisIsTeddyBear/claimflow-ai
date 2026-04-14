# ClaimFlow AI

Interview-grade hybrid multi-agent claims adjudication platform for:
- auto accident insurance claims
- healthcare claims

The system combines structured agent extraction with deterministic decision policy controls so approvals/rejections are explainable, auditable, and safe.

## Why This Design
Pure LLM adjudication is unsafe for claims operations. ClaimFlow AI applies this principle:

- LLM-compatible agents interpret unstructured evidence
- deterministic policy/rule engines make final decisions
- low-confidence/high-risk cases route to human review
- all steps are traceable and replayable

## Supported Outcomes
- `approve`
- `reject`
- `pend` (request more information)
- `escalate` (human review queue)

## Core Capabilities
- shared orchestration backbone for both domains
- explicit state machine + replayable workflow steps
- deterministic rules + coverage/benefit evaluators
- structured agent outputs and prompt contracts
- auditable decision traces and human override logs
- seeded synthetic scenarios (7 auto + 7 healthcare)
- evaluation harness for decision quality checks
- polished reviewer UI (queue, detail, timeline, audit, override)

## Repository Layout
```text
.
+- apps/
�  +- api/
�  �  +- app/
�  �  �  +- api/routes
�  �  �  +- models
�  �  �  +- repositories
�  �  �  +- schemas
�  �  �  +- services
�  �  �  +- workflows
�  �  �  +- rules
�  �  �  +- prompts
�  �  �  +- seed
�  �  �  +- tests
�  �  +- requirements.txt
�  +- web/
�     +- app
�     +- components
�     +- lib
�     +- types
+- data/
�  +- sample_claims/
�  +- synthetic_reference/
+- docs/
+- evals/
+- scripts/
```

## Architecture (High Level)
```text
[Next.js Reviewer UI]
          |
          v
     [FastAPI API]
          |
          v
 [Workflow Orchestrator + State Machine]
   |        |         |          |
   v        v         v          v
[Agents] [Rules] [Coverage] [Anomaly/Duplicate]
   |___________________________________________|
                     |
                     v
         [Deterministic Decision Policy]
                     |
                     v
         [Decision + Audit + Human Queues]
                     |
                     v
       [PostgreSQL-friendly SQLAlchemy Store]
```

## Workflow Steps
1. intake
2. extraction
3. validation
4. coverage review
5. fraud/anomaly review
6. domain advisory
7. deterministic decisioning
8. communication drafts

## Decision Precedence
1. hard reject rules / hard coverage fail
2. missing critical info -> pend
3. high risk, contradictions, low confidence -> escalate
4. clean covered claim under threshold -> approve

## Local Setup

### 1) Backend
From repo root:

```bash
python -m pip install -r apps/api/requirements.txt
uvicorn app.main:app --app-dir apps/api --reload
```

API health check:
- `GET http://localhost:8000/health`

### 2) Frontend
In a second terminal:

```bash
cd apps/web
npm install
npm run dev
```

Open:
- `http://localhost:3000/claims`

### 3) Seed Demo Scenarios
Either:
- UI button: **Seed Demo Scenarios** on `/claims`
- or CLI/API:

```bash
python scripts/seed_demo_data.py
```

## Demo Flow
1. Open Claims Queue (`/claims`)
2. Seed scenarios
3. Open a claim and run workflow
4. Inspect:
   - extracted facts
   - validation issues
   - coverage result
   - fraud/anomaly signals
   - advisory findings
   - final decision
   - workflow timeline
   - audit trail
   - communication drafts
5. Use reviewer actions to override an automated decision
6. Open `/evals` and run evaluation harness

Detailed narrative: [`docs/demo-script.md`](https://github.com/ThisIsTeddyBear/claimflow-ai/blob/main/docs/demo-script.md)

## API Endpoints
### Claims
- `POST /claims`
- `GET /claims`
- `GET /claims/{claim_id}`
- `PATCH /claims/{claim_id}`

### Documents
- `POST /claims/{claim_id}/documents`
- `GET /claims/{claim_id}/documents`
- `GET /documents/{document_id}`

### Workflow
- `POST /claims/{claim_id}/run`
- `GET /claims/{claim_id}/steps`
- `GET /claims/{claim_id}/decision`
- `POST /claims/{claim_id}/rerun-step/{step_name}`

### Human Review
- `POST /claims/{claim_id}/review/approve`
- `POST /claims/{claim_id}/review/reject`
- `POST /claims/{claim_id}/review/pend`
- `POST /claims/{claim_id}/review/escalate`
- `POST /claims/{claim_id}/review/override`

### Demo / Evals
- `POST /demo/seed`
- `GET /evals`
- `POST /evals/run`

## Prompt Contracts
Versioned prompt contracts are stored in:
- `apps/api/app/prompts/intake_agent/v1.json`
- `apps/api/app/prompts/document_extraction_agent/v1.json`
- `apps/api/app/prompts/contradiction_agent/v1.json`
- `apps/api/app/prompts/auto_liability_advisory_agent/v1.json`
- `apps/api/app/prompts/healthcare_plausibility_advisory_agent/v1.json`
- `apps/api/app/prompts/explanation_agent/v1.json`

See: [`docs/prompt-contracts.md`](https://github.com/ThisIsTeddyBear/claimflow-ai/blob/main/docs/prompt-contracts.md)

## Seeded Scenario Coverage
- Auto: straightforward approve, inactive policy reject, missing docs pend, narrative mismatch escalate, photo reuse/high value escalate, excluded driver reject, low-impact high-injury escalate
- Healthcare: routine covered approve, inactive member reject, missing prior auth pend, duplicate billing escalate, plausibility/high-cost escalate, excluded cosmetic reject, corrected claim approve

Source: `apps/api/app/seed/scenarios.json`

## Evaluation Harness
Run from CLI:

```bash
python scripts/run_evals.py
```

Outputs:
- persisted DB eval run records
- `evals/reports/latest.json`

## Tests
```bash
pytest apps/api/app/tests -q
```

Coverage includes:
- rules engine
- decision policy precedence
- duplicate detector
- end-to-end auto workflow integration

## Safety Controls
- prompt-injection defensive contracts
- deterministic final decision gate
- fraud signals escalate rather than auto-deny
- human override with immutable audit events
- synthetic data only

## Docs
- [`docs/architecture.md`](https://github.com/ThisIsTeddyBear/claimflow-ai/blob/main/docs/architecture.md)
- [`docs/workflow-spec.md`](https://github.com/ThisIsTeddyBear/claimflow-ai/blob/main/docs/workflow-spec.md)
- [`docs/prompt-contracts.md`](https://github.com/ThisIsTeddyBear/claimflow-ai/blob/main/docs/prompt-contracts.md)
- [`docs/demo-script.md`](https://github.com/ThisIsTeddyBear/claimflow-ai/blob/main/docs/demo-script.md)
- [`docs/implementation-plan.md`](https://github.com/ThisIsTeddyBear/claimflow-ai/blob/main/docs/implementation-plan.md)
- [`docs/progress.md`](https://github.com/ThisIsTeddyBear/claimflow-ai/blob/main/docs/progress.md)

## Limitations
- Uses deterministic extraction heuristics by default (LLM integration optional via env config)
- Text-first document parsing; scanned OCR is a stub-ready extension
- Demo-grade policy/benefit logic and anomaly rules

## Future Improvements
- stronger OCR and layout-aware extraction
- line-level healthcare adjudication outcomes
- richer fraud graph analytics
- prompt/version regression dashboard
- policy document retrieval + rationale citation highlighting
- active learning from human overrides

## Interview Talking Points
- Why hybrid LLM + deterministic architecture is safer
- How state machine + persisted step outputs improve explainability
- How rule packs can be versioned and governed
- How human-in-the-loop controls mitigate automation risk
- How eval harness exposes false positive/false negative tradeoffs