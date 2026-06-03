"""Startup bootstrap of the fixed admin/admin account (no longer env-configurable)."""

import pytest
from httpx import ASGITransport, AsyncClient

from app.config import BOOTSTRAP_ADMIN_LOGIN_ID, BOOTSTRAP_ADMIN_PASSWORD
from app.db.session import async_session_factory
from app.main import app
from app.service.auth_service import AuthService


async def _bootstrap() -> None:
    async with async_session_factory() as session:
        await AuthService(session).bootstrap_admin()


async def test_bootstrap_creates_fixed_admin_and_allows_login():
    await _bootstrap()

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        resp = await ac.post(
            "/auth/login",
            json={"login_id": BOOTSTRAP_ADMIN_LOGIN_ID, "password": BOOTSTRAP_ADMIN_PASSWORD},
        )
    assert resp.status_code == 200, resp.text


async def test_bootstrap_is_idempotent():
    # Two consecutive runs must not raise or create a duplicate admin.
    await _bootstrap()
    await _bootstrap()

    async with async_session_factory() as session:
        repo = AuthService(session)._user_repo
        admin = await repo.get_by_login_id(BOOTSTRAP_ADMIN_LOGIN_ID)
    assert admin is not None
    assert admin.role == "admin"
    assert admin.must_change_password is True


async def test_bootstrap_skips_when_admin_exists():
    # An existing admin (different login id) must prevent admin/admin creation.
    async with async_session_factory() as session:
        await AuthService(session).create_user(
            login_id="rootadmin",
            password="rootadmin123",
            display_name="Root",
            role="admin",
        )

    await _bootstrap()

    async with async_session_factory() as session:
        repo = AuthService(session)._user_repo
        assert await repo.get_by_login_id(BOOTSTRAP_ADMIN_LOGIN_ID) is None
