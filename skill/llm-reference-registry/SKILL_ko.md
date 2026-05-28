---
name: llm-reference-registry
description: LLM Reference Registry 활성 사용 가이드 — UI 영역, 기능, 인프라 단위, API, 코드 심볼의 UUID 기반 영구 참조 저장소. 코딩 에이전트가 MCP 도구와 REST API를 활용해 엔티티를 조회, resolve, 상호참조하는 방법을 설명한다.
version: 1.2.0
language: ko
source_language: en
source_file: SKILL.md
status: active
last_updated: 2026-05-28
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

의존 관계 파악에 유용하다. MCP 방향: `outgoing`, `incoming`, `both`.
REST API 방향은 `out`, `in`, `both`를 사용한다.

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
| `GET` | `/entities/{id}/relations?direction=both&max_depth=1` | 관계 조회 (`direction`: `out`, `in`, `both`) |
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

### 등록 단위 분해 원칙

문서 전체를 엔티티 1개로만 등록하지 말고, 문서 루트와 세부 단위를 함께 등록한다.
사용자가 "업로드", "엔티티 ID 받아와", "매핑"을 요청하면 아래 단위까지 자동으로 쪼갠다.

| 단위 | 타입 | 예시 |
|------|------|------|
| 문서/지침 루트 | `FEATURE` 또는 가장 가까운 타입 | "인증 시스템 설계 지침" |
| 세부 기능 | `FEATURE` | 로그인, 프로젝트 멤버십, 수정 권한 정책 |
| 화면/화면요소 | `UI_AREA` | 로그인 화면, 사용자 관리 화면, 프로젝트 필터 |
| API/서비스 경계 | `API` | Auth Session API, Project Access API Policy |
| 인프라/운영 단위 | `INFRA_UNIT` | 초기 관리자 bootstrap, 감사 로그 연동 |
| 스키마/코드 심볼 | `CODE_SYMBOL` | `user_account table`, Authorization Policy Service |

문서 루트는 세부 엔티티를 `CONTAINS` 관계로 연결한다.
세부 엔티티 간에는 필요에 따라 `DEPENDS_ON`, `USES`, `IMPLEMENTED_BY`, `CALLS`, `READS_FROM`, `WRITES_TO`를 연결한다.

### ID 매핑 규칙

현재 `POST /ingest/batch` 응답은 생성된 entity id 목록을 즉시 반환하지 않을 수 있다.
따라서 매핑이 필요한 업로드에서는 **에이전트가 UUID를 먼저 발급하고 각 entity의 `id` 필드에 명시한다.**

절차:

1. 문서 루트와 세부 기능/API/UI/인프라/코드 심볼 후보를 뽑는다.
2. 각 엔티티에 UUID를 선발급한다.
3. batch payload의 모든 entity에 `id`를 넣는다.
4. relations는 선발급 UUID를 사용해 같은 batch 안에서 연결한다.
5. 업로드 후 `GET /entities/{id}` 또는 `GET /entities/{id}/relations?direction=out`으로 검증한다.
6. 원본 지침/문서에 `Registry Entity 매핑` 표를 추가한다.

이 방식이면 서버가 ID 목록을 반환하지 않아도 업로드 직후 정확한 매핑을 보유할 수 있다.

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
      "id": "uuid-preassigned-by-agent",
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
- 하지만 ID 매핑이 필요한 작업에서는 생략하지 말고 에이전트가 UUID를 선발급한다.
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

### 패턴 E: 신규 엔티티 등록 후 원본 문서에 매핑

지침서, 화면 설계서, 설계 문서를 새로 작성할 때 사용한다.
문서에 포함된 식별 가능한 단위(화면, 기능, 코드 심볼)에 안정적인 UUID를
**구현 전에** 발급하고, 그 ID를 문서에 직접 삽입한다.

**1단계 — 등록 대상 단위 식별**

문서를 스캔해 각 단위를 타입으로 분류한다:

| 발견한 것 | 엔티티 타입 |
|-----------|-------------|
| 화면 영역 / UI 섹션 | `UI_AREA` |
| 사용자 대상 기능 | `FEATURE` |
| API 엔드포인트 | `API` |
| 클래스 / 함수 / 컴포넌트 | `CODE_SYMBOL` |
| 인프라 컴포넌트 | `INFRA_UNIT` |

**2단계 — UUID 발급**

단위마다 UUID를 하나씩 생성한다:

```bash
python3 -c "import uuid; print(uuid.uuid4())"
```

**3단계 — batch ingest로 업로드**

모든 단위를 `POST /ingest/batch` 한 번으로 업로드한다.
생성한 UUID를 `id`에 명시해 고정한다.
`aliases`(ko + en), `contexts`(최소 `summary` + `implementation_hint`),
`relations`(단위 간 CONTAINS / USES / DEPENDS_ON)을 함께 포함한다.

```json
{
  "source": {
    "type": "screen_spec",
    "name": "my_instruction.md",
    "uri": "file://instructions/my_instruction.md",
    "version": "2026-05-28"
  },
  "entities": [
    {
      "id": "<생성한-uuid>",
      "type": "FEATURE",
      "canonical_name": "내 기능",
      "status": "candidate",
      "aliases": {"ko": ["내 기능"], "en": ["My Feature"]},
      "contexts": [
        {"context_type": "summary", "body": "...", "language": "ko"},
        {"context_type": "implementation_hint", "body": "파일: src/...", "language": "ko"}
      ]
    }
  ],
  "relations": [
    {
      "from_entity_id": "<부모-uuid>",
      "to_entity_id": "<자식-uuid>",
      "relation_type": "CONTAINS"
    }
  ]
}
```

**4단계 — UUID를 원본 문서에 기록**

업로드 성공 후 UUID를 문서에 삽입한다. 이후 에이전트가
alias 추측 없이 UUID로 직접 참조할 수 있다.

*지침서 frontmatter (`entities:` 블록):*

```yaml
---
uuid: <지침서-uuid>
entities:
  feature:
    my_feature: <uuid>          # FEATURE 엔티티
  ui_area:
    main_screen: <uuid>         # UI_AREA 엔티티
    filter_bar:  <uuid>         # UI_AREA 엔티티
  code_symbol:
    my_service:  <uuid>         # CODE_SYMBOL 엔티티
---
```

*문서 본문 Step별 인라인 주석:*

```markdown
## Step 3. 메인 화면 구현

> **entity**: `<uuid>` (UI_AREA — 메인 화면)

파일: src/app/...
```

*화면 설계서 섹션 헤더:*

```markdown
## 로그인 화면  <!-- entity: <uuid> (UI_AREA) -->
```

**이 패턴이 중요한 이유**

- 문서를 나중에 읽는 에이전트가 alias 중복 없이 UUID로 직접 참조할 수 있다.
- 3단계에서 등록한 관계 덕분에 `get_context_bundle`이 전체 기능 그래프를 자동으로 탐색한다.
- 사람 검토 후 `active`로 승격해도 UUID는 변경되지 않으므로 하위 참조가 모두 유지된다.

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
