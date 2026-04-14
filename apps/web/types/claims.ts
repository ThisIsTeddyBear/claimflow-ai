export type ClaimDomain = "auto" | "healthcare";
export type DecisionType = "approve" | "reject" | "pend" | "escalate";

export type ClaimSummary = {
  id: string;
  claim_number: string;
  domain: ClaimDomain;
  subtype: string | null;
  status: string;
  claimant_name: string | null;
  policy_or_member_id: string | null;
  incident_or_service_date: string | null;
  estimated_amount: number | null;
  current_queue: string | null;
  latest_decision: DecisionType | null;
  latest_decision_confidence: number | null;
  risk_score: number | null;
};

export type ClaimDecision = {
  id: string;
  claim_id: string;
  decision: DecisionType;
  reasons: string[];
  evidence_refs: string[];
  required_next_action: string | null;
  reviewer_queue: string | null;
  confidence: number;
  rule_refs: string[];
  step_ref: string | null;
  decided_by: string;
  decided_by_id: string | null;
  override_of_decision_id: string | null;
  created_at: string;
};

export type ClaimDocument = {
  id: string;
  claim_id: string;
  filename: string;
  mime_type: string;
  document_type: string | null;
  uploaded_at: string;
  storage_path: string;
  ocr_text: string | null;
  extraction_confidence: number | null;
  metadata_json: Record<string, unknown>;
  fingerprint: string | null;
};

export type WorkflowStep = {
  id: string;
  claim_id: string;
  run_id: string;
  step_name: string;
  status: string;
  state_before: string | null;
  state_after: string | null;
  started_at: string;
  completed_at: string | null;
  latency_ms: number | null;
  output: Record<string, unknown>;
  error_message: string | null;
  retry_count: number;
};

export type ClaimDetail = {
  claim: {
    id: string;
    claim_number: string;
    domain: ClaimDomain;
    subtype: string | null;
    status: string;
    created_at: string;
    updated_at: string;
    submitted_at: string | null;
    incident_or_service_date: string | null;
    policy_or_member_id: string | null;
    claimant_name: string | null;
    priority_score: number | null;
    current_queue: string | null;
    estimated_amount: number | null;
    claim_payload: Record<string, unknown>;
  };
  documents: ClaimDocument[];
  extracted_facts: Array<{
    id: string;
    key: string;
    value: Record<string, unknown>;
    confidence: number;
    source_document_id: string | null;
    source_excerpt: string | null;
  }>;
  validation_issues: Array<{
    id: string;
    category: string;
    field: string | null;
    description: string;
    severity: string;
    confidence: number;
    source_document_ids: string[];
    resolvable_with_more_docs: boolean;
  }>;
  coverage_result: {
    id: string;
    is_covered: boolean | null;
    coverage_type: string | null;
    hard_fail: boolean;
    reasons: string[];
    deductible: number | null;
    benefit_notes: string[];
    confidence: number;
  } | null;
  fraud_result: {
    id: string;
    risk_score: number;
    signals: Array<Record<string, unknown>>;
    recommended_action: string;
  } | null;
  advisory_result: {
    id: string;
    findings: Array<Record<string, unknown>>;
    uncertainty_flags: string[];
    escalation_recommended: boolean;
    confidence: number;
  } | null;
  decision: ClaimDecision | null;
  workflow_steps: WorkflowStep[];
  audit_events: Array<{
    id: string;
    event_type: string;
    actor_type: string;
    actor_id: string;
    timestamp: string;
    payload: Record<string, unknown>;
  }>;
  communication_drafts: Array<{
    id: string;
    audience: string;
    title: string;
    summary: string;
    reasons: string[];
    next_steps: string[];
    tone: string;
    prompt_version: string;
    created_at: string;
  }>;
};

export type EvalRun = {
  id: string;
  status: string;
  started_at: string;
  completed_at: string | null;
  summary: Record<string, unknown>;
  results: Array<Record<string, unknown>>;
};