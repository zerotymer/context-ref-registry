# context-ref-registry

코딩 에이전트(Codex, Claude Code, Cursor 등)가 화면(UI_AREA), 기능(FEATURE), 인프라(INFRA_UNIT), API, 코드 심볼을 **UUID 기반으로 안정적으로 참조**할 수 있게 하는 경량 레지스트리 서비스.

문서 파싱은 외부 에이전트가 담당하고, 이 서비스는 정리된 결과를 저장·조회·제공하는 역할만 한다.

---

## 아키텍처

```
외부 Parser/Agent → POST /ingest/batch → Registry (SQLite)
                                              ↓
Coding Agent ← MCP read-only server ← REST API (:8000)

Coding Agent → Next BFF 게이트웨이 (:3000 /api/v1/*) → FastAPI Backend (:8000)   # API Key passthrough

Browser → Next.js Admin UI (:3000, BFF) → FastAPI Backend (:8000)

CI/CD → POST /validate-references → 레지스트리 참조 검증
```

### 공개 엔드포인트 (외부 에이전트용)

| 용도 | URL | 비고 |
|------|-----|------|
| **에이전트 API (권장)** | `https://llm-reg.zerotymer.net/api/v1/*` | Next BFF 게이트웨이 → 백엔드 프록시. API Key passthrough, 응답 봉투 미해제 |
| **백엔드 직접 API (대체)** | `https://llm-api.zerotymer.net/*` | 게이트웨이 우회. `/api/v1` 프리픽스 없음 |

> 에이전트는 **게이트웨이(`llm-reg`)를 우선** 사용하고, 닿지 않을 때만 백엔드 직접
> (`llm-api`)으로 폴백한다. 게이트웨이는 `entities` · `relations` · `search` · `resolve` ·
> `tags` · `context-bundle` · `ingest` · `export` · `validate-references` · `projects`
> 프리픽스만 프록시하며 `auth/*` · `admin/*`은 404로 차단한다.

### 인증 (API Key)

모든 에이전트 HTTP 요청은 API Key로 인증한다. 헤더는 하나뿐이다 (`X-API-Key`는 폐기):

```
Authorization: Bearer crr_<...>
```

키는 관리자가 콘솔 `/admin/api-keys`(또는 `POST /admin/api-keys`)에서 발급한다.
키 하나는 **프로젝트 하나**에 묶이며 scope는 둘 중 하나다:

| scope | 조회 | 변경 (ingest·entity·alias·relation·context·tag) |
|-------|------|------|
| `read` | 자기 프로젝트 + 공개 엔티티 | 403 |
| `write` | 자기 프로젝트 + 공개 엔티티 | 자기 프로젝트 엔티티만 (공개 엔티티 403) |

만료일(`expires_at`)은 선택이며, 평문 키는 발급 시 한 번만 표시된다.
키는 코드에 하드코딩하지 말고 환경변수에서 읽는다.

```bash
curl -H "Authorization: Bearer $REGISTRY_API_KEY" \
  "https://llm-reg.zerotymer.net/api/v1/resolve?alias=사용자%20검색&locale=ko"
```

### 에이전트 스킬

코딩 에이전트가 레지스트리를 활용하는 방법(MCP 도구 7종 · HTTP API · 인증 · 워크플로우)은
[`skill/llm-reference-registry/`](skill/llm-reference-registry/) 스킬 문서를 따른다
(영문 `SKILL.md` / 국문 `SKILL_ko.md`).

---

## 기술 스택

| 레이어 | 스택 |
|--------|------|
| Backend | FastAPI (Python 3.12) + SQLAlchemy 2.x (async) + Alembic |
| DB | SQLite (WAL) + JSON metadata — 단일 파일 `registry.db` |
| Frontend | Next.js 14 + Tailwind CSS (관리자 콘솔, BFF 패턴) |
| Auth | 단일 관리자(환경변수, JWT 쿠키) + 프로젝트 API Key (`read`/`write`) |
| MCP | Python MCP SDK — read-only |
| Package | uv (Python) / pnpm (Node) |
| Deploy | Docker Compose |

---

## 빠른 시작

### Docker Compose (배포 이미지 사용)

아래 `docker-compose.yml`을 사용하면 빌드 없이 바로 실행할 수 있다.

```yaml
services:
  api:
    image: zerotymer/llm-registry-api:latest
    ports:
      - "8000:8000"
    environment:
      ADMIN_PASSWORD: ${ADMIN_PASSWORD:?set ADMIN_PASSWORD}   # 필수 — 커밋 금지
      MCP_ALLOWED_HOSTS: "api:*"                              # 게이트웨이(/api/v1/mcp) → api:8000
      # DATABASE_URL 기본값: sqlite+aiosqlite:////data/registry.db
    volumes:
      - registry_data:/data

  frontend:
    image: zerotymer/llm-registry-front:latest
    ports:
      - "3000:3000"
    environment:
      BACKEND_API_URL: http://api:8000
    depends_on:
      - api

volumes:
  registry_data:
```

```bash
# 실행 (ADMIN_PASSWORD는 셸 환경변수 또는 .env 파일로 전달)
ADMIN_PASSWORD='<강한 비밀번호>' docker compose up -d
```

> 저장소를 직접 클론해 빌드할 때는 `backend/.env`(`backend/.env.example` 참고)에 `ADMIN_PASSWORD`를
> 넣고 `docker compose -f docker-compose.yml up -d`로 실행한다. 그냥 `docker compose up`은
> `docker-compose.override.yml`(dev: `--reload` + 소스 바인드)까지 합쳐 실행한다.

| 서비스 | 주소 |
|--------|------|
| Backend API | http://localhost:8000 |
| API 문서 | http://localhost:8000/docs |
| Frontend | http://localhost:3000 |
| 에이전트 API 게이트웨이 | http://localhost:3000/api/v1/* (백엔드 동일 경로 프록시, API Key passthrough) |

---

### 환경 변수

> **DB 스키마는 컨테이너 기동 시 자동 적용된다.** `api` 컨테이너 entrypoint가 앱 실행 전
> `alembic upgrade head`를 수행하므로 빈 볼륨에서도 스키마가 자동 생성된다. 이미 최신이면 no-op.

#### Backend (`api` 서비스)

| 변수 | 필수 | 기본값 | 설명 |
|------|:----:|--------|------|
| `ADMIN_PASSWORD` | ✅ | — | 관리자 비밀번호. 없으면 로그인이 막히고(503) 시작 시 경고 로그 |
| `ADMIN_LOGIN_ID` | | `admin` | 관리자 아이디 |
| `DATABASE_URL` | | `sqlite+aiosqlite:////data/registry.db` | SQLite 파일 경로 |
| `JWT_SECRET` | | 기동 시 자동 생성 | 고정하면 재기동 후에도 관리자 세션 유지 |
| `MCP_ALLOWED_HOSTS` | | — | `/mcp`가 추가로 받을 Host 헤더 (쉼표 구분, `api:*`·`mcp.example.com` 형식). `localhost`는 항상 허용, 그 외는 421. compose는 게이트웨이용 `api:*`를 설정 |

> `JWT_SECRET`을 지정하지 않으면 `entrypoint.sh`가 기동할 때마다 새로 만들어 모든 워커가 공유한다.
> 재기동하면 관리자 세션이 끊긴다(API Key에는 영향 없음). 알고리즘(`HS256`)과 만료(7일)는 코드에 고정.

#### Frontend (`frontend` 서비스)

| 변수 | 필수 | 기본값 | 설명 |
|------|:----:|--------|------|
| `BACKEND_API_URL` | ✅ | — | Frontend → Backend 내부 URL (예: `http://api:8000`) — 백엔드 포트 변경 시 조정 |

### 백업

별도 백업 서비스는 없다. `api`를 멈춘 뒤 볼륨 안의 `registry.db`, `registry.db-wal`, `registry.db-shm`
세 파일을 함께 복사한다.

```bash
docker compose stop api
docker run --rm -v context-ref-registry_registry_data:/data -v "$PWD":/backup alpine \
  sh -c 'cp /data/registry.db* /backup/'
docker compose start api
```

### 관리자 계정

관리자는 **1명**이며 계정은 환경변수(`ADMIN_LOGIN_ID` / `ADMIN_PASSWORD`)로만 정한다.
사용자 테이블·회원 가입·비밀번호 변경 UI는 없다. 비밀번호를 바꾸려면 `.env`를 고치고 재기동한다.

---

## 개발 환경

### Backend

```bash
cd backend
uv pip install -e ".[dev]"
uvicorn app.main:app --reload --port 8000

# 테스트 (임시 SQLite 파일 DB를 자동 생성)
.venv/bin/pytest tests/ -q
# 현재: 300 passed

# 의존성을 바꾼 뒤 (pyproject.toml 수정 후)
make lock   # uv.lock(로컬 전용, gitignore) 갱신 + requirements.lock(커밋 대상) 재생성
```

> `uv.lock`은 로컬 패키지 저장소 주소가 기록되므로 커밋하지 않는다. Docker 이미지와 CI는 버전과 sha256 해시만 담긴
> `backend/requirements.lock` / `requirements-dev.lock`을 `pip --require-hashes`로 설치한다.

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

- alias exact match → canonical_name 부분 일치 (대소문자 무시)
- `GET /search?q=` — 키워드 검색 (시맨틱 검색은 필요 시 sqlite-vec 기준으로 재설계)

### Context Bundle

- `POST /context-bundle` (`root_ids`, `max_depth`, `token_budget`) — BFS traversal, 토큰 예산 제한

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

streamable-http transport로 `api` 앱의 `/mcp`에 마운트된다(stdio 폐기). MCP 클라이언트는
`http://<host>:8000/mcp`로 접속하며 `Authorization: Bearer <api-key>` 헤더가 필요하다
(`read`·`write` 키 모두 허용). 모든 도구는 API Key의 프로젝트 범위로 결과를 필터링한다.

read-only 도구 7종 제공: `resolve_alias`, `get_entity`, `search_entities`,
`get_related_entities`, `get_context_bundle`, `get_entity_history`, `validate_references`.

### 관리자 콘솔

- 단일 관리자 로그인 (JWT 쿠키), 프로젝트 관리, API Key 발급·폐기 (프로젝트·scope·만료일)
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
| 인증 시스템 | 단일 관리자(환경변수) + 프로젝트 API Key(`read`/`write`) | ✅ 완료 |
| 운영 준비 | Audit Log, Observability (백업은 DB 파일 복사) | ✅ 완료 |
| 관리자 콘솔 | 로그인·프로젝트·API Key 관리 화면 | ✅ 완료 |
| 확장 기능 | Revision, Review UI, Export, PR 검증, OpenAPI | ✅ 완료 |
| SQLite 전환·경량화 | PostgreSQL → SQLite(WAL), 컨테이너 4→2개, 단일 관리자 인증 | ✅ 완료 |
| 확장 기능 — pgvector | 폐기. 필요해지면 sqlite-vec 기준으로 재설계 | ✖ 폐기 |
| 배포 운영 | 컨테이너 startup 시 DB 스키마 자동 적용 (`alembic upgrade head`, 멱등) | ✅ 완료 |
| 에이전트 게이트웨이 | Next BFF `/api/v1/*` → 백엔드 프록시 (API Key passthrough) | ✅ 완료 |
| MCP HTTP transport | `/mcp` streamable-http + BFF 스트리밍 프록시 `/api/v1/mcp` | ✅ 완료 |
| 참조·Ingest 확장 | 짧은 식별자 `PROJECT_ID-TYPE-N`, ingest 식별자 반환, UI_AREA 목업 HTML | ✅ 완료 |
| Bundle Graph 탭 | `/bundle` AntV G6 d3-force 관계도 | ✅ 완료 |

---

## 설계 문서

`docs/` 폴더에 00~11 번호 순으로 전체 설계가 있다.
