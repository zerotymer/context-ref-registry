"use client";

import { useState } from "react";

interface Props {
  data: unknown;
  copyButton?: boolean;
}

export function JsonViewer({ data, copyButton }: Props) {
  const [copied, setCopied] = useState(false);
  const text = JSON.stringify(data, null, 2);

  async function copy() {
    await navigator.clipboard?.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 1500);
  }

  return (
    <div>
      {copyButton && (
        <div className="flex justify-end mb-2">
          <button
            onClick={copy}
            className="text-xs text-indigo-600 hover:underline"
          >
            {copied ? "복사됨 ✓" : "JSON 복사"}
          </button>
        </div>
      )}
      <pre className="bg-gray-900 text-green-300 text-xs rounded-lg p-4 overflow-x-auto leading-relaxed max-h-96 overflow-y-auto">
        <code>{text}</code>
      </pre>
    </div>
  );
}
