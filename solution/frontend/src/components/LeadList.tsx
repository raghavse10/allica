"use client";

import { useMemo, useState } from "react";
import { Play } from "lucide-react";
import { LeadCard } from "@/components/LeadCard";
import { LeadDetail } from "@/components/LeadDetail";
import { SearchableMultiSelect } from "@/components/ui/SearchableMultiSelect";
import type { LeadResult, RunResponse } from "@/lib/types";

const BAND_OPTIONS = [
  { value: "high", label: "High" },
  { value: "medium", label: "Medium" },
  { value: "low", label: "Low" },
] as const;

interface LeadListProps {
  response: RunResponse | null;
}

/**
 * Filterable list of leads. Pure client island — operates entirely on the
 * `RunResponse` we already have in memory; no extra fetches.
 */
export function LeadList({ response }: LeadListProps) {
  const [owners, setOwners] = useState<string[]>([]);
  const [bands, setBands] = useState<string[]>([]);
  const [text, setText] = useState("");
  const [active, setActive] = useState<LeadResult | null>(null);

  const ownerSelectOptions = useMemo(() => {
    if (!response) return [];
    return Object.keys(response.summary.by_owner).map((o) => ({ value: o, label: o }));
  }, [response]);

  const filtered = useMemo(() => {
    if (!response) return [];
    return response.leads.filter((l) => {
      if (owners.length > 0 && !owners.includes(l.routing.owner)) return false;
      if (bands.length > 0 && !bands.includes(l.score.band)) return false;
      if (text && !(l.company_name ?? "").toLowerCase().includes(text.toLowerCase()))
        return false;
      return true;
    });
  }, [response, owners, bands, text]);

  if (!response) {
    return (
      <div className="grid place-items-center rounded-[var(--radius-card)] border border-dashed border-line bg-brand-cream-200/50 px-8 py-20 text-center">
        <div className="grid h-14 w-14 place-items-center rounded-full bg-brand-orange/10 text-brand-orange">
          <Play className="h-7 w-7 translate-x-0.5 fill-current" strokeWidth={1.5} aria-hidden />
        </div>
        <h3 className="mt-4 text-base font-semibold text-brand-navy-900">Ready when you are</h3>
        <p className="mt-1 max-w-sm text-sm text-ink-muted">
          Click <strong className="text-brand-navy">Run on sample data</strong> to see how the
          assistant triages 10 inbound leads.
        </p>
      </div>
    );
  }

  function openLead(lead: LeadResult) {
    // For live runs, the FastAPI response carries lead_result_ids in meta;
    // for stored runs, lead_result_id is already on the row.
    if (!lead.lead_result_id && response?.meta.lead_result_ids && lead.id) {
      lead.lead_result_id = response.meta.lead_result_ids[lead.id];
    }
    setActive(lead);
  }

  return (
    <div className="flex min-w-0 flex-col">
      <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
        <h2 className="text-lg font-semibold text-brand-navy-900">Leads</h2>
        <div className="flex flex-wrap items-center gap-2">
          <SearchableMultiSelect
            className="w-52"
            ariaLabel="Filter by owner"
            placeholder="Search owners…"
            emptySummary="All owners"
            options={ownerSelectOptions}
            value={owners}
            onChange={setOwners}
          />
          <SearchableMultiSelect
            className="w-44"
            ariaLabel="Filter by score band"
            placeholder="Search bands…"
            emptySummary="All bands"
            options={[...BAND_OPTIONS]}
            value={bands}
            onChange={setBands}
          />
          <input
            value={text}
            onChange={(e) => setText(e.target.value)}
            placeholder="Search company…"
            className="filter-input w-48"
          />
        </div>
      </div>

      {filtered.length === 0 ? (
        <p className="rounded-[var(--radius-card)] border border-dashed border-line bg-brand-cream-200/50 px-6 py-10 text-center text-sm text-ink-muted">
          No leads match the current filters.
        </p>
      ) : (
        <div className="flex flex-col gap-3">
          {filtered.map((lead) => (
            <LeadCard
              key={`${lead.id ?? "anon"}-${lead.company_name ?? ""}`}
              lead={lead}
              onClick={() => openLead(lead)}
            />
          ))}
        </div>
      )}

      <LeadDetail lead={active} onClose={() => setActive(null)} />

      <style jsx>{`
        .filter-input {
          background: var(--color-brand-cream-100);
          border: 1px solid var(--color-line);
          color: var(--color-ink);
          font-size: 13px;
          font-family: inherit;
          padding: 8px 12px;
          border-radius: 8px;
          transition: border-color 0.15s ease, box-shadow 0.15s ease;
        }
        .filter-input:focus {
          outline: none;
          border-color: var(--color-brand-orange);
          box-shadow: 0 0 0 3px rgba(255, 82, 0, 0.15);
        }
        .filter-input::placeholder {
          color: var(--color-ink-subtle);
        }
      `}</style>
    </div>
  );
}
