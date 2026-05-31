import { redirect } from "next/navigation";
import { getCurrentUser } from "@/lib/actions/auth";
import { listMyApiKeys, listMyProjects } from "@/lib/actions/api-keys";
import { ApiKeyPanel } from "./ApiKeyPanel";

export default async function ApiKeysSettingsPage() {
  const me = await getCurrentUser();
  if (!me) redirect("/login");

  const [keys, projects] = await Promise.all([listMyApiKeys(), listMyProjects()]);

  return (
    <>
      <header className="bg-white border-b border-gray-200 px-6 py-3 flex items-center justify-between shrink-0">
        <h1 className="font-semibold text-gray-900">API 설정</h1>
      </header>
      <ApiKeyPanel initialKeys={keys} projects={projects} />
    </>
  );
}
