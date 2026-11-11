"""Startup migration behaviour — `alembic upgrade head` (run by entrypoint.sh).

Guards the "DB created but schema missing" deploy incident: the entrypoint runs
`alembic upgrade head`, which must (a) create the full schema on an empty SQLite
file and (b) be a safe no-op when run again. Each test uses a throwaway DB file.
"""

import os
import sqlite3
import subprocess
import sys
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parent.parent

EXPECTED_TABLES = {"project", "entity", "api_key", "alembic_version"}


def _alembic(db_path: Path, *args: str) -> subprocess.CompletedProcess:
    env = {**os.environ, "DATABASE_URL": f"sqlite+aiosqlite:///{db_path}"}
    return subprocess.run(
        [sys.executable, "-m", "alembic", *args],
        cwd=BACKEND_ROOT, env=env, capture_output=True, text=True,
    )


def _tables(db_path: Path) -> set[str]:
    with sqlite3.connect(db_path) as conn:
        return {r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}


def test_upgrade_head_creates_schema_and_is_idempotent(tmp_path: Path):
    db = tmp_path / "registry.db"
    for _ in range(2):
        proc = _alembic(db, "upgrade", "head")
        assert proc.returncode == 0, proc.stderr
    tables = _tables(db)
    assert EXPECTED_TABLES <= tables
    assert not {"user_account", "project_member"} & tables


def test_baseline_matches_models(tmp_path: Path):
    db = tmp_path / "registry.db"
    assert _alembic(db, "upgrade", "head").returncode == 0
    proc = _alembic(db, "check")
    assert proc.returncode == 0, proc.stdout + proc.stderr
