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

```bash
docker build --platform linux/amd64 -t llm-registry-api:build ./backend
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

- **backend Dockerfile에 프로덕션 CMD 없음** — 현재 CMD는 `docker-compose.yml`에서 `--reload` 옵션으로 지정되어 있음. 빌드된 이미지 단독 실행 시 CMD를 명시해야 한다.
  ```dockerfile
  # backend/Dockerfile 하단에 추가 권장
  CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]
  ```
- **MCP 서버는 배포 이미지에서 제외** — stdio 방식으로 클라이언트가 직접 프로세스를 생성하므로 별도 이미지 배포 불필요.
- **backup 서비스도 배포 이미지에서 제외** — 운영 환경에서 별도 스케줄러(cron 등)로 대체.
