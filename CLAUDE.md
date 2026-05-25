# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 프로젝트 개요

LLM Reference Registry — 코딩 에이전트(Codex, Claude Code, Cursor 등)가 화면(UI_AREA), 기능(FEATURE), 인프라(INFRA_UNIT)를 UUID 기반으로 안정적으로 참조할 수 있게 하는 경량 저장소. 문서 파싱은 외부 에이전트가 담당하고, 이 서비스는 정리된 결과를 저장/조회/제공하는 역할만 한다.

현재 이 저장소는 **설계 문서만 존재**하고 코드 구현은 아직 없다. 구현 시 `docs/` 문서를 기준으로 한다.

## 권장 기술 스택

- **Backend**: FastAPI (Python)
- **DB**: PostgreSQL + JSONB metadata (pgvector는 optional — semantic search 필요 시 추가)
- **Deployment**: Docker Compose
- **MCP**: Python MCP SDK (read-only server)

## 개발 명령어 (구현 후 기준)

```bash
# 의존성 설치
uv pip install -r requirements.txt

# 개발 서버 실행
uvicorn app.main:app --reload

# 전체 테스트
pytest

# 단일 테스트
pytest tests/test_alias_resolve.py::test_ambiguous_returns_candidates -v

# Docker Compose 실행
docker compose up -d
```

## 프로젝트 구조 (구현 목표)

```
app/
  main.py              # FastAPI 앱 진입점
  config.py            # 환경변수/설정
  api/                 # REST endpoint 모음 (entities, aliases, contexts, relations, search, ingest, bundles)
  domain/              # models.py, enums.py, schemas.py
  repository/          # DB 접근 계층
  service/             # 비즈니스 로직 (entity, alias, context, relation, bundle, search, ingest)
  mcp/                 # MCP read-only server (server.py, tools.py)
  db/
    session.py
    migrations/
tests/
```

## 아키텍처 흐름

```
외부 Parser/Agent → POST /ingest/batch → Registry (PostgreSQL)
                                              ↓
Coding Agent ← MCP read-only server ← REST read API
```

REST API는 write/read 모두 담당하고, MCP server는 **read-only**로만 제공한다.

## 핵심 도메인 불변 규칙

- **UUID는 불변**: 생성 후 절대 변경 금지. alias나 canonical_name이 바뀌어도 UUID는 유지.
- **alias 중복 허용**: alias에 unique 제약 없음. 중복 시 `ambiguous` 응답 반환, 임의 선택 금지.
- **alias resolve 결과**: `not_found` / `resolved` / `ambiguous` 세 가지만.
- **deprecated entity 삭제 금지**: status를 `deprecated`로 바꾸고 `replacement_entity_id`를 기록.
- **MCP는 read-only**: write tool 추가 금지. 쓰기는 REST API로만.

## DB 테이블 요약

| 테이블 | 역할 |
|--------|------|
| `entity` | UUID, type, canonical_name, status, confidence |
| `entity_alias` | locale별 alias (unique 제약 없음, is_active로 비활성화) |
| `entity_context` | context_type별 텍스트 (RAG 단위) |
| `entity_relation` | from/to entity 간 관계 (CONTAINS, RELATED_TO, USES 등) |
| `entity_metadata` | JSONB 타입별 상세 필드 |
| `source_ref` | 원본 문서 참조 |

Entity status: `candidate` → `active` → `deprecated` / `archived`

## MCP Tool 목록

`resolve_alias`, `get_entity`, `search_entities`, `get_related_entities`, `get_context_bundle`, `validate_references`

가장 중요한 tool은 `get_context_bundle` — root entity에서 max_depth, token_budget 기준으로 관련 entity/context/relation을 묶어 반환.

## API 응답 형식

모든 응답은 `{"ok": true, "data": {...}}` 또는 `{"ok": false, "error": {"code": "...", "message": "..."}}`.

## 구현 순서 참고

`docs/08-implementation-plan.md` Step 1~10 순서를 따른다. Batch Ingest(`POST /ingest/batch`) 검증 시 같은 배치 내부의 relation target 존재 여부를 확인해야 한다.

## 설계 문서

`docs/` 폴더에 00~11 번호 순으로 모든 설계가 있다. 구현 중 판단이 필요하면 해당 문서를 우선 참고한다.

## Instructions 워크플로우

모든 구현 작업은 `instructions/` 아래 지침 파일을 기준으로 진행한다.

### 지침 파일 생성

새 지침 작성 시:

1. UUID 발급: `python3 -c "import uuid; print(uuid.uuid4())"`
2. `instructions/{slug}.md` 생성 — frontmatter에 uuid, title, status, created 기록
3. `instructions/instructions.log`에 한 줄 추가:
   ```
   {uuid} | {title} | {ISO8601 timestamp} | created
   ```

### 단계 진행 시

각 Step 완료 시 지침 파일 내 해당 항목 체크박스를 완료로 업데이트하고 완료일을 기록한다.

### 지침 완료 처리

지침의 모든 단계가 완료되면:

1. 지침 파일 frontmatter의 `status: completed`, `completed: {날짜}` 기록
2. `instructions/.completed/{uuid}.md`로 이동
3. `instructions/instructions.log`에 한 줄 추가:
   ```
   {uuid} | {title} | {ISO8601 timestamp} | completed
   ```
4. git commit

### 현재 지침

| UUID | 파일 | 상태 |
|------|------|------|
| 240e1460-a7e6-4b0e-a08f-10f9c74c497c | instructions/implementation_plan.md | pending |

## Git Branch 전략

브랜치 전략은 스킬 `e03f48fb-3e00-41d7-b99d-c32854567d67` (git-branch 전략)을 참조한다.

지침 Step별로 `feat/step{N}-{slug}` 브랜치를 생성하고, 완료 후 PR을 통해 `main`에 머지한다.
