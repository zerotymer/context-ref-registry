"use server";

import { backendFetch } from "@/lib/api/server";
import type { EntityRead, EntityListResponse, EntityCreate, EntityUpdate } from "@/types/api";

export async function getEntities(qs: string): Promise<EntityListResponse> {
  return backendFetch(`/entities${qs ? `?${qs}` : ""}`);
}

export async function getEntity(id: string): Promise<EntityRead> {
  return backendFetch(`/entities/${id}`);
}

export async function createEntity(body: EntityCreate): Promise<{ id: string }> {
  return backendFetch("/entities", { method: "POST", body: JSON.stringify(body) });
}

export async function updateEntity(id: string, body: EntityUpdate): Promise<EntityRead> {
  return backendFetch(`/entities/${id}`, { method: "PATCH", body: JSON.stringify(body) });
}
