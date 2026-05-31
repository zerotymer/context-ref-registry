"use client";

import { useState, useTransition } from "react";
import { useRouter } from "next/navigation";
import { loginAction } from "@/lib/actions/auth";

export function LoginForm() {
  const router = useRouter();
  const [pending, startTransition] = useTransition();
  const [loginId, setLoginId] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<{ code: string; message: string } | null>(null);

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    startTransition(async () => {
      try {
        const user = await loginAction(loginId, password);
        if (user.must_change_password) {
          router.push("/change-password");
        } else {
          router.push("/");
        }
        router.refresh();
      } catch (err: unknown) {
        const msg = err instanceof Error ? err.message : "로그인에 실패했습니다.";
        const [code, ...rest] = msg.split(":");
        const message = rest.join(":") || msg;
        if (code === "UNAUTHORIZED" && message.toLowerCase().includes("inactive")) {
          setError({ code: "INACTIVE", message: "비활성화된 계정입니다. 관리자에게 문의하세요." });
        } else {
          setError({ code: code || "ERROR", message: "아이디 또는 비밀번호가 올바르지 않습니다." });
        }
      }
    });
  }

  return (
    <div className="bg-white rounded-lg border border-gray-200 shadow-sm px-8 py-8">
      <h2 className="text-sm font-semibold text-gray-800 mb-6">로그인</h2>

      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label className="block text-xs font-medium text-gray-600 mb-1.5">아이디</label>
          <input
            type="text"
            value={loginId}
            onChange={(e) => setLoginId(e.target.value)}
            placeholder="admin"
            required
            className="w-full border border-gray-200 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-1 focus:ring-indigo-400"
          />
        </div>
        <div>
          <label className="block text-xs font-medium text-gray-600 mb-1.5">비밀번호</label>
          <input
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
            className="w-full border border-gray-200 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-1 focus:ring-indigo-400"
          />
        </div>

        {error && error.code === "INACTIVE" && (
          <div className="bg-amber-50 border border-amber-200 rounded-md px-3 py-2 text-xs text-amber-700">
            {error.message}
          </div>
        )}
        {error && error.code !== "INACTIVE" && (
          <div className="bg-red-50 border border-red-200 rounded-md px-3 py-2 text-xs text-red-700">
            {error.message}
          </div>
        )}

        <button
          type="submit"
          disabled={pending}
          className="w-full bg-indigo-600 text-white text-sm font-medium py-2 rounded-md hover:bg-indigo-700 mt-2 disabled:opacity-60 disabled:cursor-not-allowed"
        >
          {pending ? "로그인 중..." : "로그인"}
        </button>
      </form>
    </div>
  );
}
