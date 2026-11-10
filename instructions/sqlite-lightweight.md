---
uuid: 8607659b-324e-4cea-8bea-be2a9c51aa34
title: "PostgreSQL → SQLite 전환 및 배포 경량화"
status: in-progress
created: 2026-11-11
completed:
branch: feat/sqlite-lightweight
ref_docs:
  - docs/ (DB·배포 관련 설계 문서)
  - instructions/deploy-build.md
prerequisite: none
---

# PostgreSQL → SQLite 전환 및 배포 경량화

## 목적

1. DB를 PostgreSQL 16에서 SQLite(WAL)로 바꿔 컨테이너를 4개(postgres·api·frontend·backup)에서 2개(api·frontend)로 줄인다.
2. 검토 때 나온 경량화 방안(compose dev 분리, API 이미지 축소, 미사용 의존성 제거)을 반영한다.

## 결정 사항 (사용자 확정 2026-11-11)

| 항목 | 결정 |
|------|------|
| 데이터 마이그레이션 | **하지 않음.** 기존 PG 데이터는 이관하지 않고 새 SQLite DB로 시작한다 |
| 백업 | **기능 제거.** DB 파일(`registry.db`, `-wal`, `-shm`)을 복사하는 것으로 대신한다. `backup/` 컨테이너 삭제 |
| 경량화 방안 | 검토안 1~4 모두 수용 |
| 인증 체계 | **이 지시서 범위 밖.** 별도 지시서에서 다룬다. 여기서는 타입 교체(`scopes` ARRAY→JSON)만 하고 인증 로직은 건드리지 않는다 |
| pgvector 백로그 | `feat/ext-pgvector`는 폐기 대상이다. 벡터 검색이 다시 필요해지면 sqlite-vec 기준으로 새로 설계한다 |

## PG 전용 기능 → SQLite 대체 목록

| # | 현재 | 위치 | 대체 |
|---|------|------|------|
| 1 | `pg_advisory_xact_lock(hashtext(..))` | `entity_repository.py:63` | 삭제. 쓰기 트랜잭션 직렬화(Step 3)와 `uq_entity_short_seq` 제약으로 순번 중복 방지 |
| 2 | `JSONB` ×5 | `models.py` | `sa.JSON` |
| 3 | `ARRAY(String(50))` (`api_key.scopes`) | `models.py:242` | `sa.JSON` (list) |
| 4 | `postgresql.UUID(as_uuid=True)` | `models.py` | `sa.Uuid` |
| 5 | `pg_insert(..).on_conflict_do_nothing(constraint="uq_entity_tag")` | `ingest_service.py:266` | `sqlite.insert(..).on_conflict_do_nothing(index_elements=["entity_id", "tag"])` |
| 6 | GIN 인덱스 `idx_entity_metadata_gin` | 마이그레이션 001 | 삭제 (사용하는 쿼리 없음) |
| 7 | `DateTime(timezone=True)` | 모든 timestamp | SQLite는 tz를 버림 → UTC aware 값을 돌려주는 `TypeDecorator` 필요 |
| 8 | `ilike` | user/project/api_key/entity repository | 변경 없음 (SQLAlchemy가 `lower() LIKE lower()`로 컴파일) |

## 변경 파일 목록

| 파일 | 변경 내용 |
|------|-----------|
| `backend/pyproject.toml`, `uv.lock` | `asyncpg` 제거, `aiosqlite` 추가 |
| `backend/app/config.py` | 기본 `database_url` → `sqlite+aiosqlite:////data/registry.db` |
| `backend/app/db/session.py` | SQLite PRAGMA(WAL·foreign_keys·busy_timeout) + 쓰기 직렬화 |
| `backend/app/domain/models.py` | 타입 교체, `UtcDateTime` TypeDecorator |
| `backend/app/repository/entity_repository.py` | advisory lock 삭제 |
| `backend/app/service/ingest_service.py` | sqlite insert로 교체 |
| `backend/app/db/migrations/env.py` | `render_as_batch=True` |
| `backend/app/db/migrations/versions/*` | 001~012 삭제 → `001_baseline.py` 1개 |
| `backend/tests/conftest.py` | SQLite 임시 파일 DB |
| `backend/tests/test_migrations.py` | asyncpg 제거, 임시 SQLite 파일로 재작성 |
| `backend/tests/test_sqlite_specific.py` (신규) | UTC 반환, short_seq 동시 발급, FK cascade |
| `backend/Dockerfile` | `uv sync --frozen --no-dev` 멀티스테이지 |
| `docker-compose.yml` | postgres·backup 제거, `registry_data:/data` 볼륨 |
| `docker-compose.override.yml` (신규) | `--reload` + `./backend:/app` 바인드 (dev 전용) |
| `backup/` | 디렉토리 삭제 |
| `frontend/package.json`, `pnpm-lock.yaml` | `@tanstack/react-query-devtools` 제거 |
| `CLAUDE.md`, `AGENTS.md`, `instructions/README.md`, `backend/CLAUDE.md`, 관련 `docs/` | 기술 스택·구조 동기화 |

## Step-by-Step 구현 지침

> 패키지 설치는 **개인 Nexus 인덱스로만** 한다(`~/.config/uv/uv.toml`의 `internal` 기본 인덱스, pnpm은 기존 registry 설정). 공개 PyPI/npm 직접 설치 금지.
> SQLAlchemy·aiosqlite·Alembic API는 구현 전에 `ctx7`로 최신 문서를 확인한다.

### Step 1 — 의존성 교체
- [ ] `cd backend && uv remove asyncpg && uv add aiosqlite`
- [ ] `cd frontend && pnpm remove @tanstack/react-query-devtools` (src에서 import하는 곳 없음 확인 완료)
- [ ] `cd backend && uv sync` — 로컬 `.venv`에 남은 미선언 패키지(openai, numpy 등) 정리

### Step 2 — 모델 타입 교체
- [ ] `from sqlalchemy.dialects.postgresql import ...` 제거
- [ ] `UUID(as_uuid=True)` → `sa.Uuid`, `JSONB` → `sa.JSON`, `ARRAY(String(50))` → `sa.JSON`
- [ ] `UtcDateTime(TypeDecorator)` 추가: 저장할 때 UTC로 바꾸고, 읽을 때 `tzinfo=UTC`를 붙인다. 모든 `DateTime(timezone=True)`를 교체한다
- [ ] `server_default=func.now()`는 유지 (SQLite `CURRENT_TIMESTAMP` = UTC)

### Step 3 — 엔진 설정 & 쓰기 직렬화 (`session.py`)
- [ ] `connect` 이벤트에서 `PRAGMA journal_mode=WAL`, `PRAGMA foreign_keys=ON`(**필수**: 이게 없으면 `ondelete` CASCADE/SET NULL이 동작하지 않음), `PRAGMA busy_timeout=5000`
- [ ] 트랜잭션을 `BEGIN IMMEDIATE`로 시작한다 (SQLAlchemy 문서의 pysqlite/aiosqlite "serializable isolation / savepoints" 레시피: `isolation_level=None` + `begin` 이벤트에서 직접 BEGIN을 실행)
  - 이유: WAL에서 기본 deferred 트랜잭션은 "읽은 뒤 쓰기"가 다른 writer와 겹치면 `SQLITE_BUSY_SNAPSHOT`으로 즉시 실패하고 busy_timeout도 적용되지 않는다
  - `# ponytail: global write lock per transaction — split read/write sessions if read latency under ingest load matters`
- [ ] `entity_repository.next_short_seq`의 advisory lock 호출 삭제 (docstring 갱신)

### Step 4 — ingest upsert 교체
- [ ] `ingest_service.py`: `from sqlalchemy.dialects.sqlite import insert as sqlite_insert` → `.on_conflict_do_nothing(index_elements=["entity_id", "tag"])`

### Step 5 — 마이그레이션 스쿼시
- [ ] `versions/001~012` 삭제
- [ ] `env.py` 두 `context.configure(...)`에 `render_as_batch=True`
- [ ] 빈 SQLite 파일 대상 `alembic revision --autogenerate -m baseline` → `001_baseline.py`로 정리 (revision="001", GIN 인덱스 없음, 모든 UniqueConstraint 이름 유지: `uq_entity_tag`, `uq_entity_short_seq`, `uq_entity_metadata_type` 등)
- [ ] autogenerate 결과와 `Base.metadata`가 일치하는지 `alembic check`로 확인

### Step 6 — 테스트
- [ ] `conftest.py`: 기본 URL을 `sqlite+aiosqlite:///{tmp}/test.db`로 변경 (`TEST_DATABASE_URL` override는 유지). `:memory:`는 커넥션마다 DB가 분리되므로 쓰지 않는다
- [ ] `test_migrations.py`: asyncpg 의존 제거 → 임시 디렉토리의 새 DB 파일에 `alembic upgrade head` 2회 실행(멱등) 후 `EXPECTED_TABLES` 확인
- [ ] 신규 `test_sqlite_specific.py` (최소 3건)
  - API 응답의 `created_at`에 tz(`+00:00` 또는 `Z`)가 붙는지
  - 같은 `(project_id, type)`로 엔티티 N개를 `asyncio.gather`로 동시 생성 → `short_seq`가 1..N이고 중복 없음
  - 프로젝트/엔티티 삭제 시 FK cascade 동작 (`foreign_keys=ON` 회귀 방지)
- [ ] `cd backend && .venv/bin/pytest tests/` 전부 통과 (기준 354 + 신규), `cd frontend && pnpm test` 30 통과

### Step 7 — Docker / Compose
- [ ] `docker-compose.yml`: `postgres`·`backup` 서비스와 `postgres_data`·`backup_data` 볼륨 삭제, api에서 `depends_on: postgres` 삭제, `DATABASE_URL=sqlite+aiosqlite:////data/registry.db`, `registry_data:/data` 볼륨 추가
- [ ] `docker-compose.override.yml` 신규: api의 `command: uvicorn ... --reload`와 `./backend:/app` 바인드만 옮긴다 (운영은 `docker compose -f docker-compose.yml up`)
- [ ] `backup/` 디렉토리 삭제. 백업은 "api 정지 후 볼륨 내 `registry.db*` 복사"로 문서화
- [ ] `backend/Dockerfile`: builder 스테이지에서 `uv sync --frozen --no-dev --no-editable`, runtime 스테이지는 `python:3.12-slim`에 `.venv`만 복사. Nexus 인덱스 인증은 BuildKit secret(`--mount=type=secret`)으로 넘기고 이미지 레이어에 남기지 않는다. `/data` 디렉토리 생성·권한 처리
- [ ] 목표: API 이미지 383MB → 측정 후 결과 기록
- [ ] `docker compose up -d` → 빈 볼륨에서 `entrypoint.sh`의 `alembic upgrade head`로 스키마가 자동 생성되는지, `/health` 200, 프론트 로그인 확인

### Step 8 — 문서 동기화
- [ ] `CLAUDE.md`: 기술 스택(DB), Docker Compose 서비스, 구현 현황(pgvector 행 → 폐기/재설계), 프로젝트 구조(`backup/` 제거)
- [ ] `AGENTS.md`, `instructions/README.md`, `backend/CLAUDE.md`, `docs/` 중 PostgreSQL을 언급하는 문서
- [ ] `instructions/deploy-build.md`: 이미지 빌드 시 secret 전달 방법 반영

## 범위 밖

- 인증 체계 개편 (별도 지시서)
- 기존 PG 데이터 이관
- 읽기/쓰기 세션 분리 (부하 문제가 실제로 생기면 그때 진행)

## 완료 기준

- 백엔드·프론트 테스트 전부 통과
- `docker compose up -d`로 컨테이너 2개 기동, 빈 볼륨에서 스키마 자동 생성
- 코드(`backend/app`)에 `postgresql`/`asyncpg` 참조 0건: `grep -rn "postgresql\|asyncpg" backend/app` 결과 없음
