"use server";

import { revalidatePath } from "next/cache";
import { backendFetch } from "@/lib/api/server";

export type ApiKeyScope = "read" | "write";

export interface AdminApiKeyItem {
  id: string;
  name: string;
  project_id: string;
  project_name: string | null;
  scope: ApiKeyScope;
  created_at: string;
  expires_at: string | null;
  last_used_at: string | null;
  revoked_at: string | null;
  is_active: boolean;
}

export interface ApiKeyCreated extends AdminApiKeyItem {
  key: string;
}

export interface ProjectOption {
  id: string;
  name: string;
}

export async function listAdminApiKeys(params?: {
  project_id?: string;
  is_active?: boolean;
}): Promise<AdminApiKeyItem[]> {
  const qs = new URLSearchParams();
  if (params?.project_id) qs.set("project_id", params.project_id);
  if (params?.is_active !== undefined) qs.set("is_active", String(params.is_active));
  const q = qs.toString();
  return backendFetch<AdminApiKeyItem[]>(`/admin/api-keys${q ? "?" + q : ""}`);
}

export async function adminCreateApiKey(body: {
  name: string;
  project_id: string;
  scope: ApiKeyScope;
  expires_at?: string | null;
}): Promise<ApiKeyCreated> {
  const result = await backendFetch<ApiKeyCreated>("/admin/api-keys", {
    method: "POST",
    body: JSON.stringify(body),
  });
  revalidatePath("/admin/api-keys");
  return result;
}

export async function adminRevokeApiKey(id: string): Promise<void> {
  await backendFetch(`/admin/api-keys/${id}`, { method: "DELETE" });
  revalidatePath("/admin/api-keys");
}
