"use client";

import { FormEvent, useState } from "react";

import { reviewAction, reviewOverride } from "@/lib/api";
import { DecisionType } from "@/types/claims";

export function ReviewerActions({ claimId, onApplied }: { claimId: string; onApplied: () => void }) {
  const [reviewerId, setReviewerId] = useState("reviewer.demo");
  const [notes, setNotes] = useState("Reviewed by human.");
  const [queue, setQueue] = useState("manual_triage");
  const [decision, setDecision] = useState<DecisionType>("approve");
  const [pending, setPending] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleQuick = async (action: DecisionType) => {
    setPending(true);
    setError(null);
    try {
      await reviewAction(claimId, action, { reviewer_id: reviewerId, notes, reviewer_queue: queue });
      onApplied();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to apply reviewer action");
    } finally {
      setPending(false);
    }
  };

  const handleOverride = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setPending(true);
    setError(null);
    try {
      await reviewOverride(claimId, { reviewer_id: reviewerId, notes, reviewer_queue: queue, decision });
      onApplied();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to override decision");
    } finally {
      setPending(false);
    }
  };

  return (
    <div className="space-y-3">
      <div className="grid gap-2 md:grid-cols-3">
        <input
          className="rounded-lg border border-slate-300 px-3 py-2 text-sm"
          value={reviewerId}
          onChange={(event) => setReviewerId(event.target.value)}
          placeholder="reviewer id"
        />
        <input
          className="rounded-lg border border-slate-300 px-3 py-2 text-sm"
          value={queue}
          onChange={(event) => setQueue(event.target.value)}
          placeholder="queue"
        />
        <input
          className="rounded-lg border border-slate-300 px-3 py-2 text-sm"
          value={notes}
          onChange={(event) => setNotes(event.target.value)}
          placeholder="review notes"
        />
      </div>

      <div className="flex flex-wrap gap-2">
        <button className="rounded-lg bg-emerald-600 px-3 py-2 text-sm text-white disabled:opacity-50" disabled={pending} onClick={() => void handleQuick("approve")}>Approve</button>
        <button className="rounded-lg bg-rose-600 px-3 py-2 text-sm text-white disabled:opacity-50" disabled={pending} onClick={() => void handleQuick("reject")}>Reject</button>
        <button className="rounded-lg bg-amber-600 px-3 py-2 text-sm text-white disabled:opacity-50" disabled={pending} onClick={() => void handleQuick("pend")}>Pend</button>
        <button className="rounded-lg bg-orange-600 px-3 py-2 text-sm text-white disabled:opacity-50" disabled={pending} onClick={() => void handleQuick("escalate")}>Escalate</button>
      </div>

      <form className="flex flex-wrap items-center gap-2" onSubmit={handleOverride}>
        <select className="rounded-lg border border-slate-300 px-3 py-2 text-sm" value={decision} onChange={(event) => setDecision(event.target.value as DecisionType)}>
          <option value="approve">approve</option>
          <option value="reject">reject</option>
          <option value="pend">pend</option>
          <option value="escalate">escalate</option>
        </select>
        <button className="rounded-lg bg-ink px-3 py-2 text-sm text-white disabled:opacity-50" disabled={pending} type="submit">
          Override Decision
        </button>
      </form>

      {error ? <p className="text-sm text-rose-700">{error}</p> : null}
    </div>
  );
}