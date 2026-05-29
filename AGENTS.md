# AGENTS.md

이 파일은 이 레포지토리에서 작업하는 코딩 에이전트(Codex 등)의 작업 범위와 워크플로우를 정의한다.

> **참고**: 소스코드 수정이 필요한 구현 작업은 사용자의 명시적 요청이 있을 때만 수행한다. 기본 역할은 `instructions/` 지침 관리다.

---

## 현재 구현 상태

| 구분 | 상태 |
|------|------|
| MVP Core (Steps 0–10) | ✅ 완료 |
| 관리자 UI (Next.js + Tailwind) | ✅ 완료 |
| 인증 시스템 (JWT + API Key + 프로젝트 권한) | ✅ 완료 |
| 운영 준비 (API Key 인증, Audit Log, Backup, Observability) | ✅ 완료 |
| 관리자 콘솔 UI (로그인·사용자·프로젝트·멤버 화면) | ✅ 완료 |
| 인증 고급 (관리자·프로젝트 관리자 기능) | ✅ 완료 |
| 확장 기능 (pgvector, Revision, Export) | 🔲 pending |

테스트: **199 passed** (`backend/.venv/bin/pytest tests/`)

---

## 에이전트 작업 경계

- 기본 역할은 이 프로젝트의 `instructions/` 및 지침/지시문 관리다.
- 프로젝트 파일을 읽고 지침 맥락을 파악하는 것은 허용한다.
- 사용자가 명시적으로 요청하지 않는 한 소스코드 수정은 하지 않는다.
- 사용자가 명시적으로 요청하지 않는 한 빌드, 테스트, 포맷팅, 설치, 서버 실행 등 개발 흐름에 영향을 줄 수 있는 명령은 실행하지 않는다.
- 필요한 경우 낮은 영향도의 조회/확인 작업만 수행하고, 변경 작업은 사용자 의도를 먼저 확인한다.

---

## Instructions 워크플로우

모든 구현 작업은 `instructions/` 아래 지침 파일을 기준으로 진행한다.

### 지침 파일 생성

1. UUID 발급: `python3 -c "import uuid; print(uuid.uuid4())"`
2. `instructions/{slug}.md` 생성 — frontmatter에 uuid, title, status, created 기록
3. `instructions/instructions.log`에 한 줄 추가:
   ```
   {uuid} | {title} | {ISO8601 timestamp} | created
   ```
4. **브랜치 전략 스킬 필수 실행** — 스킬 `e03f48fb-3e00-41d7-b99d-c32854567d67`로 작업 브랜치를 생성한다.

### 지침 완료 처리

모든 단계 완료 시:

1. frontmatter `status: completed`, `completed: {날짜}` 기록
2. `instructions/.completed/{uuid}.md`로 이동
3. `instructions/instructions.log`에 `completed` 이벤트 추가
4. git commit

---

## Git Branch 전략

Step별 `feat/step{N}-{slug}` 브랜치 → PR → main 머지.

브랜치 전략 스킬: `e03f48fb-3e00-41d7-b99d-c32854567d67`

---

## LLM-wiki 스킬 참조

작업 완료 보고 및 리뷰 시 아래 스킬을 활용한다.

| UUID | 용도 |
|------|------|
| `a43a68f9-fda2-4960-a49a-0a97ebf96a8a` | 백엔드/인프라 완료 보고 |
| `4de41e4d-536a-44ca-8194-f8c5c316e6bf` | Full-stack 완료 보고 |
| `dbdfdbab-77ed-49fe-b70e-1f1708fc7aab` | 프론트엔드 완료 보고 |
| `69a9089b-a444-4f44-89ab-5d58210906ae` | PR 템플릿 |
| `ed847c29-b20a-420b-9314-c16dce184d62` | 코드 리뷰 |
| `e6274b24-2c08-4367-8859-b5a92bd98d59` | 정적 목업 확인용 서버 기동 (`static-mockup-preview-server`) |