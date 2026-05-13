import Link from "next/link";
import type { Route } from "next";
import { Card, CardTitle } from "@/components/ui/Card";
import { ShortIdWithTooltip } from "@/components/ui/ShortIdWithTooltip";
import { cn } from "@/lib/cn";
import { listRuns } from "@/lib/api";
import { formatRecentTime } from "@/lib/format";

/**
 * Server component — fetches recent runs at request time. Clicking a run
 * navigates to /runs/[id] which is also server-rendered.
 */
export async function RecentRuns({ activeRunId }: { activeRunId?: string }) {
  let runs;
  try {
    runs = await listRuns(20);
  } catch (e) {
    return (
      <Card padding="sm">
        <CardTitle>Recent runs</CardTitle>
        <p className="mt-2 text-xs text-ink-subtle">
          Failed to load: {e instanceof Error ? e.message : String(e)}
        </p>
      </Card>
    );
  }

  return (
    <Card padding="sm">
      <CardTitle>Recent runs</CardTitle>
      <p className="text-xs text-ink-muted">Persisted in the database.</p>

      {runs.length === 0 ? (
        <p className="mt-3 text-xs text-ink-subtle">
          No runs yet. Click &ldquo;Run on sample data&rdquo;.
        </p>
      ) : (
        <ul className="brand-scroll mt-3 max-h-60 space-y-2 overflow-y-auto pr-0.5">
          {runs.map((r) => {
            const active = r.run_id === activeRunId;
            return (
              <li key={r.run_id}>
                <Link
                  href={`/runs/${r.run_id}` as Route}
                  className={cn(
                    "block rounded-lg border px-3 py-2.5 text-start shadow-sm transition",
                    active
                      ? "border-brand-orange bg-brand-orange/[0.07] shadow-[inset_0_0_0_1px_rgba(255,82,0,0.35)]"
                      : "border-line bg-brand-cream-100 hover:border-brand-orange/45 hover:bg-brand-cream-200/60",
                  )}
                >
                  <div className="flex items-baseline justify-between gap-2">
                    <ShortIdWithTooltip
                      id={r.run_id}
                      wrapperClassName="min-w-0 flex-1"
                      className="font-mono text-xs font-semibold tracking-tight text-brand-navy-900"
                    />
                    <time
                      dateTime={r.received_at}
                      className="shrink-0 text-right text-xs font-medium tabular-nums text-ink-subtle"
                    >
                      {formatRecentTime(r.received_at)}
                    </time>
                  </div>
                  <p className="mt-1.5 text-xs leading-snug text-ink-muted tabular-nums">
                    <span className="font-semibold text-ink">{r.received}</span>
                    <span className="font-normal text-ink-subtle"> leads</span>
                    <span className="mx-1.5 text-line" aria-hidden>
                      ·
                    </span>
                    <span className="font-semibold text-ink">{r.processed}</span>
                    <span className="font-normal text-ink-subtle"> done</span>
                    <span className="mx-1.5 text-line" aria-hidden>
                      ·
                    </span>
                    <span className="font-semibold text-ink">{r.elapsed_ms}</span>
                    <span className="font-normal text-ink-subtle"> ms</span>
                  </p>
                </Link>
              </li>
            );
          })}
        </ul>
      )}
    </Card>
  );
}
