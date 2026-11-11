---
uuid: 19e52237-68d4-4952-8c30-dd0eb9285ff0
title: 배포 빌드 명령어 정리 (Docker Hub)
status: reference
created: 2026-06-03
updated: 2026-11-10
---

# 배포 빌드 명령어 정리

## 이미지 구성

| 이미지 | 소스 경로 |
|--------|-----------|
| `llm-registry-api` | `./backend` |
| `llm-registry-front` | `./frontend` |

## 태그 매트릭스 (2 × 2 = 4개)

| 이미지 | 태그 | 풀네임 |
|--------|------|--------|
| api | latest | `zerotymer/llm-registry-api:latest` |
| api | {VERSION} | `zerotymer/llm-registry-api:{VERSION}` |
| front | latest | `zerotymer/llm-registry-front:latest` |
| front | {VERSION} | `zerotymer/llm-registry-front:{VERSION}` |

---

## 사용법

```bash
docker login                  # Docker Hub (최초 1회)
make release                  # VERSION=2.1.0 (기본값)
make release VERSION=2.1.0    # 버전 지정
make -n release VERSION=2.1.0 # 실행 없이 명령만 확인
```

`make release` = `build` → `tag` → `push`. 정의는 루트 `Makefile` 참고.

> `--platform linux/amd64`: 배포 서버가 amd64 기준. arm Mac에서 빌드 시 필수 (Makefile `PLATFORM`).

---

## GitHub Actions 릴리스 (태그 push) — 권장

`v*.*.*` 태그를 push하면 `.github/workflows/release.yml`이 CI(`ci.yml`)를 통과시킨 뒤
api·front 이미지(linux/amd64)를 빌드해 **GHCR과 Docker Hub**에 `버전`·`latest`로 푸시한다(8개).

```bash
git tag v2.1.0 && git push origin v2.1.0
```

| 레지스트리 | 이미지 |
|-----------|--------|
| GHCR | `ghcr.io/zerotymer/llm-registry-api`, `ghcr.io/zerotymer/llm-registry-front` |
| Docker Hub | `zerotymer/llm-registry-api`, `zerotymer/llm-registry-front` |

필요한 secrets (GitHub Environment `DOCKER_HUB`): `DOCKERHUB_USERNAME`, `DOCKERHUB_TOKEN`(Docker Hub 액세스 토큰, Read & Write).
GHCR은 워크플로의 `GITHUB_TOKEN`으로 푸시한다. 새 GHCR 패키지는 비공개로 생성되므로 **첫 릴리스 후
GitHub → Packages → 패키지 설정에서 한 번 Public으로 변경**한다.

`make release`(아래)는 로컬에서 Docker Hub로만 푸시하는 수동 경로다.

## 주의 사항

- **DB 마이그레이션은 컨테이너 startup에 자동 적용** — `backend/entrypoint.sh`가 앱 실행 전
  `alembic upgrade head`를 수행한다(`ENTRYPOINT`). 빈 DB면 스키마 자동 생성, 최신이면 무충돌 no-op.
  신규 배포 시 수동 마이그레이션 단계 불필요. (CMD는 이미 `uvicorn ... --workers 2`로 고정됨)
- **MCP 서버는 `api` 이미지에 포함** — streamable-http로 `api` 앱의 `/mcp`에 마운트되므로
  별도 이미지·태그 추가 없이 기존 `llm-registry-api` 이미지로 함께 배포된다(태그 영향 없음).
  stdio 단독 `mcp` 서비스는 폐기. 외부 노출 표면 단일화(BFF `/api/v1/mcp`)는 단계 C에서 처리.
- **backup 서비스 폐기** — DB가 SQLite 단일 파일이므로 `api` 정지 후 볼륨의
  `registry.db`, `registry.db-wal`, `registry.db-shm`을 함께 복사한다.
- **`ADMIN_PASSWORD` 필수** — 없으면 관리자 로그인이 503으로 막힌다. 배포 환경의 `.env`나
  secret으로만 주입하고 커밋하지 않는다. `JWT_SECRET`은 선택(없으면 기동마다 새로 생성).
- **데이터 볼륨** — 컨테이너는 non-root(`app`, uid 10001)로 실행되며 `/data`에 DB를 쓴다.
  named volume을 `/data`에 마운트한다(`registry_data:/data`).
