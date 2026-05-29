import { redirect } from "next/navigation";
import { getCurrentUser } from "@/lib/actions/auth";
import { listAdminUsers } from "@/lib/actions/admin";
import { UsersTable } from "./UsersTable";

export default async function AdminUsersPage({
  searchParams,
}: {
  searchParams?: { role?: string; is_active?: string; search?: string };
}) {
  const me = await getCurrentUser();
  if (!me || me.role !== "admin") redirect("/");

  const params: { role?: string; is_active?: boolean; search?: string } = {};
  if (searchParams?.role) params.role = searchParams.role;
  if (searchParams?.is_active !== undefined) {
    params.is_active = searchParams.is_active === "true";
  }
  if (searchParams?.search) params.search = searchParams.search;

  const users = await listAdminUsers(params);

  return (
    <>
      <header className="bg-white border-b border-gray-200 px-6 py-3 flex items-center justify-between shrink-0">
        <h1 className="font-semibold text-gray-900">사용자 관리</h1>
      </header>
      <UsersTable users={users} currentFilters={searchParams} />
    </>
  );
}
