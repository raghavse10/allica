import { Card, CardTitle } from "@/components/ui/Card";
import { BandPill, BlockPill } from "@/components/ui/Pill";

export function Legend() {
  return (
    <Card padding="sm">
      <CardTitle>Legend</CardTitle>
      <ul className="m-0 mt-3 grid list-none grid-cols-[auto_minmax(0,1fr)] items-center gap-x-2 gap-y-2 p-0 text-xs text-ink-muted">
        <li className="contents">
          <span className="flex shrink-0 items-center">
            <BandPill band="high" />
          </span>
          <span className="min-w-0 leading-snug font-medium">
            ICP &gt; 0.50 — priority Growth-Inbound
          </span>
        </li>
        <li className="contents">
          <span className="flex shrink-0 items-center">
            <BandPill band="medium" />
          </span>
          <span className="min-w-0 leading-snug font-medium">
            0.30 – 0.50 — standard Growth-Inbound
          </span>
        </li>
        <li className="contents">
          <span className="flex shrink-0 items-center">
            <BandPill band="low" />
          </span>
          <span className="min-w-0 leading-snug font-medium">&lt; 0.30 — Triage qualification</span>
        </li>
        <li className="contents">
          <span className="flex shrink-0 items-center">
            <BlockPill />
          </span>
          <span className="min-w-0 leading-snug font-medium">Eligibility decline</span>
        </li>
      </ul>
    </Card>
  );
}
