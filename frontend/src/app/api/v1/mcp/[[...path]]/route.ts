// MCP streamable-http gateway — catch-all Route Handler.
//
// Proxies `/api/v1/mcp` (and any sub-path) to the backend MCP endpoint with
// API Key passthrough and full request/response streaming. This is the single
// external entry point for MCP clients; the backend `/mcp` stays internal.
// See `@/lib/api/mcp-gateway` for the streaming proxy logic.
//
// A dedicated `mcp` segment takes precedence over the REST gateway's
// `[...path]` catch-all (`../[...path]/route.ts`), so MCP traffic never hits
// the buffering REST proxy.

import { proxyMcpToBackend } from "@/lib/api/mcp-gateway";

// Node.js runtime for streaming body passthrough; force-dynamic disables
// caching so every request reaches the backend.
export const runtime = "nodejs";
export const dynamic = "force-dynamic";

// MCP streamable-http uses POST (requests), GET (SSE stream), and DELETE
// (session termination).
export function GET(request: Request) {
  return proxyMcpToBackend(request);
}

export function POST(request: Request) {
  return proxyMcpToBackend(request);
}

export function DELETE(request: Request) {
  return proxyMcpToBackend(request);
}
