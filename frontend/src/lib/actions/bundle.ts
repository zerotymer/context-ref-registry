"use server";

import { backendFetch } from "@/lib/api/server";
import type { ContextBundleRequest, ContextBundleResponse } from "@/types/api";

export async function fetchContextBundle(
  body: ContextBundleRequest,
): Promise<ContextBundleResponse> {
  return backendFetch("/context-bundle", {
    method: "POST",
    body: JSON.stringify(body),
  });
}
