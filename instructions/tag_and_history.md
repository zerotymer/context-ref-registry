---
uuid: 36ab4117-e0cc-4a30-813e-129f0835b540
title: Tag & History — Entity 태그 다중 부착 + 변경 이력 관리
status: pending
created: 2026-05-28
completed:
ref_docs:
  - docs/03-database-schema.md
  - backend/CLAUDE.md
prerequisite: MVP 완료 (240e1460)
---

# Tag & History — Entity 태그 다중 부착 + 변경 이력 관리

> **목적**: entity를 project·팀·도메인 단위로 그룹핑할 수 있는 Tag 기능과,
> entity 변경 시 전체 상태를 버전별로 보존하는 History 기능을 추가한다.
> 두 Step은 독립적으로 진행 가능하다.

---

## Step A. Entity Tag (다중 태그)

**브랜치**: `feat/entity-tag`

### 설계 원칙

- entity 1개에 태그 N개 부착 가능
- 태그는 자유 문자열 (`project:frontend`, `team:platform`, `v2` 등)
- 조회·검색에서 tag 필터 지원
- 별도 `entity_tag` 테이블로 정규화 (GIN 인덱스 → 빠른 필터)

### A-1. DB Migration

```sql
CREATE TABLE entity_tag (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    entity_id   UUID NOT NULL REFERENCES entity(id),
    tag         VARCHAR(200) NOT NULL,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (entity_id, tag)   -- 동일 entity에 중복 태그 불가
);

CREATE INDEX ix_entity_tag_entity_id ON entity_tag(entity_id);
CREATE INDEX ix_entity_tag_tag ON entity_tag(tag);  -- tag 기준 필터용
```

**작업 목록**

- [ ] Alembic revision 생성: `alembic revision --autogenerate -m "add entity_tag table"`
- [ ] migration 파일 검토 후 `alembic upgrade head`

### A-2. ORM Model (`backend/app/domain/models.py`)

```python
class EntityTag(Base):
    __tablename__ = "entity_tag"
    __table_args__ = (UniqueConstraint("entity_id", "tag", name="uq_entity_tag"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    entity_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("entity.id"), nullable=False)
    tag: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    entity: Mapped["Entity"] = relationship("Entity", back_populates="tags")
```

`Entity` 모델에 relationship 추가:

```python
tags: Mapped[list["EntityTag"]] = relationship("EntityTag", back_populates="entity", lazy="selectin")
```

### A-3. Pydantic Schema (`backend/app/domain/schemas.py`)

- `EntityResponse`에 `tags: list[str]` 필드 추가 (tag 문자열 목록)
- `EntityCreateRequest` / `EntityUpdateRequest`에 `tags: list[str] | None = None` 추가
- `IngestEntityItem`에도 `tags: list[str] | None = None` 추가

### A-4. Repository (`backend/app/repository/entity_repository.py`)

```python
# entity 조회 시 tag 필터 지원
async def list_by_tags(self, tags: list[str], ...) -> list[Entity]: ...

# tag 일괄 교체 (기존 tag 삭제 후 재삽입)
async def replace_tags(self, entity_id: UUID, tags: list[str]) -> None: ...
```

### A-5. Service (`backend/app/service/entity_service.py`)

- `create_entity`: tags 있으면 `entity_tag` 행 삽입
- `update_entity`: tags 있으면 기존 행 전체 삭제 후 재삽입 (교체 방식)
- `get_entity_response`: tags → `[t.tag for t in entity.tags]` 직렬화

### A-6. API 엔드포인트

**기존 엔드포인트 수정**

| 메서드 | 경로 | 변경 내용 |
|--------|------|-----------|
| POST | `/entities` | request body에 `tags` 수신 |
| PATCH | `/entities/{id}` | `tags` 수신 → 교체 |
| GET | `/entities/{id}` | response에 `tags` 포함 |

**신규 엔드포인트 추가**

```
GET /entities/{id}/tags          — entity 태그 목록
POST /entities/{id}/tags         — 태그 1개 추가 (body: {"tag": "..."})
DELETE /entities/{id}/tags/{tag} — 태그 1개 삭제
GET /tags                        — 전체 태그 목록 (distinct, 빈도 포함 optional)
```

**쿼리 파라미터 확장**

```
GET /entities?tags=project:frontend,team:platform   — AND 필터
GET /search?q=...&tags=...                           — 검색 + tag 필터
```

### A-7. Batch Ingest 연동 (`backend/app/service/ingest_service.py`)

- `IngestEntityItem.tags` 처리: entity upsert 후 tag 교체
- 기존 tag 유지 정책: `tags` 필드 생략 시 기존 태그 변경 없음 (None ≠ [])

### A-8. MCP Tool 확장 (`backend/app/mcp/tools.py`)

- `search_entities` tool 파라미터에 `tags: list[str] | None` 추가
- `get_entity` 결과에 `tags` 포함

### A-9. 테스트 (`backend/tests/test_tag_api.py` 신규)

- [ ] entity 생성 시 tags 포함
- [ ] tags 교체 (PATCH)
- [ ] 태그 개별 추가/삭제
- [ ] `GET /tags` 전체 목록
- [ ] tag 필터 검색
- [ ] 중복 태그 삽입 → 409 또는 무시(upsert)
- [ ] batch ingest에서 tag 처리

---

## Step B. Entity History (변경 이력)

**브랜치**: `feat/entity-history`

### 설계 원칙

- entity 상태가 변경될 때마다 스냅샷 저장
- `revision_no`는 entity별 단조 증가 (1, 2, 3, …)
- 스냅샷은 변경 **이전** 상태를 저장 (before-image)
- 누가·왜 바꿨는지 기록 (`changed_by`, `change_reason`)
- 읽기 전용 조회 API만 제공 (이력 수정·삭제 불가)

### B-1. DB Migration

```sql
CREATE TABLE entity_history (
    id             UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    entity_id      UUID NOT NULL REFERENCES entity(id),
    revision_no    INTEGER NOT NULL,           -- entity 내 단조 증가
    snapshot       JSONB NOT NULL,             -- 변경 이전 전체 상태
    changed_fields JSONB,                      -- {"field": {"before": ..., "after": ...}}
    change_type    VARCHAR(50) NOT NULL,       -- "create" | "update" | "status_change" | "deprecate"
    change_reason  TEXT,
    changed_by     VARCHAR(200),              -- 요청 출처 (agent id, user id 등)
    created_at     TIMESTAMPTZ NOT NULL DEFAULT now(),

    UNIQUE (entity_id, revision_no)
);

CREATE INDEX ix_entity_history_entity_id ON entity_history(entity_id);
CREATE INDEX ix_entity_history_created_at ON entity_history(created_at);
```

**revision_no 채번 전략**:
```sql
-- 삽입 시 서브쿼리로 max + 1 계산 (동시성 낮은 시스템 가정)
SELECT COALESCE(MAX(revision_no), 0) + 1
FROM entity_history
WHERE entity_id = :entity_id
FOR UPDATE;  -- row-level lock으로 중복 방지
```

> 고트래픽이 예상되면 advisory lock 또는 sequence-per-entity 방식으로 전환. 현재는 간단한 max+1 채번 사용.

### B-2. ORM Model (`backend/app/domain/models.py`)

```python
class EntityHistory(Base):
    __tablename__ = "entity_history"
    __table_args__ = (UniqueConstraint("entity_id", "revision_no", name="uq_entity_history_rev"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    entity_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("entity.id"), nullable=False, index=True)
    revision_no: Mapped[int] = mapped_column(nullable=False)
    snapshot: Mapped[dict] = mapped_column(JSONB, nullable=False)
    changed_fields: Mapped[dict | None] = mapped_column(JSONB)
    change_type: Mapped[str] = mapped_column(String(50), nullable=False)
    change_reason: Mapped[str | None] = mapped_column(Text)
    changed_by: Mapped[str | None] = mapped_column(String(200))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), index=True)

    entity: Mapped["Entity"] = relationship("Entity", back_populates="history")
```

`Entity` 모델에 relationship 추가:

```python
history: Mapped[list["EntityHistory"]] = relationship(
    "EntityHistory", back_populates="entity", lazy="noload", order_by="EntityHistory.revision_no"
)
```

> `lazy="noload"`: 평소 entity 조회 시 history 로드하지 않음. 이력 조회는 별도 endpoint에서만.

### B-3. Pydantic Schema (`backend/app/domain/schemas.py`)

```python
class EntityHistoryEntry(BaseModel):
    id: UUID
    entity_id: UUID
    revision_no: int
    snapshot: dict
    changed_fields: dict | None
    change_type: str
    change_reason: str | None
    changed_by: str | None
    created_at: datetime

class EntityHistoryListResponse(BaseModel):
    ok: bool = True
    data: list[EntityHistoryEntry]
    total: int
```

### B-4. History Repository (`backend/app/repository/history_repository.py` 신규)

```python
class HistoryRepository:
    async def create(self, entity_id, snapshot, changed_fields, change_type, change_reason, changed_by) -> EntityHistory:
        # next_revision_no = SELECT MAX(revision_no)+1 FOR UPDATE
        ...

    async def list_by_entity(self, entity_id, limit=50, offset=0) -> tuple[list[EntityHistory], int]:
        ...

    async def get_by_revision(self, entity_id, revision_no) -> EntityHistory | None:
        ...
```

### B-5. Service 연동 (`backend/app/service/entity_service.py`)

entity 수정이 발생하는 모든 지점에서 history 생성:

| 트리거 | change_type |
|--------|-------------|
| `create_entity` | `"create"` — 초기 상태 기록 |
| `update_entity` (PATCH) | `"update"` |
| `update_entity` (status만 변경) | `"status_change"` |
| `deprecate_entity` | `"deprecate"` |
| batch ingest (entity upsert) | `"update"` (기존 entity일 때) |

`snapshot` 내용: 변경 직전 entity 전체 상태 (aliases, tags 제외 — entity 행만)
`changed_fields` 내용: `{"status": {"before": "candidate", "after": "active"}}`

`changed_by` 수신 방법: API request header `X-Changed-By: <agent-id>` (없으면 null)

### B-6. API 엔드포인트

```
GET /entities/{id}/history                    — 이력 목록 (최신 순, limit/offset)
GET /entities/{id}/history/{revision_no}      — 특정 revision 상세
```

응답에 `X-Changed-By` 헤더 수신을 위한 dependency 추가:

```python
# api/dependencies.py
async def get_changed_by(x_changed_by: str | None = Header(default=None)) -> str | None:
    return x_changed_by
```

기존 PATCH, 상태 변경 endpoint에 `changed_by`, `change_reason` 수신 추가:

```python
# EntityUpdateRequest에 추가
change_reason: str | None = None
```

### B-7. MCP Tool 확장 (`backend/app/mcp/tools.py`)

```python
# 신규 read-only tool
async def get_entity_history(entity_id: str, limit: int = 20) -> dict:
    """entity 변경 이력 조회"""
```

### B-8. 테스트 (`backend/tests/test_history_api.py` 신규)

- [ ] entity 생성 시 revision_no=1 history 생성
- [ ] PATCH 후 revision_no 증가 확인
- [ ] status 변경 history 기록
- [ ] deprecate history 기록
- [ ] `GET /entities/{id}/history` 목록 정렬 (최신 순)
- [ ] `GET /entities/{id}/history/1` 특정 revision 조회
- [ ] revision_no 중복 없음 (동시 요청 가정 테스트)
- [ ] batch ingest에서 history 생성
- [ ] `changed_by` header 전달 및 저장 확인

---

## 구현 순서 권장

```
A-1 → A-2 → A-3 → A-4 → A-5 → A-6 → A-7 → A-8 → A-9  (Tag)
B-1 → B-2 → B-3 → B-4 → B-5 → B-6 → B-7 → B-8          (History)
```

Tag(A)와 History(B)는 동시 진행 가능하나, 각 Step 내부는 순서를 지킨다.
Tag 완료 후 History 진행을 권장 (B-5에서 tag 정보를 snapshot에 포함할 수 있음).

---

## 완료 기준 (DoD)

- [ ] 모든 기존 테스트 통과 (95 passed 유지)
- [ ] 신규 테스트 — tag: 최소 8개, history: 최소 8개
- [ ] `GET /tags` 응답 정상
- [ ] `GET /entities/{id}/history` 응답 정상
- [ ] Alembic migration 멱등 실행 (`alembic upgrade head` 재실행 무해)
- [ ] PR에 migration 파일 포함
