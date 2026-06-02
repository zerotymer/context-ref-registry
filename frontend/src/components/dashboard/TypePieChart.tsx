"use client";

import { ENTITY_TYPES, ENTITY_TYPE_PIE_COLORS } from "@/lib/constants";
import type { EntityType } from "@/types/api";

const SIZE = 140;
const CX = SIZE / 2;
const CY = SIZE / 2;
const R = 52;
const INNER_R = 28;

function polarToXY(angleDeg: number, r: number) {
  const rad = ((angleDeg - 90) * Math.PI) / 180;
  return {
    x: CX + r * Math.cos(rad),
    y: CY + r * Math.sin(rad),
  };
}

function slicePath(startDeg: number, endDeg: number): string {
  const large = endDeg - startDeg > 180 ? 1 : 0;
  const s = polarToXY(startDeg, R);
  const e = polarToXY(endDeg, R);
  const si = polarToXY(startDeg, INNER_R);
  const ei = polarToXY(endDeg, INNER_R);
  return [
    `M ${s.x} ${s.y}`,
    `A ${R} ${R} 0 ${large} 1 ${e.x} ${e.y}`,
    `L ${ei.x} ${ei.y}`,
    `A ${INNER_R} ${INNER_R} 0 ${large} 0 ${si.x} ${si.y}`,
    "Z",
  ].join(" ");
}

export function TypePieChart({
  typeCounts,
  total,
}: {
  typeCounts: Record<EntityType, number>;
  total: number;
}) {
  if (total === 0) {
    return (
      <div className="flex items-center justify-center h-32 text-gray-400 text-xs">
        데이터 없음
      </div>
    );
  }

  let cursor = 0;
  const slices = ENTITY_TYPES.map((type) => {
    const count = typeCounts[type] ?? 0;
    const deg = (count / total) * 360;
    const start = cursor;
    cursor += deg;
    return { type, count, start, end: cursor };
  }).filter((s) => s.count > 0);

  return (
    <div className="flex items-center gap-4">
      <svg width={SIZE} height={SIZE} viewBox={`0 0 ${SIZE} ${SIZE}`} className="shrink-0">
        {slices.map((s) => (
          <path
            key={s.type}
            d={slicePath(s.start, s.end)}
            fill={ENTITY_TYPE_PIE_COLORS[s.type]}
            stroke="white"
            strokeWidth={1.5}
          />
        ))}
        <text
          x={CX}
          y={CY - 5}
          textAnchor="middle"
          dominantBaseline="middle"
          className="text-xs fill-gray-500"
          fontSize={10}
        >
          합계
        </text>
        <text
          x={CX}
          y={CY + 9}
          textAnchor="middle"
          dominantBaseline="middle"
          className="font-bold fill-gray-700"
          fontSize={14}
          fontWeight={700}
        >
          {total}
        </text>
      </svg>

      <ul className="flex-1 space-y-1.5 text-xs">
        {ENTITY_TYPES.map((type) => {
          const count = typeCounts[type] ?? 0;
          const pct = total > 0 ? ((count / total) * 100).toFixed(0) : "0";
          return (
            <li key={type} className="flex items-center gap-1.5">
              <span
                className="inline-block w-2.5 h-2.5 rounded-sm shrink-0"
                style={{ backgroundColor: ENTITY_TYPE_PIE_COLORS[type] }}
              />
              <span className="text-gray-600 truncate flex-1">{type}</span>
              <span className="font-medium text-gray-800">{count}</span>
              <span className="text-gray-400 w-8 text-right">{pct}%</span>
            </li>
          );
        })}
      </ul>
    </div>
  );
}
