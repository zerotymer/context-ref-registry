import { useQuery } from "@tanstack/react-query";
import { apiFetch } from "./client";
import type { RelationRead } from "@/types/api";

export function useRelations(entityId: string | null) {
  return useQuery({
    queryKey: ["relations", entityId],
    queryFn: () => apiFetch<RelationRead[]>(`/entities/${entityId}/relations`),
    enabled: !!entityId,
  });
}
