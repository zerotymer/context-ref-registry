# 04. REST API

이 문서는 REST API 초안이다.

MVP에서는 REST API가 write/read를 모두 담당하고, MCP는 read-only로 둔다.

## 공통 응답 형식

성공:

```json
{
  "ok": true,
  "data": {}
}
```

실패:

```json
{
  "ok": false,
  "error": {
    "code": "AMBIGUOUS_ALIAS",
    "message": "alias matches multiple entities",
    "details": {}
  }
}
```

## Entity API

### Create Entity

```http
POST /entities
```

Request:

```json
{
  "id": "0d18b76a-6c0e-45b4-9289-6bdfc2e87e5a",
  "type": "UI_AREA",
  "canonical_name": "사용자 검색 조건 영역",
  "description": "사용자 목록 화면 상단의 검색 조건 입력 영역",
  "status": "candidate",
  "confidence": 0.82,
  "metadata": {
    "ui_framework": "react",
    "route_hint": "/users",
    "component_hint": "UserSearchFilter"
  }
}
```

Response:

```json
{
  "ok": true,
  "data": {
    "id": "0d18b76a-6c0e-45b4-9289-6bdfc2e87e5a"
  }
}
```

### Get Entity

```http
GET /entities/{id}
```

Response:

```json
{
  "ok": true,
  "data": {
    "id": "0d18b76a-6c0e-45b4-9289-6bdfc2e87e5a",
    "type": "UI_AREA",
    "canonical_name": "사용자 검색 조건 영역",
    "description": "사용자 목록 화면 상단의 검색 조건 입력 영역",
    "status": "active",
    "metadata": {
      "ui_framework": "react",
      "route_hint": "/users"
    }
  }
}
```

### Update Entity

```http
PATCH /entities/{id}
```

주의:

```text
- id는 변경할 수 없다.
- type 변경은 기본적으로 제한한다.
- canonical_name, description, status, metadata는 변경 가능하다.
```

## Alias API

### Add Alias

```http
POST /entities/{id}/aliases
```

Request:

```json
{
  "locale": "ko",
  "alias": "사용자 검색",
  "is_primary": false
}
```

### List Aliases

```http
GET /entities/{id}/aliases
```

### Resolve Alias

```http
GET /resolve?alias=사용자%20검색&locale=ko&type=FEATURE
```

Response when resolved:

```json
{
  "ok": true,
  "data": {
    "status": "resolved",
    "entity": {
      "id": "1c9323e9-46a4-4665-b2d1-c37e4f3b19e0",
      "type": "FEATURE",
      "canonical_name": "사용자 검색"
    }
  }
}
```

Response when ambiguous:

```json
{
  "ok": true,
  "data": {
    "status": "ambiguous",
    "candidates": [
      {
        "id": "1c9323e9-46a4-4665-b2d1-c37e4f3b19e0",
        "type": "FEATURE",
        "canonical_name": "관리자 사용자 검색",
        "summary": "관리자 사용자 목록에서 조건 검색"
      },
      {
        "id": "84e4cf43-29f8-4e77-92f2-7e4e46f9770e",
        "type": "FEATURE",
        "canonical_name": "고객 사용자 검색",
        "summary": "고객센터 화면에서 사용자 검색"
      }
    ],
    "required_action": "ask_user_to_choose_entity_id"
  }
}
```

## Context API

### Add Context

```http
POST /entities/{id}/contexts
```

Request:

```json
{
  "context_type": "summary",
  "title": "기능 요약",
  "body": "조건에 따라 사용자 목록을 조회하는 기능",
  "language": "ko",
  "source_ref_id": null
}
```

### List Contexts

```http
GET /entities/{id}/contexts
```

Query parameters:

```text
context_type
language
```

## Relation API

### Create Relation

```http
POST /relations
```

Request:

```json
{
  "from_entity_id": "0d18b76a-6c0e-45b4-9289-6bdfc2e87e5a",
  "to_entity_id": "1c9323e9-46a4-4665-b2d1-c37e4f3b19e0",
  "relation_type": "RELATED_TO",
  "description": "검색 조건 영역은 사용자 검색 기능에 사용된다.",
  "confidence": 0.9
}
```

### Get Relations

```http
GET /entities/{id}/relations
```

Query parameters:

```text
direction=out|in|both
relation_type=RELATED_TO
max_depth=1
```

## Search API

### Search Entities

```http
GET /search?q=사용자%20검색&type=FEATURE&limit=10
```

검색 순서 권장:

```text
1. id exact match
2. alias exact match
3. canonical_name partial match
4. context full text search
5. vector search optional
```

## Context Bundle API

```http
POST /context-bundle
```

Request:

```json
{
  "root_ids": [
    "1c9323e9-46a4-4665-b2d1-c37e4f3b19e0"
  ],
  "include_relations": [
    "RELATED_TO",
    "USES",
    "DEPENDS_ON",
    "READS_FROM",
    "WRITES_TO"
  ],
  "include_types": [
    "UI_AREA",
    "FEATURE",
    "INFRA_UNIT",
    "API",
    "CODE_SYMBOL"
  ],
  "max_depth": 2,
  "token_budget": 6000
}
```

Response:

```json
{
  "ok": true,
  "data": {
    "roots": [],
    "entities": [],
    "contexts": [],
    "relations": [],
    "warnings": [],
    "ambiguities": []
  }
}
```

## Batch Ingest API

```http
POST /ingest/batch
```

자세한 형식은 `07-ingest-format.md`를 참고한다.
