# 06. Context Bundle

Context Bundle은 코딩 에이전트가 특정 ID 기준으로 작업할 때 필요한 관련 정보를 묶어서 제공하는 응답이다.

단일 entity 조회와 다르다.

```text
get_entity:
- entity 자체 정보 조회

get_context_bundle:
- entity + context + relation + 관련 entity + warnings 제공
```

## 목적

코딩 에이전트가 다음과 같은 작업을 할 수 있게 한다.

```text
- 어떤 화면 영역을 수정해야 하는지 파악
- 어떤 기능과 관련되는지 파악
- 어떤 인프라 구성에 의존하는지 파악
- 관련 API, 코드 심볼, 테스트를 추후 연결
- deprecated 또는 ambiguous context를 피함
```

## Request

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
  "token_budget": 6000,
  "language": "ko"
}
```

## Response

```json
{
  "roots": [
    {
      "id": "1c9323e9-46a4-4665-b2d1-c37e4f3b19e0",
      "type": "FEATURE",
      "canonical_name": "사용자 검색",
      "status": "active"
    }
  ],
  "entities": [
    {
      "id": "0d18b76a-6c0e-45b4-9289-6bdfc2e87e5a",
      "type": "UI_AREA",
      "canonical_name": "사용자 검색 조건 영역",
      "status": "active"
    }
  ],
  "contexts": [
    {
      "entity_id": "1c9323e9-46a4-4665-b2d1-c37e4f3b19e0",
      "context_type": "summary",
      "body": "조건에 따라 사용자 목록을 조회하는 기능"
    },
    {
      "entity_id": "0d18b76a-6c0e-45b4-9289-6bdfc2e87e5a",
      "context_type": "implementation_hint",
      "body": "React 컴포넌트 UserSearchFilter 후보"
    }
  ],
  "relations": [
    {
      "from_entity_id": "0d18b76a-6c0e-45b4-9289-6bdfc2e87e5a",
      "to_entity_id": "1c9323e9-46a4-4665-b2d1-c37e4f3b19e0",
      "relation_type": "RELATED_TO"
    }
  ],
  "warnings": [],
  "ambiguities": []
}
```

## Bundle 생성 규칙

### 1. Root entity 포함

root_ids에 해당하는 entity는 항상 포함한다.

### 2. Context 우선순위

token_budget이 부족하면 다음 순서로 포함한다.

```text
1. summary
2. business_rule
3. validation_rule
4. implementation_hint
5. security_note
6. infra_note
7. details
8. compatibility_note
9. exception_case
```

### 3. Relation 탐색

기본 max_depth는 1이다.

```text
depth 0:
- root entity

depth 1:
- root와 직접 연결된 entity

depth 2:
- depth 1 entity와 연결된 entity
```

MVP에서는 max_depth 2까지만 허용해도 충분하다.

### 4. Deprecated 처리

deprecated entity가 포함되면 warnings에 추가한다.

```json
{
  "warnings": [
    {
      "type": "deprecated_entity",
      "entity_id": "old-uuid",
      "message": "This entity is deprecated.",
      "replacement_entity_id": "new-uuid"
    }
  ]
}
```

### 5. Ambiguity 처리

root_ids는 UUID이므로 ambiguity가 없어야 한다.

단, request가 alias 기반 입력을 지원하는 경우 ambiguity를 반환한다.

```json
{
  "ambiguities": [
    {
      "input": "사용자 검색",
      "candidates": ["uuid-1", "uuid-2"],
      "required_action": "ask_user_to_choose_entity_id"
    }
  ]
}
```

## Markdown Bundle optional

에이전트가 JSON보다 markdown context를 선호할 수 있으므로 optional format을 둘 수 있다.

Request:

```json
{
  "root_ids": ["uuid"],
  "format": "markdown"
}
```

Response:

```md
# Context Bundle: 사용자 검색

## Root

- ID: 1c9323e9-46a4-4665-b2d1-c37e4f3b19e0
- Type: FEATURE
- Status: active

## Summary

조건에 따라 사용자 목록을 조회하는 기능.

## Related UI Areas

- 0d18b76a-6c0e-45b4-9289-6bdfc2e87e5a: 사용자 검색 조건 영역

## Warnings

없음.
```
