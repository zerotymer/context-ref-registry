"use client";

import {
  ReactFlow,
  ReactFlowProvider,
  Background,
  Controls,
  MiniMap,
  MarkerType,
  type Node,
  type Edge,
  useNodesState,
  useEdgesState,
  Panel,
} from "@xyflow/react";
import "@xyflow/react/dist/style.css";
import dagre from "dagre";
import type { BundleEntityRead, BundleRelationRead } from "@/types/api";

const NODE_W = 200;
const NODE_H = 56;

const TYPE_COLOR: Record<string, { bg: string; border: string; text: string }> = {
  UI_AREA:     { bg: "#eef2ff", border: "#6366f1", text: "#4338ca" },
  FEATURE:     { bg: "#f5f3ff", border: "#7c3aed", text: "#6d28d9" },
  INFRA_UNIT:  { bg: "#f0fdfa", border: "#0d9488", text: "#0f766e" },
  API:         { bg: "#fff7ed", border: "#ea580c", text: "#c2410c" },
  CODE_SYMBOL: { bg: "#f0f9ff", border: "#0284c7", text: "#0369a1" },
  ISSUE:       { bg: "#fff1f2", border: "#e11d48", text: "#be123c" },
};
const FALLBACK_COLOR = { bg: "#f9fafb", border: "#9ca3af", text: "#374151" };

const RELATION_COLORS: Record<string, string> = {
  CONTAINS:       "#6366f1",
  RELATED_TO:     "#0d9488",
  USES:           "#ea580c",
  IMPLEMENTED_BY: "#7c3aed",
  READS_FROM:     "#0284c7",
  WRITES_TO:      "#e11d48",
  DEPENDS_ON:     "#d97706",
  CALLS:          "#059669",
};

function applyDagre(nodes: Node[], edges: Edge[]): Node[] {
  const g = new dagre.graphlib.Graph();
  g.setDefaultEdgeLabel(() => ({}));
  g.setGraph({ rankdir: "TB", nodesep: 80, ranksep: 100, marginx: 40, marginy: 40 });
  nodes.forEach((n) => g.setNode(n.id, { width: NODE_W, height: NODE_H }));
  edges.forEach((e) => g.setEdge(e.source, e.target));
  dagre.layout(g);
  return nodes.map((n) => {
    const p = g.node(n.id);
    return { ...n, position: { x: (p?.x ?? 0) - NODE_W / 2, y: (p?.y ?? 0) - NODE_H / 2 } };
  });
}

function buildGraph(
  entities: BundleEntityRead[],
  relations: BundleRelationRead[],
  roots: BundleEntityRead[],
): { nodes: Node[]; edges: Edge[] } {
  const rootIds = new Set(roots.map((r) => r.id));

  const nodes: Node[] = entities.map((e) => {
    const c = TYPE_COLOR[e.type] ?? FALLBACK_COLOR;
    const isRoot = rootIds.has(e.id);
    return {
      id: e.id,
      type: "default",
      data: { label: e.canonical_name },
      position: { x: 0, y: 0 },
      style: {
        background: c.bg,
        border: `${isRoot ? 3 : 1.5}px solid ${c.border}`,
        borderRadius: 8,
        color: c.text,
        fontSize: 11,
        fontWeight: isRoot ? 700 : 500,
        width: NODE_W,
        minHeight: NODE_H,
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        padding: "8px 12px",
        boxShadow: isRoot ? `0 0 0 3px ${c.border}40` : "none",
      },
    };
  });

  const edges: Edge[] = relations.map((r, i) => {
    const color = RELATION_COLORS[r.relation_type] ?? "#374151";
    return {
      id: `edge-${i}-${r.from_entity_id.slice(0, 8)}-${r.to_entity_id.slice(0, 8)}`,
      source: r.from_entity_id,
      target: r.to_entity_id,
      type: "smoothstep",
      label: r.relation_type,
      labelStyle: { fontSize: 9, fill: color, fontWeight: 600 },
      labelBgStyle: { fill: "#ffffff", fillOpacity: 0.9 },
      labelBgPadding: [4, 3] as [number, number],
      labelBgBorderRadius: 3,
      markerEnd: { type: MarkerType.ArrowClosed, color, width: 16, height: 16 },
      style: { stroke: color, strokeWidth: 2 },
      animated: false,
      zIndex: 1,
    };
  });

  return { nodes: applyDagre(nodes, edges), edges };
}

function LegendPanel({ entities }: { entities: BundleEntityRead[] }) {
  const seen = new Set<string>();
  const types = entities.map((e) => e.type).filter((t) => { if (seen.has(t)) return false; seen.add(t); return true; });
  return (
    <Panel position="top-right">
      <div className="bg-white border border-gray-200 rounded-lg px-3 py-2 shadow-sm text-xs space-y-1">
        {types.map((t) => {
          const c = TYPE_COLOR[t] ?? FALLBACK_COLOR;
          return (
            <div key={t} className="flex items-center gap-1.5">
              <span className="w-2.5 h-2.5 rounded-sm border" style={{ background: c.bg, borderColor: c.border }} />
              <span style={{ color: c.text }}>{t}</span>
            </div>
          );
        })}
      </div>
    </Panel>
  );
}

function FlowInner({
  entities,
  relations,
  roots,
}: {
  entities: BundleEntityRead[];
  relations: BundleRelationRead[];
  roots: BundleEntityRead[];
}) {
  const { nodes: initNodes, edges: initEdges } = buildGraph(entities, relations, roots);
  const [nodes, , onNodesChange] = useNodesState(initNodes);
  const [edges, , onEdgesChange] = useEdgesState(initEdges);

  return (
    <ReactFlow
      nodes={nodes}
      edges={edges}
      onNodesChange={onNodesChange}
      onEdgesChange={onEdgesChange}
      fitView
      fitViewOptions={{ padding: 0.25 }}
      minZoom={0.2}
      maxZoom={2.5}
      defaultEdgeOptions={{ zIndex: 10 }}
      elevateEdgesOnSelect
    >
      <Background gap={20} size={1} color="#e5e7eb" />
      <Controls />
      <MiniMap
        nodeColor={(n) => {
          const type = entities.find((e) => e.id === n.id)?.type ?? "";
          return (TYPE_COLOR[type] ?? FALLBACK_COLOR).border;
        }}
        maskColor="rgba(243,244,246,0.75)"
        style={{ border: "1px solid #e5e7eb", borderRadius: 6 }}
      />
      <LegendPanel entities={entities} />
    </ReactFlow>
  );
}

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

  return (
    <ReactFlowProvider>
      <div style={{ height: 520 }}>
        <FlowInner entities={entities} relations={relations} roots={roots} />
      </div>
    </ReactFlowProvider>
  );
}
