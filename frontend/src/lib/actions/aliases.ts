"use server";

import { backendFetch } from "@/lib/api/server";
import type { AliasRead, AliasCreate } from "@/types/api";

export async function getAliases(entityId: string): Promise<AliasRead[]> {
  return backendFetch(`/entities/${entityId}/aliases`);
}

export async function addAlias(entityId: string, body: AliasCreate): Promise<AliasRead> {
  return backendFetch(`/entities/${entityId}/aliases`, {
    method: "POST",
    body: JSON.stringify(body),
  });
}
