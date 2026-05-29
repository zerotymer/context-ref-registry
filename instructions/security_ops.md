---
uuid: ce6d92bf-2c2d-4944-adb3-1089a6530e56
title: 운영 준비 — 보안 & 모니터링
status: in-progress
created: 2026-05-25
completed:
ref_docs:
  - docs/09-security-and-ops.md
prerequisite: 240e1460-a7e6-4b0e-a08f-10f9c74c497c (Phase 1 MVP 완료 후 시작)
---

# 운영 준비 — 보안 & 모니터링

> **이 지침은 Phase 1 MVP 완료 후 진행한다.**
> 미결 사항이 있으므로 Phase 1 완료 시점에 구체화한다.

---

## Step 2-1. API Key 인증

**브랜치**: `feat/step2-2-access-policy`
**상태**: `[x]` completed

### 작업 목록

- [x] `X-API-Key` 헤더 기반 인증 미들웨어 구현
- [x] write 엔드포인트 보호 (`POST /entities`, `POST /ingest/batch` 등)
- [x] read 엔드포인트는 인증 없이 허용
- [x] MCP server는 기본 read-only 유지 (추가 인증 불필요)
- [x] API key DB 관리 (env 대신 DB 기반으로 구현 — 더 완전한 방식)
- [x] 인증 실패 시 표준 에러 응답: `{"ok": false, "error": {"code": "UNAUTHORIZED"}}`

### scope 구분 (운영 단계)

```
read    → GET 전체 + MCP
ingest  → POST /ingest/batch
write   → POST/PATCH /entities 등
admin   → status 변경, entity 삭제 등
```

**완료 조건**

- `X-API-Key` 없이 write → 401 ✅
- 올바른 key → 정상 동작 ✅
- MCP read-only tool → 인증 없이 동작 ✅

**완료일**: 2026-05-29

---

## Step 2-2. Audit Log

**브랜치**: `feat/security-audit-log`
**상태**: `[x]` completed

### 기록 대상 (`docs/09` 기준)

```
entity create / update / status 변경
alias add / deactivate
context add / update
relation create / delete
batch ingest (성공/실패)
```

### Audit Log 필드

```
id, actor, action, target_type, target_id,
before_snapshot (JSONB), after_snapshot (JSONB), created_at
```

### 작업 목록

- [x] `entity_audit_log` 테이블 Alembic migration
- [x] `AuditService` 구현 — 서비스 레이어에서 자동 기록
- [x] actor: MVP에서는 API key 식별자 또는 `"system"` 고정
- [x] before/after snapshot은 핵심 필드만 포함 (context body 전체 제외)

### 로그에 기록하지 않는 것

```
secret 값, 인증 토큰, context body 전체 (길이 초과 시)
```

**완료일**: 2026-05-29

---

## Step 2-3. Backup

**브랜치**: `feat/ops-backup`
**상태**: `[x]` completed

### MVP 백업 구성

- [x] `docker-compose.yml`에 backup 서비스 추가 또는 cron script 작성
- [x] `pg_dump` daily 스크립트
- [x] 백업 파일 보관 경로 정의 (로컬 볼륨 — `backup_data` Docker named volume)

**완료일**: 2026-05-29

---

## Step 2-4. Observability

**브랜치**: `feat/ops-observability`
**상태**: `[ ]` pending

### 기본 메트릭 (`docs/09` 기준)

```
API 요청 수 / 레이턴시
alias ambiguous 비율
not_found 비율
context_bundle 레이턴시
MCP tool call 수
batch ingest 성공/실패 수
```

### 작업 목록

- [ ] FastAPI middleware로 요청 로깅 (request_id, endpoint, result_status, latency_ms)
- [ ] structlog으로 JSON 구조화 로그 출력
- [ ] `GET /health` 엔드포인트 (DB 연결 상태 포함)
- [ ] Docker Compose `healthcheck` 설정 (api, postgres)

> Prometheus / Grafana는 **MVP 제외**. 필요 시 Phase 3에서 추가.

**완료일**: —

---

## 확정 사항

| 항목 | 결정 |
|------|------|
| minio | Phase 2에서도 제외. source_ref URI 기록만 유지. |
| Observability | 구조화 로그(structlog) + /health 엔드포인트만. Prometheus 제외. |

## 미결 사항

- [ ] **actor 식별**: Audit Log에서 actor를 API key 식별자로 할 것인가? 아니면 별도 사용자 개념?
- [ ] **Step 2-3 Backup**: pg_dump 주기/보관 위치 확정 (Phase 2 시작 시점에 결정)
