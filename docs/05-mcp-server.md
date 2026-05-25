# 05. MCP Server

MVP의 MCP 서버는 read-only로 구현한다.

코딩 에이전트가 registry를 조회해서 작업 컨텍스트를 얻는 것이 목적이다.

## MCP Tool 목록

```text
resolve_alias
get_entity
search_entities
get_related_entities
get_context_bundle
validate_references
```

## Tool: resolve_alias

### 목적

mutable alias를 immutable entity id 후보로 변환한다.

### Input

```json
{
  "alias": "사용자 검색",
  "locale": "ko",
  "type": "FEATURE",
  "scope": null
}
```

### Output: resolved

```json
{
  "status": "resolved",
  "entity": {
    "id": "1c9323e9-46a4-4665-b2d1-c37e4f3b19e0",
    "type": "FEATURE",
    "canonical_name": "사용자 검색"
  }
}
```

### Output: ambiguous

```json
{
  "status": "ambiguous",
  "candidates": [
    {
      "id": "uuid-1",
      "type": "FEATURE",
      "canonical_name": "관리자 사용자 검색",
      "summary": "관리자 화면에서 사용자 조건 검색"
    },
    {
      "id": "uuid-2",
      "type": "FEATURE",
      "canonical_name": "고객센터 사용자 검색",
      "summary": "고객센터 화면에서 사용자 조건 검색"
    }
  ],
  "required_action": "ask_user_to_choose_entity_id"
}
```

### 에이전트 동작 규칙

```text
- status가 ambiguous면 임의 선택하지 않는다.
- 사용자에게 후보를 보여주고 어느 ID인지 확정 질문한다.
- deprecated entity는 기본 후보 우선순위를 낮춘다.
```

## Tool: get_entity

### Input

```json
{
  "id": "1c9323e9-46a4-4665-b2d1-c37e4f3b19e0"
}
```

### Output

```json
{
  "entity": {
    "id": "1c9323e9-46a4-4665-b2d1-c37e4f3b19e0",
    "type": "FEATURE",
    "canonical_name": "사용자 검색",
    "description": "조건에 따라 사용자 목록을 조회하는 기능",
    "status": "active"
  },
  "aliases": {
    "ko": ["사용자 검색", "회원 검색"],
    "en": ["User Search"]
  },
  "metadata": {
    "granularity": "coarse",
    "certainty": "medium"
  },
  "warnings": []
}
```

## Tool: search_entities

### Input

```json
{
  "query": "사용자 목록 화면 검색 조건",
  "types": ["UI_AREA", "FEATURE"],
  "limit": 10
}
```

### Output

```json
{
  "results": [
    {
      "id": "uuid",
      "type": "UI_AREA",
      "canonical_name": "사용자 검색 조건 영역",
      "score": 0.91,
      "match_reason": "alias_exact"
    }
  ]
}
```

## Tool: get_related_entities

### Input

```json
{
  "id": "1c9323e9-46a4-4665-b2d1-c37e4f3b19e0",
  "direction": "both",
  "relation_types": ["RELATED_TO", "USES", "DEPENDS_ON"],
  "max_depth": 1
}
```

### Output

```json
{
  "root_id": "1c9323e9-46a4-4665-b2d1-c37e4f3b19e0",
  "relations": [
    {
      "from_entity_id": "uuid-a",
      "to_entity_id": "uuid-b",
      "relation_type": "RELATED_TO"
    }
  ],
  "entities": []
}
```

## Tool: get_context_bundle

가장 중요한 tool이다.

### Input

```json
{
  "root_ids": [
    "1c9323e9-46a4-4665-b2d1-c37e4f3b19e0"
  ],
  "max_depth": 2,
  "token_budget": 8000,
  "include_types": [
    "UI_AREA",
    "FEATURE",
    "INFRA_UNIT",
    "API",
    "CODE_SYMBOL"
  ],
  "include_relations": [
    "RELATED_TO",
    "USES",
    "DEPENDS_ON",
    "READS_FROM",
    "WRITES_TO"
  ]
}
```

### Output

```json
{
  "roots": [],
  "entities": [],
  "contexts": [],
  "relations": [],
  "warnings": [],
  "ambiguities": []
}
```

## Tool: validate_references

### 목적

에이전트가 작성한 지시서나 작업 계획에 들어 있는 ID/alias가 유효한지 검증한다.

### Input

```json
{
  "references": [
    "FEA-USER-SEARCH",
    "RGN-USER-FILTER",
    "0d18b76a-6c0e-45b4-9289-6bdfc2e87e5a"
  ]
}
```

### Output

```json
{
  "valid": false,
  "resolved": [
    {
      "input": "0d18b76a-6c0e-45b4-9289-6bdfc2e87e5a",
      "status": "resolved",
      "id": "0d18b76a-6c0e-45b4-9289-6bdfc2e87e5a"
    }
  ],
  "ambiguous": [
    {
      "input": "FEA-USER-SEARCH",
      "candidates": ["uuid-1", "uuid-2"]
    }
  ],
  "missing": [
    "RGN-USER-FILTER"
  ]
}
```

## MCP Resource URI

권장 URI 체계:

```text
llmref://entity/{uuid}
llmref://entity/{uuid}/context
llmref://entity/{uuid}/relations
llmref://bundle/{uuid}
llmref://search?q=...
```

## 보안 기본값

```text
- MCP server는 read-only
- write tool은 제공하지 않는다
- deprecated entity를 명확히 표시한다
- secret 값은 반환하지 않는다
- context와 instruction을 구분해 prompt injection 위험을 줄인다
```
