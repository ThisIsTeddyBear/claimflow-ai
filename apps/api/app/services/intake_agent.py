from __future__ import annotations

import json

from app.schemas.agent_outputs import IntakeAgentOutput
from app.services.llm_client import LLMClient
from app.services.prompt_registry import PromptRegistry


class IntakeAgent:
    AUTO_REQUIRED_DOCS = ["claim_form", "accident_narrative", "repair_estimate"]
    HEALTHCARE_REQUIRED_DOCS = ["claim_form", "billing_statement", "coding_summary"]

    def __init__(
        self,
        llm_client: LLMClient | None = None,
        prompt_registry: PromptRegistry | None = None,
        prompt_version: str = "v1",
    ) -> None:
        self.llm_client = llm_client
        self.prompt_registry = prompt_registry
        self.prompt_version = prompt_version

    def run(self, *, domain: str, subtype: str | None, documents: list[dict], claim_payload: dict) -> IntakeAgentOutput:
        deterministic_output = self._run_deterministic(domain=domain, subtype=subtype, documents=documents, claim_payload=claim_payload)
        llm_output = self._run_llm(domain=domain, subtype=subtype, documents=documents, claim_payload=claim_payload)
        if llm_output is None:
            return deterministic_output

        normalized_required = {self._normalize_required_doc_name(doc) for doc in deterministic_output.required_docs}
        normalized_required.discard(None)

        llm_missing_filtered: list[str] = []
        llm_extra_requests: list[str] = []
        for doc in llm_output.missing_docs:
            normalized = self._normalize_required_doc_name(doc)
            if not normalized:
                continue
            if normalized in normalized_required:
                llm_missing_filtered.append(normalized)
            else:
                llm_extra_requests.append(normalized)

        # Safety: only deterministic required document set can gate adjudication.
        missing_docs = sorted(set(deterministic_output.missing_docs) | set(llm_missing_filtered))
        completeness = round((len(deterministic_output.required_docs) - len(missing_docs)) / max(len(deterministic_output.required_docs), 1), 3)
        notes = deterministic_output.intake_notes + [note for note in llm_output.intake_notes if note not in deterministic_output.intake_notes]
        if llm_extra_requests:
            notes.append(
                "LLM suggested supplemental documentation (non-blocking): "
                + ", ".join(sorted(set(llm_extra_requests)))
            )
        confidence = round(min(deterministic_output.confidence, llm_output.confidence), 3)
        return IntakeAgentOutput(
            claim_domain=domain,
            claim_subtype=subtype,
            required_docs=deterministic_output.required_docs,
            missing_docs=missing_docs,
            completeness_score=max(0.0, min(1.0, completeness)),
            intake_notes=notes,
            confidence=max(0.0, min(1.0, confidence)),
        )

    @staticmethod
    def _normalize_required_doc_name(value: str | None) -> str | None:
        if not value:
            return None
        return value.strip().lower().replace(" ", "_")

    def _run_deterministic(self, *, domain: str, subtype: str | None, documents: list[dict], claim_payload: dict) -> IntakeAgentOutput:
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

    def _run_llm(
        self,
        *,
        domain: str,
        subtype: str | None,
        documents: list[dict],
        claim_payload: dict,
    ) -> IntakeAgentOutput | None:
        if not self.llm_client or not self.prompt_registry:
            return None

        try:
            prompt = self.prompt_registry.load("intake_agent", self.prompt_version)
        except FileNotFoundError:
            return None

        user_payload = {
            "domain": domain,
            "subtype": subtype,
            "documents": documents,
            "claim_payload": claim_payload,
            "contract": prompt.get("contract", {}),
        }
        user_prompt = (
            "Assess intake completeness for this claim packet. Return only JSON matching the contract.\n"
            f"{json.dumps(user_payload, ensure_ascii=True)}"
        )
        return self.llm_client.generate_structured(system=prompt["system"], user=user_prompt, schema=IntakeAgentOutput)

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
