"use client";

import { useEffect, useRef } from "react";
import { Graph } from "@antv/g6";
import { ENTITY_TYPE_PIE_COLORS } from "@/lib/constants";
import { computeDegrees } from "./graph-layout";
import type { ContextBundleResponse, EntityType } from "@/types/api";

// ponytail: G6 is imperative canvas, not a React component — drive it via ref +
// effect, destroy on cleanup. d3-force spreads nodes by repulsion; node size
// scales with degree so hubs read bigger (dispersion + relationship density).
const MIN_SIZE = 24;
const SIZE_PER_DEGREE = 6;
const MAX_SIZE = 64;

export function BundleGraph({ result }: { result: ContextBundleResponse }) {
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const container = containerRef.current;
    if (!container || result.entities.length === 0) return;

    const rootIds = new Set(result.roots.map((r) => r.id));
    // roots may not be included in entities; merge + dedup so edges never
    // reference a missing node (G6 throws "Node not found", React Flow didn't).
    const entityById = new Map<string, (typeof result.entities)[number]>();
    for (const e of [...result.roots, ...result.entities]) entityById.set(e.id, e);
    const nodeIds = new Set(entityById.keys());
    const degree = computeDegrees(Array.from(nodeIds), result.relations);

    const data = {
      nodes: Array.from(entityById.values()).map((e) => ({
        id: e.id,
        data: {
          label: e.canonical_name,
          type: e.type as EntityType,
          isRoot: rootIds.has(e.id),
          size: Math.min(MAX_SIZE, MIN_SIZE + (degree.get(e.id) ?? 0) * SIZE_PER_DEGREE),
        },
      })),
      // drop edges whose endpoints were filtered out (e.g. by include_types).
      edges: result.relations
        .filter((r) => nodeIds.has(r.from_entity_id) && nodeIds.has(r.to_entity_id))
        .map((r, i) => ({
          id: `e${i}`,
          source: r.from_entity_id,
          target: r.to_entity_id,
          data: { label: r.relation_type },
        })),
    };

    const graph = new Graph({
      container,
      data,
      autoFit: "view",
      behaviors: ["drag-canvas", "zoom-canvas", "drag-element"],
      layout: {
        type: "d3-force",
        collide: { radius: (d: { data?: { size?: number } }) => (d.data?.size ?? MIN_SIZE) / 2 + 8 },
        manyBody: { strength: -240 },
        link: { distance: 140 },
      },
      node: {
        style: {
          size: (d: { data?: { size?: number } }) => d.data?.size ?? MIN_SIZE,
          fill: (d: { data?: { type?: EntityType } }) =>
            ENTITY_TYPE_PIE_COLORS[d.data?.type as EntityType] ?? "#9ca3af",
          stroke: (d: { data?: { isRoot?: boolean } }) => (d.data?.isRoot ? "#f59e0b" : "#ffffff"),
          lineWidth: (d: { data?: { isRoot?: boolean } }) => (d.data?.isRoot ? 3 : 1),
          labelText: (d: { data?: { label?: string } }) => d.data?.label ?? "",
          labelPlacement: "bottom",
          labelFontSize: 11,
          labelFill: "#374151",
          labelBackground: true,
          labelBackgroundFill: "#ffffff",
          labelBackgroundOpacity: 0.75,
        },
      },
      edge: {
        style: {
          stroke: "#c7d2fe",
          lineWidth: 1.5,
          endArrow: true,
          labelText: (d: { data?: { label?: string } }) => d.data?.label ?? "",
          labelFontSize: 9,
          labelFill: "#6b7280",
          labelBackground: true,
          labelBackgroundFill: "#ffffff",
        },
      },
    });

    // render() is async; StrictMode double-invokes this effect, so defer
    // destroy() until render settles — destroying mid-render crashes G6.
    const ready = graph.render();
    ready.catch(() => {});

    return () => {
      ready.finally(() => graph.destroy());
    };
  }, [result]);

  if (result.entities.length === 0) {
    return <div className="text-xs text-gray-400 text-center py-8">그래프로 그릴 entity가 없습니다</div>;
  }

  return <div ref={containerRef} className="h-[560px] w-full" />;
}
