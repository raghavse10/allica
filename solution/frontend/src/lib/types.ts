/**
 * TypeScript mirror of the FastAPI / Pydantic schemas.
 *
 * These shapes are hand-maintained today. Once the OpenAPI surface is stable
 * we should auto-generate this file from `/openapi.json` (e.g. with
 * `openapi-typescript`) so backend and frontend types can never drift.
 */

export type ScoreBand = "high" | "medium" | "low";
export type Owner = "Growth-Inbound" | "Triage" | "Manual-Review" | "Decline";
export type Queue = "priority" | "standard" | "qualification" | "ops" | "n/a";
export type Severity = "info" | "warning" | "block";

export interface ScoreContribution {
  feature: string;
  weight: number;
  reason: string;
}

export interface Score {
  value: number;
  band: ScoreBand;
  contributions: ScoreContribution[];
}

export interface EligibilityFinding {
  code: string;
  severity: Severity;
  message: string;
}

export interface Eligibility {
  eligible: boolean;
  requires_manual_review: boolean;
  findings: EligibilityFinding[];
}

export interface Routing {
  owner: Owner;
  queue: Queue;
  rationale: string;
}

export interface ValidationReport {
  passed: boolean;
  email_valid: boolean;
  is_duplicate: boolean;
  duplicate_of: string | null;
  issues: string[];
}

export interface Enrichment {
  matched: boolean;
  company_number: string | null;
  status: string | null;
  registered_address: string | null;
  incorporated_on: string | null;
  age_years: number | null;
  sic_codes: string[];
  derived_sector: string | null;
}

export interface SafetyFlag {
  code: string;
  severity: Severity;
  message: string;
}

export interface EmailDraft {
  subject: string | null;
  body: string;
  word_count: number;
  cta_count: number;
  used_disclaimer: boolean;
  generator: "template" | "llm";
}

export interface Override {
  id: string;
  original_owner: string;
  corrected_owner: string;
  operator_id: string | null;
  reason: string | null;
  created_at: string;
}

export interface LeadResult {
  /** External lead id, e.g. "L-2001". */
  id: string | null;
  /** DB id of the persisted row — only present when the run was persisted. */
  lead_result_id?: string;
  run_id?: string;
  company_name: string | null;
  validation: ValidationReport;
  enrichment: Enrichment;
  eligibility: Eligibility;
  score: Score;
  routing: Routing;
  email: EmailDraft | null;
  safety_flags: SafetyFlag[];
  overrides?: Override[];
  processed: boolean;
  processed_at?: string;
}

export interface RunSummary {
  received: number;
  processed: number;
  dropped: number;
  duplicates: number;
  by_owner: Record<string, number>;
  by_band: Record<string, number>;
  elapsed_ms: number;
}

export interface RunResponse {
  summary: RunSummary;
  leads: LeadResult[];
  meta: {
    run_id?: string;
    cached?: boolean;
    lead_result_ids?: Record<string, string>;
    [key: string]: unknown;
  };
}

export interface RunListItem {
  run_id: string;
  received_at: string;
  completed_at: string | null;
  received: number;
  processed: number;
  duplicates: number;
  elapsed_ms: number;
  by_owner: Record<string, number>;
  by_band: Record<string, number>;
  llm_preferred: boolean;
}

export interface RunDetail extends RunListItem {
  leads: LeadResult[];
}
