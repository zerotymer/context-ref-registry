"""Unit tests for Pydantic v2 domain schemas — no DB required."""
import uuid

import pytest
from pydantic import ValidationError

from app.domain.enums import ContextType, EntityStatus, EntityType, Locale, RelationType
from app.domain.schemas import (
    AliasCreate,
    ContextCreate,
    EntityCreate,
    EntityUpdate,
    ErrorDetail,
    ErrorResponse,
    MetadataUpsert,
    OkResponse,
    RelationCreate,
    ResolveResult,
    SourceRefCreate,
)


# ---------------------------------------------------------------------------
# EntityCreate
# ---------------------------------------------------------------------------


def test_entity_create_defaults():
    e = EntityCreate(type=EntityType.FEATURE, canonical_name="사용자 검색")
    assert e.status == EntityStatus.ACTIVE
    assert e.confidence == 1.0
    assert e.id is None


def test_entity_create_with_explicit_id():
    uid = uuid.uuid4()
    e = EntityCreate(type=EntityType.UI_AREA, canonical_name="검색 영역", id=uid)
    assert e.id == uid


def test_entity_create_invalid_type():
    with pytest.raises(ValidationError):
        EntityCreate(type="UNKNOWN_TYPE", canonical_name="foo")


def test_entity_create_confidence_out_of_range():
    with pytest.raises(ValidationError):
        EntityCreate(type=EntityType.API, canonical_name="API", confidence=1.5)
    with pytest.raises(ValidationError):
        EntityCreate(type=EntityType.API, canonical_name="API", confidence=-0.1)


# ---------------------------------------------------------------------------
# EntityUpdate
# ---------------------------------------------------------------------------


def test_entity_update_all_optional():
    u = EntityUpdate()
    assert u.canonical_name is None
    assert u.status is None


def test_entity_update_status_to_deprecated():
    replacement = uuid.uuid4()
    u = EntityUpdate(
        status=EntityStatus.DEPRECATED,
        replacement_entity_id=replacement,
        deprecation_reason="기능 분리",
    )
    assert u.status == EntityStatus.DEPRECATED
    assert u.replacement_entity_id == replacement


# ---------------------------------------------------------------------------
# AliasCreate
# ---------------------------------------------------------------------------


def test_alias_create_valid():
    a = AliasCreate(locale=Locale.KO, alias="사용자 검색")
    assert a.is_primary is False
    assert a.locale == Locale.KO


def test_alias_create_invalid_locale():
    with pytest.raises(ValidationError):
        AliasCreate(locale="jp", alias="ユーザー検索")


# ---------------------------------------------------------------------------
# ContextCreate
# ---------------------------------------------------------------------------


def test_context_create_valid():
    c = ContextCreate(context_type=ContextType.SUMMARY, body="요약 내용")
    assert c.language == Locale.KO
    assert c.source_ref_id is None


def test_context_create_invalid_type():
    with pytest.raises(ValidationError):
        ContextCreate(context_type="UNKNOWN", body="body")


# ---------------------------------------------------------------------------
# RelationCreate
# ---------------------------------------------------------------------------


def test_relation_create_valid():
    r = RelationCreate(
        from_entity_id=uuid.uuid4(),
        to_entity_id=uuid.uuid4(),
        relation_type=RelationType.CONTAINS,
    )
    assert r.confidence == 1.0


def test_relation_create_invalid_type():
    with pytest.raises(ValidationError):
        RelationCreate(
            from_entity_id=uuid.uuid4(),
            to_entity_id=uuid.uuid4(),
            relation_type="INVALID",
        )


# ---------------------------------------------------------------------------
# MetadataUpsert
# ---------------------------------------------------------------------------


def test_metadata_upsert_arbitrary_data():
    m = MetadataUpsert(meta_type="ui_area", data={"component_hint": "UserSearchFilter", "route_hint": "/users"})
    assert m.data["component_hint"] == "UserSearchFilter"


# ---------------------------------------------------------------------------
# SourceRefCreate
# ---------------------------------------------------------------------------


def test_source_ref_create_valid():
    s = SourceRefCreate(uri="https://example.com/docs", title="API 문서")
    assert s.retrieved_at is None


# ---------------------------------------------------------------------------
# Common response envelope
# ---------------------------------------------------------------------------


def test_ok_response_wraps_dict():
    r = OkResponse[dict](data={"id": "abc"})
    assert r.ok is True
    assert r.data["id"] == "abc"


def test_error_response_structure():
    r = ErrorResponse(error=ErrorDetail(code="NOT_FOUND", message="entity not found"))
    assert r.ok is False
    assert r.error.code == "NOT_FOUND"


# ---------------------------------------------------------------------------
# ResolveResult
# ---------------------------------------------------------------------------


def test_resolve_result_not_found():
    r = ResolveResult(result="not_found")
    assert r.entity is None
    assert r.candidates is None


def test_resolve_result_invalid_no_entity_for_resolved():
    # result="resolved" with entity=None is schema-valid (no strict enum check),
    # but business logic enforces it — just ensure it instantiates.
    r = ResolveResult(result="resolved", entity=None)
    assert r.result == "resolved"
