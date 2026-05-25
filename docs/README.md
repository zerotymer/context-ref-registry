# LLM Reference Registry

LLM Reference Registry는 화면설계서, 기획서, 인프라 문서 등을 파싱한 결과를 저장하고, 코딩 에이전트가 안정적인 ID 기준으로 참조할 수 있게 제공하는 경량 저장소입니다.

이 프로젝트의 핵심은 문서 파싱이 아닙니다. 문서 파싱과 1차 정리는 Codex, Claude Code, Cursor 등 외부 코딩 에이전트가 수행한다고 가정합니다.

이 저장소는 다음 역할에 집중합니다.

```text
1. UUID 기반 Entity Registry
2. ko/en alias 저장 및 resolve
3. Entity별 context 저장
4. Entity 간 relation 저장
5. ID 기반 context bundle 제공
6. read-only MCP server 제공
```

## 핵심 Entity Type

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

## 핵심 원칙

```text
- id(uuid)는 불변이다.
- id(uuid)는 unique하다.
- alias는 중복 가능하다.
- alias는 ko/en 등 locale별로 변경 가능하다.
- alias가 여러 id에 매칭되면 임의 선택하지 않는다.
- 모호한 alias는 후보 목록을 반환하고 에이전트가 사용자에게 확정 질문한다.
- 이 서비스는 지침서 생성기가 아니라 context registry다.
- 지침서 생성은 추후 Codex 등 외부 에이전트에 위임한다.
```

## 추천 MVP 구성

```text
Backend:
- FastAPI 또는 Spring Boot

Storage:
- PostgreSQL
- pgvector optional
- JSONB metadata

Interfaces:
- REST API
- read-only MCP server

Deployment:
- Docker Compose
```

## 문서 구성

```text
00-architecture.md
01-requirements.md
02-domain-model.md
03-database-schema.md
04-rest-api.md
05-mcp-server.md
06-context-bundle.md
07-ingest-format.md
08-implementation-plan.md
09-security-and-ops.md
10-examples.md
11-codex-task-brief.md
```
