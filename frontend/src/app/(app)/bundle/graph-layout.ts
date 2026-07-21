import type { ContextBundleResponse } from "@/types/api";

// BFS distance from any root over the undirected relation graph.
// Disconnected nodes (no root path) land in a trailing column.
export function computeDepths(
  entityIds: string[],
  rootIds: Set<string>,
  relations: ContextBundleResponse["relations"],
): Map<string, number> {
  const adj = new Map<string, string[]>();
  for (const id of entityIds) adj.set(id, []);
  for (const r of relations) {
    adj.get(r.from_entity_id)?.push(r.to_entity_id);
    adj.get(r.to_entity_id)?.push(r.from_entity_id);
  }
  const depth = new Map<string, number>();
  const queue: string[] = [];
  for (const id of entityIds) {
    if (rootIds.has(id)) {
      depth.set(id, 0);
      queue.push(id);
    }
  }
  while (queue.length) {
    const cur = queue.shift()!;
    const d = depth.get(cur)!;
    for (const nb of adj.get(cur) ?? []) {
      if (!depth.has(nb)) {
        depth.set(nb, d + 1);
        queue.push(nb);
      }
    }
  }
  const maxDepth = Math.max(0, ...Array.from(depth.values()));
  for (const id of entityIds) if (!depth.has(id)) depth.set(id, maxDepth + 1);
  return depth;
}
