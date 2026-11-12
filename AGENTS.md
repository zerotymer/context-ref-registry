# AGENTS.md

이 파일은 이 레포지토리에서 작업하는 코딩 에이전트(Codex 등)의 작업 범위와 워크플로우를 정의한다.

> **참고**: 소스코드 수정이 필요한 구현 작업은 사용자의 명시적 요청이 있을 때만 수행한다. 기본 역할은 `instructions/` 지침 관리다.

---

## 현재 구현 상태

| 구분 | 상태 |
|------|------|
| MVP Core (Steps 0–10) | ✅ 완료 |
| 관리자 UI (Next.js + Tailwind) | ✅ 완료 |
| 인증 시스템 — 단일 관리자(환경변수, JWT 쿠키) + 프로젝트 API Key(`read`/`write`) | ✅ 완료 (사용자·멤버십 폐지) |
| 운영 준비 (API Key 인증, Audit Log, Observability — 백업은 DB 파일 복사) | ✅ 완료 |
| 관리자 콘솔 UI (로그인·프로젝트·API Key 화면) | ✅ 완료 |
| 확장 기능 (Revision, Review UI, Export, PR 검증, OpenAPI 내보내기) | ✅ 완료 |
| 확장 기능 — pgvector semantic search | ✖ 폐기 (필요 시 sqlite-vec 기준 재설계) |
| API Key 관리 UI (관리자 화면: 프로젝트·scope·만료일·마지막 사용) | ✅ 완료 |
| API Key 프로젝트 접근 제어 (키당 프로젝트 1개 필수, 전역·레거시 키 폐지) | ✅ 완료 |
| Project ID 특수문자 제한 (`[A-Za-z0-9_]`만 허용) | ✅ 완료 |
| 배치 저장 & 참조 패턴 (`POST /entities/batch`, UUID/PROJECT_ID@UUID/PROJECT_ID@TAG) | ✅ 완료 |
| 짧은 식별자 4번째 참조 패턴 (`PROJECT_ID-TYPE-N`, `(project_id,type)` 순번 불변, `EntityRead.short_id` 노출) | ✅ 완료 |
| 에이전트 API 게이트웨이 (Next BFF `/api/v1/*` → 백엔드 프록시, API Key passthrough) | ✅ 완료 |
| MCP HTTP transport 단계 A (stdio 폐기 → `api` 앱 `/mcp` streamable-http, API Key 인증, 프로젝트 범위 필터) | ✅ 완료 |
| MCP HTTP transport 단계 C (Next BFF 스트리밍 프록시 `/api/v1/mcp` → 백엔드 `/api/v1/mcp/`, SSE pipe·세션 헤더 passthrough) | ✅ 완료 |
| UI_AREA 목업 HTML (`GET /entities/{id}/mockup`) | ✅ 완료 |
| Ingest 식별자 반환 (`POST /ingest/batch` 응답 `entities[]`) | ✅ 완료 |
| Bundle Graph 탭 (`/bundle` AntV G6 d3-force 관계도) | ✅ 완료 |
| PostgreSQL → SQLite(WAL) 전환·경량화 (컨테이너 4→2개, 마이그레이션 baseline 1개) | ✅ 완료 (v2.0.0) |
| 백엔드 `/api/v1` prefix 규격화 + 리버스 프록시 안내 (프론트 단일·경로 분리 동시 호환, `docs/12-reverse-proxy.md`) | ✅ 완료 (v2.1.0) |

테스트: 백엔드 **303 passed** (`cd backend && .venv/bin/pytest tests/`) · 프론트 **30 passed** (`cd frontend && pnpm test`)

에이전트 MCP 진입점: `http://<host>:3000/api/v1/mcp` (streamable-http, `Authorization: Bearer <api-key>`, `read`·`write` 키 모두 허용).

### 진행상태 점검 / 지침 업데이트 시 필수 작업

'진행상태 점검' 또는 '지침 업데이트' 요청 시 다음을 함께 수행한다:

1. `CLAUDE.md` — 현재 지침 테이블·구현 현황·프로젝트 구조 동기화
2. `AGENTS.md` — 현재 구현 상태 테이블 동기화
3. `instructions/README.md` — 로드맵·완료 지침 요약·지침 파일 현황 동기화

---

## 에이전트 작업 경계

- 기본 역할은 이 프로젝트의 `instructions/` 및 지침/지시문 관리다.
- 프로젝트 파일을 읽고 지침 맥락을 파악하는 것은 허용한다.
- 사용자가 명시적으로 요청하지 않는 한 소스코드 수정은 하지 않는다.
- 사용자가 명시적으로 요청하지 않는 한 빌드, 테스트, 포맷팅, 설치, 서버 실행 등 개발 흐름에 영향을 줄 수 있는 명령은 실행하지 않는다.
- 필요한 경우 낮은 영향도의 조회/확인 작업만 수행하고, 변경 작업은 사용자 의도를 먼저 확인한다.

---

## Instructions 워크플로우

모든 구현 작업은 `instructions/` 아래 지침 파일을 기준으로 진행한다.

### 지침 파일 생성

1. UUID 발급: `python3 -c "import uuid; print(uuid.uuid4())"`
2. `instructions/{slug}.md` 생성 — frontmatter에 uuid, title, status, created 기록
3. `instructions/instructions.log`에 한 줄 추가:
   ```
   {uuid} | {title} | {ISO8601 timestamp} | created
   ```
4. **브랜치 전략 스킬 필수 실행** — 스킬 `e03f48fb-3e00-41d7-b99d-c32854567d67`로 작업 브랜치를 생성한다.

### 지침 완료 처리

모든 단계 완료 시:

1. frontmatter `status: completed`, `completed: {날짜}` 기록
2. `instructions/.completed/{uuid}.md`로 이동
3. `instructions/instructions.log`에 `completed` 이벤트 추가
4. git commit

---

## Git Branch 전략

Step별 `feat/step{N}-{slug}` 브랜치 → PR → main 머지.

브랜치 전략 스킬: `e03f48fb-3e00-41d7-b99d-c32854567d67`

---

## LLM-wiki 스킬 참조

작업 완료 보고 및 리뷰 시 아래 스킬을 활용한다.

| UUID | 용도 |
|------|------|
| `a43a68f9-fda2-4960-a49a-0a97ebf96a8a` | 백엔드/인프라 완료 보고 |
| `4de41e4d-536a-44ca-8194-f8c5c316e6bf` | Full-stack 완료 보고 |
| `dbdfdbab-77ed-49fe-b70e-1f1708fc7aab` | 프론트엔드 완료 보고 |
| `69a9089b-a444-4f44-89ab-5d58210906ae` | PR 템플릿 |
| `ed847c29-b20a-420b-9314-c16dce184d62` | 코드 리뷰 |
| `e6274b24-2c08-4367-8859-b5a92bd98d59` | 정적 목업 확인용 서버 기동 (`static-mockup-preview-server`) |