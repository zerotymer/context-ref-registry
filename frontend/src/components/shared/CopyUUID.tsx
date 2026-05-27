"use client";

import { useState } from "react";

export function CopyUUID({ id }: { id: string }) {
  const [copied, setCopied] = useState(false);

  async function copy() {
    await navigator.clipboard?.writeText(id);
    setCopied(true);
    setTimeout(() => setCopied(false), 1500);
  }

  return (
    <button
      onClick={copy}
      className="text-xs text-gray-400 hover:text-gray-600 font-mono border border-gray-200 rounded px-2 py-1 hover:bg-gray-50"
    >
      {id.slice(0, 8)}… {copied ? "✓" : "⎘"}
    </button>
  );
}
