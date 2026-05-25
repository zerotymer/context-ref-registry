---
title: Git 브랜치 가이드라인
description: 프로젝트 Git 브랜치 이름 및 사용 규칙.
version: 1.0.0
language: ko
source_language: en
source_file: SKILL.md
status: active
last_updated: 2026-05-25
---

# Git 브랜치 가이드라인

## 사전 정의 변수

- `{DATE}`: 현재 날짜를 `YYYY-MM-DD` 형식으로 매핑한다.
- `{DATETIME}`: 현재 날짜와 시각을 `YYYY-MM-DD_HH24:mm:SS` 형식으로 매핑한다.
  - 브랜치 이름에 사용할 경우, 크로스 플랫폼 호환성이 필요하면 `YYYY-MM-DD_HH-mm-SS` 형식을 권장한다. `:` 문자는 일부 파일시스템 및 도구에서 문제가 될 수 있다.
- `{UUID}`: UUIDv7 값의 앞 8자리를 사용한 짧은 UUID.
- `{UUIDv7}`: UUID v7 전체 값.
- `{NAME}`: 브랜치의 목적 또는 내용을 나타내는 설명형 명칭.

## 브랜치 네이밍

### `main`

`main`: 최종 운영 가능 상태를 위한 브랜치.

- 임의로 병합하지 않는다.
- 직접 커밋하지 않는다.
- 특별한 사유가 없는 한 다른 브랜치의 기준 브랜치가 된다.

### `staging`

`staging`: 운영 반영 전 최종 테스트를 위한 검증 브랜치.

- 임의로 병합하지 않는다.
- 직접 커밋하지 않는다.

### `dev`

`dev/{NAME}`: 개발 서버 테스트를 위한 브랜치.

- 임의로 병합하지 않는다.
- 직접 커밋은 제한적으로 허용한다.

### `feature`

`feature/{NAME}-{UUID}`: 기능 개발을 위한 브랜치.

- `main`에서 분기한다.
- 기능 브랜치명이 중복되지 않도록 짧은 UUID를 추가한다.

### `fix`

`fix/{DATE}/{NAME}-{UUID}`: 버그 수정 또는 관련 보정을 위한 브랜치.

- 주로 `main`에서 분기한다.

### `temp`

`temp/{UUIDv7}`: 임시 브랜치.

- 주로 `main`에서 분기한다.
- 작업을 진행하기 전에 임시로 생성한다.
- 최종 push 전에 적절한 `feature` 또는 `fix` 브랜치로 이름을 변경하거나 해당 브랜치에 병합한다.

### `merge`

`merge/{NAME}-{UUID}`: 병합 테스트 또는 병합 실행을 위한 브랜치.

- 임시 병합 테스트에 사용한다.
- `main`을 당겨와 병합을 준비하거나 `main`으로 병합을 실행할 때 사용한다.
