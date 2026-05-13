import Link from "next/link";

export default function NotFound() {
  return (
    <div className="grid place-items-center py-24 text-center">
      <h1 className="text-2xl font-bold text-brand-navy-900">Not found</h1>
      <p className="mt-2 text-sm text-ink-muted">
        The page or run you&rsquo;re looking for doesn&rsquo;t exist.
      </p>
      <Link
        href="/"
        className="mt-6 inline-flex items-center rounded-lg border border-brand-orange/35 bg-brand-orange/10 px-4 py-2 text-sm font-medium text-brand-orange-600 transition hover:bg-brand-orange/20"
      >
        Back to console
      </Link>
    </div>
  );
}
