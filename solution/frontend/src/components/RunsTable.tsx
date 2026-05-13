"use client";

import Link from "next/link";
import type { Route } from "next";
import { useCallback, useMemo } from "react";
import {
  InfiniteScrollTable,
  type InfiniteTableColumn,
} from "@/components/ui/InfiniteScrollTable";
import { ShortIdWithTooltip } from "@/components/ui/ShortIdWithTooltip";
import { listRunsPage } from "@/lib/api";
import { formatDateTime } from "@/lib/format";
import type { RunListItem } from "@/lib/types";

const PAGE_SIZE = 30;

export function RunsTable() {
  const fetchPage = useCallback(async (offset: number, limit: number) => {
    const { runs, hasMore } = await listRunsPage(offset, limit);
    return { rows: runs, hasMore };
  }, []);

  const getRowKey = useCallback((r: RunListItem) => r.run_id, []);
  const columns = useMemo<InfiniteTableColumn<RunListItem>[]>(
    () => [
      {
        id: "run_id",
        header: "Run id",
        cell: (r) => (
          <Link
            href={`/runs/${r.run_id}` as Route}
            className="block max-w-[6.5rem] min-w-0 sm:max-w-[9rem] font-mono text-[12px] text-brand-orange-600 hover:underline"
          >
            <ShortIdWithTooltip
              id={r.run_id}
              length={12}
              wrapperClassName="max-w-full"
              className="text-[12px] text-brand-orange-600"
            />
          </Link>
        ),
      },
      {
        id: "received_at",
        header: "Received at",
        cellClassName: "text-ink-muted",
        cell: (r) => formatDateTime(r.received_at),
      },
      {
        id: "received",
        header: "Leads",
        align: "right",
        cell: (r) => r.received,
      },
      {
        id: "processed",
        header: "Processed",
        align: "right",
        cell: (r) => r.processed,
      },
      {
        id: "elapsed_ms",
        header: "Latency",
        align: "right",
        cell: (r) => `${r.elapsed_ms} ms`,
      },
      {
        id: "owners",
        header: "Owners",
        cellClassName: "text-xs font-medium text-ink-muted",
        truncate: true,
        cellMaxWidthClass: "max-w-[10rem] md:max-w-[16rem] lg:max-w-[20rem]",
        tooltipPanelClassName: "whitespace-pre-line",
        tooltip: (r) =>
          Object.entries(r.by_owner)
            .map(([k, v]) => `${k}: ${v}`)
            .join("\n"),
        cell: (r) =>
          Object.entries(r.by_owner)
            .map(([k, v]) => `${k}: ${v}`)
            .join(" · "),
      },
    ],
    [],
  );

  return (
    <InfiniteScrollTable<RunListItem>
      columns={columns}
      pageSize={PAGE_SIZE}
      fetchPage={fetchPage}
      getRowKey={getRowKey}
      refreshAriaLabel="Refresh run list"
      footerCountLabels={{ singular: "run", plural: "runs" }}
      emptyMessage={
        <p className="px-4 py-8 text-center text-sm text-ink-subtle">No runs persisted yet.</p>
      }
    />
  );
}
