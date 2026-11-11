---
uuid: 19e52237-68d4-4952-8c30-dd0eb9285ff0
title: 배포 빌드 명령어 정리 (Docker Hub + Nexus OSS)
status: reference
created: 2026-06-03
---

# 배포 빌드 명령어 정리

## 이미지 구성

| 이미지 | 소스 경로 |
|--------|-----------|
| `llm-registry-api` | `./backend` |
| `llm-registry-front` | `./frontend` |

## 레지스트리 & 태그 매트릭스 (2 × 2 × 2 = 8개)

| 이미지 | 레지스트리 | 태그 | 풀네임 |
|--------|-----------|------|--------|
| api | Docker Hub | latest | `zerotymer/llm-registry-api:latest` |
| api | Docker Hub | 1.0.0 | `zerotymer/llm-registry-api:1.0.0` |
| api | Nexus OSS | latest | `nexus.zerotymer.net/docker/llm-registry-api:latest` |
| api | Nexus OSS | 1.0.0 | `nexus.zerotymer.net/docker/llm-registry-api:1.0.0` |
| front | Docker Hub | latest | `zerotymer/llm-registry-front:latest` |
| front | Docker Hub | 1.0.0 | `zerotymer/llm-registry-front:1.0.0` |
| front | Nexus OSS | latest | `nexus.zerotymer.net/docker/llm-registry-front:latest` |
| front | Nexus OSS | 1.0.0 | `nexus.zerotymer.net/docker/llm-registry-front:1.0.0` |

---

## 사전 준비 — 레지스트리 로그인

```bash
# Docker Hub
docker login

# Nexus OSS
docker login nexus.zerotymer.net
```

---

## 전체 빌드 & 푸시 절차

### Step 1 — 빌드 (로컬 임시 태그)

API 이미지는 의존성을 **개인 Nexus PyPI 인덱스로만** 받는다. 인증이 포함된 인덱스 URL을
BuildKit secret으로 넘기므로 이미지 레이어·히스토리에 남지 않는다.

```bash
# 셸에서만 설정 (커밋·.env 금지)
export NEXUS_PYPI_URL='https://<user>:<pass>@nexus.zerotymer.net/repository/pypi/simple'

docker build --platform linux/amd64 --secret id=nexus_pypi,env=NEXUS_PYPI_URL \
  -t llm-registry-api:build ./backend
docker build --platform linux/amd64 -t llm-registry-front:build ./frontend
```

> `--platform linux/amd64`: 배포 서버가 amd64인 경우 명시. arm Mac에서 빌드 시 필수.

### Step 2 — 태깅 (8개)

```bash
# api — Docker Hub
docker tag llm-registry-api:build zerotymer/llm-registry-api:latest
docker tag llm-registry-api:build zerotymer/llm-registry-api:1.0.0

# api — Nexus OSS
docker tag llm-registry-api:build nexus.zerotymer.net/docker/llm-registry-api:latest
docker tag llm-registry-api:build nexus.zerotymer.net/docker/llm-registry-api:1.0.0

# front — Docker Hub
docker tag llm-registry-front:build zerotymer/llm-registry-front:latest
docker tag llm-registry-front:build zerotymer/llm-registry-front:1.0.0

# front — Nexus OSS
docker tag llm-registry-front:build nexus.zerotymer.net/docker/llm-registry-front:latest
docker tag llm-registry-front:build nexus.zerotymer.net/docker/llm-registry-front:1.0.0
```

### Step 3 — 푸시 (8개)

```bash
# Docker Hub
docker push zerotymer/llm-registry-api:latest
docker push zerotymer/llm-registry-api:1.0.0
docker push zerotymer/llm-registry-front:latest
docker push zerotymer/llm-registry-front:1.0.0

# Nexus OSS
docker push nexus.zerotymer.net/docker/llm-registry-api:latest
docker push nexus.zerotymer.net/docker/llm-registry-api:1.0.0
docker push nexus.zerotymer.net/docker/llm-registry-front:latest
docker push nexus.zerotymer.net/docker/llm-registry-front:1.0.0
```

---

## Makefile 타겟 (루트 Makefile에 추가)

> 버전 번호만 바꿔서 재사용할 수 있도록 변수 분리.

```makefile
VERSION ?= 1.0.0
DOCKERHUB_ORG = zerotymer
NEXUS = nexus.zerotymer.net/docker
PLATFORM = linux/amd64

.PHONY: build tag push release

build:
	docker build --platform $(PLATFORM) -t llm-registry-api:build ./backend
	docker build --platform $(PLATFORM) -t llm-registry-front:build ./frontend

tag:
	docker tag llm-registry-api:build   $(DOCKERHUB_ORG)/llm-registry-api:latest
	docker tag llm-registry-api:build   $(DOCKERHUB_ORG)/llm-registry-api:$(VERSION)
	docker tag llm-registry-api:build   $(NEXUS)/llm-registry-api:latest
	docker tag llm-registry-api:build   $(NEXUS)/llm-registry-api:$(VERSION)
	docker tag llm-registry-front:build $(DOCKERHUB_ORG)/llm-registry-front:latest
	docker tag llm-registry-front:build $(DOCKERHUB_ORG)/llm-registry-front:$(VERSION)
	docker tag llm-registry-front:build $(NEXUS)/llm-registry-front:latest
	docker tag llm-registry-front:build $(NEXUS)/llm-registry-front:$(VERSION)

push:
	docker push $(DOCKERHUB_ORG)/llm-registry-api:latest
	docker push $(DOCKERHUB_ORG)/llm-registry-api:$(VERSION)
	docker push $(NEXUS)/llm-registry-api:latest
	docker push $(NEXUS)/llm-registry-api:$(VERSION)
	docker push $(DOCKERHUB_ORG)/llm-registry-front:latest
	docker push $(DOCKERHUB_ORG)/llm-registry-front:$(VERSION)
	docker push $(NEXUS)/llm-registry-front:latest
	docker push $(NEXUS)/llm-registry-front:$(VERSION)

release: build tag push
```

사용법:

```bash
make release              # VERSION=1.0.0 (기본값)
make release VERSION=1.1.0  # 버전 지정
```

---

## 주의 사항

- **DB 마이그레이션은 컨테이너 startup에 자동 적용** — `backend/entrypoint.sh`가 앱 실행 전
  `alembic upgrade head`를 수행한다(`ENTRYPOINT`). 빈 DB면 스키마 자동 생성, 최신이면 무충돌 no-op.
  신규 배포 시 수동 마이그레이션 단계 불필요. (CMD는 이미 `uvicorn ... --workers 2`로 고정됨)
- **MCP 서버는 `api` 이미지에 포함** — streamable-http로 `api` 앱의 `/mcp`에 마운트되므로
  별도 이미지·태그 추가 없이 기존 `llm-registry-api` 이미지로 함께 배포된다(8개 태그 영향 없음).
  stdio 단독 `mcp` 서비스는 폐기. 외부 노출 표면 단일화(BFF `/api/v1/mcp`)는 단계 C에서 처리.
- **backup 서비스 폐기** — DB가 SQLite 단일 파일이므로 `api` 정지 후 볼륨의
  `registry.db`, `registry.db-wal`, `registry.db-shm`을 함께 복사한다.
- **`ADMIN_PASSWORD` 필수** — 없으면 관리자 로그인이 503으로 막힌다. 배포 환경의 `.env`나
  secret으로만 주입하고 커밋하지 않는다. `JWT_SECRET`은 선택(없으면 기동마다 새로 생성).
- **데이터 볼륨** — 컨테이너는 non-root(`app`, uid 10001)로 실행되며 `/data`에 DB를 쓴다.
  named volume을 `/data`에 마운트한다(`registry_data:/data`).
