from __future__ import annotations

from datetime import timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.claim import ClaimCase


class DuplicateDetector:
    def __init__(self, db: Session) -> None:
        self.db = db

    def detect(self, claim: ClaimCase, fact_map: dict, document_fingerprints: list[str]) -> dict:
        stmt = select(ClaimCase).where(ClaimCase.id != claim.id, ClaimCase.domain == claim.domain)
        candidates = list(self.db.scalars(stmt).all())
        current_fixture = (claim.claim_payload or {}).get("fixture") if isinstance(claim.claim_payload, dict) else None
        current_eval_run_id = (claim.claim_payload or {}).get("eval_run_id") if isinstance(claim.claim_payload, dict) else None
        if current_eval_run_id:
            candidates = [
                candidate
                for candidate in candidates
                if isinstance(candidate.claim_payload, dict) and candidate.claim_payload.get("eval_run_id") == current_eval_run_id
            ]
        elif current_fixture:
            candidates = [
                candidate
                for candidate in candidates
                if isinstance(candidate.claim_payload, dict) and candidate.claim_payload.get("fixture")
            ]

        signals: list[dict] = []
        is_duplicate = False
        is_corrected = bool(claim.claim_payload.get("corrected_claim"))

        for candidate in candidates:
            same_party = candidate.policy_or_member_id and candidate.policy_or_member_id == claim.policy_or_member_id
            same_date = (
                candidate.incident_or_service_date is not None
                and claim.incident_or_service_date is not None
                and abs((candidate.incident_or_service_date - claim.incident_or_service_date).days) <= 2
            )
            same_amount = (
                candidate.estimated_amount is not None
                and claim.estimated_amount is not None
                and abs(candidate.estimated_amount - claim.estimated_amount) < 10
            )

            if same_party and same_date and same_amount:
                is_duplicate = True
                signals.append(
                    {
                        "code": "exact_claim_signature",
                        "description": f"Potential duplicate of claim {candidate.claim_number}",
                        "severity": "high",
                        "confidence": 0.9,
                        "evidence_refs": [candidate.id],
                    }
                )

        if len(document_fingerprints) != len(set(document_fingerprints)) and document_fingerprints:
            signals.append(
                {
                    "code": "document_fingerprint_reuse",
                    "description": "One or more uploaded documents are duplicated in this claim packet.",
                    "severity": "medium",
                    "confidence": 0.84,
                    "evidence_refs": [],
                }
            )

        if is_corrected and is_duplicate:
            signals.append(
                {
                    "code": "corrected_claim_marker",
                    "description": "Claim marked as corrected; reduce duplicate confidence.",
                    "severity": "low",
                    "confidence": 0.8,
                    "evidence_refs": [],
                }
            )

        return {
            "is_duplicate": is_duplicate and not is_corrected,
            "is_corrected": is_corrected,
            "signals": signals,
        }
