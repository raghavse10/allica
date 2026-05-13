"use client";

import { X } from "lucide-react";
import { useEffect } from "react";
import type { ReactNode } from "react";
import { cn } from "@/lib/cn";

interface ModalProps {
  open: boolean;
  onClose: () => void;
  children: ReactNode;
  /** Used when `ariaLabelledBy` is not set. */
  ariaLabel?: string;
  /** Id of the visible dialog title element (preferred over `ariaLabel`). */
  ariaLabelledBy?: string;
  /** Sticky top area next to the close control (e.g. dialog title + summary). */
  header?: ReactNode;
}

export function Modal({ open, onClose, children, ariaLabel, ariaLabelledBy, header }: ModalProps) {
  useEffect(() => {
    if (!open) return;
    function onKey(e: KeyboardEvent) {
      if (e.key === "Escape") onClose();
    }
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [open, onClose]);

  if (!open) return null;

  return (
    <div
      role="dialog"
      aria-modal="true"
      aria-labelledby={ariaLabelledBy}
      aria-label={ariaLabelledBy ? undefined : ariaLabel}
      onClick={(e) => {
        if (e.target === e.currentTarget) onClose();
      }}
      className="fixed inset-0 z-40 grid place-items-center bg-brand-navy-900/40 px-4 py-8 backdrop-blur-sm"
    >
      <div className="flex min-h-0 max-h-[90vh] w-full max-w-[860px] flex-col overflow-hidden rounded-2xl border border-line bg-surface-raised shadow-2xl">
        <header
          className={cn(
            "flex shrink-0 items-start gap-3 border-b border-line bg-surface-raised px-5 py-4",
            !header && "justify-end",
          )}
        >
          {header ? <div className="min-w-0 flex-1">{header}</div> : null}
          <button
            type="button"
            onClick={onClose}
            aria-label="Close dialog"
            className="grid h-8 w-8 shrink-0 place-items-center rounded-full text-ink-muted transition hover:bg-brand-cream-300 hover:text-brand-navy"
          >
            <X className="h-5 w-5" strokeWidth={2} />
          </button>
        </header>
        <div className="brand-scroll min-h-0 flex-1 overflow-y-auto px-5 pb-7 pt-4">{children}</div>
      </div>
    </div>
  );
}
