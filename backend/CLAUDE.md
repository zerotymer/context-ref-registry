# CLAUDE.md — backend/

FastAPI + SQLAlchemy 2.x 백엔드. 루트 CLAUDE.md의 내용을 보완하는 백엔드 전용 가이드.

## 개발 환경

```bash
# 의존성 설치 (backend/ 에서)
uv pip install -e ".[dev]"

# 개발 서버 (hot-reload)
uvicorn app.main:app --reload --port 8000

# 테스트 — 반드시 .venv 파이썬 사용
.venv/bin/pytest tests/ -q
.venv/bin/pytest tests/test_alias_resolve.py -v     # 단일 파일
.venv/bin/pytest tests/ -k "ambiguous" -v           # 키워드 필터

# DB 마이그레이션
alembic upgrade head
alembic revision --autogenerate -m "describe change"

# MCP 서버 단독 실행 (stdio)
python -m app.mcp
```

## 환경변수

`.env.example`을 복사해서 `.env` 생성:

```
DATABASE_URL=postgresql+asyncpg://llmref:llmref@localhost:5432/llmref
TEST_DATABASE_URL=postgresql+asyncpg://llmref:llmref@localhost:5432/llmref_test
```

테스트는 `TEST_DATABASE_URL`을 우선 사용하며, `conftest.py`에서 `os.environ["DATABASE_URL"]`에 주입한다.

## 레이어 구조 및 규칙

```
api/        → HTTP 요청/응답 변환만. 비즈니스 로직 없음.
service/    → 비즈니스 로직. 트랜잭션 경계는 service에서 관리.
repository/ → SQLAlchemy 쿼리만. session을 외부에서 주입받음.
domain/     → enums, ORM models, Pydantic schemas. 순수 데이터 정의.
```

- **service는 repository를 직접 new** (`EntityRepository(session)`) — DI 컨테이너 없음.
- **API 에러는 `RegistryError`** (`app/exceptions.py`)를 raise. `main.py`의 핸들러가 표준 JSON으로 변환.
- **session은 `async with async_session_factory() as session`** 패턴 사용. 커밋은 service에서.

## 도메인 enum 값 (코드 작성 시 참조)

```python
EntityType:   UI_AREA | FEATURE | INFRA_UNIT | API | CODE_SYMBOL
EntityStatus: candidate | active | deprecated | archived
ContextType:  summary | details | business_rule | validation_rule |
              implementation_hint | security_note | infra_note |
              compatibility_note | exception_case
RelationType: CONTAINS | RELATED_TO | USES | IMPLEMENTED_BY |
              READS_FROM | WRITES_TO | DEPENDS_ON | CALLS
Locale:       ko | en
```

## API 엔드포인트 목록

| 메서드 | 경로 | 설명 |
|--------|------|------|
| POST | `/entities` | entity 생성 (id 지정 가능) |
| GET | `/entities/{id}` | entity 조회 |
| PATCH | `/entities/{id}` | entity 수정 (id·type 변경 불가) |
| POST | `/entities/{id}/aliases` | alias 추가 |
| GET | `/entities/{id}/aliases` | alias 목록 |
| GET | `/resolve` | alias → entity resolve |
| POST | `/entities/{id}/contexts` | context 추가 |
| GET | `/entities/{id}/contexts` | context 목록 |
| POST | `/relations` | relation 생성 |
| GET | `/entities/{id}/relations` | relation 목록 (direction, max_depth) |
| GET | `/search?q=&types=&limit=` | entity 검색 (alias exact → canonical partial) |
| POST | `/context-bundle` | BFS context bundle |
| POST | `/ingest/batch` | 일괄 ingest |
| GET | `/health` | 헬스체크 |

## 핵심 불변 규칙

- `entity.id` (UUID)는 생성 후 절대 변경 금지. PATCH에서 `id`·`type` 필드 수신 시 무시.
- alias는 unique 제약 없음. 중복 resolve 시 `ambiguous` 반환 — 임의 선택 금지.
- deprecated entity는 DELETE 금지. `status=deprecated` + `replacement_entity_id` 기록.
- MCP tool은 read-only만. write tool 추가 금지.

## Batch Ingest 검증 순서

`POST /ingest/batch` 처리 흐름:

1. `source_ref` upsert (같은 URI면 재사용)
2. entity upsert — id 있으면 update, 없으면 insert. **type 변경 시 400 `TYPE_CHANGE_FORBIDDEN`**
3. alias upsert — `(entity_id, locale, alias)` 조합이 active면 스킵
4. context insert
5. relation 검증 — `from_entity_id`/`to_entity_id`가 배치 내부 또는 DB에 존재해야 함. 없으면 400 `INVALID_RELATION_TARGET`
6. relation insert

## Context Bundle BFS

`POST /context-bundle` 알고리즘:

1. `root_ids` 존재 검증 → 없으면 404
2. root entity 조회
3. BFS로 relation graph 탐색 (`max_depth` 제한)
4. `include_types` / `include_relations` 필터 적용
5. 모든 entity의 context 조회
6. `token_budget` 초과 시 우선순위 컷:
   `summary > business_rule > validation_rule > implementation_hint > security_note > infra_note > details > compatibility_note > exception_case`
7. deprecated entity → `warnings`에 추가 (`replacement_entity_id` 포함)

## 테스트 구조

```
conftest.py          DB 픽스처 (schema drop/create, table clean), docs/10 예제 shared fixture
test_entity_api.py   Entity CRUD, PATCH 제한, deprecated
test_alias_resolve.py ambiguous/resolved/not_found, locale/type 필터
test_context_api.py  Context 추가/조회, 필터
test_context_bundle.py depth, token_budget, deprecated warning
test_ingest_batch.py upsert, type 변경 금지, relation 검증
test_mcp_tools.py    MCP 6개 tool 직접 호출
test_domain_schemas.py Pydantic 스키마 검증
test_examples.py     docs/10 예제 기반 DoD 통합 테스트
test_search_api.py   GET /search (alias exact, canonical partial, type filter)
```

테스트는 **실제 PostgreSQL**(TEST_DATABASE_URL)에서 실행. mock DB 사용 금지.

각 테스트는 `_clean_tables` fixture로 테이블 전체 truncate 후 실행.

## 주의사항
- MCP server는 `stdio` transport로 실행 (`python -m app.mcp` → `app/mcp/__main__.py`). 포트 미사용, 클라이언트가 프로세스를 spawn. docker-compose `mcp` 서비스도 stdio (`stdin_open: true`).
- `pyproject.toml`의 `mcp>=1.0.0` 의존성은 시스템 Python이 아닌 `.venv`에만 설치됨 — 항상 `.venv/bin/python` 사용.
