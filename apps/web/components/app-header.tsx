import Link from "next/link";
import { Shield, Stethoscope, CarFront } from "lucide-react";

export function AppHeader() {
  return (
    <header className="mb-6 rounded-3xl border border-slate-200 bg-white/90 p-4 shadow-panel">
      <div className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
        <div className="flex items-center gap-3">
          <div className="rounded-xl bg-accent p-2 text-white">
            <Shield className="h-5 w-5" />
          </div>
          <div>
            <h1 className="text-xl font-semibold">ClaimFlow AI Ops Console</h1>
            <p className="text-sm text-muted">Hybrid adjudication for auto and healthcare claims</p>
          </div>
        </div>
        <nav className="flex items-center gap-3 text-sm font-medium">
          <Link className="rounded-lg px-3 py-2 hover:bg-slate-100" href="/claims">
            Claims Queue
          </Link>
          <Link className="rounded-lg px-3 py-2 hover:bg-slate-100" href="/claims/new">
            New Claim
          </Link>
          <Link className="rounded-lg px-3 py-2 hover:bg-slate-100" href="/evals">
            Evals
          </Link>
          <span className="hidden items-center gap-1 rounded-lg bg-slate-100 px-3 py-2 text-slate-600 md:flex">
            <CarFront className="h-4 w-4" /> Auto
          </span>
          <span className="hidden items-center gap-1 rounded-lg bg-slate-100 px-3 py-2 text-slate-600 md:flex">
            <Stethoscope className="h-4 w-4" /> Healthcare
          </span>
        </nav>
      </div>
    </header>
  );
}