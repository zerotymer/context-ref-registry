---
uuid: 19e52237-68d4-4952-8c30-dd0eb9285ff0
title: 배포 빌드 명령어 정리 (Docker Hub)
status: reference
created: 2026-06-03
---

# 배포 빌드 명령어 정리

## 이미지 구성

| 이미지 | 소스 경로 |
|--------|-----------|
| `llm-registry-api` | `./backend` |
| `llm-registry-front` | `./frontend` |

## 레지스트리 & 태그 매트릭스 (2 × 2 = 4개)

| 이미지 | 레지스트리 | 태그 | 풀네임 |
|--------|-----------|------|--------|
| api | Docker Hub | latest | `zerotymer/llm-registry-api:latest` |
| api | Docker Hub | 2.0.0 | `zerotymer/llm-registry-api:2.0.0` |
| front | Docker Hub | latest | `zerotymer/llm-registry-front:latest` |
| front | Docker Hub | 2.0.0 | `zerotymer/llm-registry-front:2.0.0` |

---

## 사전 준비 — 레지스트리 로그인

```bash
# Docker Hub
docker login

```

---

## 전체 빌드 & 푸시 절차

### Step 1 — 빌드 (로컬 임시 태그)

패키지는 **빌드하는 사람의 사용자 설정**(`~/.config/uv/uv.toml`, `~/.npmrc`)에 적힌 저장소에서 받는다.
두 파일을 BuildKit secret으로 마운트하므로 저장소 주소·인증 정보가 이미지 레이어·히스토리에 남지 않고,
프로젝트 소스에도 특정 저장소를 적지 않는다.

```bash
docker build --platform linux/amd64 --secret id=uv_config,src=$HOME/.config/uv/uv.toml \
  -t llm-registry-api:build ./backend
docker build --platform linux/amd64 --secret id=npmrc,src=$HOME/.npmrc \
  -t llm-registry-front:build ./frontend
```

> `--platform linux/amd64`: 배포 서버가 amd64인 경우 명시. arm Mac에서 빌드 시 필수.

### Step 2 — 태깅 (4개)

```bash
# api — Docker Hub
docker tag llm-registry-api:build zerotymer/llm-registry-api:latest
docker tag llm-registry-api:build zerotymer/llm-registry-api:2.0.0


# front — Docker Hub
docker tag llm-registry-front:build zerotymer/llm-registry-front:latest
docker tag llm-registry-front:build zerotymer/llm-registry-front:2.0.0

```

### Step 3 — 푸시 (4개)

```bash
# Docker Hub
docker push zerotymer/llm-registry-api:latest
docker push zerotymer/llm-registry-api:2.0.0
docker push zerotymer/llm-registry-front:latest
docker push zerotymer/llm-registry-front:2.0.0

```

---

## Makefile 타겟 (루트 Makefile에 추가)

> 버전 번호만 바꿔서 재사용할 수 있도록 변수 분리.

```makefile
VERSION ?= 2.0.0
DOCKERHUB_ORG = zerotymer
PLATFORM = linux/amd64

.PHONY: build tag push release

build:
	docker build --platform $(PLATFORM) -t llm-registry-api:build ./backend
	docker build --platform $(PLATFORM) -t llm-registry-front:build ./frontend

tag:
	docker tag llm-registry-api:build   $(DOCKERHUB_ORG)/llm-registry-api:latest
	docker tag llm-registry-api:build   $(DOCKERHUB_ORG)/llm-registry-api:$(VERSION)
	docker tag llm-registry-front:build $(DOCKERHUB_ORG)/llm-registry-front:latest
	docker tag llm-registry-front:build $(DOCKERHUB_ORG)/llm-registry-front:$(VERSION)

push:
	docker push $(DOCKERHUB_ORG)/llm-registry-api:latest
	docker push $(DOCKERHUB_ORG)/llm-registry-api:$(VERSION)
	docker push $(DOCKERHUB_ORG)/llm-registry-front:latest
	docker push $(DOCKERHUB_ORG)/llm-registry-front:$(VERSION)

release: build tag push
```

사용법:

```bash
make release              # VERSION=2.0.0 (기본값)
make release VERSION=2.1.0  # 버전 지정
```

---

## GitHub Actions 릴리스 (태그 push)

`v*.*.*` 태그를 push하면 `.github/workflows/release.yml`이 CI(`ci.yml`)를 통과시킨 뒤
api·front 이미지를 빌드해 `버전`·`latest` 태그로 Docker Hub에 푸시한다(4개).

```bash
git tag v2.1.0 && git push origin v2.1.0
```

필요한 Repository secrets:

| 이름 | 내용 |
|------|------|
| `UV_TOML` | `uv.toml` 전체. **기본(`default = true`) 인덱스는 GitHub 러너에서 접근 가능한 주소**여야 한다 (내부망 전용 주소 불가) |
| `NPMRC` | `.npmrc` 전체 (registry + 인증). 마찬가지로 러너에서 접근 가능한 registry |
| `DOCKERHUB_USERNAME` / `DOCKERHUB_TOKEN` | Docker Hub 푸시 계정 / 액세스 토큰 |

- `UV_TOML`·`NPMRC`가 비어 있으면 공개 저장소로 넘어가지 않고 실패한다.
- 의존성은 해시 고정 lock(`backend/requirements*.lock`, `frontend/pnpm-lock.yaml`)으로만 설치한다.
- 포크에서 온 PR에는 secrets가 전달되지 않아 CI가 실패한다.

## 주의 사항

- **DB 마이그레이션은 컨테이너 startup에 자동 적용** — `backend/entrypoint.sh`가 앱 실행 전
  `alembic upgrade head`를 수행한다(`ENTRYPOINT`). 빈 DB면 스키마 자동 생성, 최신이면 무충돌 no-op.
  신규 배포 시 수동 마이그레이션 단계 불필요. (CMD는 이미 `uvicorn ... --workers 2`로 고정됨)
- **MCP 서버는 `api` 이미지에 포함** — streamable-http로 `api` 앱의 `/mcp`에 마운트되므로
  별도 이미지·태그 추가 없이 기존 `llm-registry-api` 이미지로 함께 배포된다(4개 태그 영향 없음).
  stdio 단독 `mcp` 서비스는 폐기. 외부 노출 표면 단일화(BFF `/api/v1/mcp`)는 단계 C에서 처리.
- **backup 서비스 폐기** — DB가 SQLite 단일 파일이므로 `api` 정지 후 볼륨의
  `registry.db`, `registry.db-wal`, `registry.db-shm`을 함께 복사한다.
- **`ADMIN_PASSWORD` 필수** — 없으면 관리자 로그인이 503으로 막힌다. 배포 환경의 `.env`나
  secret으로만 주입하고 커밋하지 않는다. `JWT_SECRET`은 선택(없으면 기동마다 새로 생성).
- **데이터 볼륨** — 컨테이너는 non-root(`app`, uid 10001)로 실행되며 `/data`에 DB를 쓴다.
  named volume을 `/data`에 마운트한다(`registry_data:/data`).
