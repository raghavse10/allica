"use client";

import { useState, useTransition } from "react";
import { ArrowRight } from "lucide-react";
import { recordOverrideAction } from "@/app/actions";
import { cn } from "@/lib/cn";
import { formatDateTime } from "@/lib/format";
import type { LeadResult } from "@/lib/types";

const ROUTING_OWNERS = ["Growth-Inbound", "Triage", "Manual-Review", "Decline"] as const;

export function OverrideControls({ lead }: { lead: LeadResult }) {
  const [pending, startTransition] = useTransition();
  const [error, setError] = useState<string | null>(null);
  const [overrides, setOverrides] = useState(lead.overrides ?? []);
  const [savingOwner, setSavingOwner] = useState<string | null>(null);

  if (!lead.lead_result_id) {
    return (
      <div className="mt-3 text-xs text-ink-subtle">
        Run is not yet persisted; routing feedback is disabled.
      </div>
    );
  }

  function submit(owner: string) {
    setError(null);
    setSavingOwner(owner);
    startTransition(async () => {
      try {
        const created = await recordOverrideAction(lead.lead_result_id!, owner);
        setOverrides((prev) => [...prev, created]);
      } catch (e) {
        setError(e instanceof Error ? e.message : String(e));
      } finally {
        setSavingOwner(null);
      }
    });
  }

  return (
    <div className="mt-3">
      <div className="flex flex-wrap gap-1.5">
        {ROUTING_OWNERS.map((owner) => {
          const current = owner === lead.routing.owner;
          const saving = pending && savingOwner === owner;
          return (
            <button
              key={owner}
              disabled={current || pending}
              onClick={() => submit(owner)}
              className={cn(
                "rounded-lg border px-3 py-1.5 text-[11px] font-medium transition disabled:cursor-not-allowed disabled:opacity-55",
                current
                  ? "border-brand-orange bg-brand-orange/[0.08] text-brand-orange-600"
                  : "border-line bg-brand-cream-100 text-ink-muted hover:border-brand-orange hover:text-brand-orange-600 hover:bg-brand-orange/[0.05]",
              )}
            >
              {saving ? `Saving "${owner}"…` : `Re-route to ${owner}`}
            </button>
          );
        })}
      </div>

      {overrides.map((o) => (
        <div
          key={o.id}
          className="mt-2 rounded-lg border border-brand-orange/30 bg-brand-orange/[0.07] px-3 py-2 text-[11px] text-brand-orange-600"
        >
          <span className="inline-flex flex-wrap items-center gap-x-1 gap-y-0.5">
            <span>{o.original_owner}</span>
            <ArrowRight className="inline h-3 w-3 shrink-0 opacity-80" strokeWidth={2} aria-hidden />
            <span>{o.corrected_owner}</span>
            <span className="text-line" aria-hidden>
              ·
            </span>
            <span>{formatDateTime(o.created_at)}</span>
            {o.reason ? (
              <>
                <span className="text-line" aria-hidden>
                  ·
                </span>
                <span>{o.reason}</span>
              </>
            ) : null}
          </span>
        </div>
      ))}

      {error && (
        <div className="mt-2 rounded-lg border border-danger/40 bg-danger/10 px-3 py-2 text-xs text-[color:var(--color-danger)]">
          Failed to record override: {error}
        </div>
      )}
    </div>
  );
}
