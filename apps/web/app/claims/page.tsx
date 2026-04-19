"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import Link from "next/link";

import { Panel } from "@/components/panel";
import { RiskBadge, StatusBadge } from "@/components/badges";
import { listClaims, seedDemoData } from "@/lib/api";
import {
  ClaimSummary,
  ClaimStatus,
  CLAIM_DECISION_FILTER_OPTIONS,
  CLAIM_STATUS_FILTER_OPTIONS,
  DecisionType,
} from "@/types/claims";

export default function ClaimsPage() {
  const [claims, setClaims] = useState<ClaimSummary[]>([]);
  const [domain, setDomain] = useState<string>("");
  const [status, setStatus] = useState<ClaimStatus | "">("");
  const [decision, setDecision] = useState<DecisionType | "">("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [seedMessage, setSeedMessage] = useState<string | null>(null);

  const loadClaims = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await listClaims({
        domain: domain || undefined,
        status: status || undefined,
        decision: decision || undefined,
      });
      setClaims(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load claims");
    } finally {
      setLoading(false);
    }
  }, [decision, domain, status]);

  useEffect(() => {
    void loadClaims();
  }, [loadClaims]);

  const stats = useMemo(() => {
    const total = claims.length;
    const auto = claims.filter((claim) => claim.domain === "auto").length;
    const healthcare = total - auto;
    const escalated = claims.filter((claim) => claim.latest_decision === "escalate").length;
    return { total, auto, healthcare, escalated };
  }, [claims]);

  const handleSeed = async () => {
    try {
      const result = await seedDemoData();
      setSeedMessage(`Seeded ${result.claims_created} new claims from ${result.scenarios_loaded} scenarios.`);
      await loadClaims();
    } catch (err) {
      setSeedMessage(err instanceof Error ? err.message : "Failed to seed demo data");
    }
  };

  return (
    <div className="space-y-6">
      <section className="grid gap-4 md:grid-cols-4">
        <Stat label="Total Claims" value={stats.total} />
        <Stat label="Auto" value={stats.auto} />
        <Stat label="Healthcare" value={stats.healthcare} />
        <Stat label="Escalated" value={stats.escalated} />
      </section>

      <Panel title="Claims Queue" subtitle="Search and filter active and historical adjudication cases.">
        <div className="mb-4 flex flex-wrap gap-2">
          <select className="rounded-lg border border-slate-300 px-3 py-2 text-sm" value={domain} onChange={(event) => setDomain(event.target.value)}>
            <option value="">All domains</option>
            <option value="auto">Auto</option>
            <option value="healthcare">Healthcare</option>
          </select>
          <select className="rounded-lg border border-slate-300 px-3 py-2 text-sm" value={status} onChange={(event) => setStatus(event.target.value as ClaimStatus | "")}>
            {CLAIM_STATUS_FILTER_OPTIONS.map((option) => (
              <option key={option.label} value={option.value}>
                {option.label}
              </option>
            ))}
          </select>
          <select className="rounded-lg border border-slate-300 px-3 py-2 text-sm" value={decision} onChange={(event) => setDecision(event.target.value as DecisionType | "")}>
            {CLAIM_DECISION_FILTER_OPTIONS.map((option) => (
              <option key={option.label} value={option.value}>
                {option.label}
              </option>
            ))}
          </select>
          <button className="rounded-lg bg-accent px-3 py-2 text-sm font-medium text-white" onClick={() => void loadClaims()}>
            Refresh
          </button>
          <button className="rounded-lg bg-ink px-3 py-2 text-sm font-medium text-white" onClick={() => void handleSeed()}>
            Seed Demo Scenarios
          </button>
          <Link href="/claims/new" className="rounded-lg bg-okay px-3 py-2 text-sm font-medium text-white">
            Create Claim
          </Link>
        </div>

        {seedMessage ? <p className="mb-3 text-sm text-muted">{seedMessage}</p> : null}
        {error ? <p className="text-sm text-rose-700">{error}</p> : null}

        <div className="overflow-x-auto">
          <table className="w-full min-w-[1000px] border-separate border-spacing-y-2 text-sm">
            <thead>
              <tr className="text-left text-xs uppercase text-muted">
                <th className="px-3 py-2">Claim</th>
                <th className="px-3 py-2">Domain</th>
                <th className="px-3 py-2">Status</th>
                <th className="px-3 py-2">Decision</th>
                <th className="px-3 py-2">Risk</th>
                <th className="px-3 py-2">Member/Policy</th>
                <th className="px-3 py-2">Date</th>
                <th className="px-3 py-2">Amount</th>
                <th className="px-3 py-2">Queue</th>
                <th className="px-3 py-2">Open</th>
              </tr>
            </thead>
            <tbody>
              {loading ? (
                <tr>
                  <td className="px-3 py-4 text-muted" colSpan={10}>
                    Loading claims...
                  </td>
                </tr>
              ) : claims.length === 0 ? (
                <tr>
                  <td className="px-3 py-4 text-muted" colSpan={10}>
                    No claims found.
                  </td>
                </tr>
              ) : (
                claims.map((claim) => (
                  <tr key={claim.id} className="rounded-xl bg-white">
                    <td className="rounded-l-xl px-3 py-3 font-semibold">{claim.claim_number}</td>
                    <td className="px-3 py-3 capitalize">{claim.domain}</td>
                    <td className="px-3 py-3"><StatusBadge value={claim.status} /></td>
                    <td className="px-3 py-3"><StatusBadge value={claim.latest_decision ?? "none"} /></td>
                    <td className="px-3 py-3"><RiskBadge score={claim.risk_score} /></td>
                    <td className="px-3 py-3">{claim.policy_or_member_id ?? "-"}</td>
                    <td className="px-3 py-3">{claim.incident_or_service_date ?? "-"}</td>
                    <td className="px-3 py-3">{claim.estimated_amount != null ? `$${claim.estimated_amount}` : "-"}</td>
                    <td className="px-3 py-3">{claim.current_queue ?? "-"}</td>
                    <td className="rounded-r-xl px-3 py-3">
                      <Link href={`/claims/${claim.id}`} className="rounded-lg border border-slate-300 px-2 py-1 text-xs hover:bg-slate-50">
                        Review
                      </Link>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </Panel>
    </div>
  );
}

function Stat({ label, value }: { label: string; value: number }) {
  return (
    <div className="rounded-2xl border border-slate-200 bg-white/90 p-4 shadow-panel">
      <p className="text-xs uppercase tracking-wide text-muted">{label}</p>
      <p className="mt-2 text-2xl font-semibold text-ink">{value}</p>
    </div>
  );
}
