import { notFound } from "next/navigation";
import { BackToConsoleLink } from "@/components/BackToConsoleLink";
import { Card, CardTitle } from "@/components/ui/Card";
import { Legend } from "@/components/Legend";
import { RecentRuns } from "@/components/RecentRuns";
import { RunDetailShell } from "@/components/RunDetailShell";
import { ApiError, getRun } from "@/lib/api";
import { formatDateTime } from "@/lib/format";
import { BoolIcon } from "@/components/ui/BoolIcon";
import { ShortIdWithTooltip } from "@/components/ui/ShortIdWithTooltip";
import type { ReactNode } from "react";

export const dynamic = "force-dynamic";

interface PageProps {
  params: Promise<{ id: string }>;
}

export default async function RunDetailPage({ params }: PageProps) {
  const { id } = await params;

  let detail;
  try {
    detail = await getRun(id);
  } catch (e) {
    if (e instanceof ApiError && e.status === 404) notFound();
    throw e;
  }

  return (
    <div className="grid gap-6 lg:grid-cols-[360px_minmax(0,1fr)]">
      <aside className="flex flex-col gap-5">
        <Card>
          <CardTitle>Run</CardTitle>
          <div className="mt-3 space-y-2 text-xs">
            <KV
              label="ID"
              value={
                <ShortIdWithTooltip
                  id={detail.run_id}
                  length={16}
                  wrapperClassName="justify-end"
                  className="text-right font-mono text-xs text-ink"
                />
              }
            />
            <KV label="Received" value={formatDateTime(detail.received_at)} />
            <KV label="Completed" value={formatDateTime(detail.completed_at)} />
            <KV label="Latency" value={`${detail.elapsed_ms} ms`} />
            <KV
              label="LLM preferred"
              value={
                <BoolIcon
                  ok={detail.llm_preferred}
                  aria-label={detail.llm_preferred ? "LLM was preferred" : "LLM was not preferred"}
                />
              }
            />
          </div>
          <BackToConsoleLink />
        </Card>
        <RecentRuns activeRunId={detail.run_id} />
        <Legend />
      </aside>

      <RunDetailShell detail={detail} />
    </div>
  );
}

function KV({ label, value }: { label: string; value: ReactNode }) {
  return (
    <div className="flex items-center justify-between gap-2">
      <span className="shrink-0 text-ink-subtle">{label}</span>
      <span className="min-w-0 text-right text-ink">{value}</span>
    </div>
  );
}
