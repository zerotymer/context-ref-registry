"use client";

import { useCallback } from "react";
import {
  ReactFlow,
  Background,
  Controls,
  MiniMap,
  MarkerType,
  type Node,
  type Edge,
  useNodesState,
  useEdgesState,
} from "@xyflow/react";
import "@xyflow/react/dist/style.css";
import dagre from "dagre";
import type { BundleEntityRead, BundleRelationRead } from "@/types/api";

const NODE_WIDTH = 180;
const NODE_HEIGHT = 50;

const TYPE_BORDER_COLORS: Record<string, string> = {
  UI_AREA: "#6366f1",
  FEATURE: "#7c3aed",
  INFRA_UNIT: "#0d9488",
  API: "#ea580c",
  CODE_SYMBOL: "#0284c7",
  ISSUE: "#e11d48",
};

const TYPE_BG_COLORS: Record<string, string> = {
  UI_AREA: "#eef2ff",
  FEATURE: "#f5f3ff",
  INFRA_UNIT: "#f0fdfa",
  API: "#fff7ed",
  CODE_SYMBOL: "#f0f9ff",
  ISSUE: "#fff1f2",
};

function applyDagreLayout(nodes: Node[], edges: Edge[]): Node[] {
  const g = new dagre.graphlib.Graph();
  g.setDefaultEdgeLabel(() => ({}));
  g.setGraph({ rankdir: "TB", nodesep: 60, ranksep: 80 });

  nodes.forEach((n) => g.setNode(n.id, { width: NODE_WIDTH, height: NODE_HEIGHT }));
  edges.forEach((e) => g.setEdge(e.source, e.target));
  dagre.layout(g);

  return nodes.map((n) => {
    const pos = g.node(n.id);
    return { ...n, position: { x: pos.x - NODE_WIDTH / 2, y: pos.y - NODE_HEIGHT / 2 } };
  });
}

function buildGraph(
  entities: BundleEntityRead[],
  relations: BundleRelationRead[],
  roots: BundleEntityRead[],
): { nodes: Node[]; edges: Edge[] } {
  const rootIds = new Set(roots.map((r) => r.id));

  const nodes: Node[] = entities.map((e) => ({
    id: e.id,
    type: "default",
    data: { label: e.canonical_name },
    position: { x: 0, y: 0 },
    style: {
      background: TYPE_BG_COLORS[e.type] ?? "#f9fafb",
      border: `2px solid ${TYPE_BORDER_COLORS[e.type] ?? "#9ca3af"}`,
      borderWidth: rootIds.has(e.id) ? 3 : 1.5,
      borderRadius: 8,
      fontSize: 11,
      fontWeight: rootIds.has(e.id) ? 700 : 400,
      width: NODE_WIDTH,
      padding: "6px 10px",
    },
  }));

  const edges: Edge[] = relations.map((r, i) => ({
    id: `e-${i}-${r.from_entity_id}-${r.to_entity_id}`,
    source: r.from_entity_id,
    target: r.to_entity_id,
    label: r.relation_type,
    labelStyle: { fontSize: 9, fill: "#6b7280" },
    labelBgStyle: { fill: "#f9fafb", fillOpacity: 0.8 },
    markerEnd: { type: MarkerType.ArrowClosed, width: 14, height: 14 },
    style: { stroke: "#9ca3af", strokeWidth: 1.5 },
    animated: false,
  }));

  return { nodes: applyDagreLayout(nodes, edges), edges };
}

interface Props {
  entities: BundleEntityRead[];
  relations: BundleRelationRead[];
  roots: BundleEntityRead[];
}

export function BundleGraphView({ entities, relations, roots }: Props) {
  const { nodes: initialNodes, edges: initialEdges } = buildGraph(entities, relations, roots);
  const [nodes, , onNodesChange] = useNodesState(initialNodes);
  const [edges, , onEdgesChange] = useEdgesState(initialEdges);

  if (entities.length === 0) {
    return (
      <div className="flex items-center justify-center h-64 text-xs text-gray-400">
        entity 없음
      </div>
    );
  }

  return (
    <div style={{ height: 500 }}>
      <ReactFlow
        nodes={nodes}
        edges={edges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        fitView
        fitViewOptions={{ padding: 0.2 }}
        minZoom={0.3}
        maxZoom={2}
      >
        <Background gap={16} size={1} color="#e5e7eb" />
        <Controls />
        <MiniMap
          nodeColor={(n) => {
            const type = entities.find((e) => e.id === n.id)?.type ?? "";
            return TYPE_BORDER_COLORS[type] ?? "#9ca3af";
          }}
          maskColor="rgba(243,244,246,0.8)"
        />
      </ReactFlow>
    </div>
  );
}
