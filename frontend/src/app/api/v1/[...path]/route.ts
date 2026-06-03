// Agent API gateway — catch-all Route Handler.
//
// Proxies `/api/v1/*` to the backend API server with API Key passthrough.
// See `@/lib/api/gateway` for the proxy logic and allowlist.

import { proxyToBackend } from "@/lib/api/gateway";

// Node.js runtime for stable header/body streaming; force-dynamic disables
// caching so every request hits the backend.
export const runtime = "nodejs";
export const dynamic = "force-dynamic";

type RouteContext = { params: { path: string[] } };

export function GET(request: Request, { params }: RouteContext) {
  return proxyToBackend(request, params.path);
}

export function POST(request: Request, { params }: RouteContext) {
  return proxyToBackend(request, params.path);
}

export function PATCH(request: Request, { params }: RouteContext) {
  return proxyToBackend(request, params.path);
}

export function PUT(request: Request, { params }: RouteContext) {
  return proxyToBackend(request, params.path);
}

export function DELETE(request: Request, { params }: RouteContext) {
  return proxyToBackend(request, params.path);
}
