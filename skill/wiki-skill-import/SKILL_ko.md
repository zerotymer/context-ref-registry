---
name: wiki-skill-import
description: Use when importing a project-local skill from the md.zerotymer.net Wiki.js site by UUID; fetches English and Korean pages and writes SKILL.md and SKILL_ko.md.
---

# Wiki Skill Import

사용자가 skill UUID를 제공하면 `https://md.zerotymer.net`의 Wiki.js 사이트에서
프로젝트 로컬 스킬을 가져온다.

이 스킬은 두 가지 모드를 지원한다.

- 동적 참조 모드: 현재 요청을 위해 Wiki.js 페이지를 가져와 파일을 쓰지 않고
  컨텍스트로만 사용한다.
- 가져오기 모드: Wiki.js 페이지를 가져와 프로젝트 로컬 스킬 파일로 기록한다.

가져온 스킬은 다음 구조를 따라야 한다.

```text
skills/<skill-name>/
├── SKILL.md
└── SKILL_ko.md
```

`SKILL.md`는 영어 기준 지침 파일이다. `SKILL_ko.md`는 한국어 읽기용 사본이며
의미상 같은 내용을 유지해야 한다.

## 가져오기 전략

가능하면 GraphQL을 우선한다.

GraphQL은 원본 Markdown, frontmatter, 제목, 설명, locale, 페이지 메타데이터를
구조화된 응답으로 받을 수 있으므로 자동화에 가장 적합하다. 렌더링된 HTML을
스크래핑하지 않아도 되고, 코드 블록, 표, frontmatter, Markdown 문법을 더 안정적으로
보존한다.

GraphQL이 공개되어 있지 않거나 설정되지 않은 인증 정보가 필요하면 공개 페이지
HTML을 fallback으로 사용한다. HTML fallback은 읽기 전용 복구에는 쓸 수 있지만
손실이 있다. Wiki.js가 frontmatter처럼 보이는 내용을 HTML 제목으로 렌더링하고,
코드 블록은 사이트 마크업으로 감싸며, Markdown을 다시 구성해야 한다.

두 방법이 모두 실패하면 실패 원인을 명확히 보고하고, 사용자가 best-effort
가져오기를 요청하지 않는 한 부분적인 스킬 파일을 만들지 않는다.

## 동적 방식과 정적 방식

동적 가져오기는 허용된다.

사용자가 UUID를 제공하고 스킬 참조, 가져오기, 갱신을 요청하면, 요청 시점에 최신
영어와 한국어 콘텐츠를 가져온다. 사용자가 오프라인 또는 정적 동작을 명시적으로
요청하지 않는 한 이전에 다운로드한 사본에 의존하지 않는다.

사용자가 `LLM-wiki <uuid> 참고해줘` 같은 명령을 말하면 기본적으로 동적 참조
모드를 사용한다.

1. 요청 시점에 관련 Wiki.js 콘텐츠를 가져온다.
2. 가져온 콘텐츠를 현재 요청의 작업 컨텍스트에 넣는다.
3. 가져온 지침이나 참고 내용을 사용자의 현재 작업에 적용한다.
4. 사용자가 스킬 가져오기, 설치, 갱신, 영구 적용, 저장도 요청하지 않았다면
   `skills/` 파일을 쓰거나 수정하지 않는다.

그래도 최종 프로젝트 상태는 정적 파일이다. 동적으로 가져온 뒤 해석된 콘텐츠를
`skills/<skill-name>/SKILL.md`와 `skills/<skill-name>/SKILL_ko.md`에 기록해서,
네트워크가 없어도 프로젝트가 사용할 수 있게 유지한다.

## URL 패턴

`<uuid>` 같은 UUID가 주어지면 다음 공개 읽기 URL을 기준 페이지 위치로 사용한다.

```text
https://md.zerotymer.net/en/skill/<uuid>
https://md.zerotymer.net/ko/skill/<uuid>
```

편집용 경로인 `/e/<locale>/skill/<uuid>`는 공개 읽기 경로가 아니며 인증 페이지를
반환할 수 있다. 공개 HTML을 가져오기 전에 `/<locale>/skill/<uuid>`로 변환한다.

## 가져오기 워크플로

1. 사용자가 UUID를 제공했는지 확인한다.
2. `/en/skill/<uuid>`에서 영어 콘텐츠를 가져온다.
3. `/ko/skill/<uuid>`에서 한국어 콘텐츠를 가져온다.
4. 가능하면 GraphQL 원본 Markdown을 사용하고, 아니면 공개 HTML을 사용해 Markdown을
   보수적으로 재구성한다.
5. 영어 콘텐츠에 최소 `name`과 `description`을 포함한 유효한 skill frontmatter가
   있는지 확인한다.
6. frontmatter의 `name` 값을 `<skill-name>`으로 사용한다.
7. 영어 콘텐츠를 `skills/<skill-name>/SKILL.md`에 기록한다.
8. 한국어 콘텐츠를 `skills/<skill-name>/SKILL_ko.md`에 기록한다.
9. 한국어 frontmatter가 있으면 영어 파일과 의미상 맞게 유지한다. 없으면 영어
   frontmatter를 복사하고 본문은 한국어로 유지한다.
10. 가져온 스킬이 이 프로젝트에서 자동 적용되거나 참조되어야 할 때만 `AGENTS.md`와
    `AGENTS_ko.md`를 갱신한다.

## 동적 참조 워크플로

사용자가 `LLM-wiki <uuid> 참고해줘` 같은 프롬프트로 현재 작업에서 Wiki.js 스킬을
참조하라고 요청하면 이 워크플로를 사용한다.

1. 사용자가 UUID를 제공했는지 확인한다.
2. 요청 시점에 영어와 한국어 콘텐츠를 동적으로 가져온다.
3. 가능하면 GraphQL 원본 Markdown을 사용하고, 필요하면 공개 HTML로 fallback한다.
4. 가져온 콘텐츠를 작업 로컬 컨텍스트로 사용한다.
5. 가져온 지침이 관련 있고 더 높은 우선순위의 system, developer, project 지침과
   충돌하지 않을 때 따른다.
6. 어떤 Wiki.js UUID를 참조했는지 짧게 보고한다.
7. 사용자가 영구 가져오기나 프로젝트 레벨 적용을 명시적으로 요청하지 않았다면
   프로젝트 파일을 생성하거나 갱신하지 않는다.

## API 비교

GraphQL:

- 원본 보존형 가져오기에 가장 적합하다.
- 인증되면 구조화된 페이지 데이터를 반환한다.
- 자동화, 검증, 이후 갱신에 더 적합하다.
- API 토큰이나 공개 GraphQL 접근 권한이 필요할 수 있다.
- 스키마 탐색 또는 알려진 Wiki.js GraphQL query가 필요하다.

공개 HTML:

- 페이지가 공개 읽기 가능하면 동작한다.
- API 인증 정보가 필요 없다.
- 일회성 가져오기 fallback으로 적합하다.
- 원본 충실도가 떨어지고 HTML-to-Markdown 재구성이 필요하다.
- 렌더링 테마나 마크업이 바뀌면 깨질 수 있다.

이 프로젝트에서는 반복 가능한 자동화를 위해 GraphQL을 우선하고, 비인증 접근을 위해
공개 HTML fallback을 유지한다.
