from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Generic, TypeVar

from pydantic import BaseModel, ConfigDict, Field

from app.domain.enums import ContextType, EntityStatus, EntityType, Locale, RelationType

T = TypeVar("T")


# ---------------------------------------------------------------------------
# Common response envelope
# ---------------------------------------------------------------------------


class OkResponse(BaseModel, Generic[T]):
    ok: bool = True
    data: T


class ErrorDetail(BaseModel):
    code: str
    message: str


class ErrorResponse(BaseModel):
    ok: bool = False
    error: ErrorDetail


# ---------------------------------------------------------------------------
# Entity
# ---------------------------------------------------------------------------


class EntityCreate(BaseModel):
    id: uuid.UUID | None = None
    type: EntityType
    canonical_name: str = Field(..., max_length=500)
    description: str | None = None
    status: EntityStatus = EntityStatus.CANDIDATE
    confidence: float = Field(1.0, ge=0.0, le=1.0)


class EntityUpdate(BaseModel):
    canonical_name: str | None = Field(None, max_length=500)
    description: str | None = None
    status: EntityStatus | None = None
    confidence: float | None = Field(None, ge=0.0, le=1.0)
    replacement_entity_id: uuid.UUID | None = None
    deprecation_reason: str | None = None


class EntityRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    type: EntityType
    canonical_name: str
    description: str | None
    status: EntityStatus
    confidence: float
    replacement_entity_id: uuid.UUID | None
    deprecation_reason: str | None
    created_at: datetime
    updated_at: datetime


# ---------------------------------------------------------------------------
# Alias
# ---------------------------------------------------------------------------


class AliasCreate(BaseModel):
    locale: Locale
    alias: str = Field(..., max_length=500)
    is_primary: bool = False


class AliasRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    entity_id: uuid.UUID
    locale: Locale
    alias: str
    is_primary: bool
    is_active: bool
    created_at: datetime


# ---------------------------------------------------------------------------
# Alias resolve
# ---------------------------------------------------------------------------


class ResolveResult(BaseModel):
    result: str  # "not_found" | "resolved" | "ambiguous"
    entity: EntityRead | None = None
    candidates: list[EntityRead] | None = None


# ---------------------------------------------------------------------------
# Context
# ---------------------------------------------------------------------------


class ContextCreate(BaseModel):
    context_type: ContextType
    title: str | None = Field(None, max_length=500)
    body: str
    language: Locale = Locale.KO
    source_ref_id: uuid.UUID | None = None


class ContextRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    entity_id: uuid.UUID
    context_type: ContextType
    title: str | None
    body: str
    language: str
    source_ref_id: uuid.UUID | None
    created_at: datetime
    updated_at: datetime


# ---------------------------------------------------------------------------
# Relation
# ---------------------------------------------------------------------------


class RelationCreate(BaseModel):
    from_entity_id: uuid.UUID
    to_entity_id: uuid.UUID
    relation_type: RelationType
    description: str | None = None
    confidence: float = Field(1.0, ge=0.0, le=1.0)


class RelationRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    from_entity_id: uuid.UUID
    to_entity_id: uuid.UUID
    relation_type: RelationType
    description: str | None
    confidence: float
    created_at: datetime


# ---------------------------------------------------------------------------
# Metadata
# ---------------------------------------------------------------------------


class MetadataUpsert(BaseModel):
    meta_type: str = Field(..., max_length=50)
    data: dict[str, Any]


class MetadataRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    entity_id: uuid.UUID
    meta_type: str
    data: dict[str, Any]
    created_at: datetime
    updated_at: datetime


# ---------------------------------------------------------------------------
# Source ref
# ---------------------------------------------------------------------------


class SourceRefCreate(BaseModel):
    uri: str = Field(..., max_length=2000)
    title: str | None = Field(None, max_length=500)
    version: str | None = Field(None, max_length=100)
    retrieved_at: datetime | None = None


class SourceRefRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    uri: str
    title: str | None
    version: str | None
    retrieved_at: datetime | None
    created_at: datetime


# ---------------------------------------------------------------------------
# Batch Ingest
# ---------------------------------------------------------------------------


class IngestSourceInput(BaseModel):
    type: str = Field(..., max_length=100)
    name: str | None = Field(None, max_length=500)
    uri: str = Field(..., max_length=2000)
    version: str | None = Field(None, max_length=100)
    checksum: str | None = Field(None, max_length=200)


class IngestContextInput(BaseModel):
    context_type: ContextType
    title: str | None = Field(None, max_length=500)
    body: str
    language: Locale = Locale.KO


class IngestEntityInput(BaseModel):
    id: uuid.UUID | None = None
    type: EntityType
    canonical_name: str = Field(..., max_length=500)
    description: str | None = None
    status: EntityStatus = EntityStatus.CANDIDATE
    confidence: float = Field(1.0, ge=0.0, le=1.0)
    aliases: dict[Locale, list[str]] = Field(default_factory=dict)
    contexts: list[IngestContextInput] = Field(default_factory=list)
    metadata: dict[str, Any] | None = None


class IngestRelationInput(BaseModel):
    id: uuid.UUID | None = None
    from_entity_id: uuid.UUID
    to_entity_id: uuid.UUID
    relation_type: RelationType
    description: str | None = None
    confidence: float = Field(1.0, ge=0.0, le=1.0)


class BatchIngestRequest(BaseModel):
    source: IngestSourceInput
    entities: list[IngestEntityInput] = Field(default_factory=list)
    relations: list[IngestRelationInput] = Field(default_factory=list)


class IngestCounts(BaseModel):
    entities: int = 0
    aliases: int = 0
    contexts: int = 0
    relations: int = 0


class BatchIngestResult(BaseModel):
    source_ref_id: uuid.UUID
    created: IngestCounts
    updated: IngestCounts
    warnings: list[str] = Field(default_factory=list)
