import clsx from "clsx";

import { RawDataDisclosure } from "@/components/raw-data-disclosure";
import { ClaimDetail, ClaimDocument } from "@/types/claims";
import { FactSection, buildFactSections, formatConfidence } from "@/lib/claim-review-formatters";

export function ExtractedFactsSummary({
  domain,
  facts,
  documents,
}: {
  domain: ClaimDetail["claim"]["domain"];
  facts: ClaimDetail["extracted_facts"];
  documents: ClaimDocument[];
}) {
  if (facts.length === 0) {
    return (
      <div className="space-y-4">
        <EmptyState
          title="No extracted facts yet"
          description="Run the workflow to turn the uploaded documents into reviewer-friendly claim facts."
        />
        <RawDataDisclosure value={facts} />
      </div>
    );
  }

  const sections = buildFactSections(domain, facts, documents);

  return (
    <div className="space-y-6">
      {sections.map((section) => (
        <FactSectionCard key={section.title} section={section} />
      ))}
      <RawDataDisclosure value={facts} />
    </div>
  );
}

function FactSectionCard({ section }: { section: FactSection }) {
  return (
    <section className="space-y-3">
      <div className="flex items-center justify-between gap-3">
        <div>
          <h3 className="text-sm font-semibold uppercase tracking-wide text-muted">{section.title}</h3>
          <p className="text-sm text-muted">
            {section.fields.length} fact{section.fields.length === 1 ? "" : "s"} surfaced for review.
          </p>
        </div>
      </div>

      <div className="grid gap-3 md:grid-cols-2">
        {section.fields.map((field) => (
          <article key={field.key} className="rounded-2xl border border-slate-200 bg-slate-50/70 p-4">
            <div className="flex items-start justify-between gap-3">
              <div className="min-w-0">
                <p className="text-xs uppercase tracking-wide text-muted">{field.label}</p>
                <p className="mt-1 break-words text-sm font-semibold text-ink">{field.primary.displayValue}</p>
              </div>
              <ConfidencePill confidence={field.primary.confidence} />
            </div>

            <div className="mt-3 space-y-2">
              <ConfidenceBar confidence={field.primary.confidence} />
              {field.primary.sourceDocumentName ? (
                <p className="text-xs text-muted">Primary source: {field.primary.sourceDocumentName}</p>
              ) : null}
            </div>

            {(field.primary.sourceExcerpt || field.entries.length > 1) ? (
              <details className="mt-4 rounded-xl border border-slate-200 bg-white/80">
                <summary className="cursor-pointer list-none px-3 py-2 text-sm font-medium text-accent marker:hidden">
                  Source context
                </summary>
                <div className="space-y-3 border-t border-slate-200 px-3 py-3">
                  {field.primary.sourceExcerpt ? (
                    <div>
                      <p className="text-xs font-semibold uppercase tracking-wide text-muted">Excerpt</p>
                      <p className="mt-1 text-sm text-ink">{field.primary.sourceExcerpt}</p>
                    </div>
                  ) : null}

                  {field.entries.length > 1 ? (
                    <div>
                      <p className="text-xs font-semibold uppercase tracking-wide text-muted">Other extracted values</p>
                      <ul className="mt-2 space-y-2">
                        {field.entries.slice(1).map((entry) => (
                          <li key={entry.id} className="rounded-lg border border-slate-200 bg-slate-50 px-3 py-2">
                            <div className="flex flex-wrap items-center justify-between gap-2">
                              <span className="text-sm font-medium text-ink">{entry.displayValue}</span>
                              <span className="text-xs text-muted">{formatConfidence(entry.confidence)}</span>
                            </div>
                            {entry.sourceDocumentName ? <p className="mt-1 text-xs text-muted">{entry.sourceDocumentName}</p> : null}
                            {entry.sourceExcerpt ? <p className="mt-1 text-xs text-muted">{entry.sourceExcerpt}</p> : null}
                          </li>
                        ))}
                      </ul>
                    </div>
                  ) : null}
                </div>
              </details>
            ) : null}
          </article>
        ))}
      </div>
    </section>
  );
}

function ConfidencePill({ confidence }: { confidence: number }) {
  const tone = confidence >= 0.85 ? "strong" : confidence >= 0.65 ? "medium" : "light";
  return (
    <span
      className={clsx(
        "shrink-0 rounded-full px-2.5 py-1 text-xs font-semibold",
        tone === "strong" && "bg-emerald-100 text-emerald-800",
        tone === "medium" && "bg-amber-100 text-amber-800",
        tone === "light" && "bg-slate-200 text-slate-700",
      )}
    >
      {formatConfidence(confidence)}
    </span>
  );
}

function ConfidenceBar({ confidence }: { confidence: number }) {
  const color = confidence >= 0.85 ? "bg-emerald-500" : confidence >= 0.65 ? "bg-amber-500" : "bg-slate-400";
  return (
    <div aria-hidden="true" className="h-2 rounded-full bg-slate-200">
      <div className={clsx("h-2 rounded-full transition-all", color)} style={{ width: `${Math.max(6, confidence * 100)}%` }} />
    </div>
  );
}

function EmptyState({ title, description }: { title: string; description: string }) {
  return (
    <div className="rounded-2xl border border-dashed border-slate-300 bg-slate-50/80 p-6 text-center">
      <h3 className="text-sm font-semibold text-ink">{title}</h3>
      <p className="mt-2 text-sm text-muted">{description}</p>
    </div>
  );
}
