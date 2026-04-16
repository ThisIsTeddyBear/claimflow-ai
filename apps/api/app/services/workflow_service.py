from __future__ import annotations

from datetime import datetime
from pathlib import Path
from statistics import mean
from typing import Any
from uuid import uuid4

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.config import Settings
from app.models.advisory_result import AdvisoryResult
from app.models.claim import ClaimCase
from app.models.communication_draft import CommunicationDraft
from app.models.coverage_result import CoverageResult
from app.models.extracted_fact import ExtractedFact
from app.models.fraud_result import FraudResult
from app.models.validation_issue import ValidationIssue
from app.repositories.audit_repository import AuditRepository
from app.repositories.claim_repository import ClaimRepository
from app.repositories.decision_repository import DecisionRepository
from app.repositories.document_repository import DocumentRepository
from app.repositories.workflow_repository import WorkflowRepository
from app.services.advisory_agent import AdvisoryAgent
from app.services.anomaly_service import AnomalyService
from app.services.coverage_service import CoverageService
from app.services.decision_policy import DecisionPolicyEngine
from app.services.duplicate_detector import DuplicateDetector
from app.services.explanation_agent import ExplanationAgent
from app.services.extraction_agent import ExtractionAgent
from app.services.intake_agent import IntakeAgent
from app.services.llm_client import LLMClient
from app.services.prompt_registry import PromptRegistry
from app.services.rule_engine import RuleEngine
from app.services.threshold_policy import ThresholdPolicy
from app.services.validation_service import ValidationService
from app.services.contradiction_agent import ContradictionAgent
from app.workflows.state_machine import ClaimStateMachine


class WorkflowService:
    def __init__(self, db: Session, settings: Settings) -> None:
        self.db = db
        self.settings = settings

        self.claim_repo = ClaimRepository(db)
        self.document_repo = DocumentRepository(db)
        self.decision_repo = DecisionRepository(db)
        self.workflow_repo = WorkflowRepository(db)
        self.audit_repo = AuditRepository(db)

        llm_client = LLMClient(settings)
        app_root = Path(__file__).resolve().parents[1]
        prompt_registry = PromptRegistry(str(app_root / "prompts"))

        self.intake_agent = IntakeAgent(
            llm_client=llm_client,
            prompt_registry=prompt_registry,
            prompt_version=settings.prompt_version,
        )
        self.extraction_agent = ExtractionAgent(
            llm_client=llm_client,
            prompt_registry=prompt_registry,
            prompt_version=settings.prompt_version,
        )
        contradiction_agent = ContradictionAgent(
            llm_client=llm_client,
            prompt_registry=prompt_registry,
            prompt_version=settings.prompt_version,
        )
        self.validation_service = ValidationService(contradiction_agent=contradiction_agent)
        self.coverage_service = CoverageService(settings.data_dir)

        self.threshold_policy = ThresholdPolicy(
            auto_approval_ceiling=settings.auto_approval_ceiling,
            fraud_escalation_threshold=settings.fraud_escalation_threshold,
            confidence_threshold=settings.confidence_threshold,
            high_value_threshold_auto=settings.high_value_threshold_auto,
            high_value_threshold_healthcare=settings.high_value_threshold_healthcare,
        )
        self.anomaly_service = AnomalyService(self.threshold_policy)
        self.advisory_agent = AdvisoryAgent(
            llm_client=llm_client,
            prompt_registry=prompt_registry,
            prompt_version=settings.prompt_version,
        )
        self.rule_engine = RuleEngine(str(app_root / "rules"))
        self.decision_policy = DecisionPolicyEngine(self.threshold_policy)
        self.explanation_agent = ExplanationAgent(
            llm_client=llm_client,
            prompt_registry=prompt_registry,
            prompt_version=settings.prompt_version,
        )
        self.state_machine = ClaimStateMachine()

    def run_claim(self, claim_id: str, rerun_from_step: str | None = None) -> dict[str, Any]:
        claim = self.claim_repo.get(claim_id)
        if not claim:
            raise ValueError(f"Claim not found: {claim_id}")

        run_id = str(uuid4())
        if rerun_from_step:
            self.audit_repo.log(
                claim_id=claim_id,
                event_type="workflow_rerun_requested",
                actor_type="system",
                actor_id="orchestrator",
                payload={"rerun_from_step": rerun_from_step},
            )

        self._clear_non_decision_artifacts(claim_id)

        intake_output = self._execute_step(claim, run_id, "intake", "intake_processing", lambda: self._run_intake(claim))

        if intake_output.get("missing_docs"):
            decision = {
                "decision": "pend",
                "reasons": ["Missing critical documents for adjudication."] + [f"Missing: {doc}" for doc in intake_output["missing_docs"]],
                "evidence_refs": [],
                "required_next_action": "Request additional documentation",
                "reviewer_queue": None,
                "confidence": 0.94,
                "rule_refs": [],
            }
            decision_record = self._persist_decision(claim, decision, step_ref="intake")
            self._set_claim_status(claim, "pended")
            self._run_communication(claim, decision_record)
            self.audit_repo.log(
                claim_id=claim.id,
                event_type="workflow_completed",
                actor_type="system",
                actor_id="orchestrator",
                payload={"run_id": run_id, "decision": "pend", "reason": "missing_docs"},
            )
            return decision_record

        extraction_output = self._execute_step(claim, run_id, "extraction", "under_extraction", lambda: self._run_extraction(claim))
        validation_output = self._execute_step(claim, run_id, "validation", "under_validation", lambda: self._run_validation(claim))

        coverage_output = self._execute_step(
            claim,
            run_id,
            "coverage_review",
            "under_coverage_review",
            lambda: self._run_coverage(claim),
        )

        fraud_output = self._execute_step(
            claim,
            run_id,
            "fraud_review",
            "under_fraud_review",
            lambda: self._run_fraud(claim, validation_output),
        )

        advisory_output = self._execute_step(
            claim,
            run_id,
            "domain_advisory",
            "under_domain_review",
            lambda: self._run_advisory(claim, validation_output),
        )

        decision_output = self._execute_step(
            claim,
            run_id,
            "decisioning",
            "under_decisioning",
            lambda: self._run_decision(
                claim,
                intake_output,
                extraction_output,
                validation_output,
                coverage_output,
                fraud_output,
                advisory_output,
            ),
        )

        decision_record = self._persist_decision(claim, decision_output, step_ref="decisioning")
        self._apply_decision_status(claim, decision_output)

        self._execute_step(
            claim,
            run_id,
            "communication",
            claim.status,
            lambda: self._run_communication(claim, decision_record),
        )

        self.audit_repo.log(
            claim_id=claim.id,
            event_type="workflow_completed",
            actor_type="system",
            actor_id="orchestrator",
            payload={"run_id": run_id, "decision": decision_record["decision"]},
        )
        return decision_record

    def rerun_step(self, claim_id: str, step_name: str) -> dict[str, Any]:
        return self.run_claim(claim_id, rerun_from_step=step_name)

    def _execute_step(self, claim: ClaimCase, run_id: str, step_name: str, status: str, fn) -> dict[str, Any]:
        state_before = claim.status
        self._set_claim_status(claim, status)

        step = self.workflow_repo.start_step(
            {
                "claim_id": claim.id,
                "run_id": run_id,
                "step_name": step_name,
                "status": "running",
                "state_before": state_before,
                "state_after": status,
                "started_at": datetime.utcnow(),
                "output": {},
            }
        )

        self.audit_repo.log(
            claim_id=claim.id,
            event_type="workflow_step_started",
            actor_type="system",
            actor_id="orchestrator",
            payload={"run_id": run_id, "step_name": step_name, "state_before": state_before, "state_after": status},
        )

        try:
            output = fn()
            self.workflow_repo.complete_step(step, status="success", state_after=claim.status, output=output)
            self.audit_repo.log(
                claim_id=claim.id,
                event_type="workflow_step_completed",
                actor_type="system",
                actor_id="orchestrator",
                payload={"run_id": run_id, "step_name": step_name},
            )
            return output
        except Exception as exc:
            self.workflow_repo.complete_step(
                step,
                status="failed",
                state_after=claim.status,
                output={"error": str(exc)},
                error_message=str(exc),
            )
            self.audit_repo.log(
                claim_id=claim.id,
                event_type="workflow_step_failed",
                actor_type="system",
                actor_id="orchestrator",
                payload={"run_id": run_id, "step_name": step_name, "error": str(exc)},
            )
            raise

    def _run_intake(self, claim: ClaimCase) -> dict[str, Any]:
        docs = self.document_repo.list_for_claim(claim.id)
        output = self.intake_agent.run(
            domain=claim.domain,
            subtype=claim.subtype,
            documents=[{"document_type": doc.document_type, "filename": doc.filename} for doc in docs],
            claim_payload=claim.claim_payload,
        )
        return output.model_dump()

    def _run_extraction(self, claim: ClaimCase) -> dict[str, Any]:
        docs = self.document_repo.list_for_claim(claim.id)
        outputs: list[dict] = []

        for doc in docs:
            extraction = self.extraction_agent.run(
                domain=claim.domain,
                filename=doc.filename,
                document_type=doc.document_type,
                text=doc.ocr_text or "",
            )
            doc.document_type = extraction.document_type
            doc.extraction_confidence = extraction.confidence
            self.db.add(doc)

            for key, entity in extraction.entities.items():
                fact = ExtractedFact(
                    claim_id=claim.id,
                    source_document_id=doc.id,
                    key=key,
                    value={"value": entity.value},
                    confidence=entity.confidence,
                    normalized_value={"value": entity.value},
                    source_excerpt=entity.source_excerpt,
                )
                self.db.add(fact)
            outputs.append({"document_id": doc.id, **extraction.model_dump()})

        self.db.commit()
        return {"documents": outputs, "document_count": len(outputs)}

    def _run_validation(self, claim: ClaimCase) -> dict[str, Any]:
        extracted = self._fetch_extracted_fact_rows(claim.id)
        issues = self.validation_service.validate(domain=claim.domain, extracted_facts=extracted, claim_payload=claim.claim_payload)

        created: list[dict] = []
        for issue in issues:
            record = ValidationIssue(claim_id=claim.id, **issue)
            self.db.add(record)
            self.db.flush()
            created.append({"id": record.id, **issue})

        self.db.commit()
        return {"issues": created, "issue_count": len(created)}

    def _run_coverage(self, claim: ClaimCase) -> dict[str, Any]:
        fact_map = self._build_fact_map(claim.id)
        coverage = self.coverage_service.evaluate(domain=claim.domain, claim=claim, fact_map=fact_map)
        record = CoverageResult(claim_id=claim.id, **coverage)
        self.db.add(record)
        self.db.commit()
        self.db.refresh(record)
        return coverage

    def _run_fraud(self, claim: ClaimCase, validation_output: dict[str, Any]) -> dict[str, Any]:
        docs = self.document_repo.list_for_claim(claim.id)
        fingerprints = [doc.fingerprint for doc in docs if doc.fingerprint]
        duplicate_result = DuplicateDetector(self.db).detect(claim, self._build_fact_map(claim.id), fingerprints)
        anomaly = self.anomaly_service.score(
            duplicate_result=duplicate_result,
            validation_issues=validation_output.get("issues", []),
            estimated_amount=claim.estimated_amount,
            domain=claim.domain,
        )

        record = FraudResult(claim_id=claim.id, **anomaly)
        self.db.add(record)
        self.db.commit()
        self.db.refresh(record)
        return {**anomaly, "duplicate_result": duplicate_result}

    def _run_advisory(self, claim: ClaimCase, validation_output: dict[str, Any]) -> dict[str, Any]:
        fact_map = self._build_fact_map(claim.id)
        advisory = self.advisory_agent.run(
            claim_id=claim.id,
            domain=claim.domain,
            extracted_fact_map=fact_map,
            validation_issues=validation_output.get("issues", []),
            estimated_amount=claim.estimated_amount,
        )
        record = AdvisoryResult(
            claim_id=claim.id,
            domain=claim.domain,
            findings=[item.model_dump() for item in advisory.findings],
            uncertainty_flags=advisory.uncertainty_flags,
            escalation_recommended=advisory.escalation_recommended,
            confidence=advisory.confidence,
            agent_version=self.settings.prompt_version,
        )
        self.db.add(record)
        self.db.commit()
        self.db.refresh(record)
        return advisory.model_dump()

    def _run_decision(
        self,
        claim: ClaimCase,
        intake: dict[str, Any],
        extraction: dict[str, Any],
        validation: dict[str, Any],
        coverage: dict[str, Any],
        fraud: dict[str, Any],
        advisory: dict[str, Any],
    ) -> dict[str, Any]:
        facts = self._build_fact_map(claim.id)
        rule_facts = {
            **facts,
            "coverage": coverage,
            "anomaly": {"risk_score": fraud.get("risk_score")},
            "intake": {
                "completeness_score": intake.get("completeness_score", 0),
                "missing_docs": intake.get("missing_docs", []),
                "missing_docs_count": len(intake.get("missing_docs", [])),
            },
            "policy_active": not any("inactive" in reason.lower() for reason in coverage.get("reasons", [])),
            "member_active_on_dos": not any("inactive" in reason.lower() for reason in coverage.get("reasons", [])),
            "is_duplicate": fraud.get("duplicate_result", {}).get("is_duplicate", False),
        }
        rule_matches = self.rule_engine.evaluate(domain=claim.domain, facts=rule_facts)

        confidences = [
            intake.get("confidence", 0.6),
            self._average_document_confidence(extraction),
            coverage.get("confidence", 0.7),
            advisory.get("confidence", 0.7),
        ]
        overall_confidence = round(mean(confidences), 3)

        return self.decision_policy.decide(
            domain=claim.domain,
            intake=intake,
            validation_issues=validation.get("issues", []),
            coverage=coverage,
            anomaly=fraud,
            advisory=advisory,
            rule_matches=rule_matches,
            overall_confidence=overall_confidence,
            estimated_amount=claim.estimated_amount,
        )

    def _run_communication(self, claim: ClaimCase, decision: dict[str, Any]) -> dict[str, Any]:
        audiences = ["internal", "claimant" if claim.domain == "auto" else "provider", "adjuster"]
        created: list[dict] = []

        next_steps = [decision.get("required_next_action") or "No additional action"]
        for audience in audiences:
            draft = self.explanation_agent.generate(
                audience=audience,
                decision=decision["decision"],
                reasons=decision.get("reasons", []),
                next_steps=next_steps,
            )
            record = CommunicationDraft(
                claim_id=claim.id,
                audience=audience,
                title=draft.title,
                summary=draft.summary,
                reasons=draft.reasons,
                next_steps=draft.next_steps,
                tone=draft.tone,
                prompt_version=self.settings.prompt_version,
            )
            self.db.add(record)
            self.db.flush()
            created.append({"id": record.id, "audience": audience, "title": draft.title})

        self.db.commit()
        return {"draft_count": len(created), "drafts": created}

    def _persist_decision(self, claim: ClaimCase, decision: dict[str, Any], step_ref: str) -> dict[str, Any]:
        record = self.decision_repo.create(
            {
                "claim_id": claim.id,
                "decision": decision["decision"],
                "reasons": decision.get("reasons", []),
                "evidence_refs": decision.get("evidence_refs", []),
                "required_next_action": decision.get("required_next_action"),
                "reviewer_queue": decision.get("reviewer_queue"),
                "confidence": decision.get("confidence", 0.8),
                "rule_refs": decision.get("rule_refs", []),
                "step_ref": step_ref,
                "decided_by": "system",
                "decided_by_id": "orchestrator",
            }
        )

        claim.final_decision_id = record.id
        claim.current_queue = decision.get("reviewer_queue")
        self.db.add(claim)
        self.db.commit()
        self.db.refresh(record)

        payload = {
            "id": record.id,
            "decision": record.decision,
            "reasons": record.reasons,
            "evidence_refs": record.evidence_refs,
            "required_next_action": record.required_next_action,
            "reviewer_queue": record.reviewer_queue,
            "confidence": record.confidence,
            "rule_refs": record.rule_refs,
            "step_ref": record.step_ref,
            "decided_by": record.decided_by,
            "decided_by_id": record.decided_by_id,
            "override_of_decision_id": record.override_of_decision_id,
            "claim_id": record.claim_id,
            "created_at": record.created_at.isoformat() if record.created_at else None,
        }

        self.audit_repo.log(
            claim_id=claim.id,
            event_type="decision_recorded",
            actor_type="system",
            actor_id="decision_policy_engine",
            payload={"decision": record.decision, "rule_refs": record.rule_refs},
        )
        return payload

    def _apply_decision_status(self, claim: ClaimCase, decision: dict[str, Any]) -> None:
        mapping = {
            "approve": "approved",
            "reject": "rejected",
            "pend": "pended",
            "escalate": "pending_human_review",
        }
        self._set_claim_status(claim, mapping[decision["decision"]])

    def _set_claim_status(self, claim: ClaimCase, status: str) -> None:
        if not self.state_machine.can_transition(claim.status, status):
            # Recovery path: allow a fresh rerun to restart from intake when claims
            # are left in stale in-progress states after an interrupted request.
            if not (status == "intake_processing" and claim.status != "draft"):
                raise ValueError(f"Invalid status transition: {claim.status} -> {status}")
        claim.status = status
        claim.updated_at = datetime.utcnow()
        self.db.add(claim)
        self.db.commit()
        self.db.refresh(claim)

    def _fetch_extracted_fact_rows(self, claim_id: str) -> list[dict[str, Any]]:
        stmt = select(ExtractedFact).where(ExtractedFact.claim_id == claim_id)
        rows = list(self.db.scalars(stmt).all())
        return [
            {
                "id": row.id,
                "key": row.key,
                "value": row.value.get("value") if isinstance(row.value, dict) else row.value,
                "confidence": row.confidence,
                "source_document_id": row.source_document_id,
            }
            for row in rows
        ]

    def _build_fact_map(self, claim_id: str) -> dict[str, Any]:
        rows = self._fetch_extracted_fact_rows(claim_id)
        fact_map: dict[str, Any] = {}
        for row in sorted(rows, key=lambda item: item["confidence"], reverse=True):
            if row["key"] not in fact_map:
                fact_map[row["key"]] = row["value"]
        return fact_map

    @staticmethod
    def _average_document_confidence(extraction_output: dict[str, Any]) -> float:
        docs = extraction_output.get("documents", [])
        if not docs:
            return 0.5
        confidences = [doc.get("confidence", 0.5) for doc in docs]
        return round(mean(confidences), 3)

    def _clear_non_decision_artifacts(self, claim_id: str) -> None:
        self.db.execute(delete(ExtractedFact).where(ExtractedFact.claim_id == claim_id))
        self.db.execute(delete(ValidationIssue).where(ValidationIssue.claim_id == claim_id))
        self.db.execute(delete(CoverageResult).where(CoverageResult.claim_id == claim_id))
        self.db.execute(delete(FraudResult).where(FraudResult.claim_id == claim_id))
        self.db.execute(delete(AdvisoryResult).where(AdvisoryResult.claim_id == claim_id))
        self.db.execute(delete(CommunicationDraft).where(CommunicationDraft.claim_id == claim_id))
        self.db.commit()
