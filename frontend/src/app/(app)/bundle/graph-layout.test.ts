import { describe, it, expect } from "vitest";
import { computeDegrees } from "./graph-layout";
import type { ContextBundleResponse } from "@/types/api";

const rel = (from: string, to: string): ContextBundleResponse["relations"][number] => ({
  from_entity_id: from,
  to_entity_id: to,
  relation_type: "DEPENDS_ON" as ContextBundleResponse["relations"][number]["relation_type"],
});

describe("computeDegrees", () => {
  it("counts undirected connections per node", () => {
    // a is a hub: a-b, a-c, b-c
    const degree = computeDegrees(["a", "b", "c"], [rel("a", "b"), rel("a", "c"), rel("b", "c")]);
    expect(degree.get("a")).toBe(2);
    expect(degree.get("b")).toBe(2);
    expect(degree.get("c")).toBe(2);
  });

  it("gives disconnected nodes degree 0", () => {
    const degree = computeDegrees(["a", "b", "orphan"], [rel("a", "b")]);
    expect(degree.get("a")).toBe(1);
    expect(degree.get("orphan")).toBe(0);
  });

  it("ignores relations pointing outside the entity set", () => {
    const degree = computeDegrees(["a"], [rel("a", "ghost")]);
    expect(degree.get("a")).toBe(1);
    expect(degree.has("ghost")).toBe(false);
  });
});
