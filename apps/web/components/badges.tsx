import clsx from "clsx";

export function StatusBadge({ value }: { value: string | null | undefined }) {
  const normalized = (value ?? "unknown").toLowerCase();
  return (
    <span
      className={clsx(
        "inline-flex items-center rounded-full px-2.5 py-1 text-xs font-semibold uppercase tracking-wide",
        normalized.includes("approve") && "bg-emerald-100 text-emerald-800",
        normalized.includes("reject") && "bg-rose-100 text-rose-800",
        normalized.includes("pend") && "bg-amber-100 text-amber-800",
        normalized.includes("escalate") && "bg-orange-100 text-orange-800",
        normalized.includes("under") && "bg-slate-200 text-slate-800",
        normalized.includes("submitted") && "bg-teal-100 text-teal-800",
        normalized.includes("draft") && "bg-slate-100 text-slate-700",
      )}
    >
      {value ?? "unknown"}
    </span>
  );
}

export function RiskBadge({ score }: { score: number | null | undefined }) {
  if (score == null) {
    return <span className="text-sm text-muted">n/a</span>;
  }

  const level = score >= 0.7 ? "high" : score >= 0.4 ? "medium" : "low";
  const cls = level === "high" ? "bg-rose-100 text-rose-800" : level === "medium" ? "bg-amber-100 text-amber-800" : "bg-emerald-100 text-emerald-800";
  return <span className={clsx("inline-flex rounded-full px-2 py-1 text-xs font-semibold uppercase", cls)}>{`${level} (${score})`}</span>;
}