# 00. Architecture

## 목적

LLM Reference Registry는 코딩 에이전트가 화면, 기능, 인프라 단위를 명확하게 참조할 수 있도록 UUID 기반 참조 저장소를 제공한다.

문서 파싱, 화면설계서 해석, 기획서 요약은 이 서비스의 책임이 아니다. 해당 작업은 Codex 등 외부 에이전트가 수행하고, 이 서비스는 정리된 결과를 저장하고 조회 가능하게 제공한다.

## 전체 구조

```text
┌────────────────────────────┐
│ Parser / Coding Agent       │
│ - 화면설계서 파싱             │
│ - 기획서 파싱                 │
│ - 인프라 문서 파싱             │
│ - Entity 후보 생성            │
└──────────────┬─────────────┘
               │ Batch Ingest REST API
               ▼
┌────────────────────────────┐
│ LLM Reference Registry      │
├────────────────────────────┤
│ Entity Service              │
│ Alias Service               │
│ Context Service             │
│ Relation Service            │
│ Search Service              │
│ Bundle Builder              │
└──────────────┬─────────────┘
               │
               ▼
┌────────────────────────────┐
│ Storage                     │
├────────────────────────────┤
│ PostgreSQL                  │
│ - entity                    │
│ - entity_alias              │
│ - entity_context            │
│ - entity_relation           │
│ - entity_metadata           │
│                             │
│ pgvector optional            │
│ - context_embedding         │
└──────────────┬─────────────┘
               │
               ▼
┌────────────────────────────┐
│ MCP Server                  │
├────────────────────────────┤
│ resolve_alias               │
│ get_entity                  │
│ search_entities             │
│ get_related_entities        │
│ get_context_bundle          │
│ validate_references         │
└──────────────┬─────────────┘
               │
               ▼
┌────────────────────────────┐
│ Coding Agents               │
│ - Codex                     │
│ - Claude Code               │
│ - Cursor                    │
│ - Copilot                   │
└────────────────────────────┘
```

## 책임 경계

### 이 서비스가 담당하는 것

```text
- UUID 기반 entity 저장
- alias 저장 및 조회
- alias 중복 처리
- context 저장
- relation 저장
- entity 조회
- context bundle 생성
- MCP read-only tool 제공
- batch ingest API 제공
```

### 이 서비스가 담당하지 않는 것

```text
- PDF/OCR 파싱
- 화면설계서 자동 분석
- 기획서 자동 요약
- 지침서 자동 생성
- 코드 자동 수정
- PR 자동 생성
```

단, 추후 확장으로 연결할 수는 있다.

## 설계 방향

이 서비스는 일반적인 wiki가 아니라 에이전트용 참조 저장소이다.

```text
Wiki:
- 사람이 읽기 좋은 페이지 중심

LLM Reference Registry:
- 에이전트가 정확히 참조할 수 있는 ID 중심
- Entity, Context, Relation 중심
- 모호성 명시
- context bundle 제공
```

## 권장 배포 구조

MVP에서는 API 서버와 MCP 서버를 같은 repository에 두되, 실행 프로세스는 분리할 수 있게 한다.

```text
services:
  llm-ref-api:
    role: REST API, write/read

  llm-ref-mcp:
    role: MCP server, read-only

  postgres:
    role: primary storage

  minio:
    role: optional source artifact storage
```
