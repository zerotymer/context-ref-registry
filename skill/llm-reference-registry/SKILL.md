---
name: llm-reference-registry
description: Active usage guide for the LLM Reference Registry — a UUID-based persistent reference store for UI areas, features, infra units, APIs, and code symbols. Teaches LLMs how to use MCP tools and REST API to look up, resolve, and cross-reference entities during coding tasks.
version: 1.1.0
language: en
status: active
last_updated: 2026-05-28
source_project: context-ref-registry
---

# LLM Reference Registry — Active Usage for Coding Agents

## What This Is

The **LLM Reference Registry** is a persistent store that maps human-readable
names (aliases) to stable UUIDs for entities such as UI screens, features,
infrastructure units, APIs, and code symbols. It also stores rich context
(summaries, business rules, security notes, implementation hints) and a
relation graph between entities.

This skill teaches you — a coding agent — how to **actively use** this
registry during your work. When you see a reference to a UI area, feature,
or API that might be in the registry, look it up instead of guessing.

## Connection Methods

The registry exposes two interfaces. Prefer MCP when available (the agent
platform natively supports it); fall back to REST API otherwise.

| Method | Protocol | When to Use |
|--------|----------|-------------|
| **MCP** | `mcp` tool calls | Agent platform has the MCP server configured |
| **REST API** | `http://localhost:8000` | Direct HTTP access; batch operations; writing data |

---

## Core Workflow: Resolve → Bundle → Act

This is the primary pattern for using the registry effectively:

```
1. RESOLVE  — Turn an alias (e.g. "User Search Filter") into a UUID
              → MCP: resolve_alias()  /  REST: GET /resolve?alias=...
              
2. BUNDLE   — Fetch rich context around that entity
              → MCP: get_context_bundle()  /  REST: POST /context-bundle
              
3. ACT      — Use the retrieved context in your task
              (code changes, analysis, documentation, etc.)
```

If the alias is ambiguous (multiple entities share it), **ask the user to
choose** — never pick arbitrarily.

---

## MCP Tool Reference (Preferred)

The MCP server provides 6 read-only tools. Call them as native `mcp` tools.

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
and deprecation warnings.

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
get_entity(id="uuid-...")
```

Returns the entity with aliases grouped by locale and deprecation warnings.
Use this when you only need one entity's details, not the full graph.

### 4. `search_entities` — Find entities by keyword

```
search_entities(query="search", types=["UI_AREA", "FEATURE"], limit=10)
```

Search order:
1. **Alias exact match** (highest score: 1.0)
2. **Canonical name partial match** (ILIRE, score: 0.7)

Use when you don't have a UUID or exact alias.

### 5. `get_related_entities` — Explore the relation graph

```
get_related_entities(id="uuid-...", direction="both", max_depth=2)
```

Good for understanding dependencies. Direction: `outgoing`, `incoming`, or
`both`.

### 6. `validate_references` — Bulk validation

```
validate_references(references=["uuid-...", "alias-text", ...])
```

Validates a list of references (UUIDs or aliases). Returns `resolved`,
`ambiguous`, and `missing` lists. Use before executing a plan that
depends on specific entities.

---

## REST API Reference (Fallback / Write)

Use REST when MCP is unavailable or you need to write data.

### Read Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/resolve?alias=...&locale=ko&type=UI_AREA` | Alias resolve |
| `GET` | `/entities/{id}` | Entity by UUID |
| `GET` | `/search?q=...&types=FEATURE,API&limit=10` | Search |
| `GET` | `/entities/{id}/relations?direction=both&max_depth=1` | Relations |
| `GET` | `/entities/{id}/aliases` | Aliases |
| `GET` | `/entities/{id}/contexts` | Contexts |
| `POST` | `/context-bundle` | Context bundle (same params as MCP tool) |

### Write Endpoints

| Method | Path | Purpose |
|--------|------|---------|
| `POST` | `/entities` | Create entity |
| `PATCH` | `/entities/{id}` | Update (status, name, etc.) |
| `POST` | `/entities/{id}/aliases` | Add alias |
| `POST` | `/entities/{id}/contexts` | Add context |
| `POST` | `/relations` | Create relation |
| `POST` | `/ingest/batch` | **Bulk ingest** (main write entry point) |

### All responses follow this envelope:

```json
{"ok": true, "data": {...}}
{"ok": false, "error": {"code": "...", "message": "..."}}
```

---

## Batch Ingest Workflow (For Parsers)

When you parse a document (screen spec, API doc, etc.) and want to store
the result, use `POST /ingest/batch`. The request format:

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

## Entity Types (5 Kinds)

| Type | What It Represents |
|------|-------------------|
| `UI_AREA` | A screen region (search filter, navigation, data table) |
| `FEATURE` | A user-facing feature (user search, order placement) |
| `INFRA_UNIT` | Infrastructure component (database, cache, message queue) |
| `API` | An API endpoint or service boundary |
| `CODE_SYMBOL` | A code-level symbol (class, function, component) |

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
2. POST /ingest/batch with the result
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
| **MCP is read-only** | All MCP tools are read-only. Use REST API for writes. |
| **Entity type cannot change** | `TYPE_CHANGE_FORBIDDEN` error. Delete and recreate if needed. |

---

## When to NOT Use the Registry

- The entity is purely ephemeral / temporary (no persistent reference needed).
- The reference is internal to a single file and won't be reused.
- The information is already confirmed by the user with exact wording.

When in doubt, **look it up** — the registry is fast and maintains consistency.
