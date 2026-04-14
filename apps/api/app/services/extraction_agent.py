from __future__ import annotations

import re

from app.schemas.agent_outputs import ExtractedEntity, ExtractionAgentOutput
from app.services.utils import extract_amount, extract_first_date, parse_key_value_lines


class ExtractionAgent:
    CODE_SPLIT = re.compile(r"[,;\s]+")

    def run(self, *, domain: str, filename: str, document_type: str | None, text: str) -> ExtractionAgentOutput:
        normalized_doc_type = (document_type or self._infer_doc_type(filename)).strip().lower().replace(" ", "_")
        entities = self._extract_auto(text, normalized_doc_type) if domain == "auto" else self._extract_healthcare(text, normalized_doc_type)
        confidence = round(min(0.98, 0.55 + 0.06 * len(entities)), 3)
        ambiguities: list[str] = []
        if len(entities) <= 2:
            ambiguities.append("Low extraction density; document may be incomplete or low quality.")

        return ExtractionAgentOutput(
            document_type=normalized_doc_type,
            entities=entities,
            ambiguities=ambiguities,
            doc_summary=self._summarize(text),
            confidence=confidence,
        )

    def _extract_auto(self, text: str, document_type: str) -> dict[str, ExtractedEntity]:
        data = parse_key_value_lines(text)
        entities: dict[str, ExtractedEntity] = {}

        incident_date = data.get("incident_date") or data.get("accident_date")
        fallback_date_allowed = document_type in {"claim_form", "accident_narrative", "police_report"}
        parsed_incident = incident_date or (extract_first_date(text).isoformat() if fallback_date_allowed and extract_first_date(text) else None)
        if parsed_incident:
            entities["incident_date"] = ExtractedEntity(value=parsed_incident, confidence=0.86, source_excerpt=incident_date or parsed_incident)

        if location := (data.get("location") or data.get("accident_location")):
            entities["accident_location"] = ExtractedEntity(value=location, confidence=0.86, source_excerpt=location)

        if driver := (data.get("driver") or data.get("driver_name")):
            entities["driver_name"] = ExtractedEntity(value=driver, confidence=0.88, source_excerpt=driver)

        if vin := (data.get("vin") or data.get("vehicle_vin")):
            entities["vehicle_vin"] = ExtractedEntity(value=vin, confidence=0.9, source_excerpt=vin)

        if plate := (data.get("license_plate") or data.get("plate")):
            entities["license_plate"] = ExtractedEntity(value=plate, confidence=0.88, source_excerpt=plate)

        if police_no := (data.get("police_report_number") or data.get("report_number")):
            entities["police_report_number"] = ExtractedEntity(value=police_no, confidence=0.83, source_excerpt=police_no)

        amount = None
        if "estimate" in document_type:
            amount = extract_amount(text)
        if amount is not None:
            entities["repair_estimate_amount"] = ExtractedEntity(value=amount, confidence=0.83, source_excerpt=f"{amount}")

        for key in ("injury_description", "injury", "injury_claim"):
            if key in data:
                entities["injury_description"] = ExtractedEntity(value=data[key], confidence=0.75, source_excerpt=data[key])
                break

        if narrative := (data.get("narrative") or data.get("accident_narrative") or data.get("statement")):
            entities["accident_narrative"] = ExtractedEntity(value=narrative, confidence=0.7, source_excerpt=narrative[:240])

        if use_type := (data.get("use_type") or data.get("vehicle_use")):
            entities["use_type"] = ExtractedEntity(value=use_type.lower(), confidence=0.8, source_excerpt=use_type)

        return entities

    def _extract_healthcare(self, text: str, document_type: str) -> dict[str, ExtractedEntity]:
        data = parse_key_value_lines(text)
        entities: dict[str, ExtractedEntity] = {}

        if member_id := data.get("member_id"):
            entities["member_id"] = ExtractedEntity(value=member_id, confidence=0.92, source_excerpt=member_id)

        if provider_id := (data.get("provider_id") or data.get("npi")):
            entities["provider_id"] = ExtractedEntity(value=provider_id, confidence=0.9, source_excerpt=provider_id)

        if dos := (data.get("date_of_service") or data.get("service_date")):
            entities["date_of_service"] = ExtractedEntity(value=dos, confidence=0.9, source_excerpt=dos)
        else:
            extracted_date = extract_first_date(text) if document_type in {"claim_form", "billing_statement"} else None
            if extracted_date:
                entities["date_of_service"] = ExtractedEntity(value=extracted_date.isoformat(), confidence=0.75, source_excerpt=extracted_date.isoformat())

        diagnosis_raw = data.get("diagnosis_codes") or data.get("icd10") or data.get("diagnosis")
        if diagnosis_raw:
            diagnosis_codes = [code for code in self.CODE_SPLIT.split(diagnosis_raw) if code]
            entities["diagnosis_codes"] = ExtractedEntity(value=diagnosis_codes, confidence=0.86, source_excerpt=diagnosis_raw)

        procedure_raw = data.get("procedure_codes") or data.get("cpt_codes") or data.get("procedure")
        if procedure_raw:
            procedure_codes = [code for code in self.CODE_SPLIT.split(procedure_raw) if code]
            entities["procedure_codes"] = ExtractedEntity(value=procedure_codes, confidence=0.87, source_excerpt=procedure_raw)

        if units := data.get("units"):
            try:
                parsed_units = int(units)
            except ValueError:
                parsed_units = units
            entities["units"] = ExtractedEntity(value=parsed_units, confidence=0.8, source_excerpt=units)

        billed_raw = data.get("billed_amount") or data.get("amount")
        amount = None
        if billed_raw:
            amount = extract_amount(billed_raw)
        elif document_type in {"billing_statement", "invoice"}:
            amount = extract_amount(text)
        if amount is not None:
            entities["billed_amount"] = ExtractedEntity(value=amount, confidence=0.85, source_excerpt=f"{amount}")

        if pa := (data.get("prior_auth") or data.get("prior_authorization") or data.get("prior_auth_number")):
            entities["prior_auth_number"] = ExtractedEntity(value=pa, confidence=0.83, source_excerpt=pa)

        if corrected := data.get("corrected_claim"):
            entities["corrected_claim"] = ExtractedEntity(value=corrected.lower() in {"yes", "true", "1"}, confidence=0.82, source_excerpt=corrected)

        return entities

    def _infer_doc_type(self, filename: str) -> str:
        lower = filename.lower()
        if "estimate" in lower:
            return "repair_estimate"
        if "police" in lower:
            return "police_report"
        if "photo" in lower:
            return "photo"
        if "billing" in lower or "invoice" in lower:
            return "billing_statement"
        if "prior" in lower and "auth" in lower:
            return "prior_auth"
        if "claim" in lower:
            return "claim_form"
        if "code" in lower:
            return "coding_summary"
        return "supporting_document"

    @staticmethod
    def _summarize(text: str) -> str:
        text = text.strip().replace("\n", " ")
        return text[:240] if text else "No readable text extracted"
