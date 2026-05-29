import { Sidebar } from "./Sidebar";
import { getEntities } from "@/lib/actions/entities";
import type { UserRead } from "@/lib/actions/auth";

export async function AppLayout({
  children,
  user,
}: {
  children: React.ReactNode;
  user: UserRead;
}) {
  const data = await getEntities("status=candidate&limit=1");
  const candidateCount = data.total;

  return (
    <div className="flex h-screen overflow-hidden">
      <Sidebar candidateCount={candidateCount} user={user} />
      <div className="flex-1 flex flex-col overflow-hidden">{children}</div>
    </div>
  );
}
