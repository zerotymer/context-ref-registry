import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { proxyMcpToBackend } from "./mcp-gateway";

const BACKEND = "http://localhost:8000";

type FetchCall = { url: string; init: RequestInit & { duplex?: string } };

let lastCall: FetchCall | null;

function mockBackend(
  response: {
    status?: number;
    body?: BodyInit | null;
    headers?: Record<string, string>;
  } = {},
) {
  const {
    status = 200,
    body = "{}",
    headers = { "content-type": "application/json" },
  } = response;
  const fetchMock = vi.fn(
    async (url: string | URL, init?: RequestInit & { duplex?: string }) => {
      lastCall = { url: String(url), init: init ?? {} };
      return new Response(body, { status, headers });
    },
  );
  vi.stubGlobal("fetch", fetchMock);
  return fetchMock;
}

function makeRequest(
  path: string,
  init: RequestInit & { headers?: Record<string, string> } = {},
): Request {
  return new Request(`http://localhost:3000/api/v1/${path}`, init);
}

beforeEach(() => {
  lastCall = null;
});

afterEach(() => {
  vi.unstubAllGlobals();
  vi.restoreAllMocks();
});

describe("proxyMcpToBackend — target path", () => {
  it("maps /api/v1/mcp to the backend /mcp/ endpoint (trailing slash)", async () => {
    mockBackend();
    await proxyMcpToBackend(makeRequest("mcp", { method: "POST", body: "{}" }));
    // Trailing slash avoids the /mcp -> /mcp/ 307 the stream body can't survive.
    expect(lastCall!.url).toBe(`${BACKEND}/mcp/`);
  });

  it("does not follow redirects (manual)", async () => {
    mockBackend();
    await proxyMcpToBackend(makeRequest("mcp", { method: "POST", body: "{}" }));
    expect(lastCall!.init.redirect).toBe("manual");
  });
});

describe("proxyMcpToBackend — header forwarding", () => {
  it("forwards Authorization (Bearer API Key)", async () => {
    mockBackend();
    await proxyMcpToBackend(
      makeRequest("mcp", {
        method: "POST",
        body: "{}",
        headers: { Authorization: "Bearer secret-key" },
      }),
    );
    const headers = new Headers(lastCall!.init.headers);
    expect(headers.get("authorization")).toBe("Bearer secret-key");
  });

  it("forwards X-API-Key", async () => {
    mockBackend();
    await proxyMcpToBackend(
      makeRequest("mcp", {
        method: "POST",
        body: "{}",
        headers: { "X-API-Key": "abc123" },
      }),
    );
    const headers = new Headers(lastCall!.init.headers);
    expect(headers.get("x-api-key")).toBe("abc123");
  });

  it("forwards MCP session / protocol / resumability headers", async () => {
    mockBackend();
    await proxyMcpToBackend(
      makeRequest("mcp", {
        method: "POST",
        body: "{}",
        headers: {
          "Mcp-Session-Id": "sess-1",
          "Mcp-Protocol-Version": "2025-03-26",
          "Last-Event-Id": "42",
          Accept: "application/json, text/event-stream",
        },
      }),
    );
    const headers = new Headers(lastCall!.init.headers);
    expect(headers.get("mcp-session-id")).toBe("sess-1");
    expect(headers.get("mcp-protocol-version")).toBe("2025-03-26");
    expect(headers.get("last-event-id")).toBe("42");
    expect(headers.get("accept")).toBe("application/json, text/event-stream");
  });

  it("does NOT forward Cookie / access_token", async () => {
    mockBackend();
    await proxyMcpToBackend(
      makeRequest("mcp", {
        method: "POST",
        body: "{}",
        headers: {
          Authorization: "Bearer k",
          Cookie: "access_token=jwt-token",
        },
      }),
    );
    const headers = new Headers(lastCall!.init.headers);
    expect(headers.get("cookie")).toBeNull();
  });
});

describe("proxyMcpToBackend — request streaming", () => {
  it("streams the POST body with duplex: half (no buffering)", async () => {
    mockBackend();
    const body = "{\"jsonrpc\":\"2.0\"}";
    const req = makeRequest("mcp", {
      method: "POST",
      body,
      headers: { "Content-Type": "application/json" },
    });
    await proxyMcpToBackend(req);
    // The request's own ReadableStream is forwarded as-is, not text-buffered.
    expect(lastCall!.init.body).toBe(req.body);
    expect(lastCall!.init.duplex).toBe("half");
  });

  it("does not send a body (or duplex) for GET", async () => {
    mockBackend({ headers: { "content-type": "text/event-stream" } });
    await proxyMcpToBackend(makeRequest("mcp"));
    expect(lastCall!.init.body).toBeUndefined();
    expect(lastCall!.init.duplex).toBeUndefined();
  });
});

describe("proxyMcpToBackend — response streaming", () => {
  it("pipes the backend body stream through verbatim", async () => {
    const stream = new ReadableStream<Uint8Array>({
      start(controller) {
        controller.enqueue(new TextEncoder().encode("event: message\n"));
        controller.enqueue(new TextEncoder().encode("data: {}\n\n"));
        controller.close();
      },
    });
    mockBackend({
      body: stream,
      headers: { "content-type": "text/event-stream" },
    });
    const res = await proxyMcpToBackend(makeRequest("mcp"));
    expect(res.headers.get("content-type")).toBe("text/event-stream");
    expect(await res.text()).toBe("event: message\ndata: {}\n\n");
  });

  it("preserves status and the mcp-session-id response header", async () => {
    mockBackend({
      status: 200,
      headers: {
        "content-type": "application/json",
        "mcp-session-id": "sess-xyz",
      },
    });
    const res = await proxyMcpToBackend(
      makeRequest("mcp", { method: "POST", body: "{}" }),
    );
    expect(res.status).toBe(200);
    expect(res.headers.get("mcp-session-id")).toBe("sess-xyz");
  });

  it("passes through a 401 from the auth middleware", async () => {
    mockBackend({
      status: 401,
      body: JSON.stringify({
        ok: false,
        error: { code: "UNAUTHORIZED", message: "API key required" },
      }),
    });
    const res = await proxyMcpToBackend(
      makeRequest("mcp", { method: "POST", body: "{}" }),
    );
    expect(res.status).toBe(401);
    expect(JSON.parse(await res.text()).error.code).toBe("UNAUTHORIZED");
  });
});
