# Instructions

LLM Reference Registry 구현 지침 파일 모음.
모든 구현 작업은 이 디렉터리의 지침을 기준으로 진행한다.

---

## 지침 관리 규칙

| 규칙 | 내용 |
|------|------|
| 파일 생성 | UUID 발급 → `instructions/{slug}.md` 작성 → `instructions.log` 기록 |
| 진행 기록 | 각 Step 완료 시 지침 파일 체크박스 업데이트 + 완료일 기록 |
| 완료 처리 | frontmatter `status: completed` → `instructions/.completed/{uuid}.md` 이동 → log 기록 → 커밋 |
| 브랜치 전략 | Step별 `feat/step{N}-{slug}` → PR → main (스킬 `e03f48fb-3e00-41d7-b99d-c32854567d67`) |
| 참조 문서 | `docs/00~11` — 구현 중 판단 필요 시 해당 문서 우선 참고 |
| **진행상태 점검** | '진행상태 점검' 또는 '지침 업데이트' 요청 시 CLAUDE.md, AGENTS.md, instructions/README.md 동기화 필수 |

---

## 전체 구현 로드맵

```
Phase 1   — MVP 구현                                  ✅ 완료 (2026-05-25)
Phase 1.5 — Entity 목록 API                           ✅ 완료 (2026-05-27)
Phase 1.6 — Frontend BFF 전환                         ✅ 완료 (2026-05-28)
Phase 1.7 — Tag & History                             ✅ 완료 (2026-05-28)
Phase 1.8 — Tag UI                                    ✅ 완료 (2026-05-28)
Phase 2   — 인증 시스템 (JWT, API Key, 프로젝트 권한)  ✅ 완료 (2026-05-29)
Phase 2   — 운영 준비 (보안·감사로그·백업·모니터링)    ✅ 완료 (2026-05-29)
Phase 2.3 — 관리자 콘솔 UI & 인증 고급                ✅ 완료 (2026-05-29)
Phase 3   — 확장 기능 (pgvector, Revision, Export)    ✅ 완료 (2026-05-30)
Phase 3.1 — API Key 관리 UI (사용자 + 관리자 화면)    ✅ 완료 (2026-05-31)
Phase 3.2 — API Key 프로젝트 접근 제어 강화            ✅ 완료 (2026-05-31)
Phase 3.3 — Project ID 특수문자 제한 (_만 허용)        ✅ 완료 (2026-05-31)
Phase 3.4 — Entity 배치 저장 & 참조 패턴               ✅ 완료 (2026-05-31)
```

---

## 완료된 지침 요약

> 최근 3건만 표시. 전체 이력은 `instructions/instructions.log` 참고.

| 완료일 | UUID | 제목 |
|--------|------|------|
| 2026-05-31 | 4d7b7053-162b-4e15-99cc-d6700354008f | Project ID 특수문자 제한 — 언더바(_)만 허용 |
| 2026-05-31 | d679e0e0-ed7e-4de0-ba3d-554a83d3601c | API Key 프로젝트 기반 발급 및 접근 제어 강화 |
| 2026-05-31 | 498fd32d-b55b-4e14-9e6b-cdfa4639b6b0 | Entity 배치 저장 및 참조 패턴 확장 (320 passed) |

---

## Phase 3 — 확장 기능 ✅ 완료 (2026-05-30)

**목표**: 검색 고도화, 이력 추적, 외부 연동

| 순서 | UUID | 지침 파일 | 상태 |
|------|------|-----------|------|
| 3 | 03080220 | .completed/03080220-3b52-4d28-a79d-e2d698e5480f.md | `completed` 2026-05-30 |

### 완료 범위

```
3-1   pgvector semantic search    ✅ context_embedding + HNSW 인덱스 + MCP 연동
3-2   entity_revision             ✅ entity_history 테이블 + 비교 API
3-3   Review UI                   ✅ alias 비활성화 + deprecated 처리 모달
3-4   AGENTS.md export            ✅ GET /export/agents-md — 에이전트용 컨텍스트 내보내기
3-5   GitHub PR 검증              ✅ POST /validate-references + CI workflow + validate-pr-refs.py
3-6   OpenAPI export              ✅ GET /export/openapi — JSON/YAML 형식 지원
```

---

## 지침 파일 현황

> 최근 4건 표시. 전체 이력은 `instructions/instructions.log` 참고.

| UUID | 파일 | 분류 | 상태 |
|------|------|------|------|
| d679e0e0 | .completed/ | Phase 3.2 | `completed` 2026-05-31 |
| 4d7b7053 | .completed/ | Phase 3.3 | `completed` 2026-05-31 |
| 498fd32d | .completed/ | Phase 3.4 | `completed` 2026-05-31 |

> 완료된 지침 세부 내용은 `instructions/.completed/{uuid}.md`에 보관.

---

## 미정 / 백로그

아직 지침 파일로 확정하지 않은 항목.

| 항목 | 설명 | 처리 방향 |
|------|------|-----------|
| 화면설계 엔티티 목업 서비스 | UI_AREA 엔티티용 목업 서비스 제공 | 화면설계 도메인 범위 확정 후 지침화 |
| 업로드 시 엔티티 식별자 즉시 반환 | `POST /ingest/batch` 응답에 entity id·alias 매핑 포함 | Ingest API 응답 스키마 확장 지침으로 승격 |
| 짧은 식별자 반환 | UUID 외 `프로젝트ID-type-ID` 형태 식별자 생성·반환 | 프로젝트 ID 정책 지침으로 승격 |
