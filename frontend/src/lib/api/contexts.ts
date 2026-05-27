import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { apiFetch } from "./client";
import type { ContextRead, ContextCreate } from "@/types/api";

export function useContexts(entityId: string | null) {
  return useQuery({
    queryKey: ["contexts", entityId],
    queryFn: () => apiFetch<ContextRead[]>(`/entities/${entityId}/contexts`),
    enabled: !!entityId,
  });
}

export function useAddContext(entityId: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (body: ContextCreate) =>
      apiFetch<ContextRead>(`/entities/${entityId}/contexts`, {
        method: "POST",
        body: JSON.stringify(body),
      }),
    onSuccess: () =>
      qc.invalidateQueries({ queryKey: ["contexts", entityId] }),
  });
}
