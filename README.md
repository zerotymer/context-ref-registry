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

```bash
# 전체 스택 실행
docker compose up -d
```

| 서비스 | 주소 |
|--------|------|
| Backend API | http://localhost:8000 |
| API 문서 | http://localhost:8000/docs |
| Frontend | http://localhost:3000 |
| PostgreSQL | localhost:5432 |

### 환경 변수

`.env.example`을 복사 후 값 설정:

```bash
cp .env.example .env
```

주요 항목:

| 변수 | 설명 |
|------|------|
| `DATABASE_URL` | PostgreSQL 접속 URL |
| `SECRET_KEY` | JWT 서명 키 |
| `BOOTSTRAP_ADMIN_LOGIN_ID` | 최초 관리자 계정 아이디 (기본값: `admin`) |
| `BOOTSTRAP_ADMIN_PASSWORD` | 최초 관리자 계정 비밀번호 (기본값: `admin`) |
| `OPENAI_API_KEY` | pgvector 시맨틱 검색용 (선택, 미설정 시 키워드 검색만) |

### 기본 관리자 계정

서버 최초 기동 시 관리자 계정이 자동으로 생성됩니다:

| 항목 | 값 |
|------|-----|
| 아이디 | `admin` |
| 비밀번호 | `admin` |

> **보안 주의**: 최초 로그인 후 반드시 비밀번호를 변경하세요. 로그인 시 비밀번호 변경 화면으로 자동 이동됩니다. 비밀번호 변경 시 기존 API 키가 모두 삭제됩니다.

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
