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
Phase 3.8 — MCP HTTP transport (단계 A+C)            ✅ 완료 (2026-06-06)
Phase 3.9 — 목업 HTML·Ingest 식별자·짧은 식별자      ✅ 완료 (2026-06-23)
Phase 4.0 — Bundle 탐색기 Graph 탭 (AntV G6)         ✅ 완료 (2026-07-22, 지침 없이 PR #15·#16)
Phase 4.1 — SQLite 전환·경량화·단일 관리자 인증       ✅ 완료 (2026-11-11, v2.0.0)
Phase 3-1 — pgvector semantic search                 ✖ 폐기 (sqlite-vec 기준 재설계 예정)
```

---

## 완료된 지침 요약

> 최근 3건만 표시. 전체 이력은 `instructions/instructions.log` 참고.

| 완료일 | UUID | 제목 |
|--------|------|------|
| 2026-11-11 | 8607659b-324e-4cea-8bea-be2a9c51aa34 | PostgreSQL → SQLite 전환, 배포 경량화, 단일 관리자 + 프로젝트 키 인증 (v2.0.0) |
| 2026-06-23 | c5e60dba-cfc6-4dac-9db3-d0e9f4657001 | UI_AREA `metadata.mockup` → 목업 HTML 자동 생성 `GET /entities/{id}/mockup` |
| 2026-06-23 | 71f9e0d0-7257-408b-b412-eef4e1e8e521 | `/ingest/batch` 응답 `entities[]`에 entity id·operation·alias 매핑 반환 |

---

## Phase 3 — 확장 기능 ✅ 완료 (2026-05-30, pgvector 제외)

**목표**: 검색 고도화, 이력 추적, 외부 연동

| 순서 | UUID | 지침 파일 | 상태 |
|------|------|-----------|------|
| 3 | 03080220 | .completed/03080220-3b52-4d28-a79d-e2d698e5480f.md | `completed` 2026-05-30 |

### 완료 범위

```
3-1   pgvector semantic search    ⏸ 미머지 — feat/ext-pgvector 브랜치에만 존재 (지침 체크박스도 미완)
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
| 8607659b | .completed/ | SQLite·경량화·인증 | `completed` 2026-11-11 — PostgreSQL → SQLite, 컨테이너 2개, 단일 관리자 + 프로젝트 키 (v2.0.0) |
| c5e60dba | .completed/ | UI_AREA 목업 | `completed` 2026-06-23 — `GET /entities/{id}/mockup` |
| 71f9e0d0 | .completed/ | Ingest 식별자 | `completed` 2026-06-23 — `/ingest/batch` 응답 `entities[]` 매핑 |
| ad25787d | .completed/ | 짧은 식별자 | `completed` 2026-06-23 — `PROJECT_ID-TYPE-N` 4번째 참조 패턴 |

> 완료된 지침 세부 내용은 `instructions/.completed/{uuid}.md`에 보관.

---

## 미정 / 백로그

아직 지침 파일로 확정하지 않은 항목.

| 항목 | 설명 | 처리 방향 |
|------|------|-----------|
| ~~pgvector semantic search (3-1)~~ | SQLite 전환(8607659b)으로 `feat/ext-pgvector` 폐기 | 필요해지면 sqlite-vec 기준으로 새 지침 작성 |
| Bundle Graph 탭 지침 누락 | PR #15·#16이 지침 파일 없이 머지됨 | 사후 기록만 (README 로드맵 반영 완료) |
| ~~오래된 로컬/원격 브랜치 정리~~ | 2026-11-09 완료 — 로컬 23개 삭제(내용 main 반영 확인), 원격은 이미 `main`만 존재. `feat/ext-pgvector`는 **로컬에만** 보존 | 완료 |
| code symbol analyzer / source permission sync | `docs/08` '추후 확장' 항목, 미착수 | 수요 생기면 지침화 |

> ~~c5e60dba — UI_AREA 목업 HTML 자동 생성~~ → **completed (2026-06-23)**, `.completed/`로 이동.
> ~~71f9e0d0 — Ingest 식별자 반환~~ → **completed (2026-06-23)**, `.completed/`로 이동.
> ~~ad25787d — 짧은 식별자 `PROJECT_ID-TYPE-N`~~ → **completed (2026-06-23)**, `.completed/`로 이동.
