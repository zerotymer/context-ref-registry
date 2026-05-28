import { Sidebar } from "./Sidebar";
import { getEntities } from "@/lib/actions/entities";

export async function AppLayout({ children }: { children: React.ReactNode }) {
  const data = await getEntities("status=candidate&limit=1");
  const candidateCount = data.total;

  return (
    <div className="flex h-screen overflow-hidden">
      <Sidebar candidateCount={candidateCount} />
      <div className="flex-1 flex flex-col overflow-hidden">{children}</div>
    </div>
  );
}
