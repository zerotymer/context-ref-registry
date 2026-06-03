"use client";

import { useState, useTransition } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { cn } from "@/lib/utils";
import {
  createAdminUser,
  updateAdminUser,
  resetAdminUserPassword,
  type AdminUser,
} from "@/lib/actions/admin";

function RoleBadge({ role }: { role: string }) {
  const colors: Record<string, string> = {
    admin: "bg-red-50 text-red-600 border-red-200",
    project_admin: "bg-indigo-50 text-indigo-600 border-indigo-200",
    user: "bg-gray-50 text-gray-500 border-gray-200",
  };
  return (
    <span className={cn("border px-1.5 py-0.5 rounded-full text-xs font-medium", colors[role] ?? colors.user)}>
      {role}
    </span>
  );
}

function CreateUserModal({ onClose, onCreated }: { onClose: () => void; onCreated: () => void }) {
  const [pending, startTransition] = useTransition();
  const [error, setError] = useState("");
  const [form, setForm] = useState({ login_id: "", display_name: "", password: "", role: "user" });

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    startTransition(async () => {
      try {
        await createAdminUser(form);
        onCreated();
        onClose();
      } catch (err: unknown) {
        setError(err instanceof Error ? err.message : "생성에 실패했습니다.");
      }
    });
  }

  return (
    <div className="fixed inset-0 bg-black/30 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-lg w-full max-w-sm p-6">
        <h3 className="font-semibold text-gray-900 mb-4">사용자 생성</h3>
        <form onSubmit={handleSubmit} className="space-y-3">
          <div>
            <label className="block text-xs font-medium text-gray-600 mb-1">아이디</label>
            <input
              type="text"
              required
              value={form.login_id}
              onChange={(e) => setForm({ ...form, login_id: e.target.value })}
              className="w-full border border-gray-200 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-1 focus:ring-indigo-400"
            />
          </div>
          <div>
            <label className="block text-xs font-medium text-gray-600 mb-1">이름</label>
            <input
              required
              value={form.display_name}
              onChange={(e) => setForm({ ...form, display_name: e.target.value })}
              className="w-full border border-gray-200 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-1 focus:ring-indigo-400"
            />
          </div>
          <div>
            <label className="block text-xs font-medium text-gray-600 mb-1">역할</label>
            <select
              value={form.role}
              onChange={(e) => setForm({ ...form, role: e.target.value })}
              className="w-full border border-gray-200 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-1 focus:ring-indigo-400"
            >
              <option value="user">user</option>
              <option value="project_admin">project_admin</option>
              <option value="admin">admin</option>
            </select>
          </div>
          <div>
            <label className="block text-xs font-medium text-gray-600 mb-1">초기 비밀번호</label>
            <input
              type="password"
              required
              value={form.password}
              onChange={(e) => setForm({ ...form, password: e.target.value })}
              className="w-full border border-gray-200 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-1 focus:ring-indigo-400"
            />
          </div>
          {error && <p className="text-xs text-red-600">{error}</p>}
          <div className="flex justify-end gap-2 pt-2">
            <button type="button" onClick={onClose} className="px-3 py-1.5 text-sm text-gray-600 hover:text-gray-900">취소</button>
            <button
              type="submit"
              disabled={pending}
              className="px-3 py-1.5 bg-indigo-600 text-white text-sm rounded-md hover:bg-indigo-700 disabled:opacity-60"
            >
              생성
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

function ActionMenu({
  user,
  onRefresh,
}: {
  user: AdminUser;
  onRefresh: () => void;
}) {
  const [open, setOpen] = useState(false);
  const [showReset, setShowReset] = useState(false);
  const [pending, startTransition] = useTransition();

  function deactivate() {
    setOpen(false);
    startTransition(async () => {
      await updateAdminUser(user.id, { is_active: !user.is_active });
      onRefresh();
    });
  }

  function promoteRole(role: string) {
    setOpen(false);
    startTransition(async () => {
      await updateAdminUser(user.id, { role });
      onRefresh();
    });
  }

  return (
    <div className="relative">
      <button
        onClick={() => setOpen(!open)}
        className="p-1 text-gray-400 hover:text-gray-700 rounded"
      >
        ⋮
      </button>
      {open && (
        <>
          <div className="fixed inset-0 z-10" onClick={() => setOpen(false)} />
          <div className="absolute right-0 mt-1 w-44 bg-white border border-gray-200 rounded-md shadow-lg z-20 text-xs">
            {user.role !== "admin" && (
              <button
                onClick={() => promoteRole("admin")}
                disabled={pending}
                className="w-full text-left px-3 py-2 hover:bg-gray-50"
              >
                admin으로 변경
              </button>
            )}
            {user.role !== "project_admin" && (
              <button
                onClick={() => promoteRole("project_admin")}
                disabled={pending}
                className="w-full text-left px-3 py-2 hover:bg-gray-50"
              >
                project_admin으로 변경
              </button>
            )}
            {user.role !== "user" && (
              <button
                onClick={() => promoteRole("user")}
                disabled={pending}
                className="w-full text-left px-3 py-2 hover:bg-gray-50"
              >
                user로 변경
              </button>
            )}
            <button
              onClick={() => { setOpen(false); setShowReset(true); }}
              className="w-full text-left px-3 py-2 hover:bg-gray-50"
            >
              비밀번호 변경
            </button>
            <button
              onClick={deactivate}
              disabled={pending}
              className="w-full text-left px-3 py-2 hover:bg-gray-50 text-red-600"
            >
              {user.is_active ? "비활성화" : "활성화"}
            </button>
          </div>
        </>
      )}
      {showReset && (
        <ResetPasswordModal
          userId={user.id}
          onClose={() => setShowReset(false)}
          onDone={onRefresh}
        />
      )}
    </div>
  );
}

function ResetPasswordModal({
  userId,
  onClose,
  onDone,
}: {
  userId: string;
  onClose: () => void;
  onDone: () => void;
}) {
  const [pending, startTransition] = useTransition();
  const [pw, setPw] = useState("");
  const [error, setError] = useState("");

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    startTransition(async () => {
      try {
        await resetAdminUserPassword(userId, pw);
        onDone();
        onClose();
      } catch (err: unknown) {
        setError(err instanceof Error ? err.message : "비밀번호 변경에 실패했습니다.");
      }
    });
  }

  return (
    <div className="fixed inset-0 bg-black/30 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-lg w-full max-w-sm p-6">
        <h3 className="font-semibold text-gray-900 mb-1 text-base">비밀번호 변경</h3>
        <p className="text-xs text-gray-500 mb-4">사용자의 새 비밀번호를 설정합니다.</p>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-xs font-medium text-gray-700 mb-1.5">새 비밀번호</label>
            <input
              type="password"
              required
              value={pw}
              onChange={(e) => setPw(e.target.value)}
              className="w-full border border-gray-200 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-1 focus:ring-indigo-400"
              placeholder="새 비밀번호 입력"
            />
          </div>
          {error && (
            <div className="bg-red-50 border border-red-200 rounded-md px-3 py-2 text-xs text-red-700">
              {error}
            </div>
          )}
          <div className="flex gap-2 pt-1">
            <button
              type="button"
              onClick={onClose}
              className="flex-1 px-3 py-2 text-sm text-gray-700 bg-gray-100 rounded-md hover:bg-gray-200"
            >
              취소
            </button>
            <button
              type="submit"
              disabled={pending}
              className="flex-1 px-3 py-2 bg-indigo-600 text-white text-sm rounded-md hover:bg-indigo-700 disabled:opacity-60 disabled:cursor-not-allowed"
            >
              {pending ? "변경 중..." : "변경"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

export function UsersTable({
  users: initialUsers,
  currentFilters,
}: {
  users: AdminUser[];
  currentFilters?: { role?: string; is_active?: string; search?: string };
}) {
  const router = useRouter();
  const [showCreate, setShowCreate] = useState(false);
  const [role, setRole] = useState(currentFilters?.role ?? "");
  const [isActive, setIsActive] = useState(currentFilters?.is_active ?? "");
  const [search, setSearch] = useState(currentFilters?.search ?? "");

  function applyFilters() {
    const qs = new URLSearchParams();
    if (role) qs.set("role", role);
    if (isActive !== "") qs.set("is_active", isActive);
    if (search) qs.set("search", search);
    router.push(`/admin/users?${qs.toString()}`);
  }

  function refresh() {
    router.refresh();
  }

  return (
    <div className="flex-1 flex flex-col overflow-hidden">
      <div className="bg-white border-b border-gray-100 px-6 py-2.5 flex items-center gap-3 shrink-0">
        <select
          value={role}
          onChange={(e) => setRole(e.target.value)}
          onBlur={applyFilters}
          className="border border-gray-200 rounded-md text-xs px-2.5 py-1.5 focus:outline-none focus:ring-1 focus:ring-indigo-400"
        >
          <option value="">모든 역할</option>
          <option value="admin">admin</option>
          <option value="project_admin">project_admin</option>
          <option value="user">user</option>
        </select>
        <select
          value={isActive}
          onChange={(e) => setIsActive(e.target.value)}
          onBlur={applyFilters}
          className="border border-gray-200 rounded-md text-xs px-2.5 py-1.5 focus:outline-none focus:ring-1 focus:ring-indigo-400"
        >
          <option value="">모든 상태</option>
          <option value="true">활성</option>
          <option value="false">비활성</option>
        </select>
        <input
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && applyFilters()}
          placeholder="아이디 검색..."
          className="border border-gray-200 rounded-md px-2.5 py-1.5 text-xs focus:outline-none focus:ring-1 focus:ring-indigo-400 w-40"
        />
        <div className="text-xs text-gray-400 ml-auto">{initialUsers.length}명</div>
        <button
          onClick={() => setShowCreate(true)}
          className="flex items-center gap-1.5 bg-indigo-600 text-white text-xs px-3 py-1.5 rounded-md hover:bg-indigo-700"
        >
          <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
          </svg>
          사용자 생성
        </button>
      </div>

      <main className="flex-1 overflow-y-auto">
        <table className="w-full text-xs">
          <thead className="bg-gray-50 border-b border-gray-200 sticky top-0">
            <tr className="text-gray-500">
              <th className="text-left px-6 py-2.5 font-medium">아이디</th>
              <th className="text-left px-3 py-2.5 font-medium">이름</th>
              <th className="text-left px-3 py-2.5 font-medium">역할</th>
              <th className="text-left px-3 py-2.5 font-medium">상태</th>
              <th className="px-3 py-2.5 w-8" />
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100">
            {initialUsers.map((user) => (
              <tr
                key={user.id}
                className={cn("hover:bg-gray-50", !user.is_active && "opacity-60")}
              >
                <td className="px-6 py-2.5 font-medium text-gray-800">
                  {user.login_id}
                  {user.must_change_password && (
                    <span className="ml-1.5 text-amber-500 text-xs">(비밀번호 변경 필요)</span>
                  )}
                </td>
                <td className="px-3 py-2.5 text-gray-600">{user.display_name}</td>
                <td className="px-3 py-2.5">
                  <RoleBadge role={user.role} />
                </td>
                <td className="px-3 py-2.5">
                  {user.is_active ? (
                    <span className="text-green-600">활성</span>
                  ) : (
                    <span className="text-gray-400">비활성</span>
                  )}
                </td>
                <td className="px-3 py-2.5 text-right">
                  <ActionMenu user={user} onRefresh={refresh} />
                </td>
              </tr>
            ))}
            {initialUsers.length === 0 && (
              <tr>
                <td colSpan={5} className="px-6 py-8 text-center text-gray-400">
                  사용자 없음
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </main>

      {showCreate && (
        <CreateUserModal onClose={() => setShowCreate(false)} onCreated={refresh} />
      )}
    </div>
  );
}
