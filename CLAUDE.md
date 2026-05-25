# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 프로젝트 개요

LLM Reference Registry — 코딩 에이전트(Codex, Claude Code, Cursor 등)가 화면(UI_AREA), 기능(FEATURE), 인프라(INFRA_UNIT)를 UUID 기반으로 안정적으로 참조할 수 있게 하는 경량 저장소. 문서 파싱은 외부 에이전트가 담당하고, 이 서비스는 정리된 결과를 저장/조회/제공하는 역할만 한다.

백엔드 코드는 `backend/` 디렉터리에 위치하며, `docker-compose.yml`은 루트에 둔다.

## 구현 현황 (MVP 완료)

| Step | 내용 | 브랜치 | 상태 |
|------|------|--------|------|
| 0 | 프로젝트 초기화 | feat/step0-project-init | 완료 |
| 1 | DB Schema (Alembic) | feat/step1-db-schema | 완료 |
| 2 | Domain 정의 (enums/models/schemas) | feat/step2-domain | 완료 |
| 3 | Entity CRUD | feat/step3-entity-crud | 완료 |
| 4 | Alias API + resolve | feat/step4-alias-api | 완료 |
| 5 | Context API | feat/step5-context-api | 완료 |
| 6 | Relation API | feat/step6-relation-api | 완료 |
| 7 | Batch Ingest | feat/step7-batch-ingest | 완료 |
| 8 | Context Bundle | feat/step8-context-bundle | 완료 |
| 9 | MCP Server (read-only) | feat/step9-mcp-server | 완료 |
| 10 | 테스트 정리 | feat/step10-tests | 완료 |

테스트: **95 passed** (`backend/.venv/bin/pytest tests/`)

## 확정 기술 스택

- **Backend**: FastAPI (Python 3.12)
- **ORM**: SQLAlchemy 2.x (async) + Alembic
- **DB**: PostgreSQL 16 + JSONB metadata
- **MCP**: Python MCP SDK (`mcp>=1.0.0`) — read-only
- **Deployment**: Docker Compose
- **Package Manager**: uv

## 개발 명령어

```bash
# 의존성 설치 (backend/ 에서)
cd backend
uv pip install -e ".[dev]"

# 개발 서버
uvicorn app.main:app --reload

# 테스트 (venv 사용)
.venv/bin/pytest tests/ -q
.venv/bin/pytest tests/test_alias_resolve.py::TestResolveAlias::test_ambiguous_multiple_matches -v

# DB 마이그레이션
alembic upgrade head

# Docker Compose (루트)
docker compose up -d
```

## 프로젝트 구조

```
docker-compose.yml          # postgres(5432), api(8000), mcp(stdio)
backend/
  pyproject.toml
  Dockerfile
  Makefile
  .env.example
  app/
    main.py                 # FastAPI 진입점, RegistryError 핸들러
    config.py               # pydantic-settings 환경변수
    exceptions.py           # RegistryError (code, message, status_code)
    api/
      entities.py           # POST/GET/PATCH /entities
      aliases.py            # POST/GET /entities/{id}/aliases, GET /resolve
      contexts.py           # POST/GET /entities/{id}/contexts
      relations.py          # POST /relations, GET /entities/{id}/relations
      ingest.py             # POST /ingest/batch
      bundles.py            # POST /context-bundle
      search.py             # GET /search
    domain/
      enums.py              # EntityType, EntityStatus, ContextType, RelationType, Locale
      models.py             # SQLAlchemy ORM (Entity, EntityAlias, …)
      schemas.py            # Pydantic v2 request/response
    repository/             # DB 접근 계층 (entity/alias/context/relation)
    service/                # 비즈니스 로직 (entity/alias/context/relation/bundle/ingest/search)
    mcp/
      server.py             # FastMCP 인스턴스
      tools.py              # 6개 read-only tool
    db/
      session.py            # async_session_factory
      migrations/           # Alembic (versions/001_initial_schema.py)
  tests/
    conftest.py             # DB 픽스처 + docs/10 예제 데이터 shared fixture
    test_entity_api.py
    test_alias_resolve.py
    test_context_api.py
    test_context_bundle.py
    test_ingest_batch.py
    test_mcp_tools.py
    test_relation_api.py
    test_domain_schemas.py
    test_examples.py        # docs/11 DoD 통합 테스트
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

| Tool | 설명 |
|------|------|
| `resolve_alias` | alias → entity (not_found/resolved/ambiguous) |
| `get_entity` | UUID로 entity 조회, deprecated warning 포함 |
| `search_entities` | alias exact → canonical_name partial → tsvector 순 검색 |
| `get_related_entities` | 관련 entity 조회 (direction, max_depth) |
| `get_context_bundle` | 핵심 tool — BFS로 관련 entity/context/relation 묶음 반환 |
| `validate_references` | ID/alias 유효성 일괄 검증 |

## API 응답 형식

모든 응답: `{"ok": true, "data": {...}}` 또는 `{"ok": false, "error": {"code": "...", "message": "..."}}`.

## 설계 문서

`docs/` 폴더에 00~11 번호 순으로 모든 설계가 있다. 구현 중 판단이 필요하면 해당 문서를 우선 참고한다.

## Instructions 워크플로우

모든 구현 작업은 `instructions/` 아래 지침 파일을 기준으로 진행한다.

### 지침 파일 생성

1. UUID 발급: `python3 -c "import uuid; print(uuid.uuid4())"`
2. `instructions/{slug}.md` 생성 — frontmatter에 uuid, title, status, created 기록
3. `instructions/instructions.log`에 한 줄 추가:
   ```
   {uuid} | {title} | {ISO8601 timestamp} | created
   ```

### 지침 완료 처리

모든 단계 완료 시:

1. frontmatter `status: completed`, `completed: {날짜}` 기록
2. `instructions/.completed/{uuid}.md`로 이동
3. `instructions/instructions.log`에 `completed` 이벤트 추가
4. git commit

### 현재 지침

| UUID | 파일 | 상태 |
|------|------|------|
| 240e1460-a7e6-4b0e-a08f-10f9c74c497c | .completed/ | completed (2026-05-25) |
| ce6d92bf-2c2d-4944-adb3-1089a6530e56 | instructions/security_ops.md | pending |
| 03080220-3b52-4d28-a79d-e2d698e5480f | instructions/extensions.md | pending |

## Git Branch 전략

Step별 `feat/step{N}-{slug}` 브랜치 → PR → main 머지.

브랜치 전략 스킬: `e03f48fb-3e00-41d7-b99d-c32854567d67`

## LLM-wiki 스킬 참조

작업 완료 보고 및 리뷰 시 아래 스킬을 활용한다.

| UUID | 용도 |
|------|------|
| `a43a68f9-fda2-4960-a49a-0a97ebf96a8a` | 백엔드/인프라 완료 보고 |
| `4de41e4d-536a-44ca-8194-f8c5c316e6bf` | Full-stack 완료 보고 |
| `dbdfdbab-77ed-49fe-b70e-1f1708fc7aab` | 프론트엔드 완료 보고 |
| `69a9089b-a444-4f44-89ab-5d58210906ae` | PR 템플릿 |
| `ed847c29-b20a-420b-9314-c16dce184d62` | 코드 리뷰 |
