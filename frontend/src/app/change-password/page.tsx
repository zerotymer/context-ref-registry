import { redirect } from "next/navigation";
import { getCurrentUser } from "@/lib/actions/auth";
import { ChangePasswordForm } from "./ChangePasswordForm";

export default async function ChangePasswordPage() {
  const user = await getCurrentUser();
  if (!user) {
    redirect("/login");
  }

  return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center">
      <ChangePasswordForm isForced={user.must_change_password} />
    </div>
  );
}
