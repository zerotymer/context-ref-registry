"use client";

import { useState } from "react";
import Link from "next/link";
import { useEntities, useUpdateEntity } from "@/lib/api/entities";
import { useAliases } from "@/lib/api/aliases";
import { useContexts } from "@/lib/api/contexts";
import { useRelations } from "@/lib/api/relations";
import { useQueryClient } from "@tanstack/react-query";
import { EntityTypeBadge } from "@/components/shared/EntityTypeBadge";
import { ConfidenceBar } from "@/components/shared/ConfidenceBar";
import { EmptyState } from "@/components/shared/EmptyState";
import type { EntityRead } from "@/types/api";

export default function ReviewPage() {
  const { data, isLoading, refetch } = useEntities({
    status: "candidate",
    limit: 50,
    sort: "created_at",
    order: "asc",
  });

  const [dismissed, setDismissed] = useState<Set<string>>(new Set());

  const visible = data?.items.filter((e) => !dismissed.has(e.id)) ?? [];

  if (isLoading) {
    return (
      <>
        <ReviewHeader count={0} />
        <div className="flex items-center justify-center h-40 text-gray-400 text-sm">
          로딩 중...
        </div>
      </>
    );
  }

  return (
    <>
      <ReviewHeader count={visible.length} />
      <main className="flex-1 overflow-y-auto p-6 space-y-4">
        {visible.map((entity) => (
          <ReviewCard
            key={entity.id}
            entity={entity}
            onDismiss={() => setDismissed((s) => new Set(Array.from(s).concat(entity.id)))}
          />
        ))}
        {visible.length === 0 && (
          <EmptyState message="검토 대기 Entity 없음 ✓" />
        )}
      </main>
    </>
  );
}

function ReviewHeader({ count }: { count: number }) {
  return (
    <header className="bg-white border-b border-gray-200 px-6 py-3 flex items-center justify-between shrink-0">
      <div className="flex items-center gap-3">
        <h1 className="font-semibold text-gray-900">승인 대기</h1>
        {count > 0 && (
          <span className="bg-amber-100 text-amber-700 text-xs font-semibold px-2 py-0.5 rounded-full">
            {count}개 검토 필요
          </span>
        )}
      </div>
    </header>
  );
}

function ReviewCard({
  entity,
  onDismiss,
}: {
  entity: EntityRead;
  onDismiss: () => void;
}) {
  const { data: aliases } = useAliases(entity.id);
  const { data: contexts } = useContexts(entity.id);
  const { data: relations } = useRelations(entity.id);
  const qc = useQueryClient();

  const updateEntity = useUpdateEntity(entity.id);
  const isLowConfidence = entity.confidence < 0.7;

  const summary = contexts?.find((c) => c.context_type === "summary");

  function approve() {
    updateEntity.mutate(
      { status: "active" },
      {
        onSuccess: () => {
          qc.invalidateQueries({ queryKey: ["entities"] });
          onDismiss();
        },
      },
    );
  }

  function archive() {
    updateEntity.mutate(
      { status: "archived" },
      {
        onSuccess: () => {
          qc.invalidateQueries({ queryKey: ["entities"] });
          onDismiss();
        },
      },
    );
  }

  return (
    <div
      className={`bg-white rounded-lg shadow-sm ${
        isLowConfidence ? "border-2 border-amber-300" : "border border-gray-200"
      }`}
    >
      <div className="px-5 py-4">
        <div className="flex items-start justify-between mb-3">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <span className="font-semibold text-gray-900">{entity.canonical_name}</span>
              <EntityTypeBadge type={entity.type} />
              {isLowConfidence && (
                <span className="px-1.5 py-0.5 rounded text-xs bg-amber-100 text-amber-700 font-medium">
                  ⚠ 신뢰도 낮음
                </span>
              )}
            </div>
            {entity.description && (
              <p className="text-xs text-gray-500 leading-relaxed max-w-2xl">
                {entity.description}
              </p>
            )}
          </div>
          <div className="ml-4 shrink-0">
            <ConfidenceBar value={entity.confidence} />
          </div>
        </div>

        {/* Alias chips */}
        {aliases && aliases.length > 0 && (
          <div className="flex flex-wrap gap-1.5 mb-3">
            {aliases.slice(0, 6).map((a) => (
              <span
                key={a.id}
                className="text-xs bg-gray-100 text-gray-600 px-2 py-0.5 rounded-full font-mono"
              >
                {a.locale} / {a.alias}
              </span>
            ))}
          </div>
        )}

        {/* Summary context */}
        {summary && (
          <div className="bg-gray-50 rounded p-2.5 mb-3 text-xs text-gray-600 leading-relaxed">
            <span className="font-medium text-gray-500">summary · </span>
            {summary.body}
          </div>
        )}

        <div className="flex items-center justify-between">
          <div className="text-xs text-gray-400">
            Context {contexts?.length ?? 0}개 · Relation {relations?.length ?? 0}개
            {" · "}
            <Link href={`/entities/${entity.id}`} className="text-indigo-600 hover:underline">
              상세 보기
            </Link>
          </div>
          <div className="flex gap-2">
            <button
              onClick={archive}
              disabled={updateEntity.isPending}
              className="text-xs px-3 py-1.5 rounded-md border border-gray-200 text-gray-500 hover:bg-gray-50 disabled:opacity-60"
            >
              보류 (archive)
            </button>
            <Link
              href={`/entities/${entity.id}/edit`}
              className="text-xs px-3 py-1.5 rounded-md border border-gray-200 text-gray-600 hover:bg-gray-50"
            >
              수정
            </Link>
            <button
              onClick={approve}
              disabled={updateEntity.isPending}
              className="text-xs px-4 py-1.5 rounded-md bg-green-600 text-white font-medium hover:bg-green-700 disabled:opacity-60"
            >
              ✓ Active 승인
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
