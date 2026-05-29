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
Phase 1   — MVP 구현                                  ✅ 완료 (2026-05-25)
Phase 1.5 — Entity 목록 API                           ✅ 완료 (2026-05-27)
Phase 1.6 — Frontend BFF 전환                         ✅ 완료 (2026-05-28)
Phase 1.7 — Tag & History                             ✅ 완료 (2026-05-28)
Phase 1.8 — Tag UI                                    ✅ 완료 (2026-05-28)
Phase 2   — 인증 시스템 (JWT, API Key, 프로젝트 권한)  ✅ 완료 (2026-05-29)
Phase 2   — 운영 준비 (보안·감사로그·백업·모니터링)    ✅ 완료 (2026-05-29)
Phase 2.3 — 관리자 콘솔 UI & 인증 고급                ✅ 완료 (2026-05-29)
Phase 3   — 확장 기능 (pgvector, Revision, Export)    ← 다음
```

---

## 완료된 지침 요약

> 최근 3건만 표시. 전체 이력은 `instructions/instructions.log` 참고.

| 완료일 | UUID | 제목 |
|--------|------|------|
| 2026-05-29 | 0ac0d3e0-f558-4b6a-9aed-3b09ad1e953e | 관리자 콘솔 UI — 로그인·사용자·프로젝트·멤버 관리 화면 |
| 2026-05-29 | 1285a04e-652a-4b95-a3a9-160dfc897ef2 | 인증 시스템 3 — 관리자·프로젝트 관리자 기능 |
| 2026-05-29 | ce6d92bf-2c2d-4944-adb3-1089a6530e56 | 운영 준비 — 보안 & 모니터링 |

---

## Phase 3 — 확장 기능 (진행 예정)

**목표**: 검색 고도화, 이력 추적, 외부 연동

| 순서 | UUID | 지침 파일 | 상태 |
|------|------|-----------|------|
| 3 | 03080220 | extensions.md | `pending` |

### 포함 범위 (`docs/08` 기반)

```
3-1   pgvector semantic search    context_embedding 테이블 + 벡터 검색
3-2   entity_revision             변경 이력 추적 테이블
3-3   Review UI                   entity/alias/context 검토 화면
3-4   AGENTS.md export            에이전트용 context 내보내기
3-5   GitHub PR 검증              PR 내 entity 참조 유효성 자동 확인
3-6   OpenAPI export              레지스트리 스펙 내보내기
```

전제조건: Phase 2 완료 ✅ (이미 충족)

---

## 지침 파일 현황

> 완료 지침은 최근 3건만 표시. 전체 이력은 `instructions/instructions.log` 참고.

| UUID | 파일 | Phase | 상태 |
|------|------|-------|------|
| 03080220 | extensions.md | 3 | `pending` |
| 0ac0d3e0 | .completed/ | 2.3a | `completed` 2026-05-29 |
| 1285a04e | .completed/ | 2.3b | `completed` 2026-05-29 |
| ce6d92bf | .completed/ | 2 | `completed` 2026-05-29 |

> 완료된 지침 세부 내용은 `instructions/.completed/{uuid}.md`에 보관.

---

## 미정 / 백로그

아직 지침 파일로 확정하지 않은 항목.

| 항목 | 설명 | 처리 방향 |
|------|------|-----------|
| 화면설계 엔티티 목업 서비스 | UI_AREA 엔티티용 목업 서비스 제공 | 화면설계 도메인 범위 확정 후 지침화 |
| 업로드 시 엔티티 식별자 즉시 반환 | `POST /ingest/batch` 응답에 entity id·alias 매핑 포함 | Ingest API 응답 스키마 확장 지침으로 승격 |
| 짧은 식별자 반환 | UUID 외 `프로젝트ID-type-ID` 형태 식별자 생성·반환 | 프로젝트 ID 정책 지침으로 승격 |
