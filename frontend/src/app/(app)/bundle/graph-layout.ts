import type { ContextBundleResponse } from "@/types/api";

// Undirected degree (connection count) per entity. Drives node size in the
// force graph so hub nodes read bigger — relationship density at a glance.
export function computeDegrees(
  entityIds: string[],
  relations: ContextBundleResponse["relations"],
): Map<string, number> {
  const degree = new Map<string, number>();
  for (const id of entityIds) degree.set(id, 0);
  for (const r of relations) {
    if (degree.has(r.from_entity_id)) degree.set(r.from_entity_id, degree.get(r.from_entity_id)! + 1);
    if (degree.has(r.to_entity_id)) degree.set(r.to_entity_id, degree.get(r.to_entity_id)! + 1);
  }
  return degree;
}
