"use client";

import { useState, useTransition } from "react";
import { useRouter } from "next/navigation";
import { cn } from "@/lib/utils";
import {
  adminCreateApiKey,
  adminRevokeApiKey,
  type AdminApiKeyItem,
  type ApiKeyCreated,
  type ApiKeyScope,
  type ProjectOption,
} from "@/lib/actions/api-keys";

function formatDate(value: string | null): string {
  return value ? new Date(value).toLocaleString("ko-KR") : "—";
}

function ScopeBadge({ scope }: { scope: string }) {
  return (
    <span className="inline-flex items-center px-1.5 py-0.5 rounded text-xs font-mono bg-indigo-50 text-indigo-700 border border-indigo-200">
      {scope}
    </span>
  );
}

function StatusBadge({ isActive }: { isActive: boolean }) {
  return (
    <span
      className={cn(
        "px-2 py-0.5 rounded-full text-xs font-medium",
        isActive ? "bg-green-50 text-green-700" : "bg-gray-100 text-gray-400",
      )}
    >
      {isActive ? "활성" : "폐기됨"}
    </span>
  );
}

function KeyRevealModal({
  created,
  onClose,
}: {
  created: ApiKeyCreated;
  onClose: () => void;
}) {
  const [copied, setCopied] = useState(false);

  function handleCopy() {
    navigator.clipboard.writeText(created.key).then(() => {
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    });
  }

  return (
    <div className="fixed inset-0 bg-black/30 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-lg w-full max-w-md p-6">
        <h3 className="font-semibold text-gray-900 mb-1">API Key 발급 완료</h3>
        <p className="text-xs text-amber-600 bg-amber-50 border border-amber-200 rounded px-3 py-2 mb-4">
          이 키는 지금만 표시됩니다. 반드시 복사해 안전한 곳에 보관하세요.
        </p>
        <div className="font-mono text-xs bg-gray-50 border border-gray-200 rounded px-3 py-2 break-all mb-3">
          {created.key}
        </div>
        <div className="flex gap-2">
          <button
            onClick={handleCopy}
            className="flex-1 bg-indigo-600 hover:bg-indigo-700 text-white text-sm px-4 py-2 rounded-md"
          >
            {copied ? "복사됨 ✓" : "복사"}
          </button>
          <button
            onClick={onClose}
            className="flex-1 border border-gray-200 text-gray-700 text-sm px-4 py-2 rounded-md hover:bg-gray-50"
          >
            닫기
          </button>
        </div>
      </div>
    </div>
  );
}

function CreateApiKeyModal({
  projects,
  onClose,
  onCreated,
}: {
  projects: ProjectOption[];
  onClose: () => void;
  onCreated: (result: ApiKeyCreated) => void;
}) {
  const [pending, startTransition] = useTransition();
  const [error, setError] = useState("");
  const [name, setName] = useState("");
  const [scope, setScope] = useState<ApiKeyScope>("read");
  const [projectId, setProjectId] = useState(projects[0]?.id ?? "");
  const [expiresOn, setExpiresOn] = useState("");

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    startTransition(async () => {
      try {
        const result = await adminCreateApiKey({
          name,
          scope,
          project_id: projectId,
          // End of the chosen day, local time.
          expires_at: expiresOn ? new Date(`${expiresOn}T23:59:59`).toISOString() : null,
        });
        onCreated(result);
        onClose();
      } catch (err: unknown) {
        setError(err instanceof Error ? err.message : "발급에 실패했습니다.");
      }
    });
  }

  return (
    <div className="fixed inset-0 bg-black/30 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-lg w-full max-w-sm p-6">
        <h3 className="font-semibold text-gray-900 mb-4">API Key 발급</h3>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-xs font-medium text-gray-600 mb-1">이름</label>
            <input
              type="text"
              required
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="예: ci-bot, cursor"
              className="w-full border border-gray-200 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-1 focus:ring-indigo-400"
            />
          </div>
          <div>
            <label className="block text-xs font-medium text-gray-600 mb-1">프로젝트</label>
            <select
              required
              value={projectId}
              onChange={(e) => setProjectId(e.target.value)}
              className="w-full border border-gray-200 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-1 focus:ring-indigo-400"
            >
              {projects.length === 0 && <option value="">프로젝트를 먼저 생성하세요</option>}
              {projects.map((p) => (
                <option key={p.id} value={p.id}>{p.name} ({p.id})</option>
              ))}
            </select>
            <p className="text-xs text-gray-400 mt-1">키는 이 프로젝트와 공개 엔티티에만 접근합니다.</p>
          </div>
          <div>
            <label className="block text-xs font-medium text-gray-600 mb-2">스코프</label>
            <div className="flex gap-4">
              {(["read", "write"] as const).map((s) => (
                <label key={s} className="flex items-center gap-2 cursor-pointer">
                  <input
                    type="radio"
                    name="scope"
                    checked={scope === s}
                    onChange={() => setScope(s)}
                    className="h-4 w-4 border-gray-300 text-indigo-600 focus:ring-indigo-500"
                  />
                  <span className="text-xs font-mono text-gray-700">{s}</span>
                </label>
              ))}
            </div>
            <p className="text-xs text-gray-400 mt-1">read: 조회·MCP / write: 조회 + 프로젝트 엔티티 변경·ingest</p>
          </div>
          <div>
            <label className="block text-xs font-medium text-gray-600 mb-1">만료일 (선택)</label>
            <input
              type="date"
              value={expiresOn}
              onChange={(e) => setExpiresOn(e.target.value)}
              className="w-full border border-gray-200 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-1 focus:ring-indigo-400"
            />
          </div>
          {error && <p className="text-xs text-red-500">{error}</p>}
          <div className="flex gap-2 pt-1">
            <button
              type="submit"
              disabled={pending || !projectId}
              className="flex-1 bg-indigo-600 hover:bg-indigo-700 disabled:opacity-50 text-white text-sm px-4 py-2 rounded-md"
            >
              {pending ? "발급 중…" : "발급"}
            </button>
            <button
              type="button"
              onClick={onClose}
              className="flex-1 border border-gray-200 text-gray-700 text-sm px-4 py-2 rounded-md hover:bg-gray-50"
            >
              취소
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

interface AdminApiKeyPanelProps {
  initialKeys: AdminApiKeyItem[];
  projects: ProjectOption[];
  currentFilters?: { project_id?: string; is_active?: string };
}

export function AdminApiKeyPanel({ initialKeys, projects, currentFilters }: AdminApiKeyPanelProps) {
  const router = useRouter();
  const [keys, setKeys] = useState<AdminApiKeyItem[]>(initialKeys);
  const [showCreate, setShowCreate] = useState(false);
  const [revealed, setRevealed] = useState<ApiKeyCreated | null>(null);
  const [revoking, startRevoke] = useTransition();

  function applyFilters(params: { project_id?: string; is_active?: string }) {
    const qs = new URLSearchParams();
    if (params.project_id) qs.set("project_id", params.project_id);
    if (params.is_active !== undefined) qs.set("is_active", params.is_active);
    router.push(`/admin/api-keys${qs.toString() ? "?" + qs.toString() : ""}`);
  }

  function handleRevoke(id: string, name: string) {
    if (!confirm(`"${name}" 키를 폐기하시겠습니까?`)) return;
    startRevoke(async () => {
      await adminRevokeApiKey(id);
      setKeys((prev) =>
        prev.map((k) => (k.id === id ? { ...k, is_active: false, revoked_at: new Date().toISOString() } : k)),
      );
    });
  }

  function handleCreated(result: ApiKeyCreated) {
    router.refresh();
    setRevealed(result);
  }


  return (
    <div className="flex-1 overflow-auto p-6">
      <div className="flex items-center justify-between mb-4">
        <h2 className="font-semibold text-gray-900">전체 API Key 목록</h2>
        <button
          onClick={() => setShowCreate(true)}
          className="flex items-center gap-1.5 bg-indigo-600 hover:bg-indigo-700 text-white text-sm px-3 py-1.5 rounded-md"
        >
          <span>+</span>
          <span>키 발급</span>
        </button>
      </div>

      {/* Filters */}
      <div className="flex gap-3 mb-4">
        <select
          value={currentFilters?.project_id ?? ""}
          onChange={(e) =>
            applyFilters({ project_id: e.target.value || undefined, is_active: currentFilters?.is_active })
          }
          className="border border-gray-200 rounded-md px-3 py-1.5 text-sm focus:outline-none focus:ring-1 focus:ring-indigo-400"
        >
          <option value="">모든 프로젝트</option>
          {projects.map((p) => (
            <option key={p.id} value={p.id}>{p.name} ({p.id})</option>
          ))}
        </select>
        <select
          value={currentFilters?.is_active ?? ""}
          onChange={(e) =>
            applyFilters({ project_id: currentFilters?.project_id, is_active: e.target.value || undefined })
          }
          className="border border-gray-200 rounded-md px-3 py-1.5 text-sm focus:outline-none focus:ring-1 focus:ring-indigo-400"
        >
          <option value="">전체</option>
          <option value="true">활성</option>
          <option value="false">폐기됨</option>
        </select>
      </div>

      {keys.length === 0 ? (
        <div className="text-sm text-gray-400 py-12 text-center">
          조회된 API Key가 없습니다.
        </div>
      ) : (
        <div className="border border-gray-200 rounded-lg overflow-hidden">
          <table className="w-full text-sm">
            <thead>
              <tr className="bg-gray-50 text-xs font-medium text-gray-500 border-b border-gray-200">
                <th className="text-left px-4 py-2.5">이름</th>
                <th className="text-left px-4 py-2.5">프로젝트</th>
                <th className="text-left px-4 py-2.5">스코프</th>
                <th className="text-left px-4 py-2.5">생성일</th>
                <th className="text-left px-4 py-2.5">만료일</th>
                <th className="text-left px-4 py-2.5">마지막 사용</th>
                <th className="text-left px-4 py-2.5">상태</th>
                <th className="text-left px-4 py-2.5">액션</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {keys.map((key) => (
                <tr
                  key={key.id}
                  className={cn(
                    "hover:bg-gray-50",
                    !key.is_active && "opacity-50",
                  )}
                >
                  <td className="px-4 py-3 font-medium text-gray-800">{key.name}</td>
                  <td className="px-4 py-3 text-xs text-gray-600">{key.project_name ?? key.project_id}</td>
                  <td className="px-4 py-3">
                    <ScopeBadge scope={key.scope} />
                  </td>
                  <td className="px-4 py-3 text-gray-500 text-xs">
                    {new Date(key.created_at).toLocaleDateString("ko-KR")}
                  </td>
                  <td className="px-4 py-3 text-gray-500 text-xs">{formatDate(key.expires_at)}</td>
                  <td className="px-4 py-3 text-gray-500 text-xs">{formatDate(key.last_used_at)}</td>
                  <td className="px-4 py-3">
                    <StatusBadge isActive={key.is_active} />
                  </td>
                  <td className="px-4 py-3">
                    {key.is_active && (
                      <button
                        onClick={() => handleRevoke(key.id, key.name)}
                        disabled={revoking}
                        className="text-xs text-red-500 hover:text-red-700 disabled:opacity-50"
                      >
                        폐기
                      </button>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {showCreate && (
        <CreateApiKeyModal
          projects={projects}
          onClose={() => setShowCreate(false)}
          onCreated={handleCreated}
        />
      )}

      {revealed && (
        <KeyRevealModal
          created={revealed}
          onClose={() => setRevealed(null)}
        />
      )}
    </div>
  );
}
