export type EntityType = "UI_AREA" | "FEATURE" | "INFRA_UNIT" | "API" | "CODE_SYMBOL";
export type EntityStatus = "candidate" | "active" | "deprecated" | "archived";
export type ContextType =
  | "summary"
  | "details"
  | "business_rule"
  | "validation_rule"
  | "implementation_hint"
  | "security_note"
  | "infra_note"
  | "compatibility_note"
  | "exception_case";
export type RelationType =
  | "CONTAINS"
  | "RELATED_TO"
  | "USES"
  | "IMPLEMENTED_BY"
  | "READS_FROM"
  | "WRITES_TO"
  | "DEPENDS_ON"
  | "CALLS";
export type Locale = "ko" | "en";

export interface ApiResponse<T> {
  ok: boolean;
  data?: T;
  error?: { code: string; message: string };
}

export interface EntityRead {
  id: string;
  type: EntityType;
  canonical_name: string;
  description: string | null;
  status: EntityStatus;
  confidence: number;
  replacement_entity_id: string | null;
  deprecation_reason: string | null;
  created_at: string;
  updated_at: string;
}

export interface EntityListResponse {
  items: EntityRead[];
  total: number;
  limit: number;
  offset: number;
}

export interface EntityCreate {
  type: EntityType;
  canonical_name: string;
  description?: string;
  status?: EntityStatus;
  confidence?: number;
}

export interface EntityUpdate {
  canonical_name?: string;
  description?: string;
  status?: EntityStatus;
  confidence?: number;
  replacement_entity_id?: string;
  deprecation_reason?: string;
}

export interface AliasRead {
  id: string;
  entity_id: string;
  locale: Locale;
  alias: string;
  is_primary: boolean;
  is_active: boolean;
  created_at: string;
}

export interface AliasCreate {
  locale: Locale;
  alias: string;
  is_primary?: boolean;
}

export interface ContextRead {
  id: string;
  entity_id: string;
  context_type: ContextType;
  title: string | null;
  body: string;
  language: string;
  source_ref_id: string | null;
  created_at: string;
  updated_at: string;
}

export interface ContextCreate {
  context_type: ContextType;
  title?: string;
  body: string;
  language?: Locale;
}

export interface RelationRead {
  id: string;
  from_entity_id: string;
  to_entity_id: string;
  relation_type: RelationType;
  description: string | null;
  confidence: number;
  created_at: string;
}

export interface SearchResult extends EntityRead {
  match_reason: string;
}

export interface BundleEntityRead {
  id: string;
  type: EntityType;
  canonical_name: string;
  status: EntityStatus;
}

export interface BundleContextRead {
  entity_id: string;
  context_type: ContextType;
  body: string;
}

export interface BundleRelationRead {
  from_entity_id: string;
  to_entity_id: string;
  relation_type: RelationType;
}

export interface DeprecatedWarning {
  type: string;
  entity_id: string;
  message: string;
  replacement_entity_id: string | null;
}

export interface ContextBundleRequest {
  root_ids: string[];
  include_relations?: RelationType[];
  include_types?: EntityType[];
  max_depth?: number;
  token_budget?: number;
  language?: Locale;
}

export interface ContextBundleResponse {
  roots: BundleEntityRead[];
  entities: BundleEntityRead[];
  contexts: BundleContextRead[];
  relations: BundleRelationRead[];
  warnings: DeprecatedWarning[];
  ambiguities: unknown[];
}
