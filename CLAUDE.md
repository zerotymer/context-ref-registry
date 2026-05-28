# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 프로젝트 개요

LLM Reference Registry — 코딩 에이전트(Codex, Claude Code, Cursor 등)가 화면(UI_AREA), 기능(FEATURE), 인프라(INFRA_UNIT)를 UUID 기반으로 안정적으로 참조할 수 있게 하는 경량 저장소. 문서 파싱은 외부 에이전트가 담당하고, 이 서비스는 정리된 결과를 저장/조회/제공하는 역할만 한다.

## 구현 현황 (MVP 완료)

| Step | 내용 | 상태 |
|------|------|------|
| 0 | 프로젝트 초기화 | 완료 |
| 1–10 | DB Schema → 테스트 정리 | 완료 |

테스트: **139 passed** (`backend/.venv/bin/pytest tests/`)

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
docker-compose.yml   # postgres(5432), api(8000), mcp(stdio)
backend/             # FastAPI 앱 — 상세 구조는 backend/CLAUDE.md 참조
docs/                # 설계 문서 00~11
instructions/        # 구현 지침 파일
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

### 현재 지침

> 완료 지침은 최근 3건만 표시. 전체 이력은 `instructions/instructions.log` 참고.

| UUID | 파일 | 상태 |
|------|------|------|
| ce6d92bf-2c2d-4944-adb3-1089a6530e56 | instructions/security_ops.md | pending |
| 03080220-3b52-4d28-a79d-e2d698e5480f | instructions/extensions.md | pending |
| 36ab4117-e0cc-4a30-813e-129f0835b540 | .completed/ | completed (2026-05-28) |
| 5fa5df8b-61e9-4da7-86d5-9802e748c405 | .completed/ | completed (2026-05-28) |
| 7f798d9a-780a-427a-90e5-49fb8ad17139 | .completed/ | completed (2026-05-28) |

## Git Branch 전략

Step별 `feat/step{N}-{slug}` 브랜치 → PR → main 머지.

브랜치 전략 스킬: `e03f48fb-3e00-41d7-b99d-c32854567d67`

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
