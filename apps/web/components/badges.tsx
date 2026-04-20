import clsx from "clsx";

export function StatusBadge({ value }: { value: string | null | undefined }) {
  const normalized = (value ?? "unknown").toLowerCase();
  const badgeClass = (() => {
    if (normalized.includes("approve")) return "bg-emerald-100 text-emerald-800";
    if (normalized.includes("reject")) return "bg-rose-100 text-rose-800";
    if (normalized.includes("escalate")) return "bg-orange-100 text-orange-800";
    if (normalized.includes("pend")) return "bg-amber-100 text-amber-800";
    if (normalized.includes("under")) return "bg-slate-200 text-slate-800";
    if (normalized.includes("submitted")) return "bg-teal-100 text-teal-800";
    if (normalized.includes("draft")) return "bg-slate-100 text-slate-700";
    return "bg-slate-100 text-slate-700";
  })();

  return (
    <span
      className={clsx(
        "inline-flex items-center rounded-full px-2.5 py-1 text-xs font-semibold uppercase tracking-wide",
        badgeClass,
      )}
    >
      {value ?? "unknown"}
    </span>
  );
}

export function RiskBadge({ score }: { score: number | null | undefined }) {
  if (score == null) {
    return <span className="inline-flex rounded-full bg-slate-100 px-2 py-1 text-xs font-semibold uppercase text-slate-700">n/a</span>;
  }

  const level = score >= 0.7 ? "high" : score >= 0.4 ? "medium" : "low";
  const cls = level === "high" ? "bg-rose-100 text-rose-800" : level === "medium" ? "bg-amber-100 text-amber-800" : "bg-emerald-100 text-emerald-800";
  return <span className={clsx("inline-flex items-center rounded-full px-2 py-1 text-xs font-semibold uppercase", cls)}>{`${level} (${score})`}</span>;
}
