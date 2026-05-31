---
uuid: d679e0e0-ed7e-4de0-ba3d-554a83d3601c
title: API Key 프로젝트 기반 발급 및 접근 제어 강화
status: pending
created: 2026-05-31
---

# API Key 프로젝트 기반 발급 및 접근 제어 강화

## 배경 및 목적

현재 `ApiKey` 모델에 `project_id` 필드가 존재하지만 인증 레이어에서 **완전히 무시**되고 있다.
키가 어느 프로젝트에 속하든 소유자의 전체 멤버십 기반으로 접근 범위가 결정된다.

이번 작업은 API Key를 **프로젝트 단위로 발급·제한**하고 접근 제어 레이어에 실제로 반영한다.

## 확정된 정책

| 항목 | 정책 |
|------|------|
| 일반 사용자 발급 | `project_id` **필수**, 자신이 멤버인 프로젝트만 선택 가능 |
| 관리자 발급 | `project_id` **선택** — null이면 전역 키 |
| 프로젝트 키 접근 범위 | 해당 `project_id` 엔티티만 접근 가능, 타 프로젝트 → **403** |
| 전역 키(admin, null) 접근 범위 | 모든 프로젝트 접근 가능 (현행 admin 세션과 동일) |
| 레거시 키(일반 유저 + null) | 접근 범위 0으로 제한 → UI에서 재발급 유도 |

## 현재 Gap

### 백엔드

| 파일 | 현재 | 변경 필요 |
|------|------|----------|
| `auth/policy.py` | `get_visible_project_ids(user)` — api_key 무시 | api_key.project_id 반영 |
| `auth/dependencies.py` | api_key를 policy에 전달 안 함 | api_key 전달 경로 추가 |
| `api/auth.py` POST `/auth/api-keys` | project_id optional, admin 전용 → 이미 수정됨 | 일반 사용자: project_id 필수 검증 추가 |
| entity/alias/context 등 모든 read/write API | `policy.get_visible_project_ids(user)` 호출 | `(user, api_key)` 전달로 시그니처 변경 |

### 프론트엔드

| 화면 | 현재 | 변경 필요 |
|------|------|----------|
| `/settings/api-keys` 발급 모달 | 스코프만 선택 | 프로젝트 선택 드롭다운 추가 (필수) |
| `/admin/api-keys` 발급 모달 | 스코프만 선택 | 프로젝트 선택 드롭다운 추가 (선택, 미선택 = 전역) |
| API Key 목록 | project_id 미표시 | 프로젝트명 / "전역" 배지 표시 |
| 레거시 키(null + 일반유저) | 일반 활성 키처럼 표시 | "접근 제한됨" 경고 배지 + 재발급 안내 |

## 구현 단계

### Step 1 — 백엔드: policy.py 접근 제어 강화

**파일**: `backend/app/auth/policy.py`

`get_visible_project_ids` 시그니처 변경:

```python
async def get_visible_project_ids(
    self,
    user: UserAccount | None,
    api_key: ApiKey | None = None,
) -> list[str] | None:
```

로직:

```
api_key가 있을 때:
  api_key.project_id is not None
    → [api_key.project_id]  (단일 프로젝트 제한)
  api_key.project_id is None:
    소유자(created_by)가 admin 역할
      → None  (전역, 모든 프로젝트)
    소유자가 일반 user 또는 소유자 없음
      → []  (레거시 키, 접근 불가)

api_key가 없을 때 (세션 기반):
  기존 로직 유지 (user.role == "admin" → None, else 멤버십)
```

`check_can_view_entity` / `check_can_mutate_entity`는 변경 없음.
`get_visible_project_ids`의 반환값이 이미 이 메서드들을 결정하므로 충분.

### Step 2 — 백엔드: api_key를 policy 호출에 전달

**영향 파일**: `api/entities.py`, `api/aliases.py`, `api/contexts.py`, `api/relations.py`, `api/tags.py`, `api/search.py`, `api/bundles.py`, `api/ingest.py`

각 엔드포인트에서 `policy.get_visible_project_ids(user)` →
`policy.get_visible_project_ids(user, api_key)` 로 변경.

`api_key`는 이미 `get_actor` Depends에서 `(user, api_key)` 튜플로 받고 있음.
**write 엔드포인트**: `check_can_assign_project`, `check_can_mutate_entity`도 api_key 기반
제한 필요.

write 정책 추가:

```
api_key가 있고 project_id가 지정된 경우:
  api_key.project_id != 대상 entity.project_id → 403
api_key가 있고 project_id=null(전역):
  admin 전역 키 → 통과
  레거시 키 → 403
```

> `check_can_mutate_entity`에 `api_key` 파라미터 추가로 처리.

### Step 3 — 백엔드: 발급 유효성 검증 강화

**파일**: `backend/app/api/auth.py`, `backend/app/service/auth_service.py`

`POST /auth/api-keys` (일반 사용자 엔드포인트) 변경:
- `project_id`가 `None`이면 → `422 PROJECT_REQUIRED`
- `project_id`가 있으면 → 해당 프로젝트 멤버십 확인 (없으면 `403 FORBIDDEN`)

`POST /admin/api-keys` (관리자 엔드포인트) 변경:
- `project_id`가 있으면 → 프로젝트 존재 확인 (없으면 `404`)
- `project_id=null` → 전역 키 발급 (허용)

`AuthService.create_api_key` 파라미터 변경 없음.
검증은 API 레이어에서 처리.

### Step 4 — 백엔드: 테스트 업데이트

**파일**: `backend/tests/test_api_key_management.py`

추가 테스트 케이스:

```
- 일반 사용자: project_id 없이 발급 시도 → 422
- 일반 사용자: 비멤버 프로젝트로 발급 시도 → 403
- 일반 사용자: 멤버 프로젝트로 발급 → 200, project_id 포함
- 프로젝트 키: 해당 프로젝트 엔티티 GET → 200
- 프로젝트 키: 타 프로젝트 엔티티 GET → 403
- 전역 키(admin): 모든 프로젝트 엔티티 GET → 200
- 레거시 키(null + user): 엔티티 GET → 403
```

기존 `test_auth_api.py`의 api-key 관련 케이스도 project_id 필수 반영 수정.

### Step 5 — 프론트엔드: Server Actions 수정

**파일**: `frontend/src/lib/actions/api-keys.ts`

```typescript
// 타입 변경
export type ApiKeyItem = {
  id: string;
  name: string;
  scopes: string[];
  project_id: string | null;   // 이미 있음
  project_name?: string;       // ← 추가 (join 또는 별도 조회)
  created_at: string;
  revoked_at: string | null;
  is_active: boolean;
  is_legacy: boolean;          // ← 추가: project_id=null + non-admin 발급
};

// createApiKey 변경: project_id 필수
export async function createApiKey(body: {
  name: string;
  scopes: string[];
  project_id: string;          // ← optional → required (사용자용)
}): Promise<{ id: string; name: string; key: string }>

// 새 액션 추가
export async function listMyProjects(): Promise<{ id: string; name: string }[]>
```

**파일**: `frontend/src/lib/actions/admin.ts` 또는 `api-keys.ts`

```typescript
// 관리자 발급: project_id optional 유지
export async function adminCreateApiKey(body: {
  name: string;
  scopes: string[];
  project_id?: string;         // null = 전역
}): Promise<{ id: string; name: string; key: string }>
```

### Step 6 — 프론트엔드: 사용자 화면 수정

**파일**: `frontend/src/app/(app)/settings/api-keys/ApiKeyPanel.tsx`

**발급 모달 변경**:
- 스코프 체크박스 위에 프로젝트 선택 `<select>` 추가
- 옵션: `listMyProjects()` 결과 → `<option value={p.id}>{p.name}</option>`
- 프로젝트 미선택 시 제출 불가 (required)

**목록 테이블 변경**:

| 이름 | 프로젝트 | 스코프 | 생성일 | 상태 | 액션 |
|------|---------|--------|--------|------|------|
| ci-bot | **my-project** | read:entities | 2026-05-30 | 활성 | [폐기] |
| old-key | ⚠️ **접근 제한** | read:entities | 2026-05-01 | 활성 | [폐기] |

- `is_legacy=true` 키: 행 배경 노란색, 프로젝트 열에 `⚠️ 접근 제한됨` 배지
- 테이블 상단 레거시 키 경고 배너: "project_id가 없는 키는 더 이상 접근이 허용되지 않습니다. 재발급하세요."

### Step 7 — 프론트엔드: 관리자 화면 수정

**파일**: `frontend/src/app/(app)/admin/api-keys/AdminApiKeyPanel.tsx`

**발급 모달 변경**:
- 프로젝트 선택 `<select>` 추가 (선택, 미선택 = 전역)
- 전역 옵션: `<option value="">전역 (모든 프로젝트)</option>`

**목록 테이블 변경**:
- 프로젝트 열: 프로젝트명 표시, null이면 `전역` 배지 (파란색)
- `is_legacy=true` 키: `⚠️ 접근 제한` 배지 (관리자는 폐기 처리 유도)

### Step 8 — 백엔드: ApiKeyRead 스키마에 project_name 추가 (선택)

프론트엔드에서 프로젝트명을 표시하려면 별도 조회가 필요하다.
구현 방식 2가지:

**옵션 A**: `AdminApiKeyRead`에 `project_name: str | None` 추가, 백엔드에서 JOIN
**옵션 B**: 프론트엔드에서 프로젝트 목록과 대조

→ **옵션 A 권장** (백엔드 JOIN이 명확, N+1 방지)

`ApiKeyRepository.list_all()`에서 `Project` 테이블 LEFT JOIN 추가:
```python
class AdminApiKeyRead(ApiKeyRead):
    created_by_email: str | None
    project_name: str | None     # ← 추가
```

일반 사용자 `ApiKeyRead`도 `project_name` 추가:
```python
class ApiKeyRead(BaseModel):
    ...
    project_name: str | None     # ← 추가
    is_legacy: bool              # ← 추가 (project_id is None and not admin-issued)
```

## 파일 변경 목록 (전체)

### 백엔드
```
backend/app/auth/policy.py                     ← get_visible_project_ids 시그니처 변경
backend/app/api/auth.py                        ← project_id 필수 검증 (사용자)
backend/app/api/entities.py                    ← api_key 전달
backend/app/api/aliases.py                     ← api_key 전달
backend/app/api/contexts.py                    ← api_key 전달
backend/app/api/relations.py                   ← api_key 전달
backend/app/api/tags.py                        ← api_key 전달
backend/app/api/search.py                      ← api_key 전달
backend/app/api/bundles.py                     ← api_key 전달
backend/app/api/ingest.py                      ← api_key 전달
backend/app/api/admin_api_keys.py              ← project_id 존재 확인
backend/app/repository/api_key_repository.py   ← list_all에 project_name JOIN 추가
backend/app/domain/schemas.py                  ← ApiKeyRead, AdminApiKeyRead 필드 추가
backend/tests/test_api_key_management.py       ← 케이스 추가
backend/tests/test_auth_api.py                 ← project_id 필수 반영
```

### 프론트엔드
```
frontend/src/lib/actions/api-keys.ts           ← 타입·액션 변경
frontend/src/app/(app)/settings/api-keys/ApiKeyPanel.tsx    ← 모달·테이블 변경
frontend/src/app/(app)/admin/api-keys/AdminApiKeyPanel.tsx  ← 모달·테이블 변경
```

## DoD (완료 기준)

- [ ] Step 1: `policy.py` — api_key.project_id 기반 접근 범위 분기
- [ ] Step 2: 모든 read/write API 엔드포인트에 api_key 전달
- [ ] Step 3: 발급 유효성 검증 (user: project_id 필수, admin: optional)
- [ ] Step 4: 테스트 전체 pass (기존 + 신규 케이스 포함)
- [ ] Step 5: Server Actions 타입·함수 수정
- [ ] Step 6: 사용자 화면 프로젝트 선택 + 레거시 키 경고
- [ ] Step 7: 관리자 화면 프로젝트 선택 + 전역/레거시 배지
- [ ] Step 8: 백엔드 project_name JOIN, 스키마 반영
- [ ] 프론트엔드 빌드 오류 없음
