import { cn } from "@/lib/cn";
import type { HTMLAttributes, ReactNode } from "react";

export type CardPadding = "default" | "sm" | "compact";

const paddingClass: Record<CardPadding, string> = {
  default: "p-5",
  sm: "p-4",
  compact: "p-3",
};

interface CardProps extends HTMLAttributes<HTMLElement> {
  as?: "section" | "article" | "div";
  /** Inner padding; use `sm` / `compact` for sidebar and dense panels. */
  padding?: CardPadding;
  children: ReactNode;
}

export function Card({
  as: Tag = "section",
  padding = "default",
  className,
  children,
  ...rest
}: CardProps) {
  return (
    <Tag
      className={cn(
        "rounded-[var(--radius-card)] border border-line bg-surface-raised shadow-[0_1px_0_rgba(0,32,78,0.03),0_4px_16px_-10px_rgba(0,32,78,0.18)]",
        paddingClass[padding],
        className,
      )}
      {...rest}
    >
      {children}
    </Tag>
  );
}

export function CardTitle({ children, className }: { children: ReactNode; className?: string }) {
  return (
    <h2
      className={cn(
        "m-0 text-sm font-bold uppercase text-ink-muted",
        className,
      )}
    >
      {children}
    </h2>
  );
}
