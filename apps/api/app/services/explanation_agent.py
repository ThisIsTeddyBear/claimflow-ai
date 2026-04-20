from __future__ import annotations

import json
import re
from typing import Any

from app.schemas.agent_outputs import ExplanationOutput
from app.services.llm_client import LLMClient
from app.services.prompt_registry import PromptRegistry


PLACEHOLDER_PATTERNS = (
    re.compile(r"\[[A-Z0-9 _-]{2,}\]"),
    re.compile(r"\bX{4,}\b"),
    re.compile(r"\bYYYY-MM-DD\b", re.IGNORECASE),
    re.compile(r"\bREDACTED\b", re.IGNORECASE),
    re.compile(r"https?://", re.IGNORECASE),
    re.compile(r"\bwww\.", re.IGNORECASE),
)

SUSPECT_TERMS = (
    "audit log",
    "audit id",
    "benefits guide",
    "compliance",
    "contractual terms",
    "deterministic validation criteria",
    "policy manual",
    "portal",
    "regulation",
    "settlement readiness",
    "workflow system",
)


class ExplanationAgent:
    def __init__(
        self,
        llm_client: LLMClient | None = None,
        prompt_registry: PromptRegistry | None = None,
        prompt_version: str = "v1",
    ) -> None:
        self.llm_client = llm_client
        self.prompt_registry = prompt_registry
        self.prompt_version = prompt_version

    def generate(
        self,
        *,
        audience: str,
        decision: str,
        reasons: list[str],
        next_steps: list[str],
        claim_context: dict[str, Any] | None = None,
    ) -> ExplanationOutput:
        context = claim_context or {}
        deterministic = self._build_deterministic(
            audience=audience,
            decision=decision,
            reasons=reasons,
            next_steps=next_steps,
            claim_context=context,
        )

        llm_output = self._run_llm(
            audience=audience,
            decision=decision,
            reasons=reasons,
            next_steps=next_steps,
            claim_context=context,
        )
        validated = self._validate_llm_output(
            llm_output=llm_output,
            audience=audience,
            decision=decision,
            claim_context=context,
        )
        return validated or deterministic

    def _run_llm(
        self,
        *,
        audience: str,
        decision: str,
        reasons: list[str],
        next_steps: list[str],
        claim_context: dict[str, Any],
    ) -> ExplanationOutput | None:
        if not self.llm_client or not self.prompt_registry:
            return None

        try:
            prompt = self.prompt_registry.load("explanation_agent", self.prompt_version)
        except FileNotFoundError:
            return None

        user_payload = {
            "audience": audience,
            "decision": decision,
            "reasons": reasons,
            "next_steps": next_steps,
            "claim_context": claim_context,
            "contract": prompt.get("contract", {}),
        }
        user_prompt = (
            "Generate a communication draft using only the provided claim facts and deterministic decision details. "
            "Omit any detail that is missing. Return only JSON matching the contract.\n"
            f"{json.dumps(user_payload, ensure_ascii=True)}"
        )
        return self.llm_client.generate_structured(system=prompt["system"], user=user_prompt, schema=ExplanationOutput)

    def _validate_llm_output(
        self,
        *,
        llm_output: ExplanationOutput | None,
        audience: str,
        decision: str,
        claim_context: dict[str, Any],
    ) -> ExplanationOutput | None:
        if llm_output is None:
            return None

        title = self._clean_line(llm_output.title)
        summary = self._clean_line(llm_output.summary)
        reasons = self._clean_lines(llm_output.reasons)
        next_steps = self._clean_lines(llm_output.next_steps)
        tone = self._clean_line(llm_output.tone) or self._tone_for(audience)

        if not title or not summary:
            return None

        combined = " ".join([title, summary, *reasons, *next_steps]).lower()
        if self._contains_banned_artifacts(combined):
            return None

        if not self._is_decision_consistent(combined, decision=decision, claim_context=claim_context):
            return None

        if not self._is_grounded_in_context(combined, claim_context):
            return None

        return ExplanationOutput(
            title=title,
            summary=summary,
            reasons=reasons,
            next_steps=next_steps,
            tone=tone,
        )

    def _build_deterministic(
        self,
        *,
        audience: str,
        decision: str,
        reasons: list[str],
        next_steps: list[str],
        claim_context: dict[str, Any],
    ) -> ExplanationOutput:
        title = self._build_title(audience=audience, decision=decision, claim_context=claim_context)
        summary = self._build_summary(audience=audience, decision=decision, claim_context=claim_context)
        grounded_reasons = self._build_reasons(
            audience=audience,
            decision=decision,
            reasons=reasons,
            claim_context=claim_context,
        )
        grounded_next_steps = self._build_next_steps(
            audience=audience,
            decision=decision,
            reasons=reasons,
            next_steps=next_steps,
            claim_context=claim_context,
        )
        return ExplanationOutput(
            title=title,
            summary=summary,
            reasons=grounded_reasons,
            next_steps=grounded_next_steps,
            tone=self._tone_for(audience),
        )

    def _build_title(self, *, audience: str, decision: str, claim_context: dict[str, Any]) -> str:
        decision_label = self._decision_label(decision)
        descriptor = self._claim_descriptor(claim_context)
        member_or_policy = self._member_or_policy_reference(claim_context)
        claim_number = self._get_string(claim_context, "claim_number")

        if audience == "internal":
            suffix = f" {claim_number}" if claim_number else ""
            return f"Internal Note: {decision_label} {descriptor}{suffix}".strip()

        if audience == "adjuster":
            return f"Adjuster Summary: {decision_label} {descriptor}"

        if member_or_policy:
            return f"{decision_label} for {member_or_policy}"
        return f"{decision_label} {descriptor}".strip()

    def _build_summary(self, *, audience: str, decision: str, claim_context: dict[str, Any]) -> str:
        descriptor = self._claim_descriptor(claim_context)
        decision_phrase = self._decision_phrase(decision)
        subject = self._member_or_policy_reference(claim_context)
        key_facts = self._summary_fact_fragments(claim_context)

        if audience in {"provider", "claimant"}:
            opening = f"This {descriptor} has been {decision_phrase}."
            if subject:
                opening = f"This claim for {subject} has been {decision_phrase}."
        elif audience == "adjuster":
            opening = f"{self._decision_label(decision)} {descriptor}."
        else:
            opening = f"{self._decision_label(decision)} {descriptor}."

        sentences = [opening]
        if key_facts:
            sentences.append(f"Reviewed information supports {', '.join(key_facts)}.")
        if self._get_bool(claim_context, "corrected_claim"):
            sentences.append("The submission is marked as a corrected claim.")
        return " ".join(sentences)

    def _build_reasons(
        self,
        *,
        audience: str,
        decision: str,
        reasons: list[str],
        claim_context: dict[str, Any],
    ) -> list[str]:
        items: list[str] = []

        for reason in reasons:
            rewritten = self._rewrite_reason(reason, audience=audience, decision=decision)
            if rewritten and rewritten not in items:
                items.append(rewritten)

        for fact in self._supporting_fact_bullets(claim_context):
            if fact not in items:
                items.append(fact)

        return items[:4]

    def _build_next_steps(
        self,
        *,
        audience: str,
        decision: str,
        reasons: list[str],
        next_steps: list[str],
        claim_context: dict[str, Any],
    ) -> list[str]:
        queue_label = self._humanize(self._get_string(claim_context, "reviewer_queue") or "")
        missing_docs = self._extract_missing_documents(reasons)
        prior_auth_code = self._extract_prior_auth_code(reasons)

        if decision == "approve":
            if audience in {"provider", "claimant"}:
                return [
                    "No additional information is requested at this time.",
                    "Standard post-approval processing can continue.",
                ]
            if audience == "adjuster":
                return [
                    "No escalation is required.",
                    "Continue standard post-approval handling.",
                ]
            return ["Record the approval and continue standard post-approval handling."]

        if decision == "pend":
            if prior_auth_code:
                request = f"Request prior authorization support for {prior_auth_code}."
                if audience in {"provider", "claimant"}:
                    request = f"Please submit prior authorization support for {prior_auth_code}."
                return [request]
            if missing_docs:
                missing = ", ".join(self._humanize(doc) for doc in missing_docs)
                request = f"Request the missing items: {missing}."
                if audience in {"provider", "claimant"}:
                    request = f"Please submit the missing items: {missing}."
                return [request]
            if audience in {"provider", "claimant"}:
                return ["Please submit the additional information needed to continue review."]
            return ["Request the missing information and hold the claim pending receipt."]

        if decision == "reject":
            if audience in {"provider", "claimant"}:
                return ["No further action is needed unless corrected or additional supporting information is submitted."]
            if audience == "adjuster":
                return ["Document the denial outcome and monitor for any resubmission."]
            return ["Record the denial reason and close automated handling."]

        if audience in {"provider", "claimant"}:
            return ["The claim is under additional review before a final update is issued."]
        if audience == "adjuster":
            if queue_label:
                return [f"Review the claim in {queue_label}.", "Continue manual handling based on the flagged issues."]
            return ["Continue manual handling based on the flagged issues."]
        if queue_label:
            return [f"Route the claim to {queue_label}.", "Review the flagged issues before further action."]
        return ["Route the claim for manual review.", "Review the flagged issues before further action."]

    def _summary_fact_fragments(self, claim_context: dict[str, Any]) -> list[str]:
        if self._get_string(claim_context, "domain") == "healthcare":
            facts = [
                self._prefix_if_value("member", self._get_string(claim_context, "member_id") or self._get_string(claim_context, "policy_or_member_id")),
                self._prefix_if_value("provider", self._get_string(claim_context, "provider_id")),
                self._prefix_if_value("date of service", self._get_string(claim_context, "date_of_service") or self._get_string(claim_context, "incident_or_service_date")),
                self._prefix_if_value("billed amount", self._format_amount(claim_context, "billed_amount", "estimated_amount")),
                self._prefix_if_value("procedure", self._join_codes(claim_context, "procedure_codes")),
            ]
        else:
            facts = [
                self._prefix_if_value("policy", self._get_string(claim_context, "policy_or_member_id")),
                self._prefix_if_value("driver", self._get_string(claim_context, "driver_name") or self._get_string(claim_context, "claimant_name")),
                self._prefix_if_value("incident date", self._get_string(claim_context, "incident_date") or self._get_string(claim_context, "incident_or_service_date")),
                self._prefix_if_value("location", self._get_string(claim_context, "accident_location")),
                self._prefix_if_value("repair estimate", self._format_amount(claim_context, "repair_estimate_amount", "estimated_amount")),
            ]

        return [fact for fact in facts if fact][:4]

    def _supporting_fact_bullets(self, claim_context: dict[str, Any]) -> list[str]:
        items: list[str] = []

        if self._get_string(claim_context, "domain") == "healthcare":
            member = self._get_string(claim_context, "member_id") or self._get_string(claim_context, "policy_or_member_id")
            provider = self._get_string(claim_context, "provider_id")
            dos = self._get_string(claim_context, "date_of_service") or self._get_string(claim_context, "incident_or_service_date")
            billed = self._format_amount(claim_context, "billed_amount", "estimated_amount")
            units = self._get_string(claim_context, "units")
            diagnosis = self._join_codes(claim_context, "diagnosis_codes")
            procedure = self._join_codes(claim_context, "procedure_codes")

            if member or provider or dos:
                fragments = [
                    self._prefix_if_value("member", member),
                    self._prefix_if_value("provider", provider),
                    self._prefix_if_value("date of service", dos),
                ]
                items.append(f"Reviewed documents show {', '.join(fragment for fragment in fragments if fragment)}.")

            if billed or units:
                fragments = [
                    self._prefix_if_value("billed amount", billed),
                    self._prefix_if_value("units", units),
                ]
                items.append(f"Billing information shows {', '.join(fragment for fragment in fragments if fragment)}.")

            if diagnosis or procedure:
                fragments = [
                    self._prefix_if_value("diagnosis", diagnosis),
                    self._prefix_if_value("procedure", procedure),
                ]
                items.append(f"Coding information shows {', '.join(fragment for fragment in fragments if fragment)}.")

            if self._get_bool(claim_context, "corrected_claim"):
                items.append("The submission is marked as a corrected claim.")
        else:
            driver = self._get_string(claim_context, "driver_name") or self._get_string(claim_context, "claimant_name")
            incident_date = self._get_string(claim_context, "incident_date") or self._get_string(claim_context, "incident_or_service_date")
            location = self._get_string(claim_context, "accident_location")
            estimate = self._format_amount(claim_context, "repair_estimate_amount", "estimated_amount")
            injury = self._get_string(claim_context, "injury_description")

            if driver or incident_date or location:
                fragments = [
                    self._prefix_if_value("driver", driver),
                    self._prefix_if_value("incident date", incident_date),
                    self._prefix_if_value("location", location),
                ]
                items.append(f"Reviewed documents show {', '.join(fragment for fragment in fragments if fragment)}.")

            if estimate:
                items.append(f"Repair information shows {self._prefix_if_value('estimate', estimate)}.")

            if injury:
                items.append(f"Supporting records note injury description: {injury}.")

        document_types = self._string_list(claim_context.get("document_types"))
        if document_types:
            labels = ", ".join(self._humanize(doc_type) for doc_type in document_types[:4])
            items.append(f"Reviewed documents include {labels}.")

        return items

    def _rewrite_reason(self, reason: str, *, audience: str, decision: str) -> str | None:
        cleaned = self._clean_line(reason)
        if not cleaned:
            return None

        normalized = cleaned.lower()
        if self._contains_banned_artifacts(normalized):
            return None

        if audience in {"provider", "claimant"}:
            replacements = {
                "critical documents are missing for safe adjudication.": "Required claim documents are missing.",
                "material validation issues require additional evidence.": "Additional documentation is needed before the claim can be finalized.",
                "coverage outcome is not a deterministic rejection, but case needs additional review.": "The claim needs additional review before it can be finalized.",
                "risk/ambiguity threshold exceeded; routing to human review.": "The claim needs additional review before a final update can be issued.",
            }
            if normalized in replacements:
                return replacements[normalized]

        if decision == "approve" and "high-value" in normalized:
            return None

        return cleaned

    def _contains_banned_artifacts(self, text: str) -> bool:
        if any(pattern.search(text) for pattern in PLACEHOLDER_PATTERNS):
            return True
        return any(term in text for term in SUSPECT_TERMS)

    def _is_decision_consistent(self, text: str, *, decision: str, claim_context: dict[str, Any]) -> bool:
        if decision == "approve":
            if any(term in text for term in ("high-value", "fraud review", "medical review", "manual review")):
                return False
            if self._is_low_amount_claim(claim_context) and any(term in text for term in (">$10k", "over $10k", "over 10000")):
                return False
        if decision in {"approve", "pend", "escalate"} and "denial notice" in text:
            return False
        if decision == "reject" and "claim approved" in text:
            return False
        return True

    def _is_grounded_in_context(self, text: str, claim_context: dict[str, Any]) -> bool:
        evidence_tokens = [
            self._get_string(claim_context, "member_id"),
            self._get_string(claim_context, "policy_or_member_id"),
            self._get_string(claim_context, "provider_id"),
            self._get_string(claim_context, "date_of_service"),
            self._get_string(claim_context, "incident_or_service_date"),
            self._get_string(claim_context, "incident_date"),
            self._get_string(claim_context, "driver_name"),
            self._join_codes(claim_context, "procedure_codes"),
            self._join_codes(claim_context, "diagnosis_codes"),
            self._format_amount(claim_context, "billed_amount", "estimated_amount"),
            self._format_amount(claim_context, "repair_estimate_amount", "estimated_amount"),
        ]
        tokens = [token.lower() for token in evidence_tokens if token]
        if not tokens:
            return True

        required_matches = 1 if len(tokens) == 1 else 2
        matches = sum(1 for token in tokens if token in text)
        return matches >= required_matches

    def _decision_label(self, decision: str) -> str:
        return {
            "approve": "Approved",
            "reject": "Rejected",
            "pend": "Pending Review",
            "escalate": "Additional Review Required",
        }.get(decision, self._humanize(decision))

    @staticmethod
    def _decision_phrase(decision: str) -> str:
        return {
            "approve": "approved",
            "reject": "not approved",
            "pend": "placed in pending status",
            "escalate": "sent for additional review",
        }.get(decision, decision)

    def _claim_descriptor(self, claim_context: dict[str, Any]) -> str:
        domain = self._get_string(claim_context, "domain")
        subtype = self._humanize(self._get_string(claim_context, "subtype") or "")
        if domain == "healthcare":
            return f"{subtype.lower()} healthcare claim".strip() if subtype else "healthcare claim"
        if domain == "auto":
            return f"{subtype.lower()} auto claim".strip() if subtype else "auto claim"
        return "claim"

    def _member_or_policy_reference(self, claim_context: dict[str, Any]) -> str | None:
        domain = self._get_string(claim_context, "domain")
        member = self._get_string(claim_context, "member_id") or self._get_string(claim_context, "policy_or_member_id")
        if domain == "healthcare" and member:
            return f"member {member}"
        if member:
            return f"policy {member}"
        claimant = self._get_string(claim_context, "claimant_name")
        if claimant:
            return claimant
        return None

    @staticmethod
    def _tone_for(audience: str) -> str:
        return "professional" if audience in {"provider", "claimant"} else "operational"

    @staticmethod
    def _clean_line(value: str | None) -> str | None:
        if value is None:
            return None
        cleaned = re.sub(r"\s+", " ", value).strip()
        return cleaned or None

    def _clean_lines(self, values: list[str]) -> list[str]:
        cleaned: list[str] = []
        for value in values:
            line = self._clean_line(value)
            if line and line not in cleaned and not self._contains_banned_artifacts(line.lower()):
                cleaned.append(line)
        return cleaned

    @staticmethod
    def _get_string(data: dict[str, Any], key: str) -> str | None:
        value = data.get(key)
        if value is None:
            return None
        if isinstance(value, list):
            return ", ".join(str(item) for item in value if str(item).strip()) or None
        text = str(value).strip()
        return text or None

    @staticmethod
    def _get_bool(data: dict[str, Any], key: str) -> bool:
        value = data.get(key)
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            return value.strip().lower() in {"true", "yes", "1"}
        return False

    @staticmethod
    def _string_list(value: Any) -> list[str]:
        if isinstance(value, list):
            return [str(item).strip() for item in value if str(item).strip()]
        if value is None:
            return []
        single = str(value).strip()
        return [single] if single else []

    def _join_codes(self, claim_context: dict[str, Any], key: str) -> str | None:
        values = self._string_list(claim_context.get(key))
        return ", ".join(values) if values else None

    def _format_amount(self, claim_context: dict[str, Any], primary_key: str, fallback_key: str) -> str | None:
        for key in (primary_key, fallback_key):
            value = claim_context.get(key)
            if isinstance(value, (int, float)):
                return self._currency(value)
            text = self._get_string(claim_context, key)
            if text:
                return text
        return None

    @staticmethod
    def _currency(amount: float) -> str:
        whole = round(amount)
        if abs(amount - whole) < 0.001:
            return f"${whole:,.0f}"
        return f"${amount:,.2f}"

    @staticmethod
    def _prefix_if_value(label: str, value: str | None) -> str | None:
        if not value:
            return None
        return f"{label} {value}"

    @staticmethod
    def _humanize(value: str) -> str:
        return value.replace("_", " ").strip().title()

    @staticmethod
    def _extract_missing_documents(reasons: list[str]) -> list[str]:
        missing: list[str] = []
        for reason in reasons:
            if reason.lower().startswith("missing:"):
                missing.append(reason.split(":", 1)[1].strip())
        return missing

    @staticmethod
    def _extract_prior_auth_code(reasons: list[str]) -> str | None:
        for reason in reasons:
            match = re.search(r"prior authorization required for ([^.]+)", reason, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        return None

    def _is_low_amount_claim(self, claim_context: dict[str, Any]) -> bool:
        for key in ("billed_amount", "estimated_amount"):
            value = claim_context.get(key)
            if isinstance(value, (int, float)):
                return value < 10000
        return False
