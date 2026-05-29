import { redirect } from "next/navigation";
import { getCurrentUser } from "@/lib/actions/auth";
import { LoginForm } from "./LoginForm";

export default async function LoginPage() {
  const user = await getCurrentUser();
  if (user) redirect("/");

  return (
    <div className="bg-gray-50 min-h-screen flex items-center justify-center">
      <div className="w-full max-w-sm">
        <div className="text-center mb-8">
          <div className="font-semibold text-gray-900 text-lg leading-tight">
            LLM Reference
            <br />
            Registry
          </div>
          <div className="text-xs text-gray-400 mt-1">v0.1.0</div>
        </div>
        <LoginForm />
      </div>
    </div>
  );
}
