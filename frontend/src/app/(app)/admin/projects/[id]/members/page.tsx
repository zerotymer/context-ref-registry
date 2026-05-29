import Link from "next/link";
import { redirect } from "next/navigation";
import { getCurrentUser } from "@/lib/actions/auth";
import { listProjectMembers, listAdminUsers } from "@/lib/actions/admin";
import { MembersPanel } from "./MembersPanel";

export default async function ProjectMembersPage({ params }: { params: { id: string } }) {
  const me = await getCurrentUser();
  if (!me || (me.role !== "admin" && me.role !== "project_admin")) redirect("/");

  const [members, allUsers] = await Promise.all([
    listProjectMembers(params.id),
    me.role === "admin" ? listAdminUsers() : [],
  ]);

  return (
    <>
      <header className="bg-white border-b border-gray-200 px-6 py-3 flex items-center gap-2 shrink-0">
        <Link href="/admin/projects" className="text-xs text-gray-400 hover:text-gray-700">
          프로젝트 관리
        </Link>
        <span className="text-gray-300">/</span>
        <span className="font-semibold text-gray-900">{params.id}</span>
        <span className="text-gray-300">/</span>
        <span className="text-gray-600">멤버 관리</span>
      </header>
      <MembersPanel
        projectId={params.id}
        members={members}
        allUsers={allUsers}
        isAdmin={me.role === "admin"}
      />
    </>
  );
}
