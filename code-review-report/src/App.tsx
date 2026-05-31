import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { Separator } from "@/components/ui/separator";

const FINDINGS = [
  {
    id: 1,
    severity: "critical",
    file: "backend/app/api/export.py",
    line: 29,
    summary: "export 엔드포인트 인증 없음 — 익명 호출자가 전체 엔티티 번들 덤프 가능",
    scenario:
      "인증 없는 HTTP GET /export/agents-md?root_ids=<uuid> 호출 시 비공개 프로젝트의 business_rule·security_note context body를 포함한 전체 AGENTS.md 번들 반환. /export/openapi 동일. 두 라우트 모두 Depends(get_current_user) 없음, main.py에도 router-level 인증 미들웨어 없음.",
    tag: "Security · No Auth",
  },
  {
    id: 2,
    severity: "critical",
    file: "backend/app/api/validate.py",
    line: 220,
    summary:
      "POST /validate-references 인증 없음 + visible_project_ids 미전달 → 전체 alias/UUID 익명 열거 가능",
    scenario:
      "비인증 호출자가 후보 alias를 POST하면, validate_service가 alias_repo.resolve(ref)를 visible_project_ids 없이 호출해 프로젝트 가시성 필터를 건너뜀. 비공개 프로젝트 엔티티가 resolved로 반환됨. rate-limit 없어 brute-force UUID 열거 가능.",
    tag: "Security · No Auth + Access Control Bypass",
  },
  {
    id: 3,
    severity: "high",
    file: "backend/app/mcp/tools.py",
    line: 52,
    summary: "resolve_alias MCP 툴이 visible_project_ids 없이 호출 → 비공개 프로젝트 엔티티 노출",
    scenario:
      "MCP 클라이언트가 비공개 프로젝트 소속 alias를 resolve 요청 시, service.resolve(alias, locale_enum, type_enum)가 visible_project_ids를 넘기지 않아 AliasRepository가 visibility JOIN을 생략하고 비공개 엔티티의 id·canonical_name을 반환.",
    tag: "Security · Visibility Bypass",
  },
  {
    id: 4,
    severity: "high",
    file: "backend/app/service/export_service.py",
    line: 23,
    summary: "EntityType.ISSUE가 _TYPE_ORDER에 없음 → AGENTS.md에서 ISSUE 엔티티 전부 무음 삭제",
    scenario:
      "ISSUE 타입 엔티티가 포함된 번들을 _render_agents_md()에 전달 시, entities_by_type[EntityType.ISSUE]는 채워지지만 line 137의 렌더링 루프가 _TYPE_ORDER(5개 타입, ISSUE 미포함)만 순회 → 모든 ISSUE 엔티티가 오류/경고 없이 출력에서 누락.",
    tag: "Correctness · Silent Data Loss",
  },
  {
    id: 5,
    severity: "medium",
    file: "frontend/src/app/(app)/review/page.tsx",
    line: 33,
    summary:
      "canApprove가 role === 'admin'만 체크 → project_admin의 승인 버튼 영구 비활성화",
    scenario:
      "project_admin이 Review 페이지 접근 시 canApprove=false로 승인 버튼 비활성('admin 권한이 필요합니다'). 동일 사용자가 PATCH /entities/{id}를 직접 호출하면 check_can_mutate_entity(프로젝트 멤버 허용)를 통과 — UI/백엔드 정책 불일치.",
    tag: "Correctness · UI/Backend Mismatch",
  },
  {
    id: 6,
    severity: "medium",
    file: "backend/app/service/export_service.py",
    line: 64,
    summary:
      "generate_openapi에서 limit=1000 하드코딩 → 1000개 초과 시 불완전한 OpenAPI 스펙 무음 반환",
    scenario:
      "API 엔티티가 1001개인 레지스트리에서 GET /export/openapi 호출 시, entity_repo.list(limit=1000)이 최초 1000개만 반환 — 나머지는 오류·경고·페이지네이션 없이 스펙에서 누락.",
    tag: "Correctness · Silent Truncation",
  },
  {
    id: 7,
    severity: "low",
    file: "backend/app/service/export_service.py",
    line: 72,
    summary:
      "generate_openapi 루프 내 context_repo.list_by_entity() N+1 쿼리",
    scenario:
      "API 엔티티 500개 시 루프가 500번의 개별 SELECT를 순차 실행. 루프 전 IN 기반 일괄 fetch로 교체 가능.",
    tag: "Efficiency · N+1 Query",
  },
];

const SEVERITY_META: Record<
  string,
  { label: string; color: string; bg: string; border: string; dot: string; leftBar: string }
> = {
  critical: {
    label: "Critical",
    color: "text-red-400",
    bg: "bg-red-950/30",
    border: "border-zinc-800",
    dot: "bg-red-500",
    leftBar: "bg-red-600",
  },
  high: {
    label: "High",
    color: "text-orange-400",
    bg: "bg-orange-950/20",
    border: "border-zinc-800",
    dot: "bg-orange-500",
    leftBar: "bg-orange-500",
  },
  medium: {
    label: "Medium",
    color: "text-yellow-400",
    bg: "bg-yellow-950/15",
    border: "border-zinc-800",
    dot: "bg-yellow-400",
    leftBar: "bg-yellow-500",
  },
  low: {
    label: "Low",
    color: "text-sky-400",
    bg: "bg-zinc-900/40",
    border: "border-zinc-800",
    dot: "bg-sky-400",
    leftBar: "bg-sky-600",
  },
};

const COUNTS = {
  critical: FINDINGS.filter((f) => f.severity === "critical").length,
  high: FINDINGS.filter((f) => f.severity === "high").length,
  medium: FINDINGS.filter((f) => f.severity === "medium").length,
  low: FINDINGS.filter((f) => f.severity === "low").length,
};

export default function App() {
  return (
    <div className="min-h-screen bg-zinc-950 text-zinc-100" style={{ fontFamily: "'JetBrains Mono', 'Fira Code', monospace" }}>
      {/* Header bar */}
      <div className="bg-zinc-900 border-b border-zinc-800 px-6 py-4">
        <div className="max-w-3xl mx-auto flex items-center justify-between flex-wrap gap-3">
          <div>
            <span className="text-[10px] text-zinc-600 uppercase tracking-[0.15em]">Code Review Report</span>
            <h1 className="text-base font-bold text-zinc-100 mt-0.5">context-ref-registry</h1>
            <p className="text-[11px] text-zinc-500 mt-0.5">HEAD~5..HEAD · 2026-05-31 · high effort · recall-biased · 7 angles</p>
          </div>
          <div className="flex gap-2 flex-wrap">
            {(["critical","high","medium","low"] as const).map((s) => (
              <div key={s} className={`flex items-center gap-1.5 px-2.5 py-1 rounded-sm border border-zinc-700/60 text-[11px] font-bold ${SEVERITY_META[s].color}`}>
                <span className={`w-1.5 h-1.5 rounded-full ${SEVERITY_META[s].dot}`} />
                {SEVERITY_META[s].label} {COUNTS[s]}
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Stats row */}
      <div className="max-w-3xl mx-auto px-6 pt-5">
        <div className="grid grid-cols-4 gap-2 text-[11px]">
          {[["Commits", "5"], ["Files Changed", "51"], ["Total Findings", "7"], ["Verified", "7/7"]].map(([label, val]) => (
            <div key={label} className="bg-zinc-900 border border-zinc-800 rounded-sm px-3 py-2.5">
              <p className="text-zinc-600">{label}</p>
              <p className="text-zinc-200 font-bold text-sm mt-0.5">{val}</p>
            </div>
          ))}
        </div>
      </div>

      {/* Findings list */}
      <div className="max-w-3xl mx-auto px-6 py-5 space-y-3">
        {FINDINGS.map((f, i) => {
          const meta = SEVERITY_META[f.severity];
          return (
            <Card key={f.id} className={`border ${meta.border} ${meta.bg} bg-transparent text-zinc-100 overflow-hidden`}>
              <div className="flex">
                {/* Left severity bar */}
                <div className={`w-1 shrink-0 ${meta.leftBar}`} />
                <div className="flex-1 min-w-0">
                  <CardHeader className="px-4 pt-3 pb-2">
                    <div className="flex items-start gap-2.5">
                      <span className="text-[10px] text-zinc-600 font-mono pt-0.5 w-4 shrink-0">#{i + 1}</span>
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2 flex-wrap mb-1.5">
                          <span className={`text-[10px] font-bold uppercase tracking-widest ${meta.color}`}>
                            {meta.label}
                          </span>
                          <Badge variant="outline" className="text-[9px] border-zinc-700 text-zinc-500 bg-transparent rounded-none font-mono px-1.5 py-0">
                            {f.tag}
                          </Badge>
                        </div>
                        <p className="text-[13px] text-zinc-100 font-semibold leading-snug">{f.summary}</p>
                      </div>
                    </div>
                  </CardHeader>
                  <CardContent className="px-4 pb-3 pt-0 ml-6">
                    {/* File location */}
                    <code className="inline-block text-[10px] bg-zinc-900 border border-zinc-800 rounded-sm px-2 py-0.5 text-zinc-500 mb-2.5">
                      {f.file}<span className="text-zinc-700">:{f.line}</span>
                    </code>
                    <Separator className="bg-zinc-800 mb-2.5" />
                    <p className="text-[10px] text-zinc-600 uppercase tracking-wider mb-1">Failure Scenario</p>
                    <p className="text-[11px] text-zinc-400 leading-relaxed">{f.scenario}</p>
                  </CardContent>
                </div>
              </div>
            </Card>
          );
        })}

        {/* Footer */}
        <div className="pt-3 border-t border-zinc-800 flex justify-between flex-wrap gap-2 text-[10px] text-zinc-700">
          <span>7 angles · 8 candidates verified · 2 refuted · 7 confirmed/plausible</span>
          <span>Generated by Claude Code /code-review high</span>
        </div>
      </div>
    </div>
  );
}
