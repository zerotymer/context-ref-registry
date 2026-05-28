---
name: static-mockup-preview-server
description: Serves static HTML mockup files for local preview via Python's built-in HTTP server. Use when starting a local server to serve UI mockups, design previews, or prototype HTML files during development.
version: 1.0.0
language: en
wiki_uuid: e6274b24-2c08-4367-8859-b5a92bd98d59
wiki_url: https://md.zerotymer.net/en/skill/e6274b24-2c08-4367-8859-b5a92bd98d59
status: active
last_updated: 2026-05-28
source_project: context-ref-registry
---

# Static Mockup Preview Server

Serve static HTML mockup files locally for review and preview.

## When to Use

- User asks to "serve", "preview", or "open" a mockup or HTML file
- Checking UI design before implementation begins
- Sharing a prototype URL for review

## Default Command

Use Python's built-in HTTP server. Always serve from the **mockup directory**,
not the project root, so relative links between HTML files work correctly.

```bash
cd <mockup-dir> && python3 -m http.server <port>
```

## This Project's Mockup Paths

| Directory | Contents |
|-----------|----------|
| `output/tag-ui-mockup/` | Tag feature UI mockup (entity-detail, entities, new-entity modal) |
| `output/review-ui-mockup/` | Review UI mockup |

## Standard Port

Use **port 8080** for mockup servers to avoid conflict with the backend API
on port 8000.

```bash
cd output/tag-ui-mockup && python3 -m http.server 8080
```

Entry point: `http://localhost:8080/index.html`

## Run in Background

When the user needs to keep working after starting the server, run it in the
background and verify it's responding before reporting the URL.

```bash
# Start
cd <mockup-dir> && python3 -m http.server 8080 &

# Verify
curl -s -o /dev/null -w "%{http_code}" http://localhost:8080/index.html
# Expected: 200
```

## Stop the Server

```bash
lsof -ti:8080 | xargs kill
```

## Notes

- Always verify the server is responding (HTTP 200) before reporting the URL.
- Report the index URL and direct page URLs separately for convenience.
- Do not use `pkill -f` as it may match unintended processes on shared systems;
  prefer `lsof -ti:<port> | xargs kill`.
