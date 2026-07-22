import { describe, it, expect } from "vitest";
import { computeDepths } from "./graph-layout";
import type { ContextBundleResponse } from "@/types/api";

const rel = (from: string, to: string): ContextBundleResponse["relations"][number] => ({
  from_entity_id: from,
  to_entity_id: to,
  relation_type: "DEPENDS_ON" as ContextBundleResponse["relations"][number]["relation_type"],
});

describe("computeDepths", () => {
  it("assigns BFS distance from root, treats relations as undirected", () => {
    // a(root) -> b -> c, and d -> a (reverse edge still reachable)
    const depth = computeDepths(
      ["a", "b", "c", "d"],
      new Set(["a"]),
      [rel("a", "b"), rel("b", "c"), rel("d", "a")],
    );
    expect(depth.get("a")).toBe(0);
    expect(depth.get("b")).toBe(1);
    expect(depth.get("c")).toBe(2);
    expect(depth.get("d")).toBe(1); // reachable via reverse edge
  });

  it("pushes disconnected nodes to a trailing column", () => {
    const depth = computeDepths(
      ["a", "b", "orphan"],
      new Set(["a"]),
      [rel("a", "b")],
    );
    expect(depth.get("orphan")).toBe(2); // maxDepth(1) + 1
  });

  it("handles no roots without looping forever", () => {
    const depth = computeDepths(["a", "b"], new Set(), [rel("a", "b")]);
    expect(depth.get("a")).toBe(1);
    expect(depth.get("b")).toBe(1);
  });
});
