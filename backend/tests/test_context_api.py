"""Context API tests — Step 5."""
import uuid

from httpx import AsyncClient


async def _create_entity(client: AsyncClient, entity_type: str = "FEATURE") -> str:
    resp = await client.post("/entities", json={"type": entity_type, "canonical_name": "테스트 엔티티"})
    assert resp.status_code == 201
    return resp.json()["data"]["id"]


async def test_add_context_returns_201(client: AsyncClient):
    entity_id = await _create_entity(client)
    resp = await client.post(f"/entities/{entity_id}/contexts", json={
        "context_type": "summary",
        "title": "기능 요약",
        "body": "조건에 따라 사용자 목록을 조회하는 기능",
        "language": "ko",
    })
    assert resp.status_code == 201
    data = resp.json()["data"]
    assert data["entity_id"] == entity_id
    assert data["context_type"] == "summary"
    assert data["body"] == "조건에 따라 사용자 목록을 조회하는 기능"
    assert data["language"] == "ko"
    uuid.UUID(data["id"])


async def test_add_context_entity_not_found(client: AsyncClient):
    resp = await client.post(f"/entities/{uuid.uuid4()}/contexts", json={
        "context_type": "summary",
        "body": "내용",
        "language": "ko",
    })
    assert resp.status_code == 404
    body = resp.json()
    assert body["ok"] is False
    assert body["error"]["code"] == "ENTITY_NOT_FOUND"


async def test_list_contexts_returns_all(client: AsyncClient):
    entity_id = await _create_entity(client)
    for ct, body in [("summary", "요약 내용"), ("business_rule", "비즈니스 규칙"), ("implementation_hint", "구현 힌트")]:
        await client.post(f"/entities/{entity_id}/contexts", json={
            "context_type": ct,
            "body": body,
            "language": "ko",
        })

    resp = await client.get(f"/entities/{entity_id}/contexts")
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert len(data) == 3


async def test_list_contexts_filter_by_context_type(client: AsyncClient):
    entity_id = await _create_entity(client)
    await client.post(f"/entities/{entity_id}/contexts", json={
        "context_type": "summary", "body": "요약", "language": "ko"
    })
    await client.post(f"/entities/{entity_id}/contexts", json={
        "context_type": "business_rule", "body": "규칙", "language": "ko"
    })

    resp = await client.get(f"/entities/{entity_id}/contexts?context_type=summary")
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert len(data) == 1
    assert data[0]["context_type"] == "summary"


async def test_list_contexts_filter_by_language(client: AsyncClient):
    entity_id = await _create_entity(client)
    await client.post(f"/entities/{entity_id}/contexts", json={
        "context_type": "summary", "body": "요약", "language": "ko"
    })
    await client.post(f"/entities/{entity_id}/contexts", json={
        "context_type": "summary", "body": "Summary", "language": "en"
    })

    resp = await client.get(f"/entities/{entity_id}/contexts?language=en")
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert len(data) == 1
    assert data[0]["language"] == "en"
    assert data[0]["body"] == "Summary"


async def test_list_contexts_empty(client: AsyncClient):
    entity_id = await _create_entity(client)
    resp = await client.get(f"/entities/{entity_id}/contexts")
    assert resp.status_code == 200
    assert resp.json()["data"] == []


async def test_list_contexts_entity_not_found(client: AsyncClient):
    resp = await client.get(f"/entities/{uuid.uuid4()}/contexts")
    assert resp.status_code == 404
    body = resp.json()
    assert body["ok"] is False
    assert body["error"]["code"] == "ENTITY_NOT_FOUND"
