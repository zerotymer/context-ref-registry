# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 프로젝트 개요

LLM Reference Registry — 코딩 에이전트(Codex, Claude Code, Cursor 등)가 화면(UI_AREA), 기능(FEATURE), 인프라(INFRA_UNIT), API, 코드 심볼(CODE_SYMBOL), 이슈(ISSUE)를 UUID 기반으로 안정적으로 참조할 수 있게 하는 경량 저장소. 문서 파싱은 외부 에이전트가 담당하고, 이 서비스는 정리된 결과를 저장/조회/제공하는 역할만 한다.

## 구현 현황

| 구분 | 내용 | 상태 |
|------|------|------|
| MVP Core | DB Schema → REST API → MCP → 테스트 (Steps 0–10) | 완료 |
| 관리자 UI | Next.js + Tailwind, BFF 패턴, Entity·Tag 관리 | 완료 |
| 인증 시스템 | JWT + API Key 인증, 프로젝트·멤버십·접근 정책 | 완료 |
| 관리자 콘솔 | 로그인·사용자·프로젝트·멤버 관리 화면 | 완료 |
| 인증 고급 | 관리자·프로젝트 관리자 기능 | 완료 |
| 운영 준비 | 보안 & 모니터링 (API Key·Audit Log·Backup·Observability) | 완료 |
| 확장 기능 | pgvector, Revision, Export, AGENTS.md/OpenAPI 내보내기, PR 검증 | 완료 |
| API Key 관리 UI | 사용자 셀프서비스(/settings/api-keys) + 관리자(/admin/api-keys) 화면 | 완료 |
| API Key 프로젝트 접근 제어 | project_id 기반 발급 제한·접근 범위 강화, 레거시 키 제한 | 완료 |
| Project ID 특수문자 제한 | 허용 문자를 `[A-Za-z0-9_]`로 축소, 프론트·테스트 동기화 | 완료 |
| 배치 저장 & 참조 패턴 | `POST /entities/batch`, UUID/PROJECT_ID@UUID/PROJECT_ID@TAG 3가지 참조 패턴 | 완료 |
| 스키마 자동 적용 | 컨테이너 startup `entrypoint.sh` → `alembic upgrade head` (빈 DB 자동 생성, 멱등) | 완료 |
| 에이전트 API 게이트웨이 | Next BFF Route Handler `/api/v1/*` → 백엔드 프록시(API Key passthrough, OkResponse 봉투 미해제) | 완료 |
| MCP HTTP transport (단계 A) | stdio 폐기 → `api` 앱 `/mcp` streamable-http 마운트, API Key 인증 ASGI 미들웨어, 7개 tool에 프로젝트 범위 필터 | 완료 |
| MCP HTTP transport (단계 C) | Next BFF 스트리밍 프록시 `/api/v1/mcp` → 백엔드 `/mcp/` (SSE/청크 pipe, 세션·프로토콜 헤더 passthrough, 쿠키 차단). 에이전트 MCP 진입점 단일화 | 완료 |

테스트: 백엔드 **339 passed** (`cd backend && .venv/bin/pytest tests/`) · 프론트 **27 passed** (`cd frontend && pnpm test`)

## 기술 스택

- **Backend**: FastAPI (Python 3.12) + SQLAlchemy 2.x (async) + Alembic
- **DB**: PostgreSQL 16 + JSONB metadata
- **MCP**: Python MCP SDK — read-only, streamable-http (`api` 앱 `/mcp` 마운트, API Key 인증)
- **Deployment**: Docker Compose
- **Package Manager**: uv

## 아키텍처 흐름

```
외부 Parser/Agent → POST /ingest/batch → Registry (PostgreSQL)
                                              ↓
Coding Agent ← Next BFF /api/v1/mcp (스트리밍 프록시) ← MCP read-only
              (front:3000)                             (api:8000/mcp, streamable-http) ← REST read API
```

REST API는 write/read 모두 담당하고, MCP server는 **read-only**로만 제공한다.
MCP는 `api` 앱에 `/mcp` streamable-http 엔드포인트로 마운트되며 API Key 인증 +
프로젝트 범위 필터를 적용한다 (stdio 폐기). 에이전트의 **외부 진입점은 프론트
BFF `/api/v1/mcp`** (단계 C) — 요청/응답 바디를 스트림 그대로 pipe하고 세션·프로토콜
헤더를 passthrough하며 쿠키는 차단한다.

## 프로젝트 구조 (top-level)

```
docker-compose.yml      # postgres(5432), api(8000, MCP /mcp 포함), frontend(3000)
backend/                # FastAPI 앱 — 상세 구조는 backend/CLAUDE.md 참조
frontend/               # Next.js 관리자 콘솔 — BFF 패턴 (Server Actions)
                        #   + 에이전트 API 게이트웨이 (src/app/api/v1/[...path] → 백엔드 프록시)
                        #   + MCP 스트리밍 프록시 (src/app/api/v1/mcp/[[...path]] → 백엔드 /mcp/)
ci/                     # PR 참조 검증 스크립트 (validate-pr-refs.py)
.github/workflows/      # GitHub Actions CI (pr-validate-refs.yml)
docs/                   # 설계 문서 00~11
instructions/           # 구현 지침 파일
  deploy-build.md       #   배포 빌드 명령어 (영구 참조)
output/                 # 생성된 산출물 (목업 HTML, 보고서 등)
  admin-console-mockup/ #   관리자 콘솔 UI 목업
  review-ui-mockup/     #   Review UI 목업
  tag-ui-mockup/        #   Tag UI 목업
```

## Docker Compose

```bash
# 루트에서 실행
docker compose up -d
```

## 배포 빌드

> 상세 절차는 **[`instructions/deploy-build.md`](instructions/deploy-build.md)** 참고.

이미지: `llm-registry-api` (backend) + `llm-registry-front` (frontend)  
레지스트리: Docker Hub (`zerotymer/`) + Nexus OSS (`nexus.zerotymer.net/docker/`)  
태그: `latest` + 버전 태그 → 2×2×2 = **8개**

```bash
make release              # VERSION=1.0.0 (기본값)
make release VERSION=1.1.0  # 버전 지정
```

빌드 전 레지스트리 로그인 필요:

```bash
docker login                          # Docker Hub
docker login nexus.zerotymer.net      # Nexus OSS
```

## 설계 문서

`docs/` 폴더에 00~11 번호 순으로 모든 설계가 있다. 구현 중 판단이 필요하면 해당 문서를 우선 참고한다.

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

### 진행상태 점검 / 지침 업데이트 시 필수 작업

'진행상태 점검' 또는 '지침 업데이트' 요청 시 다음을 함께 수행한다:

1. `CLAUDE.md` — 현재 지침 테이블·구현 현황·프로젝트 구조 동기화
2. `AGENTS.md` — 현재 구현 상태 테이블 동기화
3. `instructions/README.md` — 로드맵·완료 지침 요약·지침 파일 현황 동기화

### 현재 지침

> 완료 지침은 최근 3건만 표시. 전체 이력은 `instructions/instructions.log` 참고.

| UUID | 파일 | 상태 |
|------|------|------|
| 612ab97e-df2b-4d1b-98ed-f3a928665606 | .completed/ | completed (2026-06-02) — Entity 프로젝트 필터 + 번들 그래프 뷰 |
| d494a542-0049-44a7-913d-398926dbc857 | .completed/ | completed (2026-06-03) — 컨테이너 startup 시 DB 스키마 자동 적용 (alembic upgrade head) |
| 2214f2c4-30a9-4555-bd24-073a841cadc3 | .completed/ | completed (2026-06-03) — 에이전트 API 게이트웨이 (Next BFF `/api/v1/*` 프록시, API Key passthrough) |
| 216b0864-6b7f-4057-8b06-b2865dc9bc53 | .completed/ | completed (2026-06-06) — MCP HTTP transport 전환. 단계 A(백엔드 `/mcp` 마운트·인증·범위 필터) + 단계 C(Next BFF 스트리밍 프록시 `/api/v1/mcp`) |
| 19e52237-68d4-4952-8c30-dd0eb9285ff0 | `deploy-build.md` | **reference** (영구) — 배포 빌드 명령어 (Docker Hub + Nexus OSS, 8개 태그) |

## Git Branch 전략

Step별 `feat/step{N}-{slug}` 브랜치 → PR → main 머지.

브랜치 전략 스킬: `e03f48fb-3e00-41d7-b99d-c32854567d67`

## 정적 서버 포트 규칙

정적 목업·보고서 확인용 서버는 **항상 포트 `8081`을 사용한다.** 다른 포트 번호 사용 금지.

```bash
# npx serve
npx serve "output/{파일_또는_디렉토리}" -s -l 8081

# Python fallback
python3 -m http.server 8081 --directory output/
```

접속: `http://localhost:8081`

## LLM-wiki 스킬 참조

작업 완료 보고 및 리뷰 시 아래 스킬을 활용한다.

| UUID | 용도 |
|------|------|
| `a43a68f9-fda2-4960-a49a-0a97ebf96a8a` | 백엔드/인프라 완료 보고 |
| `4de41e4d-536a-44ca-8194-f8c5c316e6bf` | Full-stack 완료 보고 |
| `dbdfdbab-77ed-49fe-b70e-1f1708fc7aab` | 프론트엔드 완료 보고 |
| `69a9089b-a444-4f44-89ab-5d58210906ae` | PR 템플릿 |
| `ed847c29-b20a-420b-9314-c16dce184d62` | 코드 리뷰 |
| `e6274b24-2c08-4367-8859-b5a92bd98d59` | 정적 목업 확인용 서버 기동 (`static-mockup-preview-server`, 포트 8081 고정) |
| `55723065-ac44-4a21-828e-aca40d0011c5` | 보안취약점 처리 |
