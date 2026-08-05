import { describe, expect, it } from "vitest";
import { parseGeoJson } from "../vector/VectorLayerStore";
describe("parseGeoJson", () => {
  it("converts a GeoJSON FeatureCollection into a map layer", () => {
    const result = parseGeoJson(
      JSON.stringify({
        type: "FeatureCollection",
        features: [
          {
            type: "Feature",
            properties: { name: "施工便道" },
            geometry: {
              type: "LineString",
              coordinates: [
                [108, 22],
                [108.1, 22.1],
              ],
            },
          },
        ],
      }),
      "施工矢量",
    );
    expect(result.definition.geometryType).toBe("line");
    expect(result.features[0].name).toBe("施工便道");
  });
  it("rejects mixed geometry types", () => {
    expect(() =>
      parseGeoJson(
        JSON.stringify({
          type: "FeatureCollection",
          features: [
            {
              type: "Feature",
              geometry: { type: "Point", coordinates: [108, 22] },
            },
            {
              type: "Feature",
              geometry: {
                type: "LineString",
                coordinates: [
                  [108, 22],
                  [109, 23],
                ],
              },
            },
          ],
        }),
        "混合",
      ),
    ).toThrow("一种几何类型");
  });
});
