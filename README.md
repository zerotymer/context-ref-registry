# context-ref-registry

코딩 에이전트(Codex, Claude Code, Cursor 등)가 화면(UI_AREA), 기능(FEATURE), 인프라(INFRA_UNIT)를 UUID 기반으로 안정적으로 참조할 수 있게 하는 경량 레지스트리 서비스.

문서 파싱은 외부 에이전트가 담당하고, 이 서비스는 정리된 결과를 저장·조회·제공하는 역할만 한다.

## 아키텍처

```text
외부 Parser/Agent → POST /ingest/batch → Registry (PostgreSQL)
                                              ↓
Coding Agent ← MCP read-only server ← REST API

Browser → Next.js Admin UI (BFF) → FastAPI Backend (:8000)
```

## 기술 스택

| 레이어 | 스택 |
|--------|------|
| Backend | FastAPI (Python 3.12) + SQLAlchemy 2.x (async) + Alembic |
| DB | PostgreSQL 16 + JSONB metadata |
| Frontend | Next.js 14 + Tailwind CSS (관리자 콘솔) |
| Auth | JWT (Bearer) + API Key 병행 |
| MCP | Python MCP SDK — read-only |
| Package | uv (Python) / pnpm (Node) |
| Deploy | Docker Compose |

## 빠른 시작

```bash
docker compose up -d
```

| 서비스 | 주소 |
|--------|------|
| Backend API | http://localhost:8000 |
| Frontend | http://localhost:3000 |
| PostgreSQL | localhost:5432 |

## 개발 환경

### Backend

```bash
cd backend
uv pip install -e ".[dev]"
uvicorn app.main:app --reload --port 8000

# 테스트 (실제 PostgreSQL 필요)
.venv/bin/pytest tests/ -q
```

### Frontend

```bash
cd frontend
pnpm install
pnpm dev
```

## 프로젝트 구조

```
docker-compose.yml
backend/             # FastAPI 앱 — backend/CLAUDE.md 참조
frontend/            # Next.js 관리자 콘솔 — BFF 패턴
docs/                # 설계 문서 00~11
instructions/        # 구현 지침 파일
```

## 설계 문서

`docs/` 폴더에 00~11 번호 순으로 전체 설계가 있다.
