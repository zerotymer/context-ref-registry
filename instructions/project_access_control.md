---
uuid: 8c36e2c4-4273-472d-964e-7febf9d2428e
title: 인증 시스템 2 — 프로젝트, 멤버십, 조회·수정 권한
status: draft
created: 2026-05-28
completed:
registry_entity_id: f16f5245-658e-4202-9f7b-60755e2090d0
ref_docs:
  - docs/03-database-schema.md
  - docs/09-security-and-ops.md
prerequisite: 1a2a9bf8-c772-4d6e-8bb9-469bb211e8c8 (사용자 인증 기반)
---

# 인증 시스템 2 — 프로젝트, 멤버십, 조회·수정 권한

> **목표**: 기존 엔티티를 기본 전체공개로 유지하면서, 프로젝트 ID가 있는 엔티티는 프로젝트 팀원 공개로 취급한다.
> 프로젝트 생성 및 프로젝트 관리자 임명은 전역 관리자만 가능하다.

---

## 확정 정책

| 항목 | 결정 |
|------|------|
| 프로젝트 ID | 3~20자 영어 식별자 |
| 프로젝트 ID 변경 | 불가 |
| 프로젝트명 alias | Unicode 허용, 최대 50자 |
| 프로젝트 설명 | 별도 설명 필드 제공 |
| 프로젝트 생성 | `admin`만 가능 |
| 프로젝트 관리자 임명 | `admin`만 가능 |
| 팀원 관리 | `admin`, 해당 프로젝트 `project_admin` 가능 |
| 기존 데이터 | `project_id` 없음 → 전체공개 |
| `project_id` 있는 엔티티 | 프로젝트 팀원 공개 |
| public 엔티티 수정 | `admin`만 가능 |
| 개인 엔티티 | 없음 |

---

## Registry Entity 매핑

| 구분 | 이름 | Entity ID |
|------|------|-----------|
| 문서 | 인증 시스템 2 — 프로젝트, 멤버십, 조회·수정 권한 | f16f5245-658e-4202-9f7b-60755e2090d0 |
| 기능 | 프로젝트 식별자와 alias | fe2e511d-f39d-4431-b53e-8327bc672f59 |
| 기능 | 프로젝트 멤버십 | c6241f01-1d06-4855-9a33-cc52645090ba |
| 기능 | 엔티티 project_id 공개 범위 | dd13af59-925e-47f9-bb2d-44c3b66a9f23 |
| 기능 | 엔티티 수정 권한 정책 | df06fabf-e594-4d97-8ad3-e8c90126824b |
| API | Project Access API Policy | 4d2f4f6b-feb1-41c4-91f8-2bf25896aecf |
| 스키마 | project table | 67759f9d-be76-43bb-95d6-b6de5644c08f |
| 스키마 | project_member table | 56569a89-288c-4d7a-a209-8806335022ed |
| 코드 | Authorization Policy Service | 9b9b078d-e4f8-43c0-9aef-2f8437670c88 |

---

## Step 2-2-1. 프로젝트 스키마

**브랜치**: `feat/step2-2-project-schema`
**상태**: `[ ]` pending

### 작업 목록

- [ ] `project` 테이블 Alembic migration
  ```sql
  id VARCHAR(20) PRIMARY KEY
  alias VARCHAR(50) NOT NULL
  description TEXT NULL
  is_active BOOLEAN NOT NULL DEFAULT true
  created_at TIMESTAMPTZ NOT NULL
  updated_at TIMESTAMPTZ NOT NULL
  created_by UUID NOT NULL
  ```
- [ ] `id` validation
  ```text
  ^[A-Za-z]{3,20}$
  ```
- [ ] `alias` validation
  - Unicode 허용
  - trim 후 1~50자
- [ ] 프로젝트 ID 변경 API는 만들지 않는다.
- [ ] 프로젝트 archive/deactivate 정책 정의

### 완료 조건

- `admin`만 프로젝트를 생성할 수 있다.
- 잘못된 프로젝트 ID는 422로 거부된다.
- 생성 후 프로젝트 ID 변경 경로가 없다.

**완료일**: —

---

## Step 2-2-2. 프로젝트 멤버십

**브랜치**: `feat/step2-2-project-membership`
**상태**: `[ ]` pending

### 작업 목록

- [ ] `project_member` 테이블 Alembic migration
  ```sql
  project_id VARCHAR(20) NOT NULL REFERENCES project(id)
  user_id UUID NOT NULL REFERENCES user_account(id)
  role VARCHAR(32) NOT NULL DEFAULT 'member'
  is_active BOOLEAN NOT NULL DEFAULT true
  created_at TIMESTAMPTZ NOT NULL
  created_by UUID NOT NULL
  PRIMARY KEY (project_id, user_id)
  ```
- [ ] membership role 정의
  ```text
  member
  project_admin
  ```
- [ ] 전역 `admin`은 모든 프로젝트에서 암묵적 관리자 권한을 가진다.
- [ ] 해당 프로젝트 `project_admin`은 팀원 추가/제거/역할 변경 가능
- [ ] 단, 프로젝트 관리자 임명은 전역 `admin`만 가능

### 완료 조건

- 프로젝트 팀원 추가/삭제가 가능하다.
- 프로젝트 관리자는 자기 프로젝트의 팀원 관리를 할 수 있다.
- 일반 팀원은 팀원 관리를 할 수 없다.

**완료일**: —

---

## Step 2-2-3. 엔티티 project_id 적용

**브랜치**: `feat/step2-2-entity-project-id`
**상태**: `[ ]` pending

### 작업 목록

- [ ] 주요 엔티티 테이블에 `project_id VARCHAR(20) NULL` 추가
  - entity
  - context
  - relation
  - 필요한 경우 alias/tag/history/audit는 부모 entity 기준으로 판단
- [ ] `project_id IS NULL`이면 전체공개로 판단
- [ ] `project_id IS NOT NULL`이면 프로젝트 팀원 공개로 판단
- [ ] 기존 데이터 migration 기본값은 `NULL`
- [ ] 생성/수정 API에서 project_id 입력 규칙 정의
  - `admin`: 임의 프로젝트 지정 가능
  - `project_admin`/`member`: 자신이 속한 프로젝트만 지정 가능
  - public 생성은 관리자만 가능

### 완료 조건

- 기존 데이터는 전체공개로 유지된다.
- 프로젝트 ID가 있는 데이터는 비팀원에게 조회되지 않는다.
- 없는 프로젝트 ID로 엔티티를 생성할 수 없다.

**완료일**: —

---

## Step 2-2-4. 조회·수정 권한 정책

**브랜치**: `feat/step2-2-access-policy`
**상태**: `[ ]` pending

### 조회 권한

| visibility | 조건 |
|------------|------|
| 전체공개 | `project_id IS NULL` |
| 프로젝트 팀원공개 | `project_id IS NOT NULL` + active project member |

### 수정 권한

| 대상 | 수정 가능 |
|------|-----------|
| public 엔티티 | `admin` |
| 프로젝트 엔티티 | `admin`, 해당 프로젝트 active member |
| 프로젝트 팀원 관리 | `admin`, 해당 프로젝트 `project_admin` |
| 프로젝트 생성 | `admin` |
| 프로젝트 관리자 임명 | `admin` |

### 작업 목록

- [ ] 공통 authorization dependency/service 구현
- [ ] 목록 API에 visibility filter 적용
- [ ] 상세 조회 API에 visibility check 적용
- [ ] create/update/delete/status 변경 API에 mutation policy 적용
- [ ] MCP/API Key 조회 경로의 project scope 정책 정의

### 완료 조건

- 비로그인 사용자는 public 데이터만 조회 가능하다.
- 로그인 사용자는 public + 소속 프로젝트 데이터를 조회 가능하다.
- 팀원은 자기 프로젝트 엔티티만 수정 가능하다.
- public 엔티티는 관리자만 수정 가능하다.

**완료일**: —
