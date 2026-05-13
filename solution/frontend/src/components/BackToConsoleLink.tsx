"use client";

import { ArrowLeft } from "lucide-react";
import Link from "next/link";

export function BackToConsoleLink() {
  return (
    <Link
      href="/"
      className="mt-4 inline-flex w-full items-center justify-center gap-2 rounded-lg border border-line bg-brand-cream-100 px-3 py-2 text-center text-xs text-ink-muted transition hover:border-brand-orange hover:text-brand-orange-600"
    >
      <ArrowLeft className="h-3.5 w-3.5 shrink-0" strokeWidth={2} aria-hidden />
      Back to console
    </Link>
  );
}
