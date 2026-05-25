"""Entity CRUD API tests — Step 3."""
import uuid

from httpx import AsyncClient


async def test_create_entity_returns_201(client: AsyncClient):
    response = await client.post("/entities", json={
        "type": "FEATURE",
        "canonical_name": "사용자 검색",
    })
    assert response.status_code == 201
    body = response.json()
    assert body["ok"] is True
    uuid.UUID(body["data"]["id"])  # valid UUID


async def test_create_entity_with_explicit_id(client: AsyncClient):
    entity_id = str(uuid.uuid4())
    response = await client.post("/entities", json={
        "id": entity_id,
        "type": "UI_AREA",
        "canonical_name": "검색 조건 영역",
    })
    assert response.status_code == 201
    assert response.json()["data"]["id"] == entity_id


async def test_get_entity_returns_200(client: AsyncClient):
    create_resp = await client.post("/entities", json={
        "type": "INFRA_UNIT",
        "canonical_name": "사용자 DB",
    })
    entity_id = create_resp.json()["data"]["id"]

    response = await client.get(f"/entities/{entity_id}")
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["id"] == entity_id
    assert data["type"] == "INFRA_UNIT"
    assert data["canonical_name"] == "사용자 DB"
    assert data["status"] == "candidate"


async def test_get_entity_not_found(client: AsyncClient):
    response = await client.get(f"/entities/{uuid.uuid4()}")
    assert response.status_code == 404
    body = response.json()
    assert body["ok"] is False
    assert body["error"]["code"] == "ENTITY_NOT_FOUND"


async def test_patch_entity_updates_fields(client: AsyncClient):
    create_resp = await client.post("/entities", json={
        "type": "FEATURE",
        "canonical_name": "원래 이름",
    })
    entity_id = create_resp.json()["data"]["id"]

    patch_resp = await client.patch(f"/entities/{entity_id}", json={
        "canonical_name": "수정된 이름",
        "status": "active",
    })
    assert patch_resp.status_code == 200
    data = patch_resp.json()["data"]
    assert data["canonical_name"] == "수정된 이름"
    assert data["status"] == "active"


async def test_patch_entity_type_not_changeable(client: AsyncClient):
    """type 필드는 EntityUpdate 스키마에 없으므로 extra 필드로 무시된다."""
    create_resp = await client.post("/entities", json={
        "type": "FEATURE",
        "canonical_name": "타입 보호 테스트",
    })
    entity_id = create_resp.json()["data"]["id"]

    patch_resp = await client.patch(f"/entities/{entity_id}", json={
        "canonical_name": "이름 변경",
        "type": "UI_AREA",
    })
    assert patch_resp.status_code == 200
    assert patch_resp.json()["data"]["type"] == "FEATURE"


async def test_patch_entity_not_found(client: AsyncClient):
    response = await client.patch(f"/entities/{uuid.uuid4()}", json={
        "canonical_name": "없는 엔티티",
    })
    assert response.status_code == 404
    body = response.json()
    assert body["ok"] is False
    assert body["error"]["code"] == "ENTITY_NOT_FOUND"


async def test_patch_entity_deprecation(client: AsyncClient):
    create_resp = await client.post("/entities", json={
        "type": "FEATURE",
        "canonical_name": "구버전 기능",
    })
    entity_id = create_resp.json()["data"]["id"]

    replacement_id = str(uuid.uuid4())
    await client.post("/entities", json={
        "id": replacement_id,
        "type": "FEATURE",
        "canonical_name": "신버전 기능",
    })

    patch_resp = await client.patch(f"/entities/{entity_id}", json={
        "status": "deprecated",
        "replacement_entity_id": replacement_id,
        "deprecation_reason": "신버전으로 대체",
    })
    assert patch_resp.status_code == 200
    data = patch_resp.json()["data"]
    assert data["status"] == "deprecated"
    assert data["replacement_entity_id"] == replacement_id
    assert data["deprecation_reason"] == "신버전으로 대체"
