# 02. Domain Model

## 핵심 개념

이 서비스의 중심 모델은 Entity다.

```text
Entity
 ├─ Alias
 ├─ Context
 ├─ Metadata
 └─ Relation
```

## Entity

```yaml
Entity:
  id: uuid
  type: UI_AREA | FEATURE | INFRA_UNIT | API | CODE_SYMBOL | ...
  canonical_name: string
  description: string
  status: candidate | active | deprecated | archived
  confidence: number
  created_at: datetime
  updated_at: datetime
```

## Entity Type

### UI_AREA

웹 화면의 영역 단위다.

React/Vue 컴포넌트, HTML 태그 영역, div, section, form, table, modal 등으로 매핑될 수 있다.

```yaml
id: "0d18b76a-6c0e-45b4-9289-6bdfc2e87e5a"
type: "UI_AREA"
canonical_name: "사용자 검색 조건 영역"
description: "사용자 목록 화면 상단의 검색 조건 입력 영역"
metadata:
  ui_framework: "react"
  route_hint: "/users"
  component_hint: "UserSearchFilter"
  html_role_hint: "form"
  parent_area_id: "..."
```

UI_AREA는 계층 구조를 가질 수 있다.

```text
사용자 관리 화면
 ├─ 검색 조건 영역
 ├─ 사용자 목록 테이블 영역
 └─ 사용자 상세 모달 영역
```

이 계층은 `CONTAINS` relation으로 표현한다.

### FEATURE

기능 단위다.

버튼 클릭 단위가 아니라 기획서 수준의 대략적인 기능 또는 business capability로 본다.

```yaml
id: "1c9323e9-46a4-4665-b2d1-c37e4f3b19e0"
type: "FEATURE"
canonical_name: "사용자 검색"
description: "조건에 따라 사용자 목록을 조회하는 기능"
metadata:
  granularity: "coarse"
  certainty: "medium"
```

FEATURE는 여러 UI_AREA, API, CODE_SYMBOL, INFRA_UNIT과 연결될 수 있다.

```text
FEATURE: 사용자 검색
 ├─ RELATED_TO → UI_AREA: 사용자 검색 조건 영역
 ├─ RELATED_TO → UI_AREA: 사용자 목록 테이블 영역
 ├─ USES → API: GET /api/users
 ├─ IMPLEMENTED_BY → CODE_SYMBOL: UserSearchService.search()
 └─ READS_FROM → INFRA_UNIT: 사용자 DB
```

### INFRA_UNIT

인프라 구성 단위다.

```yaml
id: "ed832d61-3319-4d61-83d4-6a29f68932a5"
type: "INFRA_UNIT"
canonical_name: "사용자 서비스 PostgreSQL"
description: "사용자 도메인의 영속 데이터를 저장하는 PostgreSQL DB"
metadata:
  infra_type: "database"
  runtime: "postgresql"
  environments:
    - local
    - dev
    - prod
```

권장 infra subtype:

```text
SERVICE
DATABASE
CACHE
QUEUE
OBJECT_STORAGE
BATCH_JOB
EXTERNAL_API
CONFIG
SECRET
NETWORK
CONTAINER
DEPLOYMENT
OBSERVABILITY
```

## Alias

```yaml
Alias:
  entity_id: uuid
  locale: ko | en | ...
  alias: string
  is_primary: boolean
```

규칙:

```text
- alias는 중복 가능하다.
- alias는 변경 가능하다.
- alias는 삭제보다 비활성화 이력을 남기는 편이 좋다.
- alias는 canonical identity가 아니다.
```

## Context

```yaml
Context:
  id: uuid
  entity_id: uuid
  context_type: summary | details | business_rule | ...
  title: string
  body: string
  language: ko | en | ...
  source_ref_id: uuid
```

context는 RAG 제공 단위로도 사용한다.

## Relation

```yaml
Relation:
  id: uuid
  from_entity_id: uuid
  to_entity_id: uuid
  relation_type: CONTAINS | RELATED_TO | USES | ...
  description: string
  confidence: number
```

## Status

```text
candidate:
- Codex 등 외부 에이전트가 생성한 후보
- 아직 사람이 확정하지 않음

active:
- 사용 가능한 확정 entity

deprecated:
- 더 이상 신규 참조에 권장하지 않음
- 기존 호환을 위해 남김

archived:
- 과거 기록용
- 기본 검색 결과에서 제외 가능
```

## Deprecated 처리 규칙

deprecated entity는 삭제하지 않는다.

대신 다음 정보를 제공한다.

```yaml
status: deprecated
replacement_entity_id: "new-uuid"
deprecation_reason: "영역이 검색 조건 영역과 목록 영역으로 분리됨"
```
