import { ClaimDetail, ClaimDocument } from "@/types/claims";

type ClaimDomain = ClaimDetail["claim"]["domain"];

type FactEntry = ClaimDetail["extracted_facts"][number];

type FactSectionConfig = {
  auto: string;
  healthcare: string;
  label: string;
  priority: number;
};

const FACT_CONFIG: Record<string, FactSectionConfig> = {
  incident_date: { auto: "Incident Details", healthcare: "Service Details", label: "Incident Date", priority: 10 },
  date_of_service: { auto: "Incident Details", healthcare: "Service Details", label: "Date of Service", priority: 10 },
  accident_location: { auto: "Incident Details", healthcare: "Claim Info", label: "Accident Location", priority: 20 },
  police_report_number: { auto: "Incident Details", healthcare: "Claim Info", label: "Police Report Number", priority: 30 },
  accident_narrative: { auto: "Incident Details", healthcare: "Claim Info", label: "Incident Narrative", priority: 40 },
  driver_name: { auto: "People / Driver", healthcare: "Claim Info", label: "Driver Name", priority: 10 },
  member_id: { auto: "Policy / Claim Info", healthcare: "Member / Provider", label: "Member ID", priority: 10 },
  provider_id: { auto: "Policy / Claim Info", healthcare: "Member / Provider", label: "Provider ID", priority: 20 },
  vehicle_vin: { auto: "Vehicle", healthcare: "Claim Info", label: "Vehicle VIN", priority: 10 },
  license_plate: { auto: "Vehicle", healthcare: "Claim Info", label: "License Plate", priority: 20 },
  use_type: { auto: "Vehicle", healthcare: "Claim Info", label: "Vehicle Use", priority: 30 },
  injury_description: { auto: "Injuries / Damage", healthcare: "Claim Info", label: "Injury Description", priority: 10 },
  repair_estimate_amount: { auto: "Injuries / Damage", healthcare: "Billing / Authorization", label: "Repair Estimate", priority: 20 },
  diagnosis_codes: { auto: "Policy / Claim Info", healthcare: "Clinical Coding", label: "Diagnosis Codes", priority: 10 },
  procedure_codes: { auto: "Policy / Claim Info", healthcare: "Clinical Coding", label: "Procedure Codes", priority: 20 },
  units: { auto: "Policy / Claim Info", healthcare: "Billing / Authorization", label: "Units", priority: 30 },
  billed_amount: { auto: "Policy / Claim Info", healthcare: "Billing / Authorization", label: "Billed Amount", priority: 40 },
  prior_auth_number: { auto: "Policy / Claim Info", healthcare: "Billing / Authorization", label: "Prior Authorization", priority: 50 },
  corrected_claim: { auto: "Policy / Claim Info", healthcare: "Claim Info", label: "Corrected Claim", priority: 60 },
};

const SECTION_ORDER: Record<ClaimDomain, string[]> = {
  auto: ["Incident Details", "People / Driver", "Vehicle", "Injuries / Damage", "Policy / Claim Info", "Other Extracted Facts"],
  healthcare: ["Service Details", "Member / Provider", "Clinical Coding", "Billing / Authorization", "Claim Info", "Other Extracted Facts"],
};

export type FormattedFactEntry = {
  id: string;
  sourceDocumentId: string | null;
  sourceDocumentName: string | null;
  sourceExcerpt: string | null;
  confidence: number;
  rawValue: unknown;
  displayValue: string;
};

export type FormattedFactField = {
  key: string;
  label: string;
  section: string;
  priority: number;
  primary: FormattedFactEntry;
  entries: FormattedFactEntry[];
};

export type FactSection = {
  title: string;
  fields: FormattedFactField[];
};

export type CoverageSummary = {
  statusLabel: "Covered" | "Not Covered" | "Needs Review";
  tone: "positive" | "negative" | "caution";
  coverageType: string;
  deductible: string;
  confidence: number;
  confidenceLabel: string;
  reasons: string[];
  benefitNotes: string[];
  hardFail: boolean;
};

export type FraudSignalSummary = {
  code: string;
  description: string;
  severity: string;
  confidence: number | null;
  evidenceRefs: string[];
};

export type FraudSummary = {
  riskScore: number;
  riskPercent: number;
  severityLabel: "Low" | "Medium" | "High";
  severityTone: "positive" | "caution" | "negative";
  recommendedAction: string;
  signals: FraudSignalSummary[];
};

export type AdvisoryFindingSummary = {
  finding: string;
  confidence: number;
  priorityGroup: string;
  evidenceRefs: string[];
};

export type AdvisoryGroup = {
  title: string;
  findings: AdvisoryFindingSummary[];
};

export type AdvisorySummary = {
  escalationRecommended: boolean;
  confidence: number;
  confidenceLabel: string;
  uncertaintyFlags: string[];
  groups: AdvisoryGroup[];
};

export function buildFactSections(
  domain: ClaimDomain,
  facts: ClaimDetail["extracted_facts"],
  documents: ClaimDocument[],
): FactSection[] {
  const documentNames = new Map(documents.map((doc) => [doc.id, doc.filename]));
  const grouped = new Map<string, FactEntry[]>();

  for (const fact of facts) {
    const existing = grouped.get(fact.key) ?? [];
    existing.push(fact);
    grouped.set(fact.key, existing);
  }

  const fields = Array.from(grouped.entries()).map(([key, entries]) => {
    const config = FACT_CONFIG[key];
    const sortedEntries = [...entries].sort((left, right) => right.confidence - left.confidence);
    const formattedEntries = sortedEntries.map((entry) => {
      const rawValue = unwrapFactValue(entry.value);
      return {
        id: entry.id,
        sourceDocumentId: entry.source_document_id,
        sourceDocumentName: entry.source_document_id ? documentNames.get(entry.source_document_id) ?? null : null,
        sourceExcerpt: entry.source_excerpt,
        confidence: entry.confidence,
        rawValue,
        displayValue: formatFactValue(key, rawValue),
      } satisfies FormattedFactEntry;
    });

    return {
      key,
      label: config?.label ?? humanizeKey(key),
      section: config ? config[domain] : "Other Extracted Facts",
      priority: config?.priority ?? 999,
      primary: formattedEntries[0],
      entries: formattedEntries,
    } satisfies FormattedFactField;
  });

  const sections = new Map<string, FormattedFactField[]>();
  for (const field of fields) {
    const bucket = sections.get(field.section) ?? [];
    bucket.push(field);
    sections.set(field.section, bucket);
  }

  const orderedSections = SECTION_ORDER[domain];
  return orderedSections
    .map((title) => {
      const fieldsForSection = (sections.get(title) ?? []).sort((left, right) => {
        if (left.priority !== right.priority) {
          return left.priority - right.priority;
        }
        return left.label.localeCompare(right.label);
      });
      return { title, fields: fieldsForSection };
    })
    .filter((section) => section.fields.length > 0);
}

export function summarizeCoverage(result: ClaimDetail["coverage_result"]): CoverageSummary | null {
  if (!result) {
    return null;
  }

  const statusLabel = result.is_covered === true ? "Covered" : result.is_covered === false ? "Not Covered" : "Needs Review";
  const tone = statusLabel === "Covered" ? "positive" : statusLabel === "Not Covered" ? "negative" : "caution";

  return {
    statusLabel,
    tone,
    coverageType: result.coverage_type ? humanizeKey(result.coverage_type) : "Not specified",
    deductible: result.deductible != null ? formatCurrency(result.deductible) : "No deductible noted",
    confidence: result.confidence,
    confidenceLabel: formatConfidence(result.confidence),
    reasons: result.reasons,
    benefitNotes: result.benefit_notes,
    hardFail: result.hard_fail,
  };
}

export function summarizeFraud(result: ClaimDetail["fraud_result"]): FraudSummary | null {
  if (!result) {
    return null;
  }

  const severityLabel = getRiskSeverity(result.risk_score);
  const severityTone = severityLabel === "High" ? "negative" : severityLabel === "Medium" ? "caution" : "positive";
  const signals = Array.isArray(result.signals)
    ? result.signals.map((signal, index) => {
        const record = isObject(signal) ? signal : {};
        return {
          code: getString(record.code) ?? `signal_${index + 1}`,
          description: getString(record.description) ?? "Signal detected during anomaly review.",
          severity: humanizeKey(getString(record.severity) ?? "unknown"),
          confidence: getNumber(record.confidence),
          evidenceRefs: getStringArray(record.evidence_refs),
        } satisfies FraudSignalSummary;
      })
    : [];

  return {
    riskScore: result.risk_score,
    riskPercent: Math.round(result.risk_score * 100),
    severityLabel,
    severityTone,
    recommendedAction: humanizeKey(result.recommended_action),
    signals,
  };
}

export function summarizeAdvisory(result: ClaimDetail["advisory_result"]): AdvisorySummary | null {
  if (!result) {
    return null;
  }

  const findings = Array.isArray(result.findings)
    ? result.findings
        .map((item) => {
          const record = isObject(item) ? item : {};
          const confidence = getNumber(record.confidence) ?? 0;
          return {
            finding: getString(record.finding) ?? "Advisory note",
            confidence,
            priorityGroup: getAdvisoryPriority(confidence),
            evidenceRefs: getStringArray(record.evidence_refs),
          } satisfies AdvisoryFindingSummary;
        })
        .sort((left, right) => right.confidence - left.confidence)
    : [];

  const groups: AdvisoryGroup[] = ["Priority Review", "Watch Items", "Additional Context"]
    .map((title) => ({
      title,
      findings: findings.filter((finding) => finding.priorityGroup === title),
    }))
    .filter((group) => group.findings.length > 0);

  return {
    escalationRecommended: result.escalation_recommended,
    confidence: result.confidence,
    confidenceLabel: formatConfidence(result.confidence),
    uncertaintyFlags: result.uncertainty_flags,
    groups,
  };
}

export function formatConfidence(confidence: number): string {
  return `${Math.round(confidence * 100)}% confidence`;
}

export function formatCurrency(amount: number): string {
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
    maximumFractionDigits: amount % 1 === 0 ? 0 : 2,
  }).format(amount);
}

export function humanizeKey(value: string): string {
  return value
    .replace(/_/g, " ")
    .replace(/\b\w/g, (char) => char.toUpperCase());
}

function unwrapFactValue(value: Record<string, unknown>): unknown {
  if ("value" in value) {
    return value.value;
  }
  return value;
}

function formatFactValue(key: string, value: unknown): string {
  if (value == null) {
    return "Not available";
  }

  if (typeof value === "boolean") {
    return value ? "Yes" : "No";
  }

  if (typeof value === "number") {
    if (key.includes("amount") || key.includes("estimate")) {
      return formatCurrency(value);
    }
    return new Intl.NumberFormat("en-US").format(value);
  }

  if (typeof value === "string") {
    const trimmed = value.trim();
    if (!trimmed) {
      return "Not available";
    }
    return trimmed;
  }

  if (Array.isArray(value)) {
    const items = value.map((item) => String(item)).filter(Boolean);
    return items.length > 0 ? items.join(", ") : "Not available";
  }

  return JSON.stringify(value);
}

function getRiskSeverity(score: number): "Low" | "Medium" | "High" {
  if (score >= 0.7) {
    return "High";
  }
  if (score >= 0.4) {
    return "Medium";
  }
  return "Low";
}

function getAdvisoryPriority(confidence: number): string {
  if (confidence >= 0.85) {
    return "Priority Review";
  }
  if (confidence >= 0.7) {
    return "Watch Items";
  }
  return "Additional Context";
}

function getString(value: unknown): string | null {
  return typeof value === "string" && value.trim() ? value : null;
}

function getNumber(value: unknown): number | null {
  return typeof value === "number" && Number.isFinite(value) ? value : null;
}

function getStringArray(value: unknown): string[] {
  if (!Array.isArray(value)) {
    return [];
  }
  return value.map((item) => String(item)).filter(Boolean);
}

function isObject(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null;
}
