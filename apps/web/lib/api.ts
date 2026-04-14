import { API_BASE_URL } from "@/lib/config";
import { ClaimDetail, ClaimDomain, ClaimSummary, DecisionType, EvalRun } from "@/types/claims";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...init,
    headers: {
      ...(init?.headers ?? {}),
    },
    cache: "no-store",
  });

  if (!response.ok) {
    const text = await response.text();
    throw new Error(`Request failed ${response.status}: ${text}`);
  }
  return (await response.json()) as T;
}

export async function listClaims(params?: { domain?: string; status?: string; decision?: string }): Promise<ClaimSummary[]> {
  const query = new URLSearchParams();
  if (params?.domain) query.set("domain", params.domain);
  if (params?.status) query.set("status", params.status);
  if (params?.decision) query.set("decision", params.decision);
  const suffix = query.toString() ? `?${query.toString()}` : "";
  return request<ClaimSummary[]>(`/claims${suffix}`);
}

export async function createClaim(payload: {
  domain: ClaimDomain;
  subtype?: string | null;
  incident_or_service_date?: string | null;
  policy_or_member_id?: string | null;
  claimant_name?: string | null;
  estimated_amount?: number | null;
  claim_payload?: Record<string, unknown>;
}) {
  return request<{ id: string }>("/claims", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
}

export async function uploadClaimDocument(claimId: string, file: File, documentType?: string): Promise<void> {
  const body = new FormData();
  body.append("file", file);
  if (documentType) {
    body.append("document_type", documentType);
  }

  await request(`/claims/${claimId}/documents`, {
    method: "POST",
    body,
  });
}

export async function runWorkflow(claimId: string) {
  return request(`/claims/${claimId}/run`, { method: "POST" });
}

export async function rerunWorkflowStep(claimId: string, stepName: string) {
  return request(`/claims/${claimId}/rerun-step/${stepName}`, { method: "POST" });
}

export async function getClaimDetail(claimId: string): Promise<ClaimDetail> {
  return request<ClaimDetail>(`/claims/${claimId}`);
}

export async function reviewAction(claimId: string, action: DecisionType, payload: { reviewer_id: string; notes: string; reviewer_queue?: string }) {
  return request(`/claims/${claimId}/review/${action}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
}

export async function reviewOverride(
  claimId: string,
  payload: { reviewer_id: string; notes: string; decision: DecisionType; reviewer_queue?: string },
) {
  return request(`/claims/${claimId}/review/override`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
}

export async function seedDemoData() {
  return request<{ scenarios_loaded: number; claims_created: number; documents_created: number }>("/demo/seed", {
    method: "POST",
  });
}

export async function listEvals(): Promise<EvalRun[]> {
  return request<EvalRun[]>("/evals");
}

export async function runEvals(): Promise<EvalRun> {
  return request<EvalRun>("/evals/run", { method: "POST" });
}