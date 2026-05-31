"use client";

import { useState, useTransition } from "react";
import { useRouter } from "next/navigation";
import { cn } from "@/lib/utils";
import {
  createApiKey,
  revokeApiKey,
  type ApiKeyItem,
  type ApiKeyCreated,
  type ProjectOption,
} from "@/lib/actions/api-keys";

const VALID_SCOPES = [
  { value: "read:entities", label: "read:entities — Entity/Alias/Context/Relation 읽기" },
  { value: "write:entities", label: "write:entities — Entity 생성·수정" },
  { value: "ingest", label: "ingest — POST /ingest/batch" },
  { value: "read:all", label: "read:all — 전체 읽기 (superscope)" },
];

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

function LegacyBadge() {
  return (
    <span className="px-2 py-0.5 rounded-full text-xs font-medium bg-yellow-50 text-yellow-700 border border-yellow-200">
      ⚠️ 접근 제한
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
  const [scopes, setScopes] = useState<string[]>([]);
  const [projectId, setProjectId] = useState("");

  function toggleScope(scope: string) {
    setScopes((prev) =>
      prev.includes(scope) ? prev.filter((s) => s !== scope) : [...prev, scope],
    );
  }

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!projectId) {
      setError("프로젝트를 선택해주세요.");
      return;
    }
    if (scopes.length === 0) {
      setError("스코프를 하나 이상 선택해주세요.");
      return;
    }
    setError("");
    startTransition(async () => {
      try {
        const result = await createApiKey({ name, scopes, project_id: projectId });
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
        <h3 className="font-semibold text-gray-900 mb-4">새 API Key 발급</h3>
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
            <label className="block text-xs font-medium text-gray-600 mb-1">
              프로젝트 <span className="text-red-500">*</span>
            </label>
            <select
              required
              value={projectId}
              onChange={(e) => setProjectId(e.target.value)}
              className="w-full border border-gray-200 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-1 focus:ring-indigo-400"
            >
              <option value="">프로젝트를 선택하세요</option>
              {projects.map((p) => (
                <option key={p.id} value={p.id}>{p.name}</option>
              ))}
            </select>
            {projects.length === 0 && (
              <p className="text-xs text-amber-600 mt-1">가입된 프로젝트가 없습니다. 먼저 프로젝트에 참여하세요.</p>
            )}
          </div>
          <div>
            <label className="block text-xs font-medium text-gray-600 mb-2">스코프</label>
            <div className="space-y-2">
              {VALID_SCOPES.map((s) => (
                <label key={s.value} className="flex items-start gap-2 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={scopes.includes(s.value)}
                    onChange={() => toggleScope(s.value)}
                    className="mt-0.5 h-4 w-4 rounded border-gray-300 text-indigo-600 focus:ring-indigo-500"
                  />
                  <span className="text-xs text-gray-700">{s.label}</span>
                </label>
              ))}
            </div>
          </div>
          {error && <p className="text-xs text-red-500">{error}</p>}
          <div className="flex gap-2 pt-1">
            <button
              type="submit"
              disabled={pending}
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

export function ApiKeyPanel({
  initialKeys,
  projects,
}: {
  initialKeys: ApiKeyItem[];
  projects: ProjectOption[];
}) {
  const router = useRouter();
  const [keys, setKeys] = useState<ApiKeyItem[]>(initialKeys);
  const [showCreate, setShowCreate] = useState(false);
  const [revealed, setRevealed] = useState<ApiKeyCreated | null>(null);
  const [revoking, startRevoke] = useTransition();

  const hasLegacyKeys = keys.some((k) => k.is_legacy && k.is_active);

  function handleRevoke(id: string, name: string) {
    if (!confirm(`"${name}" 키를 폐기하시겠습니까? 이 작업은 되돌릴 수 없습니다.`)) return;
    startRevoke(async () => {
      await revokeApiKey(id);
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
      {hasLegacyKeys && (
        <div className="mb-4 p-3 bg-yellow-50 border border-yellow-200 rounded-lg text-sm text-yellow-800">
          ⚠️ 프로젝트가 지정되지 않은 키는 더 이상 접근이 허용되지 않습니다. 해당 키를 폐기하고 재발급하세요.
        </div>
      )}

      <div className="flex items-center justify-between mb-4">
        <h2 className="font-semibold text-gray-900">내 API Key</h2>
        <button
          onClick={() => setShowCreate(true)}
          className="flex items-center gap-1.5 bg-indigo-600 hover:bg-indigo-700 text-white text-sm px-3 py-1.5 rounded-md"
        >
          <span>+</span>
          <span>새 API Key 발급</span>
        </button>
      </div>

      {keys.length === 0 ? (
        <div className="text-sm text-gray-400 py-12 text-center">
          발급된 API Key가 없습니다.
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
                    key.is_legacy && key.is_active && "bg-yellow-50/40",
                  )}
                >
                  <td className="px-4 py-3 font-medium text-gray-800">{key.name}</td>
                  <td className="px-4 py-3">
                    {key.is_legacy ? (
                      <LegacyBadge />
                    ) : (
                      <span className="text-xs text-gray-600">{key.project_name ?? key.project_id ?? "—"}</span>
                    )}
                  </td>
                  <td className="px-4 py-3">
                    <div className="flex flex-wrap gap-1">
                      {key.scopes.map((s) => (
                        <ScopeBadge key={s} scope={s} />
                      ))}
                    </div>
                  </td>
                  <td className="px-4 py-3 text-gray-500 text-xs">
                    {new Date(key.created_at).toLocaleDateString("ko-KR")}
                  </td>
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
