"use client";

import { useCallback, useEffect, useState } from "react";

import { Panel } from "@/components/panel";
import { listEvals, runEvals } from "@/lib/api";
import { EvalRun } from "@/types/claims";

export default function EvalsPage() {
  const [runs, setRuns] = useState<EvalRun[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [running, setRunning] = useState(false);

  const load = useCallback(async () => {
    setError(null);
    try {
      setRuns(await listEvals());
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load eval runs");
    }
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  const handleRun = async () => {
    setRunning(true);
    try {
      await runEvals();
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to run evaluations");
    } finally {
      setRunning(false);
    }
  };

  return (
    <div className="space-y-6">
      <Panel title="Evaluation Harness" subtitle="Run extraction + decision outcome checks across synthetic fixtures.">
        <div className="flex items-center gap-2">
          <button className="rounded-lg bg-accent px-3 py-2 text-sm font-medium text-white disabled:opacity-50" disabled={running} onClick={() => void handleRun()}>
            {running ? "Running Evals..." : "Run Evaluations"}
          </button>
          <button className="rounded-lg border border-slate-300 px-3 py-2 text-sm" onClick={() => void load()}>
            Refresh
          </button>
        </div>
        {error ? <p className="mt-2 text-sm text-rose-700">{error}</p> : null}
      </Panel>

      <Panel title="Recent Evaluation Runs" subtitle="Accuracy and scenario-by-scenario outcome alignment.">
        <div className="space-y-4">
          {runs.map((run) => (
            <article key={run.id} className="rounded-xl border border-slate-200 p-4">
              <p className="text-sm font-semibold">Run {run.id}</p>
              <p className="text-xs text-muted">Started {new Date(run.started_at).toLocaleString()}</p>
              <p className="mt-2 text-sm">Summary: {JSON.stringify(run.summary)}</p>
              <details className="mt-2">
                <summary className="cursor-pointer text-sm text-accent">View scenario results</summary>
                <pre className="mt-2 max-h-72 overflow-auto rounded-lg bg-slate-950 p-3 text-xs text-slate-100">
                  {JSON.stringify(run.results, null, 2)}
                </pre>
              </details>
            </article>
          ))}
          {runs.length === 0 ? <p className="text-sm text-muted">No eval runs yet.</p> : null}
        </div>
      </Panel>
    </div>
  );
}