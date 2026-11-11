---
uuid: 19e52237-68d4-4952-8c30-dd0eb9285ff0
title: 배포 빌드 명령어 정리 (Docker Hub)
status: reference
created: 2026-06-03
updated: 2026-11-10
---

# 배포 빌드 명령어 정리

> 2026-11-10: Nexus OSS(`nexus.zerotymer.net/docker`)는 더 이상 공유 대상이 아니므로 배포에서 제외. Docker Hub 단독.

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
make release                  # VERSION=1.0.0 (기본값)
make release VERSION=1.1.0    # 버전 지정
make -n release VERSION=1.1.0 # 실행 없이 명령만 확인
```

`make release` = `build` → `tag` → `push`. 정의는 루트 `Makefile` 참고.

> `--platform linux/amd64`: 배포 서버가 amd64 기준. arm Mac에서 빌드 시 필수 (Makefile `PLATFORM`).

---

## 주의 사항

- **DB 마이그레이션은 컨테이너 startup에 자동 적용** — `backend/entrypoint.sh`가 앱 실행 전
  `alembic upgrade head`를 수행한다(`ENTRYPOINT`). 빈 DB면 스키마 자동 생성, 최신이면 무충돌 no-op.
  신규 배포 시 수동 마이그레이션 단계 불필요. (CMD는 이미 `uvicorn ... --workers 2`로 고정됨)
- **MCP 서버는 `api` 이미지에 포함** — streamable-http로 `api` 앱의 `/mcp`에 마운트되므로
  별도 이미지·태그 추가 없이 기존 `llm-registry-api` 이미지로 함께 배포된다(태그 영향 없음).
  stdio 단독 `mcp` 서비스는 폐기. 외부 노출 표면 단일화(BFF `/api/v1/mcp`)는 단계 C에서 처리.
- **backup 서비스도 배포 이미지에서 제외** — 운영 환경에서 별도 스케줄러(cron 등)로 대체.
