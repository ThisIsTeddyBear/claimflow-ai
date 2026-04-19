import { JsonView } from "@/components/json-view";

export function RawDataDisclosure({ title = "View raw JSON", value }: { title?: string; value: unknown }) {
  return (
    <details className="rounded-xl border border-slate-200 bg-slate-50/80">
      <summary className="cursor-pointer list-none px-4 py-3 text-sm font-medium text-ink marker:hidden">
        <span className="inline-flex items-center gap-2">
          <span className="text-xs uppercase tracking-wide text-muted">Debug</span>
          {title}
        </span>
      </summary>
      <div className="border-t border-slate-200 px-4 py-4">
        <JsonView value={value} />
      </div>
    </details>
  );
}
