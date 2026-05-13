"use client";

import { ExternalLink } from "lucide-react";
import type { Route } from "next";
import Image from "next/image";
import Link from "next/link";
import { usePathname } from "next/navigation";
import type { ReactNode } from "react";
import { cn } from "@/lib/cn";

function NavLink({
  href,
  children,
  className,
}: {
  href: Route;
  children: ReactNode;
  className?: string;
}) {
  const pathname = usePathname();
  const active =
    href === "/"
      ? pathname === "/"
      : pathname === href || pathname.startsWith(`${href}/`);

  return (
    <Link
      href={href}
      className={cn(
        "inline-flex items-center gap-1 rounded-lg px-2.5 py-2 text-[15px] font-medium leading-none tracking-tight transition-colors sm:gap-1.5 sm:px-3",
        active ? "text-brand-orange" : "text-brand-navy hover:text-brand-navy-900",
        className,
      )}
    >
      {children}
    </Link>
  );
}

/**
 * Site chrome — uses palette from `@theme` in globals.css:
 * Navy links `#00204e` (text-brand-navy), strong navy `#000f27`, accent `#ff5200`.
 * Nav: medium (500) sans ~15px, chevron matches label; active label + chevron orange.
 * CTA: `bg-brand-navy` (former hover tone), darker on hover.
 */
export function Navbar() {
  return (
    <header className="sticky top-0 z-30 border-b border-line bg-brand-cream-200/95 backdrop-blur">
      <div className="mx-auto flex max-w-[1400px] flex-wrap items-center justify-between gap-x-6 gap-y-3 px-6 py-3.5">
        <Link href="/" className="flex min-w-0 shrink-0 items-center gap-3">
          {/* Explicit box matches 1000:135 so `fill` + `object-contain` actually scales (Next Image ignores h/w utilities on the img). */}
          <span className="relative inline-block h-3 w-[calc(0.75rem_*_1000_/135)] shrink-0 sm:h-4 sm:w-[calc(1rem_*_1000_/135)]">
            <Image
              src="/logo-name-blue.png"
              alt="Allica"
              fill
              sizes="(max-width: 640px) 90px, 120px"
              className="object-contain object-left"
              priority
            />
          </span>
          <span className="hidden min-w-0 text-[11px] font-medium leading-snug text-ink-muted sm:block">
            Inbound triage, scoring &amp; first-touch drafting
          </span>
        </Link>

        <nav
          className="order-3 flex w-full flex-none items-center justify-center gap-4 sm:order-none sm:flex-1 sm:gap-7 lg:justify-center lg:gap-10"
          aria-label="Primary"
        >
          <NavLink href="/">Home</NavLink>
          <NavLink href="/runs">Runs</NavLink>
        </nav>

        <div className="ml-auto flex shrink-0 items-center sm:ml-0">
          <a
            href="/api/docs"
            target="_blank"
            rel="noreferrer"
            className="inline-flex items-center gap-1.5 rounded-full bg-brand-navy px-5 py-2.5 text-sm font-bold text-white shadow-sm transition hover:bg-brand-navy-900"
          >
            API docs
            <ExternalLink className="h-3.5 w-3.5 shrink-0 opacity-95" strokeWidth={2.5} aria-hidden />
          </a>
        </div>
      </div>
    </header>
  );
}
