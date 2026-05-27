"use client";

import { useState } from "react";
import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import { useEntity, useUpdateEntity } from "@/lib/api/entities";
import { useAliases, useAddAlias } from "@/lib/api/aliases";
import { useContexts, useAddContext } from "@/lib/api/contexts";
import { useRelations } from "@/lib/api/relations";
import { EntityStatusBadge } from "@/components/shared/EntityStatusBadge";
import { EntityTypeBadge } from "@/components/shared/EntityTypeBadge";
import { ConfidenceBar } from "@/components/shared/ConfidenceBar";
import { CopyUUID } from "@/components/shared/CopyUUID";
import { formatDate } from "@/lib/utils";
import { CONTEXT_TYPES, CONTEXT_TYPE_COLORS } from "@/lib/constants";
import type { ContextType, Locale } from "@/types/api";

type Tab = "alias" | "context" | "relation" | "bundle";

export default function EntityDetailPage() {
  const { id } = useParams<{ id: string }>();
  const router = useRouter();
  const [tab, setTab] = useState<Tab>("alias");

  const { data: entity, isLoading } = useEntity(id);
  const { data: aliases } = useAliases(id);
  const { data: contexts } = useContexts(id);
  const { data: relations } = useRelations(id);

  const updateEntity = useUpdateEntity(id);

  function approve() {
    updateEntity.mutate({ status: "active" }, { onSuccess: () => router.refresh() });
  }

  function deprecate() {
    const reason = window.prompt("Deprecation 사유를 입력하세요:");
    if (reason === null) return;
    updateEntity.mutate({ status: "deprecated", deprecation_reason: reason });
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-full text-gray-400 text-sm">
        로딩 중...
      </div>
    );
  }

  if (!entity) {
    return (
      <div className="flex items-center justify-center h-full text-gray-400 text-sm">
        Entity를 찾을 수 없습니다.
      </div>
    );
  }

  return (
    <>
      {/* Header */}
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
            href={`/entities/${id}/edit`}
            className="text-xs border border-gray-200 rounded px-3 py-1.5 hover:bg-gray-50"
          >
            수정
          </Link>
          {entity.status === "candidate" && (
            <button
              onClick={approve}
              disabled={updateEntity.isPending}
              className="text-xs bg-green-600 text-white rounded px-3 py-1.5 hover:bg-green-700 font-medium disabled:opacity-60"
            >
              ✓ Active 승인
            </button>
          )}
          {entity.status === "active" && (
            <button
              onClick={deprecate}
              disabled={updateEntity.isPending}
              className="text-xs bg-red-500 text-white rounded px-3 py-1.5 hover:bg-red-600 font-medium disabled:opacity-60"
            >
              Deprecated 처리
            </button>
          )}
        </div>
      </header>

      {/* Meta bar */}
      <div className="bg-white border-b border-gray-100 px-6 py-2 flex items-center gap-4 text-xs shrink-0">
        <EntityTypeBadge type={entity.type} />
        <EntityStatusBadge status={entity.status} />
        <span className="text-gray-400">신뢰도</span>
        <ConfidenceBar value={entity.confidence} />
        <span className="text-gray-300">|</span>
        <span className="text-gray-400">등록: {formatDate(entity.created_at)}</span>
        <span className="text-gray-400">· 수정: {formatDate(entity.updated_at)}</span>
      </div>

      {/* Deprecation banner */}
      {entity.status === "deprecated" && (
        <div className="bg-red-50 border-b border-red-200 px-6 py-2 text-xs text-red-700">
          <span className="font-medium">Deprecated</span>
          {entity.deprecation_reason && ` — ${entity.deprecation_reason}`}
          {entity.replacement_entity_id && (
            <Link
              href={`/entities/${entity.replacement_entity_id}`}
              className="ml-2 underline"
            >
              대체 entity 보기 →
            </Link>
          )}
        </div>
      )}

      {/* Description */}
      {entity.description && (
        <div className="bg-white border-b border-gray-100 px-6 py-3 text-gray-600 text-xs shrink-0">
          {entity.description}
        </div>
      )}

      {/* Tabs */}
      <div className="flex-1 overflow-hidden flex flex-col">
        <div className="bg-white border-b border-gray-200 px-6 flex gap-1 shrink-0">
          {(["alias", "context", "relation", "bundle"] as Tab[]).map((t) => {
            const counts: Record<Tab, number | undefined> = {
              alias: aliases?.length,
              context: contexts?.length,
              relation: relations?.length,
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
          {tab === "alias" && (
            <AliasPane entityId={id} aliases={aliases ?? []} />
          )}
          {tab === "context" && (
            <ContextPane entityId={id} contexts={contexts ?? []} />
          )}
          {tab === "relation" && (
            <RelationPane entityId={id} relations={relations ?? []} />
          )}
          {tab === "bundle" && (
            <div className="text-center py-10">
              <Link
                href={`/bundle?root=${id}`}
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

function AliasPane({
  entityId,
  aliases,
}: {
  entityId: string;
  aliases: import("@/types/api").AliasRead[];
}) {
  const [locale, setLocale] = useState<Locale>("ko");
  const [alias, setAlias] = useState("");
  const [isPrimary, setIsPrimary] = useState(false);
  const addAlias = useAddAlias(entityId);

  function submit(e: React.FormEvent) {
    e.preventDefault();
    addAlias.mutate(
      { locale, alias, is_primary: isPrimary },
      { onSuccess: () => setAlias("") },
    );
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
              </tr>
            ))}
            {!aliases.length && (
              <tr>
                <td colSpan={4} className="py-4 text-center text-gray-400">
                  등록된 alias 없음
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      {/* Add alias form */}
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
            disabled={addAlias.isPending}
            className="bg-indigo-600 text-white text-xs px-3 py-1.5 rounded hover:bg-indigo-700 disabled:opacity-60"
          >
            추가
          </button>
        </div>
      </form>
    </>
  );
}

function ContextPane({
  entityId,
  contexts,
}: {
  entityId: string;
  contexts: import("@/types/api").ContextRead[];
}) {
  const [contextType, setContextType] = useState<ContextType>("summary");
  const [body, setBody] = useState("");
  const addContext = useAddContext(entityId);

  function submit(e: React.FormEvent) {
    e.preventDefault();
    addContext.mutate({ context_type: contextType, body }, { onSuccess: () => setBody("") });
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

      {/* Add context form */}
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
          <div className="flex justify-end">
            <button
              type="submit"
              disabled={addContext.isPending}
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

function RelationPane({
  relations,
}: {
  entityId: string;
  relations: import("@/types/api").RelationRead[];
}) {
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
