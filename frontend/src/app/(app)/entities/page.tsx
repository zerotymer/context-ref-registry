import { Suspense } from "react";
import { getEntities } from "@/lib/actions/entities";
import { getMyProjects } from "@/lib/actions/projects";
import { EntityList } from "./EntityList";

const PAGE_SIZE = 20;

interface SearchParams {
  status?: string;
  types?: string | string[];
  tags?: string;
  project_id?: string;
  offset?: string;
}

function buildQs(params: SearchParams): string {
  const qs = new URLSearchParams();
  if (params.status) qs.set("status", params.status);
  const types = params.types
    ? Array.isArray(params.types)
      ? params.types
      : [params.types]
    : [];
  types.forEach((t) => qs.append("types", t));
  if (params.tags) {
    params.tags.split(",").filter(Boolean).forEach((tag) => qs.append("tags", tag));
  }
  if (params.project_id) qs.set("project_id", params.project_id);
  qs.set("limit", String(PAGE_SIZE));
  if (params.offset) qs.set("offset", params.offset);
  qs.set("sort", "created_at");
  qs.set("order", "desc");
  return qs.toString();
}

export default async function EntitiesPage({
  searchParams,
}: {
  searchParams: SearchParams;
}) {
  const [data, projects] = await Promise.all([
    getEntities(buildQs(searchParams)),
    getMyProjects(),
  ]);
  return (
    <Suspense>
      <EntityList data={data} pageSize={PAGE_SIZE} projects={projects} />
    </Suspense>
  );
}
