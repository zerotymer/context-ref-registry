import { getEntities } from "@/lib/actions/entities";
import { getAliases } from "@/lib/actions/aliases";
import { getContexts } from "@/lib/actions/contexts";
import { getRelations } from "@/lib/actions/relations";
import { getCurrentUser } from "@/lib/actions/auth";
import { ReviewList } from "./ReviewList";
import type { AliasRead, ContextRead, RelationRead, EntityRead } from "@/types/api";

export interface ReviewItem {
  entity: EntityRead;
  aliases: AliasRead[];
  contexts: ContextRead[];
  relations: RelationRead[];
}

export default async function ReviewPage() {
  const [me, data] = await Promise.all([
    getCurrentUser(),
    getEntities("status=candidate&limit=50&sort=created_at&order=asc"),
  ]);

  const items: ReviewItem[] = await Promise.all(
    data.items.map(async (entity) => {
      const [aliases, contexts, relations] = await Promise.all([
        getAliases(entity.id),
        getContexts(entity.id),
        getRelations(entity.id),
      ]);
      return { entity, aliases, contexts, relations };
    }),
  );

  return <ReviewList items={items} canApprove={me?.role === "admin"} />;
}
