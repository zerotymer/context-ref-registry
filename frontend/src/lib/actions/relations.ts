"use server";

import { backendFetch } from "@/lib/api/server";
import type { RelationRead } from "@/types/api";

export async function getRelations(entityId: string): Promise<RelationRead[]> {
  return backendFetch(`/entities/${entityId}/relations`);
}
