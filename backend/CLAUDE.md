# CLAUDE.md — backend/

FastAPI + SQLAlchemy 2.x 백엔드 전용 가이드.

## 디렉터리 구조

```
backend/
  pyproject.toml
  Dockerfile
  Makefile
  alembic.ini
  .env.example
  app/
    main.py                 # FastAPI 진입점, RegistryError 핸들러
    config.py               # pydantic-settings 환경변수
    exceptions.py           # RegistryError (code, message, status_code)
    dependencies.py         # FastAPI Depends — 인증 미들웨어 (get_current_user 등)
    policy.py               # 접근 정책 — 프로젝트 멤버십 기반 권한 검사
    api/
      auth.py               # POST /auth/login, /logout, /users, /api-keys; GET /auth/me
      projects.py           # CRUD /projects, /projects/{id}/members
      admin_projects.py     # GET /admin/projects (관리자 전용)
      admin_users.py        # GET /admin/users (관리자 전용)
      entities.py           # POST/GET/PATCH /entities
      aliases.py            # POST/GET /entities/{id}/aliases, GET /resolve, PATCH alias 비활성화
      contexts.py           # POST/GET /entities/{id}/contexts
      relations.py          # POST /relations, GET /entities/{id}/relations
      tags.py               # POST/DELETE /entities/{id}/tags, GET /tags
      ingest.py             # POST /ingest/batch
      bundles.py            # POST /context-bundle
      search.py             # GET /search
      export.py             # GET /export/agents-md, GET /export/openapi
      validate.py           # POST /validate-references
    auth/
      dependencies.py       # 인증 Depends 구현체 (JWT 검증, API Key 조회)
      policy.py             # 역할 기반 접근 제어
    domain/
      enums.py              # EntityType, EntityStatus, ContextType, RelationType, Locale
      models.py             # SQLAlchemy ORM (Entity, EntityAlias, User, Project, …)
      schemas.py            # Pydantic v2 request/response
    repository/             # DB 접근 계층
      entity_repository.py
      alias_repository.py
      context_repository.py
      relation_repository.py
      user_repository.py
      api_key_repository.py
      project_repository.py
      project_member_repository.py
      history_repository.py
    service/                # 비즈니스 로직
      entity_service.py
      alias_service.py
      context_service.py
      relation_service.py
      auth_service.py       # 로그인, JWT 발급, API Key 관리
      project_service.py    # 프로젝트 생성, 멤버 초대, 권한 검사
      bundle_service.py
      ingest_service.py
      search_service.py
      export_service.py     # AGENTS.md / OpenAPI 3.1.0 export
      validate_service.py   # PR 참조 검증 (UUID / alias 일괄 검증)
    mcp/
      server.py             # FastMCP 인스턴스
      tools.py              # 6개 read-only tool
    db/
      session.py            # async_session_factory
      migrations/           # Alembic (versions/)
  tests/
    conftest.py
    test_auth_api.py
    test_project_api.py
    test_admin_projects_api.py
    test_admin_users_api.py
    test_entity_api.py
    test_entity_list_api.py
    test_alias_resolve.py
    test_alias_deactivate.py
    test_context_api.py
    test_context_bundle.py
    test_tag_api.py
    test_history_api.py
    test_revision_compare_api.py
    test_ingest_batch.py
    test_mcp_tools.py
    test_relation_api.py
    test_domain_schemas.py
    test_examples.py
    test_search_api.py
    test_export_agents_md.py
    test_export_openapi.py
    test_validate_references_api.py
    test_audit_log.py
    test_observability.py
```

## 개발 환경

```bash
# 의존성 설치 (backend/ 에서)
uv pip install -e ".[dev]"

# 개발 서버 (hot-reload)
uvicorn app.main:app --reload --port 8000

# 테스트 — 반드시 .venv 파이썬 사용
.venv/bin/pytest tests/ -q
.venv/bin/pytest tests/test_alias_resolve.py -v     # 단일 파일
.venv/bin/pytest tests/ -k "ambiguous" -v           # 키워드 필터

# DB 마이그레이션
alembic upgrade head
alembic revision --autogenerate -m "describe change"

# MCP 서버 단독 실행 (stdio)
python -m app.mcp
```

## 환경변수

`.env.example`을 복사해서 `.env` 생성:

```
DATABASE_URL=postgresql+asyncpg://llmref:llmref@localhost:5432/llmref
TEST_DATABASE_URL=postgresql+asyncpg://llmref:llmref@localhost:5432/llmref_test
```

테스트는 `TEST_DATABASE_URL`을 우선 사용하며, `conftest.py`에서 `os.environ["DATABASE_URL"]`에 주입한다.

## 레이어 구조 및 규칙

```
api/        → HTTP 요청/응답 변환만. 비즈니스 로직 없음.
service/    → 비즈니스 로직. 트랜잭션 경계는 service에서 관리.
repository/ → SQLAlchemy 쿼리만. session을 외부에서 주입받음.
domain/     → enums, ORM models, Pydantic schemas. 순수 데이터 정의.
```

- **service는 repository를 직접 new** (`EntityRepository(session)`) — DI 컨테이너 없음.
- **API 에러는 `RegistryError`** (`app/exceptions.py`)를 raise. `main.py`의 핸들러가 표준 JSON으로 변환.
- **session은 `async with async_session_factory() as session`** 패턴 사용. 커밋은 service에서.

## DB 테이블 요약

| 테이블 | 역할 |
|--------|------|
| `users` | 사용자 계정 (email, hashed_password, role) |
| `sessions` | JWT 세션 (token, expires_at) |
| `api_keys` | API Key (key_hash, name, user_id) |
| `projects` | 프로젝트 (name, owner_id) |
| `project_members` | 프로젝트 멤버십 (project_id, user_id, role: viewer/editor/admin) |
| `entity` | UUID, type, canonical_name, status, confidence, project_id |
| `entity_alias` | locale별 alias (unique 제약 없음, is_active로 비활성화) |
| `entity_context` | context_type별 텍스트 (RAG 단위) |
| `entity_relation` | from/to entity 간 관계 (CONTAINS, RELATED_TO, USES 등) |
| `entity_metadata` | JSONB 타입별 상세 필드 |
| `entity_tag` | entity ↔ tag 다중 부착 |
| `entity_history` | entity 변경 이력 (field, old_value, new_value) |
| `source_ref` | 원본 문서 참조 |

Entity status: `candidate` → `active` → `deprecated` / `archived`

## 도메인 enum 값 (코드 작성 시 참조)

```python
EntityType:   UI_AREA | FEATURE | INFRA_UNIT | API | CODE_SYMBOL | ISSUE
EntityStatus: candidate | active | deprecated | archived
ContextType:  summary | details | business_rule | validation_rule |
              implementation_hint | security_note | infra_note |
              compatibility_note | exception_case
RelationType: CONTAINS | RELATED_TO | USES | IMPLEMENTED_BY |
              READS_FROM | WRITES_TO | DEPENDS_ON | CALLS
Locale:       ko | en
```

## API 엔드포인트 목록

### 인증

| 메서드 | 경로 | 설명 |
|--------|------|------|
| POST | `/auth/users` | 사용자 등록 |
| POST | `/auth/login` | 로그인 (JWT 발급) |
| POST | `/auth/logout` | 로그아웃 (세션 무효화) |
| GET | `/auth/me` | 현재 사용자 조회 |
| POST | `/auth/api-keys` | API Key 발급 |

### 프로젝트

| 메서드 | 경로 | 설명 |
|--------|------|------|
| POST | `/projects` | 프로젝트 생성 |
| GET | `/projects` | 프로젝트 목록 |
| GET | `/projects/{id}` | 프로젝트 조회 |
| GET | `/projects/{id}/members` | 멤버 목록 |
| POST | `/projects/{id}/members` | 멤버 추가 |
| PUT | `/projects/{id}/members/{user_id}` | 멤버 역할 변경 |
| DELETE | `/projects/{id}/members/{user_id}` | 멤버 제거 |

### Registry

| 메서드 | 경로 | 설명 |
|--------|------|------|
| POST | `/entities` | entity 생성 (id 지정 가능) |
| GET | `/entities` | entity 목록 조회 (필터·페이징) |
| GET | `/entities/{id}` | entity 조회 |
| PATCH | `/entities/{id}` | entity 수정 (id·type 변경 불가) |
| POST | `/entities/{id}/aliases` | alias 추가 |
| GET | `/entities/{id}/aliases` | alias 목록 |
| PATCH | `/entities/{id}/aliases/{alias_id}` | alias 비활성화 |
| GET | `/resolve` | alias → entity resolve |
| POST | `/entities/{id}/contexts` | context 추가 |
| GET | `/entities/{id}/contexts` | context 목록 |
| POST | `/entities/{id}/tags` | tag 부착 |
| DELETE | `/entities/{id}/tags/{tag}` | tag 제거 |
| GET | `/entities/{id}/history` | 변경 이력 |
| GET | `/entities/{id}/revisions` | revision 목록 |
| GET | `/entities/{id}/revisions/compare` | revision 비교 |
| POST | `/relations` | relation 생성 |
| GET | `/entities/{id}/relations` | relation 목록 (direction, max_depth) |
| GET | `/search?q=&types=&limit=` | entity 검색 |
| POST | `/context-bundle` | BFS context bundle |
| POST | `/ingest/batch` | 일괄 ingest |
| GET | `/export/agents-md` | AGENTS.md 형식 컨텍스트 내보내기 |
| GET | `/export/openapi` | OpenAPI 3.1.0 spec (JSON/YAML) 내보내기 |
| POST | `/validate-references` | PR 내 참조 일괄 검증 (UUID / alias) |
| GET | `/health` | 헬스체크 |

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

## 핵심 불변 규칙

- `entity.id` (UUID)는 생성 후 절대 변경 금지. PATCH에서 `id`·`type` 필드 수신 시 무시.
- alias는 unique 제약 없음. 중복 resolve 시 `ambiguous` 반환 — 임의 선택 금지.
- deprecated entity는 DELETE 금지. `status=deprecated` + `replacement_entity_id` 기록.
- MCP tool은 read-only만. write tool 추가 금지.

## Batch Ingest 검증 순서

`POST /ingest/batch` 처리 흐름:

1. `source_ref` upsert (같은 URI면 재사용)
2. entity upsert — id 있으면 update, 없으면 insert. **type 변경 시 400 `TYPE_CHANGE_FORBIDDEN`**
3. alias upsert — `(entity_id, locale, alias)` 조합이 active면 스킵
4. context insert
5. relation 검증 — `from_entity_id`/`to_entity_id`가 배치 내부 또는 DB에 존재해야 함. 없으면 400 `INVALID_RELATION_TARGET`
6. relation insert

## Context Bundle BFS

`POST /context-bundle` 알고리즘:

1. `root_ids` 존재 검증 → 없으면 404
2. root entity 조회
3. BFS로 relation graph 탐색 (`max_depth` 제한)
4. `include_types` / `include_relations` 필터 적용
5. 모든 entity의 context 조회
6. `token_budget` 초과 시 우선순위 컷:
   `summary > business_rule > validation_rule > implementation_hint > security_note > infra_note > details > compatibility_note > exception_case`
7. deprecated entity → `warnings`에 추가 (`replacement_entity_id` 포함)

## 테스트 구조

```
conftest.py                    DB 픽스처 (schema drop/create, table clean), 공유 fixture
test_auth_api.py               로그인, 로그아웃, 사용자 등록, API Key 발급
test_project_api.py            프로젝트 CRUD, 멤버 초대/제거, 역할 변경
test_admin_projects_api.py     관리자 프로젝트 관리 API (project_admin 권한 포함)
test_admin_users_api.py        관리자 사용자 관리 API
test_entity_api.py             Entity CRUD, PATCH 제한, deprecated
test_entity_list_api.py        GET /entities 목록 조회, 필터·페이징
test_alias_resolve.py          ambiguous/resolved/not_found, locale/type 필터
test_alias_deactivate.py       alias 비활성화 (PATCH)
test_context_api.py            Context 추가/조회, 필터
test_context_bundle.py         depth, token_budget, deprecated warning
test_tag_api.py                tag 부착/제거, 다중 tag
test_history_api.py            entity 변경 이력 조회
test_revision_compare_api.py   revision 목록 및 비교 API
test_ingest_batch.py           upsert, type 변경 금지, relation 검증
test_mcp_tools.py              MCP 6개 tool 직접 호출
test_relation_api.py           relation 생성/조회, direction/depth
test_domain_schemas.py         Pydantic 스키마 검증
test_examples.py               docs/10 예제 기반 DoD 통합 테스트
test_search_api.py             GET /search (alias exact, canonical partial, type filter)
test_export_agents_md.py       GET /export/agents-md — AGENTS.md 포맷 검증
test_export_openapi.py         GET /export/openapi — JSON/YAML OpenAPI 3.1.0 검증
test_validate_references_api.py POST /validate-references — valid/ambiguous/missing 분류
test_audit_log.py              Audit Log 기록 및 조회
test_observability.py          Observability 엔드포인트
```

테스트는 **실제 PostgreSQL**(TEST_DATABASE_URL)에서 실행. mock DB 사용 금지.

각 테스트는 `_clean_tables` fixture로 테이블 전체 truncate 후 실행.

## 주의사항
- MCP server는 `stdio` transport로 실행 (`python -m app.mcp` → `app/mcp/__main__.py`). 포트 미사용, 클라이언트가 프로세스를 spawn. docker-compose `mcp` 서비스도 stdio (`stdin_open: true`).
- `pyproject.toml`의 `mcp>=1.0.0` 의존성은 시스템 Python이 아닌 `.venv`에만 설치됨 — 항상 `.venv/bin/python` 사용.
