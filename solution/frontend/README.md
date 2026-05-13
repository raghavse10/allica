# Allica Frontend — Next.js 15 Operator Console

A production-grade React frontend for the Allica GTM Assistant, built to be
extended.

## Stack

| Layer | Choice | Why |
|---|---|---|
| Framework | **Next.js 15** (App Router, RSC) | File-based routing for the pages we'll add (`/runs/[id]`, `/leads/[id]`, settings, auth). Server components fetch the API with no client JS. Server Actions give us free CSRF for mutations. |
| Language | **TypeScript** (strict) | Pydantic schemas mirrored 1:1 in `src/lib/types.ts`. Compile-time guarantees that the UI never reads a field the API doesn't return. |
| Styling | **Tailwind v4** | Brand tokens declared once via `@theme`; every component reads them as utilities. No `tailwind.config.js` needed in v4. |
| Fonts | `next/font/google` (Inter, JetBrains Mono) | Self-hosted, no FOIT, no extra `<link>`s. |
| Networking | Native `fetch` + small typed client (`src/lib/api.ts`) | No SWR/React-Query yet — Server Components + Server Actions cover everything we need. |
| Class merging | `clsx` (tiny) | Avoids the bigger `tailwind-merge` until we actually conflict. |

## Layout

```
frontend/
├── src/
│   ├── app/                       Next App Router pages
│   │   ├── layout.tsx             Top bar, fonts, brand chrome
│   │   ├── page.tsx               Home: HomeShell + RecentRuns
│   │   ├── runs/page.tsx          All runs table
│   │   ├── runs/[id]/page.tsx     Single run detail (server-rendered)
│   │   ├── not-found.tsx          404
│   │   └── actions.ts             "use server" — POST /run + POST feedback
│   ├── components/
│   │   ├── ui/                    Card, Button, Pill, Modal, ScoreCircle
│   │   ├── HomeShell.tsx          Client island that owns the live RunResponse
│   │   ├── RunControls.tsx        Calls runPipelineAction
│   │   ├── RunSummary.tsx         Stats + distribution bars
│   │   ├── RecentRuns.tsx         RSC — server-fetched, links to /runs/[id]
│   │   ├── Legend.tsx
│   │   ├── LeadList.tsx           Filterable list + modal trigger
│   │   ├── LeadCard.tsx
│   │   ├── LeadDetail.tsx         Modal contents
│   │   ├── OverrideControls.tsx   Calls recordOverrideAction
│   │   └── RunDetailShell.tsx     Adapts a stored RunDetail → RunResponse
│   ├── lib/
│   │   ├── api.ts                 Typed FastAPI client (server + client safe)
│   │   ├── types.ts               TS mirror of Pydantic schemas
│   │   ├── format.ts              shortId, formatDateTime
│   │   └── cn.ts                  clsx wrapper
│   └── styles/globals.css         Tailwind v4 + brand @theme tokens
├── next.config.ts                 Dev rewrites /api/* → http://localhost:8000
├── postcss.config.mjs             @tailwindcss/postcss
├── tsconfig.json
└── package.json
```

## Run

```bash
# 1. Start the FastAPI backend (in one terminal):
cd ..
.venv/bin/uvicorn allica.api.app:app --port 8000

# 2. Start the Next dev server (in another):
cd frontend
npm install
npm run dev
```

Then open <http://localhost:3000>.

The dev server proxies every browser request hitting `/api/*` to
`http://localhost:8000/*` (configurable via `ALLICA_API_URL`), so you never
deal with CORS in development.

## Build

```bash
npm run build       # production build
npm run start       # serve the build
npm run typecheck   # tsc --noEmit
npm run lint        # next lint
```

## Brand tokens (single source of truth)

In `src/styles/globals.css`:

```css
@theme {
  --color-brand-orange:      #ff5200;
  --color-brand-orange-600:  #cc4201;
  --color-brand-cream-100:   #fdfcfb;
  --color-brand-cream-200:   #f8f6f2;
  --color-brand-cream-300:   #f5f0e9;
  --color-brand-navy:        #00204e;
  --color-brand-navy-900:    #000f27;
  /* …semantic aliases (surface, ink, line, danger) */
}
```

Tailwind v4 generates utilities from these automatically — `bg-brand-orange`,
`text-brand-navy-900`, `border-brand-cream-300`, `text-ink-muted`, …

## How to extend

* **New page:** drop a file under `src/app/` — App Router picks it up. Server
  components are the default; add `"use client"` only where you need React state.
* **New API endpoint:** add it to `src/lib/api.ts` with a typed return shape.
  Mutations should be wrapped in a Server Action in `src/app/actions.ts` so they
  benefit from the framework's CSRF protection and revalidation.
* **New mutation:** create a function in `actions.ts` marked `"use server"`,
  call it from a client component via `useTransition()`, and use
  `revalidatePath()` to refresh server-rendered data.
* **Auth:** Drop in `next-auth` or your provider of choice in `src/middleware.ts`.

## Deployment

The frontend and the FastAPI backend are **fully decoupled** — separate
images, no shared code, no shared build step. Pick the topology that fits.

### Topology A — Co-located (default)

Two containers behind one reverse proxy. The browser only ever talks to
the FE host; the FE proxies `/api/*` to the BE over the internal network.

```
[ browser ] → fe.example.com → [ next ] → /api/*  → http://api:8000
                                  ↳ everything else → Next pages
```

Env vars to set on the FE container:

| Var | Value | Where |
|---|---|---|
| `ALLICA_API_URL` | `http://api:8000` (internal hostname) | runtime |

Leave `NEXT_PUBLIC_API_URL` unset. Run `docker compose up` in `solution/`
to see this in action.

### Topology B — Independent (FE on Vercel, BE on Fly / Railway / K8s)

Two services on different hostnames. The browser hits the BE directly;
CORS is the only cross-origin concern.

```
[ browser ] → app.example.com (Vercel)   ← static + RSC + actions
              ↘ also fetches → api.example.com (Fly / your cluster)
```

Env vars to set:

| Service | Var | Value | When |
|---|---|---|---|
| FE | `NEXT_PUBLIC_API_URL` | `https://api.example.com` | **build time** (baked into the JS bundle) |
| FE | `ALLICA_API_URL` | `https://api.example.com` (or an internal URL) | runtime, for RSC + actions |
| BE | `ALLICA_CORS_ORIGINS` | `https://app.example.com` | runtime |

Build the FE image with the public API URL baked in:

```bash
docker build \
  --build-arg NEXT_PUBLIC_API_URL=https://api.example.com \
  -t allica-web:prod \
  solution/frontend
```

Or on Vercel: set `NEXT_PUBLIC_API_URL` in the project's Environment
Variables (build-time scope) and deploy normally.

### Topology C — Same Vercel project, BE on a separate worker

Use Vercel rewrites in `next.config.ts` (already set up — leave
`NEXT_PUBLIC_API_URL` unset and set `ALLICA_API_URL` to the BE URL).
Browser sees `/api/*`; Vercel's edge proxies to your BE.

FastAPI is now a pure JSON API: `GET /` returns a small service-identity
document; the operator UI lives entirely in this Next.js app. There is no
parallel static-HTML console to keep in sync.
