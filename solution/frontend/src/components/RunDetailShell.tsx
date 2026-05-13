"use client";

import { useMemo } from "react";
import { LeadList } from "@/components/LeadList";
import { RunSummary } from "@/components/RunSummary";
import type { RunDetail, RunResponse } from "@/lib/types";

/**
 * Adapts a RunDetail (storage view) into the RunResponse shape the rest of
 * the UI already understands, then delegates to the same LeadList /
 * RunSummary components used on the home page.
 */
export function RunDetailShell({ detail }: { detail: RunDetail }) {
  const response = useMemo<RunResponse>(() => {
    return {
      summary: {
        received: detail.received,
        processed: detail.processed,
        dropped: detail.received - detail.processed,
        duplicates: detail.duplicates,
        by_owner: detail.by_owner,
        by_band: detail.by_band,
        elapsed_ms: detail.elapsed_ms,
      },
      leads: detail.leads,
      meta: { run_id: detail.run_id, cached: true },
    };
  }, [detail]);

  return (
    <div className="flex min-w-0 flex-col gap-5">
      <RunSummary summary={response.summary} cached />
      <LeadList response={response} />
    </div>
  );
}
