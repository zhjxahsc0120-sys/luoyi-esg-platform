import { readFile } from "node:fs/promises";
import { resolve } from "node:path";
import { describe, expect, it } from "vitest";

describe("converted SHP data", () => {
  it("contains all real layers in WGS84 with semantic styles", async () => {
    const root = resolve("public/data/shp");
    const manifest = JSON.parse(
      await readFile(resolve(root, "manifest.json"), "utf8"),
    );
    expect(manifest.crs).toBe("EPSG:4326");
    expect(manifest.layers).toHaveLength(10);
    expect(
      manifest.layers.find(
        (layer: { name: string }) => layer.name === "水源保护区1",
      ).style.color,
    ).toBe("#28a9e0");
    expect(
      manifest.layers.find((layer: { name: string }) => layer.name === "1标段")
        .geometryType,
    ).toBe("line");
    for (const layer of manifest.layers) {
      const data = JSON.parse(
        await readFile(resolve("public", layer.source.url.slice(1)), "utf8"),
      );
      expect(data.features.length).toBeGreaterThan(0);
    }
  });
});
