"""GET /entities/{id}/mockup — UI_AREA mockup HTML rendering."""
from httpx import AsyncClient

from app.db.session import async_session_factory
from app.service.auth_service import AuthService
from app.service.project_service import ProjectService


async def _ingest_ui_area(client: AsyncClient, mockup: dict | None, project_id: str | None = None) -> str:
    metadata = {"ui_framework": "react"}
    if mockup is not None:
        metadata["mockup"] = mockup
    entity = {
        "type": "UI_AREA",
        "canonical_name": "주문 목록 화면",
        "status": "active",
        "metadata": metadata,
    }
    if project_id is not None:
        entity["project_id"] = project_id
    resp = await client.post("/ingest/batch", json={
        "source": {"type": "screen_spec", "name": "t.md", "uri": "file://t.md", "version": "1"},
        "entities": [entity],
        "relations": [],
    })
    assert resp.status_code == 200, resp.text
    # ingest returns nothing useful here; fetch the id via list
    listed = await client.get("/entities", params={"types": "UI_AREA", "limit": 100})
    items = [e for e in listed.json()["data"]["items"] if e["canonical_name"] == "주문 목록 화면"]
    return items[-1]["id"]


async def test_mockup_renders_html(admin_client: AsyncClient):
    eid = await _ingest_ui_area(admin_client, {
        "title": "주문 목록 화면",
        "layout": "stack",
        "components": [
            {"kind": "header", "text": "주문 목록"},
            {"kind": "table", "columns": ["주문번호", "상태", "금액"]},
            {"kind": "button", "text": "신규 주문"},
            {"kind": "field", "label": "검색", "input": "text"},
        ],
    })
    resp = await admin_client.get(f"/entities/{eid}/mockup")
    assert resp.status_code == 200
    assert resp.headers["content-type"].startswith("text/html")
    html = resp.text
    assert "<!doctype html>" in html
    assert "주문 목록 화면" in html  # title
    assert "<th>주문번호</th>" in html
    assert "신규 주문" in html


async def test_mockup_non_ui_area_returns_400(admin_client: AsyncClient):
    create = await admin_client.post("/entities", json={"type": "FEATURE", "canonical_name": "기능"})
    eid = create.json()["data"]["id"]
    resp = await admin_client.get(f"/entities/{eid}/mockup")
    assert resp.status_code == 400
    assert resp.json()["error"]["code"] == "NOT_A_UI_AREA"


async def test_mockup_out_of_scope_returns_404(client: AsyncClient, admin_client: AsyncClient):
    project_id = "MOCKUP_PROJ"
    async with async_session_factory() as session:
        admin = await AuthService(session).create_user(
            login_id="mockup_admin", password="pass123", display_name="M", role="admin",
        )
        await ProjectService(session).create_project(
            id=project_id, alias="MOCKUP", description=None, created_by=admin.id,
        )
    eid = await _ingest_ui_area(admin_client, {"components": [{"kind": "header", "text": "x"}]}, project_id=project_id)

    resp = await client.get(f"/entities/{eid}/mockup")
    assert resp.status_code == 404


async def test_mockup_escapes_user_text(admin_client: AsyncClient):
    eid = await _ingest_ui_area(admin_client, {
        "title": "<script>alert(1)</script>",
        "components": [{"kind": "text", "text": "<img src=x onerror=alert(1)>"}],
    })
    resp = await admin_client.get(f"/entities/{eid}/mockup")
    html = resp.text
    assert "<script>alert(1)</script>" not in html
    assert "&lt;script&gt;" in html
    assert "<img src=x" not in html


async def test_mockup_unknown_kind_renders_safe(admin_client: AsyncClient):
    eid = await _ingest_ui_area(admin_client, {
        "components": [{"kind": "wormhole", "text": "boom"}],
    })
    resp = await admin_client.get(f"/entities/{eid}/mockup")
    assert resp.status_code == 200
    assert "c-unknown" in resp.text


async def test_mockup_no_definition_renders_placeholder(admin_client: AsyncClient):
    eid = await _ingest_ui_area(admin_client, None)
    resp = await admin_client.get(f"/entities/{eid}/mockup")
    assert resp.status_code == 200
    assert "주문 목록 화면" in resp.text  # canonical_name fallback title
    assert "placeholder" in resp.text
