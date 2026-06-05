---
name: llm-reference-registry
description: Active usage guide for the LLM Reference Registry — a UUID-based persistent reference store for UI areas, features, infra units, APIs, code symbols, and issues. Teaches LLMs how to use MCP tools and the HTTP API (via the Next BFF gateway or the backend directly) to look up, resolve, and cross-reference entities during coding tasks.
version: 1.3.0
language: en
status: active
last_updated: 2026-06-06
source_project: context-ref-registry
---

# LLM Reference Registry — Active Usage for Coding Agents

## What This Is

The **LLM Reference Registry** is a persistent store that maps human-readable
names (aliases) to stable UUIDs for entities such as UI screens, features,
infrastructure units, APIs, code symbols, and issues. It also stores rich
context (summaries, business rules, security notes, implementation hints) and a
relation graph between entities.

This skill teaches you — a coding agent — how to **actively use** this
registry during your work. When you see a reference to a UI area, feature,
or API that might be in the registry, look it up instead of guessing.

## Connection Methods

The registry exposes two interfaces. Prefer **MCP** when the agent platform has
the MCP server configured; otherwise use the **HTTP API**.

| Method | Endpoint | When to Use |
|--------|----------|-------------|
| **MCP** | stdio (`python -m app.mcp`) | Agent platform has the MCP server configured. Read-only. |
| **HTTP API (gateway)** | `https://llm-reg.zerotymer.net/api/v1/*` | **Preferred HTTP path.** Next BFF Route Handler → backend proxy. |
| **HTTP API (direct)** | `https://llm-api.zerotymer.net/*` | Fallback: backend API directly (no `/api/v1` prefix). |

### Which HTTP endpoint to use

1. **Default to the gateway** — `https://llm-reg.zerotymer.net/api/v1/...`.
   It is the Next.js Route Handler that proxies to the backend with API Key
   passthrough. Paths keep their normal names but are **prefixed with `/api/v1`**.
2. **Fall back to the direct backend** — `https://llm-api.zerotymer.net/...`
   (no `/api/v1` prefix) only if the gateway is unreachable.
3. For **local development** the gateway is `http://localhost:3000/api/v1/*`
   and the backend is `http://localhost:8000/*`.

> The gateway **does not unwrap** the response envelope and preserves the
> backend status code, content-type, and body verbatim — so a gateway call and
> a direct backend call return the same shape. Cookies are never forwarded;
> authentication is delegated entirely to the API Key headers below.

### Gateway path allowlist

The gateway only proxies the agent-facing surface. Allowed top-level prefixes:

```
entities  relations  search  resolve  tags
context-bundle  ingest  export  validate-references  projects
```

`auth/*` and `admin/*` (human/cookie-session surfaces) are **always blocked**
at the gateway and return `404`. Use the direct backend for those if ever needed.

---

## Authentication (API Key)

All agent HTTP requests authenticate with an **API Key**. The backend accepts
the key in either of two headers — send one:

```
X-API-Key: <your-api-key>
```
or
```
Authorization: Bearer <your-api-key>
```

- The gateway forwards exactly these headers (`x-api-key`, `authorization`,
  `content-type`, `accept`) to the backend; everything else (cookies, etc.) is
  dropped.
- **Get a key**: a user issues one from the admin console (`/settings/api-keys`)
  or via `POST /auth/api-keys`. API Keys are scoped to a project; requests are
  limited to entities the key's project can access.
- On missing/invalid key the backend returns `401`. Never hard-code the key in
  source — read it from an environment variable (e.g. `REGISTRY_API_KEY`).

**Example (gateway, preferred):**

```bash
curl -H "X-API-Key: $REGISTRY_API_KEY" \
  "https://llm-reg.zerotymer.net/api/v1/resolve?alias=User%20Search&locale=en"
```

**Example (direct backend, fallback):**

```bash
curl -H "X-API-Key: $REGISTRY_API_KEY" \
  "https://llm-api.zerotymer.net/resolve?alias=User%20Search&locale=en"
```

MCP tool calls do not pass an API Key (the server runs with its own DB session);
authentication only applies to the HTTP interfaces.

---

## Core Workflow: Resolve → Bundle → Act

This is the primary pattern for using the registry effectively:

```
1. RESOLVE  — Turn an alias (e.g. "User Search Filter") into a UUID
              → MCP: resolve_alias()  /  HTTP: GET /api/v1/resolve?alias=...

2. BUNDLE   — Fetch rich context around that entity
              → MCP: get_context_bundle()  /  HTTP: POST /api/v1/context-bundle

3. ACT      — Use the retrieved context in your task
              (code changes, analysis, documentation, etc.)
```

If the alias is ambiguous (multiple entities share it), **ask the user to
choose** — never pick arbitrarily.

---

## Reference Patterns (3 forms)

`get_entity` and `get_context_bundle` (MCP and HTTP) accept three reference forms:

| Form | Example | Notes |
|------|---------|-------|
| **UUID** | `550e8400-e29b-41d4-a716-446655440000` | Direct, unambiguous. |
| **PROJECT_ID@UUID** | `my_project@550e8400-...` | Scopes the UUID to a project. |
| **PROJECT_ID@TAG** | `my_project@auth` | Resolves a tag within a project. Fails if multiple match. |

`PROJECT_ID` allows characters `[A-Za-z0-9_]` only.

---

## MCP Tool Reference (Preferred)

The MCP server provides 7 read-only tools. Call them as native `mcp` tools.

### 1. `resolve_alias` — First step for any reference

```
resolve_alias(alias="사용자 검색", locale="ko")
→ {"status": "resolved", "entity": {"id": "uuid-...", ...}}
```

- Always specify `locale` when you know the language.
- Use `type` filter to narrow results: `type="UI_AREA"`
- When `ambiguous`, list candidates and ask the user.

### 2. `get_context_bundle` — Primary tool for rich context

```
get_context_bundle(root_ids=["uuid-..."], max_depth=2, token_budget=8000)
```

Returns roots, related entities, contexts (priority-ordered), relations,
and deprecation warnings. `root_ids` accepts any of the 3 reference patterns.

**Key parameters:**
| Param | Default | Notes |
|-------|---------|-------|
| `max_depth` | `2` | BFS depth. 0 = roots only. Max 10. |
| `token_budget` | `8000` | Context body token limit. Higher = more detail. |
| `include_types` | all | Filter entity types returned. |
| `include_relations` | all | Filter relation types traversed. |
| `language` | `"ko"` | Filter context by language. |

**Context priority** (when token_budget is exceeded):
1. `summary` → 2. `business_rule` → 3. `validation_rule` → 4. `implementation_hint`
5. `security_note` → 6. `infra_note` → 7. `details` → 8. `compatibility_note`
9. `exception_case`

### 3. `get_entity` — Single entity lookup

```
get_entity(id="uuid-...")     # or PROJECT_ID@UUID, PROJECT_ID@TAG
```

Returns the entity with aliases grouped by locale, tags, and deprecation
warnings. Use this when you only need one entity's details, not the full graph.

### 4. `search_entities` — Find entities by keyword

```
search_entities(query="search", types=["UI_AREA", "FEATURE"], tags=["auth"], limit=10)
```

Search order:
1. **Alias exact match** (highest score: 1.0)
2. **Canonical name partial match** (ILIKE, score: 0.7)

`tags` filter uses AND logic. Use when you don't have a UUID or exact alias.

### 5. `get_related_entities` — Explore the relation graph

```
get_related_entities(id="uuid-...", direction="both", max_depth=2)
```

Good for understanding dependencies. MCP direction values are `outgoing`,
`incoming`, or `both`. (HTTP API direction values are `out`, `in`, or `both`.)

### 6. `get_entity_history` — Change history

```
get_entity_history(id="uuid-...", limit=20)
```

Returns the revision list (descending) with `change_type`, `changed_fields`,
`change_reason`, and `changed_by`. Use to understand how an entity evolved.

### 7. `validate_references` — Bulk validation

```
validate_references(references=["uuid-...", "alias-text", ...])
```

Validates a list of references (UUIDs or aliases). Returns `valid`, `resolved`,
`ambiguous`, and `missing`. Use before executing a plan that depends on
specific entities.

---

## HTTP API Reference (Gateway / Direct)

Use the HTTP API when MCP is unavailable or you need to write data. Paths below
are **backend paths**. Through the gateway, prefix every path with `/api/v1`
(e.g. `GET /api/v1/resolve?...`). Direct-backend calls use the path as-is.
All requests require an API Key header (see Authentication).

### Read Endpoints

| Method | Path (backend) | Description |
|--------|------|-------------|
| `GET` | `/resolve?alias=...&locale=ko&type=UI_AREA` | Alias resolve |
| `GET` | `/entities` | List entities (filter/paging) |
| `GET` | `/entities/{ref}` | Entity by UUID / PROJECT_ID@UUID / PROJECT_ID@TAG |
| `GET` | `/search?q=...&types=FEATURE,API&limit=10` | Search |
| `GET` | `/entities/{ref}/relations?direction=both&max_depth=1` | Relations (`direction`: `out`, `in`, `both`) |
| `GET` | `/entities/{ref}/aliases` | Aliases |
| `GET` | `/entities/{ref}/contexts` | Contexts |
| `GET` | `/entities/{ref}/history` | Change history |
| `GET` | `/entities/{ref}/tags` | Tags |
| `POST` | `/context-bundle` | Context bundle (same params as MCP tool) |
| `GET` | `/export/agents-md` | AGENTS.md context export |
| `GET` | `/export/openapi` | OpenAPI 3.1.0 spec (JSON/YAML) |

### Write Endpoints

| Method | Path (backend) | Purpose |
|--------|------|---------|
| `POST` | `/entities` | Create entity |
| `POST` | `/entities/batch` | **Bulk create entities** (returns `207` + per-item result) |
| `PATCH` | `/entities/{ref}` | Update (status, name, etc. — id/type cannot change) |
| `POST` | `/entities/{ref}/aliases` | Add alias |
| `POST` | `/entities/{ref}/contexts` | Add context |
| `POST` | `/entities/{ref}/tags` | Attach tag |
| `POST` | `/relations` | Create relation |
| `POST` | `/ingest/batch` | **Bulk ingest** (main write entry point: source + entities + relations) |
| `POST` | `/validate-references` | Bulk reference validation |

### All responses follow this envelope:

```json
{"ok": true, "data": {...}}
{"ok": false, "error": {"code": "...", "message": "..."}}
```

(The gateway passes this through verbatim — it does **not** unwrap `data`.)

---

## Batch Ingest Workflow (For Parsers)

When you parse a document (screen spec, API doc, etc.) and want to store
the result, use `POST /ingest/batch` (gateway: `POST /api/v1/ingest/batch`).
The request format:

### Decompose Registration Units

Do not register a whole document as only one entity. Register a document/root
entity and the detailed units inside it. When the user asks to upload, get
entity IDs, or map IDs, automatically split into these units.

| Unit | Type | Example |
|------|------|---------|
| Document/instruction root | `FEATURE` or closest type | "Auth system design instruction" |
| Detailed feature | `FEATURE` | Login, project membership, mutation policy |
| Screen/screen element | `UI_AREA` | Login screen, user management screen, project filter |
| API/service boundary | `API` | Auth Session API, Project Access API Policy |
| Infrastructure/ops unit | `INFRA_UNIT` | Initial admin bootstrap, audit log integration |
| Schema/code symbol | `CODE_SYMBOL` | `user_account table`, Authorization Policy Service |
| Bug/task/issue | `ISSUE` | "Login loop on multi-worker", "Add pagination" |

Connect the root entity to detailed entities with `CONTAINS`.
Connect detailed entities with `DEPENDS_ON`, `USES`, `IMPLEMENTED_BY`,
`CALLS`, `READS_FROM`, or `WRITES_TO` when useful.

### ID Mapping Rules

`POST /ingest/batch` may not immediately return the list of generated entity
IDs. For uploads that require mapping, **pre-generate UUIDs and include each
entity's `id` field in the batch payload.**

Procedure:

1. Extract the document root and detailed feature/API/UI/infra/code-symbol candidates.
2. Pre-generate one UUID per entity.
3. Put the UUID in every entity's `id` field.
4. Build relations using those UUIDs inside the same batch.
5. Verify with `GET /entities/{id}` or `GET /entities/{id}/relations?direction=out`.
6. Add a `Registry Entity Mapping` table back to the source instruction/document.

This preserves exact mappings immediately after upload even when the server
does not return generated IDs.

```json
{
  "source": {
    "type": "screen_spec",
    "name": "source-filename.md",
    "uri": "file://docs/...",
    "version": "2026-05-27"
  },
  "entities": [
    {
      "id": "uuid-preassigned-by-agent",
      "type": "UI_AREA",
      "canonical_name": "사용자 검색 조건 영역",
      "description": "...",
      "status": "candidate",
      "aliases": {"ko": ["검색 조건"], "en": ["Search Filter"]},
      "contexts": [
        {"context_type": "summary", "body": "...", "language": "ko"}
      ]
    }
  ],
  "relations": [
    {
      "from_entity_id": "uuid-a",
      "to_entity_id": "uuid-b",
      "relation_type": "RELATED_TO"
    }
  ]
}
```

**Rules:**
- `id` is optional; if omitted the server generates one.
- When ID mapping is required, do not omit it. Pre-generate UUIDs.
- If `id` is provided and already exists, the entity is **updated** (but type cannot change).
- `from_entity_id` / `to_entity_id` in relations must exist in the batch or DB.
- Default status is `candidate` — promote to `active` after human review.

---

## Entity Lifecycle (What You Should Know)

```
candidate ──▶ active ──▶ deprecated ──▶ archived
```

| Status | Meaning |
|--------|---------|
| `candidate` | Parsed by agent, not yet reviewed |
| `active` | Confirmed by human |
| `deprecated` | Replaced. Check `replacement_entity_id`. **Do not delete.** |
| `archived` | No longer relevant |

When you encounter a **deprecated** entity:
1. Check `replacement_entity_id`.
2. Use the replacement for your task.
3. Include the deprecation in your response to the user.

---

## Entity Types (6 Kinds)

| Type | What It Represents |
|------|-------------------|
| `UI_AREA` | A screen region (search filter, navigation, data table) |
| `FEATURE` | A user-facing feature (user search, order placement) |
| `INFRA_UNIT` | Infrastructure component (database, cache, message queue) |
| `API` | An API endpoint or service boundary |
| `CODE_SYMBOL` | A code-level symbol (class, function, component) |
| `ISSUE` | A bug, task, or tracked work item |

---

## Context Types (9 Kinds)

| Type | When to Use |
|------|-------------|
| `summary` | Brief description of what this entity is |
| `details` | Detailed explanation |
| `business_rule` | Business logic constraints and rules |
| `validation_rule` | Input/output validation rules |
| `implementation_hint` | Code-level hints (component name, framework) |
| `security_note` | Security considerations |
| `infra_note` | Infrastructure / deployment notes |
| `compatibility_note` | Compatibility with other systems |
| `exception_case` | Edge cases and error scenarios |

---

## Relation Types (8 Kinds)

| Type | Direction | Meaning |
|------|-----------|---------|
| `CONTAINS` | → | Parent contains child (UI_AREA contains sub-area) |
| `RELATED_TO` | ↔ | General association |
| `USES` | → | Depends on for operation |
| `IMPLEMENTED_BY` | → | Feature implemented by code symbol |
| `READS_FROM` | → | Reads data from (API reads from DB) |
| `WRITES_TO` | → | Writes data to |
| `DEPENDS_ON` | → | Strong dependency (service A depends on service B) |
| `CALLS` | → | Invokes (UI calls API) |

---

## Common Patterns

### Pattern A: User mentions a UI area by name

```
1. resolve_alias("주문 목록", locale="ko")
   → resolved → get UUID
2. get_context_bundle(root_ids=[uuid], max_depth=2, token_budget=6000)
   → Get full context + related entities + relations
3. Present findings to user with deprecation warnings
```

### Pattern B: You need to find all entities related to a feature

```
1. search_entities("user management", types=["FEATURE"])
   → Get candidate UUIDs
2. get_context_bundle(root_ids=[uuid], max_depth=3, token_budget=10000,
     include_relations=["USES", "DEPENDS_ON", "CALLS"],
     include_types=["UI_AREA", "API", "INFRA_UNIT"])
   → Explore the dependency graph
```

### Pattern C: Before modifying code, validate all references

```
1. validate_references(references=["user-search", "uuid-...", "OrderList"])
   → Check which are valid
2. For any ambiguous results, ask user to clarify.
3. For deprecated entities, use replacement_entity_id.
```

### Pattern D: Storage after parsing a document

```
1. Parse document → build entity list with contexts/relations
2. POST /ingest/batch (gateway: /api/v1/ingest/batch) with the result
3. Check response for warnings and counts
```

### Pattern E: Register new entities and map back to source document

Use this pattern when you write a new instruction file, screen spec, or
design document that contains multiple identifiable units (screens, features,
code symbols). The goal is to assign stable UUIDs **before** implementation
starts and embed them directly into the source document.

**Step 1 — Identify units to register**

Scan the document and classify each identifiable unit by type:

| What you find | Entity type |
|---------------|-------------|
| Screen area / UI section | `UI_AREA` |
| User-facing functionality | `FEATURE` |
| API endpoint | `API` |
| Class / function / component | `CODE_SYMBOL` |
| Infrastructure component | `INFRA_UNIT` |
| Bug / task / work item | `ISSUE` |

**Step 2 — Generate UUIDs**

Generate one UUID per unit before uploading:

```bash
python3 -c "import uuid; print(uuid.uuid4())"
```

**Step 3 — Upload via batch ingest**

Upload all units in a single `POST /ingest/batch` call.
Include the generated `id` explicitly so the UUID is pinned.
Add `aliases` (ko + en), `contexts` (at minimum `summary` + `implementation_hint`),
and `relations` (CONTAINS / USES / DEPENDS_ON between the units).

```json
{
  "source": {
    "type": "screen_spec",
    "name": "my_instruction.md",
    "uri": "file://instructions/my_instruction.md",
    "version": "2026-05-28"
  },
  "entities": [
    {
      "id": "<generated-uuid>",
      "type": "FEATURE",
      "canonical_name": "My Feature",
      "status": "candidate",
      "aliases": {"ko": ["내 기능"], "en": ["My Feature"]},
      "contexts": [
        {"context_type": "summary", "body": "...", "language": "ko"},
        {"context_type": "implementation_hint", "body": "File: src/...", "language": "ko"}
      ]
    }
  ],
  "relations": [
    {
      "from_entity_id": "<parent-uuid>",
      "to_entity_id": "<child-uuid>",
      "relation_type": "CONTAINS"
    }
  ]
}
```

**Step 4 — Write UUIDs back into the source document**

After successful upload, embed the UUIDs into the document so future
agents can resolve them without guessing.

*Instruction file frontmatter (`entities:` block):*

```yaml
---
uuid: <instruction-uuid>        # the instruction itself
entities:
  feature:
    my_feature: <uuid>          # FEATURE entity
  ui_area:
    main_screen: <uuid>         # UI_AREA entity
    filter_bar:  <uuid>         # UI_AREA entity
  code_symbol:
    my_service: <uuid>          # CODE_SYMBOL entity
---
```

*Per-step inline annotation (inside the document body):*

```markdown
## Step 3. Main Screen Implementation

> **entity**: `<uuid>` (UI_AREA — Main Screen)

File: src/app/...
```

*Screen spec or design document:*

```markdown
## 로그인 화면  <!-- entity: <uuid> (UI_AREA) -->
```

**Why this matters**

- Any agent reading the document later can directly reference the entity
  by UUID — no alias resolution ambiguity.
- Relations uploaded in Step 3 let `get_context_bundle` traverse the
  full feature graph automatically.
- Promotes to `active` after human review; all downstream references
  remain stable because the UUID never changes.

---

## Invariants (Never Violate These)

| Rule | Why |
|------|-----|
| **UUID is immutable** | Never change an entity's UUID. Use PATCH for name/status. |
| **Aliases can be ambiguous** | When `resolve_alias` returns `ambiguous`, ask the user. Never pick arbitrarily. |
| **Deprecated entities must not be deleted** | Set `status: deprecated` and record `replacement_entity_id`. |
| **MCP is read-only** | All MCP tools are read-only. Use the HTTP API for writes. |
| **Entity type cannot change** | `TYPE_CHANGE_FORBIDDEN` error. Delete and recreate if needed. |
| **API Key required for HTTP** | Send `X-API-Key` or `Authorization: Bearer`. Never hard-code it. |

---

## When to NOT Use the Registry

- The entity is purely ephemeral / temporary (no persistent reference needed).
- The reference is internal to a single file and won't be reused.
- The information is already confirmed by the user with exact wording.

When in doubt, **look it up** — the registry is fast and maintains consistency.
