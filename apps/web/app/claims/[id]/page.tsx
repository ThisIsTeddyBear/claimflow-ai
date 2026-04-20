"use client";

import { useCallback, useEffect, useState } from "react";
import { useParams } from "next/navigation";

import { DecisionCard } from "@/components/decision-card";
import { CommunicationDraftsList } from "@/components/communication-drafts-list";
import { ExtractedFactsSummary } from "@/components/extracted-facts-summary";
import { JsonView } from "@/components/json-view";
import { Panel } from "@/components/panel";
import { ReviewerActions } from "@/components/reviewer-actions";
import { ReviewInsights } from "@/components/review-insights";
import { RiskBadge, StatusBadge } from "@/components/badges";
import { WorkflowTimeline } from "@/components/workflow-timeline";
import { getClaimDetail, rerunWorkflowStep, runWorkflow } from "@/lib/api";
import { ClaimDetail } from "@/types/claims";

export default function ClaimDetailPage() {
  const params = useParams<{ id: string }>();
  const claimId = params.id ?? "";
  const [detail, setDetail] = useState<ClaimDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [running, setRunning] = useState(false);

  const load = useCallback(async () => {
    if (!claimId) {
      setLoading(false);
      setError("Invalid claim id.");
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const data = await getClaimDetail(claimId);
      setDetail(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load claim");
    } finally {
      setLoading(false);
    }
  }, [claimId]);

  useEffect(() => {
    void load();
  }, [load]);

  const handleRunWorkflow = async () => {
    setRunning(true);
    try {
      await runWorkflow(claimId);
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to run workflow");
    } finally {
      setRunning(false);
    }
  };

  const handleRerun = async (stepName: string) => {
    setRunning(true);
    try {
      await rerunWorkflowStep(claimId, stepName);
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to rerun workflow step");
    } finally {
      setRunning(false);
    }
  };

  if (loading) {
    return <p className="text-sm text-muted">Loading claim...</p>;
  }

  if (error) {
    return <p className="text-sm text-rose-700">{error}</p>;
  }

  if (!detail) {
    return <p className="text-sm text-muted">Claim not found.</p>;
  }

  return (
    <div className="space-y-6">
      <Panel title="Claim Header" subtitle="Intake snapshot and current workflow state.">
        <div className="space-y-5">
          <div className="space-y-1">
            <h2 className="text-2xl font-semibold text-ink">{detail.claim.claim_number}</h2>
            {detail.claim.claimant_name ? <p className="text-sm text-muted">{detail.claim.claimant_name}</p> : null}
          </div>

          <dl className="grid gap-x-6 gap-y-3 text-sm sm:grid-cols-2 xl:grid-cols-3">
            <HeaderDetail label="Domain" value={detail.claim.domain} />
            <HeaderDetail label="Subtype" value={detail.claim.subtype ?? "-"} />
            <HeaderDetail label="Member/Policy" value={detail.claim.policy_or_member_id ?? "-"} />
            <HeaderDetail label="Claimant" value={detail.claim.claimant_name ?? "-"} />
            <HeaderDetail label="Date" value={detail.claim.incident_or_service_date ?? "-"} />
            <HeaderDetail label="Amount" value={detail.claim.estimated_amount != null ? `$${detail.claim.estimated_amount}` : "-"} />
          </dl>

          <section className="space-y-3">
            <p className="text-xs font-medium uppercase tracking-wide text-muted">Workflow Summary</p>
            <dl className="grid gap-3 md:grid-cols-3">
              <WorkflowMetric label="Status">
                <StatusBadge value={detail.claim.status || "Unknown"} />
              </WorkflowMetric>
              <WorkflowMetric label="Decision">
                <StatusBadge value={detail.decision?.decision ?? "None"} />
              </WorkflowMetric>
              <WorkflowMetric label="Risk">
                <RiskBadge score={detail.fraud_result?.risk_score} />
              </WorkflowMetric>
            </dl>
          </section>
        </div>
        <div className="mt-5 flex flex-wrap gap-2 border-t border-slate-200 pt-4">
          <button className="rounded-lg bg-accent px-3 py-2 text-sm font-medium text-white disabled:opacity-50" disabled={running} onClick={() => void handleRunWorkflow()}>
            {running ? "Running..." : "Run Workflow"}
          </button>
          <button className="rounded-lg bg-ink px-3 py-2 text-sm font-medium text-white disabled:opacity-50" disabled={running} onClick={() => void handleRerun("extraction")}>
            Rerun From Extraction
          </button>
          <button className="rounded-lg border border-slate-300 px-3 py-2 text-sm" disabled={running} onClick={() => void load()}>
            Refresh
          </button>
        </div>
      </Panel>

      <div className="grid gap-6 xl:grid-cols-3">
        <div className="space-y-6 xl:col-span-2">
          <Panel title="Documents" subtitle="Uploaded packet documents and parsed text preview.">
            <div className="space-y-3">
              {detail.documents.map((doc) => (
                <div key={doc.id} className="rounded-xl border border-slate-200 bg-slate-50 p-3">
                  <div className="flex flex-wrap items-center gap-2">
                    <p className="font-medium">{doc.filename}</p>
                    <StatusBadge value={doc.document_type ?? "unknown"} />
                    {doc.extraction_confidence != null ? <span className="text-xs text-muted">extraction {doc.extraction_confidence.toFixed(2)}</span> : null}
                  </div>
                  <p className="mt-2 line-clamp-3 text-xs text-muted">{doc.ocr_text ?? "No parsed text"}</p>
                </div>
              ))}
              {detail.documents.length === 0 ? <p className="text-sm text-muted">No documents uploaded.</p> : null}
            </div>
          </Panel>

          <Panel title="Extracted Facts" subtitle="Structured entity output from extraction agent.">
            <ExtractedFactsSummary domain={detail.claim.domain} facts={detail.extracted_facts} documents={detail.documents} />
          </Panel>

          <Panel title="Validation Issues" subtitle="Contradictions and deterministic validation findings.">
            {detail.validation_issues.length === 0 ? (
              <p className="text-sm text-muted">No validation issues found.</p>
            ) : (
              <ul className="space-y-2 text-sm">
                {detail.validation_issues.map((issue) => (
                  <li key={issue.id} className="rounded-xl border border-slate-200 p-3">
                    <div className="flex flex-wrap items-center gap-2">
                      <StatusBadge value={issue.severity} />
                      <span className="text-xs uppercase text-muted">{issue.category}</span>
                    </div>
                    <p className="mt-1 text-ink">{issue.description}</p>
                  </li>
                ))}
              </ul>
            )}
          </Panel>

          <Panel title="Coverage, Anomaly, Advisory" subtitle="Deterministic coverage checks and advisory findings.">
            <ReviewInsights
              coverageResult={detail.coverage_result}
              fraudResult={detail.fraud_result}
              advisoryResult={detail.advisory_result}
            />
          </Panel>

          <Panel title="Workflow Timeline" subtitle="Replayable step-by-step execution trace.">
            <WorkflowTimeline steps={detail.workflow_steps} />
          </Panel>

          <Panel title="Audit Trail" subtitle="System and human events with payload details.">
            <JsonView value={detail.audit_events} />
          </Panel>
        </div>

        <div className="space-y-6">
          <Panel title="Final Decision" subtitle="Deterministic outcome and rationale.">
            <DecisionCard decision={detail.decision} />
          </Panel>

          <Panel title="Why This Decision?" subtitle="Reason chain, evidence references, and rule refs.">
            <JsonView
              value={{
                reasons: detail.decision?.reasons ?? [],
                evidence_refs: detail.decision?.evidence_refs ?? [],
                rule_refs: detail.decision?.rule_refs ?? [],
                required_next_action: detail.decision?.required_next_action,
              }}
            />
          </Panel>

          <Panel title="Human Review Actions" subtitle="Approve, reject, pend, escalate, or override.">
            <ReviewerActions claimId={claimId} onApplied={() => void load()} />
          </Panel>

          <Panel title="Communication Drafts" subtitle="Internal and external message drafts from explanation agent.">
            <CommunicationDraftsList drafts={detail.communication_drafts} />
          </Panel>
        </div>
      </div>
    </div>
  );
}

function WorkflowMetric({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div className="rounded-xl border border-slate-200 bg-slate-50/60 px-4 py-3">
      <dt className="text-xs font-medium uppercase tracking-wide text-muted">{label}</dt>
      <dd className="mt-2 flex min-h-8 items-center">{children}</dd>
    </div>
  );
}

function HeaderDetail({ label, value }: { label: string; value: string }) {
  return (
    <div className="space-y-1">
      <dt className="text-xs font-medium uppercase tracking-wide text-muted">{label}</dt>
      <dd className="text-sm text-ink">{value}</dd>
    </div>
  );
}
