import type { EntityStatus } from "@/types/api";

const STATUS_DOT: Record<EntityStatus, string> = {
  active: "bg-green-400",
  candidate: "bg-amber-400",
  deprecated: "bg-red-400",
  archived: "bg-gray-400",
};

const STATUS_TEXT: Record<EntityStatus, string> = {
  active: "text-green-600",
  candidate: "text-amber-600",
  deprecated: "text-red-500",
  archived: "text-gray-500",
};

export function EntityStatusBadge({ status }: { status: EntityStatus }) {
  return (
    <span className={`flex items-center gap-1.5 ${STATUS_TEXT[status]}`}>
      <span className={`w-1.5 h-1.5 rounded-full ${STATUS_DOT[status]}`} />
      {status}
    </span>
  );
}
