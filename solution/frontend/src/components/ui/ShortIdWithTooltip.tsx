"use client";

import { cn } from "@/lib/cn";
import { shortId } from "@/lib/format";
import { Tooltip } from "@/components/ui/Tooltip";

export interface ShortIdWithTooltipProps {
  id: string;
  /** Passed through to {@link shortId}. */
  length?: number;
  /** Classes on the visible text span. */
  className?: string;
  /** Classes on the {@link Tooltip} trigger wrapper (`inline-flex` shell). */
  wrapperClassName?: string;
  panelClassName?: string;
}

/**
 * Renders a truncated id via {@link shortId}; when truncated, wraps in the
 * shared branded {@link Tooltip} with the full id.
 */
export function ShortIdWithTooltip({
  id,
  length = 8,
  className,
  wrapperClassName,
  panelClassName,
}: ShortIdWithTooltipProps) {
  const display = shortId(id, length);
  if (!id || display === id) {
    return <span className={className}>{display}</span>;
  }

  return (
    <Tooltip
      className={cn("min-w-0 max-w-full", wrapperClassName)}
      content={
        <span className="font-mono text-[11px] tracking-tight break-all">{id}</span>
      }
      panelClassName={panelClassName}
    >
      <span className={cn("block min-w-0 max-w-full truncate", className)}>{display}</span>
    </Tooltip>
  );
}
