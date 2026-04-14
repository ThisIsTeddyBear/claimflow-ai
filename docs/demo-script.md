# Demo Script

## 1. Start Services
1. Start API from repo root:
   - `python -m pip install -r apps/api/requirements.txt`
   - `uvicorn app.main:app --app-dir apps/api --reload`
2. Start web app:
   - `cd apps/web`
   - `npm install`
   - `npm run dev`

## 2. Seed Demo Data
- In UI, click **Seed Demo Scenarios** on `/claims`.
- Or API call: `POST /demo/seed`.

## 3. Walk Through Representative Scenarios
1. Auto straightforward approve (`auto_01_straightforward_approve`)
2. Auto policy inactive reject (`auto_02_policy_inactive_reject`)
3. Auto narrative mismatch escalate (`auto_04_narrative_mismatch_escalate`)
4. Healthcare routine approve (`health_01_routine_approve`)
5. Healthcare missing prior auth pend (`health_03_missing_prior_auth_pend`)
6. Healthcare duplicate billing escalate (`health_04_duplicate_billing_escalate`)

## 4. Show Explainability
On claim detail page:
- extracted facts
- validation issues
- coverage result
- anomaly signals
- advisory findings
- final decision card
- workflow timeline
- audit trail
- communication drafts

## 5. Show Human Override
- Use reviewer action panel to override an automated decision.
- Show new decision record and updated audit trail.

## 6. Run Evaluations
- From `/evals`, click **Run Evaluations**.
- Review aggregate accuracy and per-scenario expected vs actual results.

## 7. Interview Talking Points
- Deterministic decision precedence protects against unconstrained LLM behavior.
- LLM/agent outputs are structured and auditable.
- Workflow steps are replayable with traceable step-level artifacts.
- Human review and override are first-class controls.