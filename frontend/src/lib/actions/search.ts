"use server";

import { backendFetch } from "@/lib/api/server";
import type { SearchResult, EntityType } from "@/types/api";

export async function searchEntities(
  q: string,
  types?: EntityType[],
  limit = 20,
): Promise<SearchResult[]> {
  const qs = new URLSearchParams({ q, limit: String(limit) });
  if (types?.length) types.forEach((t) => qs.append("types", t));
  return backendFetch(`/search?${qs}`);
}
