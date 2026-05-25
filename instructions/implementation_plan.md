---
uuid: 240e1460-a7e6-4b0e-a08f-10f9c74c497c
title: MVP 구현 계획 — LLM Reference Registry
status: pending
created: 2026-05-25
completed:
ref_docs:
  - docs/08-implementation-plan.md
  - docs/11-codex-task-brief.md
  - docs/03-database-schema.md
  - docs/04-rest-api.md
  - docs/05-mcp-server.md
  - docs/06-context-bundle.md
  - docs/07-ingest-format.md
  - docs/09-security-and-ops.md
---

# MVP 구현 계획 — LLM Reference Registry

## 확정 기술 스택

| 항목 | 확정값 |
|------|--------|
| Language | Python 3.12 |
| Framework | FastAPI |
| ORM | SQLAlchemy 2.x (async) |
| Migration | Alembic |
| DB | PostgreSQL 16 |
| MCP | Python MCP SDK (read-only) |
| Deployment | Docker Compose (minio 제외, MVP에서 불필요) |
| Package Manager | uv |
| Test | pytest (real DB via TEST_DATABASE_URL 환경변수) |
| Test Fixtures | `conftest.py` — docs/10 예제 데이터 기반 |

## 완료 기준 (Definition of Done)

`docs/11-codex-task-brief.md` 기준:

- [ ] `docker compose up`으로 API와 DB가 정상 실행
- [ ] batch ingest sample 성공
- [ ] alias resolve ambiguous case 동작
- [ ] context bundle API JSON 반환
- [ ] MCP tool `get_context_bundle` 호출 성공
- [ ] `pytest` 전체 통과

---

## Step 0. 프로젝트 초기화

**브랜치**: `feat/step0-project-init`
**상태**: `[x]` completed

### 작업 목록

- [x] `pyproject.toml` 작성 (uv 기반)
- [x] `docker-compose.yml` 작성 (api, mcp, postgres 서비스 — minio 제외)
- [x] `.env.example`에 `TEST_DATABASE_URL` 항목 포함
- [x] `.env.example` 작성
- [x] `app/` 디렉터리 뼈대 생성
- [x] `tests/` 디렉터리 생성
- [x] `Makefile` 기본 명령어 정의

### 완료 조건

- `docker compose up -d` 실행 시 postgres 컨테이너 기동
- `uv pip install -e .` 성공 ✓

**완료일**: 2026-05-25

---

## Step 1. DB Schema 작성

**브랜치**: `feat/step1-db-schema`
**상태**: `[x]` completed
**참조**: `docs/03-database-schema.md`

### 작업 목록

- [x] Alembic 초기화 (`alembic init`)
- [x] `entity` 테이블 migration 작성
- [x] `entity_alias` 테이블 migration 작성 (unique 제약 없음)
- [x] `entity_context` 테이블 migration 작성
- [x] `entity_relation` 테이블 migration 작성
- [x] `entity_metadata` 테이블 migration 작성 (JSONB)
- [x] `source_ref` 테이블 migration 작성
- [x] 인덱스 전체 확인 (type, status, alias, locale+alias)

### 완료 조건

- `alembic upgrade head` 성공
- 모든 테이블 및 인덱스 생성 확인

**완료일**: 2026-05-25

---

## Step 2. Domain 정의

**브랜치**: `feat/step2-domain`
**상태**: `[ ]` pending
**참조**: `docs/02-domain-model.md`, `docs/11-codex-task-brief.md`

### 작업 목록

- [ ] `app/domain/enums.py` — EntityType, EntityStatus, ContextType, RelationType, Locale
- [ ] `app/domain/models.py` — SQLAlchemy ORM 모델 (Entity, EntityAlias, EntityContext, EntityRelation, EntityMetadata, SourceRef)
- [ ] `app/domain/schemas.py` — Pydantic v2 request/response schema
- [ ] 공통 응답 스키마: `{"ok": true, "data": {}}` / `{"ok": false, "error": {"code", "message"}}`

### 완료 조건

- `from app.domain.enums import EntityType` import 성공
- Pydantic schema validation 단위 테스트 통과

**완료일**: —

---

## Step 3. Entity CRUD

**브랜치**: `feat/step3-entity-crud`
**상태**: `[ ]` pending
**참조**: `docs/04-rest-api.md`

### 작업 목록

- [ ] `app/repository/entity_repository.py`
- [ ] `app/service/entity_service.py`
- [ ] `app/api/entities.py`
  - `POST /entities` — id 지정 또는 서버 UUID 생성
  - `GET /entities/{id}` — 404 시 표준 에러 반환
  - `PATCH /entities/{id}` — id·type 변경 거부
- [ ] `app/db/session.py` — async SQLAlchemy session 설정

### 주의사항

- `id`는 생성 후 변경 불가 → PATCH에서 id 필드 수신 시 무시 또는 400
- `type` 변경은 기본 거부
- deprecated entity 조회 시 status 명시 필수

### 완료 조건

- `POST /entities` → 201, UUID 반환
- `GET /entities/{uuid}` → 200, entity 반환
- `GET /entities/nonexistent` → 404

**완료일**: —

---

## Step 4. Alias API

**브랜치**: `feat/step4-alias-api`
**상태**: `[ ]` pending
**참조**: `docs/04-rest-api.md`, `docs/02-domain-model.md`

### 작업 목록

- [ ] `app/repository/alias_repository.py`
- [ ] `app/service/alias_service.py`
- [ ] `app/api/aliases.py`
  - `POST /entities/{id}/aliases`
  - `GET /entities/{id}/aliases`
  - `GET /resolve?alias=&locale=&type=`

### resolve 결과 3가지 (반드시 준수)

```
not_found  → 매칭 없음
resolved   → 단일 매칭
ambiguous  → 복수 매칭, candidates 반환, 임의 선택 금지
```

### 완료 조건 (테스트 필수)

- alias 중복 등록 시 `ambiguous` 반환
- 단일 매칭 시 `resolved` 반환
- 없는 alias → `not_found`

**완료일**: —

---

## Step 5. Context API

**브랜치**: `feat/step5-context-api`
**상태**: `[ ]` pending
**참조**: `docs/04-rest-api.md`

### 작업 목록

- [ ] `app/repository/context_repository.py`
- [ ] `app/service/context_service.py`
- [ ] `app/api/contexts.py`
  - `POST /entities/{id}/contexts`
  - `GET /entities/{id}/contexts?context_type=&language=`

### 완료 조건

- context 추가 후 조회 성공
- context_type, language 필터 동작

**완료일**: —

---

## Step 6. Relation API

**브랜치**: `feat/step6-relation-api`
**상태**: `[ ]` pending
**참조**: `docs/04-rest-api.md`

### 작업 목록

- [ ] `app/repository/relation_repository.py`
- [ ] `app/service/relation_service.py`
- [ ] `app/api/relations.py`
  - `POST /relations` — from/to entity 존재 여부 검증
  - `GET /entities/{id}/relations?direction=&relation_type=&max_depth=`

### 완료 조건

- relation 생성 후 조회 성공
- direction=out/in/both 동작
- from/to entity 미존재 시 에러

**완료일**: —

---

## Step 7. Batch Ingest

**브랜치**: `feat/step7-batch-ingest`
**상태**: `[ ]` pending
**참조**: `docs/07-ingest-format.md`

### 작업 목록

- [ ] `app/service/ingest_service.py`
- [ ] `app/api/ingest.py`
  - `POST /ingest/batch`

### 검증 로직 (필수)

- UUID 형식 검증
- type / status / context_type / locale 허용값 검증
- relation의 `from_entity_id` / `to_entity_id` 존재 확인:
  - **같은 배치 내부 entity** 또는 **기존 DB entity** 모두 유효
  - 둘 다 없으면 → `INVALID_RELATION_TARGET` 에러

### Upsert 정책

- Entity: id 없음 → 신규, id 있음 → update (type 변경 불가)
- Alias: 같은 entity_id + locale + alias 가 active면 스킵
- Relation: MVP에서는 중복 허용

### 완료 조건 (테스트 필수)

- 정상 배치 → created 건수 반환
- 배치 내 relation target 누락 → 실패
- 같은 배치 내부 entity를 relation target으로 사용 가능

**완료일**: —

---

## Step 8. Context Bundle

**브랜치**: `feat/step8-context-bundle`
**상태**: `[ ]` pending
**참조**: `docs/06-context-bundle.md`, `docs/04-rest-api.md`

### 작업 목록

- [ ] `app/service/bundle_service.py`
- [ ] `app/api/bundles.py`
  - `POST /context-bundle`

### BFS 탐색 알고리즘

```
1. root_ids 검증 (UUID 존재 여부)
2. root entity 조회
3. relation graph BFS (max_depth까지)
4. include_types / include_relations 필터
5. contexts 조회
6. token_budget 초과 시 우선순위 컷:
   summary > business_rule > validation_rule >
   implementation_hint > security_note > infra_note >
   details > compatibility_note > exception_case
7. deprecated entity → warnings에 추가 (replacement_entity_id 포함)
8. 응답 조립: roots / entities / contexts / relations / warnings
```

### 완료 조건 (테스트 필수)

- root + depth 1 entity 포함 확인
- max_depth 제한 동작
- deprecated entity → warning 반환

**완료일**: —

---

## Step 9. MCP Server

**브랜치**: `feat/step9-mcp-server`
**상태**: `[ ]` pending
**참조**: `docs/05-mcp-server.md`

### 작업 목록

- [ ] `app/mcp/server.py` — Python MCP SDK 서버 설정
- [ ] `app/mcp/tools.py` — read-only tool 구현

### 구현할 Tool 목록

| Tool | 설명 |
|------|------|
| `resolve_alias` | alias → entity id 변환 (not_found/resolved/ambiguous) |
| `get_entity` | UUID로 entity 조회 |
| `search_entities` | 쿼리로 entity 검색 |
| `get_related_entities` | 관련 entity 조회 |
| `get_context_bundle` | 핵심 tool — bundle 반환 |
| `validate_references` | ID/alias 유효성 검증 |

### 보안 원칙

- write tool 추가 금지
- secret 값 반환 금지
- context는 data로 처리 (instruction 아님)

### 완료 조건

- MCP client로 `get_context_bundle` 호출 성공
- `resolve_alias` ambiguous case 동작

**완료일**: —

---

## Step 10. 테스트 작성

**브랜치**: `feat/step10-tests`
**상태**: `[ ]` pending
**참조**: `docs/11-codex-task-brief.md`

### 필수 테스트 목록

| 파일 | 테스트 케이스 |
|------|-------------|
| `conftest.py` | pytest fixtures — docs/10 예제 데이터 (UI_AREA, FEATURE, INFRA_UNIT, Relation) |
| `test_entity_api.py` | UUID 생성/조회, PATCH 제한, deprecated 표시 |
| `test_alias_resolve.py` | ambiguous / resolved / not_found |
| `test_context_bundle.py` | depth 탐색, token_budget 컷, deprecated warning |
| `test_ingest_batch.py` | 정상 배치, relation target 누락 실패, 배치 내부 참조 |

### conftest.py fixtures 구성 (docs/10 기반)

```python
# 사용할 예제 entity 3개 + relation 2개
entity_user_search_area     # UI_AREA: 사용자 검색 조건 영역
entity_user_search_feature  # FEATURE: 사용자 검색
entity_user_db              # INFRA_UNIT: 사용자 서비스 PostgreSQL
relation_area_to_feature    # RELATED_TO
relation_feature_to_db      # READS_FROM
```

### 테스트 DB 격리

```bash
# .env.test 또는 환경변수
TEST_DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/llmref_test
```

pytest 실행 전 test DB에 `alembic upgrade head` 자동 실행, 각 테스트 후 rollback.

### 완료 조건

- `pytest` 전체 통과
- 전체 6개 완료 기준 확인 (`docs/11` 참조)

**완료일**: —

---

## 확정 사항

| 항목 | 결정 |
|------|------|
| Write API 인증 | MVP에서 인증 없이 시작. 운영 단계에서 API Key/scope 추가. |
| Python 버전 | 3.12 |
| 브랜치 전략 | Step별 `feat/step{N}-{slug}` → PR → main (스킬 `e03f48fb-3e00-41d7-b99d-c32854567d67` 참조) |
| Search 방식 | PostgreSQL LIKE + full-text (tsvector). alias exact → canonical_name partial → context tsvector 순서. |
