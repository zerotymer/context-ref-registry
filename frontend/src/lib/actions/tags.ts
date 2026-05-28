"use server";

import { backendFetch } from "@/lib/api/server";

export async function addTag(entityId: string, tag: string): Promise<void> {
  await backendFetch(`/entities/${entityId}/tags`, {
    method: "POST",
    body: JSON.stringify({ tag }),
  });
}

export async function deleteTag(entityId: string, tag: string): Promise<void> {
  await backendFetch(`/entities/${entityId}/tags/${encodeURIComponent(tag)}`, {
    method: "DELETE",
  });
}
