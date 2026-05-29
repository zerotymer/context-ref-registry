"use client";

import { useState, useTransition } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { cn } from "@/lib/utils";
import {
  addProjectMember,
  updateProjectMemberRole,
  removeProjectMember,
  type AdminMember,
  type AdminUser,
} from "@/lib/actions/admin";

function RoleBadge({ role }: { role: string }) {
  const colors: Record<string, string> = {
    project_admin: "bg-indigo-50 text-indigo-600 border-indigo-200",
    member: "bg-gray-50 text-gray-500 border-gray-200",
  };
  return (
    <span className={cn("border px-1.5 py-0.5 rounded-full text-xs font-medium", colors[role] ?? colors.member)}>
      {role}
    </span>
  );
}

function AddMemberModal({
  projectId,
  allUsers,
  existingUserIds,
  onClose,
  onAdded,
}: {
  projectId: string;
  allUsers: AdminUser[];
  existingUserIds: Set<string>;
  onClose: () => void;
  onAdded: () => void;
}) {
  const [pending, startTransition] = useTransition();
  const [userId, setUserId] = useState("");
  const [role, setRole] = useState("member");
  const [error, setError] = useState("");

  const available = allUsers.filter((u) => !existingUserIds.has(u.id) && u.is_active);

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!userId) return;
    setError("");
    startTransition(async () => {
      try {
        await addProjectMember(projectId, { user_id: userId, role });
        onAdded();
        onClose();
      } catch (err: unknown) {
        setError(err instanceof Error ? err.message : "추가에 실패했습니다.");
      }
    });
  }

  return (
    <div className="fixed inset-0 bg-black/30 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-lg w-full max-w-sm p-6">
        <h3 className="font-semibold text-gray-900 mb-4">멤버 추가</h3>
        <form onSubmit={handleSubmit} className="space-y-3">
          <div>
            <label className="block text-xs font-medium text-gray-600 mb-1">사용자</label>
            <select
              required
              value={userId}
              onChange={(e) => setUserId(e.target.value)}
              className="w-full border border-gray-200 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-1 focus:ring-indigo-400"
            >
              <option value="">선택하세요</option>
              {available.map((u) => (
                <option key={u.id} value={u.id}>{u.email}</option>
              ))}
            </select>
          </div>
          <div>
            <label className="block text-xs font-medium text-gray-600 mb-1">역할</label>
            <select
              value={role}
              onChange={(e) => setRole(e.target.value)}
              className="w-full border border-gray-200 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-1 focus:ring-indigo-400"
            >
              <option value="member">member</option>
              <option value="project_admin">project_admin</option>
            </select>
          </div>
          {error && <p className="text-xs text-red-600">{error}</p>}
          <div className="flex justify-end gap-2 pt-2">
            <button type="button" onClick={onClose} className="px-3 py-1.5 text-sm text-gray-600">취소</button>
            <button type="submit" disabled={pending || !userId} className="px-3 py-1.5 bg-indigo-600 text-white text-sm rounded-md disabled:opacity-60">추가</button>
          </div>
        </form>
      </div>
    </div>
  );
}

function MemberRow({
  member,
  projectId,
  isAdmin,
  onRefresh,
}: {
  member: AdminMember;
  projectId: string;
  isAdmin: boolean;
  onRefresh: () => void;
}) {
  const [pending, startTransition] = useTransition();
  const [confirmRemove, setConfirmRemove] = useState(false);

  function handleRoleChange(role: string) {
    startTransition(async () => {
      await updateProjectMemberRole(projectId, member.user_id, role);
      onRefresh();
    });
  }

  function handleRemove() {
    startTransition(async () => {
      await removeProjectMember(projectId, member.user_id);
      onRefresh();
      setConfirmRemove(false);
    });
  }

  return (
    <>
      <tr className={cn("hover:bg-gray-50", !member.is_active && "opacity-60")}>
        <td className="px-6 py-2.5 font-mono text-xs text-gray-600">{member.user_id}</td>
        <td className="px-3 py-2.5">
          {isAdmin ? (
            <select
              value={member.role}
              onChange={(e) => handleRoleChange(e.target.value)}
              disabled={pending || !member.is_active}
              className="border border-gray-200 rounded px-2 py-1 text-xs focus:outline-none focus:ring-1 focus:ring-indigo-400 disabled:opacity-60"
            >
              <option value="member">member</option>
              <option value="project_admin">project_admin</option>
            </select>
          ) : (
            <RoleBadge role={member.role} />
          )}
        </td>
        <td className="px-3 py-2.5">
          {member.is_active ? <span className="text-green-600 text-xs">활성</span> : <span className="text-gray-400 text-xs">비활성</span>}
        </td>
        <td className="px-3 py-2.5 text-right">
          {member.is_active && (
            <button
              onClick={() => setConfirmRemove(true)}
              disabled={pending}
              className="text-xs text-red-500 hover:text-red-700 disabled:opacity-50"
            >
              제거
            </button>
          )}
        </td>
      </tr>
      {confirmRemove && (
        <div className="fixed inset-0 bg-black/30 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg shadow-lg p-6 max-w-xs w-full">
            <p className="text-sm text-gray-800 mb-4">이 멤버를 프로젝트에서 제거하시겠습니까?</p>
            <div className="flex justify-end gap-2">
              <button onClick={() => setConfirmRemove(false)} className="px-3 py-1.5 text-sm text-gray-600">취소</button>
              <button onClick={handleRemove} disabled={pending} className="px-3 py-1.5 bg-red-600 text-white text-sm rounded-md disabled:opacity-60">제거</button>
            </div>
          </div>
        </div>
      )}
    </>
  );
}

export function MembersPanel({
  projectId,
  members,
  allUsers,
  isAdmin,
}: {
  projectId: string;
  members: AdminMember[];
  allUsers: AdminUser[];
  isAdmin: boolean;
}) {
  const router = useRouter();
  const [showAdd, setShowAdd] = useState(false);
  const activeMembers = members.filter((m) => m.is_active);
  const existingUserIds = new Set(activeMembers.map((m) => m.user_id));

  function refresh() {
    router.refresh();
  }

  return (
    <div className="flex-1 flex flex-col overflow-hidden">
      <div className="bg-white border-b border-gray-100 px-6 py-2.5 flex items-center gap-3 shrink-0">
        <div className="text-xs text-gray-400">{activeMembers.length}명의 활성 멤버</div>
        <div className="ml-auto flex gap-2">
          {isAdmin && (
            <button
              onClick={() => setShowAdd(true)}
              className="flex items-center gap-1.5 bg-indigo-600 text-white text-xs px-3 py-1.5 rounded-md hover:bg-indigo-700"
            >
              <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
              </svg>
              멤버 추가
            </button>
          )}
        </div>
      </div>

      <main className="flex-1 overflow-y-auto">
        <table className="w-full text-xs">
          <thead className="bg-gray-50 border-b border-gray-200 sticky top-0">
            <tr className="text-gray-500">
              <th className="text-left px-6 py-2.5 font-medium">사용자 ID</th>
              <th className="text-left px-3 py-2.5 font-medium">역할</th>
              <th className="text-left px-3 py-2.5 font-medium">상태</th>
              <th className="px-3 py-2.5 w-16" />
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100">
            {members.map((member) => (
              <MemberRow
                key={member.user_id}
                member={member}
                projectId={projectId}
                isAdmin={isAdmin}
                onRefresh={refresh}
              />
            ))}
            {members.length === 0 && (
              <tr>
                <td colSpan={4} className="px-6 py-8 text-center text-gray-400">
                  멤버 없음
                </td>
              </tr>
            )}
          </tbody>
        </table>

        <div className="px-6 py-4 border-t border-gray-100 mt-4">
          <div className="text-xs text-gray-500 mb-2">프로젝트 기준 엔티티 필터</div>
          <Link
            href={`/entities?project=${projectId}`}
            className="inline-flex items-center gap-1 text-xs text-indigo-600 hover:underline"
          >
            <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
            </svg>
            Entity 목록에서 {projectId} 프로젝트 엔티티만 보기
          </Link>
        </div>
      </main>

      {showAdd && (
        <AddMemberModal
          projectId={projectId}
          allUsers={allUsers}
          existingUserIds={existingUserIds}
          onClose={() => setShowAdd(false)}
          onAdded={refresh}
        />
      )}
    </div>
  );
}
