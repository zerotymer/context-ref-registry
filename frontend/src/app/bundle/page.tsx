"use client";

import { useState, useEffect, Suspense } from "react";
import { useSearchParams } from "next/navigation";
import { useContextBundle } from "@/lib/api/bundle";
import { JsonViewer } from "@/components/shared/JsonViewer";
import { ENTITY_TYPES, CONTEXT_TYPE_COLORS, ENTITY_TYPE_COLORS } from "@/lib/constants";
import type { ContextBundleResponse, EntityType } from "@/types/api";

type ResultTab = "context" | "entities" | "relations" | "json";

const APPROX_CHARS_PER_TOKEN = 4;

function estimateTokens(result: ContextBundleResponse): number {
  const text = result.contexts.map((c) => c.body).join(" ");
  return Math.round(text.length / APPROX_CHARS_PER_TOKEN);
}

export default function BundlePage() {
  return (
    <Suspense fallback={null}>
      <BundlePageInner />
    </Suspense>
  );
}

function BundlePageInner() {
  const searchParams = useSearchParams();
  const [rootId, setRootId] = useState(searchParams.get("root") ?? "");
  const [maxDepth, setMaxDepth] = useState(1);
  const [tokenBudget, setTokenBudget] = useState(6000);
  const [includeTypes, setIncludeTypes] = useState<Set<EntityType>>(
    new Set(ENTITY_TYPES.filter((t) => t !== "API")),
  );
  const [resultTab, setResultTab] = useState<ResultTab>("context");

  const bundle = useContextBundle();

  function toggleType(type: EntityType) {
    setIncludeTypes((prev) => {
      const next = new Set(prev);
      if (next.has(type)) next.delete(type);
      else next.add(type);
      return next;
    });
  }

  function fetch() {
    if (!rootId.trim()) return;
    bundle.mutate({
      root_ids: [rootId.trim()],
      max_depth: maxDepth,
      token_budget: tokenBudget,
      include_types: includeTypes.size > 0 ? Array.from(includeTypes) : undefined,
    });
  }

  // auto-fetch if root is pre-filled
  useEffect(() => {
    if (searchParams.get("root")) fetch();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const result = bundle.data;
  const estimatedTokens = result ? estimateTokens(result) : 0;

  return (
    <>
      <header className="bg-white border-b border-gray-200 px-6 py-3 shrink-0">
        <h1 className="font-semibold text-gray-900">Context Bundle 탐색기</h1>
        <p className="text-xs text-gray-400 mt-0.5">
          root entity를 기준으로 BFS 관계 그래프와 context를 조회합니다.
        </p>
      </header>

      <div className="flex-1 overflow-hidden flex">
        {/* Left panel */}
        <div className="w-72 border-r border-gray-200 bg-white flex flex-col shrink-0 overflow-y-auto">
          <div className="p-4 border-b border-gray-100">
            <div className="text-xs font-medium text-gray-600 mb-3">조회 설정</div>

            <div className="mb-3">
              <label className="block text-xs text-gray-500 mb-1">Root Entity UUID</label>
              <input
                type="text"
                value={rootId}
                onChange={(e) => setRootId(e.target.value)}
                className="w-full border border-gray-200 rounded-md px-2.5 py-1.5 text-xs font-mono focus:outline-none focus:ring-1 focus:ring-indigo-400"
                placeholder="UUID를 입력하세요"
              />
            </div>

            <div className="mb-3">
              <label className="block text-xs text-gray-500 mb-1">
                Max Depth: <strong>{maxDepth}</strong>
              </label>
              <input
                type="range"
                min={0}
                max={5}
                value={maxDepth}
                onChange={(e) => setMaxDepth(parseInt(e.target.value))}
                className="w-full"
              />
            </div>

            <div className="mb-3">
              <label className="block text-xs text-gray-500 mb-1">Token Budget</label>
              <input
                type="number"
                value={tokenBudget}
                onChange={(e) => setTokenBudget(parseInt(e.target.value) || 6000)}
                className="w-full border border-gray-200 rounded-md px-2.5 py-1.5 text-xs focus:outline-none focus:ring-1 focus:ring-indigo-400"
              />
            </div>

            <div className="mb-4">
              <label className="block text-xs text-gray-500 mb-1.5">Include Types</label>
              <div className="space-y-1 text-xs">
                {ENTITY_TYPES.map((type) => (
                  <label key={type} className="flex items-center gap-2">
                    <input
                      type="checkbox"
                      checked={includeTypes.has(type)}
                      onChange={() => toggleType(type)}
                      className="rounded"
                    />
                    <span>{type}</span>
                  </label>
                ))}
              </div>
            </div>

            <button
              onClick={fetch}
              disabled={bundle.isPending || !rootId.trim()}
              className="w-full bg-indigo-600 text-white text-xs font-medium py-2 rounded-md hover:bg-indigo-700 disabled:opacity-60"
            >
              {bundle.isPending ? "조회 중..." : "Bundle 조회"}
            </button>

            {bundle.error && (
              <p className="mt-2 text-xs text-red-500">
                {(bundle.error as Error).message}
              </p>
            )}
          </div>
        </div>

        {/* Right panel */}
        <div className="flex-1 overflow-y-auto">
          {!result && !bundle.isPending && (
            <div className="flex flex-col items-center justify-center h-full text-center text-gray-400 p-8">
              <svg className="w-12 h-12 mb-3 text-gray-200" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
              </svg>
              <div className="font-medium text-gray-500">Bundle 조회 결과가 여기에 표시됩니다</div>
              <div className="text-xs mt-1">왼쪽에서 root entity와 파라미터를 설정하고 조회하세요.</div>
            </div>
          )}

          {bundle.isPending && (
            <div className="flex items-center justify-center h-40 text-gray-400 text-sm">
              조회 중...
            </div>
          )}

          {result && (
            <div className="p-5 space-y-4">
              {/* Summary bar */}
              <div className="bg-indigo-50 border border-indigo-100 rounded-lg px-4 py-3 flex items-center justify-between">
                <div className="flex gap-6 text-xs">
                  <span>
                    <span className="font-semibold text-indigo-800">{result.entities.length}</span>{" "}
                    <span className="text-indigo-600">entities</span>
                  </span>
                  <span>
                    <span className="font-semibold text-indigo-800">{result.contexts.length}</span>{" "}
                    <span className="text-indigo-600">contexts</span>
                  </span>
                  <span>
                    <span className="font-semibold text-indigo-800">{result.relations.length}</span>{" "}
                    <span className="text-indigo-600">relations</span>
                  </span>
                </div>
                <div className="flex items-center gap-2 text-xs">
                  <span className="text-gray-500">Token (est.)</span>
                  <div className="w-32 h-2 bg-indigo-100 rounded-full">
                    <div
                      className="h-2 bg-indigo-500 rounded-full"
                      style={{ width: `${Math.min(100, (estimatedTokens / tokenBudget) * 100)}%` }}
                    />
                  </div>
                  <span className="text-indigo-700 font-medium">
                    {estimatedTokens.toLocaleString()} / {tokenBudget.toLocaleString()}
                  </span>
                </div>
              </div>

              {/* Deprecation warnings */}
              {result.warnings.length > 0 && (
                <div className="bg-red-50 border border-red-200 rounded-lg px-4 py-3 text-xs text-red-700">
                  <div className="font-medium mb-1">경고: Deprecated entity 포함</div>
                  {result.warnings.map((w, i) => (
                    <div key={i}>• {w.message}</div>
                  ))}
                </div>
              )}

              {/* Result tabs */}
              <div className="bg-white rounded-lg border border-gray-200 overflow-hidden">
                <div className="flex border-b border-gray-100 px-1 pt-1">
                  {(["context", "entities", "relations", "json"] as ResultTab[]).map((t) => {
                    const labels: Record<ResultTab, string> = {
                      context: `Context (${result.contexts.length})`,
                      entities: `Entities (${result.entities.length})`,
                      relations: `Relations (${result.relations.length})`,
                      json: "JSON",
                    };
                    return (
                      <button
                        key={t}
                        onClick={() => setResultTab(t)}
                        className={`px-4 py-2 text-xs font-medium border-b-2 ${
                          resultTab === t
                            ? "border-indigo-600 text-indigo-700"
                            : "border-transparent text-gray-500 hover:text-gray-700"
                        }`}
                      >
                        {labels[t]}
                      </button>
                    );
                  })}
                </div>

                {resultTab === "context" && (
                  <div className="p-4 space-y-2.5 max-h-[500px] overflow-y-auto">
                    {result.contexts.length === 0 && (
                      <div className="text-xs text-gray-400 text-center py-4">context 없음</div>
                    )}
                    {result.contexts.map((ctx, i) => {
                      const entity = result.entities.find((e) => e.id === ctx.entity_id);
                      return (
                        <div key={i} className="bg-gray-50 rounded p-2.5">
                          <div className="flex items-center gap-2 mb-1">
                            <span className={`inline-block px-1.5 py-0.5 rounded text-xs font-medium ${CONTEXT_TYPE_COLORS[ctx.context_type]}`}>
                              {ctx.context_type}
                            </span>
                            {entity && (
                              <span className="text-xs text-gray-400">{entity.canonical_name}</span>
                            )}
                          </div>
                          <p className="text-xs text-gray-700 leading-relaxed">{ctx.body}</p>
                        </div>
                      );
                    })}
                  </div>
                )}

                {resultTab === "entities" && (
                  <div className="p-4 space-y-2">
                    {result.entities.map((e) => {
                      const isRoot = result.roots.some((r) => r.id === e.id);
                      return (
                        <div key={e.id} className="flex items-center gap-2 px-3 py-2 bg-gray-50 rounded text-xs">
                          <span className={`w-2 h-2 rounded-full ${isRoot ? "bg-indigo-400" : "bg-gray-300"}`} />
                          <span className={`font-medium ${isRoot ? "text-indigo-700" : "text-gray-700"}`}>
                            {e.canonical_name}
                          </span>
                          <span className={`ml-auto px-1.5 py-0.5 rounded text-xs font-medium ${ENTITY_TYPE_COLORS[e.type]}`}>
                            {e.type}
                          </span>
                          {isRoot && <span className="text-amber-500 text-xs">root</span>}
                        </div>
                      );
                    })}
                  </div>
                )}

                {resultTab === "relations" && (
                  <div className="p-4 space-y-1.5">
                    {result.relations.map((r, i) => {
                      const from = result.entities.find((e) => e.id === r.from_entity_id);
                      const to = result.entities.find((e) => e.id === r.to_entity_id);
                      return (
                        <div key={i} className="flex items-center gap-2 text-xs px-3 py-2 bg-gray-50 rounded">
                          <span className="font-medium text-gray-700 truncate max-w-xs">
                            {from?.canonical_name ?? r.from_entity_id.slice(0, 8)}
                          </span>
                          <span className="text-gray-400 shrink-0">──{r.relation_type}──▶</span>
                          <span className="font-medium text-indigo-700 truncate max-w-xs">
                            {to?.canonical_name ?? r.to_entity_id.slice(0, 8)}
                          </span>
                        </div>
                      );
                    })}
                    {result.relations.length === 0 && (
                      <div className="text-xs text-gray-400 text-center py-4">relation 없음</div>
                    )}
                  </div>
                )}

                {resultTab === "json" && (
                  <div className="p-4">
                    <JsonViewer data={result} copyButton />
                  </div>
                )}
              </div>
            </div>
          )}
        </div>
      </div>
    </>
  );
}
