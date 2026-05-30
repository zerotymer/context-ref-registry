---
uuid: 03080220-3b52-4d28-a79d-e2d698e5480f
title: 확장 기능 — pgvector, Revision, Export
status: draft
created: 2026-05-25
completed:
ref_docs:
  - docs/03-database-schema.md
  - docs/08-implementation-plan.md
prerequisite: ce6d92bf-2c2d-4944-adb3-1089a6530e56 (Phase 2 완료 후 또는 필요 시)
---

# 확장 기능 — pgvector, Revision, Export

> **이 지침은 운영 단계 진입 후 필요에 따라 개별 진행한다.**
> 각 Step은 독립적으로 진행 가능하다.

---

## Step 3-1. pgvector Semantic Search

**브랜치**: `feat/ext-pgvector`
**상태**: `[ ]` pending
**참조**: `docs/03-database-schema.md` (context_embedding 테이블)

### 조건

pgvector는 다음 조건에서 추가한다:

```
- LIKE + full-text 검색 품질이 충분하지 않을 때
- 사용자가 자연어로 검색할 필요가 생길 때
```

### 작업 목록

- [ ] PostgreSQL `vector` extension 활성화
- [ ] `context_embedding` 테이블 Alembic migration (`embedding vector(1536)`)
- [ ] embedding 생성 서비스 (OpenAI text-embedding-3-small 또는 동등 모델)
- [ ] batch ingest 시 context body → embedding 비동기 생성
- [ ] `GET /search` vector 검색 경로 추가 (기존 full-text fallback 유지)
- [ ] MCP `search_entities` tool에 vector 검색 연동

### 검색 우선순위 (확장 후)

```
1. id exact match
2. alias exact match
3. canonical_name partial match (LIKE)
4. context full-text search (tsvector)
5. context vector search (pgvector cosine similarity)
```

**완료일**: —

---

## Step 3-2. Entity Revision History

**브랜치**: `feat/ext-revision`
**상태**: `[x]` completed
**참조**: `docs/03-database-schema.md` (entity_revision 테이블)

### 작업 목록

- [x] `entity_history` 테이블 Alembic migration (`003_add_entity_history.py`)
  — entity_id, revision_no, snapshot (JSONB), changed_fields (JSONB), change_type, change_reason, changed_by, created_at
  — UNIQUE (entity_id, revision_no)
- [x] entity create/update 시 자동 revision 생성 (EntityService 후킹)
- [x] `GET /entities/{id}/history` 엔드포인트 + `GET /entities/{id}/history/{revision_no}` 단건 조회
- [x] revision 비교 API — `GET /entities/{id}/history/{rev_a}/compare/{rev_b}`
  — `_effective_state()` 로 before-image snapshot + changed_fields["after"] 적용 후 field-level diff 반환

### 구현 세부사항

- `entity_history` 테이블은 `entity_revision`과 동등 (changed_fields, change_type 추가 포함)
- snapshot = before-image (update 시) 또는 created state (create 시)
- `RevisionCompareResponse`: `diff[field] = {before, after, changed}` 구조
- 테스트: `test_history_api.py` 15개 + `test_revision_compare_api.py` 6개 → 전체 236 passed

**완료일**: 2026-05-30

---

## Step 3-3. Review UI

**브랜치**: `feat/ext-review-ui`
**상태**: `[x]` completed
**참조**: `frontend/src/app/(app)/review/`, `frontend/src/app/(app)/entities/[id]/`

### 작업 목록

- [x] 기술 스택 확정 → Next.js + Tailwind (기존 관리자 콘솔에 통합)
- [x] entity 목록 + status 필터 → EntityList (`/entities?status=candidate` 등)
- [x] candidate → active 승인 UI → ReviewCard + EntityDetail 헤더 승인 버튼
- [x] alias 추가/비활성화 UI
  — AliasPane에 비활성화 버튼 추가
  — 백엔드 `DELETE /entities/{id}/aliases/{alias_id}` 엔드포인트 추가
  — `test_alias_deactivate.py` 6개 테스트 → 모두 통과
- [x] deprecated 처리 UI (replacement_entity_id 연결)
  — EntityDetail "Deprecated 처리" 버튼 → DeprecateModal (사유 + 대체 UUID 입력)
  — `window.prompt` 방식 제거

### 구현 세부사항

- `AliasRepository.deactivate()`, `AliasService.deactivate_alias()` 신규 추가
- `DeprecateModal`: replacement_entity_id 지정 가능한 모달 컴포넌트
- 전체 테스트: **242 passed**

**완료일**: 2026-05-30

---

## Step 3-4. AGENTS.md Export

**브랜치**: `feat/ext-agents-export`
**상태**: `[ ]` pending

### 목적

에이전트가 작업 시작 시 참조할 `AGENTS.md` 형태의 context 내보내기.

### 작업 목록

- [ ] `GET /export/agents-md?root_ids=&max_depth=&token_budget=` 엔드포인트
- [ ] Context Bundle을 Markdown 형식으로 변환
- [ ] entity type별 섹션 구분
- [ ] deprecated warning 포함

**완료일**: —

---

## Step 3-5. GitHub PR 검증

**브랜치**: `feat/ext-pr-validation`
**상태**: `[ ]` pending

### 목적

PR diff에서 entity UUID/alias 참조를 추출하여 레지스트리 유효성 확인.

### 작업 목록

- [ ] GitHub webhook 또는 CI 스크립트 연동
- [ ] PR 코드/커밋 메시지에서 UUID/alias 패턴 추출
- [ ] `POST /validate-references` 또는 MCP `validate_references` 연동
- [ ] 결과를 PR comment로 게시

**완료일**: —

---

## Step 3-6. OpenAPI Export

**브랜치**: `feat/ext-openapi-export`
**상태**: `[ ]` pending

### 목적

레지스트리에 등록된 API entity를 OpenAPI spec으로 내보내기.

### 작업 목록

- [ ] `GET /export/openapi` 엔드포인트
- [ ] API type entity → OpenAPI path 변환 규칙 정의
- [ ] context body → description 매핑

**완료일**: —

---

## 우선순위 가이드

```
3-1 pgvector     → 검색 품질 불만 생길 때
3-2 Revision     → 운영 중 변경 이력 추적 필요 시
3-3 Review UI    → candidate entity 수가 많아질 때
3-4 AGENTS.md    → 에이전트 온보딩 자동화 필요 시
3-5 PR 검증      → 레지스트리 정합성 CI 통합 필요 시
3-6 OpenAPI      → API entity 활용도 높아질 때
```
