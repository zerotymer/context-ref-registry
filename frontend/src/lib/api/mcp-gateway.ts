// MCP streamable-http gateway proxy.
//
// Forwards `/api/v1/mcp` to the backend MCP endpoint (`/mcp/`, served by the
// `api` app as a read-only streamable-http transport). Unlike the REST gateway
// (`gateway.ts`), MCP uses SSE / chunked streaming and long-lived connections,
// so this proxy MUST pipe request and response bodies as streams rather than
// buffering them with `request.text()` / `backendRes.text()`.
//
// Like the REST gateway, it forwards API Key headers and never forwards
// cookies — authentication is delegated entirely to the backend's
// `McpApiKeyAuthMiddleware`.

const BACKEND = process.env.BACKEND_API_URL ?? "http://localhost:8000";

// Request headers forwarded to the backend (whitelist). Beyond auth + content
// negotiation, MCP streamable-http carries session / protocol / resumability
// headers that the proxy must relay verbatim. Cookies and hop-by-hop headers
// are intentionally dropped.
const FORWARD_REQUEST_HEADERS = [
  "authorization",
  "x-api-key",
  "content-type",
  "accept",
  "mcp-session-id",
  "mcp-protocol-version",
  "last-event-id",
];

// Response headers preserved back to the client. `mcp-session-id` lets the
// client bind subsequent requests to the same session; content-type carries
// the SSE / JSON discriminator.
const FORWARD_RESPONSE_HEADERS = [
  "content-type",
  "cache-control",
  "mcp-session-id",
  "mcp-protocol-version",
];

/**
 * Proxy an MCP request to the backend streamable-http endpoint.
 *
 * Bodies are streamed in both directions; nothing is buffered. The backend
 * endpoint is `/mcp/` (trailing slash) — targeting it directly avoids the
 * `/mcp` -> `/mcp/` 307 redirect, which a streamed (single-read) request body
 * could not survive.
 *
 * @param request incoming Next.js Route Handler request
 */
export async function proxyMcpToBackend(request: Request): Promise<Response> {
  const url = new URL(request.url);
  // /api/v1/mcp[/...] -> /mcp[/...]; normalize the bare endpoint to a trailing
  // slash so the backend serves it without redirecting.
  const stripped = url.pathname.replace(/^\/api\/v1/, "");
  const backendPath = stripped === "/mcp" ? "/mcp/" : stripped;
  const targetUrl = `${BACKEND}${backendPath}${url.search}`;

  // Forward only whitelisted headers. No cookies, no hop-by-hop headers.
  const headers = new Headers();
  for (const name of FORWARD_REQUEST_HEADERS) {
    const value = request.headers.get(name);
    if (value) headers.set(name, value);
  }

  const method = request.method.toUpperCase();
  const hasBody = method !== "GET" && method !== "HEAD";

  // Stream the request body straight through. `duplex: "half"` is required by
  // the WHATWG fetch spec (undici) when sending a ReadableStream body.
  const init: RequestInit & { duplex?: "half" } = {
    method,
    headers,
    cache: "no-store",
    redirect: "manual",
  };
  if (hasBody) {
    init.body = request.body;
    init.duplex = "half";
  }

  const backendRes = await fetch(targetUrl, init);

  // Pipe the backend body stream verbatim (SSE / chunked). No buffering.
  const responseHeaders = new Headers();
  for (const name of FORWARD_RESPONSE_HEADERS) {
    const value = backendRes.headers.get(name);
    if (value) responseHeaders.set(name, value);
  }

  return new Response(backendRes.body, {
    status: backendRes.status,
    headers: responseHeaders,
  });
}
