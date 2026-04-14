from __future__ import annotations

from app.schemas.agent_outputs import IntakeAgentOutput


class IntakeAgent:
    AUTO_REQUIRED_DOCS = ["claim_form", "accident_narrative", "repair_estimate"]
    HEALTHCARE_REQUIRED_DOCS = ["claim_form", "billing_statement", "coding_summary"]

    def run(self, *, domain: str, subtype: str | None, documents: list[dict], claim_payload: dict) -> IntakeAgentOutput:
        normalized_types = {self._normalize_doc_type(doc.get("document_type"), doc.get("filename", "")) for doc in documents}
        normalized_types.discard(None)

        required_docs = self.AUTO_REQUIRED_DOCS if domain == "auto" else self.HEALTHCARE_REQUIRED_DOCS

        if domain == "auto" and claim_payload.get("injury_involved"):
            required_docs = [*required_docs, "medical_report"]
        if domain == "healthcare" and claim_payload.get("requires_prior_auth"):
            required_docs = [*required_docs, "prior_auth"]

        missing_docs = [doc for doc in required_docs if doc not in normalized_types]
        completeness = round((len(required_docs) - len(missing_docs)) / max(len(required_docs), 1), 3)

        notes: list[str] = []
        if missing_docs:
            notes.append("Missing critical documents for deterministic adjudication.")
        if subtype is None:
            notes.append("Subtype not provided; inferred routing uses conservative defaults.")

        confidence = 0.9 if completeness >= 0.8 else 0.65
        return IntakeAgentOutput(
            claim_domain=domain,
            claim_subtype=subtype,
            required_docs=required_docs,
            missing_docs=missing_docs,
            completeness_score=completeness,
            intake_notes=notes,
            confidence=confidence,
        )

    def _normalize_doc_type(self, doc_type: str | None, filename: str) -> str | None:
        if doc_type:
            return doc_type.strip().lower().replace(" ", "_")

        lower_name = filename.lower()
        if "estimate" in lower_name:
            return "repair_estimate"
        if "police" in lower_name:
            return "police_report"
        if "photo" in lower_name or "image" in lower_name:
            return "photo"
        if "narrative" in lower_name or "statement" in lower_name:
            return "accident_narrative"
        if "billing" in lower_name or "invoice" in lower_name:
            return "billing_statement"
        if "prior" in lower_name and "auth" in lower_name:
            return "prior_auth"
        if "code" in lower_name:
            return "coding_summary"
        if "medical" in lower_name:
            return "medical_report"
        if "claim" in lower_name or "fnol" in lower_name:
            return "claim_form"
        return None