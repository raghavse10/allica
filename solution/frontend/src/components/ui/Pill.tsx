import { cn } from "@/lib/cn";
import type { ReactNode } from "react";
import type { ScoreBand, Severity } from "@/lib/types";

const baseChip =
  "inline-flex items-center rounded-full text-[10px] font-bold uppercase tracking-[0.06em] px-2 py-[3px] border";

export function BandPill({ band, className }: { band: ScoreBand; className?: string }) {
  const styles: Record<ScoreBand, string> = {
    high: "bg-brand-orange/12 text-brand-orange-600 border-brand-orange/35",
    medium: "bg-brand-navy/8 text-brand-navy border-brand-navy/25",
    low: "bg-ink-subtle/15 text-ink-muted border-ink-subtle/35",
  };
  return <span className={cn(baseChip, styles[band], className)}>{band}</span>;
}

export function BlockPill() {
  return (
    <span className={cn(baseChip, "bg-danger/10 text-[color:var(--color-danger)] border-danger/35")}>
      decline
    </span>
  );
}

export function CachedPill({ className }: { className?: string }) {
  return (
    <span
      title="This response was served from the database, not re-computed."
      className={cn(
        "inline-flex shrink-0 items-center rounded-full border border-brand-orange/35 bg-brand-orange/12 px-[7px] py-[2px] text-[9px] font-bold uppercase tracking-[0.08em] text-brand-orange-600",
        className,
      )}
    >
      cached
    </span>
  );
}

/** Companies House company status (active, dissolved, etc.). */
export function CompaniesHouseStatusPill({ status }: { status: string | null }) {
  const raw = status?.trim();
  if (!raw) {
    return (
      <span className={cn(baseChip, "bg-brand-cream-300 text-ink-muted border-line normal-case font-semibold")}>
        —
      </span>
    );
  }
  const key = raw.toLowerCase();
  let style =
    "bg-brand-navy/8 text-brand-navy border-brand-navy/25";
  if (key === "active") {
    style = "bg-emerald-600/10 text-emerald-800 border-emerald-700/25";
  } else if (
    key.includes("dissolv") ||
    key.includes("liquidat") ||
    key.includes("ceased") ||
    key === "converted-closed"
  ) {
    style = "bg-danger/10 text-[color:var(--color-danger)] border-danger/35";
  } else if (key.includes("proposal") || key.includes("administration") || key.includes("receivership")) {
    style = "bg-brand-orange/12 text-brand-orange-600 border-brand-orange/40";
  }

  return (
    <span className={cn(baseChip, style)} title={raw}>
      {raw}
    </span>
  );
}

export function OwnerPill({ owner, queue }: { owner: string; queue?: string }) {
  let style = "bg-brand-cream-300 text-ink border-line";
  if (owner === "Manual-Review") style = "bg-brand-navy/8 text-brand-navy border-brand-navy/25";
  else if (owner === "Decline") style = "bg-danger/10 text-[color:var(--color-danger)] border-danger/35";
  else if (queue === "priority")
    style = "bg-brand-orange/12 text-brand-orange-600 border-brand-orange/40";

  return (
    <span
      className={cn(
        "inline-flex items-center rounded-full border px-[9px] py-[3px] text-[11px] font-semibold",
        style,
      )}
    >
      {owner}
    </span>
  );
}

export function SeverityChip({ severity }: { severity: Severity }) {
  const map: Record<Severity, string> = {
    info: "bg-brand-navy/8 text-brand-navy",
    warning: "bg-brand-orange/12 text-brand-orange-600",
    block: "bg-danger/10 text-[color:var(--color-danger)]",
  };
  return (
    <span className={cn("inline-block rounded-full px-2 py-[3px] text-[10px] font-bold uppercase tracking-[0.06em] text-center", map[severity])}>
      {severity}
    </span>
  );
}

export function FlagPill({ severity, children }: { severity: Severity; children: ReactNode }) {
  const map: Record<Severity, string> = {
    info: "bg-brand-navy/8 text-brand-navy border-brand-navy/25",
    warning: "bg-brand-orange/12 text-brand-orange-600 border-brand-orange/35",
    block: "bg-danger/10 text-[color:var(--color-danger)] border-danger/40",
  };
  return (
    <span
      className={cn(
        "inline-flex items-center rounded-full border px-[7px] py-[2px] font-mono text-[10px] font-semibold",
        map[severity],
      )}
    >
      {children}
    </span>
  );
}
