import { ClaimDecision } from "@/types/claims";
import { StatusBadge } from "@/components/badges";

export function DecisionCard({ decision }: { decision: ClaimDecision | null }) {
  if (!decision) {
    return <p className="text-sm text-muted">No decision yet.</p>;
  }

  return (
    <div className="space-y-3 rounded-2xl border border-slate-200 bg-white p-4">
      <div className="flex items-center justify-between">
        <StatusBadge value={decision.decision} />
        <span className="text-xs text-muted">confidence {decision.confidence.toFixed(2)}</span>
      </div>
      <ul className="list-disc space-y-1 pl-5 text-sm text-ink">
        {decision.reasons.map((reason) => (
          <li key={reason}>{reason}</li>
        ))}
      </ul>
      {decision.required_next_action ? <p className="text-sm text-muted">Next action: {decision.required_next_action}</p> : null}
      {decision.reviewer_queue ? <p className="text-sm text-muted">Queue: {decision.reviewer_queue}</p> : null}
    </div>
  );
}