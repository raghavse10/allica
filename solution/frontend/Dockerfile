# syntax=docker/dockerfile:1.6
# ---------- deps ------------------------------------------------------------
FROM node:22-alpine AS deps
WORKDIR /app
COPY package.json package-lock.json* ./
RUN npm ci

# ---------- builder ---------------------------------------------------------
FROM node:22-alpine AS builder
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY . .

# Build-time env vars are baked into the client bundle (Next embeds anything
# prefixed NEXT_PUBLIC_*). Set NEXT_PUBLIC_API_URL at build time when you
# want the browser to call the API directly:
#   docker build --build-arg NEXT_PUBLIC_API_URL=https://api.example.com .
ARG NEXT_PUBLIC_API_URL=""
ENV NEXT_PUBLIC_API_URL=${NEXT_PUBLIC_API_URL}

RUN npm run build

# ---------- runtime ---------------------------------------------------------
FROM node:22-alpine AS runner
WORKDIR /app

ENV NODE_ENV=production \
    PORT=3000 \
    HOSTNAME=0.0.0.0

# Run as a non-root user.
RUN addgroup -S nextjs && adduser -S -G nextjs nextjs

# Next's `output: "standalone"` produces a slim bundle that contains exactly
# the files the server needs at runtime — no full node_modules.
COPY --from=builder --chown=nextjs:nextjs /app/.next/standalone ./
COPY --from=builder --chown=nextjs:nextjs /app/.next/static ./.next/static
COPY --from=builder --chown=nextjs:nextjs /app/public ./public

USER nextjs

EXPOSE 3000
HEALTHCHECK --interval=30s --timeout=3s --retries=3 \
  CMD wget -qO- http://localhost:3000/ >/dev/null || exit 1

# At runtime ALLICA_API_URL controls server-side fetches (RSC + actions).
# It is OK if this is an internal hostname unreachable from the browser.
CMD ["node", "server.js"]
