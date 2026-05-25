# 08. Implementation Plan

## 목표

MVP 목표는 다음이다.

```text
- Codex가 생성한 entity 후보를 저장한다.
- UUID 기반으로 entity를 조회한다.
- alias로 entity 후보를 resolve한다.
- 관련 context bundle을 제공한다.
- MCP read-only server를 제공한다.
```

## 추천 기술 스택

### Backend

둘 중 하나를 선택한다.

```text
FastAPI:
- MVP 속도 빠름
- MCP Python SDK와 같이 쓰기 좋음
- Python 기반 에이전트/embedding 처리와 잘 맞음

Spring Boot:
- 장기 운영, 권한, 감사 로그, 엔터프라이즈 구조에 강함
- 사용자가 Java/Spring에 익숙하면 적합
```

MVP는 FastAPI 추천.

### DB

```text
PostgreSQL
pgvector optional
```

### Deployment

```text
Docker Compose
```

## Repository 구조 예시

FastAPI 기준:

```text
llm-ref-registry/
  README.md
  docker-compose.yml
  pyproject.toml

  app/
    main.py
    config.py

    api/
      entities.py
      aliases.py
      contexts.py
      relations.py
      search.py
      ingest.py
      bundles.py

    domain/
      models.py
      enums.py
      schemas.py

    repository/
      entity_repository.py
      alias_repository.py
      context_repository.py
      relation_repository.py

    service/
      entity_service.py
      alias_service.py
      context_service.py
      relation_service.py
      bundle_service.py
      search_service.py
      ingest_service.py

    mcp/
      server.py
      tools.py

    db/
      session.py
      migrations/

  tests/
    test_entity_api.py
    test_alias_resolve.py
    test_context_bundle.py
    test_ingest_batch.py
```

## 구현 순서

### Step 1. DB schema 작성

```text
- entity
- entity_alias
- entity_context
- entity_relation
- entity_metadata
- source_ref
```

### Step 2. Domain enum 정의

```text
EntityType
EntityStatus
ContextType
RelationType
Locale
```

### Step 3. Entity CRUD 구현

```text
POST /entities
GET /entities/{id}
PATCH /entities/{id}
```

### Step 4. Alias API 구현

```text
POST /entities/{id}/aliases
GET /entities/{id}/aliases
GET /resolve
```

중요:

```text
alias resolve 결과는 not_found/resolved/ambiguous로 분리한다.
```

### Step 5. Context API 구현

```text
POST /entities/{id}/contexts
GET /entities/{id}/contexts
```

### Step 6. Relation API 구현

```text
POST /relations
GET /entities/{id}/relations
```

### Step 7. Batch Ingest 구현

```text
POST /ingest/batch
```

검증:

```text
- 같은 batch 내부의 relation target 확인
- 기존 DB entity 확인
- type/status/context_type 검증
```

### Step 8. Context Bundle 구현

```text
POST /context-bundle
```

알고리즘:

```text
1. root_ids 검증
2. root entity 조회
3. relation graph를 max_depth까지 탐색
4. include_types/include_relations 필터 적용
5. contexts 조회
6. token_budget 기준 우선순위 적용
7. deprecated warning 생성
8. JSON 응답 생성
```

### Step 9. MCP Server 구현

read-only tool:

```text
resolve_alias
get_entity
search_entities
get_related_entities
get_context_bundle
validate_references
```

### Step 10. 테스트 작성

필수 테스트:

```text
- UUID id로 entity 조회 가능
- alias 중복 시 ambiguous 반환
- deprecated entity warning
- context bundle depth 제한
- batch ingest 성공
- batch ingest relation target 누락 실패
```

## MVP 제외 항목

다음은 초기 구현에서 제외한다.

```text
- 지침서 자동 생성
- PDF 파싱
- OCR
- Figma 직접 연동
- 코드 심볼 자동 분석
- Jira/Confluence/Notion 연동
- PR 검증
- 복잡한 graph DB
```

## 추후 확장

```text
- pgvector semantic search
- revision history
- review UI
- AGENTS.md export
- OpenAPI export
- GitHub PR 검증
- code symbol analyzer
- source permission sync
```
