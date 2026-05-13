"use client";

import { RefreshCw } from "lucide-react";
import { cn } from "@/lib/cn";
import { Button } from "@/components/ui/Button";
import { Tooltip } from "@/components/ui/Tooltip";
import { useCallback, useEffect, useRef, useState } from "react";
import type { ReactNode } from "react";

export interface InfiniteTableColumn<T> {
  id: string;
  header: string;
  headerClassName?: string;
  cellClassName?: string;
  align?: "left" | "right" | "center";
  cell: (row: T) => ReactNode;
  /** Wraps the cell in a `truncate` container (use with `tooltip` for full value on hover). */
  truncate?: boolean;
  /** Max-width on the truncate wrapper; defaults to `max-w-[12rem]`. */
  cellMaxWidthClass?: string;
  /** When the return value is non-empty, wraps the cell in {@link Tooltip}. */
  tooltip?: (row: T) => ReactNode | null | undefined | false;
  /** Extra classes on the tooltip panel (e.g. `whitespace-pre-line`). */
  tooltipPanelClassName?: string;
}

export interface InfiniteScrollTableProps<T> {
  columns: InfiniteTableColumn<T>[];
  pageSize?: number;
  fetchPage: (offset: number, limit: number) => Promise<{ rows: T[]; hasMore: boolean }>;
  getRowKey: (row: T) => string;
  emptyMessage?: ReactNode;
  className?: string;
  /** When false, hides the refresh control. Default true. */
  showRefresh?: boolean;
  /** Accessible name for the refresh action (e.g. "Refresh run list"). */
  refreshAriaLabel?: string;
  /** When false, hides the row-count footer. Default true. */
  showRowCountFooter?: boolean;
  /** Footer wording, e.g. `{ singular: "run", plural: "runs" }`. Default row / rows. */
  footerCountLabels?: { singular: string; plural: string };
}

const shell = "mt-4 overflow-x-auto rounded-xl border border-line";

function renderTableCell<T>(col: InfiniteTableColumn<T>, row: T): ReactNode {
  const inner = col.cell(row);
  const tipRaw = col.tooltip?.(row);
  const hasTip =
    tipRaw != null &&
    tipRaw !== false &&
    (typeof tipRaw !== "string" || tipRaw.length > 0);

  let body: ReactNode = inner;
  if (col.truncate) {
    body = (
      <span
        className={cn(
          "block min-w-0 truncate",
          col.cellMaxWidthClass ?? "max-w-[12rem]",
        )}
      >
        {inner}
      </span>
    );
  }
  if (hasTip) {
    return (
      <Tooltip content={tipRaw as ReactNode} panelClassName={col.tooltipPanelClassName}>
        {body}
      </Tooltip>
    );
  }
  return body;
}

/**
 * Generic `<table>` with window-level infinite scroll: loads the next page when
 * the bottom sentinel intersects the viewport.
 */
export function InfiniteScrollTable<T>({
  columns,
  pageSize = 30,
  fetchPage,
  getRowKey,
  emptyMessage,
  className,
  showRefresh = true,
  refreshAriaLabel = "Refresh",
  showRowCountFooter = true,
  footerCountLabels,
}: InfiniteScrollTableProps<T>) {
  const [rows, setRows] = useState<T[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [initialLoadDone, setInitialLoadDone] = useState(false);
  const [hasMore, setHasMore] = useState(true);
  const offsetRef = useRef(0);
  const hasMoreRef = useRef(true);
  const loadingRef = useRef(false);
  /** Bumps when inputs reset so in-flight responses from an older session are ignored. */
  const fetchGen = useRef(0);

  const loadMore = useCallback(async () => {
    if (loadingRef.current || !hasMoreRef.current) return;
    const callGen = fetchGen.current;
    loadingRef.current = true;
    setLoading(true);
    setError(null);
    try {
      const off = offsetRef.current;
      const { rows: batch, hasMore } = await fetchPage(off, pageSize);
      if (callGen !== fetchGen.current) return;
      offsetRef.current = off + batch.length;
      hasMoreRef.current = hasMore;
      setHasMore(hasMore);
      setRows((prev) => {
        if (off === 0) return batch;
        const seen = new Set(prev.map((r) => getRowKey(r)));
        const extra = batch.filter((r) => !seen.has(getRowKey(r)));
        return [...prev, ...extra];
      });
    } catch (e) {
      if (callGen === fetchGen.current) {
        setError(e instanceof Error ? e.message : "Failed to load");
      }
    } finally {
      loadingRef.current = false;
      setLoading(false);
      if (callGen === fetchGen.current) {
        setInitialLoadDone(true);
      }
    }
  }, [fetchPage, pageSize, getRowKey]);

  useEffect(() => {
    fetchGen.current += 1;
    loadingRef.current = false;
    offsetRef.current = 0;
    hasMoreRef.current = true;
    setHasMore(true);
    setRows([]);
    setInitialLoadDone(false);
    setError(null);
    void loadMore();
  }, [loadMore]);

  const sentinelRef = useRef<HTMLTableRowElement | null>(null);

  useEffect(() => {
    const el = sentinelRef.current;
    if (!el || !hasMoreRef.current || rows.length === 0) return;

    const obs = new IntersectionObserver(
      (entries) => {
        const hit = entries.some((e) => e.isIntersecting);
        if (hit) void loadMore();
      },
      { root: null, rootMargin: "240px 0px", threshold: 0 },
    );
    obs.observe(el);
    return () => obs.disconnect();
  }, [loadMore, rows.length, loading]);

  const showEmpty = initialLoadDone && !loading && rows.length === 0 && !error;
  const initialLoading = !initialLoadDone && rows.length === 0 && !error;

  const reloadFromStart = useCallback(() => {
    fetchGen.current += 1;
    loadingRef.current = false;
    offsetRef.current = 0;
    hasMoreRef.current = true;
    setHasMore(true);
    setRows([]);
    setError(null);
    setInitialLoadDone(false);
    void loadMore();
  }, [loadMore]);

  const countSingular = footerCountLabels?.singular ?? "row";
  const countPlural = footerCountLabels?.plural ?? "rows";

  const refreshToolbar =
    showRefresh ? (
      <div className="flex justify-end border-b border-line bg-brand-cream-100/60 px-2 py-1.5">
        <Button
          type="button"
          variant="ghost"
          size="sm"
          onClick={reloadFromStart}
          disabled={loading}
          aria-label={refreshAriaLabel}
        >
          <RefreshCw
            className={cn(
              "h-3.5 w-3.5 shrink-0",
              loading && rows.length === 0 && "animate-spin",
            )}
            aria-hidden
          />
          Refresh
        </Button>
      </div>
    ) : null;

  if (initialLoading) {
    return (
      <div className={cn(shell, className)}>
        {refreshToolbar}
        <div className="px-4 py-10 text-center text-sm text-ink-muted">Loading…</div>
      </div>
    );
  }

  if (showEmpty) {
    return (
      <div className={cn(shell, className)}>
        {refreshToolbar}
        {emptyMessage ?? (
          <p className="px-4 py-8 text-center text-sm text-ink-subtle">No rows yet.</p>
        )}
      </div>
    );
  }

  if (error && rows.length === 0) {
    return (
      <div className={cn(shell, className)}>
        {refreshToolbar}
        <div className="flex flex-wrap items-center justify-between gap-2 px-4 py-8 text-sm text-danger">
          <span>{error}</span>
          <button
            type="button"
            onClick={reloadFromStart}
            className="font-semibold text-brand-navy underline-offset-2 hover:underline"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className={cn(shell, className)}>
      {refreshToolbar}
      <table className="w-full text-sm">
        <thead className="bg-brand-cream-100 text-left text-[11px] uppercase tracking-wider text-ink-subtle">
          <tr>
            {columns.map((col) => (
              <th
                key={col.id}
                scope="col"
                className={cn(
                  "px-3 py-2.5 font-semibold",
                  col.align === "right" && "text-right",
                  col.align === "center" && "text-center",
                  col.headerClassName,
                )}
              >
                {col.header}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((row) => (
            <tr
              key={getRowKey(row)}
              className="border-t border-line transition hover:bg-brand-cream-100"
            >
              {columns.map((col) => (
                <td
                  key={col.id}
                  className={cn(
                    "px-3 py-2.5",
                    col.align === "right" && "text-right tabular-nums",
                    col.align === "center" && "text-center",
                    col.cellClassName,
                  )}
                >
                  {renderTableCell(col, row)}
                </td>
              ))}
            </tr>
          ))}
          <tr ref={sentinelRef} className="border-0">
            <td colSpan={columns.length} className="h-10 border-0 bg-transparent p-0" />
          </tr>
        </tbody>
      </table>

      {error && (
        <div className="flex flex-wrap items-center justify-between gap-2 border-t border-line bg-brand-cream-100/80 px-3 py-2 text-xs text-danger">
          <span>{error}</span>
          <button
            type="button"
            onClick={reloadFromStart}
            className="font-semibold text-brand-navy underline-offset-2 hover:underline"
          >
            Retry
          </button>
        </div>
      )}

      {loading && rows.length > 0 && (
        <div className="border-t border-line px-3 py-2 text-center text-xs text-ink-muted">
          Loading more…
        </div>
      )}

      {showRowCountFooter && rows.length > 0 && (
        <div
          className="border-t border-line bg-brand-cream-100/60 px-3 py-2 text-right text-xs text-ink-muted"
          aria-live="polite"
        >
          <span className="font-semibold tabular-nums text-ink">
            {rows.length.toLocaleString()}
          </span>{" "}
          {rows.length === 1 ? countSingular : countPlural}
          {hasMore ? " loaded · scroll for more" : " total"}
        </div>
      )}
    </div>
  );
}
