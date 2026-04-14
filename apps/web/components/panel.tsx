import { PropsWithChildren } from "react";

export function Panel({ title, subtitle, children }: PropsWithChildren<{ title: string; subtitle?: string }>) {
  return (
    <section className="rounded-2xl border border-slate-200 bg-white/90 p-5 shadow-panel">
      <header className="mb-4">
        <h2 className="text-lg font-semibold text-ink">{title}</h2>
        {subtitle ? <p className="text-sm text-muted">{subtitle}</p> : null}
      </header>
      {children}
    </section>
  );
}