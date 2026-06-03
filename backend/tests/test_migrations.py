"""Startup migration behaviour — `alembic upgrade head` (run by entrypoint.sh).

These tests guard the permanent fix for the "DB created but schema missing"
deploy incident: the container entrypoint runs `alembic upgrade head`, which must
(a) create the full schema on an empty database and (b) be a safe no-op when run
again, with no "already exists" conflicts.

Each test runs against a throwaway database so it never touches the shared test
schema managed by conftest.
"""

import os
import subprocess
import sys
import uuid
from pathlib import Path

import asyncpg
import pytest
from sqlalchemy.engine import make_url

# backend/ root — where alembic.ini lives, so `alembic` resolves script_location.
BACKEND_ROOT = Path(__file__).resolve().parent.parent

# Tables a fully-migrated schema must contain (sample across migrations 001..011).
EXPECTED_TABLES = {"project", "entity", "user_account", "api_key", "alembic_version"}


def _async_url(base, dbname: str) -> str:
    # render_as_string(hide_password=False) — str(URL) masks the password as '***'.
    return base.set(database=dbname).render_as_string(hide_password=False)


def _asyncpg_dsn(base, dbname: str) -> str:
    # asyncpg wants a plain postgresql:// DSN (no +asyncpg driver suffix).
    return base.set(drivername="postgresql", database=dbname).render_as_string(
        hide_password=False
    )


@pytest.fixture
async def temp_db():
    """Create a fresh empty database, yield its async URL, drop it afterwards."""
    base = make_url(os.environ["DATABASE_URL"])
    db_name = f"llmref_migtest_{uuid.uuid4().hex[:8]}"
    admin_dsn = _asyncpg_dsn(base, "postgres")

    try:
        conn = await asyncpg.connect(admin_dsn)
    except Exception as exc:  # pragma: no cover - environment without CREATEDB
        pytest.skip(f"cannot reach maintenance database to create temp DB: {exc!r}")

    try:
        await conn.execute(f'CREATE DATABASE "{db_name}"')
    finally:
        await conn.close()

    try:
        yield base, db_name
    finally:
        conn = await asyncpg.connect(admin_dsn)
        try:
            # FORCE drops even if a lingering connection remains (PG 13+).
            await conn.execute(f'DROP DATABASE IF EXISTS "{db_name}" WITH (FORCE)')
        finally:
            await conn.close()


def _run_alembic_upgrade(async_url: str) -> subprocess.CompletedProcess:
    env = {**os.environ, "DATABASE_URL": async_url}
    return subprocess.run(
        [sys.executable, "-m", "alembic", "upgrade", "head"],
        cwd=BACKEND_ROOT,
        env=env,
        capture_output=True,
        text=True,
    )


async def _table_names(base, db_name: str) -> set[str]:
    conn = await asyncpg.connect(_asyncpg_dsn(base, db_name))
    try:
        rows = await conn.fetch(
            "SELECT tablename FROM pg_tables WHERE schemaname = 'public'"
        )
    finally:
        await conn.close()
    return {r["tablename"] for r in rows}


async def _alembic_version(base, db_name: str) -> list[str]:
    conn = await asyncpg.connect(_asyncpg_dsn(base, db_name))
    try:
        rows = await conn.fetch("SELECT version_num FROM alembic_version")
    finally:
        await conn.close()
    return [r["version_num"] for r in rows]


async def test_upgrade_head_creates_schema_on_empty_db(temp_db):
    base, db_name = temp_db
    async_url = _async_url(base, db_name)

    result = _run_alembic_upgrade(async_url)
    assert result.returncode == 0, result.stderr

    tables = await _table_names(base, db_name)
    missing = EXPECTED_TABLES - tables
    assert not missing, f"missing tables after upgrade: {missing}"

    # Exactly one revision recorded, and it is the single head ('011').
    assert await _alembic_version(base, db_name) == ["011"]


async def test_upgrade_head_is_idempotent(temp_db):
    base, db_name = temp_db
    async_url = _async_url(base, db_name)

    first = _run_alembic_upgrade(async_url)
    assert first.returncode == 0, first.stderr
    tables_after_first = await _table_names(base, db_name)
    version_after_first = await _alembic_version(base, db_name)

    # Re-running against an already-current DB must succeed with no conflicts.
    second = _run_alembic_upgrade(async_url)
    assert second.returncode == 0, second.stderr
    assert "already exists" not in (second.stderr + second.stdout).lower()

    assert await _table_names(base, db_name) == tables_after_first
    assert await _alembic_version(base, db_name) == version_after_first
