"use server";

import { revalidatePath } from "next/cache";
import { backendFetch } from "@/lib/api/server";

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

export interface AdminUser {
  id: string;
  email: string;
  display_name: string;
  role: string;
  is_active: boolean;
}

export interface AdminProject {
  id: string;
  alias: string;
  description: string | null;
  is_active: boolean;
}

export interface AdminMember {
  project_id: string;
  user_id: string;
  role: string;
  is_active: boolean;
}

// ---------------------------------------------------------------------------
// User actions
// ---------------------------------------------------------------------------

export async function listAdminUsers(params?: {
  role?: string;
  is_active?: boolean;
  search?: string;
}): Promise<AdminUser[]> {
  const qs = new URLSearchParams();
  if (params?.role) qs.set("role", params.role);
  if (params?.is_active !== undefined) qs.set("is_active", String(params.is_active));
  if (params?.search) qs.set("search", params.search);
  const q = qs.toString();
  return backendFetch<AdminUser[]>(`/admin/users${q ? "?" + q : ""}`);
}

export async function createAdminUser(data: {
  email: string;
  password: string;
  display_name: string;
  role: string;
}): Promise<AdminUser> {
  const user = await backendFetch<AdminUser>("/admin/users", {
    method: "POST",
    body: JSON.stringify(data),
  });
  revalidatePath("/admin/users");
  return user;
}

export async function updateAdminUser(
  userId: string,
  data: { display_name?: string; role?: string; is_active?: boolean },
): Promise<AdminUser> {
  const user = await backendFetch<AdminUser>(`/admin/users/${userId}`, {
    method: "PATCH",
    body: JSON.stringify(data),
  });
  revalidatePath("/admin/users");
  return user;
}

export async function resetAdminUserPassword(userId: string, newPassword: string): Promise<void> {
  await backendFetch(`/admin/users/${userId}/reset-password`, {
    method: "POST",
    body: JSON.stringify({ new_password: newPassword }),
  });
  revalidatePath("/admin/users");
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

// ---------------------------------------------------------------------------
// Member actions
// ---------------------------------------------------------------------------

export async function listProjectMembers(projectId: string): Promise<AdminMember[]> {
  return backendFetch<AdminMember[]>(`/admin/projects/${projectId}/members`);
}

export async function addProjectMember(
  projectId: string,
  data: { user_id: string; role: string },
): Promise<AdminMember> {
  const member = await backendFetch<AdminMember>(`/admin/projects/${projectId}/members`, {
    method: "POST",
    body: JSON.stringify(data),
  });
  revalidatePath(`/admin/projects/${projectId}/members`);
  return member;
}

export async function updateProjectMemberRole(
  projectId: string,
  userId: string,
  role: string,
): Promise<AdminMember> {
  const member = await backendFetch<AdminMember>(`/admin/projects/${projectId}/members/${userId}`, {
    method: "PATCH",
    body: JSON.stringify({ role }),
  });
  revalidatePath(`/admin/projects/${projectId}/members`);
  return member;
}

export async function removeProjectMember(projectId: string, userId: string): Promise<void> {
  await backendFetch(`/admin/projects/${projectId}/members/${userId}`, {
    method: "DELETE",
  });
  revalidatePath(`/admin/projects/${projectId}/members`);
}
