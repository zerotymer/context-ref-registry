---
uuid: 1285a04e-652a-4b95-a3a9-160dfc897ef2
title: 인증 시스템 3 — 관리자·프로젝트 관리자 기능
status: draft
created: 2026-05-28
completed:
registry_entity_id: 775c9218-05eb-4cd0-969a-212d673835d7
ref_docs:
  - docs/09-security-and-ops.md
prerequisite:
  - 1a2a9bf8-c772-4d6e-8bb9-469bb211e8c8
  - 8c36e2c4-4273-472d-964e-7febf9d2428e
---

# 인증 시스템 3 — 관리자·프로젝트 관리자 기능

> **목표**: 전역 관리자와 프로젝트 관리자가 각 권한 범위 안에서 사용자, 프로젝트, 팀원, 엔티티 운영을 수행할 수 있게 한다.

---

## 권한 범위

### 전역 관리자 (`admin`)

- 사용자 계정 생성/비활성화/역할 변경
- 프로젝트 생성/수정/비활성화
- 프로젝트 관리자 임명/해제
- 모든 프로젝트 팀원 관리
- 모든 프로젝트 엔티티 조회/수정
- public 엔티티 조회/수정
- API Key 생성/폐기/scope 관리

### 프로젝트 관리자 (`project_admin`)

- 자기 프로젝트 팀원 추가/제거
- 자기 프로젝트 일반 팀원 역할 관리
- 자기 프로젝트 엔티티 조회/수정
- 자기 프로젝트 candidate 검토/active 승인
- 자기 프로젝트 alias/context 관리

### 일반 사용자 (`user`)

- public 엔티티 조회
- 소속 프로젝트 엔티티 조회/수정
- 자기 계정 정보 조회

---

## Registry Entity 매핑

| 구분 | 이름 | Entity ID |
|------|------|-----------|
| 문서 | 인증 시스템 3 — 관리자·프로젝트 관리자 기능 | 775c9218-05eb-4cd0-969a-212d673835d7 |
| 기능 | 관리자 사용자 관리 | 21eb72cb-ccc8-4c8c-9a39-8125ff52ccbd |
| 기능 | 관리자 프로젝트 관리 | 8622af84-644e-4d61-89d8-0ac8d7ad834c |
| 기능 | 프로젝트 관리자 팀원 관리 | 68008177-e121-4571-bbb0-dd24abd7d079 |
| 화면 | 관리자 로그인 화면 | 5696c90e-45f1-4ad4-9775-8b7039c7180f |
| 화면 | 사용자 관리 화면 | bc09e7f6-88cd-4f5a-be3e-410cba004409 |
| 화면 | 프로젝트 관리 화면 | b08cde52-f137-4a93-8b9c-8e1f3e4b860b |
| 화면 | 프로젝트 멤버 관리 화면 | c4cbc108-caaf-4f8a-bda0-041c3819068e |
| 화면 | 프로젝트 기준 엔티티 필터 | 9feeb89b-dbfc-4efd-8d72-1ed7be23dd9e |
| 인프라 | 관리자 감사 로그 연동 | d5634a78-bb73-463c-bd55-a16b9862d1d6 |

---

## Step 2-3-1. 관리자 사용자 관리 API

**브랜치**: `feat/step2-3-admin-users`
**상태**: `[ ]` pending

### 작업 목록

- [ ] `GET /admin/users`
- [ ] `POST /admin/users`
- [ ] `PATCH /admin/users/{user_id}`
- [ ] `POST /admin/users/{user_id}/reset-password`
- [ ] 사용자 비활성화 API
- [ ] 관리자 발급 계정 생성 화면/API에서 임의 가입 경로가 없도록 검증

### 완료 조건

- `admin`만 사용자를 생성할 수 있다.
- 비활성 사용자는 로그인 및 API 행위가 거부된다.
- 사용자 생성/변경은 Audit Log에 기록된다.

**완료일**: —

---

## Step 2-3-2. 프로젝트 관리 API

**브랜치**: `feat/step2-3-admin-projects`
**상태**: `[ ]` pending

### 작업 목록

- [ ] `GET /admin/projects`
- [ ] `POST /admin/projects`
- [ ] `PATCH /admin/projects/{project_id}`
- [ ] `GET /admin/projects/{project_id}/members`
- [ ] `POST /admin/projects/{project_id}/members`
- [ ] `PATCH /admin/projects/{project_id}/members/{user_id}`
- [ ] `DELETE /admin/projects/{project_id}/members/{user_id}`
- [ ] 프로젝트 관리자 임명/해제 API는 `admin` 전용으로 제한

### 완료 조건

- `admin`은 모든 프로젝트를 관리할 수 있다.
- 프로젝트 관리자는 자기 프로젝트 팀원을 관리할 수 있다.
- 프로젝트 관리자는 다른 프로젝트에 접근할 수 없다.

**완료일**: —

---

## Step 2-3-3. 관리자 화면

**브랜치**: `feat/step2-3-admin-console`
**상태**: `[ ]` pending

### 화면 범위

- 로그인 화면
- 현재 사용자 메뉴
- 사용자 목록/생성/비활성화
- 프로젝트 목록/생성/수정
- 프로젝트 멤버 목록/추가/제거
- 프로젝트 관리자 임명/해제
- 프로젝트 기준 엔티티 필터
- public 엔티티 관리자 수정 경로

### 작업 목록

- [ ] Frontend BFF에서 인증 cookie/session 전달 구조 반영
- [ ] 관리자 메뉴는 권한별로 노출 제어
- [ ] API 에러 코드를 사용자 행동 단위 메시지로 매핑
- [ ] 프로젝트 선택 필터를 entity 목록/상세/수정 화면에 연결

### 완료 조건

- 비로그인 사용자는 관리자 화면에 접근할 수 없다.
- 프로젝트 관리자는 자기 프로젝트 관리 화면만 볼 수 있다.
- 일반 사용자는 관리자 메뉴를 볼 수 없다.

**완료일**: —

---

## Step 2-3-4. 감사 로그 연동

**브랜치**: `feat/step2-3-admin-audit`
**상태**: `[ ]` pending
**연계**: `instructions/security_ops.md` Step 2-2

### 기록 대상

- 사용자 생성/비활성화/역할 변경
- 로그인 실패 반복 이벤트
- 프로젝트 생성/수정/비활성화
- 프로젝트 팀원 추가/삭제/역할 변경
- 프로젝트 관리자 임명/해제
- API Key 생성/폐기/scope 변경
- public 엔티티 수정
- 프로젝트 엔티티 수정

### 완료 조건

- 모든 관리자 행위는 actor와 target을 남긴다.
- API Key 기반 행위도 actor를 식별할 수 있다.
- secret, token, password 원문은 로그에 남기지 않는다.

**완료일**: —
