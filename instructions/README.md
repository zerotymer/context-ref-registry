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

---

## 전체 구현 로드맵

```
Phase 1   — MVP 구현                        ✅ 완료 (2026-05-25)
Phase 1.5 — Entity 목록 API                 ✅ 완료 (2026-05-27)
Phase 1.6 — Frontend BFF 전환               ✅ 완료 (2026-05-28)
Phase 1.7 — Tag & History                   ✅ 완료 (2026-05-28)
Phase 1.8 — Tag UI                          ✅ 완료 (2026-05-28)
Phase 2   — 인증 시스템 (JWT, API Key, 프로젝트 권한)  ✅ 완료 (2026-05-29)
Phase 2   — 운영 준비 (보안·감사로그·백업·모니터링)    ✅ 완료 (2026-05-29)
Phase 2.3 — 관리자 콘솔 & 인증 고급             ← 진행 중
Phase 3   — 확장 기능 (Future)               ← 운영 후 필요 시
```

---

## 완료된 지침 요약

> 최근 3건만 표시. 전체 이력은 `instructions/instructions.log` 참고.

세부 작업 목록은 `instructions/.completed/{uuid}.md`에 보관한다.

| 완료일 | UUID | 제목 |
|--------|------|------|
| 2026-05-29 | ce6d92bf-2c2d-4944-adb3-1089a6530e56 | 운영 준비 — 보안 & 모니터링 (API Key·Audit Log·Backup·Observability) |
| 2026-05-29 | 8c36e2c4-4273-472d-964e-7febf9d2428e | 인증 시스템 2 — 프로젝트, 멤버십, 조회·수정 권한 |
| 2026-05-29 | 1a2a9bf8-c772-4d6e-8bb9-469bb211e8c8 | 인증 시스템 1 — 사용자 계정, 로그인, API Key 병행 |

---

## Phase 2.3 — 관리자 콘솔 & 인증 고급 (진행 중)

**목표**: 관리자 운영 화면 구현 및 프로젝트 관리자 역할 기능 추가

| 순서 | UUID | 지침 파일 | 상태 |
|------|------|-----------|------|
| 2.3a | 0ac0d3e0 | admin_console_ui.md | `pending` |
| 2.3b | 1285a04e | admin_project_console.md | `pending` |

### 포함 범위

```
2.3a  관리자 콘솔 UI    로그인·사용자·프로젝트·멤버 관리 화면 (Next.js)
2.3b  인증 고급        관리자/프로젝트 관리자 기능, 권한 강화
```

---

## Phase 2 — 완료된 지침

| UUID | 제목 | 완료일 |
|------|------|--------|
| ce6d92bf | 운영 준비 (보안·Audit Log·Backup·Observability) | 2026-05-29 |
| 8c36e2c4 | 인증 시스템 2 — 프로젝트, 멤버십, 접근 권한 | 2026-05-29 |
| 1a2a9bf8 | 인증 시스템 1 — 사용자 계정, 로그인, API Key | 2026-05-29 |

### 운영 준비 완료 항목 (ce6d92bf)

```
2-1   API Key 인증          write 엔드포인트 헤더 검증, scope 분리    ✅
2-2   Audit Log             entity/alias/context/relation/batch 이력    ✅
2-3   Backup                pg_dump daily, docker volume backup         ✅
2-4   Observability         structlog JSON, /health, Docker healthcheck  ✅
```

---

## Phase 3 — 확장 기능 (Future)

**목표**: 검색 고도화, 이력 추적, 외부 연동

| 순서 | UUID | 지침 파일 | 상태 |
|------|------|-----------|------|
| 3 | 03080220 | extensions.md | `pending` |

### 포함 범위 (`docs/08` 추후 확장 기반)

```
3-1   pgvector semantic search    context_embedding 테이블 + 벡터 검색
3-2   entity_revision             변경 이력 추적 테이블
3-3   Review UI                   entity/alias/context 검토 화면
3-4   AGENTS.md export            에이전트용 context 내보내기
3-5   GitHub PR 검증              PR 내 entity 참조 유효성 자동 확인
3-6   OpenAPI export              레지스트리 스펙 내보내기
```

---

## 지침 파일 현황

> 완료 지침은 최근 3건만 표시. 전체 이력은 `instructions/instructions.log` 참고.

| UUID | 파일 | Phase | 상태 |
|------|------|-------|------|
| 0ac0d3e0 | admin_console_ui.md | 2.3a | `pending` |
| 1285a04e | admin_project_console.md | 2.3b | `pending` |
| 03080220 | extensions.md | 3 | `pending` |
| ce6d92bf | .completed/ | 2 | `completed` 2026-05-29 |
| 8c36e2c4 | .completed/ | 2.2 | `completed` 2026-05-29 |
| 1a2a9bf8 | .completed/ | 2.1 | `completed` 2026-05-29 |

> 완료된 지침 세부 내용은 `instructions/.completed/{uuid}.md`에 보관.

---

## 미정 / 백로그

아직 별도 지침 파일로 확정하지 않았거나, 구현 범위가 더 구체화되어야 하는 항목.

| 항목 | 설명 | 처리 방향 |
|------|------|-----------|
| 화면설계 엔티티 목업 서비스 | UI_AREA 엔티티를 위한 목업 서비스 제공 | 화면설계 도메인 범위 확정 후 지침화 |
| 화면설계 하위 식별자 목업 서비스 | 자동 하위 식별자 포함 목업 서비스 | `UI_AREA` 식별 체계와 함께 구체화 |
| 업로드 시 엔티티 식별자 즉시 반환 | `POST /ingest/batch` 응답에 entity id·alias·context 매핑 포함 | Ingest API 응답 스키마 확장 지침으로 승격 |
| 짧은 식별자 반환 | UUID 외 `프로젝트ID-type-ID` 형태 짧은 식별자 생성·반환 | 프로젝트 ID 정책 지침으로 승격 |
