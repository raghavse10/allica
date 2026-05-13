import { Check, X } from "lucide-react";
import { cn } from "@/lib/cn";

/** Tick when `ok` is true, cross when false — use for booleans shown in summaries. */
export function BoolIcon({
  ok,
  className,
  "aria-label": ariaLabel,
}: {
  ok: boolean;
  className?: string;
  "aria-label"?: string;
}) {
  const Icon = ok ? Check : X;
  return (
    <span
      className="inline-flex items-center justify-center"
      role="img"
      aria-label={ariaLabel ?? (ok ? "Yes" : "No")}
    >
      <Icon
        className={cn(
          "h-4 w-4 shrink-0",
          ok ? "text-emerald-700" : "text-[color:var(--color-danger)]",
          className,
        )}
        strokeWidth={2.5}
        aria-hidden
      />
    </span>
  );
}
