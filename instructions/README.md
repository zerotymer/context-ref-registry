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
Phase 1   — MVP 구현              ✅ 완료 (2026-05-25)
Phase 1.5 — Entity 목록 API       ✅ 완료 (2026-05-27)
Phase 1.6 — Frontend BFF 전환     ✅ 완료 (2026-05-28)
Phase 1.7 — Tag & History         ✅ 완료 (2026-05-28)
Phase 1.8 — Tag UI                ✅ 완료 (2026-05-28)
Phase 2   — 운영 준비 (Post-MVP)  ← 다음
Phase 2.1 — 인증/프로젝트 권한     ← 설계 지침 작성
Phase 3   — 확장 기능 (Future)    ← 운영 후 필요 시
```

---

## 완료된 지침 요약

> 최근 3건만 표시. 전체 이력은 `instructions/instructions.log` 참고.

세부 작업 목록은 `instructions/.completed/{uuid}.md`에 보관한다.

| 완료일 | UUID | 제목 |
|--------|------|------|
| 2026-05-28 | 36ab4117-e0cc-4a30-813e-129f0835b540 | Tag & History — Entity 태그 다중 부착 + 변경 이력 관리 |
| 2026-05-28 | 5fa5df8b-61e9-4da7-86d5-9802e748c405 | Frontend BFF — Server Actions + Server Components 전환 |
| 2026-05-28 | 7f798d9a-780a-427a-90e5-49fb8ad17139 | Tag UI — Entity 태그 관리 화면 구현 |

---

## Phase 2 — 운영 준비 (Post-MVP)

**목표**: 인증 추가, 프로젝트 권한, 감사 로그, 백업, 모니터링

| 순서 | UUID | 지침 파일 | 상태 |
|------|------|-----------|------|
| 2 | ce6d92bf | security_ops.md | `draft` |
| 2.1 | 1a2a9bf8 | auth_identity.md | `draft` |
| 2.2 | 8c36e2c4 | project_access_control.md | `draft` |
| 2.3 | 1285a04e | admin_project_console.md | `draft` |

### 포함 범위 (`docs/09` 기반)

```
2-1   API Key 인증          write 엔드포인트 헤더 검증, scope 분리
2-2   Audit Log             entity create/update/status 변경 이력 기록
2-3   Backup                pg_dump daily, docker volume backup
2-4   Observability         요청 수, 레이턴시, ambiguous 비율, MCP call 수
```

### 인증/프로젝트 권한 분할 지침

```
2.1   사용자 인증           관리자 발급 계정, 이메일/비밀번호 로그인, API Key 병행
2.2   프로젝트 권한         project_id, 프로젝트 멤버십, 조회/수정 권한 정책
2.3   관리자 기능           사용자/프로젝트/팀원/API Key 운영 화면과 감사 로그
```

### Registry 등록 범위

```
문서 루트 엔티티 3개
세부 엔티티 24개: FEATURE 10, API 2, UI_AREA 5, INFRA_UNIT 4, CODE_SYMBOL 3
관계 35개: 문서→세부 CONTAINS 및 세부 기능 간 DEPENDS_ON/USES/IMPLEMENTED_BY
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

> 완료 지침은 최근 3건만 표시. 전체 이력은 `instructions/instructions.log` 참고.

| UUID | 파일 | Phase | 상태 | Registry Entity |
|------|------|-------|------|-----------------|
| ce6d92bf-2c2d-4944-adb3-1089a6530e56 | security_ops.md | 2 | `pending` | — |
| 1a2a9bf8-c772-4d6e-8bb9-469bb211e8c8 | auth_identity.md | 2.1 | `pending` | eb3bb01a-a210-4420-aed2-52c4f729819e |
| 8c36e2c4-4273-472d-964e-7febf9d2428e | project_access_control.md | 2.2 | `pending` | f16f5245-658e-4202-9f7b-60755e2090d0 |
| 1285a04e-652a-4b95-a3a9-160dfc897ef2 | admin_project_console.md | 2.3 | `pending` | 775c9218-05eb-4cd0-969a-212d673835d7 |
| 03080220-3b52-4d28-a79d-e2d698e5480f | extensions.md | 3 | `pending` | — |
| 36ab4117-e0cc-4a30-813e-129f0835b540 | .completed/ | 1.7 | `completed` 2026-05-28 |
| 5fa5df8b-61e9-4da7-86d5-9802e748c405 | .completed/ | 1.6 | `completed` 2026-05-28 |
| 7f798d9a-780a-427a-90e5-49fb8ad17139 | .completed/ | 1.8 | `completed` 2026-05-28 |

> 완료된 지침 세부 내용은 `instructions/.completed/{uuid}.md`에 보관.

---

## 미정 / 백로그

아직 별도 지침 파일로 확정하지 않았거나, 구현 범위가 더 구체화되어야 하는 항목.
구현 단위가 확정되면 UUID를 발급하고 `instructions/{slug}.md`로 승격한다.

| 항목 | 설명 | 처리 방향 |
|------|------|-----------|
| 인증시스템 구현 | 관리자 발급 계정, 이메일/비밀번호 로그인, API Key 병행, actor 식별 방식을 정의한다. | `auth_identity.md`로 승격 |
| 프로젝트 별 그룹화 | entity/context/relation을 프로젝트 단위로 묶고, project_id 기반 조회·수정 권한을 정의한다. | `project_access_control.md`로 승격 |
| 관리자 시스템 구현 | 사용자/프로젝트/팀원/API Key 운영 및 프로젝트 관리자 기능을 구현한다. | `admin_project_console.md`로 승격 |
| 화면설계 엔티티 목업 서비스 | 화면설계 엔티티(`UI_AREA`)를 위한 목업 서비스를 제공한다. | 화면설계 도메인 범위 확정 후 지침화 |
| 화면설계 하위 식별자 목업 서비스 | 화면설계를 위한 자동 하위 식별자를 포함한 목업 서비스를 제공한다. | `UI_AREA` 식별 체계와 함께 구체화 |
| 업로드 시 엔티티 식별자 즉시 반환 | `POST /ingest/batch` 결과에 생성/업데이트된 entity id 목록과 alias/context/relation 매핑을 포함해, 별도 검색 없이 업로드 직후 문서 매핑이 가능하게 한다. | Ingest API 응답 스키마 확장 지침으로 승격 |
| README 최신화 | 신규 지침 생성 시 README의 로드맵/현황 표를 함께 갱신한다. | 지침 관리 규칙에 포함 |
