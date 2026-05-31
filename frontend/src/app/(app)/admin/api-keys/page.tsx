import { redirect } from "next/navigation";
import { getCurrentUser } from "@/lib/actions/auth";
import { listAdminApiKeys } from "@/lib/actions/api-keys";
import { AdminApiKeyPanel } from "./AdminApiKeyPanel";

export default async function AdminApiKeysPage({
  searchParams,
}: {
  searchParams?: { search?: string; is_active?: string };
}) {
  const me = await getCurrentUser();
  if (!me || me.role !== "admin") redirect("/");

  const params: { search?: string; is_active?: boolean } = {};
  if (searchParams?.search) params.search = searchParams.search;
  if (searchParams?.is_active !== undefined) {
    params.is_active = searchParams.is_active === "true";
  }

  const keys = await listAdminApiKeys(params);

  return (
    <>
      <header className="bg-white border-b border-gray-200 px-6 py-3 flex items-center justify-between shrink-0">
        <h1 className="font-semibold text-gray-900">API Key 관리</h1>
      </header>
      <AdminApiKeyPanel initialKeys={keys} currentFilters={searchParams} />
    </>
  );
}
