"use client";

import { Check, ChevronDown, ChevronUp } from "lucide-react";
import { useEffect, useId, useMemo, useRef, useState } from "react";
import { cn } from "@/lib/cn";

export interface MultiSelectOption {
  value: string;
  label: string;
}

interface SearchableMultiSelectProps {
  options: MultiSelectOption[];
  value: string[];
  onChange: (next: string[]) => void;
  placeholder: string;
  /** Shown in the trigger when nothing is selected (e.g. "All owners") */
  emptySummary?: string;
  ariaLabel: string;
  className?: string;
  /** When search has no matches */
  noResultsText?: string;
}

function summaryLabel(
  selected: string[],
  optionMap: Map<string, string>,
  emptySummary: string,
): string {
  if (selected.length === 0) return emptySummary;
  if (selected.length === 1) return optionMap.get(selected[0]) ?? selected[0];
  const [a, b, ...rest] = selected;
  const la = optionMap.get(a) ?? a;
  if (selected.length === 2) {
    const lb = optionMap.get(b!) ?? b!;
    return `${la}, ${lb}`;
  }
  const lb = optionMap.get(b!) ?? b!;
  return `${la}, ${lb} +${rest.length}`;
}

export function SearchableMultiSelect({
  options,
  value,
  onChange,
  placeholder,
  emptySummary = "Any",
  ariaLabel,
  className,
  noResultsText = "No matches",
}: SearchableMultiSelectProps) {
  const listId = useId();
  const searchId = useId();
  const rootRef = useRef<HTMLDivElement>(null);
  const searchInputRef = useRef<HTMLInputElement>(null);
  const [open, setOpen] = useState(false);
  const [query, setQuery] = useState("");

  const optionMap = useMemo(() => new Map(options.map((o) => [o.value, o.label])), [options]);

  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase();
    if (!q) return options;
    return options.filter(
      (o) => o.label.toLowerCase().includes(q) || o.value.toLowerCase().includes(q),
    );
  }, [options, query]);

  useEffect(() => {
    if (!open) return;
    function onDocMouseDown(e: MouseEvent) {
      const el = rootRef.current;
      if (!el || !(e.target instanceof Node) || el.contains(e.target)) return;
      setOpen(false);
    }
    document.addEventListener("mousedown", onDocMouseDown);
    return () => document.removeEventListener("mousedown", onDocMouseDown);
  }, [open]);

  useEffect(() => {
    if (!open) return;
    function onKey(e: KeyboardEvent) {
      if (e.key === "Escape") {
        e.stopPropagation();
        setOpen(false);
      }
    }
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [open]);

  useEffect(() => {
    if (open) {
      setQuery("");
      queueMicrotask(() => searchInputRef.current?.focus());
    }
  }, [open]);

  function toggle(v: string) {
    if (value.includes(v)) onChange(value.filter((x) => x !== v));
    else onChange([...value, v]);
  }

  const triggerText = summaryLabel(value, optionMap, emptySummary);

  return (
    <div ref={rootRef} className={cn("relative", className)}>
      <button
        type="button"
        aria-expanded={open}
        aria-haspopup="listbox"
        aria-controls={open ? listId : undefined}
        aria-label={ariaLabel}
        onClick={() => setOpen((o) => !o)}
        className={cn(
          "flex w-full min-w-[10rem] items-center justify-between gap-2 rounded-lg border border-line bg-brand-cream-100 px-3 py-2 text-left text-[13px] text-ink transition",
          "hover:border-brand-orange/40 focus:border-brand-orange focus:outline-none focus:ring-[3px] focus:ring-[rgba(255,82,0,0.15)]",
        )}
      >
        <span className="min-w-0 truncate font-medium">{triggerText}</span>
        <span className="shrink-0 text-ink-subtle" aria-hidden>
          {open ? (
            <ChevronUp className="h-4 w-4" strokeWidth={2} />
          ) : (
            <ChevronDown className="h-4 w-4" strokeWidth={2} />
          )}
        </span>
      </button>

      {open && (
        <div
          id={listId}
          role="listbox"
          aria-multiselectable="true"
          className="absolute left-0 right-0 z-50 mt-1 overflow-hidden rounded-lg border border-line bg-brand-cream-100 py-1 shadow-lg ring-1 ring-black/5"
        >
          <div className="border-b border-line px-2 pb-2 pt-1">
            <label htmlFor={searchId} className="sr-only">
              Filter {placeholder.toLowerCase()}
            </label>
            <input
              ref={searchInputRef}
              id={searchId}
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder={placeholder}
              className="w-full rounded-md border border-line bg-surface px-2.5 py-1.5 text-[13px] text-ink placeholder:text-ink-subtle focus:border-brand-orange focus:outline-none focus:ring-[3px] focus:ring-[rgba(255,82,0,0.12)]"
              onKeyDown={(e) => e.stopPropagation()}
            />
          </div>

          <div className="brand-scroll max-h-52 overflow-y-auto py-1">
            {filtered.length === 0 ? (
              <p className="px-3 py-2 text-center text-[13px] text-ink-muted">{noResultsText}</p>
            ) : (
              filtered.map((opt) => {
                const checked = value.includes(opt.value);
                return (
                  <button
                    key={opt.value}
                    type="button"
                    role="option"
                    aria-selected={checked}
                    onClick={() => toggle(opt.value)}
                    className={cn(
                      "flex w-full items-center gap-2 px-3 py-1.5 text-left text-[13px] transition",
                      checked
                        ? "bg-brand-orange/10 text-brand-navy-900"
                        : "text-ink hover:bg-brand-cream-200",
                    )}
                  >
                    <span
                      className={cn(
                        "grid h-4 w-4 shrink-0 place-items-center rounded border",
                        checked
                          ? "border-brand-orange bg-brand-orange text-white"
                          : "border-line bg-surface text-transparent",
                      )}
                      aria-hidden
                    >
                      {checked && <Check className="h-2.5 w-2.5" strokeWidth={3} />}
                    </span>
                    <span className="min-w-0 truncate">{opt.label}</span>
                  </button>
                );
              })
            )}
          </div>

          {value.length > 0 && (
            <div className="border-t border-line px-2 py-1.5">
              <button
                type="button"
                onClick={() => onChange([])}
                className="w-full rounded-md py-1 text-center text-[12px] font-medium text-ink-muted transition hover:bg-brand-cream-200 hover:text-brand-orange-600"
              >
                Clear selection
              </button>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
