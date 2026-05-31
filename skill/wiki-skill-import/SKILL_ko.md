---
name: wiki-skill-import
description: 사용자가 UUID를 제공하면 wikijs-agent-gateway를 통해 Wiki.js 사이트에서 프로젝트 로컬 스킬을 가져온다. 영어와 한국어 페이지를 가져와 SKILL.md와 SKILL_ko.md를 작성한다.
---

# Wiki Skill Import (via wikijs-gateway)

UUID를 기반으로 Wiki.js 사이트에서 프로젝트 로컬 스킬을 가져온다.
기존 Wiki.js 직접 접근(HTML/GraphQL) 대신 `wikijs-agent-gateway`를 데이터 소스로 사용한다.

이 스킬은 두 가지 모드를 지원한다.

- **동적 참조 모드**: 요청 시점에 Wiki.js 페이지를 가져와 파일을 쓰지 않고 컨텍스트로만 사용한다.
- **가져오기 모드**: Wiki.js 페이지를 가져와 프로젝트 로컬 스킬 파일로 기록한다.

가져온 스킬은 다음 구조를 따라야 한다.

```text
skills/<skill-name>/
├── SKILL.md
└── SKILL_ko.md
```

`SKILL.md`는 영어 기준 지침 파일이다. `SKILL_ko.md`는 한국어 읽기용 사본이며 의미상 같은 내용을 유지해야 한다.

## 전제 조건

게이트웨이에 접근 가능해야 한다. 기본 공개 엔드포인트는 다음과 같다.

```
GATEWAY_URL=https://md-gw.zerotymer.net
```

읽기 엔드포인트(`/health`, `/pages/by-uuid`, `/pages/by-path`, `/pages/search`,
`/pages/by-paths`)는 **공개 — 토큰 불필요**.

쓰기 엔드포인트(`/pages/patch-section`, `/pages/upsert`, `/pages/dry-run`)는
`Authorization: Bearer $GATEWAY_ADMIN_TOKEN` 헤더가 필요하다. 수정/upsert 워크플로에서만 필요하다.

## 가져오기 전략

게이트웨이의 `GET /pages/by-uuid`를 사용한다. 게이트웨이는 각 locale별로 원본 Markdown `content`, `title`, `description`, `locale`, `path`, `contentHash`를 포함한 구조화된 JSON을 반환한다. HTML 스크래핑이나 GraphQL 스키마 탐색이 필요 없다.

```
GET $GATEWAY_URL/pages/by-uuid?uuid=<uuid>[&type=<type>]
```

읽기 요청에는 `Authorization` 헤더가 필요하지 않다.

`type` 파라미터는 선택 사항이다. 호출자가 경로 prefix(예: `skill`, `guide`, `agent`)를 제공하면 전달한다. 생략하면 게이트웨이는 경로를 `<uuid>` 단독으로 해석한다. type에 관계없이 로컬 저장 위치는 항상 `skills/<name>/`이다.

게이트웨이가 두 locale 모두 404를 반환하면 실패를 보고하고, 사용자가 best-effort 가져오기를 요청하지 않는 한 부분적인 스킬 파일을 만들지 않는다.

## 동적 방식과 정적 방식

동적 가져오기는 허용된다.

사용자가 UUID를 제공하고 스킬 참조, 가져오기, 갱신을 요청하면 요청 시점에 최신 영어와 한국어 콘텐츠를 가져온다. 사용자가 오프라인 또는 정적 동작을 명시적으로 요청하지 않는 한 이전에 다운로드한 사본에 의존하지 않는다.

사용자가 `LLM-wiki <uuid> 참고해줘` 같은 명령을 입력하면 기본적으로 동적 참조 모드를 사용한다.

1. 요청 시점에 게이트웨이를 통해 관련 콘텐츠를 가져온다.
2. 가져온 콘텐츠를 현재 요청의 작업 컨텍스트에 넣는다.
3. 가져온 지침이나 참고 내용을 사용자의 현재 작업에 적용한다.
4. 사용자가 스킬 가져오기, 설치, 갱신, 영구 적용, 저장도 요청하지 않았다면 `skills/` 파일을 쓰거나 수정하지 않는다.

그래도 최종 프로젝트 상태는 정적 파일이다. 동적으로 가져온 뒤 해석된 콘텐츠를 `skills/<skill-name>/SKILL.md`와 `skills/<skill-name>/SKILL_ko.md`에 기록해서, 네트워크가 없어도 프로젝트가 사용할 수 있게 유지한다.

## 가져오기 워크플로

1. 사용자가 UUID를 제공했는지 확인한다. 없으면 요청한다.
2. 사용자에게 선택적 `type` 인자를 받는다(예: `skill`, `guide`, `agent`). 제공하지 않으면 비워둔다 — 임의로 기본값을 넣지 않는다.
3. 게이트웨이를 호출한다.
   ```bash
   curl -s "$GATEWAY_URL/pages/by-uuid?uuid=<uuid>&type=<type>" | jq .
   # type을 제공하지 않은 경우 &type=<type> 생략
   ```
4. 응답을 파싱한다.
   - `pages.en` — 영어 페이지 (`null`일 수 있음)
   - `pages.ko` — 한국어 페이지 (`null`일 수 있음)
   - 각 페이지 객체에는 `content`(Markdown 원본), `title`, `description`, `locale`, `path`, `tags`, `contentHash` 포함
5. `pages.en`과 `pages.ko`가 모두 `null`이면 중단하고 `PAGE_NOT_FOUND`를 보고한다.
6. 영어 `content`의 frontmatter `name:` 필드에서 스킬 이름을 추출한다. frontmatter가 없으면 `title`을 slug 형태로 변환해 사용한다.
7. `name`을 `<skill-name>`으로 사용한다.
8. 영어 콘텐츠를 `skills/<skill-name>/SKILL.md`에 기록한다.
   - `pages.en`이 `null`이면 한국어 콘텐츠를 복사하고 영어 부재를 파일 헤더에 기록한다.
9. 한국어 콘텐츠를 `skills/<skill-name>/SKILL_ko.md`에 기록한다.
   - `pages.ko`가 `null`이면 영어 콘텐츠를 복사하고 한국어 부재를 파일 헤더에 기록한다.
10. 한국어 frontmatter가 있으면 영어 파일과 의미상 맞게 유지한다. 없으면 영어 frontmatter를 복사하고 본문은 한국어로 유지한다.
11. 가져온 스킬이 이 프로젝트에서 자동 적용되거나 참조되어야 할 때만 `AGENTS.md`와 `AGENTS_ko.md`를 갱신한다.

## 동적 참조 워크플로

사용자가 `LLM-wiki <uuid> 참고해줘` 같은 프롬프트로 현재 작업에서 Wiki.js 스킬을 참조하라고 요청하면 이 워크플로를 사용한다.

1. 사용자가 UUID를 제공했는지 확인한다.
2. UUID(와 type이 있으면 함께)를 사용해 게이트웨이의 `GET /pages/by-uuid`를 호출한다. 읽기 요청에는 인증 헤더 불필요.
3. 가져온 `content` 필드를 작업 로컬 컨텍스트로 사용한다.
4. 가져온 지침이 관련 있고 더 높은 우선순위의 system, developer, project 지침과 충돌하지 않을 때 따른다.
5. 어떤 UUID를 참조했는지, 어떤 locale이 있었는지 짧게 보고한다.
6. 사용자가 영구 가져오기나 프로젝트 레벨 적용을 명시적으로 요청하지 않았다면 프로젝트 파일을 생성하거나 갱신하지 않는다.

## 응답 구조 참고

```json
{
  "uuid": "550e8400-e29b-41d4-a716-446655440000",
  "type": "skill",
  "pages": {
    "en": {
      "id": 10,
      "path": "skill/550e8400-...",
      "locale": "en",
      "title": "My Skill",
      "description": "이 스킬이 하는 일",
      "content": "---\nname: my-skill\ndescription: ...\n---\n# My Skill\n...",
      "tags": ["skill"],
      "contentHash": "sha256..."
    },
    "ko": {
      "id": 11,
      "path": "skill/550e8400-...",
      "locale": "ko",
      "title": "내 스킬",
      "content": "---\nname: my-skill\n...\n---\n# 내 스킬\n...",
      "contentHash": "sha256..."
    }
  }
}
```

locale 값이 `null`이면 해당 locale 페이지가 존재하지 않는 것이다.

## 에러 처리

| 상황 | 대응 |
|------|------|
| 게이트웨이 연결 실패 | `curl $GATEWAY_URL/health`로 진단; 진행 중단 |
| 쓰기 시 401 / 403 | `GATEWAY_ADMIN_TOKEN`이 올바르게 설정되었는지 확인 |
| 두 locale 모두 404 | uuid에 대해 `PAGE_NOT_FOUND` 보고; 사용자가 best-effort를 요청하지 않으면 중단 |
| 한 locale만 404 | 가능한 locale을 작성; 파일 헤더에 누락된 locale 기록 |
| `content`가 비어 있음 | 사용자에게 경고; 빈 스킬 파일 작성 금지 |
| frontmatter에 `name` 없음 | `title`을 slug 변환해 스킬 이름으로 사용; 사용자에게 경고 |
