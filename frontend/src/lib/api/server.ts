import { cookies } from "next/headers";
import { ApiError } from "./client";

const BACKEND = process.env.BACKEND_API_URL ?? "http://localhost:8000";

export async function backendFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const cookieStore = cookies();
  const token = cookieStore.get("access_token")?.value;

  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(init?.headers as Record<string, string>),
  };
  if (token) {
    headers["Cookie"] = `access_token=${token}`;
  }

  const res = await fetch(`${BACKEND}${path}`, {
    ...init,
    headers,
    cache: "no-store",
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
