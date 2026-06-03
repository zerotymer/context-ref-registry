---
uuid: 2214f2c4-30a9-4555-bd24-073a841cadc3
title: Next BFF Route Handler 에이전트 API 게이트웨이 (API Key passthrough)
status: in_progress
created: 2026-06-03
---

# Next BFF Route Handler 에이전트 API 게이트웨이

## 배경 / 문제

현재 코딩 에이전트(Codex / Claude Code / Cursor 등)는 백엔드 API 서버
(`:8000`)에 **직접** 요청한다. 인증은 API Key(`Authorization: Bearer <key>`
또는 `X-API-Key: <key>`)로 수행한다.

운영 관점에서 **프론트엔드(`:3000`)에 에이전트용 단일 진입점(통합 게이트웨이)**
을 두려고 한다. 이를 위해 Next.js App Router의 **Route Handler**로 에이전트용
API를 프록시(passthrough)한다. 백엔드 `:8000`과 프론트 `:3000`은 그대로 둘 다
기동하며, "외부에 무엇을 오픈할지"는 리버스 프록시/서버측 설정 영역(서버 관리자
결정권)이므로 본 지침의 범위가 아니다.

> 현행 BFF(`lib/api/server.ts`의 `backendFetch`)는 **JWT 쿠키 기반**으로
> 관리자 웹 UI(사람) Server Action 전용이다. 이번 작업의 프록시는 그것과
> **완전히 별개**다. 쿠키를 주입하지 않고 **API Key 헤더만 그대로 통과**시킨다.

## 결정 사항 (확정)

| 항목 | 결정 |
|------|------|
| 매핑 범위 | **전체 에이전트 API** (관리자 전용 `auth`·`admin_*` 제외) |
| 목적 | **통합 게이트웨이** — 프론트(`/api/v1/*`)가 에이전트용 단일 진입점 (외부 노출 범위는 서버 관리자/리버스 프록시 결정권) |
| URL 경로 규칙 | **`/api/v1/*` → 백엔드 동일 경로** (예: `/api/v1/entities` → `/entities`) |
| 인증 처리 | **API Key 헤더만 passthrough** — 쿠키 주입 안 함, 키 없으면 백엔드가 401 |

## 설계

### 단일 catch-all 프록시 핸들러

엔드포인트마다 `route.ts`를 만들지 않는다. **catch-all 동적 세그먼트** 하나로
모든 에이전트 API를 프록시한다.

```
frontend/src/app/api/v1/[...path]/route.ts
```

- `GET / POST / PATCH / PUT / DELETE` 메서드 export
- 요청 경로 `/api/v1/<path>` → 백엔드 `${BACKEND_API_URL}/<path>` 로 전달
  - `BACKEND_API_URL`은 기존 `lib/api/server.ts`와 동일 env 재사용
    (`?? "http://localhost:8000"`)
- **쿼리스트링 그대로 전달** (`?q=...&types=...&limit=...`)
- **요청 바디 그대로 전달** (POST/PATCH/PUT — `request.text()` 또는 stream)
- **응답 passthrough**: 백엔드의 **status code·content-type·body를 그대로 반환**
  - ⚠️ `backendFetch`처럼 `OkResponse` 봉투를 풀지 **않는다**. 에이전트는 직접
    호출과 동일한 응답 형태를 기대한다.
  - ⚠️ `201`/`207`/`401`/`404` 등 상태코드 보존 (배치는 207, 생성은 201).
  - ⚠️ `export` 계열은 봉투가 아님:
    `/export/agents-md`(text/plain), `/export/openapi`(JSON raw).
    → content-type 보존 필수.

### 헤더 처리 (핵심)

**전달(forward)하는 헤더만 화이트리스트**로 추린다:

| 헤더 | 처리 |
|------|------|
| `Authorization` | 그대로 전달 (Bearer API Key) |
| `X-API-Key` | 그대로 전달 |
| `Content-Type` | 그대로 전달 (바디 있는 메서드) |
| `Accept` | 그대로 전달 |
| `Cookie` / `access_token` | **전달 금지** (쿠키 주입·전파 안 함) |
| 기타 hop-by-hop (`Host`, `Connection` 등) | 전달 금지 |

→ 인증 책임은 전적으로 백엔드에 위임한다. 게이트웨이는 인증을 **판단하지
않고**, 키가 없거나 잘못되면 백엔드가 401/403을 반환하고 그대로 passthrough.

### 경로 허용 범위 (allowlist)

catch-all이므로 `auth`·`admin_*`로의 우회 접근을 막아야 한다. **허용 prefix
화이트리스트**를 둔다(아래에 없는 경로는 게이트웨이에서 404).

에이전트 API 전체 목록 (백엔드 라우터 기준):

| 백엔드 경로(prefix) | 게이트웨이 경로 | 메서드 |
|------|------|------|
| `/entities` | `/api/v1/entities` | GET, POST |
| `/entities/batch` | `/api/v1/entities/batch` | POST(207) |
| `/entities/{ref}` | `/api/v1/entities/{ref}` | GET, PATCH |
| `/entities/{ref}/tags` | … | GET, POST, DELETE |
| `/entities/{ref}/history[...]` | … | GET |
| `/entities/{ref}/contexts` | … | GET, POST |
| `/entities/{ref}/relations` | … | GET |
| `/entities/{ref}/aliases` | … | GET, POST, DELETE |
| `/relations` | `/api/v1/relations` | POST |
| `/search` | `/api/v1/search` | GET |
| `/resolve` | `/api/v1/resolve` | GET |
| `/tags` | `/api/v1/tags` | GET |
| `/context-bundle` | `/api/v1/context-bundle` | POST |
| `/ingest/batch` | `/api/v1/ingest/batch` | POST |
| `/export/agents-md` | `/api/v1/export/agents-md` | GET |
| `/export/openapi` | `/api/v1/export/openapi` | GET |
| `/validate-references` | `/api/v1/validate-references` | POST |
| `/projects[...]` | `/api/v1/projects` | GET, POST, (members 관리) |

**제외(게이트웨이로 노출하지 않음)**: `auth_router`(`/auth/*`),
`admin_users`, `admin_projects`, `admin_api_keys` — 이들은 사람용(쿠키 세션)
이며 관리자 웹 UI의 Server Action 경로로만 접근한다.

> 구현 단순화를 위해 허용 판단은 **최상위 prefix 화이트리스트**
> (`entities`, `relations`, `search`, `resolve`, `tags`, `context-bundle`,
> `ingest`, `export`, `validate-references`, `projects`)로 처리하고,
> denylist(`auth`, `admin`)를 추가로 막는다.

### 런타임

- Node.js 런타임 사용 (`export const runtime = "nodejs"`) — 헤더/바디 stream
  안정성. Edge 불필요.
- `export const dynamic = "force-dynamic"` — 캐시 금지(`cache: "no-store"`).

## 구현 단계 (체크리스트)

- [ ] **Step 1 — 프록시 헬퍼**
  `frontend/src/lib/api/gateway.ts` 신설.
  - `proxyToBackend(request: Request, pathParts: string[]): Promise<Response>`
  - 허용 prefix 검증 → 미허용 시 404 JSON
  - 헤더 화이트리스트 구성 → 백엔드 fetch → status·헤더·바디 passthrough
  - `BACKEND_API_URL` env 재사용
- [ ] **Step 2 — Route Handler**
  `frontend/src/app/api/v1/[...path]/route.ts` 신설.
  - `GET/POST/PATCH/PUT/DELETE` → `proxyToBackend(request, params.path)` 위임
  - `runtime = "nodejs"`, `dynamic = "force-dynamic"`
- [ ] **Step 3 — 테스트** (⚠️ 테스트 없는 PR 금지 — 전역 규칙)
  - 프론트엔드에 테스트 러너 부재 → **Vitest** 도입
    (`vitest.config.ts`, `package.json` `"test": "vitest run"`)
  - `frontend/src/lib/api/gateway.test.ts`:
    - Authorization/X-API-Key 헤더가 백엔드로 전달되는지
    - 쿠키/access_token이 **전달되지 않는지**
    - 쿼리스트링·바디 보존
    - 응답 status code(201/207/401/404) 보존
    - 미허용 경로(`auth`, `admin`)는 404
    - `fetch`는 mock 처리
- [ ] **Step 4 — 문서 동기화**
  - `CLAUDE.md` 구현 현황 테이블에 항목 추가
  - `AGENTS.md` 구현 상태 동기화
  - `instructions/README.md` 로드맵·완료 지침 갱신
  - 신규 에이전트 진입점(`/api/v1/*`) README/배포 노트 명시
- [ ] **Step 5 — 완료 처리**
  - frontmatter `status: completed`, `completed` 기록
  - `instructions/.completed/{uuid}.md` 이동 + log 기록 + commit

## 참고 / 주의

- 본 게이트웨이는 **백엔드를 대체하지 않고 프록시**한다. 응답 봉투(`OkResponse`)
  를 풀지 않는 것이 핵심 — 직접 호출과 100% 동일 동작 보장.
- 백엔드 인증 로직(`backend/app/auth/dependencies.py`)은 변경하지 않는다.
  이미 `Authorization: Bearer` / `X-API-Key` / 쿠키 3종을 지원한다.
- 통합 게이트웨이는 **코드 레벨(Route Handler 추가)** 작업이다. 백엔드 `:8000`
  과 프론트 `:3000`은 그대로 **둘 다 기동**한다. "외부에 무엇을 오픈할지"는
  리버스 프록시/서버측 설정 영역이며 **서버 관리자의 결정권**이다(보안 사안).
  → 본 지침은 compose/인프라 포트 구성을 **변경하지 않는다.**
- 브랜치 전략 스킬(`e03f48fb-3e00-41d7-b99d-c32854567d67`)로 작업 브랜치 생성
  후 진행.
