# Allica GTM Assistant

A production-grade **inbound-lead triage service** for Allica's GTM team. The service:

1. **Cleans & deduplicates** raw inbound leads.
2. **Validates** them (email shape, identity).
3. **Enriches** with the (stubbed) Companies House registry.
4. **Applies eligibility & risk rules** (per `docs/eligibility.md`).
5. **Scores ICP / priority** with an explainable additive model.
6. **Routes** the lead (Growth-Inbound / Triage / Manual-Review / Decline).
7. **Drafts a compliant first-touch email** (template by default; optional LLM via Gemini or OpenAI, always re-sanitised).
8. **Surfaces safety flags** for any prohibited language — in input *or* output.
9. **Persists every run** to a database (SQLite for dev, Postgres-ready for prod) with payload-hash idempotency, full lead history, and operator feedback capture for the routing learning loop.
10. **Redacts PII** before storage — emails and notes are SHA-256 salted-hashed; only an 80-char single-line excerpt is kept for operator recognition.

Surfaces: a polished operator UI, a JSON HTTP API, a CLI, and a Docker image.

---

## Quick Start

Prerequisites: **Python 3.10+** (tested on 3.14).

```bash
cd solution
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Bundled sample leads and Companies House stub live in **`solution/data/`** (`leads_small.json`, `companies_house_stub.json`). Omitting `leads` on `POST /run` loads that copy; you can also point the CLI at `data/leads_small.json` from the `solution/` directory.

### Run the API

```bash
uvicorn allica.api.app:app --reload --port 8000
# or
./scripts/serve.sh
```

The first request creates a `allica.sqlite` file next to the package — that's where every run, lead verdict, safety event and operator override is stored. Delete the file to start fresh.

### Run the operator console (frontend)

The operator UI is a **Next.js 15 + React 19 + TypeScript** app under `frontend/`. The FastAPI service is API-only — it serves JSON, never HTML.

```bash
# Terminal 1 — backend
.venv/bin/uvicorn allica.api.app:app --port 8000

# Terminal 2 — frontend
cd frontend
npm install
npm run dev
```

Then open <http://localhost:3000>. The Next dev server proxies `/api/*` to FastAPI so the browser never deals with CORS. See `frontend/README.md` for the full architecture and how to extend it.

### Run with Docker

The compose file ships **two services** (`api` + `web`) so you can verify
the decoupled topology end-to-end:

```bash
# SQLite-backed API + Next.js web, two containers:
docker compose up --build
# → web at http://localhost:3000, API at http://localhost:8000

# Production-shaped: Postgres + alembic migrations
docker compose --profile postgres up --build
```

**Independent deployment** (FE on Vercel, BE on Fly/K8s/etc.) is fully
supported — see `frontend/README.md` for the env-var matrix and topology
options. Key knobs:

| Where | Var | Purpose |
|---|---|---|
| BE | `ALLICA_CORS_ORIGINS` | Comma-separated allowlist (default `*`). |
| FE (build) | `NEXT_PUBLIC_API_URL` | Public API URL baked into the browser bundle. |
| FE (runtime) | `ALLICA_API_URL` | URL the Next server uses for RSC / server actions. Can be internal. |

Then open:

* **Operator UI** (Next.js dev server) → <http://localhost:3000/>
* **API** — OpenAPI → <http://localhost:8000/docs>, health → <http://localhost:8000/health>, service root → <http://localhost:8000/> (JSON metadata, not the UI)

### Try the endpoint

```bash
# Run on the bundled sample data
curl -s -X POST http://localhost:8000/run \
     -H 'Content-Type: application/json' \
     -d '{}' | jq .summary

# Run on your own leads file (the JSON file is a bare array; the API expects
# `{"leads": [...]}` — wrap with jq from the `solution/` directory)
jq '{leads: .}' data/leads_small.json | curl -s -X POST http://localhost:8000/run \
     -H 'Content-Type: application/json' \
     -d @-
```

### CLI

```bash
# Pretty-print the full response for the bundled sample
python -m allica.cli run --summary

# Run on a custom file, write JSON to disk, skip emails
python -m allica.cli run -i data/leads_small.json -o out.json --no-email

# Use an LLM (output is always sanitised). Provider auto-detected from env:
GEMINI_API_KEY=AI...  python -m allica.cli run --llm     # Google Gemini
OPENAI_API_KEY=sk-... python -m allica.cli run --llm     # OpenAI

# Run the eval suite (evals/cases.json)
python -m allica.cli eval -v
```

### Tests

```bash
python -m pytest -v
```

30 unit tests covering validation, dedup, safety rules, email composer fallbacks, storage-backed API, and end-to-end pipeline behaviour. The eval suite (`allica/cli eval`) runs the full pipeline against `evals/cases.json` and reports a green/red summary.

---

## Storage

Every `POST /run` is persisted to a database. The same payload submitted twice returns the cached result (look for `meta.cached: true` in the response and a tiny "cached" badge in the UI).

| Layer | What it does | File |
|---|---|---|
| **Engine + sessions** | SQLAlchemy 2.x sync engine, connection pool, FK enforcement on SQLite, redacted URL logging. | `allica/storage/engine.py` |
| **Models** | `Run`, `LeadResult`, `SafetyEvent`, `RoutingOverride`, `RunError`. UUID PKs, FK cascades, JSON columns for replay. | `allica/storage/models.py` |
| **Repositories** | One per aggregate root. Sessions are passed in (unit-of-work pattern). | `allica/storage/repositories.py` |
| **PII redaction** | Salted SHA-256 of email/notes; never store raw. 80-char sanitised excerpt for operator UI. | `allica/storage/redaction.py` |
| **Idempotency** | SHA-256 of the canonical request body; `UNIQUE` index on `runs.payload_hash`. | `allica/storage/hashing.py` |
| **Service layer** | Calls the pure pipeline, then persists. Pipeline stays untouched. | `allica/services/run_service.py` |
| **Migrations** | Alembic, with auto-create on startup for SQLite dev. | `migrations/`, `alembic.ini` |

### Switching to Postgres

```bash
export DATABASE_URL=postgresql+psycopg://user:pass@host:5432/allica
export ALLICA_DB_AUTO_MIGRATE=false
pip install "psycopg[binary]"
alembic upgrade head
uvicorn allica.api.app:app
```

Or just use the bundled compose profile:

```bash
docker compose --profile postgres up
```

### New endpoints (storage-backed)

| Method & path | Purpose |
|---|---|
| `POST /run` | Run pipeline. Idempotent on payload hash. Response includes `meta.run_id`, `meta.cached`, `meta.lead_result_ids`. |
| `GET  /runs?limit=N` | List recent runs (newest first). |
| `GET  /runs/{run_id}` | Full persisted run with every lead, safety event and override. |
| `GET  /leads/history?external_id=L-2001` | Every time this lead has been processed. |
| `GET  /leads/history?company=Acme%20Ltd` | Same, by company name. |
| `POST /leads/{lead_result_id}/feedback` | Record an operator routing override (the labelled-data feedback loop). |

### What the DB stores (and what it never stores)

| Persisted | Not persisted |
|---|---|
| Counts, scores, bands, owner, queue, rationale | Raw email addresses |
| `score_contributions`, `eligibility_findings`, `safety_events` (full JSON for replay) | Raw notes (only the 80-char excerpt + hash) |
| Email subject + body of every drafted email (we already sent / would send these) | LLM API keys |
| `email_hash`, `notes_hash` — salted SHA-256 (per-deployment salt via `ALLICA_PII_SALT`) | Anything not in the schemas |

### Production setup checklist

- [x] **Idempotency** — payload-hash UNIQUE index, cached responses return instantly.
- [x] **Connection pooling** — SQLAlchemy default pool; `pool_pre_ping=True`.
- [x] **FK constraints** — enforced on SQLite (PRAGMA), default on Postgres.
- [x] **Cascades** — deleting a run removes its leads, events and overrides (GDPR-friendly).
- [x] **Migrations** — Alembic with autogenerate; dev gets auto-create on startup.
- [x] **PII handling** — salted hashes, no raw email/notes ever leave Python objects.
- [x] **Health check** — `GET /health` reports storage backend.
- [x] **Structured logs** — JSON logs include redacted DB URL and idempotency hits.
- [x] **Non-root container user** — `allica:allica` in Dockerfile.
- [x] **Docker Healthcheck** — built into the image.

## Response shape

`POST /run` returns:

```jsonc
{
  "summary": {
    "received":    10,
    "processed":   9,
    "dropped":     1,           // duplicates + structurally-invalid
    "duplicates":  1,
    "by_owner":    {"Growth-Inbound": 6, "Manual-Review": 2, ...},
    "by_band":     {"high": 3, "medium": 4, "low": 2},
    "elapsed_ms":  11
  },
  "leads": [
    {
      "id": "L-2001",
      "company_name": "Oxfordshire Bakery Ltd",
      "validation": { "passed": true, "email_valid": true, "is_duplicate": false, ... },
      "enrichment": { "matched": true, "company_number": "08976543", "status": "active",
                      "sic_codes": ["10710"], "derived_sector": "Food & Beverage",
                      "registered_address": "...", "incorporated_on": "2014-05-12",
                      "age_years": 11.0 },
      "eligibility": { "eligible": true, "requires_manual_review": false,
                       "findings": [{"code": "...", "severity": "info", "message": "..."}] },
      "score": { "value": 0.85, "band": "high",
                 "contributions": [{"feature": "revenue", "weight": 0.20,
                                    "reason": "£1,800,000 fits the £500k–£2m band."}] },
      "routing": { "owner": "Growth-Inbound", "queue": "priority",
                   "rationale": "High ICP (0.85) — priority response per playbook." },
      "email": { "subject": "...", "body": "...", "word_count": 142, "cta_count": 1,
                 "used_disclaimer": false, "generator": "template" },
      "safety_flags": [{"code": "...", "severity": "info", "message": "..."}],
      "processed": true
    },
    ...
  ],
  "meta": { "registry_path": "...", "email_drafting": true, "llm_preferred": false }
}
```

Field names and types live in `allica/core/schemas.py` (Pydantic models), so the OpenAPI spec at `/docs` is the canonical contract.

---

## Project layout

```
solution/
├── README.md
├── pyproject.toml
├── requirements.txt
├── .env.example
├── data/                        # Bundled leads_small.json + companies_house_stub.json (default inputs)
├── scripts/
│   ├── serve.sh                 # uvicorn dev server
│   └── run_pipeline.sh          # CLI shortcut
└── allica/
    ├── api/
    │   └── app.py               # FastAPI app + /run + history + feedback + /sample
    ├── core/
    │   ├── schemas.py           # Pydantic response contract (single source of truth)
    │   ├── constants.py         # All thresholds, weights, limits — one place to tune
    │   ├── patterns.py          # Shared compiled regex patterns
    │   ├── paths.py             # Filesystem path discovery
    │   ├── text_utils.py        # normalise_text / normalise_host / first_name / count_words
    │   ├── sectors.py           # SIC_TO_SECTOR + TARGET_SECTORS + SECTOR_PROPS
    │   ├── registry.py          # CompaniesHouseStub adapter
    │   ├── enrichment.py        # enrich_lead — joins lead + registry
    │   ├── routing.py           # owner / queue decision
    │   ├── pipeline.py          # orchestrator — wires pure stages (persistence is in RunService)
    │   ├── logging_setup.py     # structured JSON logs
    │   ├── validation/          # cleaning, dedup, email shape, structural validator
    │   │   ├── cleaning.py
    │   │   ├── email_check.py
    │   │   ├── dedup.py
    │   │   └── validator.py
    │   ├── eligibility/         # one rule function per finding
    │   │   ├── rules.py
    │   │   └── assessor.py
    │   ├── scoring/             # explainable additive ICP score
    │   │   ├── keywords.py      # data: USE_CASE_KEYWORDS, NEGATIVE_KEYWORDS
    │   │   ├── features.py      # one contribution function per signal
    │   │   ├── banding.py       # score → band
    │   │   └── scorer.py        # aggregator
    │   ├── safety/              # banned-phrase sanitiser + disclaimer + CTA counter
    │   │   ├── rules.py         # data: BANNED_RULES
    │   │   ├── sanitiser.py
    │   │   ├── input_scanner.py
    │   │   └── cta.py
    │   └── email/               # template + optional LLM drafting
    │       ├── context.py       # EmailContext + need inference
    │       ├── template.py      # deterministic generator
    │       ├── prompt.py        # LLM system prompt + JSON parser
    │       ├── composer.py      # template/LLM dispatch + safety wiring
    │       └── llm/             # provider-agnostic LLM dispatch
    │           ├── base.py      # LLMProvider Protocol
    │           ├── gemini.py
    │           ├── openai.py
    │           └── dispatcher.py
    ├── tests/                   # pytest unit tests + eval runner
    │   ├── test_validation.py
    │   ├── test_safety.py
    │   ├── test_pipeline.py
    │   ├── test_storage_api.py
    │   └── eval_runner.py
    └── cli.py

solution/frontend/             # Next.js 15 + React 19 + TypeScript operator console
                                # See frontend/README.md for full layout.
```

### Module conventions

* **Data lives in `*/keywords.py`, `*/rules.py`, `sectors.py`, `constants.py`.** Tuning policy = editing data, not code.
* **One responsibility per file.** `safety/sanitiser.py` rewrites; `safety/rules.py` is the rule list; `safety/input_scanner.py` flags prospect-side risk; `safety/cta.py` counts CTAs. None overlap.
* **Subpackages re-export their public API** in `__init__.py`, so callers write `from allica.core.safety import sanitise_email` without knowing the internal layout.
* **Lazy LLM imports** — `google-genai` and `openai` are only imported inside the provider that needs them. The package runs with neither installed.

---

## Candidate — Problem and design framing

### 1. Problem interpretation

Allica receives inbound lending interest from established UK SMEs through forms, referrals and events. Today a human triages every one — cleaning the input, checking eligibility, choosing an owner, and writing the first reply — which doesn't scale and is repetitive. This assistant should turn each raw lead into a **decision and a draft in under a second**: dedup, validate, enrich from Companies House, score against Allica's ICP, route to the right team, and produce a safe first-touch email. A "good" v1 hides the easy 70% from operators (auto-routes the obvious good leads to Growth-Inbound, the obvious bad ones to Decline, and surfaces the gray-zone ones to Manual-Review with a clear rationale) so humans only spend time where their judgement actually moves the needle.

### 2. Metrics and constraints

* **Primary success metric: first-pass routing accuracy** — the proportion of leads whose auto-assigned owner (Growth-Inbound / Triage / Manual-Review / Decline) matches what an experienced operator would have chosen, sampled weekly. This directly measures whether we're saving the team time without dropping good leads.
* **Guardrail 1: unsafe-message rate** — proportion of drafted emails that an operator (or our regex sanitiser) flags as containing prohibited language (guarantees, exact timelines, invented rates). Target: 0%. We treat this as a hard ceiling because a single non-compliant outbound email is far more expensive than a missed opportunity.
* **Guardrail 2: false-pass rate on ineligible leads** — proportion of leads with a `block`-severity eligibility finding that *still* land in Growth-Inbound rather than Decline / Manual-Review. Target: 0%. This catches a bug class where a soft scoring signal overrides a hard policy rule.

### 3. Main tradeoffs

In a 3–5 hour timebox I deliberately did **not** build:

* **A learned model.** The data is tiny and the rules in `docs/eligibility.md` and `docs/gtm_playbook.md` are crisp. A transparent additive score plus a small rules layer is faster to build, easier for the GTM team to challenge, and trivial to re-weight as we learn — all of which matter more right now than marginal accuracy.
* **A real Companies House integration.** The stub is sufficient to demonstrate the join + the eligibility surface that depends on `status` and `incorporated_on`. Real integration adds rate limits, caching, and webhook flows that aren't in scope.
* **Auth, SSO, durable job queues, and multi-tenant isolation.** Runs are persisted (SQLite by default; Postgres-ready) with idempotent replay and history APIs, but there is no login/session model, no SQS-style work queues, and no per-customer data boundary.
* **Multi-provider LLM orchestration beyond Gemini/OpenAI, RAG, embeddings.** Optional LLM email drafting uses one provider at a time with a deterministic template fallback and mandatory safety post-processing; the *routing* logic stays rule-based. Eval case E-10 (retrieval) is left as a documented next step rather than half-built.
* **Native mobile apps or white-label embeds.** The operator experience is a **Next.js** web console (`frontend/`) plus OpenAPI — not a native client or SDK for third-party sites.

### 4. High-level architecture

```
              ┌───────────────────┐
inbound ───▶  │   POST /run       │  FastAPI primary entrypoint (+ `/runs`, feedback, `/health`; see OpenAPI)
   JSON       └────────┬──────────┘
                       ▼
                ┌──────────────┐
                │   clean      │  trim, lowercase, normalise URLs
                ├──────────────┤
                │   dedup      │  (norm name, norm host) heuristic
                ├──────────────┤
                │   validate   │  email shape, identity, mark/drop
                ├──────────────┤
                │   enrich     │  Companies House stub → status, SIC, age
                ├──────────────┤
                │ eligibility  │  hard rules from docs/eligibility.md
                ├──────────────┤
                │   score      │  additive ICP, every weight named
                ├──────────────┤
                │   route      │  band + eligibility → owner/queue
                ├──────────────┤
                │   email      │  template by default, LLM optional
                ├──────────────┤
                │   safety     │  banned-phrase sanitiser, disclaimer
                └──────┬───────┘
                       ▼
                ┌──────────────┐
                │ RunResponse  │  summary + per-lead full breakdown
                └──────────────┘

Next.js console     ← solution/frontend/, calls /run + /runs + /leads/...
CLI (`allica run`) ← same pipeline, JSON in / JSON out
```

Each pipeline stage in `allica/core/` is a **pure function** (`input → output`, no I/O). `pipeline.py` orchestrates those stages only. **Persistence** (runs, idempotency, overrides) lives in `RunService` + SQLAlchemy models — outside the pure core — so scoring and rules stay easy to test in isolation.

---

## Candidate — Design Notes

### 1. Scoring and routing

The ICP score is an **additive model with named contributions** (`allica/core/scoring/`, aggregated in `scorer.py`). We start from a 0.40 base — an inbound enquiry is itself a positive signal — and add or subtract weighted contributions:

| Feature              | Range          | Why                                                        |
| -------------------- | -------------- | ---------------------------------------------------------- |
| **revenue band**     | -0.25 → +0.35  | Strongest signal: Allica's product fits a band.           |
| **sector fit**       | -0.10 → +0.20  | Five target sectors get a positive nudge; others penalty. |
| **trading history**  | -0.20 → +0.10  | Companies <2 years go to alternate flow per policy.       |
| **headcount**        | -0.10 → +0.10  | Catches sole-trader-like ops the docs exclude.            |
| **use-case keywords**| ±0.10 / -0.30  | "equipment", "invoice", "refinance" are direct fits; "venture capital" is a hard negative. |

The total is clamped to `[0, 1]` and bucketed using the bands from the GTM playbook (`>0.5` high, `0.3–0.5` medium, `<0.3` low). Every contribution is returned in the API response with a human-readable `reason`, so operators can see exactly *why* a lead scored what it did — that explainability was a non-negotiable requirement.

Routing is a layered decision (`allica/core/routing.py`):

1. Eligibility `block` → **Decline**.
2. Eligibility `requires_manual_review` → **Manual-Review** (this overrides the score so a "high ICP but VC request" lead isn't auto-progressed).
3. Score band → **Growth-Inbound** (priority/standard) or **Triage**.

The two hardest routing buckets to choose were *Triage* vs *Manual-Review*. I went with: **Triage** for "low ICP but processable, just qualify on a call", **Manual-Review** for "policy says a human must look at this before any outbound." That mirrors how the docs talk about each.

### 2. Safety and compliance

The biggest risks are: (a) the LLM (or a sloppy template) shipping a prohibited phrase like "guaranteed approval", "approval within 24 hours", "lowest rates", or an invented APR; and (b) the email referencing pricing/terms without the required disclaimer.

`allica/core/safety/` (regex-driven sanitiser in `sanitiser.py`, rules in `rules.py`) has two responsibilities:

* It **rewrites** banned phrases to safe equivalents (e.g. "guaranteed approval" → "potential approval", "within 24 hours" → "quickly", "4.5% APR" → "indicative pricing") and surfaces a `SafetyFlag` for each rewrite.
* If the body mentions rates / terms / pricing it **appends** the required disclaimer (`Subject to status and credit checks. Terms apply.`).

Crucially, this same sanitiser runs whether the email came from the deterministic template *or* the optional LLM — the LLM cannot bypass compliance. If the LLM output ever contains a `block`-severity phrase we throw it away and fall back to the template entirely (rather than ship a half-rewritten model output). The same regex set also runs over the *prospect's own notes* so an operator sees flags like `prospect_guarantee_language` when someone writes "need approval within 24 hours guaranteed" — exactly the L-2005 case in the sample data.

What I'd add next: (i) per-sector forbidden-claim lists (e.g. healthcare-specific compliance language), (ii) an LLM-graded "tone" check on top of the regex, (iii) a daily report of which flags fired most often, to drive the regex set itself.

### 3. Failure modes and observability

Top failure modes and how the prototype handles them:

| Failure                                    | Detection                                                                                     | Mitigation                                                                                              |
| ------------------------------------------ | --------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------- |
| **No Companies House match**               | `Enrichment.matched=False`; eligibility raises `ch_no_match`; routes to Manual-Review.        | Surface in UI as a yellow warning so the operator knows to verify before outreach.                      |
| **LLM error / timeout / empty output**     | `generate_email_via_llm` returns `None` on any exception or missing key.                    | Falls back to deterministic template — every email always ships.                                        |
| **LLM produces banned language**           | Sanitiser catches it; if a `block` flag is raised, we drop the LLM output and use the template.| Hard guard: nothing prohibited can leave the system regardless of model behaviour.                      |
| **Bad input (missing fields, bad JSON)**   | Pydantic rejects malformed payloads at the API edge.                                          | Returns 422 with the offending field name.                                                              |
| **Bad email shape on lead**                | `validation.email_valid=False`; pipeline still routes but never drafts.                       | Operator sees "no email drafted" in UI and the validation issue list.                                   |
| **Duplicate flood**                        | `summary.duplicates`; UI greys-out duplicates so they don't compete for attention.            | Logging counts these so a sudden spike (e.g. broken form retry loop) is visible in metrics.             |

**Observability shipped:** structured JSON logs (`allica/core/logging_setup.py`) with a single line per pipeline run summarising counts and latency, no PII (notes/email/contact name are never logged — only ids and counts). The summary block in the API response *is* the metrics surface — in production I'd push `summary.elapsed_ms`, `summary.by_owner`, `summary.duplicates`, and a count of each safety-flag code to a metrics backend (Datadog/CloudWatch) and alert on (a) p95 latency > 2s, (b) any `block`-severity safety flag firing on outbound copy, (c) duplicate rate > 20%.

### 4. Next steps (1–2 days)

In priority order:

1. **Retrieval-augmented grounding** for the email step (eval E-10 calls this out). Index `docs/eligibility.md`, `docs/gtm_playbook.md`, plus a small library of past good emails; retrieve 3-5 snippets per lead and pass them to the LLM as grounding context. The current template hard-codes too much; this lets the GTM team edit a markdown file instead of code.
2. **Real Companies House integration** with on-disk caching, retries, and a stale-while-revalidate freshness window. Add a CCJ check via a credit-bureau stub.
3. **Richer operator feedback and exports.** Extend beyond routing overrides: thumbs on drafts, structured decline reasons, and CSV/Parquet export of labelled rows for offline model training.
4. **Auth + audit trail.** OAuth-protected endpoints; field-level audit of who changed what; retention policies aligned to GDPR.
5. **Production observability stack.** Ship metrics from `summary.*` and safety-flag counts to Datadog/CloudWatch with alerts on latency, duplicate spikes, and any outbound `block`-severity flags.

---

## LLM email drafting (optional)

The pipeline ships with a deterministic template generator (always available, no key required). To use an LLM instead, install one provider SDK and set its key:

```bash
# Google Gemini (free tier available at https://aistudio.google.com/apikey)
pip install google-genai
export GEMINI_API_KEY=AI...
# optional: pick a specific model (default: gemini-2.0-flash)
export ALLICA_LLM_MODEL=gemini-2.0-flash

# — or —

# OpenAI
pip install openai
export OPENAI_API_KEY=sk-...
export ALLICA_LLM_MODEL=gpt-4o-mini  # optional
```

**Easiest path** — paste the key into the bundled `local.env` file and source it:

```bash
# Open solution/local.env, paste your key after `GEMINI_API_KEY=`, save, then:
source ./scripts/use_env.sh
```

(The script confirms which provider is now active. `local.env` is gitignored so the key never leaves your machine.)

Then either:
* tick **"Prefer LLM"** in the operator UI before clicking Run, or
* call `python -m allica.cli run --llm`, or
* `POST /run` with `{"prefer_llm": true}`.

Selection rules:
* If `ALLICA_LLM_PROVIDER` is set to `gemini` or `openai`, that wins.
* Otherwise: Gemini is used if `GEMINI_API_KEY` (or `GOOGLE_API_KEY`) is set; else OpenAI if `OPENAI_API_KEY` is set; else the deterministic template.

**Safety guarantee:** every LLM output (regardless of provider) is run through the same regex sanitiser as the template path. If the model produces a hard-blocked phrase (`guaranteed approval`, exact APR, "lowest rates", etc.), we discard the LLM output and ship the template. The LLM cannot bypass compliance.

**Single CTA:** After sanitisation, if the body does not contain exactly one call-to-action cue (same `count_ctas` heuristic the template path is regression-tested against), we revert to the template and surface a `llm_cta_count` warning — matching the playbook’s “one clear ask” rule.

## Notes on hosting

Anything that runs a Python ASGI app works (Fly.io, Render, Railway, AWS Lambda via Mangum). **Request handling** is a thin API over a **stateless core pipeline**; **run history** is persisted to SQLite or Postgres, so scale the app and database tiers independently. Env vars: `GEMINI_API_KEY` / `OPENAI_API_KEY` (optional), `ALLICA_LLM_PROVIDER` (optional), `ALLICA_LLM_MODEL` (optional), `ALLICA_LOG_LEVEL`, `PORT`. See `.env.example`.
