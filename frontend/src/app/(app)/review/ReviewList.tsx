"use client";

import { useState, useTransition } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { updateEntity } from "@/lib/actions/entities";
import { EntityTypeBadge } from "@/components/shared/EntityTypeBadge";
import { ConfidenceBar } from "@/components/shared/ConfidenceBar";
import { EmptyState } from "@/components/shared/EmptyState";
import { CONTEXT_TYPE_COLORS } from "@/lib/constants";
import type { ReviewItem } from "./page";

export function ReviewList({ items }: { items: ReviewItem[] }) {
  const [dismissed, setDismissed] = useState<Set<string>>(new Set<string>());
  const visible = items.filter((i) => !dismissed.has(i.entity.id));

  return (
    <>
      <header className="bg-white border-b border-gray-200 px-6 py-3 flex items-center justify-between shrink-0">
        <div className="flex items-center gap-3">
          <h1 className="font-semibold text-gray-900">승인 대기</h1>
          {visible.length > 0 && (
            <span className="bg-amber-100 text-amber-700 text-xs font-semibold px-2 py-0.5 rounded-full">
              {visible.length}개 검토 필요
            </span>
          )}
        </div>
      </header>
      <main className="flex-1 overflow-y-auto p-6 space-y-4">
        {visible.map((item) => (
          <ReviewCard
            key={item.entity.id}
            item={item}
            onDismiss={() =>
              setDismissed((prev) => { const next = new Set<string>(prev); next.add(item.entity.id); return next; })
            }
          />
        ))}
        {visible.length === 0 && <EmptyState message="검토 대기 Entity 없음 ✓" />}
      </main>
    </>
  );
}

function ReviewCard({
  item,
  onDismiss,
}: {
  item: ReviewItem;
  onDismiss: () => void;
}) {
  const { entity, aliases, contexts, relations } = item;
  const router = useRouter();
  const [isPending, startTransition] = useTransition();
  const isLowConfidence = entity.confidence < 0.7;
  const summary = contexts.find((c) => c.context_type === "summary");

  function approve() {
    onDismiss();
    startTransition(async () => {
      await updateEntity(entity.id, { status: "active" });
      router.refresh();
    });
  }

  function archive() {
    onDismiss();
    startTransition(async () => {
      await updateEntity(entity.id, { status: "archived" });
      router.refresh();
    });
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

        {aliases.length > 0 && (
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

        {summary && (
          <div className="bg-gray-50 rounded p-2.5 mb-3 text-xs text-gray-600 leading-relaxed">
            <span className={`inline-block mr-1 px-1.5 py-0.5 rounded font-medium ${CONTEXT_TYPE_COLORS.summary}`}>
              summary
            </span>
            {summary.body}
          </div>
        )}

        <div className="flex items-center justify-between">
          <div className="text-xs text-gray-400">
            Context {contexts.length}개 · Relation {relations.length}개
            {" · "}
            <Link href={`/entities/${entity.id}`} className="text-indigo-600 hover:underline">
              상세 보기
            </Link>
          </div>
          <div className="flex gap-2">
            <button
              onClick={archive}
              disabled={isPending}
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
              disabled={isPending}
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
