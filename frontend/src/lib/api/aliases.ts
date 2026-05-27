import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { apiFetch } from "./client";
import type { AliasRead, AliasCreate } from "@/types/api";

export function useAliases(entityId: string | null) {
  return useQuery({
    queryKey: ["aliases", entityId],
    queryFn: () => apiFetch<AliasRead[]>(`/entities/${entityId}/aliases`),
    enabled: !!entityId,
  });
}

export function useAddAlias(entityId: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (body: AliasCreate) =>
      apiFetch<AliasRead>(`/entities/${entityId}/aliases`, {
        method: "POST",
        body: JSON.stringify(body),
      }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["aliases", entityId] }),
  });
}
