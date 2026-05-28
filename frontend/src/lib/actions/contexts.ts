"use server";

import { backendFetch } from "@/lib/api/server";
import type { ContextRead, ContextCreate } from "@/types/api";

export async function getContexts(entityId: string): Promise<ContextRead[]> {
  return backendFetch(`/entities/${entityId}/contexts`);
}

export async function addContext(entityId: string, body: ContextCreate): Promise<ContextRead> {
  return backendFetch(`/entities/${entityId}/contexts`, {
    method: "POST",
    body: JSON.stringify(body),
  });
}
