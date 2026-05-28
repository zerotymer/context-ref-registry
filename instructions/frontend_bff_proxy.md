---
uuid: 5fa5df8b-61e9-4da7-86d5-9802e748c405
title: Frontend BFF Proxy — Next.js를 통한 Backend API 호출 구조 전환
status: pending
created: 2026-05-28
completed:
ref_docs:
  - README.md
  - docs/00-architecture.md
  - frontend/src/lib/api/client.ts
  - docker-compose.yml
prerequisite: Review UI 구현 완료 (6cd788d7)
---

# Frontend BFF Proxy — Next.js를 통한 Backend API 호출 구조 전환

> **목적**: 브라우저에서 FastAPI backend(`:8000`)를 직접 호출하는 구조를 제거하고,
> Next.js frontend 내부 BFF/API route를 경유해 backend를 호출하도록 전환한다.

---

## 현재 문제

현재 frontend API client는 다음 구조를 사용한다.

```ts
const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";
fetch(`${API_BASE}${path}`)
```

이 구조는 브라우저 번들에 backend endpoint가 노출되고, 환경별 CORS/네트워크 경계가 frontend 코드에 직접 반영된다.
Docker Compose에서도 `NEXT_PUBLIC_API_URL=http://api:8000`이 frontend에 주입되어 브라우저 실행 위치와 container network 위치가 섞일 수 있다.

---

## 목표 구조

```text
Browser
  -> Next.js frontend origin
  -> Next.js BFF route handler (/api/backend/* 또는 /api/*)
  -> FastAPI backend (:8000, internal service URL)
```

### 원칙

- 브라우저 코드는 상대 경로만 호출한다.
- backend 내부 URL은 server-only 환경 변수로만 관리한다.
- `NEXT_PUBLIC_*` 변수에는 backend origin을 넣지 않는다.
- FastAPI response envelope(`{ ok, data, error }`)는 그대로 유지한다.
- BFF는 인증/쿠키/헤더 전달 정책을 수용할 수 있는 얇은 proxy 계층으로 시작한다.

---

## Step 1. Next.js BFF Route 추가

**브랜치**: `feat/frontend-bff-proxy`

### 파일

```text
frontend/src/app/api/backend/[...path]/route.ts
```

### 요구사항

- `GET`, `POST`, `PATCH`, `PUT`, `DELETE` 메서드를 지원한다.
- backend base URL은 `BACKEND_API_URL`에서 읽는다.
- 기본값은 로컬 개발용 `http://localhost:8000`으로 둔다.
- 요청 path와 query string을 backend로 그대로 전달한다.
- JSON body가 있는 요청은 body를 그대로 전달한다.
- backend 응답 status와 body를 가능한 그대로 반환한다.
- `content-type: application/json`을 기본으로 유지하되, 향후 파일/stream 응답 확장을 막지 않도록 구현을 단순 proxy 형태로 둔다.

### 예시 동작

```text
GET  /api/backend/entities?status=active
  -> GET  {BACKEND_API_URL}/entities?status=active

POST /api/backend/entities
  -> POST {BACKEND_API_URL}/entities
```

---

## Step 2. Frontend API Client 전환

### 파일

```text
frontend/src/lib/api/client.ts
```

### 변경사항

- `NEXT_PUBLIC_API_URL` 의존성을 제거한다.
- `API_BASE`는 브라우저 상대 경로 `/api/backend`를 사용한다.
- 기존 `apiFetch<T>(path, init)` 호출부가 변경 없이 동작해야 한다.
- `path`가 `/entities`처럼 leading slash를 포함하는 현재 사용 패턴을 유지한다.

### 완료 기준

```ts
apiFetch("/entities")
```

위 호출이 브라우저에서 다음 순서로 처리된다.

```text
Browser -> /api/backend/entities -> FastAPI /entities
```

---

## Step 3. 환경 변수 및 Compose 정리

### 파일

```text
docker-compose.yml
frontend/.env.example 또는 README.md
```

### 변경사항

- frontend service 환경 변수에서 `NEXT_PUBLIC_API_URL`을 제거한다.
- frontend server runtime 변수로 `BACKEND_API_URL=http://api:8000`을 설정한다.
- 로컬 비컨테이너 개발 시에는 `BACKEND_API_URL=http://localhost:8000`을 사용한다.

### 환경 변수 정책

| 변수 | 노출 범위 | 용도 |
|------|-----------|------|
| `BACKEND_API_URL` | server-only | Next.js BFF가 FastAPI를 호출할 내부 URL |
| `NEXT_PUBLIC_API_URL` | 사용 금지 | 브라우저에 backend origin을 노출하므로 제거 |

---

## Step 4. CORS 및 보안 정책 정리

### 작업 목록

- [ ] frontend 브라우저 코드에서 backend origin 직접 호출이 남아 있는지 검색
- [ ] FastAPI CORS 설정이 frontend 직접 호출을 전제로 과도하게 열려 있다면 축소
- [ ] 향후 API Key/auth 도입 시 BFF에서 server-only secret을 붙일지, 사용자별 credential을 전달할지 정책 메모 추가
- [ ] backend 오류 응답이 BFF를 거쳐도 기존 UI 에러 처리와 호환되는지 확인

---

## Step 5. 검증

### 정적 확인

- [ ] `rg "NEXT_PUBLIC_API_URL|localhost:8000|:8000" frontend`
- [ ] `rg "fetch\\(" frontend/src`
- [ ] `apiFetch` 호출부가 모두 BFF 경유 경로를 사용하는지 확인

### 수동 확인

- [ ] 로컬 개발 환경에서 frontend 화면 로딩
- [ ] Entity 목록 조회
- [ ] Entity 상세 조회
- [ ] Entity 생성/수정 등 write 요청이 BFF를 경유하는지 Network 탭에서 확인
- [ ] Docker Compose 환경에서 `frontend -> api` internal URL 호출 확인

### 테스트 권장

- [ ] BFF route handler 단위 테스트 또는 최소 smoke test 추가
- [ ] 기존 frontend API 호출 흐름 회귀 확인

---

## 완료 기준

- [ ] 브라우저 코드에 backend origin 직접 참조가 없다.
- [ ] frontend는 `/api/backend/*` 상대 경로만 호출한다.
- [ ] Next.js BFF는 `BACKEND_API_URL`로 FastAPI를 호출한다.
- [ ] Docker Compose에서 frontend 환경 변수는 `BACKEND_API_URL=http://api:8000`을 사용한다.
- [ ] README에 BFF 경유 구조와 환경 변수 정책이 문서화되어 있다.

**완료일**: —
