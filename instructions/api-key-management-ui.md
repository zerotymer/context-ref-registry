---
uuid: c4309c75-5633-4187-a785-3b40c8e037b2
title: API Key 관리 UI — 사용자/관리자 화면 구현
status: pending
created: 2026-05-31
---

# API Key 관리 UI — 사용자/관리자 화면 구현

## 배경 및 목적

백엔드에 `POST /auth/api-keys` 발급 엔드포인트는 있으나 목록 조회·폐기 API와
프론트엔드 화면이 모두 없다. 코딩 에이전트·CI 파이프라인이 API Key를 직접
발급·관리할 수 있도록 관리자 전용 화면과 일반 사용자 셀프서비스 화면을 함께 구현한다.

## 현재 상태 (Gap)

### 백엔드
| 항목 | 현황 |
|------|------|
| `POST /auth/api-keys` | ✅ 있음 — **admin 전용** (수정 필요) |
| `GET /auth/api-keys` | ❌ 없음 — 내 키 목록 |
| `DELETE /auth/api-keys/{id}` | ❌ 없음 — 키 폐기 |
| `GET /admin/api-keys` | ❌ 없음 — 전체 키 목록 (admin 전용) |
| `ApiKeyRepository.list_by_user` | ❌ 없음 |
| `ApiKeyRepository.revoke` | ❌ 없음 |

### 프론트엔드
| 항목 | 현황 |
|------|------|
| `/settings/api-keys` 페이지 | ❌ 없음 |
| `/admin/api-keys` 페이지 | ❌ 없음 |
| Sidebar "API 설정" 메뉴 | ❌ 없음 |
| Server Actions (`api-keys.ts`) | ❌ 없음 |

## 설계

### Scope 목록 (공통 상수)

```python
VALID_SCOPES = [
    "read:entities",   # Entity/Alias/Context/Relation 읽기
    "write:entities",  # Entity 생성·수정
    "ingest",          # POST /ingest/batch
    "read:all",        # 전체 읽기 (superscope)
]
```

### 권한 모델

| 기능 | 일반 user | project_admin | admin |
|------|-----------|---------------|-------|
| 내 키 목록 조회 | ✅ | ✅ | ✅ |
| 내 키 발급 | ✅ | ✅ | ✅ |
| 내 키 폐기 | ✅ | ✅ | ✅ |
| 전체 키 목록 조회 | ❌ | ❌ | ✅ |
| 타인 키 폐기 | ❌ | ❌ | ✅ |

→ `POST /auth/api-keys`를 **일반 user도 사용 가능**하도록 변경 (admin 전용 → 로그인 사용자 전용)

### 화면 구성

#### A. 사용자 화면 `/settings/api-keys` (모든 로그인 사용자)

```
┌──────────────────────────────────────────────────────────┐
│ API 설정                              [+ 새 API Key 발급] │
├──────────────────────────────────────────────────────────┤
│ 이름         스코프              생성일       상태  액션 │
│ ci-bot    read:entities ingest  2026-05-30   활성  [폐기] │
│ cursor    read:all               2026-05-28   활성  [폐기] │
│ old-key   read:entities          2026-05-01  폐기됨  -   │
└──────────────────────────────────────────────────────────┘
```

- 발급 모달: 이름 입력 + 스코프 다중 선택 (체크박스)
- 발급 완료 모달: Raw Key 표시 (한 번만 보임) + 복사 버튼
- 폐기: 확인 다이얼로그 후 `DELETE /auth/api-keys/{id}`

#### B. 관리자 화면 `/admin/api-keys` (admin 전용)

```
┌────────────────────────────────────────────────────────────────────┐
│ API Key 관리                                      [+ 키 발급]      │
├──────────────────────────────────────────────────────────────────  ┤
│  소유자           이름       스코프      생성일       상태  액션   │
│  alice@co    ci-bot   read:entities  2026-05-30   활성  [폐기]     │
│  bob@co      cursor   read:all       2026-05-28   활성  [폐기]     │
└────────────────────────────────────────────────────────────────────┘
```

- 소유자 필터 (이메일 검색)
- 활성/폐기 필터
- 관리자가 타인 키를 대신 발급하거나 폐기 가능

#### C. Sidebar 변경

```
[기존 공통 메뉴]
  Dashboard
  Entity 목록
  승인 대기
  Bundle 탐색기
+ API 설정          ← 신규 (모든 사용자)

[관리자 섹션 — admin만]
  사용자 관리
  프로젝트 관리
+ API Key 관리      ← 신규 (admin만)
```

## 구현 단계

### Step 1 — 백엔드: API Key 목록·폐기 엔드포인트 추가

파일: `backend/app/repository/api_key_repository.py`
- `list_by_user(user_id)` → `list[ApiKey]` (revoked_at IS NULL 포함 전체, 최신순)
- `list_all(created_by_email=None, is_active=None)` → `list[ApiKey]` (admin용, JOIN user_account)
- `revoke(api_key_id)` → `ApiKey` (revoked_at = now())

파일: `backend/app/service/auth_service.py`
- `list_api_keys(user_id)` → `list[ApiKey]`
- `list_all_api_keys(...)` → `list[ApiKey]` (admin용)
- `revoke_api_key(api_key_id, actor_id, is_admin)` → 소유자 본인 or admin만 허용

파일: `backend/app/api/auth.py`
- `POST /auth/api-keys` — `get_current_admin` → `get_current_user` 변경 (일반 user 허용)
- `GET /auth/api-keys` — 내 키 목록 (로그인 사용자)
- `DELETE /auth/api-keys/{key_id}` — 폐기 (본인 or admin)

파일: `backend/app/api/auth.py` 또는 `admin_api_keys.py`
- `GET /admin/api-keys` — 전체 목록 (admin 전용, 소유자 정보 포함)

응답 스키마 추가 (`ApiKeyRead` 확장):
```python
class ApiKeyRead(BaseModel):
    id: UUID
    name: str
    scopes: list[str]
    project_id: UUID | None
    created_at: str
    revoked_at: str | None    # ← 추가
    is_active: bool           # ← 계산 필드 (revoked_at is None)

class AdminApiKeyRead(ApiKeyRead):
    created_by_email: str | None   # ← admin 전용
```

테스트 파일 신규 생성: `backend/tests/test_api_key_management.py`
- 일반 user 발급/목록/폐기 정상 흐름
- 타인 키 폐기 → 403
- admin 전체 목록 조회
- admin 타인 키 폐기

### Step 2 — 프론트엔드: Server Actions 추가

파일: `frontend/src/lib/actions/api-keys.ts`

```typescript
export type ApiKeyItem = {
  id: string;
  name: string;
  scopes: string[];
  project_id: string | null;
  created_at: string;
  revoked_at: string | null;
  is_active: boolean;
};

export type AdminApiKeyItem = ApiKeyItem & {
  created_by_email: string | null;
};

export async function listMyApiKeys(): Promise<ApiKeyItem[]>
export async function createApiKey(body: { name: string; scopes: string[] }): Promise<{ id: string; name: string; key: string }>
export async function revokeApiKey(id: string): Promise<void>
export async function listAdminApiKeys(params?: { search?: string; is_active?: boolean }): Promise<AdminApiKeyItem[]>
export async function adminRevokeApiKey(id: string): Promise<void>
```

### Step 3 — 프론트엔드: 사용자 화면

파일 신규: `frontend/src/app/(app)/settings/api-keys/page.tsx` (Server Component)
파일 신규: `frontend/src/app/(app)/settings/api-keys/ApiKeyPanel.tsx` (Client Component)

`ApiKeyPanel` 포함 기능:
- API Key 목록 테이블 (이름, 스코프 배지, 생성일, 상태, 폐기 버튼)
- `CreateApiKeyModal`: 이름 + 스코프 다중 체크박스
- `KeyRevealModal`: 발급 직후 Raw Key 표시 + 복사 버튼 + 경고 문구
- 폐기 시 `confirm()` 다이얼로그

### Step 4 — 프론트엔드: 관리자 화면

파일 신규: `frontend/src/app/(app)/admin/api-keys/page.tsx` (Server Component, admin redirect)
파일 신규: `frontend/src/app/(app)/admin/api-keys/AdminApiKeyPanel.tsx` (Client Component)

`AdminApiKeyPanel` 포함 기능:
- 전체 Key 목록 테이블 (소유자 이메일, 이름, 스코프, 생성일, 상태, 폐기)
- 소유자 이메일 검색 필터
- 활성/폐기 필터
- 대신 발급 모달 (소유자 이메일 선택 또는 미지정)

### Step 5 — Sidebar 메뉴 추가

파일: `frontend/src/components/layout/Sidebar.tsx`
- `baseItems`에 "API 설정" (`/settings/api-keys`) 추가 — 키 아이콘
- `adminItems`에 "API Key 관리" (`/admin/api-keys`) 추가

## DoD (완료 기준)

- [ ] Step 1: `GET /auth/api-keys`, `DELETE /auth/api-keys/{id}`, `GET /admin/api-keys` 구현 및 테스트 통과
- [ ] Step 2: `api-keys.ts` Server Actions 구현
- [ ] Step 3: `/settings/api-keys` 사용자 화면 — 목록·발급·Raw Key 표시·폐기 동작
- [ ] Step 4: `/admin/api-keys` 관리자 화면 — 전체 목록·필터·폐기 동작
- [ ] Step 5: Sidebar 메뉴 표시 확인
- [ ] 전체 테스트 pass (`pytest tests/`)
- [ ] 프론트엔드 빌드 오류 없음 (`next build` or 컨테이너 재기동 확인)

## 목업 참조

`output/api-key-management-mockup.html` 참조
