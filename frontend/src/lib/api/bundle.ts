import { useMutation } from "@tanstack/react-query";
import { apiFetch } from "./client";
import type { ContextBundleRequest, ContextBundleResponse } from "@/types/api";

export function useContextBundle() {
  return useMutation({
    mutationFn: (body: ContextBundleRequest) =>
      apiFetch<ContextBundleResponse>("/context-bundle", {
        method: "POST",
        body: JSON.stringify(body),
      }),
  });
}
