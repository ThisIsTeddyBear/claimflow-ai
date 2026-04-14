# Architecture

## Overview
ClaimFlow AI is a hybrid adjudication platform where deterministic policy controls own final claim outcomes while agent modules extract and interpret unstructured evidence.

## Stack
- Backend: FastAPI, SQLAlchemy, Pydantic v2, PostgreSQL-friendly schema (SQLite default for local dev)
- Frontend: Next.js App Router, TypeScript, Tailwind CSS
- Workflow: Explicit supervisor/orchestrator with replayable step persistence
- Data: Synthetic reference datasets and seeded scenario claim packets

## Core Components
1. API layer (`apps/api/app/api/routes`)
- Claim CRUD
- Document upload/lookup
- Workflow run/rerun
- Human review actions
- Seed/eval endpoints

2. Orchestration layer (`apps/api/app/services/workflow_service.py`)
- Shared workflow backbone across auto + healthcare
- Explicit state transitions via `ClaimStateMachine`
- Step-level persistence to `workflow_steps`
- Audit event logging at start/completion/failure and decision events

3. Agent layer (`apps/api/app/services/*_agent.py`)
- Intake agent
- Extraction agent
- Contradiction agent
- Domain advisory agent
- Explanation agent

4. Deterministic services
- Coverage/benefits evaluator
- Rules engine (YAML-backed)
- Duplicate detector
- Anomaly scoring
- Threshold policy
- Final decision policy engine (deterministic precedence)

5. Persistence
- Claims, documents, facts, issues, coverage/fraud/advisory outputs
- Decision records with reasons/rule refs
- Communication drafts
- Audit events
- Evaluation run records

## Decision Safety Model
Decision precedence:
1. deterministic reject gates (hard fail / high-priority rules)
2. missing critical information -> pend
3. risk/ambiguity/low-confidence -> escalate
4. clean covered claim under threshold -> approve

LLMs are optional and non-authoritative. Final approval/rejection never depends solely on unconstrained model prose.

## Ambiguity Resolutions
- `PEND` is used for recoverable missing info and prior-auth gaps.
- Contradictions are treated as quality/risk signals; they do not directly imply fraud.
- Fraud/anomaly signals route to human review (`ESCALATE`) rather than direct denial.
- Local-first defaults to deterministic agent fallbacks so the demo runs without external LLM credentials.

## Replayability and Auditability
- Each workflow step has `run_id`, timing, input-derived output, and success/failure status.
- Every major event logs actor type (`system`, `agent`, `human`) and payload.
- Human overrides create new decision records with pointer to overridden decision.

## Security/Safety Practices (Demo Scope)
- Prompt contracts enforce hostile-document assumptions and strict JSON output.
- Synthetic data only; no production PHI/PII.
- Reviewer endpoints are separated from read endpoints.