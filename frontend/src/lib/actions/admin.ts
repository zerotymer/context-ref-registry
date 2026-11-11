"use server";

import { revalidatePath } from "next/cache";
import { backendFetch } from "@/lib/api/server";

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

export interface AdminProject {
  id: string;
  alias: string;
  description: string | null;
  is_active: boolean;
}

// ---------------------------------------------------------------------------
// Project actions
// ---------------------------------------------------------------------------

export async function listAdminProjects(params?: {
  is_active?: boolean;
  search?: string;
}): Promise<AdminProject[]> {
  const qs = new URLSearchParams();
  if (params?.is_active !== undefined) qs.set("is_active", String(params.is_active));
  if (params?.search) qs.set("search", params.search);
  const q = qs.toString();
  return backendFetch<AdminProject[]>(`/admin/projects${q ? "?" + q : ""}`);
}

export async function createAdminProject(data: {
  id: string;
  alias: string;
  description?: string;
}): Promise<AdminProject> {
  const project = await backendFetch<AdminProject>("/admin/projects", {
    method: "POST",
    body: JSON.stringify(data),
  });
  revalidatePath("/admin/projects");
  return project;
}

export async function updateAdminProject(
  projectId: string,
  data: { alias?: string; description?: string; is_active?: boolean },
): Promise<AdminProject> {
  const project = await backendFetch<AdminProject>(`/admin/projects/${projectId}`, {
    method: "PATCH",
    body: JSON.stringify(data),
  });
  revalidatePath("/admin/projects");
  return project;
}
