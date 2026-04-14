"use client";

import { FormEvent, useState } from "react";
import { useRouter } from "next/navigation";

import { Panel } from "@/components/panel";
import { createClaim, uploadClaimDocument } from "@/lib/api";
import { ClaimDomain } from "@/types/claims";

export default function NewClaimPage() {
  const router = useRouter();
  const [domain, setDomain] = useState<ClaimDomain>("auto");
  const [subtype, setSubtype] = useState("own_damage");
  const [date, setDate] = useState("");
  const [memberOrPolicy, setMemberOrPolicy] = useState("");
  const [claimantName, setClaimantName] = useState("");
  const [amount, setAmount] = useState("");
  const [files, setFiles] = useState<FileList | null>(null);
  const [status, setStatus] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setSubmitting(true);
    setStatus(null);

    try {
      const claim = await createClaim({
        domain,
        subtype,
        incident_or_service_date: date || null,
        policy_or_member_id: memberOrPolicy || null,
        claimant_name: claimantName || null,
        estimated_amount: amount ? Number(amount) : null,
        claim_payload: {},
      });

      if (files) {
        const uploads = Array.from(files).map((file) => uploadClaimDocument(claim.id, file));
        await Promise.all(uploads);
      }

      setStatus("Claim created successfully.");
      router.push(`/claims/${claim.id}`);
    } catch (err) {
      setStatus(err instanceof Error ? err.message : "Failed to create claim");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <Panel title="New Claim Intake" subtitle="Create a synthetic claim and attach supporting documents.">
      <form className="grid gap-4" onSubmit={handleSubmit}>
        <div className="grid gap-4 md:grid-cols-2">
          <label className="grid gap-1 text-sm">
            Domain
            <select className="rounded-lg border border-slate-300 px-3 py-2" value={domain} onChange={(event) => setDomain(event.target.value as ClaimDomain)}>
              <option value="auto">Auto</option>
              <option value="healthcare">Healthcare</option>
            </select>
          </label>

          <label className="grid gap-1 text-sm">
            Subtype
            <input className="rounded-lg border border-slate-300 px-3 py-2" value={subtype} onChange={(event) => setSubtype(event.target.value)} />
          </label>

          <label className="grid gap-1 text-sm">
            Incident / Service Date
            <input type="date" className="rounded-lg border border-slate-300 px-3 py-2" value={date} onChange={(event) => setDate(event.target.value)} />
          </label>

          <label className="grid gap-1 text-sm">
            Policy / Member ID
            <input className="rounded-lg border border-slate-300 px-3 py-2" value={memberOrPolicy} onChange={(event) => setMemberOrPolicy(event.target.value)} />
          </label>

          <label className="grid gap-1 text-sm">
            Claimant Name
            <input className="rounded-lg border border-slate-300 px-3 py-2" value={claimantName} onChange={(event) => setClaimantName(event.target.value)} />
          </label>

          <label className="grid gap-1 text-sm">
            Estimated Amount
            <input type="number" className="rounded-lg border border-slate-300 px-3 py-2" value={amount} onChange={(event) => setAmount(event.target.value)} />
          </label>
        </div>

        <label className="grid gap-1 text-sm">
          Attach Documents
          <input className="rounded-lg border border-slate-300 px-3 py-2" type="file" multiple onChange={(event) => setFiles(event.target.files)} />
        </label>

        <button className="w-fit rounded-lg bg-accent px-4 py-2 text-sm font-semibold text-white disabled:opacity-50" disabled={submitting} type="submit">
          {submitting ? "Creating..." : "Create Claim"}
        </button>

        {status ? <p className="text-sm text-muted">{status}</p> : null}
      </form>
    </Panel>
  );
}