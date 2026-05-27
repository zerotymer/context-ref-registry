import type { EntityType, EntityStatus, ContextType, RelationType } from "@/types/api";

export const ENTITY_TYPES: EntityType[] = [
  "UI_AREA",
  "FEATURE",
  "INFRA_UNIT",
  "API",
  "CODE_SYMBOL",
];

export const ENTITY_STATUSES: EntityStatus[] = [
  "candidate",
  "active",
  "deprecated",
  "archived",
];

export const CONTEXT_TYPES: ContextType[] = [
  "summary",
  "details",
  "business_rule",
  "validation_rule",
  "implementation_hint",
  "security_note",
  "infra_note",
  "compatibility_note",
  "exception_case",
];

export const RELATION_TYPES: RelationType[] = [
  "CONTAINS",
  "RELATED_TO",
  "USES",
  "IMPLEMENTED_BY",
  "READS_FROM",
  "WRITES_TO",
  "DEPENDS_ON",
  "CALLS",
];

export const ENTITY_TYPE_COLORS: Record<EntityType, string> = {
  UI_AREA: "bg-indigo-50 text-indigo-700",
  FEATURE: "bg-violet-50 text-violet-700",
  INFRA_UNIT: "bg-teal-50 text-teal-700",
  API: "bg-orange-50 text-orange-700",
  CODE_SYMBOL: "bg-sky-50 text-sky-700",
};

export const ENTITY_TYPE_BAR_COLORS: Record<EntityType, string> = {
  UI_AREA: "bg-indigo-500",
  FEATURE: "bg-violet-400",
  INFRA_UNIT: "bg-teal-400",
  API: "bg-orange-400",
  CODE_SYMBOL: "bg-sky-400",
};

export const CONTEXT_TYPE_COLORS: Record<ContextType, string> = {
  summary: "bg-green-50 text-green-700",
  details: "bg-blue-50 text-blue-700",
  business_rule: "bg-blue-50 text-blue-700",
  validation_rule: "bg-yellow-50 text-yellow-700",
  implementation_hint: "bg-purple-50 text-purple-700",
  security_note: "bg-red-50 text-red-700",
  infra_note: "bg-orange-50 text-orange-700",
  compatibility_note: "bg-gray-50 text-gray-700",
  exception_case: "bg-pink-50 text-pink-700",
};
