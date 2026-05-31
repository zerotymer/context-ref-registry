---
name: wiki-skill-import
description: Use when importing a project-local skill from the Wiki.js site via wikijs-agent-gateway; fetches English and Korean pages by UUID and writes SKILL.md and SKILL_ko.md.
---

# Wiki Skill Import (via wikijs-gateway)

Import project-local skills from the Wiki.js site by UUID, using
`wikijs-agent-gateway` as the data source instead of accessing Wiki.js directly.

This skill supports two modes:

- **Dynamic reference mode**: fetch the Wiki.js page at request time and use
  it as context without writing files.
- **Import mode**: fetch the Wiki.js page and write project-local skill files.

The imported skill must follow this layout:

```text
skills/<skill-name>/
├── SKILL.md
└── SKILL_ko.md
```

`SKILL.md` is the English source instruction file. `SKILL_ko.md` is the Korean
reading copy and must stay semantically equivalent.

## Prerequisites

The gateway must be reachable. The default public endpoint is:

```
GATEWAY_URL=https://md-gw.zerotymer.net
```

Read endpoints (`/health`, `/pages/by-uuid`, `/pages/by-path`, `/pages/search`,
`/pages/by-paths`) are **public — no token required**.

Write endpoints (`/pages/patch-section`, `/pages/upsert`, `/pages/dry-run`)
require `Authorization: Bearer $GATEWAY_ADMIN_TOKEN`. Only needed for
modify/upsert workflows.

## Fetch Strategy

Use `GET /pages/by-uuid` from the gateway. The gateway returns structured JSON
containing the original Markdown `content`, `title`, `description`, `locale`,
`path`, and `contentHash` for each locale. No HTML scraping or GraphQL schema
discovery is needed.

```
GET $GATEWAY_URL/pages/by-uuid?uuid=<uuid>[&type=<type>]
```

No `Authorization` header needed for read requests.

The `type` parameter is optional. Pass it when the caller provides a path
prefix (e.g. `skill`, `guide`, `agent`). When omitted the gateway resolves the
path as `<uuid>` alone. The local save location is always `skills/<name>/`
regardless of type.

If the gateway returns 404 for both locales, report the failure and do not
create partial skill files unless the user asks for a best-effort import.

## Dynamic vs Static

Dynamic import is allowed.

When the user provides a UUID and asks to reference, import, or refresh a skill,
fetch the latest English and Korean content at request time. Do not rely on a
previously downloaded copy unless the user explicitly asks for offline or static
behavior.

If the user issues a command such as `LLM-wiki <uuid> 참고해줘`, use dynamic
reference mode by default:

1. Fetch the relevant content via the gateway at request time.
2. Load the fetched content into the working context for this request.
3. Apply the instruction or reference content to the user's current task.
4. Do not write or modify `skills/` files unless the user also asks to import,
   install, update, apply permanently, or save the skill.

Static storage is still the final project state: after dynamic fetch, write the
resolved content into `skills/<skill-name>/SKILL.md` and
`skills/<skill-name>/SKILL_ko.md` so the project remains usable without network
access.

## Import Workflow

1. Validate that the user provided a UUID. Ask if missing.
2. Accept an optional `type` argument from the user (e.g. `skill`, `guide`,
   `agent`). Leave it empty when not provided — do not default to any value.
3. Call the gateway:
   ```bash
   curl -s "$GATEWAY_URL/pages/by-uuid?uuid=<uuid>&type=<type>" | jq .
   # Omit &type=<type> when type is not provided
   ```
4. Parse the response:
   - `pages.en` — English page (may be `null`)
   - `pages.ko` — Korean page (may be `null`)
   - Each page object contains: `content` (Markdown source), `title`,
     `description`, `locale`, `path`, `tags`, `contentHash`
5. If both `pages.en` and `pages.ko` are `null`, stop and report `PAGE_NOT_FOUND`.
6. Extract the skill `name` from the English frontmatter `name:` field in
   `content`. Fall back to the `title` field slugified if frontmatter is absent.
7. Use `name` as `<skill-name>`.
8. Write English content to `skills/<skill-name>/SKILL.md`.
   - If `pages.en` is `null`, copy the Korean content and note the absence.
9. Write Korean content to `skills/<skill-name>/SKILL_ko.md`.
   - If `pages.ko` is `null`, copy the English content and note the absence.
10. If Korean frontmatter is present, keep it semantically aligned with the
    English file. If absent, copy the English frontmatter and keep the Korean body.
11. Update `AGENTS.md` and `AGENTS_ko.md` only when the imported skill must be
    applied automatically or referenced by this project.

## Dynamic Reference Workflow

Use this workflow when the user asks to reference a Wiki.js skill for the
current task, including prompts such as `LLM-wiki <uuid> 참고해줘`.

1. Validate that the user provided a UUID.
2. Call `GET /pages/by-uuid` with the UUID (and type if provided) — no
   auth header needed for reads.
3. Use the fetched `content` fields as task-local context.
4. Follow the fetched instructions when they are relevant and do not conflict
   with higher-priority system, developer, or project instructions.
5. Report briefly which UUID was referenced and which locales were found.
6. Do not create or update project files unless the user explicitly requests a
   persistent import or project-level application.

## Response Structure Reference

```json
{
  "uuid": "550e8400-e29b-41d4-a716-446655440000",
  "type": "skill",
  "pages": {
    "en": {
      "id": 10,
      "path": "skill/550e8400-...",
      "locale": "en",
      "title": "My Skill",
      "description": "What this skill does",
      "content": "---\nname: my-skill\ndescription: ...\n---\n# My Skill\n...",
      "tags": ["skill"],
      "contentHash": "sha256..."
    },
    "ko": {
      "id": 11,
      "path": "skill/550e8400-...",
      "locale": "ko",
      "title": "내 스킬",
      "content": "---\nname: my-skill\n...\n---\n# 내 스킬\n...",
      "contentHash": "sha256..."
    }
  }
}
```

A locale value of `null` means the page does not exist in that locale.

## Error Handling

| Situation | Action |
|-----------|--------|
| Gateway unreachable | Run `curl $GATEWAY_URL/health` to diagnose; do not proceed |
| 401 / 403 on write | Check `GATEWAY_ADMIN_TOKEN` is set correctly |
| 404 both locales | Report `PAGE_NOT_FOUND` for uuid; stop unless user requests best-effort |
| 404 one locale | Write available locale; note the missing one in the file header |
| `content` is empty | Warn the user; do not write an empty skill file |
| No frontmatter `name` | Slugify `title` and use as skill name; warn the user |
