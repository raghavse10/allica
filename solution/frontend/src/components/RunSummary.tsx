import { Card, CardTitle } from "@/components/ui/Card";
import { CachedPill } from "@/components/ui/Pill";
import type { RunSummary as RunSummaryT } from "@/lib/types";
import type { ReactNode } from "react";

interface RunSummaryProps {
  summary: RunSummaryT;
  cached?: boolean;
}

export function RunSummary({ summary, cached }: RunSummaryProps) {
  return (
    <Card padding="sm">
      <CardTitle>Run summary</CardTitle>
      <div className="mt-4 grid grid-cols-2 gap-3">
        <Stat
          label="Received"
          labelEnd={cached ? <CachedPill /> : undefined}
          value={summary.received}
        />
        <Stat label="Processed" value={summary.processed} />
        <Stat label="Duplicates" value={summary.duplicates} />
        <Stat
          label="Latency"
          value={
            <>
              {summary.elapsed_ms}
              <span className="ml-0.5 text-[13px] font-medium text-ink-subtle">ms</span>
            </>
          }
        />
      </div>

      <div className="mt-4 space-y-1">
        <DistributionGroup label="By owner" entries={Object.entries(summary.by_owner)} />
        <DistributionGroup label="By ICP band" entries={Object.entries(summary.by_band)} />
      </div>
    </Card>
  );
}

function Stat({
  label,
  labelEnd,
  value,
}: {
  label: ReactNode;
  labelEnd?: ReactNode;
  value: ReactNode;
}) {
  return (
    <div className="rounded-[10px] border border-line bg-brand-cream-100 px-3.5 py-3">
      <div className="flex min-h-[22px] items-center justify-between gap-2 text-[11px] font-semibold uppercase tracking-[0.06em] text-ink-subtle">
        <span className="min-w-0 truncate">{label}</span>
        {labelEnd ? <span className="flex shrink-0 items-center">{labelEnd}</span> : null}
      </div>
      <div className="mt-1 text-2xl font-bold text-brand-navy-900 tabular-nums">{value}</div>
    </div>
  );
}

function DistributionGroup({
  label,
  entries,
}: {
  label: string;
  entries: [string, number][];
}) {
  if (!entries.length) return null;
  const max = Math.max(1, ...entries.map(([, v]) => v));
  return (
    <div>
      <div className="mb-1 mt-2.5 text-xs font-semibold uppercase tracking-[0.04em] text-ink-subtle">
        {label}
      </div>
      <div className="flex flex-col gap-[3px]">
        {entries.map(([k, v]) => (
          <div key={k} className="grid grid-cols-[110px_minmax(0,1fr)_28px] items-center gap-2.5 py-[3px] text-xs text-ink">
            <div className="truncate">{k}</div>
            <div className="h-1.5 overflow-hidden rounded-full bg-brand-cream-300">
              <span
                className="block h-full rounded-full"
                style={{
                  width: `${(v / max) * 100}%`,
                  background:
                    "linear-gradient(90deg, var(--color-brand-orange), var(--color-brand-orange-600))",
                }}
              />
            </div>
            <div className="text-right text-ink-muted font-semibold tabular-nums">{v}</div>
          </div>
        ))}
      </div>
    </div>
  );
}
