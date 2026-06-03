// Agent API gateway proxy.
//
// Passthrough proxy that forwards agent-facing API requests from the Next.js
// frontend (`/api/v1/*`) to the backend API server, preserving the backend's
// status code, content-type, and body verbatim. Unlike `backendFetch` in
// `server.ts` (JWT cookie-based, for admin web UI Server Actions), this proxy
// does NOT inject cookies and does NOT unwrap the `OkResponse` envelope.
// Authentication is delegated entirely to the backend via API Key headers.

const BACKEND = process.env.BACKEND_API_URL ?? "http://localhost:8000";

// Top-level path prefixes exposed through the gateway (agent API surface).
const ALLOWED_PREFIXES = new Set([
  "entities",
  "relations",
  "search",
  "resolve",
  "tags",
  "context-bundle",
  "ingest",
  "export",
  "validate-references",
  "projects",
]);

// Human/admin (cookie-session) surfaces that must never be reachable here,
// even if somehow added to the allowlist by mistake.
const DENIED_PREFIXES = new Set(["auth", "admin"]);

// Request headers forwarded to the backend (whitelist). Cookies and
// hop-by-hop headers are intentionally dropped.
const FORWARD_REQUEST_HEADERS = [
  "authorization",
  "x-api-key",
  "content-type",
  "accept",
];

function notFound(path: string): Response {
  return Response.json(
    {
      ok: false,
      error: {
        code: "NOT_FOUND",
        message: `Gateway route not allowed: /${path}`,
      },
    },
    { status: 404 },
  );
}

/**
 * Proxy an agent API request to the backend.
 *
 * @param request   incoming Next.js Route Handler request
 * @param pathParts catch-all segments (`params.path`) — used for allowlist check
 */
export async function proxyToBackend(
  request: Request,
  pathParts: string[],
): Promise<Response> {
  const prefix = pathParts[0] ?? "";

  // Allowlist + explicit denylist. Anything outside the agent API surface 404s
  // at the gateway (never reaches the backend).
  if (
    !prefix ||
    DENIED_PREFIXES.has(prefix) ||
    !ALLOWED_PREFIXES.has(prefix)
  ) {
    return notFound(pathParts.join("/"));
  }

  // Reconstruct the backend path from the original (still URL-encoded) pathname
  // to avoid re-encoding artifacts (refs may contain `@`, e.g. PROJECT_ID@TAG).
  const url = new URL(request.url);
  const backendPath = url.pathname.replace(/^\/api\/v1/, "");
  const targetUrl = `${BACKEND}${backendPath}${url.search}`;

  // Forward only whitelisted headers. No cookies, no hop-by-hop headers.
  const headers = new Headers();
  for (const name of FORWARD_REQUEST_HEADERS) {
    const value = request.headers.get(name);
    if (value) headers.set(name, value);
  }

  const method = request.method.toUpperCase();
  const hasBody = method !== "GET" && method !== "HEAD";
  const body = hasBody ? await request.text() : undefined;

  const backendRes = await fetch(targetUrl, {
    method,
    headers,
    body,
    cache: "no-store",
    redirect: "manual",
  });

  // Passthrough: preserve status code and content-type, return body verbatim.
  // Do NOT unwrap the OkResponse envelope — agents expect the same shape as a
  // direct backend call (201/207/401/404 and text/plain or raw JSON for export).
  const responseHeaders = new Headers();
  const contentType = backendRes.headers.get("content-type");
  if (contentType) responseHeaders.set("content-type", contentType);
  const contentDisposition = backendRes.headers.get("content-disposition");
  if (contentDisposition) {
    responseHeaders.set("content-disposition", contentDisposition);
  }

  const responseBody = await backendRes.text();
  return new Response(responseBody, {
    status: backendRes.status,
    headers: responseHeaders,
  });
}
