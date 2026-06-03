import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { proxyToBackend } from "./gateway";

const BACKEND = "http://localhost:8000";

type FetchCall = { url: string; init: RequestInit };

let lastCall: FetchCall | null;

function mockBackend(
  response: { status?: number; body?: string; contentType?: string } = {},
) {
  const { status = 200, body = "{}", contentType = "application/json" } =
    response;
  const fetchMock = vi.fn(async (url: string | URL, init?: RequestInit) => {
    lastCall = { url: String(url), init: init ?? {} };
    return new Response(body, {
      status,
      headers: contentType ? { "content-type": contentType } : {},
    });
  });
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

describe("proxyToBackend — header forwarding", () => {
  it("forwards Authorization (Bearer API Key) to the backend", async () => {
    mockBackend();
    await proxyToBackend(
      makeRequest("entities", {
        headers: { Authorization: "Bearer secret-key" },
      }),
      ["entities"],
    );
    const headers = new Headers(lastCall!.init.headers);
    expect(headers.get("authorization")).toBe("Bearer secret-key");
  });

  it("forwards X-API-Key to the backend", async () => {
    mockBackend();
    await proxyToBackend(
      makeRequest("search?q=foo", { headers: { "X-API-Key": "abc123" } }),
      ["search"],
    );
    const headers = new Headers(lastCall!.init.headers);
    expect(headers.get("x-api-key")).toBe("abc123");
  });

  it("does NOT forward Cookie / access_token", async () => {
    mockBackend();
    await proxyToBackend(
      makeRequest("entities", {
        headers: {
          Authorization: "Bearer k",
          Cookie: "access_token=jwt-token",
        },
      }),
      ["entities"],
    );
    const headers = new Headers(lastCall!.init.headers);
    expect(headers.get("cookie")).toBeNull();
  });
});

describe("proxyToBackend — request passthrough", () => {
  it("preserves the query string", async () => {
    mockBackend();
    await proxyToBackend(
      makeRequest("search?q=hello&types=FEATURE&limit=5"),
      ["search"],
    );
    expect(lastCall!.url).toBe(
      `${BACKEND}/search?q=hello&types=FEATURE&limit=5`,
    );
  });

  it("forwards the request body for POST", async () => {
    mockBackend({ status: 201 });
    const payload = JSON.stringify({ name: "x" });
    await proxyToBackend(
      makeRequest("entities", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: payload,
      }),
      ["entities"],
    );
    expect(lastCall!.init.method).toBe("POST");
    expect(lastCall!.init.body).toBe(payload);
  });

  it("does not send a body for GET", async () => {
    mockBackend();
    await proxyToBackend(makeRequest("tags"), ["tags"]);
    expect(lastCall!.init.body).toBeUndefined();
  });
});

describe("proxyToBackend — response passthrough", () => {
  it.each([201, 207, 401, 404])(
    "preserves backend status code %i",
    async (status) => {
      mockBackend({ status });
      const res = await proxyToBackend(
        makeRequest("entities/batch", { method: "POST", body: "[]" }),
        ["entities", "batch"],
      );
      expect(res.status).toBe(status);
    },
  );

  it("preserves content-type for text/plain export", async () => {
    mockBackend({ contentType: "text/plain; charset=utf-8", body: "# AGENTS" });
    const res = await proxyToBackend(
      makeRequest("export/agents-md"),
      ["export", "agents-md"],
    );
    expect(res.headers.get("content-type")).toBe("text/plain; charset=utf-8");
    expect(await res.text()).toBe("# AGENTS");
  });

  it("does not unwrap the OkResponse envelope", async () => {
    const envelope = JSON.stringify({ ok: true, data: { id: "1" } });
    mockBackend({ body: envelope });
    const res = await proxyToBackend(makeRequest("tags"), ["tags"]);
    expect(await res.text()).toBe(envelope);
  });
});

describe("proxyToBackend — allowlist", () => {
  it.each([
    ["auth", ["auth", "login"]],
    ["admin", ["admin", "users"]],
    ["unknown", ["nope"]],
  ])("returns 404 for disallowed prefix %s", async (_label, parts) => {
    const fetchMock = mockBackend();
    const res = await proxyToBackend(makeRequest(parts.join("/")), parts);
    expect(res.status).toBe(404);
    // Disallowed routes must never reach the backend.
    expect(fetchMock).not.toHaveBeenCalled();
  });

  it("allows whitelisted prefixes", async () => {
    const fetchMock = mockBackend();
    const res = await proxyToBackend(makeRequest("projects"), ["projects"]);
    expect(res.status).toBe(200);
    expect(fetchMock).toHaveBeenCalledOnce();
  });
});
