import type { NextConfig } from "next";

/**
 * Two deployment topologies, switched by env var:
 *
 *   1. Co-located (default): the browser hits /api/* on the FE host and
 *      Next rewrites those requests to ALLICA_API_URL (or localhost:8000
 *      in dev). This keeps everything same-origin and CORS-free.
 *
 *   2. Independent: set NEXT_PUBLIC_API_URL=https://api.example.com and
 *      the browser talks directly to the API. The /api/* rewrite is
 *      disabled because it isn't needed.
 *
 * No code changes; pick a topology by setting (or not setting) the env var.
 */

const PROXY_TARGET = process.env.ALLICA_API_URL ?? "http://localhost:8000";
const USE_PROXY = !process.env.NEXT_PUBLIC_API_URL;

const nextConfig: NextConfig = {
  reactStrictMode: true,
  typedRoutes: true,
  /** Avoid barrel-resolution issues with `lucide-react` in the RSC / webpack flight pipeline. */
  experimental: {
    optimizePackageImports: ["lucide-react"],
  },
  // Enables `next build && next start` to produce a slim standalone server
  // bundle (no node_modules in the runtime image). Required by the multi-
  // stage Dockerfile.
  output: "standalone",
  async rewrites() {
    if (!USE_PROXY) return [];
    return [{ source: "/api/:path*", destination: `${PROXY_TARGET}/:path*` }];
  },
};

export default nextConfig;
