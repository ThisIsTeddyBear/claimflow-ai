# Workflow Spec

## Shared Lifecycle
States:
- draft
- submitted
- intake_processing
- awaiting_documents
- under_extraction
- under_validation
- under_coverage_review
- under_fraud_review
- under_domain_review
- under_decisioning
- pending_human_review
- approved
- rejected
- pended
- ready_for_settlement
- closed

State transitions are validated by `ClaimStateMachine` (`apps/api/app/workflows/state_machine.py`).

## Supervisor Execution Order
1. intake
2. extraction
3. validation
4. coverage_review
5. fraud_review
6. domain_advisory
7. decisioning
8. communication

Each step is persisted to `workflow_steps` with:
- `run_id`
- `step_name`
- `status`
- state before/after
- timing and latency
- structured output payload

## Decision Matrix
Precedence implemented in `DecisionPolicyEngine`:
1. hard reject rules / hard coverage fail => reject
2. missing critical docs/info => pend
3. high risk or advisory uncertainty => escalate
4. covered + confident + threshold eligible => approve
5. fallback => pend

## Human-in-the-Loop
Reviewer endpoints:
- approve/reject/pend/escalate
- override

All review actions write a new decision record and audit event including:
- reviewer id
- previous decision
- new decision
- notes
- timestamp

## Rerun Behavior
`POST /claims/{id}/rerun-step/{step}` triggers a fresh workflow execution and records a rerun audit event with requested step marker.