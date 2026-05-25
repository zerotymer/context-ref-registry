# 프로젝트 완료 보고 — LLM Reference Registry (Backend/Infra)

> **보고일**: 2026-05-25  
> **작성**: Claude Code (Sonnet 4.6)  
> **스킬 참조**: `a43a68f9-fda2-4960-a49a-0a97ebf96a8a` (백엔드/인프라 완료 보고)

---

## 1. 프로젝트 개요

코딩 에이전트(Codex, Claude Code, Cursor 등)가 화면(UI_AREA), 기능(FEATURE), 인프라(INFRA_UNIT)를
UUID 기반으로 안정적으로 참조할 수 있게 하는 **경량 레지스트리 서비스**. 문서 파싱은 외부 에이전트가 담당하며,
이 서비스는 정리된 결과의 저장·조회·제공만 담당한다.

---

## 2. MVP 구현 현황 (Phase 1 완료)

| Step | 내용 | 브랜치 | 상태 |
|------|------|--------|------|
| 0 | 프로젝트 초기화 | feat/step0-project-init | ✅ 완료 |
| 1 | DB Schema (Alembic) | feat/step1-db-schema | ✅ 완료 |
| 2 | Domain 정의 (enums/models/schemas) | feat/step2-domain | ✅ 완료 |
| 3 | Entity CRUD | feat/step3-entity-crud | ✅ 완료 |
| 4 | Alias API + resolve | feat/step4-alias-api | ✅ 완료 |
| 5 | Context API | feat/step5-context-api | ✅ 완료 |
| 6 | Relation API | feat/step6-relation-api | ✅ 완료 |
| 7 | Batch Ingest | feat/step7-batch-ingest | ✅ 완료 |
| 8 | Context Bundle | feat/step8-context-bundle | ✅ 완료 |
| 9 | MCP Server (read-only) | feat/step9-mcp-server | ✅ 완료 |
| 10 | 테스트 정리 | feat/step10-tests | ✅ 완료 |

**MVP 지침 완료**: `240e1460-a7e6-4b0e-a08f-10f9c74c497c` (2026-05-25)

---

## 3. 기술 스택

| 항목 | 선택 |
|------|------|
| Runtime | Python 3.12 |
| Framework | FastAPI (async) |
| ORM | SQLAlchemy 2.x (async) + Alembic |
| DB | PostgreSQL 16 + JSONB metadata |
| MCP | Python MCP SDK (`mcp>=1.0.0`) — read-only |
| Package Manager | uv |
| 배포 | Docker Compose |

---

## 4. 아키텍처

```
외부 Parser/Agent → POST /ingest/batch → Registry (PostgreSQL)
                                               ↓
Coding Agent ← MCP read-only server ← REST read API
```

### 서비스 구성 (docker-compose.yml)

| 서비스 | 이미지/포트 | 역할 |
|--------|------------|------|
| `postgres` | postgres:16-alpine / 5432 | 데이터 저장소 |
| `api` | ./backend / 8000 | FastAPI REST API (read+write) |
| `mcp` | ./backend / stdio | Read-only MCP server (에이전트 연동) |

### 소스 파일 구조

```
backend/app/
  main.py, config.py, exceptions.py   — 진입점 & 공통
  api/       (7개)  entities, aliases, contexts, relations,
                    ingest, bundles, search
  domain/    (3개)  enums, models, schemas
  repository/(4개)  entity, alias, context, relation
  service/   (7개)  entity, alias, context, relation,
                    bundle, ingest, search
  mcp/       (3개)  server, tools, __main__
  db/               session, migrations (Alembic)
```

총 소스 파일: **37개** (`.py`)

---

## 5. DB 스키마

| 테이블 | 역할 |
|--------|------|
| `entity` | UUID, type, canonical_name, status, confidence |
| `entity_alias` | locale별 alias (unique 제약 없음, is_active로 비활성화) |
| `entity_context` | context_type별 텍스트 (RAG 단위) |
| `entity_relation` | from/to entity 간 관계 (CONTAINS, RELATED_TO, USES 등) |
| `entity_metadata` | JSONB 타입별 상세 필드 |
| `source_ref` | 원본 문서 참조 |

**Entity 상태 흐름**: `candidate` → `active` → `deprecated` / `archived`

---

## 6. REST API 엔드포인트

| 메서드 | 경로 | 설명 |
|--------|------|------|
| POST | `/entities` | Entity 생성 |
| GET | `/entities/{id}` | Entity 조회 |
| PATCH | `/entities/{id}` | Entity 수정 |
| POST | `/entities/{id}/aliases` | Alias 추가 |
| GET | `/entities/{id}/aliases` | Alias 목록 |
| GET | `/resolve` | Alias → Entity 해석 |
| POST | `/entities/{id}/contexts` | Context 추가 |
| GET | `/entities/{id}/contexts` | Context 목록 |
| POST | `/relations` | Relation 생성 |
| GET | `/entities/{id}/relations` | Relation 목록 |
| POST | `/ingest/batch` | 일괄 ingest |
| POST | `/context-bundle` | Context Bundle 생성 (BFS) |
| GET | `/search` | 다단계 검색 |

**공통 응답 형식**: `{"ok": true, "data": {...}}` / `{"ok": false, "error": {"code": "...", "message": "..."}}`

---

## 7. MCP Tool 목록 (read-only)

| Tool | 설명 |
|------|------|
| `resolve_alias` | alias → entity (not_found / resolved / ambiguous) |
| `get_entity` | UUID로 entity 조회, deprecated warning 포함 |
| `search_entities` | alias exact → canonical_name partial → tsvector 순 |
| `get_related_entities` | 관련 entity 조회 (direction, max_depth) |
| `get_context_bundle` | BFS로 관련 entity/context/relation 묶음 반환 |
| `validate_references` | ID/alias 유효성 일괄 검증 |

---

## 8. 핵심 도메인 불변 규칙

| 규칙 | 내용 |
|------|------|
| UUID 불변 | 생성 후 절대 변경 금지 |
| alias 중복 허용 | 중복 시 `ambiguous` 응답, 임의 선택 금지 |
| resolve 결과 | `not_found` / `resolved` / `ambiguous` 세 가지만 |
| deprecated 보존 | 삭제 금지 — status 변경 + `replacement_entity_id` 기록 |
| MCP read-only | write tool 추가 금지 |

---

## 9. 테스트 현황

| 항목 | 결과 |
|------|------|
| 전체 테스트 | **100 passed** |
| 실패 | 0 |
| 실행 시간 | 2.36s |

### 테스트 파일 목록 (11개)

```
conftest.py            — DB 픽스처 + shared fixture
test_entity_api.py
test_alias_resolve.py
test_context_api.py
test_context_bundle.py
test_domain_schemas.py
test_examples.py       — docs/11 DoD 통합 테스트
test_ingest_batch.py
test_mcp_tools.py
test_relation_api.py
test_search_api.py
```

---

## 10. 미완료 지침 (Phase 2/3 대기)

### Phase 2 — 운영 준비 (`ce6d92bf`)

| Step | 내용 | 상태 |
|------|------|------|
| 2-1 | API Key 인증 (`X-API-Key` 헤더, write 보호) | pending |
| 2-2 | Audit Log (`entity_audit_log` 테이블 + AuditService) | pending |
| 2-3 | Backup (`pg_dump` daily cron) | pending |
| 2-4 | Observability (structlog JSON 로그 + `GET /health`) | pending |

**미결 사항**
- actor 식별: API key 식별자 vs. 별도 사용자 개념
- Backup 경로 확정 (로컬 볼륨 vs. minio)

### Phase 3 — 확장 기능 (`03080220`)

| Step | 내용 | 트리거 조건 |
|------|------|------------|
| 3-1 | pgvector Semantic Search | 검색 품질 불만 시 |
| 3-2 | Entity Revision History | 변경 이력 추적 필요 시 |
| 3-3 | Review UI (candidate 승인 UI) | candidate 수 증가 시 |
| 3-4 | AGENTS.md Export | 에이전트 온보딩 자동화 필요 시 |
| 3-5 | GitHub PR 검증 (webhook/CI) | CI 통합 필요 시 |
| 3-6 | OpenAPI Export | API entity 활용도 증가 시 |

---

## 11. Git 현황

- **브랜치**: `main` (origin/main 동기화 완료)
- **최근 커밋**: `5a9ded3` — chore: add Claude Code project settings and skills
- **미커밋 변경**: `CLAUDE.md` (LLM-wiki 스킬 참조 섹션 추가)

---

## 12. 다음 액션 (권장 순서)

1. **`CLAUDE.md` 변경 커밋** — LLM-wiki 스킬 참조 섹션
2. **Phase 2 시작 결정** — `ce6d92bf` security_ops.md 검토 후 착수
   - 우선 순위: Step 2-1 (API Key 인증) → Step 2-4 (Observability) → Step 2-2 (Audit Log)
3. **미결 사항 확정** — actor 식별 방식, Backup 위치
4. Phase 3은 Phase 2 완료 후 필요에 따라 개별 진행
