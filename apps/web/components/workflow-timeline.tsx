import { WorkflowStep } from "@/types/claims";

export function WorkflowTimeline({ steps }: { steps: WorkflowStep[] }) {
  return (
    <div className="space-y-3">
      {steps.map((step) => (
        <div key={step.id} className="rounded-xl border border-slate-200 bg-slate-50 p-3">
          <div className="flex flex-wrap items-center justify-between gap-2">
            <p className="font-medium text-ink">{step.step_name}</p>
            <span className="text-xs uppercase text-muted">{step.status}</span>
          </div>
          <p className="text-xs text-muted">
            {step.state_before ?? "-"} ? {step.state_after ?? "-"}
          </p>
          <p className="text-xs text-muted">Started: {new Date(step.started_at).toLocaleString()}</p>
          {step.completed_at ? <p className="text-xs text-muted">Completed: {new Date(step.completed_at).toLocaleString()}</p> : null}
        </div>
      ))}
      {steps.length === 0 ? <p className="text-sm text-muted">No workflow steps recorded yet.</p> : null}
    </div>
  );
}