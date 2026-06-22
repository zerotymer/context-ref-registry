---
uuid: c5e60dba-cfc6-4dac-9db3-d0e9f4657001
title: 화면설계(UI_AREA) 엔티티 목업 HTML 자동 생성 서비스
status: pending
created: 2026-06-22
---

# 화면설계(UI_AREA) 엔티티 목업 HTML 자동 생성 서비스

## 배경 / 문제

`UI_AREA` 엔티티는 화면(영역)을 나타낸다. 현재는 텍스트 context/metadata만
저장하고, 에이전트·사람이 "이 화면이 대략 어떻게 생겼는지" 시각적으로 확인할
수단이 없다.

`UI_AREA` 엔티티의 **metadata(레이아웃·필드·구성요소)로부터 서버가 목업 HTML을
자동 렌더링**해 제공한다. 파일을 업로드/저장하지 않고, 저장소는 데이터만 유지한다
(이 서비스의 책임 분리 원칙 유지 — 파싱·저작은 외부 에이전트, 저장소는 데이터).

## 결정 사항 (확정)

| 항목 | 결정 |
|------|------|
| 방식 | **metadata → HTML 자동 생성** (업로드 파일 저장 아님, 외부 URL 참조 아님) |
| 입력 | `UI_AREA` 엔티티의 `entity_metadata`(JSONB)에 담긴 구조화된 화면 정의 |
| 출력 | 단일 HTML 문서 (정적, JS 의존 최소) — GET 엔드포인트로 즉시 렌더 |
| 저장 | 생성물 미저장 (요청 시 렌더). 저장소는 metadata만 유지 |
| 대상 타입 | `UI_AREA` 한정 (다른 타입은 404/400) |

## 설계

### metadata 스키마 (목업 입력 규약)

`UI_AREA` 엔티티 metadata에 목업 렌더용 선택 필드를 규약화한다. 없으면
canonical_name·description 기반 최소 플레이스홀더 렌더.

```jsonc
{
  "mockup": {
    "title": "주문 목록 화면",
    "layout": "stack",              // stack | grid | columns
    "components": [
      { "kind": "header", "text": "주문 목록" },
      { "kind": "table", "columns": ["주문번호", "상태", "금액"] },
      { "kind": "button", "text": "신규 주문" },
      { "kind": "field", "label": "검색", "input": "text" }
    ]
  }
}
```

- `kind` 화이트리스트로 제한(헤더/텍스트/테이블/버튼/필드/이미지 placeholder 등).
  알 수 없는 kind는 회색 박스 + 라벨로 안전 렌더(에러로 죽이지 않음).

### 렌더 엔드포인트

```
GET /entities/{id}/mockup        → text/html (목업 HTML)
```

- entity 조회 → `type != UI_AREA`면 400 `NOT_A_UI_AREA`
- MCP 프로젝트 범위 필터와 동일하게, API Key 가시 범위 밖이면 404 은닉
- 서버사이드 문자열 템플릿으로 생성 (의존성 추가 없음 — stdlib/기존 스택).
  **모든 사용자 입력 텍스트 HTML 이스케이프** (XSS 방지 — 신뢰 경계).
- 인라인 CSS, 외부 리소스/스크립트 없음 (정적·이식 가능).

### 프록시/문서

- Next BFF `/api/v1/entities/{id}/mockup`는 passthrough(content-type 보존).
  - ⚠️ export 계열처럼 OkResponse 봉투가 아닌 raw text/html — content-type 보존 필수.
- 미리보기는 정적 서버 포트 규칙(8081) 및 `static-mockup-preview-server` 스킬 활용 가능.

## DoD (Definition of Done)

- [ ] `mockup` metadata 규약 정의 + component kind 화이트리스트
- [ ] `GET /entities/{id}/mockup` — UI_AREA만, HTML 반환, 범위 밖 404
- [ ] HTML 이스케이프(XSS) 적용, 알 수 없는 kind 안전 렌더
- [ ] 테스트: UI_AREA 렌더 성공/구조 검증, 비-UI_AREA 400, 범위밖 404,
      XSS 입력 이스케이프, mockup 필드 없을 때 플레이스홀더 렌더
- [ ] 백엔드 전체 테스트 green
- [ ] `docs/02-domain-model.md`(UI_AREA mockup 규약) · `backend/CLAUDE.md`(엔드포인트) 갱신

## 메모

- 브랜치는 구현 착수 시 브랜치 전략 스킬
  (`e03f48fb-3e00-41d7-b99d-c32854567d67`)로 생성.
- 범위 확장 후보(이번 제외): 컴포넌트 kind 추가, 반응형 레이아웃, 테마.
  YAGNI — 실제 metadata 사례가 쌓인 뒤 추가.
