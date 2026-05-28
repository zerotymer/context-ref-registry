---
name: static-mockup-preview-server
description: Python 내장 HTTP 서버로 정적 HTML 목업 파일을 로컬에서 서빙한다. UI 목업, 디자인 시안, 프로토타입 HTML 파일을 개발 중에 미리 볼 때 사용한다.
version: 1.0.0
language: ko
source_language: en
source_file: SKILL.md
wiki_uuid: e6274b24-2c08-4367-8859-b5a92bd98d59
wiki_url: https://md.zerotymer.net/ko/skill/e6274b24-2c08-4367-8859-b5a92bd98d59
status: active
last_updated: 2026-05-28
source_project: context-ref-registry
---

# 정적 목업 확인용 서버

정적 HTML 목업 파일을 로컬에서 서빙해 확인하는 스킬.

## 사용 시점

- 사용자가 목업이나 HTML 파일을 "서버로 올려줘", "미리봐", "열어줘" 라고 요청할 때
- 구현 전 UI 디자인을 확인할 때
- 프로토타입 URL을 공유해 검토할 때

## 기본 명령어

Python 내장 HTTP 서버를 사용한다. 반드시 **목업 디렉터리**에서 실행해야
HTML 파일 간 상대 링크가 올바르게 동작한다.

```bash
cd <목업-디렉터리> && python3 -m http.server <포트>
```

## 이 프로젝트의 목업 경로

| 디렉터리 | 내용 |
|----------|------|
| `output/tag-ui-mockup/` | 태그 기능 UI 목업 (entity-detail, entities, 새 Entity 모달) |
| `output/review-ui-mockup/` | Review UI 목업 |

## 표준 포트

백엔드 API(8000)와 충돌을 피하기 위해 목업 서버는 **8080 포트**를 사용한다.

```bash
cd output/tag-ui-mockup && python3 -m http.server 8080
```

진입점: `http://localhost:8080/index.html`

## 백그라운드 실행

서버 기동 후에도 작업을 계속해야 하면 백그라운드로 실행하고,
URL을 보고하기 전에 서버가 응답하는지 확인한다.

```bash
# 시작
cd <목업-디렉터리> && python3 -m http.server 8080 &

# 확인
curl -s -o /dev/null -w "%{http_code}" http://localhost:8080/index.html
# 기대값: 200
```

## 서버 종료

```bash
lsof -ti:8080 | xargs kill
```

## 주의사항

- URL을 보고하기 전에 반드시 HTTP 200 응답을 확인한다.
- index URL과 각 페이지 URL을 함께 안내한다.
- `pkill -f` 는 공유 환경에서 의도치 않은 프로세스를 종료할 수 있으므로
  `lsof -ti:<port> | xargs kill` 을 사용한다.
