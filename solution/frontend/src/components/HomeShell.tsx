"use client";

import { useState } from "react";
import { LeadList } from "@/components/LeadList";
import { RunControls } from "@/components/RunControls";
import { RunSummary } from "@/components/RunSummary";
import type { RunResponse } from "@/lib/types";

interface HomeShellProps {
  recentRuns: React.ReactNode;
  legend: React.ReactNode;
}

/**
 * Holds the most recent RunResponse in client state and lets the sidebar
 * (`RunControls`) and the main pane (`RunSummary` + `LeadList`) talk to
 * each other. Server-rendered things (recent runs, legend) are passed in
 * as ReactNode so they keep their RSC benefits.
 */
export function HomeShell({ recentRuns, legend }: HomeShellProps) {
  const [response, setResponse] = useState<RunResponse | null>(null);

  return (
    <div className="grid gap-6 lg:grid-cols-[360px_minmax(0,1fr)]">
      <aside className="flex flex-col gap-5">
        <RunControls onResult={setResponse} />
        {response && (
          <RunSummary summary={response.summary} cached={!!response.meta.cached} />
        )}
        {recentRuns}
        {legend}
      </aside>

      <LeadList response={response} />
    </div>
  );
}
