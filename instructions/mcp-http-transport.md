---
uuid: 216b0864-6b7f-4057-8b06-b2865dc9bc53
title: MCP HTTP transport 전환 (stdio 폐기, 단계 A 백엔드 마운트 → 단계 C BFF 프록시)
status: in_progress
created: 2026-06-06
---

# MCP HTTP transport 전환

## 배경 / 문제

현재 MCP 서버는 **stdio transport**로만 동작한다(`mcp.run()` 기본값).

- `docker-compose.yml`의 `mcp` 서비스: 포트 없음, `stdin_open: true`. 클라이언트가
  `python -m app.mcp` 프로세스를 매번 spawn해야 한다.
- 클라이언트 머신에 **코드 전체 + `.venv` + DB 직접 접근(`DATABASE_URL`)** 이 필요하다.
- 인증이 **전혀 없다** — 띄우면 read-only지만 전체 레지스트리가 무인증 노출.
- `deploy-build.md:146` 기준 **배포 이미지에서 제외**되어 있다.
- 테스트(`test_mcp_tools.py`)는 `mcp.call_tool()`로 **tool 로직만** 검증하며 주석에
  *"no MCP transport is needed"* 라고 명시 — **MCP 서버로서의 end-to-end(핸드셰이크
  →tool 호출) 동작은 한 번도 검증된 적이 없다.**

→ stdio는 폐기한다. front(`:3000`) / back(`:8000`)처럼 **떠 있는 서버에 HTTP로
붙어서** 동작을 검증·운영할 수 있는 구조로 전환한다.

## 재활용 / 폐기 자산

| 구분 | 대상 |
|------|------|
| **재활용** | `backend/app/mcp/tools.py` — 6개 read-only tool 로직·스키마 **그대로 유지** |
| **재활용** | `backend/app/mcp/server.py`의 `FastMCP` 인스턴스(`mcp`)·instructions 문자열 |
| **폐기** | stdio transport (`mcp.run()`), `__main__.py`의 `python -m app.mcp` 실행 경로 |
| **폐기** | `docker-compose.yml`의 stdio `mcp` 서비스 (`entrypoint`, `stdin_open`) |

## 결정 사항 (확정)

| 항목 | 결정 |
|------|------|
| transport | **streamable-http** (공식 MCP SDK `FastMCP.streamable_http_app()`) |
| 백엔드 서빙 | **단계 A** — `api` FastAPI 앱에 `/mcp` 마운트 (별도 프로세스/포트 분리 안 함) |
| 외부 노출 | **단계 C** — 단계 A 위에 프론트 BFF 프록시(`/api/v1/mcp`) 추가 (A ⊂ C) |
| DB / 코드 | 백엔드와 **동일 코드·동일 커넥션 풀 공유** (tool이 이미 `app.service`/`app.repository` 직접 사용) |

> **단계 관계**: C는 A를 **포함**한다. C의 프록시 대상이 곧 A가 만든 백엔드
> `/mcp` 엔드포인트다. **A를 먼저 완성·검증**한 뒤, 외부 노출을 BFF 뒤로 옮겨 C로
> 마감한다. A 산출물은 그대로 C의 토대가 되므로 버리는 작업이 없다.

## 미해결 결정 (별도 세션 착수 시 확정 필요)

> 아래는 구현 착수 전에 사용자가 결정해야 하는 사항. 기본 제안을 함께 적는다.

1. **인증 적용 방식** — 마운트된 `streamable_http_app()`은 **하위 ASGI 앱**이라
   FastAPI `Depends`(`get_current_user`/API Key 검증)가 직접 안 걸린다.
   - (제안) `/mcp` 경로에 **ASGI 미들웨어** 또는 마운트 래퍼로 API Key 검사 →
     기존 `backend/app/auth/dependencies.py`의 키 검증 로직 재사용.
   - 대안: 단계 A에서는 무인증으로 내부 검증만 하고, 외부 인증은 단계 C의 BFF
     passthrough + 리버스 프록시에 위임.
2. **인증 주체(읽기 권한 모델)** — MCP는 read-only인데, API Key의 project 접근
   범위를 tool 호출에 반영할지(현재 stdio는 무시하고 전체 조회). 반영 시 tool
   시그니처/세션 컨텍스트 변경 필요 → **범위 확정 필요**.
3. **`/mcp` 외부 직접 노출 여부** — 단계 A 검증 동안 `api:8000/mcp`를 host에
   공개할지. (제안) 검증 동안만 공개 → C 완료 후 내부 전용으로 회수.

---

## 단계 A — 백엔드 FastAPI 앱에 `/mcp` 마운트

목표: `http://host:8000/mcp` 로 MCP 클라이언트가 붙어 핸드셰이크 + tool 호출 가능.

### 설계

공식 MCP SDK 패턴(`mcp.server.fastmcp.FastMCP`):

- `mcp.streamable_http_app()` 로 ASGI 앱을 얻어 기존 FastAPI에 마운트.
- **세션 매니저 lifespan 필수** — `async with mcp.session_manager.run(): yield`.
  현재 `main.py`에 이미 `lifespan`(bootstrap_admin)이 있으므로 **두 컨텍스트를
  합친다** (`contextlib.AsyncExitStack`).
- 마운트 경로를 `/mcp`로, 엔드포인트가 정확히 `/mcp`가 되도록
  `mcp.settings.streamable_http_path = "/"` 설정 (마운트 prefix와 중복 방지).

```python
# main.py (개념 스케치 — 착수 시 정확한 형태 확정)
import contextlib
from app.mcp.server import mcp

mcp.settings.streamable_http_path = "/"   # 마운트가 /mcp prefix 부여

@contextlib.asynccontextmanager
async def lifespan(app: FastAPI):
    async with contextlib.AsyncExitStack() as stack:
        await stack.enter_async_context(mcp.session_manager.run())
        # 기존 bootstrap_admin (best-effort)
        try:
            async with async_session_factory() as session:
                await AuthService(session).bootstrap_admin()
        except Exception:
            logger.warning("bootstrap_admin skipped", exc_info=True)
        yield

app = FastAPI(..., lifespan=lifespan)
app.mount("/mcp", mcp.streamable_http_app())
```

### 구현 단계 (체크리스트)

- [x] **A-1 — server.py / __main__.py 정리**
  - `mcp.run()` (stdio) 제거. `server.py`는 `FastMCP` 인스턴스 + tools import +
    `mcp.settings.streamable_http_path = "/"` 만 남김.
  - `__main__.py`는 http 안내 메시지 출력 후 exit(1)로 대체.
- [x] **A-2 — main.py 마운트 + lifespan 병합**
  - `mcp.session_manager.run()` 을 기존 lifespan과 `AsyncExitStack`으로 병합.
  - `app.mount("/mcp", McpApiKeyAuthMiddleware(mcp.streamable_http_app()))`.
  - `streamable_http_path="/"` 로 엔드포인트 `/mcp` (클라이언트는 `/mcp`→`/mcp/`
    307 리다이렉트를 자동 추종).
- [x] **A-3 — 인증 적용** (결정 #1: ASGI 미들웨어 API Key 검사)
  - `app/mcp/http_auth.py` `McpApiKeyAuthMiddleware` — `Authorization: Bearer` /
    `X-API-Key` 추출 → `AuthService.get_user_by_api_key` 재사용, 실패 시 401.
  - 결정 #2(프로젝트 범위 반영): `AccessPolicy.get_visible_project_ids` 결과를
    ASGI `scope`에 심고(`app/mcp/scope.py`), 7개 tool이 `mcp.get_context()`로
    읽어 범위 필터링. 범위 밖 entity는 `ENTITY_NOT_FOUND`/결과 제외로 은닉.
- [x] **A-4 — docker-compose 정리**
  - stdio `mcp` 서비스 제거 (MCP는 `api` 서비스가 `:8000/mcp`로 서빙).
- [x] **A-5 — 테스트**
  - 기존 `test_mcp_tools.py`(call_tool 직접) 유지 — 16 passed.
  - 신규 `test_mcp_http.py` — uvicorn 실서버 + MCP 클라이언트로 핸드셰이크 →
    `list_tools`(7종) → tool 호출, 키 없음/오류 → 401, 프로젝트 범위 필터 검증. 5 passed.
  - 전체 백엔드 **339 passed**.
- [x] **A-6 — 문서 동기화**
  - `backend/CLAUDE.md` (주의사항·구조·tool 표·dev 명령), 루트 `CLAUDE.md`
    (구현 현황·아키텍처·구조·테스트 수), `AGENTS.md`, `instructions/deploy-build.md`
    ("MCP 배포 제외" → `api` 이미지 포함), `instructions/README.md` 갱신 완료.

### 단계 A 완료 기준 (DoD)

- `docker compose up -d` 후 `http://host:8000/mcp` 에 MCP 클라이언트가 붙어
  tool 목록 조회 + 1개 tool 호출이 성공한다.
- 백엔드 테스트 그린 (기존 + 신규 transport 테스트).

---

## 단계 C — 프론트 BFF 프록시 (`/api/v1/mcp`)

목표: 외부 노출 표면을 프론트(`:3000`) 한 곳으로 단일화. 백엔드 `/mcp`는 내부
전용으로 회수. 기존 `/api/v1/*` 게이트웨이 패턴과 일관.

> ⚠️ 기존 `gateway.ts`(REST passthrough)와 **다른 점**: MCP streamable-http는
> **SSE/청크 스트리밍·장수명 연결**이다. `request.text()`로 통째 버퍼링하는 기존
> 프록시로는 부족 → **스트림 그대로 pipe** 해야 한다. 착수 시 Next Route Handler
> 의 스트리밍 응답(Web `ReadableStream` passthrough) 방식 확정 필요.

### 구현 단계 (체크리스트)

- [ ] **C-1 — 스트리밍 프록시 핸들러**
  - `frontend/src/app/api/v1/mcp/[[...path]]/route.ts` (또는 기존 `[...path]`
    catch-all 확장) — `/api/v1/mcp/*` → `${BACKEND_API_URL}/mcp/*`.
  - 요청/응답 **바디 스트림 pipe** (버퍼링 금지), SSE content-type 보존.
  - API Key 헤더(`Authorization`/`X-API-Key`) passthrough, 쿠키 전달 금지
    (기존 gateway 헤더 화이트리스트 재사용).
  - `runtime = "nodejs"`, `dynamic = "force-dynamic"`.
- [ ] **C-2 — 백엔드 노출 회수**
  - compose에서 `api`의 `/mcp` 외부 직접 공개 제거(내부 docker 네트워크만).
    외부는 프론트 BFF 경유로만.
- [ ] **C-3 — 테스트**
  - `frontend` Vitest — `/api/v1/mcp` 프록시가 헤더 passthrough·스트림 전달·쿠키
    차단을 지키는지 (`fetch` mock, 스트림 응답 mock).
- [ ] **C-4 — 문서 동기화**
  - `CLAUDE.md` / `AGENTS.md` / `instructions/README.md` — 에이전트 MCP 진입점이
    `/api/v1/mcp` 임을 명시.

### 단계 C 완료 기준 (DoD)

- MCP 클라이언트가 `http://host:3000/api/v1/mcp` (API Key 헤더)로 붙어 tool 호출
  성공. 백엔드 `:8000/mcp`는 외부에서 직접 접근 불가(내부 전용).
- 프론트 테스트 그린.

---

## 참고 / 주의

- **착수 시 라이브러리 문서 우선 확인**: 정확한 `streamable_http_app()` /
  `session_manager` / `settings.streamable_http_path` API는 버전에 따라 다를 수
  있다 → `ctx7`로 `/modelcontextprotocol/python-sdk` 현행 문서 확인 후 구현.
  (현재 설치: `mcp 1.27.1`.)
- tool 로직(`tools.py`)은 **건드리지 않는다** — transport만 교체.
- 브랜치 전략 스킬(`e03f48fb-3e00-41d7-b99d-c32854567d67`)로 작업 브랜치 생성 후
  진행. 단계 A / 단계 C를 **별도 PR**로 나누는 것을 권장(A 검증 후 C 착수).
- `main` 직접 push 금지, 테스트 없는 PR 금지(전역 규칙).
