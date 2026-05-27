import { useQuery } from "@tanstack/react-query";
import { apiFetch } from "./client";
import type { SearchResult, EntityType } from "@/types/api";

export function useSearch(
  q: string,
  types?: EntityType[],
  limit = 20,
) {
  const qs = new URLSearchParams({ q, limit: String(limit) });
  if (types?.length) types.forEach((t) => qs.append("types", t));

  return useQuery({
    queryKey: ["search", q, types, limit],
    queryFn: () => apiFetch<SearchResult[]>(`/search?${qs}`),
    enabled: q.length > 0,
  });
}
