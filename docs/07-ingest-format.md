# 07. Batch Ingest Format

Batch Ingest는 Codex 등 외부 파서가 정리한 entity 후보를 registry에 저장하는 API다.

```http
POST /ingest/batch
```

## 기본 원칙

```text
- id가 없으면 서버가 UUID를 생성할 수 있다.
- id가 있으면 해당 UUID를 그대로 사용한다.
- UUID는 생성 후 변경하지 않는다.
- alias 중복은 허용한다.
- 기존 entity가 있으면 upsert 정책을 따른다.
- Codex가 생성한 결과는 기본 status=candidate로 저장한다.
```

## Request

```json
{
  "source": {
    "type": "screen_spec",
    "name": "user-management-screen-spec.md",
    "uri": "file://docs/user-management-screen-spec.md",
    "version": "2026-05-25",
    "checksum": "sha256..."
  },
  "entities": [
    {
      "id": "0d18b76a-6c0e-45b4-9289-6bdfc2e87e5a",
      "type": "UI_AREA",
      "canonical_name": "사용자 검색 조건 영역",
      "description": "사용자 목록 화면 상단의 검색 조건 입력 영역",
      "status": "candidate",
      "confidence": 0.82,
      "aliases": {
        "ko": [
          "사용자 검색 영역",
          "검색 조건"
        ],
        "en": [
          "User Search Filter",
          "Search Criteria"
        ]
      },
      "contexts": [
        {
          "context_type": "summary",
          "title": "영역 요약",
          "body": "사용자명, 이메일, 상태값으로 검색 조건을 입력하는 영역",
          "language": "ko"
        },
        {
          "context_type": "implementation_hint",
          "title": "구현 힌트",
          "body": "React 컴포넌트명은 UserSearchFilter 후보",
          "language": "ko"
        }
      ],
      "metadata": {
        "ui_framework": "react",
        "route_hint": "/users",
        "component_hint": "UserSearchFilter",
        "html_role_hint": "form"
      }
    },
    {
      "id": "1c9323e9-46a4-4665-b2d1-c37e4f3b19e0",
      "type": "FEATURE",
      "canonical_name": "사용자 검색",
      "description": "조건에 따라 사용자 목록을 조회하는 기능",
      "status": "candidate",
      "confidence": 0.78,
      "aliases": {
        "ko": [
          "사용자 검색",
          "회원 검색",
          "사용자 조회"
        ],
        "en": [
          "User Search",
          "Search Users"
        ]
      },
      "contexts": [
        {
          "context_type": "summary",
          "body": "사용자명, 이메일, 상태값 조건으로 사용자 목록을 조회한다.",
          "language": "ko"
        },
        {
          "context_type": "business_rule",
          "body": "검색 조건이 비어 있으면 전체 목록을 조회한다.",
          "language": "ko"
        }
      ],
      "metadata": {
        "granularity": "coarse",
        "certainty": "medium"
      }
    }
  ],
  "relations": [
    {
      "id": "c9c17b87-92c2-4f55-a5f7-d88d2314a1c1",
      "from_entity_id": "0d18b76a-6c0e-45b4-9289-6bdfc2e87e5a",
      "to_entity_id": "1c9323e9-46a4-4665-b2d1-c37e4f3b19e0",
      "relation_type": "RELATED_TO",
      "description": "사용자 검색 조건 영역은 사용자 검색 기능과 관련된다.",
      "confidence": 0.91
    }
  ]
}
```

## Response

```json
{
  "ok": true,
  "data": {
    "source_ref_id": "source-uuid",
    "created": {
      "entities": 2,
      "aliases": 7,
      "contexts": 4,
      "relations": 1
    },
    "updated": {
      "entities": 0,
      "aliases": 0,
      "contexts": 0,
      "relations": 0
    },
    "warnings": []
  }
}
```

## Upsert 정책

### Entity

```text
id가 존재하지 않으면 create
id가 존재하면 update
id는 변경 불가
type 변경은 기본 거부
```

### Alias

```text
같은 entity_id + locale + alias가 이미 active면 중복 생성하지 않는다.
다른 entity에 같은 alias가 있어도 허용한다.
```

### Context

MVP에서는 동일 body라도 새 context로 추가할 수 있다.

운영 단계에서는 다음 정책을 추가한다.

```text
entity_id + context_type + body_hash 기준 중복 방지
```

### Relation

MVP에서는 중복 relation 허용 가능.

운영 단계에서는 다음 기준으로 중복 방지한다.

```text
from_entity_id + to_entity_id + relation_type
```

## Validation

Batch ingest 시 최소 검증:

```text
- UUID 형식
- type 허용값
- status 허용값
- relation의 from/to entity 존재 여부
- context_type 허용값
- locale 허용값
```

## Error 예시

```json
{
  "ok": false,
  "error": {
    "code": "INVALID_RELATION_TARGET",
    "message": "to_entity_id does not exist in existing registry or current batch.",
    "details": {
      "to_entity_id": "missing-uuid"
    }
  }
}
```
