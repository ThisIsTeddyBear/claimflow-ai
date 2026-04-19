import clsx from "clsx";

import { RawDataDisclosure } from "@/components/raw-data-disclosure";
import { ClaimDetail } from "@/types/claims";
import {
  AdvisorySummary,
  FraudSummary,
  CoverageSummary,
  formatConfidence,
  summarizeAdvisory,
  summarizeCoverage,
  summarizeFraud,
} from "@/lib/claim-review-formatters";

export function ReviewInsights({
  coverageResult,
  fraudResult,
  advisoryResult,
}: {
  coverageResult: ClaimDetail["coverage_result"];
  fraudResult: ClaimDetail["fraud_result"];
  advisoryResult: ClaimDetail["advisory_result"];
}) {
  const coverage = summarizeCoverage(coverageResult);
  const fraud = summarizeFraud(fraudResult);
  const advisory = summarizeAdvisory(advisoryResult);

  return (
    <div className="space-y-4">
      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
        <CoveragePanel summary={coverage} />
        <FraudPanel summary={fraud} />
        <AdvisoryPanel summary={advisory} />
      </div>

      <RawDataDisclosure
        title="View raw review data"
        value={{
          coverage_result: coverageResult,
          fraud_result: fraudResult,
          advisory_result: advisoryResult,
        }}
      />
    </div>
  );
}

function CoveragePanel({ summary }: { summary: CoverageSummary | null }) {
  if (!summary) {
    return <EmptyInsightCard title="Coverage" description="Coverage checks have not been run yet." />;
  }

  return (
    <section className="rounded-2xl border border-slate-200 bg-slate-50/70 p-4">
      <header className="space-y-3">
        <p className="text-sm font-semibold text-ink">Coverage</p>
        <StatusBanner
          eyebrow="Coverage status"
          title={summary.statusLabel}
          subtitle={summary.hardFail ? "This case hit a deterministic coverage hard fail." : summary.coverageType}
          tone={summary.tone}
        />
      </header>

      <dl className="mt-4 grid gap-3 sm:grid-cols-2">
        <MetaItem label="Coverage Type" value={summary.coverageType} />
        <MetaItem label="Deductible" value={summary.deductible} />
        <MetaItem label="Confidence" value={summary.confidenceLabel} />
        <MetaItem label="Hard Fail" value={summary.hardFail ? "Yes" : "No"} />
      </dl>

      <InsightList title="Reasons" items={summary.reasons} emptyLabel="No coverage reasons were returned." />
      <InsightList title="Benefit Notes" items={summary.benefitNotes} emptyLabel="No benefit notes provided." />
    </section>
  );
}

function FraudPanel({ summary }: { summary: FraudSummary | null }) {
  if (!summary) {
    return <EmptyInsightCard title="Fraud / Anomaly" description="Risk scoring has not been run yet." />;
  }

  return (
    <section className="rounded-2xl border border-slate-200 bg-slate-50/70 p-4">
      <header className="space-y-3">
        <div className="flex items-start justify-between gap-3">
          <div>
            <p className="text-sm font-semibold text-ink">Fraud / Anomaly</p>
            <p className="text-sm text-muted">Recommended action: {summary.recommendedAction}</p>
          </div>
          <SeverityChip label={summary.severityLabel} tone={summary.severityTone} />
        </div>

        <div className="rounded-2xl border border-slate-200 bg-white/90 p-4">
          <div className="flex items-end justify-between gap-3">
            <div>
              <p className="text-xs uppercase tracking-wide text-muted">Risk Score</p>
              <p className="mt-1 text-3xl font-semibold text-ink">{summary.riskPercent}%</p>
            </div>
            <p className="text-sm font-medium text-muted">{summary.severityLabel} severity</p>
          </div>
          <div aria-hidden="true" className="mt-3 h-2 rounded-full bg-slate-200">
            <div
              className={clsx(
                "h-2 rounded-full transition-all",
                summary.severityTone === "negative" && "bg-rose-500",
                summary.severityTone === "caution" && "bg-amber-500",
                summary.severityTone === "positive" && "bg-emerald-500",
              )}
              style={{ width: `${Math.max(6, summary.riskPercent)}%` }}
            />
          </div>
        </div>
      </header>

      <div className="mt-4 space-y-3">
        <h3 className="text-xs font-semibold uppercase tracking-wide text-muted">Signals</h3>
        {summary.signals.length === 0 ? (
          <p className="rounded-xl border border-dashed border-slate-300 bg-white/80 px-3 py-4 text-sm text-muted">
            No anomaly signals detected.
          </p>
        ) : (
          <ul className="space-y-3">
            {summary.signals.map((signal) => (
              <li key={`${signal.code}-${signal.description}`} className="rounded-xl border border-slate-200 bg-white/90 p-3">
                <div className="flex flex-wrap items-start justify-between gap-2">
                  <div>
                    <p className="text-sm font-semibold text-ink">{signal.description}</p>
                    <p className="mt-1 text-xs uppercase tracking-wide text-muted">{signal.code}</p>
                  </div>
                  <div className="flex flex-wrap gap-2">
                    <span className="rounded-full bg-slate-100 px-2 py-1 text-xs font-semibold text-slate-700">{signal.severity}</span>
                    {signal.confidence != null ? (
                      <span className="rounded-full bg-slate-100 px-2 py-1 text-xs font-semibold text-slate-700">{formatConfidence(signal.confidence)}</span>
                    ) : null}
                  </div>
                </div>
                {signal.evidenceRefs.length > 0 ? (
                  <div className="mt-3 flex flex-wrap gap-2">
                    {signal.evidenceRefs.map((ref) => (
                      <Chip key={ref} value={ref} />
                    ))}
                  </div>
                ) : null}
              </li>
            ))}
          </ul>
        )}
      </div>
    </section>
  );
}

function AdvisoryPanel({ summary }: { summary: AdvisorySummary | null }) {
  if (!summary) {
    return <EmptyInsightCard title="Domain Advisory" description="No advisory findings are available yet." />;
  }

  return (
    <section className="rounded-2xl border border-slate-200 bg-slate-50/70 p-4">
      <header className="space-y-3">
        <p className="text-sm font-semibold text-ink">Domain Advisory</p>
        <StatusBanner
          eyebrow="Advisory recommendation"
          title={summary.escalationRecommended ? "Escalation Recommended" : "No Escalation Recommended"}
          subtitle={summary.confidenceLabel}
          tone={summary.escalationRecommended ? "caution" : "positive"}
        />
      </header>

      <div className="mt-4 space-y-4">
        {summary.groups.length === 0 ? (
          <p className="rounded-xl border border-dashed border-slate-300 bg-white/80 px-3 py-4 text-sm text-muted">
            No advisory findings were produced.
          </p>
        ) : (
          summary.groups.map((group) => (
            <section key={group.title} className="space-y-2">
              <h3 className="text-xs font-semibold uppercase tracking-wide text-muted">{group.title}</h3>
              <ul className="space-y-3">
                {group.findings.map((finding) => (
                  <li key={`${group.title}-${finding.finding}`} className="rounded-xl border border-slate-200 bg-white/90 p-3">
                    <div className="flex items-start justify-between gap-3">
                      <p className="text-sm font-semibold text-ink">{finding.finding}</p>
                      <span className="rounded-full bg-slate-100 px-2 py-1 text-xs font-semibold text-slate-700">
                        {formatConfidence(finding.confidence)}
                      </span>
                    </div>
                    {finding.evidenceRefs.length > 0 ? (
                      <div className="mt-3 flex flex-wrap gap-2">
                        {finding.evidenceRefs.map((ref) => (
                          <Chip key={ref} value={ref} />
                        ))}
                      </div>
                    ) : null}
                  </li>
                ))}
              </ul>
            </section>
          ))
        )}

        <InsightList
          title="Uncertainty Flags"
          items={summary.uncertaintyFlags}
          emptyLabel="No uncertainty flags were raised."
        />
      </div>
    </section>
  );
}

function StatusBanner({
  eyebrow,
  title,
  subtitle,
  tone,
}: {
  eyebrow: string;
  title: string;
  subtitle: string;
  tone: "positive" | "negative" | "caution";
}) {
  return (
    <div
      className={clsx(
        "rounded-2xl border px-4 py-4",
        tone === "positive" && "border-emerald-200 bg-emerald-50",
        tone === "negative" && "border-rose-200 bg-rose-50",
        tone === "caution" && "border-amber-200 bg-amber-50",
      )}
    >
      <p className="text-xs font-semibold uppercase tracking-wide text-muted">{eyebrow}</p>
      <p className="mt-1 text-lg font-semibold text-ink">{title}</p>
      <p className="mt-1 text-sm text-muted">{subtitle}</p>
    </div>
  );
}

function MetaItem({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-xl border border-slate-200 bg-white/90 px-3 py-3">
      <dt className="text-xs uppercase tracking-wide text-muted">{label}</dt>
      <dd className="mt-1 text-sm font-medium text-ink">{value}</dd>
    </div>
  );
}

function InsightList({ title, items, emptyLabel }: { title: string; items: string[]; emptyLabel: string }) {
  return (
    <div className="mt-4 space-y-2">
      <h3 className="text-xs font-semibold uppercase tracking-wide text-muted">{title}</h3>
      {items.length === 0 ? (
        <p className="rounded-xl border border-dashed border-slate-300 bg-white/80 px-3 py-4 text-sm text-muted">{emptyLabel}</p>
      ) : (
        <ul className="space-y-2">
          {items.map((item) => (
            <li key={item} className="rounded-xl border border-slate-200 bg-white/90 px-3 py-3 text-sm text-ink">
              {item}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}

function SeverityChip({ label, tone }: { label: string; tone: "positive" | "caution" | "negative" }) {
  return (
    <span
      className={clsx(
        "rounded-full px-2.5 py-1 text-xs font-semibold uppercase tracking-wide",
        tone === "positive" && "bg-emerald-100 text-emerald-800",
        tone === "caution" && "bg-amber-100 text-amber-800",
        tone === "negative" && "bg-rose-100 text-rose-800",
      )}
    >
      {label}
    </span>
  );
}

function Chip({ value }: { value: string }) {
  return <span className="rounded-full bg-slate-100 px-2 py-1 text-xs font-medium text-slate-700">{value}</span>;
}

function EmptyInsightCard({ title, description }: { title: string; description: string }) {
  return (
    <section className="rounded-2xl border border-dashed border-slate-300 bg-slate-50/80 p-4">
      <p className="text-sm font-semibold text-ink">{title}</p>
      <p className="mt-2 text-sm text-muted">{description}</p>
    </section>
  );
}
