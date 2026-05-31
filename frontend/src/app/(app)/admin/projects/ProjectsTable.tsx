"use client";

import { useState, useTransition } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { cn } from "@/lib/utils";
import { createAdminProject, updateAdminProject, type AdminProject } from "@/lib/actions/admin";

function CreateProjectModal({ onClose, onCreated }: { onClose: () => void; onCreated: () => void }) {
  const [pending, startTransition] = useTransition();
  const [error, setError] = useState("");
  const [form, setForm] = useState({ id: "", alias: "", description: "" });

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    if (!/^[A-Za-z0-9_]{3,50}$/.test(form.id)) {
      setError("프로젝트 ID는 3~50자이며 영문·숫자·언더바(_)만 허용됩니다.");
      return;
    }
    startTransition(async () => {
      try {
        await createAdminProject({ id: form.id, alias: form.alias, description: form.description || undefined });
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
        <h3 className="font-semibold text-gray-900 mb-4">프로젝트 생성</h3>
        <form onSubmit={handleSubmit} className="space-y-3">
          <div>
            <label className="block text-xs font-medium text-gray-600 mb-1">프로젝트 ID</label>
            <input
              required
              value={form.id}
              onChange={(e) => setForm({ ...form, id: e.target.value })}
              placeholder="예: my_project, team_sub_v2"
              className="w-full border border-gray-200 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-1 focus:ring-indigo-400"
            />
          </div>
          <div>
            <label className="block text-xs font-medium text-gray-600 mb-1">이름</label>
            <input
              required
              value={form.alias}
              onChange={(e) => setForm({ ...form, alias: e.target.value })}
              className="w-full border border-gray-200 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-1 focus:ring-indigo-400"
            />
          </div>
          <div>
            <label className="block text-xs font-medium text-gray-600 mb-1">설명 (선택)</label>
            <input
              value={form.description}
              onChange={(e) => setForm({ ...form, description: e.target.value })}
              className="w-full border border-gray-200 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-1 focus:ring-indigo-400"
            />
          </div>
          {error && <p className="text-xs text-red-600">{error}</p>}
          <div className="flex justify-end gap-2 pt-2">
            <button type="button" onClick={onClose} className="px-3 py-1.5 text-sm text-gray-600">취소</button>
            <button type="submit" disabled={pending} className="px-3 py-1.5 bg-indigo-600 text-white text-sm rounded-md disabled:opacity-60">생성</button>
          </div>
        </form>
      </div>
    </div>
  );
}

function ProjectActionMenu({
  project,
  isAdmin,
  onRefresh,
}: {
  project: AdminProject;
  isAdmin: boolean;
  onRefresh: () => void;
}) {
  const [open, setOpen] = useState(false);
  const [showEdit, setShowEdit] = useState(false);
  const [pending, startTransition] = useTransition();

  function toggleActive() {
    setOpen(false);
    startTransition(async () => {
      await updateAdminProject(project.id, { is_active: !project.is_active });
      onRefresh();
    });
  }

  return (
    <div className="relative">
      <button onClick={() => setOpen(!open)} className="p-1 text-gray-400 hover:text-gray-700 rounded">⋮</button>
      {open && (
        <>
          <div className="fixed inset-0 z-10" onClick={() => setOpen(false)} />
          <div className="absolute right-0 mt-1 w-36 bg-white border border-gray-200 rounded-md shadow-lg z-20 text-xs">
            <Link
              href={`/admin/projects/${project.id}/members`}
              className="block px-3 py-2 hover:bg-gray-50"
              onClick={() => setOpen(false)}
            >
              멤버 관리
            </Link>
            {isAdmin && (
              <>
                <button
                  onClick={() => { setOpen(false); setShowEdit(true); }}
                  className="w-full text-left px-3 py-2 hover:bg-gray-50"
                >
                  수정
                </button>
                <button
                  onClick={toggleActive}
                  disabled={pending}
                  className="w-full text-left px-3 py-2 hover:bg-gray-50 text-red-600"
                >
                  {project.is_active ? "비활성화" : "활성화"}
                </button>
              </>
            )}
          </div>
        </>
      )}
      {showEdit && (
        <EditProjectModal
          project={project}
          onClose={() => setShowEdit(false)}
          onDone={onRefresh}
        />
      )}
    </div>
  );
}

function EditProjectModal({
  project,
  onClose,
  onDone,
}: {
  project: AdminProject;
  onClose: () => void;
  onDone: () => void;
}) {
  const [pending, startTransition] = useTransition();
  const [form, setForm] = useState({ alias: project.alias, description: project.description ?? "" });
  const [error, setError] = useState("");

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    startTransition(async () => {
      try {
        await updateAdminProject(project.id, { alias: form.alias, description: form.description || undefined });
        onDone();
        onClose();
      } catch (err: unknown) {
        setError(err instanceof Error ? err.message : "수정에 실패했습니다.");
      }
    });
  }

  return (
    <div className="fixed inset-0 bg-black/30 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-lg w-full max-w-sm p-6">
        <h3 className="font-semibold text-gray-900 mb-4">프로젝트 수정 — {project.id}</h3>
        <form onSubmit={handleSubmit} className="space-y-3">
          <div>
            <label className="block text-xs font-medium text-gray-600 mb-1">이름</label>
            <input
              required
              value={form.alias}
              onChange={(e) => setForm({ ...form, alias: e.target.value })}
              className="w-full border border-gray-200 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-1 focus:ring-indigo-400"
            />
          </div>
          <div>
            <label className="block text-xs font-medium text-gray-600 mb-1">설명</label>
            <input
              value={form.description}
              onChange={(e) => setForm({ ...form, description: e.target.value })}
              className="w-full border border-gray-200 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-1 focus:ring-indigo-400"
            />
          </div>
          {error && <p className="text-xs text-red-600">{error}</p>}
          <div className="flex justify-end gap-2 pt-2">
            <button type="button" onClick={onClose} className="px-3 py-1.5 text-sm text-gray-600">취소</button>
            <button type="submit" disabled={pending} className="px-3 py-1.5 bg-indigo-600 text-white text-sm rounded-md disabled:opacity-60">저장</button>
          </div>
        </form>
      </div>
    </div>
  );
}

export function ProjectsTable({
  projects: initialProjects,
  isAdmin,
  currentFilters,
}: {
  projects: AdminProject[];
  isAdmin: boolean;
  currentFilters?: { is_active?: string; search?: string };
}) {
  const router = useRouter();
  const [showCreate, setShowCreate] = useState(false);
  const [isActive, setIsActive] = useState(currentFilters?.is_active ?? "");
  const [search, setSearch] = useState(currentFilters?.search ?? "");

  function applyFilters() {
    const qs = new URLSearchParams();
    if (isActive !== "") qs.set("is_active", isActive);
    if (search) qs.set("search", search);
    router.push(`/admin/projects?${qs.toString()}`);
  }

  function refresh() {
    router.refresh();
  }

  return (
    <div className="flex-1 flex flex-col overflow-hidden">
      <div className="bg-white border-b border-gray-100 px-6 py-2.5 flex items-center gap-3 shrink-0">
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
          placeholder="프로젝트 검색..."
          className="border border-gray-200 rounded-md px-2.5 py-1.5 text-xs focus:outline-none focus:ring-1 focus:ring-indigo-400 w-40"
        />
        <div className="text-xs text-gray-400 ml-auto">{initialProjects.length}개</div>
        {isAdmin && (
          <button
            onClick={() => setShowCreate(true)}
            className="flex items-center gap-1.5 bg-indigo-600 text-white text-xs px-3 py-1.5 rounded-md hover:bg-indigo-700"
          >
            <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
            </svg>
            프로젝트 생성
          </button>
        )}
      </div>

      <main className="flex-1 overflow-y-auto">
        <table className="w-full text-xs">
          <thead className="bg-gray-50 border-b border-gray-200 sticky top-0">
            <tr className="text-gray-500">
              <th className="text-left px-6 py-2.5 font-medium">ID</th>
              <th className="text-left px-3 py-2.5 font-medium">이름</th>
              <th className="text-left px-3 py-2.5 font-medium">설명</th>
              <th className="text-left px-3 py-2.5 font-medium">상태</th>
              <th className="px-3 py-2.5 w-8" />
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100">
            {initialProjects.map((project) => (
              <tr
                key={project.id}
                className={cn("hover:bg-gray-50", !project.is_active && "opacity-60")}
              >
                <td className="px-6 py-2.5 font-mono font-medium text-gray-800">{project.id}</td>
                <td className="px-3 py-2.5 text-gray-700">{project.alias}</td>
                <td className="px-3 py-2.5 text-gray-500 max-w-xs truncate">{project.description ?? "—"}</td>
                <td className="px-3 py-2.5">
                  {project.is_active ? (
                    <span className="text-green-600">활성</span>
                  ) : (
                    <span className="text-gray-400">비활성</span>
                  )}
                </td>
                <td className="px-3 py-2.5 text-right">
                  <ProjectActionMenu project={project} isAdmin={isAdmin} onRefresh={refresh} />
                </td>
              </tr>
            ))}
            {initialProjects.length === 0 && (
              <tr>
                <td colSpan={5} className="px-6 py-8 text-center text-gray-400">
                  프로젝트 없음
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </main>

      {showCreate && (
        <CreateProjectModal onClose={() => setShowCreate(false)} onCreated={refresh} />
      )}
    </div>
  );
}
