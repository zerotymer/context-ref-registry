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

테스트: **304 passed** (`cd backend && .venv/bin/pytest tests/`)

## 기술 스택

- **Backend**: FastAPI (Python 3.12) + SQLAlchemy 2.x (async) + Alembic
- **DB**: PostgreSQL 16 + JSONB metadata
- **MCP**: Python MCP SDK — read-only
- **Deployment**: Docker Compose
- **Package Manager**: uv

## 아키텍처 흐름

```
외부 Parser/Agent → POST /ingest/batch → Registry (PostgreSQL)
                                              ↓
Coding Agent ← MCP read-only server ← REST read API
```

REST API는 write/read 모두 담당하고, MCP server는 **read-only**로만 제공한다.

## 프로젝트 구조 (top-level)

```
docker-compose.yml      # postgres(5432), api(8000), frontend(3000), mcp(stdio)
backend/                # FastAPI 앱 — 상세 구조는 backend/CLAUDE.md 참조
frontend/               # Next.js 관리자 콘솔 — BFF 패턴 (Server Actions)
ci/                     # PR 참조 검증 스크립트 (validate-pr-refs.py)
.github/workflows/      # GitHub Actions CI (pr-validate-refs.yml)
docs/                   # 설계 문서 00~11
instructions/           # 구현 지침 파일
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
| c4309c75-5633-4187-a785-3b40c8e037b2 | .completed/ | completed (2026-05-31) — API Key 관리 UI — 사용자/관리자 화면 구현 |
| d679e0e0-ed7e-4de0-ba3d-554a83d3601c | .completed/ | completed (2026-05-31) — API Key 프로젝트 기반 발급 및 접근 제어 강화 |
| 4d7b7053-162b-4e15-99cc-d6700354008f | .completed/ | completed (2026-05-31) — Project ID 특수문자 제한 — 언더바(_)만 허용 |

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
