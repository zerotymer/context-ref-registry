# 03. Database Schema

이 문서는 PostgreSQL 기준 스키마 초안이다.

MVP에서는 PostgreSQL만 사용하고, semantic search가 필요해지는 시점에 pgvector를 추가한다.

## Extension

pgvector를 사용할 경우:

```sql
create extension if not exists vector;
```

## entity

```sql
create table entity (
    id uuid primary key,
    type varchar(50) not null,
    canonical_name text not null,
    description text,
    status varchar(30) not null default 'candidate',
    confidence numeric(4,3),
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now(),
    created_by text,
    updated_by text
);

create index idx_entity_type on entity (type);
create index idx_entity_status on entity (status);
create index idx_entity_name on entity (canonical_name);
```

## entity_alias

alias는 중복 가능해야 하므로 unique 제약을 걸지 않는다.

```sql
create table entity_alias (
    id bigserial primary key,
    entity_id uuid not null references entity(id) on delete cascade,
    locale varchar(10) not null,
    alias text not null,
    is_primary boolean not null default false,
    is_active boolean not null default true,
    created_at timestamptz not null default now(),
    created_by text
);

create index idx_entity_alias_entity_id
    on entity_alias (entity_id);

create index idx_entity_alias_alias
    on entity_alias (alias);

create index idx_entity_alias_locale_alias
    on entity_alias (locale, alias);

create index idx_entity_alias_active
    on entity_alias (is_active);
```

## entity_context

```sql
create table entity_context (
    id uuid primary key,
    entity_id uuid not null references entity(id) on delete cascade,
    context_type varchar(50) not null,
    title text,
    body text not null,
    language varchar(10),
    source_ref_id uuid,
    token_estimate int,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now(),
    created_by text,
    updated_by text
);

create index idx_entity_context_entity_id
    on entity_context (entity_id);

create index idx_entity_context_type
    on entity_context (context_type);

create index idx_entity_context_language
    on entity_context (language);
```

## entity_relation

```sql
create table entity_relation (
    id uuid primary key,
    from_entity_id uuid not null references entity(id) on delete cascade,
    to_entity_id uuid not null references entity(id) on delete cascade,
    relation_type varchar(50) not null,
    description text,
    confidence numeric(4,3),
    created_at timestamptz not null default now(),
    created_by text
);

create index idx_entity_relation_from
    on entity_relation (from_entity_id);

create index idx_entity_relation_to
    on entity_relation (to_entity_id);

create index idx_entity_relation_type
    on entity_relation (relation_type);
```

## entity_metadata

타입별 상세 필드가 달라지므로 JSONB로 저장한다.

```sql
create table entity_metadata (
    entity_id uuid primary key references entity(id) on delete cascade,
    metadata jsonb not null default '{}',
    updated_at timestamptz not null default now()
);

create index idx_entity_metadata_gin
    on entity_metadata using gin (metadata);
```

## source_ref

원본 문서나 외부 산출물 참조를 저장한다.

```sql
create table source_ref (
    id uuid primary key,
    source_type varchar(50) not null,
    name text not null,
    uri text,
    version text,
    checksum text,
    created_at timestamptz not null default now(),
    metadata jsonb not null default '{}'
);

create index idx_source_ref_type
    on source_ref (source_type);

create index idx_source_ref_name
    on source_ref (name);
```

권장 source_type:

```text
screen_spec
planning_doc
figma
openapi
infra_doc
markdown
pdf
manual
```

## context_embedding optional

pgvector를 사용할 때만 추가한다.

```sql
create table context_embedding (
    context_id uuid primary key references entity_context(id) on delete cascade,
    embedding vector,
    embedding_model varchar(100),
    created_at timestamptz not null default now()
);
```

실제 embedding dimension은 사용하는 모델에 맞게 지정한다.

예:

```sql
embedding vector(1536)
```

## entity_revision optional

운영 단계에서 추가한다.

```sql
create table entity_revision (
    id uuid primary key,
    entity_id uuid not null references entity(id) on delete cascade,
    revision_no int not null,
    snapshot jsonb not null,
    created_at timestamptz not null default now(),
    created_by text,
    change_reason text,
    unique (entity_id, revision_no)
);

create index idx_entity_revision_entity_id
    on entity_revision (entity_id);
```

## 상태값 권장

```text
candidate
active
deprecated
archived
```

## Relation Type 권장

```text
CONTAINS
RELATED_TO
DEPENDS_ON
USES
IMPLEMENTS
TRIGGERS
READS_FROM
WRITES_TO
CONFIGURED_BY
DEPLOYED_AS
RENDERS_TO
IMPLEMENTED_BY
SUPERSEDES
```
