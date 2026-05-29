import { getEntity } from "@/lib/actions/entities";
import { EntityEditForm } from "./EntityEditForm";

export default async function EntityEditPage({ params }: { params: { id: string } }) {
  const entity = await getEntity(params.id);
  return <EntityEditForm entity={entity} />;
}
