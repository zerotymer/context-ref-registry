# 01. Requirements

## 기능 요구사항

### RQ-001. UUID 기반 Entity 저장

모든 entity는 불변 UUID를 가진다.

```text
- UUID는 unique해야 한다.
- UUID는 생성 이후 변경하지 않는다.
- alias나 이름이 변경되어도 UUID는 유지한다.
```

### RQ-002. Entity Type 지원

MVP에서 필수 지원할 entity type은 다음과 같다.

```text
UI_AREA
FEATURE
INFRA_UNIT
```

추후 확장 가능한 타입:

```text
API
CODE_SYMBOL
DOCUMENT
DATA_MODEL
CONFIG
SECRET
TEST_CASE
```

### RQ-003. Alias 저장

Entity는 여러 alias를 가질 수 있다.

```text
- alias는 locale별로 저장한다.
- ko, en을 우선 지원한다.
- alias는 중복될 수 있다.
- alias는 변경 가능하다.
- alias는 primary key로 사용하지 않는다.
```

예:

```json
{
  "ko": ["사용자 검색", "회원 검색"],
  "en": ["User Search", "Search Users"]
}
```

### RQ-004. Alias Resolve

alias 조회 결과는 다음 중 하나다.

```text
not_found
resolved
ambiguous
```

중복 alias가 있을 경우 임의로 하나를 선택하지 않는다.

```json
{
  "status": "ambiguous",
  "candidates": [
    {
      "id": "uuid-1",
      "type": "FEATURE",
      "canonical_name": "관리자 사용자 검색"
    },
    {
      "id": "uuid-2",
      "type": "FEATURE",
      "canonical_name": "고객센터 사용자 검색"
    }
  ],
  "required_action": "ask_user_to_choose_entity_id"
}
```

### RQ-005. Context 저장

Entity는 여러 context를 가질 수 있다.

권장 context type:

```text
summary
details
business_rule
validation_rule
exception_case
implementation_hint
security_note
compatibility_note
infra_note
```

### RQ-006. Relation 저장

Entity 간 관계를 저장한다.

MVP 필수 relation:

```text
CONTAINS
RELATED_TO
DEPENDS_ON
USES
```

추후 확장 relation:

```text
IMPLEMENTS
TRIGGERS
READS_FROM
WRITES_TO
CONFIGURED_BY
DEPLOYED_AS
RENDERS_TO
IMPLEMENTED_BY
```

### RQ-007. Context Bundle 조회

코딩 에이전트는 단일 entity가 아니라 관계를 포함한 context bundle을 요청할 수 있어야 한다.

```text
Input:
- root_ids
- max_depth
- include_types
- include_relations
- token_budget

Output:
- root entity
- contexts
- related entities
- relation summary
- warnings
- ambiguities
```

### RQ-008. Batch Ingest API

Codex 등 외부 파서가 여러 entity, alias, context, relation을 한 번에 저장할 수 있어야 한다.

### RQ-009. MCP Read-only Server

MVP의 MCP 서버는 read-only로 시작한다.

쓰기 기능은 REST API로 제한한다.

## 비기능 요구사항

### NFR-001. 단순성

MVP는 PostgreSQL만으로 동작해야 한다. pgvector는 optional이다.

### NFR-002. 변경 추적

최소한 다음 필드는 저장한다.

```text
created_at
updated_at
created_by
updated_by
source
```

운영 단계에서는 revision table을 추가한다.

### NFR-003. 모호성 우선

모호한 참조를 임의로 선택하지 않는다.

### NFR-004. Legacy/Deprecated 명시

status가 deprecated 또는 archived인 entity는 조회 결과에 명확히 표시한다.

에이전트는 deprecated entity를 기본 선택하지 않아야 한다.

### NFR-005. 보안

```text
- MCP server는 기본 read-only
- registry write는 인증 필요
- source 문서 권한을 추후 고려
- secret 값은 직접 저장하지 않는다
- prompt injection 방어를 위해 source context와 instruction을 구분한다
```
