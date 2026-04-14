# Implementation Plan

This plan operationalizes `instructions.md` as the source of truth.

## Milestone 1: Foundations and Scaffolding
1. Create monorepo folder structure for API, web app, shared packages, data, docs, evals, and scripts.
2. Implement FastAPI service skeleton, configuration, SQLAlchemy setup, and base models.
3. Implement Next.js + TypeScript + Tailwind scaffold with reviewer dashboard shell.
4. Create seeded synthetic reference datasets and sample claim packets.
5. Implement claim CRUD and document upload APIs.

## Milestone 2: Document Processing and Agent Contracts
1. Implement parser abstraction for text/PDF ingestion with OCR hook.
2. Add versioned prompt files and prompt contract docs.
3. Implement agent interfaces and structured outputs:
   - intake agent
   - extraction agent
   - contradiction agent
   - domain advisory agent
   - explanation agent
4. Persist extracted facts and step outputs.

## Milestone 3: Deterministic Decision Backbone
1. Build rule engine with versioned YAML rule packs.
2. Build auto coverage evaluator and healthcare benefit evaluator.
3. Build duplicate detector and anomaly scoring.
4. Build threshold policy + deterministic final decision engine.
5. Enforce explicit workflow state machine transitions.

## Milestone 4: End-to-End Workflows
1. Implement shared orchestrator and replayable step runner.
2. Implement full auto claims flow.
3. Implement full healthcare claims flow.
4. Add communication draft generation.
5. Add rerun-step endpoint behavior.

## Milestone 5: Human Review and Auditability
1. Implement reviewer queues and review actions.
2. Implement override flows and immutable audit timeline entries.
3. Add claim decision rationale with evidence references and trace IDs.
4. Add claim detail aggregation endpoints for UI.

## Milestone 6: Evals, Tests, and Demo Polish
1. Implement eval fixtures and evaluation runner.
2. Add unit + integration tests for core deterministic logic and workflows.
3. Build polished UI pages:
   - claims list
   - new claim intake
   - claim detail with timeline, evidence, decision, and audit
   - evaluation dashboard
4. Finalize docs:
   - architecture
   - workflow spec
   - prompt contracts
   - demo script
   - README

## Execution Notes
- Prefer deterministic safety for final outcomes.
- Use LLM-compatible interfaces but keep local deterministic fallback for runnable demo.
- Resolve ambiguities with interview-defensible choices and document in architecture notes.