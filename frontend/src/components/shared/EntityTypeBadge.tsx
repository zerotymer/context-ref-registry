import type { EntityType } from "@/types/api";
import { ENTITY_TYPE_COLORS } from "@/lib/constants";

export function EntityTypeBadge({ type }: { type: EntityType }) {
  return (
    <span
      className={`px-1.5 py-0.5 rounded text-xs font-medium ${ENTITY_TYPE_COLORS[type]}`}
    >
      {type}
    </span>
  );
}
