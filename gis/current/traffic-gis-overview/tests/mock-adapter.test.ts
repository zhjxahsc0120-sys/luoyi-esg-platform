import { describe, expect, it } from "vitest";
import { MockTrafficAdapter } from "../adapters/mock-adapter";
describe("MockTrafficAdapter", () => {
  it("filters features by section", async () => {
    const adapter = new MockTrafficAdapter();
    const ctx = { projectId: "demo", sectionId: "TJ-01" };
    const layers = await adapter.getLayers(ctx);
    const route = layers.find((l) => l.id === "highway-main")!;
    const features = await adapter.getFeatures(route, ctx);
    expect(features.length).toBe(1);
    expect(features[0].properties.sectionId).toBe("TJ-01");
  });
});
