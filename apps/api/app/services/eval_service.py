from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import Settings
from app.models.claim import ClaimCase
from app.models.document import ClaimDocument
from app.models.evaluation_run import EvaluationRun
from app.models.extracted_fact import ExtractedFact
from app.services.utils import sha256_text
from app.services.workflow_service import WorkflowService


class EvalService:
    def __init__(self, db: Session, settings: Settings) -> None:
        self.db = db
        self.settings = settings

    def run(self) -> EvaluationRun:
        fixture_paths = sorted(Path("./evals/fixtures").glob("**/*.json"))
        started = datetime.utcnow()
        results: list[dict] = []
        eval_run_id = str(uuid4())

        for fixture_path in fixture_paths:
            loaded = json.loads(fixture_path.read_text(encoding="utf-8"))
            fixtures = loaded if isinstance(loaded, list) else [loaded]
            for fixture in fixtures:
                claim = self._create_eval_claim(fixture, eval_run_id)
                workflow = WorkflowService(self.db, self.settings)
                decision = workflow.run_claim(claim.id)
                expected = fixture["expected_decision"]
                actual = decision["decision"]
                passed = expected == actual
                extraction_recall = self._required_field_recall(claim.id, fixture["domain"])
                results.append(
                    {
                        "scenario_id": fixture["scenario_id"],
                        "domain": fixture["domain"],
                        "expected_decision": expected,
                        "actual_decision": actual,
                        "passed": passed,
                        "required_field_recall": extraction_recall,
                    }
                )

        pass_count = sum(1 for result in results if result["passed"])
        avg_recall = round(sum(result["required_field_recall"] for result in results) / max(len(results), 1), 3)
        routing_distribution: dict[str, int] = {}
        for result in results:
            routing_distribution[result["actual_decision"]] = routing_distribution.get(result["actual_decision"], 0) + 1
        auto_adjudication_rate = round(
            sum(1 for result in results if result["actual_decision"] in {"approve", "reject"}) / max(len(results), 1),
            3,
        )
        summary = {
            "total": len(results),
            "passed": pass_count,
            "failed": len(results) - pass_count,
            "decision_accuracy": round(pass_count / max(len(results), 1), 3),
            "avg_required_field_recall": avg_recall,
            "routing_distribution": routing_distribution,
            "auto_adjudication_rate": auto_adjudication_rate,
            "avg_latency_ms": None,
        }

        report_path = Path("./evals/reports/latest.json")
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(
            json.dumps({"started_at": started.isoformat(), "completed_at": datetime.utcnow().isoformat(), "summary": summary, "results": results}, indent=2),
            encoding="utf-8",
        )

        run = EvaluationRun(
            status="completed",
            started_at=started,
            completed_at=datetime.utcnow(),
            summary=summary,
            results=results,
        )
        self.db.add(run)
        self.db.commit()
        self.db.refresh(run)
        return run

    def _create_eval_claim(self, fixture: dict, eval_run_id: str) -> ClaimCase:
        claim = ClaimCase(
            claim_number=f"EVAL-{uuid4().hex[:10].upper()}",
            domain=fixture["domain"],
            subtype=fixture.get("subtype"),
            status="submitted",
            submitted_at=datetime.utcnow(),
            incident_or_service_date=datetime.strptime(fixture["incident_or_service_date"], "%Y-%m-%d").date(),
            policy_or_member_id=fixture.get("policy_or_member_id"),
            claimant_name=fixture.get("claimant_name"),
            estimated_amount=fixture.get("estimated_amount"),
            claim_payload={
                **fixture.get("claim_payload", {}),
                "fixture": fixture["scenario_id"],
                "eval_run_id": eval_run_id,
            },
            current_queue="manual_triage",
        )
        self.db.add(claim)
        self.db.flush()

        upload_dir = Path(self.settings.upload_dir) / claim.id
        upload_dir.mkdir(parents=True, exist_ok=True)

        for doc in fixture.get("documents", []):
            file_path = upload_dir / doc["filename"]
            file_path.write_text(doc["content"], encoding="utf-8")
            record = ClaimDocument(
                claim_id=claim.id,
                filename=doc["filename"],
                mime_type="text/plain",
                document_type=doc.get("document_type"),
                storage_path=str(file_path),
                ocr_text=doc["content"],
                metadata_json={"evaluation_fixture": fixture["scenario_id"]},
                fingerprint=sha256_text(doc["content"]),
            )
            self.db.add(record)

        self.db.commit()
        self.db.refresh(claim)
        return claim

    def _required_field_recall(self, claim_id: str, domain: str) -> float:
        required = {
            "auto": {"incident_date", "driver_name", "repair_estimate_amount"},
            "healthcare": {"member_id", "date_of_service", "procedure_codes"},
        }[domain]
        rows = list(self.db.scalars(select(ExtractedFact).where(ExtractedFact.claim_id == claim_id)).all())
        extracted = {row.key for row in rows}
        return round(len(required.intersection(extracted)) / max(len(required), 1), 3)
