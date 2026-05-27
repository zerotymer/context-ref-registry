"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import { useEntity, useUpdateEntity } from "@/lib/api/entities";
import { ENTITY_STATUSES } from "@/lib/constants";
import type { EntityStatus } from "@/types/api";

export default function EntityEditPage() {
  const { id } = useParams<{ id: string }>();
  const router = useRouter();
  const { data: entity, isLoading } = useEntity(id);
  const updateEntity = useUpdateEntity(id);

  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [status, setStatus] = useState<EntityStatus>("candidate");
  const [confidence, setConfidence] = useState(1.0);

  useEffect(() => {
    if (entity) {
      setName(entity.canonical_name);
      setDescription(entity.description ?? "");
      setStatus(entity.status);
      setConfidence(entity.confidence);
    }
  }, [entity]);

  function submit(e: React.FormEvent) {
    e.preventDefault();
    updateEntity.mutate(
      { canonical_name: name, description: description || undefined, status, confidence },
      { onSuccess: () => router.push(`/entities/${id}`) },
    );
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-full text-gray-400 text-sm">
        로딩 중...
      </div>
    );
  }

  return (
    <>
      <header className="bg-white border-b border-gray-200 px-6 py-3 flex items-center gap-3 shrink-0">
        <Link
          href={`/entities/${id}`}
          className="text-gray-400 hover:text-gray-600 flex items-center gap-1 text-xs"
        >
          <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
          </svg>
          상세
        </Link>
        <span className="text-gray-300">/</span>
        <h1 className="font-semibold text-gray-900">Entity 수정</h1>
      </header>

      <main className="flex-1 overflow-y-auto p-6">
        <div className="max-w-lg">
          <form onSubmit={submit} className="space-y-4">
            <div>
              <label className="block text-xs text-gray-500 mb-1">canonical_name</label>
              <input
                value={name}
                onChange={(e) => setName(e.target.value)}
                required
                className="w-full border border-gray-200 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-1 focus:ring-indigo-400"
              />
            </div>
            <div>
              <label className="block text-xs text-gray-500 mb-1">설명</label>
              <textarea
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                rows={3}
                className="w-full border border-gray-200 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-1 focus:ring-indigo-400"
              />
            </div>
            <div>
              <label className="block text-xs text-gray-500 mb-1">상태</label>
              <select
                value={status}
                onChange={(e) => setStatus(e.target.value as EntityStatus)}
                className="border border-gray-200 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-1 focus:ring-indigo-400"
              >
                {ENTITY_STATUSES.map((s) => (
                  <option key={s} value={s}>{s}</option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-xs text-gray-500 mb-1">
                신뢰도: {confidence.toFixed(2)}
              </label>
              <input
                type="range"
                min={0}
                max={1}
                step={0.01}
                value={confidence}
                onChange={(e) => setConfidence(parseFloat(e.target.value))}
                className="w-full"
              />
            </div>
            {updateEntity.error && (
              <p className="text-xs text-red-500">
                {(updateEntity.error as Error).message}
              </p>
            )}
            <div className="flex gap-2">
              <Link
                href={`/entities/${id}`}
                className="px-4 py-2 text-sm border border-gray-200 rounded-md hover:bg-gray-50"
              >
                취소
              </Link>
              <button
                type="submit"
                disabled={updateEntity.isPending}
                className="px-4 py-2 text-sm bg-indigo-600 text-white rounded-md hover:bg-indigo-700 disabled:opacity-60"
              >
                {updateEntity.isPending ? "저장 중..." : "저장"}
              </button>
            </div>
          </form>
        </div>
      </main>
    </>
  );
}
