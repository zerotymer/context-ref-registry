# context-ref-registry
LLM Agent용 참조 저장소

## 현재 작업 지침

구현 작업은 `instructions/` 아래 지침서를 기준으로 진행한다.

- `instructions/frontend_bff_proxy.md`: frontend가 backend(`:8000`)를 직접 호출하는 구조를 제거하고 Next.js BFF route를 경유하도록 전환한다.
- `instructions/README.md`: 전체 로드맵과 지침 파일 현황을 관리한다.

## Frontend API 호출 구조 메모

목표 구조는 다음과 같다.

```text
Browser -> Next.js BFF (/api/backend/*) -> FastAPI backend (:8000)
```

브라우저 코드에서는 backend origin을 직접 참조하지 않는다. backend 내부 URL은 Next.js server runtime 환경 변수 `BACKEND_API_URL`로만 관리하고, `NEXT_PUBLIC_API_URL`은 사용하지 않는다.
