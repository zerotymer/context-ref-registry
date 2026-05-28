import { Suspense } from "react";
import { getEntities } from "@/lib/actions/entities";
import { EntityList } from "./EntityList";

const PAGE_SIZE = 20;

interface SearchParams {
  status?: string;
  types?: string | string[];
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
  const data = await getEntities(buildQs(searchParams));
  return (
    <Suspense>
      <EntityList data={data} pageSize={PAGE_SIZE} />
    </Suspense>
  );
}
