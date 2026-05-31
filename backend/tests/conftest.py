import os

# Must be set before app modules are imported so pydantic-settings picks up the test URL
os.environ["DATABASE_URL"] = os.environ.get(
    "TEST_DATABASE_URL",
    "postgresql+asyncpg://llmref:llmref@localhost:5432/llmref_test",
)

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import create_async_engine

from app.domain.models import Base
from app.main import app
from app.service.auth_service import AuthService
from app.db.session import async_session_factory

_test_engine = create_async_engine(os.environ["DATABASE_URL"], echo=False)


@pytest.fixture(scope="session", autouse=True)
async def _create_schema():
    async with _test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with _test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture(autouse=True)
async def _clean_tables():
    async with _test_engine.begin() as conn:
        for table in reversed(Base.metadata.sorted_tables):
            await conn.execute(table.delete())


@pytest.fixture
async def client() -> AsyncClient:
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c


@pytest.fixture
async def admin_client() -> AsyncClient:
    """Separate authenticated admin client — independent from `client` fixture."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        async with async_session_factory() as session:
            await AuthService(session).create_user(
                login_id="admin",
                password="admin123",
                display_name="Test Admin",
                role="admin",
            )
        resp = await ac.post("/auth/login", json={"login_id": "admin", "password": "admin123"})
        assert resp.status_code == 200, resp.text
        yield ac


@pytest.fixture
async def project_admin_client() -> AsyncClient:
    """Authenticated project_admin client."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        async with async_session_factory() as session:
            await AuthService(session).create_user(
                login_id="padmin",
                password="padmin123",
                display_name="Project Admin",
                role="project_admin",
            )
        resp = await ac.post("/auth/login", json={"login_id": "padmin", "password": "padmin123"})
        assert resp.status_code == 200, resp.text
        yield ac


# ---------------------------------------------------------------------------
# Shared example fixtures based on docs/10-examples.md
# ---------------------------------------------------------------------------

# Fixed UUIDs from docs/10
_AREA_ID = "0d18b76a-6c0e-45b4-9289-6bdfc2e87e5a"
_FEATURE_ID = "1c9323e9-46a4-4665-b2d1-c37e4f3b19e0"
_INFRA_ID = "ed832d61-3319-4d61-83d4-6a29f68932a5"


@pytest.fixture
async def entity_user_search_area(admin_client: AsyncClient) -> dict:  # noqa: F811
    """UI_AREA: 사용자 검색 조건 영역 (docs/10 example 1)."""
    resp = await admin_client.post("/ingest/batch", json={
        "source": {"type": "screen_spec", "name": "examples.md", "uri": "file://docs/10-examples.md", "version": "2026-05-25"},
        "entities": [{
            "id": _AREA_ID,
            "type": "UI_AREA",
            "canonical_name": "사용자 검색 조건 영역",
            "status": "active",
            "confidence": 1.0,
            "aliases": {"ko": ["사용자 검색 영역", "검색 조건", "회원 검색 조건"], "en": ["User Search Filter", "Search Criteria"]},
            "contexts": [{"context_type": "summary", "body": "사용자명, 이메일, 상태값으로 검색 조건을 입력하는 영역", "language": "ko"}],
            "metadata": {"ui_framework": "react", "route_hint": "/users", "component_hint": "UserSearchFilter"},
        }],
        "relations": [],
    })
    assert resp.status_code == 200
    return {"id": _AREA_ID}


@pytest.fixture
async def entity_user_search_feature(admin_client: AsyncClient) -> dict:
    """FEATURE: 사용자 검색 (docs/10 example 1)."""
    resp = await admin_client.post("/ingest/batch", json={
        "source": {"type": "screen_spec", "name": "examples.md", "uri": "file://docs/10-examples.md", "version": "2026-05-25"},
        "entities": [{
            "id": _FEATURE_ID,
            "type": "FEATURE",
            "canonical_name": "사용자 검색",
            "status": "active",
            "confidence": 1.0,
            "aliases": {"ko": ["사용자 검색", "회원 검색", "사용자 조회"], "en": ["User Search", "Search Users"]},
            "contexts": [
                {"context_type": "summary", "body": "사용자명, 이메일, 상태값 조건으로 사용자 목록을 조회한다.", "language": "ko"},
                {"context_type": "business_rule", "body": "검색 조건이 비어 있으면 전체 목록을 조회한다.", "language": "ko"},
            ],
            "metadata": {"granularity": "coarse", "certainty": "medium"},
        }],
        "relations": [],
    })
    assert resp.status_code == 200
    return {"id": _FEATURE_ID}


@pytest.fixture
async def entity_user_db(admin_client: AsyncClient) -> dict:
    """INFRA_UNIT: 사용자 서비스 PostgreSQL (docs/10 example 1)."""
    resp = await admin_client.post("/ingest/batch", json={
        "source": {"type": "screen_spec", "name": "examples.md", "uri": "file://docs/10-examples.md", "version": "2026-05-25"},
        "entities": [{
            "id": _INFRA_ID,
            "type": "INFRA_UNIT",
            "canonical_name": "사용자 서비스 PostgreSQL",
            "status": "active",
            "confidence": 1.0,
            "aliases": {"ko": ["사용자 DB", "회원 DB"], "en": ["User DB", "User PostgreSQL"]},
            "contexts": [{"context_type": "infra_note", "body": "로컬 개발 환경에서는 docker-compose의 user-postgres 서비스로 실행된다.", "language": "ko"}],
            "metadata": {"infra_type": "database", "runtime": "postgresql", "environments": ["local", "dev", "prod"]},
        }],
        "relations": [],
    })
    assert resp.status_code == 200
    return {"id": _INFRA_ID}


@pytest.fixture
async def relation_area_to_feature(
    admin_client: AsyncClient,
    entity_user_search_area: dict,
    entity_user_search_feature: dict,
) -> dict:
    """RELATED_TO: 사용자 검색 조건 영역 → 사용자 검색 (docs/10 example 2)."""
    resp = await admin_client.post("/relations", json={
        "from_entity_id": entity_user_search_area["id"],
        "to_entity_id": entity_user_search_feature["id"],
        "relation_type": "RELATED_TO",
        "description": "사용자 검색 조건 영역은 사용자 검색 기능과 관련된다.",
    })
    assert resp.status_code == 201
    return resp.json()["data"]


@pytest.fixture
async def relation_feature_to_db(
    admin_client: AsyncClient,
    entity_user_search_feature: dict,
    entity_user_db: dict,
) -> dict:
    """READS_FROM: 사용자 검색 → 사용자 서비스 PostgreSQL (docs/10 example 2)."""
    resp = await admin_client.post("/relations", json={
        "from_entity_id": entity_user_search_feature["id"],
        "to_entity_id": entity_user_db["id"],
        "relation_type": "READS_FROM",
        "description": "사용자 검색 기능은 사용자 DB에서 데이터를 조회한다.",
    })
    assert resp.status_code == 201
    return resp.json()["data"]
