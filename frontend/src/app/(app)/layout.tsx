import { redirect } from "next/navigation";
import { AppLayout } from "@/components/layout/AppLayout";
import { getCurrentUser } from "@/lib/actions/auth";

export default async function AuthenticatedLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const user = await getCurrentUser();
  if (!user) {
    redirect("/login");
  }

  return <AppLayout user={user}>{children}</AppLayout>;
}
