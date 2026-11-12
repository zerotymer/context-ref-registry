# 12. Reverse Proxy (안내)

이 저장소는 리버스 프록시를 **포함하지 않는다.** 프록시 제품 선택·설정·TLS는 서버 관리자(사용자)의
판단이며, 이 문서는 연동에 필요한 **URL 규격과 요구사항**만 안내한다.

## URL 규격

백엔드(`api:8000`)의 REST·MCP·문서는 모두 `/api/v1` 아래에 있고, 프론트(`frontend:3000`)
게이트웨이도 **같은 `/api/v1` 경로**를 노출한다. 그래서 외부 URL은 라우팅 방식과 관계없이 같다.

| 외부 경로 | 처리 | 외부 공개 |
|-----------|------|-----------|
| `/`, `/login`, `/entities/*`, `/bundle`, `/review`, `/admin/*` | 프론트 관리자 UI | O |
| `/api/v1/{entities,relations,search,resolve,tags,context-bundle,ingest,export,validate-references,projects}/*` | 백엔드 REST (`Authorization: Bearer <api-key>`) | O |
| `/api/v1/mcp/` | 백엔드 MCP streamable-http (API Key) | O |
| `/api/v1/auth/*`, `/api/v1/admin/*` | 백엔드 관리자 API — 프론트 BFF가 서버 내부에서만 호출 | **X** |
| `/api/v1/docs`, `/api/v1/openapi.json` | Swagger | X (필요 시 공개) |
| `/health` | 컨테이너 헬스체크 | X |

> 프론트 UI의 `/admin/*`(페이지)와 백엔드의 `/api/v1/admin/*`(API)는 다른 경로다.

## 라우팅 방식

앱은 두 방식을 **항상 동시에 호환**한다. 앱 쪽 설정 스위치는 없으며 프록시 설정만으로 고른다.

| 방식 | 라우팅 | 특징 |
|------|--------|------|
| A. 프론트 단일 업스트림 | `/` → `frontend:3000` | 가장 단순. 프론트 게이트웨이가 allowlist로 `/api/v1/auth`·`/api/v1/admin`·docs를 404 처리 |
| B. 경로 분리 | `/api/v1/` → `api:8000`, `/` → `frontend:3000` | 거치는 단계가 하나 줄어 MCP 스트리밍이 단순. **비공개 경로 차단을 프록시가 직접 해야 함** |

방식 B는 Dependency-Track(`/api` → API 서버, `/` → 프론트)과 같은 구조다.

## 프록시 요구사항

| 항목 | A | B | 내용 |
|------|---|---|------|
| `X-Forwarded-Proto` 전달 | 필수 | 필수 | 프론트가 HTTPS 여부를 보고 관리자 쿠키에 `Secure`를 붙임 |
| `X-Forwarded-For`/`Host` 전달 | 권장 | 권장 | 로그·감사 기록용 |
| MCP 응답 버퍼링 끄기 | 필수 | 필수 | `/api/v1/mcp`는 SSE/청크 스트리밍. 버퍼링하면 응답이 지연·멈춤 |
| 긴 read timeout | 권장 | 권장 | MCP 세션이 오래 열려 있음 (예: 1시간) |
| 비공개 경로 차단 | — | **필수** | `/api/v1/auth/`, `/api/v1/admin/`, `/api/v1/docs`, `/api/v1/openapi.json` → 404 |
| MCP Host 허용 | — | **필수** | 아래 참고 |

### MCP Host 허용 (방식 B)

백엔드 MCP는 DNS rebinding 방어로 허용된 Host만 받는다(그 외 421). 방식 B에서는 외부 도메인
Host가 그대로 전달되므로 둘 중 하나를 한다.

- `api` 서비스 환경변수에 도메인 추가: `MCP_ALLOWED_HOSTS=api:*,registry.example.com`
- 또는 프록시가 백엔드로 보낼 때 `Host`를 `api:8000`(또는 `localhost:8000`)으로 바꿔 보냄

방식 A는 프론트가 `api:8000`으로 다시 요청하므로 compose 기본값(`api:*`)으로 충분하다.

### 포트

운영 compose는 `api`를 `127.0.0.1:8000`(루프백)에만, `frontend`를 `3000`에 연다.
같은 서버에 설치한 프록시는 두 포트 모두 접근할 수 있다. 프록시를 컨테이너로 같은 compose 네트워크에
올린다면 `api:8000`, `frontend:3000`으로 접근하면 된다.

## 예시 (참고용, nginx)

저장소에 포함하지 않는 참고 예시다. TLS 설정은 생략했다.

### 방식 A

```nginx
server {
    listen 443 ssl;
    server_name registry.example.com;

    location / {
        proxy_pass http://127.0.0.1:3000;
        proxy_http_version 1.1;
        proxy_set_header Host              $host;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header X-Forwarded-For   $proxy_add_x_forwarded_for;
    }

    location /api/v1/mcp {
        proxy_pass http://127.0.0.1:3000;
        proxy_http_version 1.1;
        proxy_set_header Host              $host;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header X-Forwarded-For   $proxy_add_x_forwarded_for;
        proxy_buffering off;
        proxy_read_timeout 1h;
    }
}
```

### 방식 B

```nginx
server {
    listen 443 ssl;
    server_name registry.example.com;

    # Backend-only surfaces: never public (frontend BFF calls them internally).
    location ^~ /api/v1/auth/   { return 404; }
    location ^~ /api/v1/admin/  { return 404; }
    location = /api/v1/docs         { return 404; }
    location = /api/v1/openapi.json { return 404; }

    location /api/v1/mcp {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Host              localhost:8000;  # or add the domain to MCP_ALLOWED_HOSTS
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header X-Forwarded-For   $proxy_add_x_forwarded_for;
        proxy_buffering off;
        proxy_read_timeout 1h;
    }

    location /api/v1/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Host              $host;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header X-Forwarded-For   $proxy_add_x_forwarded_for;
    }

    location / {
        proxy_pass http://127.0.0.1:3000;
        proxy_http_version 1.1;
        proxy_set_header Host              $host;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header X-Forwarded-For   $proxy_add_x_forwarded_for;
    }
}
```

다른 프록시(Caddy, Traefik, HAProxy 등)도 위 **요구사항 표**를 만족하면 된다.

## 범위 밖

- 하위 경로 배포 (`example.com/registry/`) — 루트 배포만 지원
- 프록시 설정 파일·컨테이너 제공, TLS 설정
