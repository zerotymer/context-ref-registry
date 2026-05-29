import { getEntity } from "@/lib/actions/entities";
import { getAliases } from "@/lib/actions/aliases";
import { getContexts } from "@/lib/actions/contexts";
import { getRelations } from "@/lib/actions/relations";
import { EntityDetail } from "./EntityDetail";

export default async function EntityDetailPage({ params }: { params: { id: string } }) {
  const [entity, aliases, contexts, relations] = await Promise.all([
    getEntity(params.id),
    getAliases(params.id),
    getContexts(params.id),
    getRelations(params.id),
  ]);

  return (
    <EntityDetail
      entity={entity}
      aliases={aliases}
      contexts={contexts}
      relations={relations}
    />
  );
}
