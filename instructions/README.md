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
Phase 1 — MVP 구현              ✅ 완료 (2026-05-25)
Phase 1.5 — Entity 목록 API      ✅ 완료 (2026-05-27)
Phase 2 — 운영 준비 (Post-MVP)  ← 다음
Phase 3 — 확장 기능 (Future)    ← 운영 후 필요 시
```

---

## 완료된 지침 요약

완료된 지침의 세부 작업 목록은 `instructions/.completed/`에 보관한다.
이 README에는 다음 작업 판단에 필요한 요약만 유지한다.

| 완료일 | UUID | 제목 | 결과 |
|--------|------|------|------|
| 2026-05-25 | 240e1460-a7e6-4b0e-a08f-10f9c74c497c | MVP 구현 계획 | FastAPI/API, DB schema, ingest, context bundle, MCP, 테스트 구현 완료 |
| 2026-05-27 | c6794b7d-f36b-4697-b6ee-77a978615456 | Entity 목록 조회 API — `GET /entities` | status/type 필터, 페이지네이션, total count, 정렬, 테스트 구현 완료 |

### MVP 완료 기준 잔여 확인

MVP 구현 지침은 완료 처리되었지만, 아래 환경 검증만 별도 확인 항목으로 남긴다.

- [ ] `docker compose up` → API + DB 정상 기동 확인

---

## Phase 2 — 운영 준비 (Post-MVP)

**목표**: 인증 추가, 감사 로그, 백업, 모니터링

| 순서 | UUID | 지침 파일 | 상태 |
|------|------|-----------|------|
| 2 | ce6d92bf | security_ops.md | `draft` |

### 포함 범위 (`docs/09` 기반)

```
2-1   API Key 인증          write 엔드포인트 헤더 검증, scope 분리
2-2   Audit Log             entity create/update/status 변경 이력 기록
2-3   Backup                pg_dump daily, docker volume backup
2-4   Observability         요청 수, 레이턴시, ambiguous 비율, MCP call 수
```

---

## Phase 3 — 확장 기능 (Future)

**목표**: 검색 고도화, 이력 추적, 외부 연동

| 순서 | UUID | 지침 파일 | 상태 |
|------|------|-----------|------|
| 3 | 03080220 | extensions.md | `draft` |

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

| UUID | 파일 | Phase | 상태 |
|------|------|-------|------|
| 240e1460-a7e6-4b0e-a08f-10f9c74c497c | .completed/ | 1 | `completed` 2026-05-25 |
| c6794b7d-f36b-4697-b6ee-77a978615456 | .completed/ | 1.5 | `completed` 2026-05-27 |
| ce6d92bf-2c2d-4944-adb3-1089a6530e56 | security_ops.md | 2 | `draft` |
| 03080220-3b52-4d28-a79d-e2d698e5480f | extensions.md | 3 | `draft` |
| 6cd788d7-9200-41e2-bda9-06c7b96d5de7 | review_ui.md | 3 | `pending` |

> 완료된 지침은 `instructions/.completed/{uuid}.md`에 보관.
> 전체 이력은 `instructions/instructions.log` 참고.

---

## 미정 / 백로그

아직 별도 지침 파일로 확정하지 않았거나, 구현 범위가 더 구체화되어야 하는 항목.
구현 단위가 확정되면 UUID를 발급하고 `instructions/{slug}.md`로 승격한다.

| 항목 | 설명 | 처리 방향 |
|------|------|-----------|
| 인증시스템 구현 | API Key 인증을 시작점으로 write/admin 엔드포인트 보호, scope 정책, actor 식별 방식을 확정한다. | Phase 2 `security_ops.md` Step 2-1로 구체화 |
| 프로젝트 별 그룹화 | entity/context/relation을 프로젝트 단위로 묶어 조회·관리할 수 있게 한다. 프로젝트 식별자, 필터 기준, UI 그룹 표시 방식을 정의한다. | 관리자 시스템 설계 시 함께 구체화 |
| 관리자 시스템 구현 | candidate 검토, active 승인, archive/deprecated 처리, alias/context 관리가 가능한 관리자 화면을 구현한다. | `review_ui.md` 기반으로 진행 |
| README 최신화 | 신규 지침 생성 시 README의 로드맵/현황 표를 함께 갱신한다. | 지침 관리 규칙에 포함 |
| docker compose 검증 | Phase 1 완료 기준 중 `docker compose up` API + DB 기동 확인이 아직 미체크다. | 환경 실행 후 완료 체크 |
