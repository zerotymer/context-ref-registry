"""SQLite-specific regressions: tz-aware timestamps, serialized short_seq, FK cascade."""
import asyncio
import uuid

from httpx import AsyncClient
from sqlalchemy import delete, func, select

from app.db.session import async_session_factory
from app.domain.models import ApiKey, Entity, EntityHistory, EntityTag, Project
from tests.conftest import create_key


async def test_created_at_is_timezone_aware(admin_client: AsyncClient):
    resp = await admin_client.post("/api/v1/entities", json={"type": "FEATURE", "canonical_name": "tz"})
    entity_id = resp.json()["data"]["id"]
    created_at = (await admin_client.get(f"/api/v1/entities/{entity_id}")).json()["data"]["created_at"]
    assert created_at.endswith(("+00:00", "Z")), created_at


async def test_concurrent_short_seq_is_unique(admin_client: AsyncClient):
    await admin_client.post("/api/v1/projects", json={"id": "SEQ", "alias": "seq"})
    n = 10
    resps = await asyncio.gather(*[
        admin_client.post("/api/v1/entities", json={"type": "FEATURE", "canonical_name": f"e{i}", "project_id": "SEQ"})
        for i in range(n)
    ])
    assert all(r.status_code == 201 for r in resps), [r.text for r in resps]

    async with async_session_factory() as session:
        seqs = (await session.execute(
            select(Entity.short_seq).where(Entity.project_id == "SEQ", Entity.type == "FEATURE")
        )).scalars().all()
    assert sorted(seqs) == list(range(1, n + 1))


async def test_fk_cascade_is_enforced(admin_client: AsyncClient):
    """foreign_keys=ON: deleting a project drops its keys, deleting an entity drops tags/history."""
    await create_key("CASC", "read")
    resp = await admin_client.post(
        "/api/v1/entities", json={"type": "FEATURE", "canonical_name": "cascade", "project_id": "CASC"}
    )
    entity_id = resp.json()["data"]["id"]
    assert (await admin_client.post(f"/api/v1/entities/{entity_id}/tags", json={"tag": "t"})).status_code == 201

    async with async_session_factory() as session:
        await session.execute(delete(Entity).where(Entity.id == uuid.UUID(entity_id)))
        await session.commit()
    async with async_session_factory() as session:
        for model in (EntityTag, EntityHistory):
            count = await session.scalar(select(func.count()).select_from(model))
            assert count == 0, model

        await session.execute(delete(Project).where(Project.id == "CASC"))
        await session.commit()
    async with async_session_factory() as session:
        assert await session.scalar(select(func.count()).select_from(ApiKey)) == 0
