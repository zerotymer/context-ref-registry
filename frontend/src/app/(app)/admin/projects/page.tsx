import { redirect } from "next/navigation";
import { getCurrentUser } from "@/lib/actions/auth";
import { listAdminProjects } from "@/lib/actions/admin";
import { ProjectsTable } from "./ProjectsTable";

export default async function AdminProjectsPage({
  searchParams,
}: {
  searchParams?: { is_active?: string; search?: string };
}) {
  const me = await getCurrentUser();
  if (!me || (me.role !== "admin" && me.role !== "project_admin")) redirect("/");

  const params: { is_active?: boolean; search?: string } = {};
  if (searchParams?.is_active !== undefined) {
    params.is_active = searchParams.is_active === "true";
  }
  if (searchParams?.search) params.search = searchParams.search;

  const projects = await listAdminProjects(params);

  return (
    <>
      <header className="bg-white border-b border-gray-200 px-6 py-3 flex items-center justify-between shrink-0">
        <h1 className="font-semibold text-gray-900">프로젝트 관리</h1>
      </header>
      <ProjectsTable projects={projects} isAdmin={me.role === "admin"} currentFilters={searchParams} />
    </>
  );
}
