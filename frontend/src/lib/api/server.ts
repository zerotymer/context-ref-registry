import { ApiError } from "./client";

const BACKEND = process.env.BACKEND_API_URL ?? "http://localhost:8000";

export async function backendFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${BACKEND}${path}`, {
    headers: { "Content-Type": "application/json", ...init?.headers },
    cache: "no-store",
    ...init,
  });
  const body = await res.json();
  if (!body.ok) {
    throw new ApiError(
      body.error?.code ?? "UNKNOWN",
      body.error?.message ?? "Unknown error",
      res.status,
    );
  }
  return body.data as T;
}
