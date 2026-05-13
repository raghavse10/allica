"use client";

import { Modal } from "@/components/ui/Modal";
import { BoolIcon } from "@/components/ui/BoolIcon";
import { BandPill, CompaniesHouseStatusPill, SeverityChip } from "@/components/ui/Pill";
import { OverrideControls } from "@/components/OverrideControls";
import { Check } from "lucide-react";
import type { LeadResult } from "@/lib/types";
import type { ReactNode } from "react";

export function LeadDetail({
  lead,
  onClose,
}: {
  lead: LeadResult | null;
  onClose: () => void;
}) {
  return (
    <Modal
      open={!!lead}
      onClose={onClose}
      ariaLabel="Lead detail"
      ariaLabelledBy={lead ? "lead-detail-title" : undefined}
      header={lead ? <LeadDetailHeader lead={lead} /> : undefined}
    >
      {lead && <DetailContent lead={lead} />}
    </Modal>
  );
}

function LeadDetailHeader({ lead }: { lead: LeadResult }) {
  return (
    <div className="min-w-0">
      <h2
        id="lead-detail-title"
        className="m-0 truncate text-[20px] font-bold leading-tight text-brand-navy-900"
      >
        {lead.company_name ?? "Unknown"}
      </h2>
      <div className="mt-1.5 flex flex-wrap items-center gap-2 text-[13px] text-ink-muted">
        <BandPill band={lead.score.band} />
        <span>·</span>
        <span>ICP {lead.score.value.toFixed(3)}</span>
        <span>·</span>
        <span>
          routed to <strong className="text-ink">{lead.routing.owner}</strong> ({lead.routing.queue})
        </span>
      </div>
    </div>
  );
}

function DetailContent({ lead }: { lead: LeadResult }) {
  const e = lead.enrichment;
  return (
    <div>
      <Section title="Routing rationale">
        <p className="m-0 text-[13px] text-ink">{lead.routing.rationale}</p>
        <OverrideControls lead={lead} />
      </Section>

      <Section title="Validation">
        <KV
          rows={[
            [
              "Passed",
              <BoolIcon key="passed" ok={lead.validation.passed} aria-label={lead.validation.passed ? "Passed" : "Did not pass"} />,
            ],
            [
              "Email valid",
              <BoolIcon
                key="email"
                ok={lead.validation.email_valid}
                aria-label={lead.validation.email_valid ? "Email is valid" : "Email is not valid"}
              />,
            ],
            [
              "Is duplicate",
              <span key="dup" className="inline-flex flex-wrap items-center gap-2">
                <BoolIcon
                  ok={!lead.validation.is_duplicate}
                  aria-label={lead.validation.is_duplicate ? "Is a duplicate" : "Not a duplicate"}
                />
                {lead.validation.is_duplicate && lead.validation.duplicate_of ? (
                  <span className="text-[13px] text-ink-muted">of {lead.validation.duplicate_of}</span>
                ) : null}
              </span>,
            ],
            ["Issues", lead.validation.issues.join(", ") || "—"],
          ]}
        />
      </Section>

      <Section title="Companies House enrichment">
        {e.matched ? (
          <KV
            rows={[
              ["Company number", e.company_number ?? "—"],
              ["Status", <CompaniesHouseStatusPill key="ch-status" status={e.status} />],
              ["Sector", e.derived_sector ?? "—"],
              ["SIC codes", e.sic_codes.join(", ") || "—"],
              ["Address", e.registered_address ?? "—"],
              ["Incorporated", `${e.incorporated_on ?? "—"} (${e.age_years ?? "?"} yrs)`],
            ]}
          />
        ) : (
          <p className="m-0 text-[13px] text-ink-subtle">No Companies House match.</p>
        )}
      </Section>

      <Section title="Eligibility findings">
        {lead.eligibility.findings.length === 0 ? (
          <p className="m-0 text-[13px] text-ink-subtle">No findings.</p>
        ) : (
          <div className="flex flex-col gap-2">
            {lead.eligibility.findings.map((f, i) => (
              <div
                key={`${f.code}-${i}`}
                className="grid grid-cols-[80px_1fr] items-start gap-3 rounded-lg border border-line bg-brand-cream-100 px-3 py-2.5"
              >
                <SeverityChip severity={f.severity} />
                <div>
                  <strong className="text-xs text-brand-navy-900">{f.code}</strong>
                  <div className="mt-0.5 text-xs leading-relaxed text-ink-muted">{f.message}</div>
                </div>
              </div>
            ))}
          </div>
        )}
      </Section>

      <Section title="Score breakdown">
        <div className="flex flex-col gap-1.5">
          {lead.score.contributions.map((c, i) => (
            <div
              key={`${c.feature}-${i}`}
              className={`grid grid-cols-[180px_60px_1fr] items-center gap-3 rounded-lg border border-line bg-brand-cream-100 px-3 py-2 text-xs ${
                c.weight >= 0
                  ? "border-l-[3px] border-l-brand-orange"
                  : "border-l-[3px] border-l-[color:var(--color-danger)]"
              }`}
            >
              <span className="font-mono text-[11px] text-ink-muted">{c.feature}</span>
              <span className="font-bold text-brand-navy-900 tabular-nums">
                {c.weight >= 0 ? "+" : ""}
                {c.weight.toFixed(2)}
              </span>
              <span className="text-ink-muted">{c.reason}</span>
            </div>
          ))}
        </div>
      </Section>

      <Section title="Safety flags">
        {lead.safety_flags.length === 0 ? (
          <p className="m-0 text-[13px] text-ink-subtle">No safety flags.</p>
        ) : (
          <div className="flex flex-col gap-2">
            {lead.safety_flags.map((f, i) => (
              <div
                key={`${f.code}-${i}`}
                className="grid grid-cols-[80px_1fr] items-start gap-3 rounded-lg border border-line bg-brand-cream-100 px-3 py-2.5"
              >
                <SeverityChip severity={f.severity} />
                <div>
                  <strong className="text-xs text-brand-navy-900">{f.code}</strong>
                  <div className="mt-0.5 text-xs leading-relaxed text-ink-muted">{f.message}</div>
                </div>
              </div>
            ))}
          </div>
        )}
      </Section>

      <Section title="First-touch email draft">
        {lead.email ? (
          <>
            <div className="rounded-[10px] border border-line bg-brand-cream-100 p-4">
              <div className="mb-2.5 border-b border-line pb-2 font-semibold text-brand-navy-900">
                {lead.email.subject}
              </div>
              <div className="whitespace-pre-wrap text-[13px] leading-relaxed text-ink">
                {lead.email.body}
              </div>
            </div>
            <div className="mt-2 flex flex-wrap gap-3 text-[11px] text-ink-subtle">
              <span>{lead.email.word_count} words</span>
              <span>{lead.email.cta_count} CTA</span>
              <span>Generator: {lead.email.generator}</span>
              {lead.email.used_disclaimer && (
                <span className="inline-flex items-center gap-1">
                  disclaimer
                  <Check className="h-3 w-3 text-brand-orange" strokeWidth={2.5} aria-hidden />
                </span>
              )}
            </div>
          </>
        ) : (
          <p className="m-0 text-[13px] text-ink-subtle">
            No email drafted (lead is duplicate, ineligible, or has invalid email).
          </p>
        )}
      </Section>
    </div>
  );
}

function Section({ title, children }: { title: string; children: ReactNode }) {
  return (
    <section className="mt-5 border-t border-line pt-4 first-of-type:mt-0 first-of-type:border-t-0 first-of-type:pt-0">
      <h4 className="m-0 mb-2.5 text-xs font-bold uppercase tracking-[0.08em] text-ink-subtle">
        {title}
      </h4>
      {children}
    </section>
  );
}

function KV({ rows }: { rows: [string, ReactNode][] }) {
  return (
    <dl className="m-0 grid grid-cols-[150px_1fr] gap-x-4 gap-y-1.5 text-[13px]">
      {rows.map(([k, v]) => (
        <div key={k} className="contents">
          <dt className="font-medium text-ink-subtle">{k}</dt>
          <dd className="m-0 flex min-h-[1.25rem] items-center text-ink">{v}</dd>
        </div>
      ))}
    </dl>
  );
}
