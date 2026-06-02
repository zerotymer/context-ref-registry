"use server";

import { backendFetch } from "@/lib/api/server";
import { getCurrentUser } from "@/lib/actions/auth";

export interface ProjectRead {
  id: string;
  alias: string;
  description: string | null;
  is_active: boolean;
}

export async function getMyProjects(): Promise<ProjectRead[]> {
  const user = await getCurrentUser();
  if (!user) return [];

  const endpoint = user.role === "admin" ? "/admin/projects" : "/projects";
  try {
    return await backendFetch<ProjectRead[]>(endpoint);
  } catch {
    return [];
  }
}
