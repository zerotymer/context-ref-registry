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
Phase 2 — 운영 준비 (Post-MVP)  ← 다음
Phase 3 — 확장 기능 (Future)    ← 운영 후 필요 시
```

---

## Phase 1 — MVP 구현 ✅

**목표**: `docker compose up` + `pytest` 통과 + MCP tool 동작

| 순서 | UUID | 지침 파일 | 상태 |
|------|------|-----------|------|
| 1 | 240e1460 | .completed/240e1460-a7e6-4b0e-a08f-10f9c74c497c.md | `completed` |

### Step 완료 이력

```
Step 0   프로젝트 초기화        ✅
Step 1   DB Schema 작성         ✅
Step 2   Domain 정의            ✅
Step 3   Entity CRUD            ✅
Step 4   Alias API              ✅
Step 5   Context API            ✅
Step 6   Relation API           ✅
Step 7   Batch Ingest           ✅
Step 8   Context Bundle         ✅
Step 9   MCP Server             ✅
Step 10  테스트 작성             ✅
```

**완료 기준** (`docs/11` 기준):

- [x] `POST /ingest/batch` sample 성공
- [x] `GET /resolve` ambiguous case 동작
- [x] `POST /context-bundle` JSON 반환
- [x] MCP `get_context_bundle` 호출 성공
- [x] `pytest` 전체 통과 (100 passed)
- [ ] `docker compose up` → API + DB 정상 기동 (환경 실행 필요)

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
| ce6d92bf-2c2d-4944-adb3-1089a6530e56 | security_ops.md | 2 | `draft` |
| 03080220-3b52-4d28-a79d-e2d698e5480f | extensions.md | 3 | `draft` |

> 완료된 지침은 `instructions/.completed/{uuid}.md`에 보관.
> 전체 이력은 `instructions/instructions.log` 참고.
