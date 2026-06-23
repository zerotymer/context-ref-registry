"""UI_AREA mockup HTML renderer.

Server-side string templating — no template engine, no external resources.
Input is the entity's `metadata["mockup"]` convention (see docs/02-domain-model).
ALL user text is HTML-escaped (XSS — trust boundary). Unknown component kinds
render as a safe gray placeholder box, never an error.
"""
from __future__ import annotations

from html import escape

from app.domain.models import Entity

# Component kinds we know how to render. Anything else → safe placeholder box.
_KNOWN_KINDS = {"header", "text", "table", "button", "field", "image"}
_LAYOUTS = {"stack", "grid", "columns"}

_CSS = """
*{box-sizing:border-box}body{font:14px/1.5 system-ui,sans-serif;margin:0;padding:24px;background:#f5f5f7;color:#1d1d1f}
.mockup{max-width:900px;margin:0 auto;background:#fff;border:1px solid #d2d2d7;border-radius:12px;padding:24px}
.mockup h1{font-size:20px;margin:0 0 16px}
.components{display:flex;flex-direction:column;gap:12px}
.components.grid{display:grid;grid-template-columns:repeat(2,1fr)}
.components.columns{flex-direction:row;flex-wrap:wrap}
.c-header{font-size:16px;font-weight:600;border-bottom:2px solid #1d1d1f;padding-bottom:4px}
.c-text{color:#515154}
.c-button{display:inline-block;background:#0071e3;color:#fff;border:none;border-radius:8px;padding:8px 16px;font:inherit;cursor:default}
.c-field{display:flex;flex-direction:column;gap:4px}
.c-field label{font-size:12px;color:#515154}
.c-field .box{border:1px solid #d2d2d7;border-radius:6px;padding:8px;background:#fafafa;color:#86868b}
table{border-collapse:collapse;width:100%}
th,td{border:1px solid #d2d2d7;padding:6px 10px;text-align:left}
th{background:#f5f5f7;font-weight:600}
.c-image,.c-unknown{background:#e8e8ed;border:1px dashed #aeaeb2;border-radius:8px;padding:24px;text-align:center;color:#86868b}
.placeholder{color:#86868b;font-style:italic}
""".strip()


def render_mockup(entity: Entity) -> str:
    """Render a UI_AREA entity's mockup metadata into a standalone HTML document."""
    mockup = _mockup_def(entity)
    title = entity.canonical_name
    if mockup and isinstance(mockup.get("title"), str):
        title = mockup["title"]

    if not mockup or not mockup.get("components"):
        body = _placeholder_body(entity)
    else:
        layout = mockup.get("layout") if mockup.get("layout") in _LAYOUTS else "stack"
        parts = [_render_component(c) for c in mockup["components"] if isinstance(c, dict)]
        body = f'<div class="components {escape(layout)}">{"".join(parts)}</div>'

    return (
        "<!doctype html><html lang=\"ko\"><head><meta charset=\"utf-8\">"
        f"<title>{escape(title)}</title><style>{_CSS}</style></head>"
        f'<body><div class="mockup"><h1>{escape(title)}</h1>{body}</div></body></html>'
    )


def _mockup_def(entity: Entity) -> dict | None:
    for m in entity.metadata_entries:
        if isinstance(m.data, dict) and isinstance(m.data.get("mockup"), dict):
            return m.data["mockup"]
    return None


def _placeholder_body(entity: Entity) -> str:
    desc = escape(entity.description) if entity.description else "목업 정의(metadata.mockup)가 없습니다."
    return f'<p class="placeholder">{desc}</p>'


def _render_component(c: dict) -> str:
    kind = c.get("kind")
    if kind not in _KNOWN_KINDS:
        return f'<div class="c-unknown">{escape(str(kind))}</div>'

    if kind == "header":
        return f'<div class="c-header">{escape(str(c.get("text", "")))}</div>'
    if kind == "text":
        return f'<p class="c-text">{escape(str(c.get("text", "")))}</p>'
    if kind == "button":
        return f'<button class="c-button">{escape(str(c.get("text", "")))}</button>'
    if kind == "field":
        label = escape(str(c.get("label", "")))
        input_type = escape(str(c.get("input", "text")))
        return f'<div class="c-field"><label>{label}</label><div class="box">{input_type}</div></div>'
    if kind == "image":
        return f'<div class="c-image">🖼 {escape(str(c.get("alt", "image")))}</div>'
    # table
    cols = c.get("columns") or []
    head = "".join(f"<th>{escape(str(col))}</th>" for col in cols if not isinstance(col, (dict, list)))
    empty = f'<tr><td colspan="{max(len(cols), 1)}" class="placeholder">데이터 없음</td></tr>'
    return f"<table><thead><tr>{head}</tr></thead><tbody>{empty}</tbody></table>"
