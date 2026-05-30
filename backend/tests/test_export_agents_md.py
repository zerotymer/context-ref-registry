"""Tests for GET /export/agents-md endpoint."""
import pytest
from httpx import AsyncClient


async def _create_entity(admin_client: AsyncClient, etype: str, name: str, status: str = "active") -> dict:
    r = await admin_client.post("/entities", json={"type": etype, "canonical_name": name, "status": status})
    assert r.status_code == 201
    return r.json()["data"]


async def _create_relation(admin_client: AsyncClient, from_id: str, to_id: str, rtype: str) -> None:
    r = await admin_client.post(
        "/relations",
        json={"from_entity_id": from_id, "to_entity_id": to_id, "relation_type": rtype},
    )
    assert r.status_code == 201


async def _add_context(admin_client: AsyncClient, entity_id: str, context_type: str, body: str) -> None:
    r = await admin_client.post(
        f"/entities/{entity_id}/contexts",
        json={"context_type": context_type, "body": body, "language": "ko"},
    )
    assert r.status_code == 201


@pytest.mark.asyncio
async def test_agents_md_returns_text(admin_client: AsyncClient):
    entity = await _create_entity(admin_client, "FEATURE", "결제 처리")
    r = await admin_client.get(f"/export/agents-md?root_ids={entity['id']}")
    assert r.status_code == 200
    assert "text/plain" in r.headers["content-type"]


@pytest.mark.asyncio
async def test_agents_md_contains_entity_name_and_id(admin_client: AsyncClient):
    entity = await _create_entity(admin_client, "FEATURE", "결제 처리")
    r = await admin_client.get(f"/export/agents-md?root_ids={entity['id']}")
    assert r.status_code == 200
    body = r.text
    assert "결제 처리" in body
    assert entity["id"] in body


@pytest.mark.asyncio
async def test_agents_md_entity_type_section(admin_client: AsyncClient):
    ui = await _create_entity(admin_client, "UI_AREA", "검색 영역")
    feat = await _create_entity(admin_client, "FEATURE", "검색 기능")
    await _create_relation(admin_client, feat["id"], ui["id"], "USES")

    r = await admin_client.get(f"/export/agents-md?root_ids={feat['id']}&max_depth=1")
    assert r.status_code == 200
    body = r.text
    assert "## UI_AREA" in body
    assert "## FEATURE" in body


@pytest.mark.asyncio
async def test_agents_md_context_included(admin_client: AsyncClient):
    entity = await _create_entity(admin_client, "FEATURE", "주문 처리")
    await _add_context(admin_client, entity["id"], "summary", "주문을 처리하는 핵심 기능입니다.")
    await _add_context(admin_client, entity["id"], "business_rule", "재고 0 이면 주문 불가")

    r = await admin_client.get(f"/export/agents-md?root_ids={entity['id']}")
    assert r.status_code == 200
    body = r.text
    assert "주문을 처리하는 핵심 기능입니다." in body
    assert "재고 0 이면 주문 불가" in body
    assert "#### summary" in body
    assert "#### business_rule" in body


@pytest.mark.asyncio
async def test_agents_md_deprecated_warning(admin_client: AsyncClient):
    entity = await _create_entity(admin_client, "FEATURE", "구형 검색", status="deprecated")
    r = await admin_client.get(f"/export/agents-md?root_ids={entity['id']}")
    assert r.status_code == 200
    body = r.text
    assert "⚠️" in body
    assert "deprecated" in body
    assert entity["id"] in body


@pytest.mark.asyncio
async def test_agents_md_relations_table(admin_client: AsyncClient):
    feat = await _create_entity(admin_client, "FEATURE", "알림 기능")
    infra = await _create_entity(admin_client, "INFRA_UNIT", "메일 서버")
    await _create_relation(admin_client, feat["id"], infra["id"], "USES")

    r = await admin_client.get(f"/export/agents-md?root_ids={feat['id']}&max_depth=1")
    assert r.status_code == 200
    body = r.text
    assert "## Relations" in body
    assert "USES" in body


@pytest.mark.asyncio
async def test_agents_md_not_found_returns_404(admin_client: AsyncClient):
    import uuid
    fake_id = str(uuid.uuid4())
    r = await admin_client.get(f"/export/agents-md?root_ids={fake_id}")
    assert r.status_code == 404


@pytest.mark.asyncio
async def test_agents_md_token_budget_respected(admin_client: AsyncClient):
    entity = await _create_entity(admin_client, "FEATURE", "토큰 테스트")
    await _add_context(admin_client, entity["id"], "exception_case", "x" * 600)
    await _add_context(admin_client, entity["id"], "summary", "간단 요약")

    r = await admin_client.get(f"/export/agents-md?root_ids={entity['id']}&token_budget=100")
    assert r.status_code == 200
    body = r.text
    assert "간단 요약" in body
    assert "x" * 600 not in body


@pytest.mark.asyncio
async def test_agents_md_header_and_generated_line(admin_client: AsyncClient):
    entity = await _create_entity(admin_client, "INFRA_UNIT", "DB 클러스터")
    r = await admin_client.get(f"/export/agents-md?root_ids={entity['id']}")
    assert r.status_code == 200
    body = r.text
    assert "# Context Registry" in body
    assert "> Generated:" in body
