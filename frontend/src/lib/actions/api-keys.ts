"use server";

import { revalidatePath } from "next/cache";
import { backendFetch } from "@/lib/api/server";

export interface ApiKeyItem {
  id: string;
  name: string;
  scopes: string[];
  project_id: string | null;
  created_at: string;
  revoked_at: string | null;
  is_active: boolean;
}

export interface AdminApiKeyItem extends ApiKeyItem {
  created_by_email: string | null;
}

export interface ApiKeyCreated {
  id: string;
  name: string;
  scopes: string[];
  key: string;
}

export async function listMyApiKeys(): Promise<ApiKeyItem[]> {
  return backendFetch<ApiKeyItem[]>("/auth/api-keys");
}

export async function createApiKey(body: {
  name: string;
  scopes: string[];
  project_id?: string | null;
}): Promise<ApiKeyCreated> {
  const result = await backendFetch<ApiKeyCreated>("/auth/api-keys", {
    method: "POST",
    body: JSON.stringify(body),
  });
  revalidatePath("/settings/api-keys");
  return result;
}

export async function revokeApiKey(id: string): Promise<void> {
  await backendFetch(`/auth/api-keys/${id}`, { method: "DELETE" });
  revalidatePath("/settings/api-keys");
}

export async function listAdminApiKeys(params?: {
  search?: string;
  is_active?: boolean;
}): Promise<AdminApiKeyItem[]> {
  const qs = new URLSearchParams();
  if (params?.search) qs.set("search", params.search);
  if (params?.is_active !== undefined) qs.set("is_active", String(params.is_active));
  const q = qs.toString();
  return backendFetch<AdminApiKeyItem[]>(`/admin/api-keys${q ? "?" + q : ""}`);
}

export async function adminCreateApiKey(body: {
  name: string;
  scopes: string[];
  project_id?: string | null;
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
