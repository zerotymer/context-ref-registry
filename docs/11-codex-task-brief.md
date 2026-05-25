# 11. Codex Task Brief

이 문서는 Codex 등 코딩 에이전트에게 구현 작업을 맡길 때 사용할 수 있는 작업 지시 초안이다.

## 목표

LLM Reference Registry MVP를 구현한다.

이 서비스는 화면설계서/기획서/인프라 문서를 파싱한 결과를 저장하고, 코딩 에이전트가 UUID 기반으로 context를 조회할 수 있게 제공한다.

## 구현 범위

### 필수 구현

```text
1. Entity 저장/조회
2. Alias 저장/resolve
3. Context 저장/조회
4. Relation 저장/조회
5. Batch ingest API
6. Context bundle API
7. Read-only MCP server
```

### 필수 Entity Type

```text
UI_AREA
FEATURE
INFRA_UNIT
```

### 필수 상태값

```text
candidate
active
deprecated
archived
```

### 필수 Relation Type

```text
CONTAINS
RELATED_TO
DEPENDS_ON
USES
READS_FROM
WRITES_TO
```

## 기술 스택

MVP는 다음 기준으로 구현한다.

```text
Language: Python
Framework: FastAPI
Database: PostgreSQL
ORM: SQLAlchemy 2.x
Migration: Alembic
MCP: Python MCP SDK
Deployment: Docker Compose
```

pgvector는 optional로 두고, 초기 구현에서는 full text 또는 단순 검색으로 시작한다.

## 주요 설계 규칙

```text
- entity.id는 UUID이며 변경 불가하다.
- alias는 중복 가능하다.
- alias resolve 결과가 여러 개면 ambiguous를 반환한다.
- ambiguous 상태에서는 임의 선택하지 않는다.
- MCP server는 read-only다.
- deprecated entity는 삭제하지 않고 warning으로 표시한다.
- secret 값은 저장하지 않는다.
```

## API 구현 목록

```text
POST   /entities
GET    /entities/{id}
PATCH  /entities/{id}

POST   /entities/{id}/aliases
GET    /entities/{id}/aliases
GET    /resolve

POST   /entities/{id}/contexts
GET    /entities/{id}/contexts

POST   /relations
GET    /entities/{id}/relations

GET    /search
POST   /context-bundle
POST   /ingest/batch
```

## MCP Tool 구현 목록

```text
resolve_alias
get_entity
search_entities
get_related_entities
get_context_bundle
validate_references
```

## 테스트 요구사항

다음 테스트를 반드시 작성한다.

```text
1. entity 생성 후 UUID로 조회된다.
2. alias가 중복되면 resolve_alias가 ambiguous를 반환한다.
3. alias가 하나만 매칭되면 resolved를 반환한다.
4. 존재하지 않는 alias는 not_found를 반환한다.
5. context bundle은 root entity와 직접 relation entity를 포함한다.
6. max_depth가 relation 탐색에 적용된다.
7. deprecated entity가 bundle에 포함되면 warning이 반환된다.
8. batch ingest에서 relation target이 없으면 실패한다.
9. batch ingest에서 같은 batch 내부 entity를 relation target으로 사용할 수 있다.
10. MCP get_entity는 REST get_entity와 같은 핵심 데이터를 반환한다.
```

## 제외 범위

다음은 구현하지 않는다.

```text
- PDF 파싱
- OCR
- Figma 연동
- Jira/Confluence/Notion 연동
- 지침서 자동 생성
- 코드 자동 수정
- PR 검증
- graph DB
```

## 산출물

```text
- 동작하는 FastAPI 서버
- 동작하는 MCP 서버
- PostgreSQL schema migration
- Docker Compose
- README
- API 테스트
```

## 완료 기준

```text
1. docker compose up으로 API와 DB가 실행된다.
2. batch ingest sample이 성공한다.
3. resolve alias ambiguous case가 동작한다.
4. context bundle API가 JSON을 반환한다.
5. MCP tool로 get_context_bundle을 호출할 수 있다.
6. pytest가 통과한다.
```
