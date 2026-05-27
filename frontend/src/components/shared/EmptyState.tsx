export function EmptyState({ message }: { message: string }) {
  return (
    <div className="text-center py-20">
      <div className="text-4xl mb-3">✓</div>
      <div className="font-medium text-gray-700">{message}</div>
    </div>
  );
}
