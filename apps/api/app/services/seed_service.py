from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import Settings
from app.models.claim import ClaimCase
from app.models.document import ClaimDocument
from app.services.utils import sha256_text


class DemoSeedService:
    def __init__(self, db: Session, settings: Settings) -> None:
        self.db = db
        self.settings = settings

    def seed(self) -> dict:
        scenarios_path = Path("./apps/api/app/seed/scenarios.json")
        scenarios = json.loads(scenarios_path.read_text(encoding="utf-8"))

        existing = list(self.db.scalars(select(ClaimCase)).all())
        existing_scenario_ids = {
            claim.claim_payload.get("scenario_id")
            for claim in existing
            if isinstance(claim.claim_payload, dict) and claim.claim_payload.get("scenario_id")
        }

        created_claims = 0
        created_documents = 0

        for scenario in scenarios:
            scenario_id = scenario["scenario_id"]
            if scenario_id in existing_scenario_ids:
                continue

            claim = ClaimCase(
                claim_number=f"SCN-{scenario_id[:18].upper()}",
                domain=scenario["domain"],
                subtype=scenario.get("subtype"),
                status="submitted",
                submitted_at=datetime.utcnow(),
                incident_or_service_date=datetime.strptime(scenario["incident_or_service_date"], "%Y-%m-%d").date(),
                policy_or_member_id=scenario.get("policy_or_member_id"),
                claimant_name=scenario.get("claimant_name"),
                estimated_amount=scenario.get("estimated_amount"),
                claim_payload={
                    **scenario.get("claim_payload", {}),
                    "scenario_id": scenario_id,
                    "expected_decision": scenario.get("expected_decision"),
                },
                current_queue="manual_triage",
            )
            self.db.add(claim)
            self.db.flush()
            created_claims += 1

            upload_dir = Path(self.settings.upload_dir) / claim.id
            upload_dir.mkdir(parents=True, exist_ok=True)

            scenario_sample_dir = Path(self.settings.data_dir) / "sample_claims" / scenario["domain"] / scenario_id
            scenario_sample_dir.mkdir(parents=True, exist_ok=True)

            for doc in scenario.get("documents", []):
                filename = doc["filename"]
                content = doc["content"]
                doc_type = doc.get("document_type")

                sample_path = scenario_sample_dir / filename
                sample_path.write_text(content, encoding="utf-8")

                stored_path = upload_dir / filename
                stored_path.write_text(content, encoding="utf-8")

                record = ClaimDocument(
                    claim_id=claim.id,
                    filename=filename,
                    mime_type="text/plain",
                    document_type=doc_type,
                    storage_path=str(stored_path),
                    ocr_text=content,
                    extraction_confidence=None,
                    metadata_json={"seeded": True, "scenario_id": scenario_id},
                    fingerprint=sha256_text(content),
                )
                self.db.add(record)
                created_documents += 1

        self.db.commit()
        return {
            "scenarios_loaded": len(scenarios),
            "claims_created": created_claims,
            "documents_created": created_documents,
        }