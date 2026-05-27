---
name: llm-reference-registry
description: LLM Reference Registry 활성 사용 가이드 — UI 영역, 기능, 인프라 단위, API, 코드 심볼의 UUID 기반 영구 참조 저장소. 코딩 에이전트가 MCP 도구와 REST API를 활용해 엔티티를 조회, resolve, 상호참조하는 방법을 설명한다.
version: 1.0.0
language: ko
source_language: en
source_file: SKILL.md
status: active
last_updated: 2026-05-27
source_project: context-ref-registry
---

# LLM Reference Registry — 코딩 에이전트 활용 가이드

## 이게 무엇인가

**LLM Reference Registry**는 사람이 읽는 이름(alias)을 안정적인 UUID에 매핑하는 영구 저장소다.
UI 화면, 기능, 인프라 단위, API, 코드 심볼을 등록하고, 풍부한 컨텍스트(요약, 비즈니스 규칙,
보안 노트, 구현 힌트)와 엔티티 간 관계 그래프를 함께 저장한다.

이 스킬은 코딩 에이전트인 **당신**이 작업 중 레지스트리를 **적극적으로 활용**하는 방법을
가르친다. UI 영역, 기능, API에 대한 참조를 발견하면 추측하지 말고 레지스트리를 조회하라.

## 연결 방법

레지스트리는 두 가지 인터페이스를 제공한다. MCP가 가능하면 우선 사용하고, 없으면 REST API를 사용한다.

| 방법 | 프로토콜 | 사용 시점 |
|------|----------|-----------|
| **MCP** | `mcp` tool 호출 | 에이전트 플랫폼에 MCP 서버가 설정된 경우 |
| **REST API** | `http://localhost:8000` | 직접 HTTP 접근, 배치 작업, 데이터 쓰기 |

---

## 핵심 워크플로우: Resolve → Bundle → Act

레지스트리를 효과적으로 사용하는 기본 패턴:

```
1. RESOLVE  — 별칭(alias)을 UUID로 변환
              → MCP: resolve_alias()  /  REST: GET /resolve?alias=...
              
2. BUNDLE   — 해당 엔티티 주변의 풍부한 컨텍스트 조회
              → MCP: get_context_bundle()  /  REST: POST /context-bundle
              
3. ACT      — 조회한 컨텍스트를 바탕으로 작업 수행
              (코드 변경, 분석, 문서화 등)
```

alias가 중복되어 `ambiguous`가 반환되면 **사용자에게 선택을 요청**하라.
절대 임의로 선택하지 마라.

---

## MCP 도구 레퍼런스 (우선 사용)

MCP 서버는 6개의 읽기 전용 도구를 제공한다. 네이티브 `mcp` 도구로 호출한다.

### 1. `resolve_alias` — 모든 참조의 첫 단계

```
resolve_alias(alias="사용자 검색", locale="ko")
→ {"status": "resolved", "entity": {"id": "uuid-...", ...}}
```

- 언어를 알면 항상 `locale`을 지정한다.
- `type` 필터로 결과를 좁힌다: `type="UI_AREA"`
- `ambiguous`가 반환되면 후보를 나열하고 사용자에게 선택을 요청한다.

### 2. `get_context_bundle` — 풍부한 컨텍스트 조회의 핵심 도구

```
get_context_bundle(root_ids=["uuid-..."], max_depth=2, token_budget=8000)
```

루트, 관련 엔티티, 컨텍스트(우선순위 정렬), 관계, 폐기 경고를 반환한다.

**주요 파라미터:**

| 파라미터 | 기본값 | 설명 |
|----------|--------|------|
| `max_depth` | `2` | BFS 깊이. 0=루트만. 최대 10. |
| `token_budget` | `8000` | 컨텍스트 본문 토큰 제한. 높을수록 상세. |
| `include_types` | 전체 | 반환할 엔티티 타입 필터 |
| `include_relations` | 전체 | 탐색할 관계 타입 필터 |
| `language` | `"ko"` | 컨텍스트 언어 필터 |

**컨텍스트 우선순위** (token_budget 초과 시 잘림):
1. `summary` → 2. `business_rule` → 3. `validation_rule` → 4. `implementation_hint`
5. `security_note` → 6. `infra_note` → 7. `details` → 8. `compatibility_note`
9. `exception_case`

### 3. `get_entity` — 단일 엔티티 조회

```
get_entity(id="uuid-...")
```

엔티티 정보와 locale별 alias, 폐기 경고를 반환한다.
전체 그래프가 아닌 단일 엔티티만 필요할 때 사용한다.

### 4. `search_entities` — 키워드로 엔티티 검색

```
search_entities(query="search", types=["UI_AREA", "FEATURE"], limit=10)
```

검색 순서:
1. **Alias 정확 일치** (점수: 1.0)
2. **정식 이름 부분 일치** (ILIKE, 점수: 0.7)

UUID나 정확한 alias를 모를 때 사용한다.

### 5. `get_related_entities` — 관계 그래프 탐색

```
get_related_entities(id="uuid-...", direction="both", max_depth=2)
```

의존 관계 파악에 유용하다. 방향: `outgoing`, `incoming`, `both`.

### 6. `validate_references` — 일괄 참조 검증

```
validate_references(references=["uuid-...", "alias-text", ...])
```

UUID나 alias 목록의 유효성을 검증한다. `resolved`, `ambiguous`, `missing`을 반환한다.
특정 엔티티에 의존하는 계획을 실행하기 전에 사용한다.

---

## REST API 레퍼런스 (대체 수단 / 쓰기)

MCP를 사용할 수 없거나 데이터를 써야 할 때 REST API를 사용한다.

### 읽기 엔드포인트

| 메서드 | 경로 | 설명 |
|--------|------|------|
| `GET` | `/resolve?alias=...&locale=ko&type=UI_AREA` | Alias 해소 |
| `GET` | `/entities/{id}` | UUID로 엔티티 조회 |
| `GET` | `/search?q=...&types=FEATURE,API&limit=10` | 검색 |
| `GET` | `/entities/{id}/relations?direction=both&max_depth=1` | 관계 조회 |
| `GET` | `/entities/{id}/aliases` | 별칭 목록 |
| `GET` | `/entities/{id}/contexts` | 컨텍스트 목록 |
| `POST` | `/context-bundle` | 컨텍스트 번들 (MCP 도구와 동일 파라미터) |

### 쓰기 엔드포인트

| 메서드 | 경로 | 용도 |
|--------|------|------|
| `POST` | `/entities` | 엔티티 생성 |
| `PATCH` | `/entities/{id}` | 업데이트 (상태, 이름 등) |
| `POST` | `/entities/{id}/aliases` | 별칭 추가 |
| `POST` | `/entities/{id}/contexts` | 컨텍스트 추가 |
| `POST` | `/relations` | 관계 생성 |
| `POST` | `/ingest/batch` | **일괄 수집** (주요 쓰기 진입점) |

### 모든 응답 형식:

```json
{"ok": true, "data": {...}}
{"ok": false, "error": {"code": "...", "message": "..."}}
```

---

## Batch Ingest 워크플로우 (파서용)

문서(화면설계서, API 문서 등)를 파싱한 후 결과를 저장하려면 `POST /ingest/batch`를 사용한다.

```json
{
  "source": {
    "type": "screen_spec",
    "name": "source-filename.md",
    "uri": "file://docs/...",
    "version": "2026-05-27"
  },
  "entities": [
    {
      "type": "UI_AREA",
      "canonical_name": "사용자 검색 조건 영역",
      "description": "...",
      "status": "candidate",
      "aliases": {"ko": ["검색 조건"], "en": ["Search Filter"]},
      "contexts": [
        {"context_type": "summary", "body": "...", "language": "ko"}
      ]
    }
  ],
  "relations": [
    {
      "from_entity_id": "uuid-a",
      "to_entity_id": "uuid-b",
      "relation_type": "RELATED_TO"
    }
  ]
}
```

**규칙:**
- `id`는 선택사항. 생략하면 서버가 생성한다.
- `id`가 존재하면 해당 엔티티를 **업데이트**한다 (단, type은 변경 불가).
- relations의 `from_entity_id` / `to_entity_id`는 배치 내부나 DB에 존재해야 한다.
- 기본 status는 `candidate` — 사람 검토 후 `active`로 승격한다.

---

## 엔티티 생명주기

```
candidate ──▶ active ──▶ deprecated ──▶ archived
```

| 상태 | 의미 |
|------|------|
| `candidate` | 에이전트가 파싱, 아직 사람 검토 전 |
| `active` | 사람이 확인 완료 |
| `deprecated` | 대체됨. `replacement_entity_id` 확인. **삭제 금지.** |
| `archived` | 더 이상 관련 없음 |

**deprecated** 엔티티를 만나면:
1. `replacement_entity_id`를 확인한다.
2. 대체 엔티티를 사용하여 작업을 수행한다.
3. 폐기 사실을 사용자 응답에 포함한다.

---

## 엔티티 타입 (5종)

| 타입 | 의미 |
|------|------|
| `UI_AREA` | 화면 영역 (검색 필터, 내비게이션, 데이터 테이블) |
| `FEATURE` | 사용자 대상 기능 (사용자 검색, 주문 접수) |
| `INFRA_UNIT` | 인프라 컴포넌트 (데이터베이스, 캐시, 메시지 큐) |
| `API` | API 엔드포인트 또는 서비스 경계 |
| `CODE_SYMBOL` | 코드 레벨 심볼 (클래스, 함수, 컴포넌트) |

---

## 컨텍스트 타입 (9종)

| 타입 | 사용 시점 |
|------|-----------|
| `summary` | 이 엔티티가 무엇인지 간략히 설명 |
| `details` | 상세 설명 |
| `business_rule` | 비즈니스 로직 제약과 규칙 |
| `validation_rule` | 입/출력 검증 규칙 |
| `implementation_hint` | 코드 레벨 힌트 (컴포넌트명, 프레임워크) |
| `security_note` | 보안 고려사항 |
| `infra_note` | 인프라/배포 관련 사항 |
| `compatibility_note` | 다른 시스템과의 호환성 |
| `exception_case` | 엣지 케이스와 오류 시나리오 |

---

## 관계 타입 (8종)

| 타입 | 방향 | 의미 |
|------|------|------|
| `CONTAINS` | → | 부모가 자식을 포함 (UI_AREA가 하위 영역 포함) |
| `RELATED_TO` | ↔ | 일반적인 연관 관계 |
| `USES` | → | 동작을 위해 의존 |
| `IMPLEMENTED_BY` | → | 기능이 코드 심볼로 구현됨 |
| `READS_FROM` | → | 데이터 읽기 (API가 DB에서 읽음) |
| `WRITES_TO` | → | 데이터 쓰기 |
| `DEPENDS_ON` | → | 강한 의존 관계 (서비스 A가 서비스 B에 의존) |
| `CALLS` | → | 호출 (UI가 API를 호출) |

---

## 자주 쓰는 패턴

### 패턴 A: 사용자가 UI 영역을 이름으로 언급

```
1. resolve_alias("주문 목록", locale="ko")
   → resolved → UUID 획득
2. get_context_bundle(root_ids=[uuid], max_depth=2, token_budget=6000)
   → 전체 컨텍스트 + 관련 엔티티 + 관계 조회
3. 폐기 경고와 함께 결과를 사용자에게 제시
```

### 패턴 B: 특정 기능과 관련된 모든 엔티티 찾기

```
1. search_entities("user management", types=["FEATURE"])
   → 후보 UUID 획득
2. get_context_bundle(root_ids=[uuid], max_depth=3, token_budget=10000,
     include_relations=["USES", "DEPENDS_ON", "CALLS"],
     include_types=["UI_AREA", "API", "INFRA_UNIT"])
   → 의존 관계 그래프 탐색
```

### 패턴 C: 코드 수정 전 모든 참조 검증

```
1. validate_references(references=["user-search", "uuid-...", "OrderList"])
   → 유효성 확인
2. ambiguous 결과는 사용자에게 명확히 요청
3. deprecated 엔티티는 replacement_entity_id 사용
```

### 패턴 D: 문서 파싱 후 저장

```
1. 문서 파싱 → 엔티티/컨텍스트/관계 목록 구성
2. POST /ingest/batch 로 결과 전송
3. 응답에서 경고와 카운트 확인
```

---

## 불변 규칙 (절대 위반 금지)

| 규칙 | 이유 |
|------|------|
| **UUID는 불변** | 엔티티의 UUID를 절대 변경하지 않음. 이름/상태 변경은 PATCH 사용. |
| **Alias는 중복 가능** | `resolve_alias`가 `ambiguous` 반환 시 사용자에게 물어볼 것. 임의 선택 금지. |
| **Deprecated 엔티티 삭제 금지** | `status: deprecated`로 설정하고 `replacement_entity_id` 기록. |
| **MCP는 읽기 전용** | 모든 MCP 도구는 읽기 전용. 쓰기는 REST API 사용. |
| **엔티티 타입 변경 불가** | `TYPE_CHANGE_FORBIDDEN` 에러. 필요시 삭제 후 재생성. |

---

## 레지스트리를 사용하지 말아야 할 때

- 엔티티가 순간적/임시적이라 영구 참조가 필요 없을 때
- 참조가 단일 파일 내부에 한정되어 재사용되지 않을 때
- 사용자가 정확한 표현으로 이미 확인한 정보일 때

**의심스러우면 조회하라** — 레지스트리는 빠르고 일관성을 유지한다.
