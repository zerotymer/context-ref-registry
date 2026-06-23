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
Phase 3.5 — Entity 프로젝트 필터 + 번들 그래프 뷰      ✅ 완료 (2026-06-02)
Phase 3.6 — 컨테이너 startup DB 스키마 자동 적용       ✅ 완료 (2026-06-03)
Phase 3.7 — 에이전트 API 게이트웨이 (Next BFF /api/v1) ✅ 완료 (2026-06-03)
```

---

## 완료된 지침 요약

> 최근 3건만 표시. 전체 이력은 `instructions/instructions.log` 참고.

| 완료일 | UUID | 제목 |
|--------|------|------|
| 2026-06-02 | 612ab97e-df2b-4d1b-98ed-f3a928665606 | Entity 프로젝트 필터 + 번들 그래프 뷰 |
| 2026-06-03 | d494a542-0049-44a7-913d-398926dbc857 | 컨테이너 startup DB 스키마 자동 적용 (alembic upgrade head) |
| 2026-06-03 | 2214f2c4-30a9-4555-bd24-073a841cadc3 | 에이전트 API 게이트웨이 (Next BFF `/api/v1/*` 프록시, 프론트 16 passed) |

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
| d494a542 | .completed/ | Phase 3.6 | `completed` 2026-06-03 |
| 2214f2c4 | .completed/ | Phase 3.7 | `completed` 2026-06-03 |
| 216b0864 | .completed/ | MCP HTTP | `completed` 2026-06-06 — 단계 A(백엔드 `/mcp`) + 단계 C(Next BFF `/api/v1/mcp` 스트리밍 프록시) |

> 완료된 지침 세부 내용은 `instructions/.completed/{uuid}.md`에 보관.

---

## 미정 / 백로그

아직 지침 파일로 확정하지 않은 항목.

| 항목 | 설명 | 처리 방향 |
|------|------|-----------|
| _(없음)_ | 기존 백로그 3건 모두 지침화 (아래) | — |

### 지침화된 백로그 (구현 대기, `status: pending`)

| UUID | 지침 파일 | 내용 |
|------|-----------|------|
| 71f9e0d0-7257-408b-b412-eef4e1e8e521 | `ingest-batch-return-identifiers.md` | `POST /ingest/batch` 응답에 entity id·alias 매핑 반환 |
| ad25787d-4392-4d35-9751-ba050ae7cf9e | `short-identifier-scheme.md` | 짧은 식별자 `PROJECT_ID-TYPE-N` 생성 + 4번째 참조 패턴 등록 |

> ~~c5e60dba — UI_AREA 목업 HTML 자동 생성~~ → **completed (2026-06-23)**, `.completed/`로 이동.
