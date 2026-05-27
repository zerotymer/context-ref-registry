import { cn } from "@/lib/utils";

interface Props {
  value: number;
  showLabel?: boolean;
}

export function ConfidenceBar({ value, showLabel = true }: Props) {
  const isLow = value < 0.7;
  return (
    <div className="flex items-center gap-1.5">
      <div className="w-16 h-1.5 bg-gray-100 rounded-full">
        <div
          className={cn(
            "h-1.5 rounded-full",
            isLow ? "bg-amber-400" : "bg-indigo-400",
          )}
          style={{ width: `${value * 100}%` }}
        />
      </div>
      {showLabel && (
        <span
          className={cn(
            "text-xs font-medium",
            isLow ? "text-amber-600" : "text-gray-600",
          )}
        >
          {value.toFixed(2)}
        </span>
      )}
    </div>
  );
}
