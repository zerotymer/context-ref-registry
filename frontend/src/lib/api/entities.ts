import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { apiFetch } from "./client";
import type {
  EntityRead,
  EntityListResponse,
  EntityCreate,
  EntityUpdate,
  EntityStatus,
  EntityType,
} from "@/types/api";

interface ListParams {
  status?: EntityStatus;
  types?: EntityType[];
  limit?: number;
  offset?: number;
  sort?: "created_at" | "updated_at" | "canonical_name";
  order?: "asc" | "desc";
}

function buildListQs(params: ListParams): string {
  const qs = new URLSearchParams();
  if (params.status) qs.set("status", params.status);
  if (params.types?.length) params.types.forEach((t) => qs.append("types", t));
  if (params.limit !== undefined) qs.set("limit", String(params.limit));
  if (params.offset !== undefined) qs.set("offset", String(params.offset));
  if (params.sort) qs.set("sort", params.sort);
  if (params.order) qs.set("order", params.order);
  return qs.toString() ? `?${qs}` : "";
}

export function useEntities(params: ListParams = {}) {
  return useQuery({
    queryKey: ["entities", params],
    queryFn: () =>
      apiFetch<EntityListResponse>(`/entities${buildListQs(params)}`),
  });
}

export function useEntity(id: string | null) {
  return useQuery({
    queryKey: ["entity", id],
    queryFn: () => apiFetch<EntityRead>(`/entities/${id}`),
    enabled: !!id,
  });
}

export function useCreateEntity() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (body: EntityCreate) =>
      apiFetch<{ id: string }>("/entities", {
        method: "POST",
        body: JSON.stringify(body),
      }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["entities"] }),
  });
}

export function useUpdateEntity(id: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (body: EntityUpdate) =>
      apiFetch<EntityRead>(`/entities/${id}`, {
        method: "PATCH",
        body: JSON.stringify(body),
      }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["entity", id] });
      qc.invalidateQueries({ queryKey: ["entities"] });
    },
  });
}
