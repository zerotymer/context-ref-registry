---
name: wiki-skill-import
description: Use when importing a project-local skill from the md.zerotymer.net Wiki.js site by UUID; fetches English and Korean pages and writes SKILL.md and SKILL_ko.md.
---

# Wiki Skill Import

Import project-local skills from the Wiki.js site at `https://md.zerotymer.net`
when the user provides a skill UUID.

This skill supports two modes:

- Dynamic reference mode: fetch the Wiki.js page for the current request and
  use it as context without writing files.
- Import mode: fetch the Wiki.js page and write project-local skill files.

The imported skill must follow this layout:

```text
skills/<skill-name>/
├── SKILL.md
└── SKILL_ko.md
```

`SKILL.md` is the English source instruction file. `SKILL_ko.md` is the Korean
reading copy and must stay semantically equivalent.

## Fetch Strategy

Prefer GraphQL when available.

GraphQL is the best source for automation because it can return the original
Markdown source, frontmatter, title, description, locale, and page metadata in
a structured response. It avoids scraping rendered HTML and preserves code
blocks, tables, frontmatter, and Markdown syntax more reliably.

Use public page HTML as a fallback when GraphQL is not publicly available or
requires credentials that are not configured. HTML fallback is acceptable for
read-only recovery, but it is lossy: Wiki.js renders frontmatter-like content
as HTML headings, code blocks are wrapped in site markup, and Markdown must be
reconstructed.

If both methods fail, report the failure clearly and do not create partial skill
files unless the user asks for a best-effort import.

## Dynamic Vs Static

Dynamic import is allowed.

When the user provides a UUID and asks to reference, import, or refresh a skill,
fetch the latest English and Korean content at request time. Do not rely on a
previously downloaded copy unless the user explicitly asks for offline or static
behavior.

If the user says a command like `LLM-wiki <uuid> 참고해줘`, use dynamic
reference mode by default:

1. Fetch the relevant Wiki.js content at request time.
2. Load the fetched content into the working context for this request.
3. Apply the instruction or reference content to the user's current task.
4. Do not write or modify `skills/` files unless the user also asks to import,
   install, update, apply permanently, or save the skill.

Static storage is still the final project state: after dynamic fetch, write the
resolved content into `skills/<skill-name>/SKILL.md` and
`skills/<skill-name>/SKILL_ko.md` so the project remains usable without network
access.

## URL Pattern

For a UUID such as `<uuid>`, use these public read URLs as the canonical page
locations:

```text
https://md.zerotymer.net/en/skill/<uuid>
https://md.zerotymer.net/ko/skill/<uuid>
```

The edit-style path `/e/<locale>/skill/<uuid>` is not the public read path and
may return an authorization page. Convert it to `/<locale>/skill/<uuid>` before
fetching public HTML.

## Import Workflow

1. Validate that the user provided a UUID.
2. Fetch English content from `/en/skill/<uuid>`.
3. Fetch Korean content from `/ko/skill/<uuid>`.
4. Prefer GraphQL source Markdown if available; otherwise use public HTML and
   reconstruct Markdown conservatively.
5. Verify that the English content has valid skill frontmatter with at least
   `name` and `description`.
6. Use the frontmatter `name` value as `<skill-name>`.
7. Write English content to `skills/<skill-name>/SKILL.md`.
8. Write Korean content to `skills/<skill-name>/SKILL_ko.md`.
9. If Korean frontmatter is present, keep it semantically aligned with the
   English file. If it is absent, copy the English frontmatter and keep the
   Korean body.
10. Update `AGENTS.md` and `AGENTS_ko.md` only when the imported skill must be
    applied automatically or referenced by this project.

## Dynamic Reference Workflow

Use this workflow when the user asks to reference a Wiki.js skill for the
current task, including prompts such as `LLM-wiki <uuid> 참고해줘`.

1. Validate that the user provided a UUID.
2. Fetch the English and Korean content dynamically at request time.
3. Prefer GraphQL source Markdown; fall back to public HTML if needed.
4. Use the fetched content as task-local context.
5. Follow the fetched instructions when they are relevant and do not conflict
   with higher-priority system, developer, or project instructions.
6. Report briefly which Wiki.js UUID was referenced.
7. Do not create or update project files unless the user explicitly requests a
   persistent import or project-level application.

## API Comparison

GraphQL:

- Best for source-preserving imports.
- Returns structured page data when authorized.
- Better for automation, validation, and future refreshes.
- May require an API token or public GraphQL access.
- Requires schema discovery or a known Wiki.js GraphQL query.

Public HTML:

- Works when the page is publicly readable.
- Does not require API credentials.
- Good fallback for one-off imports.
- Loses source fidelity and requires HTML-to-Markdown reconstruction.
- Can break if the rendered theme or markup changes.

For this project, prefer GraphQL for repeatable automation and keep public HTML
fallback for unauthenticated access.
