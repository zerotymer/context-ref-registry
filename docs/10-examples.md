# 10. Examples

## 예제 1. 사용자 관리 화면

### UI Area

```json
{
  "id": "0d18b76a-6c0e-45b4-9289-6bdfc2e87e5a",
  "type": "UI_AREA",
  "canonical_name": "사용자 검색 조건 영역",
  "description": "사용자 목록 화면 상단의 검색 조건 입력 영역",
  "status": "active",
  "aliases": {
    "ko": ["사용자 검색 영역", "검색 조건", "회원 검색 조건"],
    "en": ["User Search Filter", "Search Criteria"]
  },
  "contexts": [
    {
      "context_type": "summary",
      "body": "사용자명, 이메일, 상태값으로 검색 조건을 입력하는 영역"
    }
  ],
  "metadata": {
    "ui_framework": "react",
    "route_hint": "/users",
    "component_hint": "UserSearchFilter",
    "html_role_hint": "form"
  }
}
```

### Feature

```json
{
  "id": "1c9323e9-46a4-4665-b2d1-c37e4f3b19e0",
  "type": "FEATURE",
  "canonical_name": "사용자 검색",
  "description": "조건에 따라 사용자 목록을 조회하는 기능",
  "status": "active",
  "aliases": {
    "ko": ["사용자 검색", "회원 검색", "사용자 조회"],
    "en": ["User Search", "Search Users"]
  },
  "contexts": [
    {
      "context_type": "summary",
      "body": "사용자명, 이메일, 상태값 조건으로 사용자 목록을 조회한다."
    },
    {
      "context_type": "business_rule",
      "body": "검색 조건이 비어 있으면 전체 목록을 조회한다."
    }
  ],
  "metadata": {
    "granularity": "coarse",
    "certainty": "medium"
  }
}
```

### Infra Unit

```json
{
  "id": "ed832d61-3319-4d61-83d4-6a29f68932a5",
  "type": "INFRA_UNIT",
  "canonical_name": "사용자 서비스 PostgreSQL",
  "description": "사용자 도메인의 영속 데이터를 저장하는 PostgreSQL DB",
  "status": "active",
  "aliases": {
    "ko": ["사용자 DB", "회원 DB"],
    "en": ["User DB", "User PostgreSQL"]
  },
  "contexts": [
    {
      "context_type": "infra_note",
      "body": "로컬 개발 환경에서는 docker-compose의 user-postgres 서비스로 실행된다."
    }
  ],
  "metadata": {
    "infra_type": "database",
    "runtime": "postgresql",
    "environments": ["local", "dev", "prod"]
  }
}
```

## 예제 2. Relation

```json
[
  {
    "from_entity_id": "0d18b76a-6c0e-45b4-9289-6bdfc2e87e5a",
    "to_entity_id": "1c9323e9-46a4-4665-b2d1-c37e4f3b19e0",
    "relation_type": "RELATED_TO",
    "description": "사용자 검색 조건 영역은 사용자 검색 기능과 관련된다."
  },
  {
    "from_entity_id": "1c9323e9-46a4-4665-b2d1-c37e4f3b19e0",
    "to_entity_id": "ed832d61-3319-4d61-83d4-6a29f68932a5",
    "relation_type": "READS_FROM",
    "description": "사용자 검색 기능은 사용자 DB에서 데이터를 조회한다."
  }
]
```

## 예제 3. Alias Resolve Ambiguous

Request:

```http
GET /resolve?alias=사용자%20검색&locale=ko
```

Response:

```json
{
  "ok": true,
  "data": {
    "status": "ambiguous",
    "candidates": [
      {
        "id": "1c9323e9-46a4-4665-b2d1-c37e4f3b19e0",
        "type": "FEATURE",
        "canonical_name": "사용자 검색",
        "summary": "관리자 사용자 목록에서 조건 검색"
      },
      {
        "id": "6c13719e-7f89-4955-a823-66f83e0e7abc",
        "type": "UI_AREA",
        "canonical_name": "사용자 검색 조건 영역",
        "summary": "사용자 목록 화면 상단의 검색 조건 입력 영역"
      }
    ],
    "required_action": "ask_user_to_choose_entity_id"
  }
}
```

## 예제 4. Context Bundle

Request:

```json
{
  "root_ids": [
    "1c9323e9-46a4-4665-b2d1-c37e4f3b19e0"
  ],
  "include_relations": [
    "RELATED_TO",
    "READS_FROM"
  ],
  "include_types": [
    "UI_AREA",
    "FEATURE",
    "INFRA_UNIT"
  ],
  "max_depth": 1,
  "token_budget": 4000
}
```

Response:

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
    },
    {
      "id": "ed832d61-3319-4d61-83d4-6a29f68932a5",
      "type": "INFRA_UNIT",
      "canonical_name": "사용자 서비스 PostgreSQL",
      "status": "active"
    }
  ],
  "contexts": [
    {
      "entity_id": "1c9323e9-46a4-4665-b2d1-c37e4f3b19e0",
      "context_type": "summary",
      "body": "사용자명, 이메일, 상태값 조건으로 사용자 목록을 조회한다."
    },
    {
      "entity_id": "ed832d61-3319-4d61-83d4-6a29f68932a5",
      "context_type": "infra_note",
      "body": "로컬 개발 환경에서는 docker-compose의 user-postgres 서비스로 실행된다."
    }
  ],
  "relations": [
    {
      "from_entity_id": "0d18b76a-6c0e-45b4-9289-6bdfc2e87e5a",
      "to_entity_id": "1c9323e9-46a4-4665-b2d1-c37e4f3b19e0",
      "relation_type": "RELATED_TO"
    },
    {
      "from_entity_id": "1c9323e9-46a4-4665-b2d1-c37e4f3b19e0",
      "to_entity_id": "ed832d61-3319-4d61-83d4-6a29f68932a5",
      "relation_type": "READS_FROM"
    }
  ],
  "warnings": [],
  "ambiguities": []
}
```
