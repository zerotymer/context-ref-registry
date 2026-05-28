---
uuid: 1a2a9bf8-c772-4d6e-8bb9-469bb211e8c8
title: 인증 시스템 1 — 사용자 계정, 로그인, API Key 병행
status: draft
created: 2026-05-28
completed:
registry_entity_id: eb3bb01a-a210-4420-aed2-52c4f729819e
ref_docs:
  - docs/09-security-and-ops.md
prerequisite: ce6d92bf-2c2d-4944-adb3-1089a6530e56 (보안 운영 지침과 병행)
---

# 인증 시스템 1 — 사용자 계정, 로그인, API Key 병행

> **목표**: 관리자 발급 사용자 계정 기반 로그인을 추가하고, 기존 API 중심 운영을 위해 API Key 인증을 병행한다.
> 사용자가 임의 가입하거나 계정을 자체 생성하는 흐름은 제공하지 않는다.

---

## 확정 정책

| 항목 | 결정 |
|------|------|
| 로그인 방식 | 이메일/비밀번호 |
| 계정 생성 | 관리자 발급만 허용 |
| 자체 가입 | 불가 |
| SSO | 추후 필요 기능으로 기록. 이번 범위 제외 |
| API Key | 사용자 로그인과 병행 |
| public 엔티티 수정 | 관리자만 가능 |
| 개인 소유 엔티티 | 없음 |

---

## 역할 모델

### 전역 역할

```
user
admin
project_admin
```

- `admin`: 전역 관리자. 모든 프로젝트, 사용자, 엔티티, API Key에 개입 가능하다.
- `project_admin`: 특정 프로젝트의 관리자 권한을 가진 사용자다. 실제 권한은 프로젝트 멤버십에서 결정한다.
- `user`: 일반 사용자. 소속 프로젝트 범위 내 조회/수정 권한을 가진다.

> `project_admin`은 전역 단일 역할만으로 판단하지 않고, 프로젝트별 멤버십 role과 함께 판단한다.

---

## Registry Entity 매핑

| 구분 | 이름 | Entity ID |
|------|------|-----------|
| 문서 | 인증 시스템 1 — 사용자 계정, 로그인, API Key 병행 | eb3bb01a-a210-4420-aed2-52c4f729819e |
| 기능 | 관리자 발급 사용자 계정 | 7de841ee-f9e0-4e91-9112-866c2732c045 |
| 기능 | 이메일 비밀번호 로그인 | 0b85e6ca-a153-4931-87ce-532d4a61f5c7 |
| 기능 | API Key 병행 인증 | b7d26182-1e67-42c3-a1f5-b379f5e84643 |
| API | Auth Session API | 38e27d51-53ae-42ca-aab3-cbf8e10de620 |
| 인프라 | 초기 관리자 계정 bootstrap | 86c81238-9764-40de-a352-73d5dcd66ec7 |
| 인프라 | 비밀번호 해시 정책 | 77aa4986-87bd-401e-a18c-c94f25b29383 |
| 스키마 | user_account table | 71be58d1-214a-44fb-90f4-32ea2212457b |

---

## Step 2-1-1. 사용자 계정 스키마

**브랜치**: `feat/step2-1-auth-identity`
**상태**: `[ ]` pending

### 작업 목록

- [ ] `user_account` 테이블 Alembic migration
  ```sql
  id UUID PRIMARY KEY
  email VARCHAR(320) UNIQUE NOT NULL
  password_hash TEXT NOT NULL
  display_name VARCHAR(80) NOT NULL
  role VARCHAR(32) NOT NULL DEFAULT 'user'
  is_active BOOLEAN NOT NULL DEFAULT true
  created_at TIMESTAMPTZ NOT NULL
  updated_at TIMESTAMPTZ NOT NULL
  created_by UUID NULL
  ```
- [ ] role enum 또는 제한값 정의: `user`, `admin`, `project_admin`
- [ ] 이메일 정규화 정책 정의: 소문자 저장, 앞뒤 공백 제거
- [ ] 비밀번호 해시 정책 정의: bcrypt 또는 argon2id
- [ ] 초기 관리자 계정 bootstrap 방법 정의
  - 환경변수 기반 1회 생성 또는 CLI command
  - 동일 이메일 존재 시 no-op

### 완료 조건

- 관리자가 아니면 사용자 계정을 생성할 수 없다.
- 비밀번호 원문은 저장되지 않는다.
- inactive 사용자는 로그인할 수 없다.

**완료일**: —

---

## Step 2-1-2. 로그인/세션 API

**브랜치**: `feat/step2-1-login-session`
**상태**: `[ ]` pending

### 작업 목록

- [ ] `POST /auth/login`
- [ ] `POST /auth/logout`
- [ ] `GET /auth/me`
- [ ] 인증 실패 표준 에러 응답 정의
  ```json
  {"ok": false, "error": {"code": "UNAUTHORIZED"}}
  ```
- [ ] 세션 방식 확정
  - Frontend BFF 구조와 맞춰 httpOnly cookie 기반 세션을 우선 검토
  - 순수 API client용 bearer token 필요 여부는 구현 전 재확인
- [ ] 로그인 rate limit 또는 실패 지연 정책 검토

### 완료 조건

- 로그인 성공 시 현재 사용자와 역할을 확인할 수 있다.
- 로그아웃 후 보호 API 접근이 거부된다.
- 비활성 계정은 로그인 실패한다.

**완료일**: —

---

## Step 2-1-3. API Key 병행 인증

**브랜치**: `feat/step2-1-api-key-auth`
**상태**: `[ ]` pending
**연계**: `instructions/security_ops.md` Step 2-1

### 목적

대부분의 자동화 행위는 API로 수행되므로 사용자 로그인과 별도로 API Key 인증을 유지한다.

### 작업 목록

- [ ] `api_key` 테이블 또는 기존 환경변수 방식 확장 여부 결정
- [ ] API Key actor 식별자 정의
  ```sql
  id, name, key_hash, scopes, project_id NULL, created_by, revoked_at, created_at
  ```
- [ ] scope 정책 정의
  ```text
  read
  ingest
  write
  admin
  ```
- [ ] API Key와 사용자 세션이 동시에 제공될 때 우선순위 정의
  - 기본: 사용자 세션 우선
  - system ingest: API Key actor 사용
- [ ] Audit Log actor에 `user:{uuid}` / `api_key:{id}` / `system` 형식 기록

### 완료 조건

- API Key만으로 batch ingest/write 자동화가 가능하다.
- admin scope 없는 API Key는 관리자 기능을 호출할 수 없다.
- revoked API Key는 즉시 거부된다.

**완료일**: —

---

## 추후 기능

- SSO 연동
  - OIDC/SAML Provider 연동
  - 이메일 도메인 기반 자동 매핑
  - 기존 관리자 발급 계정과 외부 ID 연결
