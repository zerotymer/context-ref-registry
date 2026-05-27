"use client";

import { useState, useCallback } from "react";
import Link from "next/link";
import { useEntities } from "@/lib/api/entities";
import { EntityStatusBadge } from "@/components/shared/EntityStatusBadge";
import { EntityTypeBadge } from "@/components/shared/EntityTypeBadge";
import { ConfidenceBar } from "@/components/shared/ConfidenceBar";
import { formatDate } from "@/lib/utils";
import { ENTITY_TYPES, ENTITY_STATUSES } from "@/lib/constants";
import type { EntityStatus, EntityType } from "@/types/api";
import { NewEntityModal } from "./NewEntityModal";

const PAGE_SIZE = 20;

export default function EntitiesPage() {
  const [status, setStatus] = useState<EntityStatus | "">("");
  const [typeFilter, setTypeFilter] = useState<EntityType | "">("");
  const [page, setPage] = useState(0);
  const [showNew, setShowNew] = useState(false);

  const { data, isLoading } = useEntities({
    status: status || undefined,
    types: typeFilter ? [typeFilter] : undefined,
    limit: PAGE_SIZE,
    offset: page * PAGE_SIZE,
    sort: "created_at",
    order: "desc",
  });

  const total = data?.total ?? 0;
  const totalPages = Math.ceil(total / PAGE_SIZE);

  const handleStatusChange = useCallback((v: string) => {
    setStatus(v as EntityStatus | "");
    setPage(0);
  }, []);

  const handleTypeChange = useCallback((v: string) => {
    setTypeFilter(v as EntityType | "");
    setPage(0);
  }, []);

  return (
    <>
      <header className="bg-white border-b border-gray-200 px-6 py-3 flex items-center justify-between shrink-0">
        <h1 className="font-semibold text-gray-900">Entity 목록</h1>
        <button
          onClick={() => setShowNew(true)}
          className="flex items-center gap-1.5 bg-indigo-600 text-white text-sm px-3 py-1.5 rounded-md hover:bg-indigo-700"
        >
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
          </svg>
          새 Entity
        </button>
      </header>

      {/* Toolbar */}
      <div className="bg-white border-b border-gray-100 px-6 py-2.5 flex items-center gap-3 shrink-0">
        <select
          value={typeFilter}
          onChange={(e) => handleTypeChange(e.target.value)}
          className="border border-gray-200 rounded-md text-sm px-2.5 py-1.5 focus:outline-none focus:ring-1 focus:ring-indigo-400"
        >
          <option value="">모든 타입</option>
          {ENTITY_TYPES.map((t) => (
            <option key={t} value={t}>
              {t}
            </option>
          ))}
        </select>
        <select
          value={status}
          onChange={(e) => handleStatusChange(e.target.value)}
          className="border border-gray-200 rounded-md text-sm px-2.5 py-1.5 focus:outline-none focus:ring-1 focus:ring-indigo-400"
        >
          <option value="">모든 상태</option>
          {ENTITY_STATUSES.map((s) => (
            <option key={s} value={s}>
              {s}
            </option>
          ))}
        </select>
        <div className="text-xs text-gray-400 ml-auto">{total}개 결과</div>
      </div>

      {/* Table */}
      <main className="flex-1 overflow-y-auto">
        {isLoading ? (
          <div className="flex items-center justify-center h-40 text-gray-400 text-sm">
            로딩 중...
          </div>
        ) : (
          <table className="w-full text-xs">
            <thead className="bg-gray-50 border-b border-gray-200 sticky top-0">
              <tr className="text-gray-500">
                <th className="text-left px-6 py-2.5 font-medium">canonical_name</th>
                <th className="text-left px-3 py-2.5 font-medium">타입</th>
                <th className="text-left px-3 py-2.5 font-medium">상태</th>
                <th className="text-left px-3 py-2.5 font-medium">신뢰도</th>
                <th className="text-left px-3 py-2.5 font-medium">등록일</th>
                <th className="px-3 py-2.5" />
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100 bg-white">
              {data?.items.map((entity) => (
                <tr
                  key={entity.id}
                  className={`hover:bg-gray-50 ${entity.confidence < 0.7 ? "bg-amber-50/40" : ""}`}
                >
                  <td className="px-6 py-3">
                    <Link
                      href={`/entities/${entity.id}`}
                      className="font-medium text-indigo-700 hover:underline"
                    >
                      {entity.canonical_name}
                    </Link>
                    {entity.description && (
                      <div className="text-gray-400 mt-0.5 truncate max-w-xs">
                        {entity.description}
                      </div>
                    )}
                  </td>
                  <td className="px-3 py-3">
                    <EntityTypeBadge type={entity.type} />
                  </td>
                  <td className="px-3 py-3">
                    <EntityStatusBadge status={entity.status} />
                  </td>
                  <td className="px-3 py-3">
                    <ConfidenceBar value={entity.confidence} />
                  </td>
                  <td className="px-3 py-3 text-gray-400">{formatDate(entity.created_at)}</td>
                  <td className="px-3 py-3">
                    <Link
                      href={`/entities/${entity.id}`}
                      className="text-gray-400 hover:text-indigo-600 p-1 rounded hover:bg-indigo-50 inline-block"
                    >
                      <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
                      </svg>
                    </Link>
                  </td>
                </tr>
              ))}
              {!data?.items.length && (
                <tr>
                  <td colSpan={6} className="py-12 text-center text-gray-400">
                    등록된 entity 없음
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        )}

        {/* Pagination */}
        {totalPages > 1 && (
          <div className="border-t border-gray-200 px-6 py-3 flex items-center justify-between bg-white">
            <div className="text-xs text-gray-400">
              {page * PAGE_SIZE + 1}–{Math.min((page + 1) * PAGE_SIZE, total)} / {total}개
            </div>
            <div className="flex gap-1">
              <button
                onClick={() => setPage((p) => Math.max(0, p - 1))}
                disabled={page === 0}
                className="px-2.5 py-1 rounded border border-gray-200 text-gray-400 text-xs disabled:opacity-40"
              >
                ←
              </button>
              {Array.from({ length: Math.min(totalPages, 5) }).map((_, i) => (
                <button
                  key={i}
                  onClick={() => setPage(i)}
                  className={`px-2.5 py-1 rounded border text-xs ${
                    page === i
                      ? "border-indigo-300 bg-indigo-50 text-indigo-700 font-medium"
                      : "border-gray-200 text-gray-600 hover:bg-gray-50"
                  }`}
                >
                  {i + 1}
                </button>
              ))}
              <button
                onClick={() => setPage((p) => Math.min(totalPages - 1, p + 1))}
                disabled={page >= totalPages - 1}
                className="px-2.5 py-1 rounded border border-gray-200 text-gray-600 text-xs disabled:opacity-40 hover:bg-gray-50"
              >
                →
              </button>
            </div>
          </div>
        )}
      </main>

      {showNew && <NewEntityModal onClose={() => setShowNew(false)} />}
    </>
  );
}
