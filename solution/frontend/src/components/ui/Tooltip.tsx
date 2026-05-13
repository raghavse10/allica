"use client";

import { cn } from "@/lib/cn";
import { createPortal } from "react-dom";
import {
  useCallback,
  useEffect,
  useId,
  useLayoutEffect,
  useRef,
  useState,
} from "react";
import type { ReactNode } from "react";

export interface TooltipProps {
  children: ReactNode;
  /** Shown in the floating panel; null/undefined/empty string → no tooltip, children only. */
  content: ReactNode;
  delayShow?: number;
  /** Extra classes on the trigger wrapper (width constraints often go here). */
  className?: string;
  /** Classes merged onto the portaled tooltip panel (e.g. `whitespace-pre-line`). */
  panelClassName?: string;
}

/**
 * Branded hover/focus tooltip portaled to `document.body` with `position: fixed`
 * so it is not clipped by `overflow-x-auto` table shells.
 */
export function Tooltip({ children, content, delayShow = 180, className, panelClassName }: TooltipProps) {
  const [open, setOpen] = useState(false);
  const [mounted, setMounted] = useState(false);
  const triggerRef = useRef<HTMLSpanElement>(null);
  const tipRef = useRef<HTMLDivElement>(null);
  const ttId = useId();
  const showTimer = useRef<ReturnType<typeof setTimeout> | null>(null);
  const [pos, setPos] = useState({ top: 0, left: 0 });

  const hide = useCallback(() => {
    if (showTimer.current) {
      clearTimeout(showTimer.current);
      showTimer.current = null;
    }
    setOpen(false);
  }, []);

  const updatePosition = useCallback(() => {
    const t = triggerRef.current;
    const tip = tipRef.current;
    if (!t) return;
    const r = t.getBoundingClientRect();
    const gap = 8;
    const th = tip?.offsetHeight ?? 40;
    let top = r.top - th - gap;
    if (top < 8) top = r.bottom + gap;
    setPos({ top, left: r.left + r.width / 2 });
  }, []);

  useEffect(() => {
    setMounted(true);
  }, []);

  useLayoutEffect(() => {
    if (!open || !mounted) return;
    updatePosition();
    const id = requestAnimationFrame(() => updatePosition());
    const t = triggerRef.current;
    const tip = tipRef.current;
    const ro = new ResizeObserver(() => updatePosition());
    if (t) ro.observe(t);
    if (tip) ro.observe(tip);
    window.addEventListener("scroll", updatePosition, true);
    window.addEventListener("resize", updatePosition);
    return () => {
      cancelAnimationFrame(id);
      ro.disconnect();
      window.removeEventListener("scroll", updatePosition, true);
      window.removeEventListener("resize", updatePosition);
    };
  }, [open, mounted, updatePosition, content]);

  useEffect(() => {
    if (!open) return;
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") hide();
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [open, hide]);

  const show = useCallback(() => {
    if (showTimer.current) clearTimeout(showTimer.current);
    showTimer.current = setTimeout(() => {
      showTimer.current = null;
      setOpen(true);
    }, delayShow);
  }, [delayShow]);

  if (content === false) return <>{children}</>;
  if (content == null) return <>{children}</>;
  if (typeof content === "string" && content.length === 0) return <>{children}</>;

  const panel =
    open &&
    mounted &&
    createPortal(
      <div
        ref={tipRef}
        id={ttId}
        role="tooltip"
        style={{
          position: "fixed",
          top: pos.top,
          left: pos.left,
          transform: "translateX(-50%)",
        }}
        className={cn(
          "pointer-events-none z-[200] max-w-[min(22rem,calc(100vw-1.5rem))] rounded-lg border border-brand-navy/20",
          "bg-brand-navy-900 px-2.5 py-1.5 text-left text-[12px] font-medium leading-snug text-brand-cream-100 shadow-xl",
          panelClassName,
        )}
      >
        {content}
      </div>,
      document.body,
    );

  return (
    <>
      <span
        ref={triggerRef}
        className={cn("inline-flex min-w-0 max-w-full align-middle", className)}
        onMouseEnter={show}
        onMouseLeave={hide}
        onFocus={show}
        onBlur={(e) => {
          const rt = e.relatedTarget as Node | null;
          if (rt && triggerRef.current?.contains(rt)) return;
          hide();
        }}
        aria-describedby={open ? ttId : undefined}
      >
        {children}
      </span>
      {panel}
    </>
  );
}
