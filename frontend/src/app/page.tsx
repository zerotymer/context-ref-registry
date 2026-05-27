"use client";

import Link from "next/link";
import { useEntities } from "@/lib/api/entities";
import { EntityStatusBadge } from "@/components/shared/EntityStatusBadge";
import { EntityTypeBadge } from "@/components/shared/EntityTypeBadge";
import { formatDate } from "@/lib/utils";
import { ENTITY_TYPES, ENTITY_TYPE_BAR_COLORS } from "@/lib/constants";
import type { EntityType } from "@/types/api";

function StatCard({
  label,
  value,
  color,
  alert,
  sub,
}: {
  label: string;
  value: number;
  color: string;
  alert?: boolean;
  sub: string;
}) {
  return (
    <div
      className={`bg-white rounded-lg border p-4 ${alert ? "border-amber-200 bg-amber-50" : "border-gray-200"}`}
    >
      <div className={`text-xs mb-1 ${alert ? "text-amber-600 font-medium" : "text-gray-500"}`}>
        {alert && (
          <span className="inline-flex items-center gap-1">
            <svg className="w-3 h-3" fill="currentColor" viewBox="0 0 20 20">
              <path
                fillRule="evenodd"
                d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z"
                clipRule="evenodd"
              />
            </svg>
            {label}
          </span>
        )}
        {!alert && label}
      </div>
      <div className={`text-3xl font-bold ${color}`}>{value}</div>
      <div className={`text-xs mt-1 ${alert ? "text-amber-500" : "text-gray-400"}`}>{sub}</div>
    </div>
  );
}

export default function DashboardPage() {
  const { data: activeData } = useEntities({ status: "active", limit: 1 });
  const { data: candidateData } = useEntities({ status: "candidate", limit: 1 });
  const { data: deprecatedData } = useEntities({ status: "deprecated", limit: 1 });
  const { data: recentData } = useEntities({ limit: 10, sort: "created_at", order: "desc" });

  // type distribution: fetch all with limit=100
  const { data: allData } = useEntities({ limit: 100 });

  const activeCount = activeData?.total ?? 0;
  const candidateCount = candidateData?.total ?? 0;
  const deprecatedCount = deprecatedData?.total ?? 0;
  const totalAliases = 0; // alias count requires separate API, skip for now

  const typeCounts: Record<EntityType, number> = {
    UI_AREA: 0,
    FEATURE: 0,
    INFRA_UNIT: 0,
    API: 0,
    CODE_SYMBOL: 0,
  };
  const totalAll = allData?.total ?? 0;
  allData?.items.forEach((e) => {
    typeCounts[e.type] = (typeCounts[e.type] ?? 0) + 1;
  });

  return (
    <>
      <header className="bg-white border-b border-gray-200 px-6 py-3 flex items-center justify-between shrink-0">
        <h1 className="font-semibold text-gray-900">Dashboard</h1>
      </header>

      <main className="flex-1 overflow-y-auto p-6 space-y-6">
        {/* Stats row */}
        <div className="grid grid-cols-4 gap-4">
          <StatCard label="Active" value={activeCount} color="text-green-600" sub="승인 완료" />
          <StatCard
            label="Candidate"
            value={candidateCount}
            color="text-amber-600"
            alert={candidateCount > 0}
            sub="검토 필요"
          />
          <StatCard label="Deprecated" value={deprecatedCount} color="text-red-400" sub="대체됨" />
          <StatCard label="전체 Entity" value={totalAll} color="text-indigo-600" sub="등록된 entity" />
        </div>

        <div className="grid grid-cols-3 gap-4">
          {/* Type distribution */}
          <div className="bg-white rounded-lg border border-gray-200 p-4 col-span-1">
            <div className="font-medium text-gray-700 mb-3 text-sm">타입별 분포</div>
            <div className="space-y-2.5">
              {ENTITY_TYPES.map((type) => {
                const count = typeCounts[type];
                const pct = totalAll > 0 ? (count / totalAll) * 100 : 0;
                return (
                  <div key={type}>
                    <div className="flex justify-between text-xs mb-1">
                      <span className="text-gray-600">{type}</span>
                      <span className="font-medium">{count}</span>
                    </div>
                    <div className="h-1.5 bg-gray-100 rounded-full">
                      <div
                        className={`h-1.5 rounded-full ${ENTITY_TYPE_BAR_COLORS[type]}`}
                        style={{ width: `${pct}%` }}
                      />
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

          {/* Recent entities */}
          <div className="bg-white rounded-lg border border-gray-200 p-4 col-span-2">
            <div className="flex items-center justify-between mb-3">
              <div className="font-medium text-gray-700 text-sm">최근 등록 Entity</div>
              <Link href="/entities" className="text-xs text-indigo-600 hover:underline">
                전체 보기 →
              </Link>
            </div>
            <table className="w-full text-xs">
              <thead>
                <tr className="text-gray-400 border-b border-gray-100">
                  <th className="text-left pb-2 font-medium">이름</th>
                  <th className="text-left pb-2 font-medium">타입</th>
                  <th className="text-left pb-2 font-medium">상태</th>
                  <th className="text-left pb-2 font-medium">등록일</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-50">
                {recentData?.items.map((entity) => (
                  <tr key={entity.id} className="hover:bg-gray-50">
                    <td className="py-2 font-medium text-indigo-700">
                      <Link href={`/entities/${entity.id}`} className="hover:underline">
                        {entity.canonical_name}
                      </Link>
                    </td>
                    <td className="py-2">
                      <EntityTypeBadge type={entity.type} />
                    </td>
                    <td className="py-2">
                      <EntityStatusBadge status={entity.status} />
                    </td>
                    <td className="py-2 text-gray-400">{formatDate(entity.created_at)}</td>
                  </tr>
                ))}
                {!recentData?.items.length && (
                  <tr>
                    <td colSpan={4} className="py-6 text-center text-gray-400">
                      등록된 entity 없음
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>

        {/* Alert banner */}
        {candidateCount > 0 && (
          <div className="bg-amber-50 border border-amber-200 rounded-lg px-4 py-3 flex items-center justify-between">
            <div className="flex items-center gap-2 text-amber-700 text-sm">
              <svg className="w-4 h-4 shrink-0" fill="currentColor" viewBox="0 0 20 20">
                <path
                  fillRule="evenodd"
                  d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z"
                  clipRule="evenodd"
                />
              </svg>
              <span>
                <strong>{candidateCount}개</strong>의 candidate entity가 검토를 기다리고 있습니다.
              </span>
            </div>
            <Link href="/review" className="text-sm font-medium text-amber-700 underline hover:no-underline">
              지금 검토 →
            </Link>
          </div>
        )}
      </main>
    </>
  );
}
