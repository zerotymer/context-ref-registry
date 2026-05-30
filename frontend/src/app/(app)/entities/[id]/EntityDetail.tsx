"use client";

import { useState, useTransition } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { updateEntity } from "@/lib/actions/entities";
import { addAlias, deactivateAlias } from "@/lib/actions/aliases";
import { addContext } from "@/lib/actions/contexts";
import { addTag, deleteTag } from "@/lib/actions/tags";
import { EntityStatusBadge } from "@/components/shared/EntityStatusBadge";
import { EntityTypeBadge } from "@/components/shared/EntityTypeBadge";
import { ConfidenceBar } from "@/components/shared/ConfidenceBar";
import { CopyUUID } from "@/components/shared/CopyUUID";
import { formatDate } from "@/lib/utils";
import { CONTEXT_TYPES, CONTEXT_TYPE_COLORS } from "@/lib/constants";
import type {
  EntityRead,
  AliasRead,
  ContextRead,
  RelationRead,
  ContextType,
  Locale,
} from "@/types/api";

type Tab = "alias" | "context" | "relation" | "bundle";

export function EntityDetail({
  entity,
  aliases,
  contexts,
  relations,
}: {
  entity: EntityRead;
  aliases: AliasRead[];
  contexts: ContextRead[];
  relations: RelationRead[];
}) {
  const router = useRouter();
  const [tab, setTab] = useState<Tab>("alias");
  const [isPending, startTransition] = useTransition();
  const [showDeprecateModal, setShowDeprecateModal] = useState(false);

  function approve() {
    startTransition(async () => {
      await updateEntity(entity.id, { status: "active" });
      router.refresh();
    });
  }

  function handleDeprecated(reason: string, replacementId: string) {
    setShowDeprecateModal(false);
    startTransition(async () => {
      await updateEntity(entity.id, {
        status: "deprecated",
        deprecation_reason: reason || undefined,
        replacement_entity_id: replacementId || undefined,
      });
      router.refresh();
    });
  }

  return (
    <>
      <header className="bg-white border-b border-gray-200 px-6 py-3 flex items-center gap-3 shrink-0">
        <Link
          href="/entities"
          className="text-gray-400 hover:text-gray-600 flex items-center gap-1 text-xs"
        >
          <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
          </svg>
          목록
        </Link>
        <span className="text-gray-300">/</span>
        <h1 className="font-semibold text-gray-900 flex-1">{entity.canonical_name}</h1>
        <div className="flex items-center gap-2">
          <CopyUUID id={entity.id} />
          <Link
            href={`/entities/${entity.id}/edit`}
            className="text-xs border border-gray-200 rounded px-3 py-1.5 hover:bg-gray-50"
          >
            수정
          </Link>
          {entity.status === "candidate" && (
            <button
              onClick={approve}
              disabled={isPending}
              className="text-xs bg-green-600 text-white rounded px-3 py-1.5 hover:bg-green-700 font-medium disabled:opacity-60"
            >
              ✓ Active 승인
            </button>
          )}
          {entity.status === "active" && (
            <button
              onClick={() => setShowDeprecateModal(true)}
              disabled={isPending}
              className="text-xs bg-red-500 text-white rounded px-3 py-1.5 hover:bg-red-600 font-medium disabled:opacity-60"
            >
              Deprecated 처리
            </button>
          )}
        </div>
      </header>

      <div className="bg-white border-b border-gray-100 px-6 py-2 flex items-center gap-4 text-xs shrink-0">
        <EntityTypeBadge type={entity.type} />
        <EntityStatusBadge status={entity.status} />
        <span className="text-gray-400">신뢰도</span>
        <ConfidenceBar value={entity.confidence} />
        <span className="text-gray-300">|</span>
        <TagBar entityId={entity.id} initialTags={entity.tags ?? []} />
        <span className="text-gray-300">|</span>
        <span className="text-gray-400">등록: {formatDate(entity.created_at)}</span>
        <span className="text-gray-400">· 수정: {formatDate(entity.updated_at)}</span>
      </div>

      {entity.status === "deprecated" && (
        <div className="bg-red-50 border-b border-red-200 px-6 py-2 text-xs text-red-700">
          <span className="font-medium">Deprecated</span>
          {entity.deprecation_reason && ` — ${entity.deprecation_reason}`}
          {entity.replacement_entity_id && (
            <Link href={`/entities/${entity.replacement_entity_id}`} className="ml-2 underline">
              대체 entity 보기 →
            </Link>
          )}
        </div>
      )}

      {entity.description && (
        <div className="bg-white border-b border-gray-100 px-6 py-3 text-gray-600 text-xs shrink-0">
          {entity.description}
        </div>
      )}

      {showDeprecateModal && (
        <DeprecateModal
          onConfirm={handleDeprecated}
          onCancel={() => setShowDeprecateModal(false)}
        />
      )}

      <div className="flex-1 overflow-hidden flex flex-col">
        <div className="bg-white border-b border-gray-200 px-6 flex gap-1 shrink-0">
          {(["alias", "context", "relation", "bundle"] as Tab[]).map((t) => {
            const counts: Record<Tab, number | undefined> = {
              alias: aliases.length,
              context: contexts.length,
              relation: relations.length,
              bundle: undefined,
            };
            const labels: Record<Tab, string> = {
              alias: "Alias",
              context: "Context",
              relation: "Relation",
              bundle: "Bundle 미리보기",
            };
            return (
              <button
                key={t}
                onClick={() => setTab(t)}
                className={`px-4 py-2.5 text-sm font-medium border-b-2 ${
                  tab === t
                    ? "border-indigo-600 text-indigo-700"
                    : "border-transparent text-gray-500 hover:text-gray-700"
                }`}
              >
                {labels[t]}
                {counts[t] !== undefined && (
                  <span
                    className={`ml-1 text-xs px-1.5 py-0.5 rounded-full ${
                      tab === t
                        ? "bg-indigo-100 text-indigo-600"
                        : "bg-gray-100 text-gray-500"
                    }`}
                  >
                    {counts[t]}
                  </span>
                )}
              </button>
            );
          })}
        </div>

        <div className="flex-1 overflow-y-auto p-6">
          {tab === "alias" && <AliasPane entityId={entity.id} aliases={aliases} />}
          {tab === "context" && <ContextPane entityId={entity.id} contexts={contexts} />}
          {tab === "relation" && <RelationPane relations={relations} />}
          {tab === "bundle" && (
            <div className="text-center py-10">
              <Link
                href={`/bundle?root=${entity.id}`}
                className="text-sm text-indigo-600 hover:underline"
              >
                Bundle 탐색기에서 열기 →
              </Link>
            </div>
          )}
        </div>
      </div>
    </>
  );
}

function TagBar({ entityId, initialTags }: { entityId: string; initialTags: string[] }) {
  const router = useRouter();
  const [tags, setTags] = useState(initialTags);
  const [editing, setEditing] = useState(false);
  const [input, setInput] = useState("");
  const [isPending, startTransition] = useTransition();

  function handleAdd() {
    const val = input.trim().replace(/^#+/, "");
    if (!val || tags.includes(val)) return;
    startTransition(async () => {
      await addTag(entityId, val);
      setTags((prev) => [...prev, val]);
      setInput("");
      setEditing(false);
      router.refresh();
    });
  }

  function handleDelete(tag: string) {
    startTransition(async () => {
      await deleteTag(entityId, tag);
      setTags((prev) => prev.filter((t) => t !== tag));
      router.refresh();
    });
  }

  return (
    <div className="flex items-center gap-1.5 flex-wrap">
      {tags.map((tag) => (
        <span key={tag}
          className="inline-flex items-center gap-1 bg-violet-50 text-violet-700 border border-violet-200 px-2 py-0.5 rounded-full text-xs">
          #{tag}
          <button onClick={() => handleDelete(tag)}
            disabled={isPending}
            className="hover:text-violet-900 disabled:opacity-40">×</button>
        </span>
      ))}
      {editing ? (
        <input
          autoFocus
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter") { e.preventDefault(); handleAdd(); }
            if (e.key === "Escape") { setEditing(false); setInput(""); }
          }}
          onBlur={() => { if (!input.trim()) setEditing(false); }}
          className="border border-indigo-400 rounded-full px-2 py-0.5 text-xs focus:outline-none focus:ring-1 focus:ring-indigo-400 w-28"
          placeholder="태그 입력 후 Enter"
        />
      ) : (
        <button onClick={() => setEditing(true)}
          className="inline-flex items-center gap-0.5 text-gray-400 hover:text-indigo-600 border border-dashed border-gray-300 hover:border-indigo-400 px-2 py-0.5 rounded-full text-xs">
          <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M12 4v16m8-8H4" />
          </svg>
          태그
        </button>
      )}
    </div>
  );
}

function AliasPane({ entityId, aliases }: { entityId: string; aliases: AliasRead[] }) {
  const router = useRouter();
  const [locale, setLocale] = useState<Locale>("ko");
  const [alias, setAlias] = useState("");
  const [isPrimary, setIsPrimary] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isPending, startTransition] = useTransition();

  function submit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    startTransition(async () => {
      try {
        await addAlias(entityId, { locale, alias, is_primary: isPrimary });
        setAlias("");
        router.refresh();
      } catch (e) {
        setError((e as Error).message);
      }
    });
  }

  function handleDeactivate(aliasId: string) {
    startTransition(async () => {
      await deactivateAlias(entityId, aliasId);
      router.refresh();
    });
  }

  return (
    <>
      <div className="flex items-center justify-between mb-4">
        <h3 className="font-medium text-gray-700 text-sm">등록된 Alias</h3>
      </div>
      <div className="bg-white rounded-lg border border-gray-200 overflow-hidden mb-4">
        <table className="w-full text-xs">
          <thead className="bg-gray-50 border-b border-gray-100">
            <tr className="text-gray-400">
              <th className="text-left px-4 py-2 font-medium">언어</th>
              <th className="text-left px-4 py-2 font-medium">alias</th>
              <th className="text-left px-4 py-2 font-medium">Primary</th>
              <th className="text-left px-4 py-2 font-medium">상태</th>
              <th className="px-4 py-2" />
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-50">
            {aliases.map((a) => (
              <tr key={a.id} className="hover:bg-gray-50">
                <td className="px-4 py-2.5">
                  <span className="font-mono bg-gray-100 text-gray-600 px-1.5 py-0.5 rounded">
                    {a.locale}
                  </span>
                </td>
                <td className="px-4 py-2.5 font-medium">{a.alias}</td>
                <td className="px-4 py-2.5">
                  {a.is_primary ? (
                    <span className="text-green-600 font-medium">✓ primary</span>
                  ) : (
                    <span className="text-gray-300">—</span>
                  )}
                </td>
                <td className="px-4 py-2.5">
                  {a.is_active ? (
                    <span className="flex items-center gap-1 text-green-600">
                      <span className="w-1.5 h-1.5 rounded-full bg-green-400" />
                      active
                    </span>
                  ) : (
                    <span className="text-gray-400">inactive</span>
                  )}
                </td>
                <td className="px-4 py-2.5 text-right">
                  {a.is_active && (
                    <button
                      onClick={() => handleDeactivate(a.id)}
                      disabled={isPending}
                      className="text-xs text-red-400 hover:text-red-600 disabled:opacity-40"
                    >
                      비활성화
                    </button>
                  )}
                </td>
              </tr>
            ))}
            {!aliases.length && (
              <tr>
                <td colSpan={5} className="py-4 text-center text-gray-400">
                  등록된 alias 없음
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      <form onSubmit={submit} className="bg-gray-50 rounded-lg border border-gray-200 p-4">
        <h4 className="text-xs font-medium text-gray-600 mb-3">Alias 추가</h4>
        <div className="flex gap-2 items-end">
          <div>
            <label className="block text-xs text-gray-400 mb-1">언어</label>
            <select
              value={locale}
              onChange={(e) => setLocale(e.target.value as Locale)}
              className="border border-gray-200 rounded px-2 py-1.5 text-xs focus:outline-none"
            >
              <option value="ko">ko</option>
              <option value="en">en</option>
            </select>
          </div>
          <div className="flex-1">
            <label className="block text-xs text-gray-400 mb-1">alias</label>
            <input
              value={alias}
              onChange={(e) => setAlias(e.target.value)}
              required
              className="w-full border border-gray-200 rounded px-2 py-1.5 text-xs focus:outline-none focus:ring-1 focus:ring-indigo-400"
              placeholder="alias 텍스트"
            />
          </div>
          <label className="flex items-center gap-1.5 text-xs text-gray-500 pb-1.5">
            <input
              type="checkbox"
              checked={isPrimary}
              onChange={(e) => setIsPrimary(e.target.checked)}
              className="rounded"
            />
            Primary
          </label>
          <button
            type="submit"
            disabled={isPending}
            className="bg-indigo-600 text-white text-xs px-3 py-1.5 rounded hover:bg-indigo-700 disabled:opacity-60"
          >
            추가
          </button>
        </div>
        {error && <p className="mt-2 text-xs text-red-500">{error}</p>}
      </form>
    </>
  );
}

function ContextPane({ entityId, contexts }: { entityId: string; contexts: ContextRead[] }) {
  const router = useRouter();
  const [contextType, setContextType] = useState<ContextType>("summary");
  const [body, setBody] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [isPending, startTransition] = useTransition();

  function submit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    startTransition(async () => {
      try {
        await addContext(entityId, { context_type: contextType, body });
        setBody("");
        router.refresh();
      } catch (e) {
        setError((e as Error).message);
      }
    });
  }

  return (
    <>
      <div className="flex items-center justify-between mb-4">
        <h3 className="font-medium text-gray-700 text-sm">등록된 Context</h3>
      </div>
      <div className="space-y-3 mb-4">
        {contexts.map((ctx) => (
          <div key={ctx.id} className="bg-white rounded-lg border border-gray-200 p-4">
            <div className="flex items-center gap-2 mb-2">
              <span className={`px-2 py-0.5 rounded text-xs font-medium ${CONTEXT_TYPE_COLORS[ctx.context_type]}`}>
                {ctx.context_type}
              </span>
              <span className="text-xs text-gray-400 font-mono">{ctx.language}</span>
              {ctx.title && (
                <span className="text-xs text-gray-500 font-medium">{ctx.title}</span>
              )}
            </div>
            <p className="text-xs text-gray-700 leading-relaxed">{ctx.body}</p>
          </div>
        ))}
        {!contexts.length && (
          <div className="text-center py-6 text-gray-400 text-xs">등록된 context 없음</div>
        )}
      </div>

      <form onSubmit={submit} className="bg-gray-50 rounded-lg border border-gray-200 p-4">
        <h4 className="text-xs font-medium text-gray-600 mb-3">Context 추가</h4>
        <div className="space-y-2">
          <div>
            <label className="block text-xs text-gray-400 mb-1">타입</label>
            <select
              value={contextType}
              onChange={(e) => setContextType(e.target.value as ContextType)}
              className="border border-gray-200 rounded px-2 py-1.5 text-xs focus:outline-none"
            >
              {CONTEXT_TYPES.map((t) => (
                <option key={t} value={t}>{t}</option>
              ))}
            </select>
          </div>
          <div>
            <label className="block text-xs text-gray-400 mb-1">내용</label>
            <textarea
              value={body}
              onChange={(e) => setBody(e.target.value)}
              required
              rows={3}
              className="w-full border border-gray-200 rounded px-2 py-1.5 text-xs focus:outline-none focus:ring-1 focus:ring-indigo-400"
            />
          </div>
          {error && <p className="text-xs text-red-500">{error}</p>}
          <div className="flex justify-end">
            <button
              type="submit"
              disabled={isPending}
              className="bg-indigo-600 text-white text-xs px-3 py-1.5 rounded hover:bg-indigo-700 disabled:opacity-60"
            >
              추가
            </button>
          </div>
        </div>
      </form>
    </>
  );
}

function RelationPane({ relations }: { relations: RelationRead[] }) {
  return (
    <>
      <h3 className="font-medium text-gray-700 text-sm mb-4">Relations</h3>
      <div className="bg-white rounded-lg border border-gray-200 overflow-hidden">
        <table className="w-full text-xs">
          <thead className="bg-gray-50 border-b border-gray-100">
            <tr className="text-gray-400">
              <th className="text-left px-4 py-2 font-medium">관계 타입</th>
              <th className="text-left px-4 py-2 font-medium">From</th>
              <th className="text-left px-4 py-2 font-medium">To</th>
              <th className="text-left px-4 py-2 font-medium">설명</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-50">
            {relations.map((r) => (
              <tr key={r.id} className="hover:bg-gray-50">
                <td className="px-4 py-2.5">
                  <span className="font-mono bg-gray-100 text-gray-600 px-1.5 py-0.5 rounded">
                    {r.relation_type}
                  </span>
                </td>
                <td className="px-4 py-2.5 font-mono text-gray-500 text-xs">
                  {r.from_entity_id.slice(0, 8)}…
                </td>
                <td className="px-4 py-2.5 font-mono text-gray-500 text-xs">
                  {r.to_entity_id.slice(0, 8)}…
                </td>
                <td className="px-4 py-2.5 text-gray-400">{r.description ?? "—"}</td>
              </tr>
            ))}
            {!relations.length && (
              <tr>
                <td colSpan={4} className="py-4 text-center text-gray-400">
                  등록된 relation 없음
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </>
  );
}

function DeprecateModal({
  onConfirm,
  onCancel,
}: {
  onConfirm: (reason: string, replacementId: string) => void;
  onCancel: () => void;
}) {
  const [reason, setReason] = useState("");
  const [replacementId, setReplacementId] = useState("");

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40">
      <div className="bg-white rounded-lg shadow-xl w-full max-w-md p-6">
        <h2 className="font-semibold text-gray-900 mb-1">Deprecated 처리</h2>
        <p className="text-xs text-gray-500 mb-4">
          이 Entity를 deprecated 상태로 변경합니다. 대체 Entity UUID를 지정하면 번들 조회 시 warning에 포함됩니다.
        </p>
        <div className="space-y-3">
          <div>
            <label className="block text-xs text-gray-500 mb-1">사유 (선택)</label>
            <input
              value={reason}
              onChange={(e) => setReason(e.target.value)}
              placeholder="deprecation 사유를 입력하세요"
              className="w-full border border-gray-200 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-1 focus:ring-red-400"
            />
          </div>
          <div>
            <label className="block text-xs text-gray-500 mb-1">대체 Entity UUID (선택)</label>
            <input
              value={replacementId}
              onChange={(e) => setReplacementId(e.target.value)}
              placeholder="xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
              className="w-full border border-gray-200 rounded-md px-3 py-2 text-sm font-mono focus:outline-none focus:ring-1 focus:ring-red-400"
            />
          </div>
        </div>
        <div className="flex justify-end gap-2 mt-5">
          <button
            onClick={onCancel}
            className="px-4 py-2 text-sm border border-gray-200 rounded-md hover:bg-gray-50"
          >
            취소
          </button>
          <button
            onClick={() => onConfirm(reason, replacementId)}
            className="px-4 py-2 text-sm bg-red-500 text-white rounded-md hover:bg-red-600 font-medium"
          >
            Deprecated 처리
          </button>
        </div>
      </div>
    </div>
  );
}
