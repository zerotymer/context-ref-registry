"""Audit log integration tests — Step 2-2."""
import uuid

import pytest
from httpx import AsyncClient
from sqlalchemy import select

from app.db.session import async_session_factory
from app.domain.models import EntityAuditLog


async def _get_audit_logs(action: str | None = None) -> list[EntityAuditLog]:
    async with async_session_factory() as session:
        stmt = select(EntityAuditLog)
        if action:
            stmt = stmt.where(EntityAuditLog.action == action)
        stmt = stmt.order_by(EntityAuditLog.created_at)
        result = await session.execute(stmt)
        return list(result.scalars().all())


async def test_entity_create_writes_audit_log(admin_client: AsyncClient):
    resp = await admin_client.post("/entities", json={
        "type": "FEATURE",
        "canonical_name": "감사 로그 테스트 기능",
    })
    assert resp.status_code == 201
    entity_id = resp.json()["data"]["id"]

    logs = await _get_audit_logs("entity_create")
    assert len(logs) == 1
    log = logs[0]
    assert log.action == "entity_create"
    assert log.target_type == "entity"
    assert log.target_id == entity_id
    assert log.before_snapshot is None
    assert log.after_snapshot is not None
    assert log.after_snapshot["id"] == entity_id
    assert log.actor != ""


async def test_entity_update_writes_audit_log(admin_client: AsyncClient):
    create_resp = await admin_client.post("/entities", json={
        "type": "FEATURE",
        "canonical_name": "수정 전 이름",
    })
    entity_id = create_resp.json()["data"]["id"]

    patch_resp = await admin_client.patch(f"/entities/{entity_id}", json={
        "canonical_name": "수정 후 이름",
    })
    assert patch_resp.status_code == 200

    logs = await _get_audit_logs("entity_update")
    assert len(logs) == 1
    log = logs[0]
    assert log.before_snapshot["canonical_name"] == "수정 전 이름"
    assert log.after_snapshot["canonical_name"] == "수정 후 이름"


async def test_entity_status_change_writes_audit_log(admin_client: AsyncClient):
    create_resp = await admin_client.post("/entities", json={
        "type": "FEATURE",
        "canonical_name": "상태 변경 테스트",
        "status": "candidate",
    })
    entity_id = create_resp.json()["data"]["id"]

    await admin_client.patch(f"/entities/{entity_id}", json={"status": "active"})

    logs = await _get_audit_logs("entity_status_change")
    assert len(logs) == 1
    log = logs[0]
    assert log.before_snapshot["status"] == "candidate"
    assert log.after_snapshot["status"] == "active"


async def test_alias_add_writes_audit_log(admin_client: AsyncClient):
    create_resp = await admin_client.post("/entities", json={
        "type": "FEATURE",
        "canonical_name": "알리아스 테스트",
    })
    entity_id = create_resp.json()["data"]["id"]

    alias_resp = await admin_client.post(f"/entities/{entity_id}/aliases", json={
        "locale": "ko",
        "alias": "테스트 기능",
    })
    assert alias_resp.status_code == 201

    logs = await _get_audit_logs("alias_add")
    assert len(logs) == 1
    log = logs[0]
    assert log.target_type == "alias"
    assert log.after_snapshot["entity_id"] == entity_id
    assert log.after_snapshot["locale"] == "ko"
    assert log.after_snapshot["alias"] == "테스트 기능"


async def test_context_add_writes_audit_log(admin_client: AsyncClient):
    create_resp = await admin_client.post("/entities", json={
        "type": "FEATURE",
        "canonical_name": "컨텍스트 테스트",
    })
    entity_id = create_resp.json()["data"]["id"]

    ctx_resp = await admin_client.post(f"/entities/{entity_id}/contexts", json={
        "context_type": "summary",
        "body": "테스트 설명",
        "language": "ko",
    })
    assert ctx_resp.status_code == 201

    logs = await _get_audit_logs("context_add")
    assert len(logs) == 1
    log = logs[0]
    assert log.target_type == "context"
    assert log.after_snapshot["entity_id"] == entity_id
    assert log.after_snapshot["context_type"] == "summary"
    assert "body" not in (log.after_snapshot or {})


async def test_relation_create_writes_audit_log(admin_client: AsyncClient):
    from_resp = await admin_client.post("/entities", json={"type": "FEATURE", "canonical_name": "출발 기능"})
    to_resp = await admin_client.post("/entities", json={"type": "INFRA_UNIT", "canonical_name": "목적지 인프라"})
    from_id = from_resp.json()["data"]["id"]
    to_id = to_resp.json()["data"]["id"]

    rel_resp = await admin_client.post("/relations", json={
        "from_entity_id": from_id,
        "to_entity_id": to_id,
        "relation_type": "USES",
    })
    assert rel_resp.status_code == 201

    logs = await _get_audit_logs("relation_create")
    assert len(logs) == 1
    log = logs[0]
    assert log.target_type == "relation"
    assert log.after_snapshot["from_entity_id"] == from_id
    assert log.after_snapshot["to_entity_id"] == to_id
    assert log.after_snapshot["relation_type"] == "USES"


async def test_batch_ingest_writes_audit_log(admin_client: AsyncClient):
    ingest_resp = await admin_client.post("/ingest/batch", json={
        "source": {
            "type": "screen_spec",
            "name": "audit-test-source",
            "uri": "file://audit-test.md",
        },
        "entities": [{
            "type": "UI_AREA",
            "canonical_name": "배치 테스트 영역",
            "status": "active",
            "confidence": 1.0,
            "aliases": {},
            "contexts": [],
        }],
        "relations": [],
    })
    assert ingest_resp.status_code == 200

    logs = await _get_audit_logs("batch_ingest")
    assert len(logs) == 1
    log = logs[0]
    assert log.target_type == "batch"
    assert log.after_snapshot["source_uri"] == "file://audit-test.md"
    assert log.after_snapshot["created"]["entities"] == 1


async def test_audit_log_actor_uses_email_for_user_session(admin_client: AsyncClient):
    await admin_client.post("/entities", json={
        "type": "FEATURE",
        "canonical_name": "actor 테스트",
    })

    logs = await _get_audit_logs("entity_create")
    assert len(logs) == 1
    assert "admin@test.com" in logs[0].actor


async def test_audit_log_actor_uses_api_key_name(client: AsyncClient):
    """API key 인증 시 actor는 'api_key:{name}' 형식."""
    async with async_session_factory() as session:
        from app.service.auth_service import AuthService
        svc = AuthService(session)
        user = await svc.create_user(
            email="apikey_user@test.com",
            password="pass1234",
            display_name="API Key User",
            role="admin",
        )
        _, raw_key = await svc.create_api_key(
            name="my-test-key",
            scopes=["write"],
            created_by=user.id,
        )

    resp = await client.post("/entities", json={
        "type": "FEATURE",
        "canonical_name": "API key actor 테스트",
    }, headers={"X-API-Key": raw_key})
    assert resp.status_code == 201

    logs = await _get_audit_logs("entity_create")
    assert len(logs) == 1
    assert logs[0].actor == "api_key:my-test-key"
