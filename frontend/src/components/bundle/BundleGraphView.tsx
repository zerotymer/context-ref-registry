"use client";

import { Canvas, Node, Edge, MarkerArrow, Label, type NodeData, type EdgeData } from "reaflow";
import type { BundleEntityRead, BundleRelationRead } from "@/types/api";

const TYPE_COLOR: Record<string, { bg: string; border: string; text: string }> = {
  UI_AREA:     { bg: "#eef2ff", border: "#6366f1", text: "#4338ca" },
  FEATURE:     { bg: "#f5f3ff", border: "#7c3aed", text: "#6d28d9" },
  INFRA_UNIT:  { bg: "#f0fdfa", border: "#0d9488", text: "#0f766e" },
  API:         { bg: "#fff7ed", border: "#ea580c", text: "#c2410c" },
  CODE_SYMBOL: { bg: "#f0f9ff", border: "#0284c7", text: "#0369a1" },
  ISSUE:       { bg: "#fff1f2", border: "#e11d48", text: "#be123c" },
};
const FALLBACK = { bg: "#f9fafb", border: "#9ca3af", text: "#374151" };

const RELATION_COLOR: Record<string, string> = {
  CONTAINS:       "#6366f1",
  RELATED_TO:     "#0d9488",
  USES:           "#ea580c",
  IMPLEMENTED_BY: "#7c3aed",
  READS_FROM:     "#0284c7",
  WRITES_TO:      "#e11d48",
  DEPENDS_ON:     "#d97706",
  CALLS:          "#059669",
};

interface Props {
  entities: BundleEntityRead[];
  relations: BundleRelationRead[];
  roots: BundleEntityRead[];
}

export function BundleGraphView({ entities, relations, roots }: Props) {
  if (entities.length === 0) {
    return (
      <div className="flex items-center justify-center h-64 text-xs text-gray-400">
        entity 없음
      </div>
    );
  }

  const rootIds = new Set(roots.map((r) => r.id));

  const nodes: NodeData[] = entities.map((e) => ({
    id: e.id,
    text: e.canonical_name,
    width: 200,
    height: 44,
    data: { type: e.type, isRoot: rootIds.has(e.id) },
  }));

  const edges: EdgeData[] = relations.map((r, i) => ({
    id: `edge-${i}-${r.from_entity_id.slice(0, 6)}-${r.to_entity_id.slice(0, 6)}`,
    from: r.from_entity_id,
    to: r.to_entity_id,
    text: r.relation_type,
  }));

  return (
    <div style={{ height: 520, border: "1px solid #e5e7eb", borderRadius: 8, overflow: "hidden" }}>
      <Canvas
        nodes={nodes}
        edges={edges}
        fit
        readonly
        direction="DOWN"
        maxHeight={520}
        layoutOptions={{
          "elk.layered.spacing.nodeNodeBetweenLayers": "60",
          "elk.spacing.nodeNode": "40",
        }}
        arrow={
          <MarkerArrow style={{ fill: "#6b7280" }} />
        }
        node={(nodeProps) => {
          const d = nodeProps.properties?.data ?? {};
          const c = TYPE_COLOR[d.type] ?? FALLBACK;
          return (
            <Node
              {...nodeProps}
              style={{
                fill: c.bg,
                stroke: c.border,
                strokeWidth: d.isRoot ? 3 : 1.5,
              }}
              label={
                <Label
                  style={{ fill: c.text, fontWeight: d.isRoot ? 700 : 500, fontSize: 11 }}
                />
              }
            />
          );
        }}
        edge={(edgeProps) => {
          const relType = edgeProps.properties?.text ?? "";
          const color = RELATION_COLOR[relType] ?? "#6b7280";
          return (
            <Edge
              {...edgeProps}
              style={{ stroke: color, strokeWidth: 2 }}
              label={
                <Label
                  style={{ fill: color, fontSize: 9, fontWeight: 600 }}
                />
              }
            />
          );
        }}
      />
    </div>
  );
}
