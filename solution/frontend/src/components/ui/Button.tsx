"use client";

import { cn } from "@/lib/cn";
import type { ButtonHTMLAttributes, ReactNode } from "react";

type Variant = "primary" | "ghost" | "subtle";
type Size = "sm" | "md";

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: Variant;
  size?: Size;
  block?: boolean;
  children: ReactNode;
}

const base =
  "cursor-pointer inline-flex items-center justify-center gap-1.5 rounded-[10px] font-semibold transition active:translate-y-px disabled:opacity-55 disabled:cursor-not-allowed";

const variants: Record<Variant, string> = {
  primary:
    "bg-brand-orange text-white shadow-[0_1px_0_rgba(204,66,1,0.4),0_6px_16px_-8px_rgba(255,82,0,0.55)] hover:bg-brand-orange-600 disabled:shadow-none border border-transparent",
  ghost:
    "bg-brand-cream-100 text-ink-muted border border-line hover:border-brand-orange hover:text-brand-orange-600",
  subtle:
    "bg-transparent text-ink-muted hover:text-brand-orange-600 border border-transparent",
};

const sizes: Record<Size, string> = {
  sm: "px-3 py-1.5 text-xs",
  md: "px-3.5 py-2.5 text-[13px]",
};

export function Button({
  variant = "primary",
  size = "md",
  block,
  className,
  children,
  ...rest
}: ButtonProps) {
  return (
    <button
      className={cn(base, variants[variant], sizes[size], block && "w-full", className)}
      {...rest}
    >
      {children}
    </button>
  );
}
