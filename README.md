# context-ref-registry

코딩 에이전트(Codex, Claude Code, Cursor 등)가 화면(UI_AREA), 기능(FEATURE), 인프라(INFRA_UNIT), API, 코드 심볼을 **UUID 기반으로 안정적으로 참조**할 수 있게 하는 경량 레지스트리 서비스.

문서 파싱은 외부 에이전트가 담당하고, 이 서비스는 정리된 결과를 저장·조회·제공하는 역할만 한다.

---

## 아키텍처

```
외부 Parser/Agent → POST /ingest/batch → Registry (PostgreSQL)
                                              ↓
Coding Agent ← MCP read-only server ← REST API (:8000)

Browser → Next.js Admin UI (:3000, BFF) → FastAPI Backend (:8000)

CI/CD → POST /validate-references → 레지스트리 참조 검증
```

---

## 기술 스택

| 레이어 | 스택 |
|--------|------|
| Backend | FastAPI (Python 3.12) + SQLAlchemy 2.x (async) + Alembic |
| DB | PostgreSQL 16 + pgvector + JSONB metadata |
| Frontend | Next.js 14 + Tailwind CSS (관리자 콘솔, BFF 패턴) |
| Auth | JWT (Bearer) + API Key 병행, 프로젝트 기반 권한 |
| MCP | Python MCP SDK — read-only |
| Package | uv (Python) / pnpm (Node) |
| Deploy | Docker Compose |

---

## 빠른 시작

### Docker Compose (배포 이미지 사용)

아래 `docker-compose.yml`을 사용하면 빌드 없이 바로 실행할 수 있다.

```yaml
services:
  postgres:
    image: postgres:16-alpine
    environment:
      POSTGRES_DB: llmref
      POSTGRES_USER: llmref
      POSTGRES_PASSWORD: llmref        # 운영 환경에서는 반드시 변경
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U llmref"]
      interval: 5s
      timeout: 5s
      retries: 5

  api:
    image: zerotymer/llm-registry-api:latest
    ports:
      - "8000:8000"
    environment:
      DATABASE_URL: postgresql+asyncpg://llmref:llmref@postgres:5432/llmref
      JWT_SECRET: "change-me-to-a-long-random-string"   # 필수 변경
      JWT_EXPIRE_MINUTES: 10080
      BOOTSTRAP_ADMIN_LOGIN_ID: admin
      BOOTSTRAP_ADMIN_PASSWORD: admin                   # 필수 변경
      BOOTSTRAP_ADMIN_DISPLAY_NAME: Admin
    depends_on:
      postgres:
        condition: service_healthy

  frontend:
    image: zerotymer/llm-registry-front:latest
    ports:
      - "3000:3000"
    environment:
      BACKEND_API_URL: http://api:8000
    depends_on:
      - api

volumes:
  postgres_data:
```

```bash
# 실행
docker compose up -d
```

| 서비스 | 주소 |
|--------|------|
| Backend API | http://localhost:8000 |
| API 문서 | http://localhost:8000/docs |
| Frontend | http://localhost:3000 |
| PostgreSQL | localhost:5432 |

---

### 환경 변수

운영 환경변수는 **접속 정보(DB/내부 URL)와 backup 정책**으로만 최소화되어 있다. JWT 서명 키와 만료, 초기 관리자 계정은 더 이상 환경변수가 아니며 코드에 고정된다.

#### Backend (`api` 서비스)

| 변수 | 필수 | 기본값 | 설명 |
|------|:----:|--------|------|
| `DATABASE_URL` | ✅ | — | PostgreSQL 접속 URL (`postgresql+asyncpg://...`) — 외부 DB 연결 시 변경 |

> JWT 서명 키(`JWT_SECRET`)는 **프로세스 기동 시마다 임의 문자열로 자동 생성**되며 시작 로그에 기록된다. 외부 서비스와 연결되지 않으므로 재기동 시 기존 세션은 무효화된다. 알고리즘(`HS256`)과 만료(7일)는 코드에 고정.

#### Frontend (`frontend` 서비스)

| 변수 | 필수 | 기본값 | 설명 |
|------|:----:|--------|------|
| `BACKEND_API_URL` | ✅ | — | Frontend → Backend 내부 URL (예: `http://api:8000`) — 백엔드 포트 변경 시 조정 |

#### Backup (`backup` 서비스)

| 변수 | 필수 | 기본값 | 설명 |
|------|:----:|--------|------|
| `PGHOST` | ✅ | — | 백업 대상 PostgreSQL 호스트 (예: `postgres`) |
| `PGPORT` | | `5432` | 대상 포트 |
| `PGUSER` | ✅ | — | 대상 사용자 (postgres와 동일) |
| `PGPASSWORD` | ✅ | — | 대상 비밀번호 (postgres와 동일) |
| `PGDATABASE` | ✅ | — | 대상 DB (예: `llmref`) |
| `BACKUP_SCHEDULE` | | `0 2 * * *` | 백업 cron 스케줄 |
| `BACKUP_RETAIN_DAYS` | | `7` | 백업 보존 기간(일) |

### 기본 관리자 계정

서버 최초 기동 시(관리자 계정이 하나도 없을 때) 관리자 계정이 자동으로 생성됩니다. 계정 정보는 **`admin` / `admin`으로 고정**되어 있습니다:

| 항목 | 값 |
|------|-----|
| 아이디 | `admin` |
| 비밀번호 | `admin` |

> **보안 주의**: 초기 계정은 `admin/admin`으로 **고정**되며, 이를 변경하는 책임은 전적으로 운영 관리자에게 있습니다. 최초 로그인 후 반드시 비밀번호를 변경하세요. 로그인 시 비밀번호 변경 화면으로 자동 이동됩니다. 비밀번호 변경 시 기존 API 키가 모두 삭제됩니다.

---

## 개발 환경

### Backend

```bash
cd backend
uv pip install -e ".[dev]"
uvicorn app.main:app --reload --port 8000

# 테스트 (실제 PostgreSQL 필요)
.venv/bin/pytest tests/ -q
# 현재: 286 passed
```

### Frontend

```bash
cd frontend
pnpm install
pnpm dev
```

---

## 주요 기능

### Entity 관리

- `UI_AREA`, `FEATURE`, `INFRA_UNIT`, `API`, `CODE_SYMBOL` 타입 지원
- alias 기반 조회 (UUID 외 사람이 읽기 좋은 이름)
- 태그 다중 부착, 상태 관리 (`candidate` → `active` → `deprecated`)
- 변경 이력 자동 기록 및 revision 비교 API

### 검색

- alias exact match → canonical_name ILIKE → full-text (tsvector) → vector 유사도 (pgvector)
- `GET /search?q=` — 키워드 + 시맨틱 통합 검색

### Context Bundle

- `GET /bundles?root_ids=&max_depth=&token_budget=` — depth-first traversal, 토큰 예산 제한

### Export

| 엔드포인트 | 설명 |
|-----------|------|
| `GET /export/agents-md` | AGENTS.md 형식 — 에이전트 온보딩용 컨텍스트 내보내기 |
| `GET /export/openapi` | OpenAPI 3.1.0 spec (JSON/YAML) — API entity 기반 자동 생성 |

### PR 참조 검증

```bash
# CI에서 사용
python ci/validate-pr-refs.py \
  --registry-url $REGISTRY_URL \
  --api-key $REGISTRY_API_KEY \
  --post-comment
```

- PR diff에서 UUID / `@ref:alias` / `@entity:alias` 패턴 자동 추출
- `POST /validate-references` — valid/ambiguous/missing 분류 응답
- `.github/workflows/pr-validate-refs.yml` — GitHub Actions 연동 ready

### MCP Server (read-only)

```bash
python -m app.mcp
```

`search_entities`, `get_entity`, `get_context_bundle`, `validate_references` 도구 제공.

### 관리자 콘솔

- 로그인 (JWT), 사용자·프로젝트·멤버 관리
- Entity 목록·상세·승인(candidate→active)·deprecated 처리
- alias 비활성화, 태그 관리
- Audit Log 조회

---

## 프로젝트 구조

```
docker-compose.yml
backend/
  app/
    api/          # REST 엔드포인트
    service/      # 비즈니스 로직
    repository/   # DB 접근
    domain/       # 모델·스키마·Enum
    mcp/          # MCP 서버
    auth/         # JWT·API Key 인증
  tests/          # 286 테스트
  alembic/        # DB 마이그레이션 (migrations/versions/)
frontend/         # Next.js 관리자 콘솔 (BFF 패턴)
ci/               # PR 검증 스크립트 (validate-pr-refs.py)
.github/workflows/ # PR 검증 CI workflow (pr-validate-refs.yml)
docs/             # 설계 문서 00~11
instructions/     # 구현 지침 파일
```

---

## 구현 현황

| Phase | 내용 | 상태 |
|-------|------|------|
| MVP (Steps 0–10) | DB Schema → REST API → MCP → 테스트 | ✅ 완료 |
| 관리자 UI | Next.js + Tailwind, BFF 패턴, Entity·Tag 관리 | ✅ 완료 |
| 인증 시스템 | JWT + API Key, 프로젝트·멤버십·접근 정책, 관리자 기능 | ✅ 완료 |
| 운영 준비 | Audit Log, Backup, Observability | ✅ 완료 |
| 관리자 콘솔 | 로그인·사용자·프로젝트·멤버 관리 화면 | ✅ 완료 |
| 확장 기능 | pgvector, Revision, Review UI, Export, PR 검증, OpenAPI | ✅ 완료 |

---

## 설계 문서

`docs/` 폴더에 00~11 번호 순으로 전체 설계가 있다.
