"use client";

import { Mail, MailX } from "lucide-react";
import { cn } from "@/lib/cn";
import { BandPill, BlockPill, FlagPill, OwnerPill } from "@/components/ui/Pill";
import { ScoreCircle } from "@/components/ui/ScoreCircle";
import type { LeadResult } from "@/lib/types";

interface LeadCardProps {
  lead: LeadResult;
  onClick?: () => void;
}

export function LeadCard({ lead, onClick }: LeadCardProps) {
  const owner = lead.routing.owner;
  return (
    <article
      onClick={onClick}
      className={cn(
        "grid cursor-pointer grid-cols-[minmax(0,1fr)_110px] gap-4 rounded-[var(--radius-card)] border border-line border-l-4 border-l-line bg-surface-raised p-4 transition hover:-translate-y-px hover:border-brand-orange hover:border-l-brand-orange hover:shadow-[0_6px_24px_-12px_rgba(0,32,78,0.25)]",
        lead.validation.is_duplicate && "border-dashed opacity-70",
      )}
    >
      <div>
        <div className="flex flex-wrap items-center gap-2">
          <span className="rounded bg-brand-cream-300 px-1.5 py-0.5 font-mono text-[11px] text-ink-subtle">
            {lead.id ?? "—"}
          </span>
          <span className="text-[15px] font-semibold text-brand-navy-900">
            {lead.company_name ?? "Unknown company"}
          </span>
          <BandPill band={lead.score.band} />
          {owner === "Decline" && <BlockPill />}
        </div>

        <div className="mt-1.5 flex flex-wrap items-center gap-1.5 text-xs text-ink-muted">
          <OwnerPill owner={owner} queue={lead.routing.queue} />
          <span className="text-line">·</span>
          <span>{lead.enrichment.derived_sector ?? "sector unknown"}</span>
          {lead.enrichment.matched ? (
            <>
              <span className="text-line">·</span>
              <span>CH {lead.enrichment.company_number}</span>
            </>
          ) : (
            <>
              <span className="text-line">·</span>
              <span className="text-brand-orange-600">no CH match</span>
            </>
          )}
          {lead.validation.is_duplicate && (
            <>
              <span className="text-line">|</span>
              <span>
                duplicate of <span className="text-ink">{lead.validation.duplicate_of ?? "?"}</span>
              </span>
            </>
          )}
        </div>

        <p className="mt-2 text-[13px] leading-relaxed text-ink">{lead.routing.rationale}</p>

        {lead.safety_flags.length > 0 && (
          <div className="mt-2.5 flex flex-wrap gap-1.5">
            {lead.safety_flags.slice(0, 4).map((f, i) => (
              <FlagPill key={`${f.code}-${i}`} severity={f.severity}>
                {f.code}
              </FlagPill>
            ))}
          </div>
        )}
      </div>

      <div className="flex flex-col items-center justify-center gap-2">
        <ScoreCircle value={lead.score.value} />
        {lead.email ? (
          <div className="flex items-center gap-1 text-center text-[11px] text-ink-subtle">
            <Mail className="h-3.5 w-3.5 shrink-0 text-ink-muted" strokeWidth={2} aria-hidden />
            <span>Drafted</span>
          </div>
        ) : (
          <div className="flex items-center gap-1 text-center text-[11px] text-ink-subtle">
            <MailX className="h-3.5 w-3.5 shrink-0 text-ink-muted" strokeWidth={2} aria-hidden />
            <span>No email</span>
          </div>
        )}
      </div>
    </article>
  );
}
