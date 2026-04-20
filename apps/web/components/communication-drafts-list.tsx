import { RawDataDisclosure } from "@/components/raw-data-disclosure";
import { ClaimDetail } from "@/types/claims";

type CommunicationDraftViewModel = {
  audience: string | null;
  title: string | null;
  summary: string | null;
  reasons: string[];
  nextSteps: string[];
  tone: string | null;
  createdAt: string | null;
};

export function CommunicationDraftsList({ drafts }: { drafts: ClaimDetail["communication_drafts"] | unknown }) {
  const items = normalizeCommunicationDrafts(drafts);

  if (items.length === 0) {
    return (
      <div className="space-y-4">
        <p className="rounded-xl border border-dashed border-slate-300 bg-slate-50/80 px-4 py-4 text-sm text-muted">
          Communication drafts are not available yet or could not be parsed for display.
        </p>
        {drafts != null ? <RawDataDisclosure title="View raw communication drafts" value={drafts} /> : null}
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div className="space-y-3">
        {items.map((draft, index) => (
          <article key={`${draft.audience ?? "draft"}-${draft.createdAt ?? index}`} className="rounded-2xl border border-slate-200 bg-slate-50/60 p-4">
            <header className="space-y-3">
              <div className="space-y-1">
                <h3 className="text-base font-semibold text-ink">{draft.title ?? `Draft ${index + 1}`}</h3>
                <div className="flex flex-wrap items-center gap-2 text-xs text-muted">
                  {draft.audience ? <MetaChip value={humanizeValue(draft.audience)} /> : null}
                  {draft.tone ? <MetaChip value={`${humanizeValue(draft.tone)} tone`} /> : null}
                  {draft.createdAt ? <span>Created {draft.createdAt}</span> : null}
                </div>
              </div>

              {draft.summary ? <p className="text-sm leading-6 text-ink">{draft.summary}</p> : null}
            </header>

            <div className="mt-4 space-y-4">
              {draft.reasons.length > 0 ? <DraftList title="Reasons" items={draft.reasons} /> : null}
              {draft.nextSteps.length > 0 ? <DraftList title="Next Steps" items={draft.nextSteps} /> : null}
            </div>
          </article>
        ))}
      </div>

      <RawDataDisclosure title="View raw communication drafts" value={drafts} />
    </div>
  );
}

function DraftList({ title, items }: { title: string; items: string[] }) {
  return (
    <section className="space-y-2">
      <h4 className="text-xs font-semibold uppercase tracking-wide text-muted">{title}</h4>
      <ul className="space-y-2">
        {items.map((item) => (
          <li key={item} className="rounded-xl border border-slate-200 bg-white/90 px-3 py-3 text-sm text-ink">
            {item}
          </li>
        ))}
      </ul>
    </section>
  );
}

function MetaChip({ value }: { value: string }) {
  return <span className="rounded-full bg-white/90 px-2.5 py-1 font-medium text-slate-700">{value}</span>;
}

function normalizeCommunicationDrafts(value: unknown): CommunicationDraftViewModel[] {
  const parsed = parseUnknown(value);

  if (Array.isArray(parsed)) {
    return parsed.map((item) => normalizeDraft(item)).filter((item): item is CommunicationDraftViewModel => item !== null);
  }

  if (isObject(parsed) && Array.isArray(parsed.drafts)) {
    return parsed.drafts.map((item) => normalizeDraft(item)).filter((item): item is CommunicationDraftViewModel => item !== null);
  }

  if (isObject(parsed)) {
    const draft = normalizeDraft(parsed);
    return draft ? [draft] : [];
  }

  return [];
}

function normalizeDraft(value: unknown): CommunicationDraftViewModel | null {
  const parsed = parseUnknown(value);
  if (!isObject(parsed)) {
    return null;
  }

  const draft: CommunicationDraftViewModel = {
    audience: getString(parsed.audience),
    title: getString(parsed.title),
    summary: getString(parsed.summary),
    reasons: getStringArray(parsed.reasons),
    nextSteps: getStringArray(parsed.next_steps ?? parsed.nextSteps),
    tone: getString(parsed.tone),
    createdAt: formatDateTime(getString(parsed.created_at)),
  };

  if (!draft.audience && !draft.title && !draft.summary && draft.reasons.length === 0 && draft.nextSteps.length === 0 && !draft.tone && !draft.createdAt) {
    return null;
  }

  return draft;
}

function parseUnknown(value: unknown): unknown {
  if (typeof value !== "string") {
    return value;
  }

  const trimmed = value.trim();
  if (!trimmed) {
    return value;
  }

  if (!(trimmed.startsWith("{") || trimmed.startsWith("["))) {
    return value;
  }

  try {
    return JSON.parse(trimmed);
  } catch {
    return value;
  }
}

function getString(value: unknown): string | null {
  if (typeof value !== "string") {
    return null;
  }
  const trimmed = value.trim();
  return trimmed ? trimmed : null;
}

function getStringArray(value: unknown): string[] {
  const parsed = parseUnknown(value);

  if (Array.isArray(parsed)) {
    return parsed.map((item) => String(item).trim()).filter(Boolean);
  }

  const single = getString(parsed);
  return single ? [single] : [];
}

function formatDateTime(value: string | null): string | null {
  if (!value) {
    return null;
  }

  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) {
    return value;
  }

  return new Intl.DateTimeFormat("en-US", {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(parsed);
}

function humanizeValue(value: string): string {
  return value
    .replace(/_/g, " ")
    .replace(/\b\w/g, (character) => character.toUpperCase());
}

function isObject(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null;
}
