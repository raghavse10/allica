/** Fetch helper: server uses ALLICA_API_URL; browser uses NEXT_PUBLIC_API_URL or `/api` proxy. */
import type {
  LeadResult,
  Override,
  RunDetail,
  RunListItem,
  RunResponse,
} from "./types";

const isServer = typeof window === "undefined";

/** Base URL the React server uses (RSC, server actions). */
const SERVER_BASE = (
  process.env.ALLICA_API_URL ??
  process.env.NEXT_PUBLIC_API_URL ??
  "http://localhost:8000"
).replace(/\/$/, "");

/** Base URL the browser uses. Empty string → use Next's /api proxy. */
const CLIENT_BASE = (process.env.NEXT_PUBLIC_API_URL ?? "").replace(/\/$/, "");

function url(path: string): string {
  const normalised = path.startsWith("/") ? path : `/${path}`;
  if (isServer) return `${SERVER_BASE}${normalised}`;
  return CLIENT_BASE
    ? `${CLIENT_BASE}${normalised}`
    : `/api${normalised}`; // dev fallback: rely on next.config rewrites
}

class ApiError extends Error {
  constructor(
    public status: number,
    message: string,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const target = url(path);
  let res: Response;
  try {
    res = await fetch(target, {
      ...init,
      headers: {
        "Content-Type": "application/json",
        ...(init?.headers ?? {}),
      },
      cache: "no-store",
    });
  } catch (cause) {
    const msg = cause instanceof Error ? cause.message : String(cause);
    throw new ApiError(503, `Cannot reach API (${target}): ${msg}`);
  }

  const text = await res.text();
  if (!res.ok) {
    throw new ApiError(res.status, `HTTP ${res.status}: ${text}`);
  }

  if (!text) {
    return null as T;
  }

  try {
    return JSON.parse(text) as T;
  } catch {
    throw new ApiError(502, `Invalid JSON from API ${path}: ${text.slice(0, 400)}`);
  }
}

// ---------------------------------------------------------------------------
// Read endpoints
// ---------------------------------------------------------------------------

export async function listRuns(limit = 20): Promise<RunListItem[]> {
  const data = await request<{ runs?: RunListItem[] }>(
    `/runs?limit=${encodeURIComponent(limit)}`,
  );
  return Array.isArray(data.runs) ? data.runs : [];
}

/** Paginated runs for infinite scroll (`offset` is number of rows to skip). */
export async function listRunsPage(
  offset: number,
  limit: number,
): Promise<{ runs: RunListItem[]; hasMore: boolean }> {
  const data = await request<{ runs?: RunListItem[]; has_more?: boolean }>(
    `/runs?limit=${encodeURIComponent(limit)}&offset=${encodeURIComponent(offset)}`,
  );
  const runs = Array.isArray(data.runs) ? data.runs : [];
  const hasMore =
    typeof data.has_more === "boolean" ? data.has_more : runs.length === limit;
  return { runs, hasMore };
}

export async function getRun(runId: string): Promise<RunDetail> {
  return request<RunDetail>(`/runs/${encodeURIComponent(runId)}`);
}

export async function getLeadHistory(opts: {
  externalId?: string;
  company?: string;
}): Promise<{ results: LeadResult[] }> {
  const params = new URLSearchParams();
  if (opts.externalId) params.set("external_id", opts.externalId);
  if (opts.company) params.set("company", opts.company);
  return request<{ results?: LeadResult[] }>(
    `/leads/history?${params.toString()}`,
  ).then((data) => ({
    results: Array.isArray(data.results) ? data.results : [],
  }));
}

export async function getSampleLeads(): Promise<unknown[]> {
  const data = await request<unknown>("/sample");
  return Array.isArray(data) ? data : [];
}

export async function getHealth(): Promise<{ status: string; storage: string }> {
  return request<{ status: string; storage: string }>("/health");
}

// ---------------------------------------------------------------------------
// Mutations
// ---------------------------------------------------------------------------

export interface RunRequest {
  leads?: unknown[];
  draft_email?: boolean;
  prefer_llm?: boolean;
}

export async function postRun(body: RunRequest = {}): Promise<RunResponse> {
  return request<RunResponse>("/run", {
    method: "POST",
    body: JSON.stringify(body),
  });
}

export interface FeedbackBody {
  corrected_owner: string;
  operator_id?: string | null;
  reason?: string | null;
}

export async function postFeedback(
  leadResultId: string,
  body: FeedbackBody,
): Promise<Override> {
  return request<Override>(
    `/leads/${encodeURIComponent(leadResultId)}/feedback`,
    { method: "POST", body: JSON.stringify(body) },
  );
}

export { ApiError };
export type { Override } from "./types";
