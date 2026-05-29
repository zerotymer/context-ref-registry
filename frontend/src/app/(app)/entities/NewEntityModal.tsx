"use client";

import { useRef, useState, useTransition } from "react";
import { createEntity } from "@/lib/actions/entities";
import { addTag } from "@/lib/actions/tags";
import { ENTITY_TYPES } from "@/lib/constants";
import type { EntityType } from "@/types/api";

export function NewEntityModal({ onClose }: { onClose: () => void }) {
  const [type, setType] = useState<EntityType>("UI_AREA");
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [tags, setTags] = useState<string[]>([]);
  const [tagInput, setTagInput] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [isPending, startTransition] = useTransition();
  const tagInputRef = useRef<HTMLInputElement>(null);

  function addTagItem(val: string) {
    const clean = val.trim().replace(/^#+/, "").replace(",", "");
    if (clean && !tags.includes(clean)) setTags((prev) => [...prev, clean]);
  }

  function removeTagItem(tag: string) {
    setTags((prev) => prev.filter((t) => t !== tag));
  }

  function submit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    startTransition(async () => {
      try {
        const { id } = await createEntity({ type, canonical_name: name, description: description || undefined });
        await Promise.all(tags.map((tag) => addTag(id, tag)));
        onClose();
      } catch (e) {
        setError((e as Error).message);
      }
    });
  }

  return (
    <div className="fixed inset-0 bg-black/40 z-50 flex items-center justify-center">
      <div className="bg-white rounded-lg shadow-lg w-full max-w-md p-6">
        <h2 className="font-semibold text-gray-900 mb-4">새 Entity 추가</h2>
        <form onSubmit={submit} className="space-y-3">
          <div>
            <label className="block text-xs text-gray-500 mb-1">타입</label>
            <select
              value={type}
              onChange={(e) => setType(e.target.value as EntityType)}
              className="w-full border border-gray-200 rounded-md px-2.5 py-1.5 text-sm focus:outline-none focus:ring-1 focus:ring-indigo-400"
            >
              {ENTITY_TYPES.map((t) => (
                <option key={t} value={t}>{t}</option>
              ))}
            </select>
          </div>
          <div>
            <label className="block text-xs text-gray-500 mb-1">canonical_name</label>
            <input
              value={name}
              onChange={(e) => setName(e.target.value)}
              required
              className="w-full border border-gray-200 rounded-md px-2.5 py-1.5 text-sm focus:outline-none focus:ring-1 focus:ring-indigo-400"
              placeholder="예: Dashboard 화면"
            />
          </div>
          <div>
            <label className="block text-xs text-gray-500 mb-1">설명 (선택)</label>
            <textarea
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              rows={2}
              className="w-full border border-gray-200 rounded-md px-2.5 py-1.5 text-sm focus:outline-none focus:ring-1 focus:ring-indigo-400"
            />
          </div>
          <div>
            <label className="block text-xs text-gray-500 mb-1 font-medium">
              태그 <span className="text-gray-400 font-normal">(선택 · Enter로 추가)</span>
            </label>
            <div onClick={() => tagInputRef.current?.focus()}
              className="min-h-9 w-full border border-gray-200 rounded-md px-2 py-1.5 flex items-center gap-1.5 flex-wrap cursor-text focus-within:ring-1 focus-within:ring-indigo-400">
              {tags.map((tag) => (
                <span key={tag}
                  className="inline-flex items-center gap-1 bg-violet-50 text-violet-700 border border-violet-200 px-2 py-0.5 rounded-full text-xs">
                  #{tag}
                  <button type="button" onClick={() => removeTagItem(tag)}>×</button>
                </span>
              ))}
              <input
                ref={tagInputRef}
                value={tagInput}
                onChange={(e) => setTagInput(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === "Enter" || e.key === ",") {
                    e.preventDefault();
                    addTagItem(tagInput);
                    setTagInput("");
                  }
                }}
                placeholder="태그 입력..."
                className="flex-1 min-w-20 text-xs focus:outline-none bg-transparent"
              />
            </div>
            <p className="text-xs text-gray-400 mt-1">Enter 또는 쉼표(,)로 추가</p>
          </div>
          {error && <p className="text-xs text-red-500">{error}</p>}
          <div className="flex gap-2 justify-end pt-2">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-1.5 text-sm border border-gray-200 rounded-md hover:bg-gray-50"
            >
              취소
            </button>
            <button
              type="submit"
              disabled={isPending}
              className="px-4 py-1.5 text-sm bg-indigo-600 text-white rounded-md hover:bg-indigo-700 disabled:opacity-60"
            >
              {isPending ? "생성 중..." : "생성"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
