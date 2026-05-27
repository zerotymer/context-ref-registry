"use client";

import { Sidebar } from "./Sidebar";
import { useEntities } from "@/lib/api/entities";

export function AppLayout({ children }: { children: React.ReactNode }) {
  const { data } = useEntities({ status: "candidate", limit: 1 });
  const candidateCount = data?.total ?? 0;

  return (
    <div className="flex h-screen overflow-hidden">
      <Sidebar candidateCount={candidateCount} />
      <div className="flex-1 flex flex-col overflow-hidden">{children}</div>
    </div>
  );
}
