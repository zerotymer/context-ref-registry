"use client";

import { useMemo } from "react";
import {
  ReactFlow,
  Background,
  Controls,
  Handle,
  Position,
  MarkerType,
  type Node,
  type Edge,
  type NodeProps,
} from "@xyflow/react";
import "@xyflow/react/dist/style.css";
import { ENTITY_TYPE_COLORS } from "@/lib/constants";
import { computeDepths } from "./graph-layout";
import type { ContextBundleResponse, EntityType } from "@/types/api";

// ponytail: BFS-depth top-down layout instead of a dagre/elk dependency.
// Depth flows down (rows), siblings spread horizontally. Swap in dagre if trees get wide.
const COL_W = 230; // horizontal gap between siblings
const ROW_H = 120; // vertical gap between depth levels

type NodeData = {
  label: string;
  type: EntityType;
  isRoot: boolean;
};

function EntityNode({ data }: NodeProps) {
  const { label, type, isRoot } = data as NodeData;
  return (
    <div
      className={`rounded-md border bg-white px-3 py-2 shadow-sm min-w-[150px] max-w-[200px] ${
        isRoot ? "border-indigo-400 ring-2 ring-indigo-200" : "border-gray-200"
      }`}
    >
      <Handle type="target" position={Position.Top} className="!bg-gray-400" />
      <div className="flex items-center gap-1.5">
        <span
          className={`px-1.5 py-0.5 rounded text-[10px] font-medium shrink-0 ${ENTITY_TYPE_COLORS[type]}`}
        >
          {type}
        </span>
        {isRoot && <span className="text-[10px] text-amber-500">root</span>}
      </div>
      <div className="text-xs font-medium text-gray-800 mt-1 truncate">{label}</div>
      <Handle type="source" position={Position.Bottom} className="!bg-gray-400" />
    </div>
  );
}

const nodeTypes = { entity: EntityNode };

export function BundleGraph({ result }: { result: ContextBundleResponse }) {
  const { nodes, edges } = useMemo(() => {
    const rootIds = new Set(result.roots.map((r) => r.id));
    const entityIds = result.entities.map((e) => e.id);
    const depth = computeDepths(entityIds, rootIds, result.relations);

    const rowIndex = new Map<number, number>();
    const nodes: Node[] = result.entities.map((e) => {
      const d = depth.get(e.id) ?? 0;
      const row = rowIndex.get(d) ?? 0;
      rowIndex.set(d, row + 1);
      return {
        id: e.id,
        type: "entity",
        position: { x: row * COL_W, y: d * ROW_H },
        data: { label: e.canonical_name, type: e.type, isRoot: rootIds.has(e.id) },
      };
    });

    const edges: Edge[] = result.relations.map((r, i) => ({
      id: `e${i}`,
      source: r.from_entity_id,
      target: r.to_entity_id,
      label: r.relation_type,
      animated: true,
      labelStyle: { fontSize: 10, fill: "#6b7280" },
      labelBgStyle: { fill: "#fff" },
      style: { stroke: "#6366f1", strokeWidth: 1.5 },
      markerEnd: {
        type: MarkerType.ArrowClosed,
        color: "#6366f1",
        width: 22,
        height: 22,
      },
    }));

    return { nodes, edges };
  }, [result]);

  if (result.entities.length === 0) {
    return <div className="text-xs text-gray-400 text-center py-8">그래프로 그릴 entity가 없습니다</div>;
  }

  return (
    <div className="h-[560px]">
      <ReactFlow
        nodes={nodes}
        edges={edges}
        nodeTypes={nodeTypes}
        fitView
        minZoom={0.1}
        proOptions={{ hideAttribution: true }}
      >
        <Background />
        <Controls showInteractive={false} />
      </ReactFlow>
    </div>
  );
}
