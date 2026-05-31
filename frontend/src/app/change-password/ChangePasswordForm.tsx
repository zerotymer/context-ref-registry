"use client";

import { useState, useTransition } from "react";
import { useRouter } from "next/navigation";
import { changePasswordAction } from "@/lib/actions/auth";

export function ChangePasswordForm({ isForced }: { isForced?: boolean }) {
  const router = useRouter();
  const [pending, startTransition] = useTransition();
  const [currentPassword, setCurrentPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [error, setError] = useState<string | null>(null);

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);

    if (newPassword !== confirmPassword) {
      setError("새 비밀번호와 확인 비밀번호가 일치하지 않습니다.");
      return;
    }
    if (newPassword.length < 4) {
      setError("비밀번호는 4자 이상이어야 합니다.");
      return;
    }

    startTransition(async () => {
      try {
        await changePasswordAction(currentPassword, newPassword);
        router.push("/");
        router.refresh();
      } catch (err: unknown) {
        const msg = err instanceof Error ? err.message : "비밀번호 변경에 실패했습니다.";
        const parts = msg.split(":");
        if (parts[0] === "UNAUTHORIZED") {
          setError("현재 비밀번호가 올바르지 않습니다.");
        } else {
          setError(parts.slice(1).join(":") || msg);
        }
      }
    });
  }

  return (
    <div className="bg-white rounded-lg border border-gray-200 shadow-sm px-8 py-8 w-full max-w-sm">
      <h2 className="text-sm font-semibold text-gray-800 mb-2">비밀번호 변경</h2>
      {isForced && (
        <p className="text-xs text-amber-600 bg-amber-50 border border-amber-200 rounded-md px-3 py-2 mb-4">
          초기 비밀번호를 사용 중입니다. 보안을 위해 비밀번호를 변경해주세요.
        </p>
      )}

      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label className="block text-xs font-medium text-gray-600 mb-1.5">현재 비밀번호</label>
          <input
            type="password"
            value={currentPassword}
            onChange={(e) => setCurrentPassword(e.target.value)}
            required
            className="w-full border border-gray-200 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-1 focus:ring-indigo-400"
          />
        </div>
        <div>
          <label className="block text-xs font-medium text-gray-600 mb-1.5">새 비밀번호</label>
          <input
            type="password"
            value={newPassword}
            onChange={(e) => setNewPassword(e.target.value)}
            required
            className="w-full border border-gray-200 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-1 focus:ring-indigo-400"
          />
        </div>
        <div>
          <label className="block text-xs font-medium text-gray-600 mb-1.5">새 비밀번호 확인</label>
          <input
            type="password"
            value={confirmPassword}
            onChange={(e) => setConfirmPassword(e.target.value)}
            required
            className="w-full border border-gray-200 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-1 focus:ring-indigo-400"
          />
        </div>

        {error && (
          <div className="bg-red-50 border border-red-200 rounded-md px-3 py-2 text-xs text-red-700">
            {error}
          </div>
        )}

        <button
          type="submit"
          disabled={pending}
          className="w-full bg-indigo-600 text-white text-sm font-medium py-2 rounded-md hover:bg-indigo-700 mt-2 disabled:opacity-60 disabled:cursor-not-allowed"
        >
          {pending ? "변경 중..." : "비밀번호 변경"}
        </button>
      </form>
    </div>
  );
}
