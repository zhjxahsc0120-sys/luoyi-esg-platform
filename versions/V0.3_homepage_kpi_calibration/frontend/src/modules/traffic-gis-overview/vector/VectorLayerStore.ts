import type {
  TrafficGeometry,
  TrafficLayerDefinition,
  TrafficMapFeature,
} from "../types";
import {
  loadGisConfiguration,
  saveGisConfiguration,
} from "../config/configuration-api";
export interface VectorLayerRecord {
  id: string;
  name: string;
  color: string;
  visible: boolean;
  definition: TrafficLayerDefinition;
  features: TrafficMapFeature[];
}
type GeoJsonFeature = {
  type: "Feature";
  id?: string | number;
  properties?: Record<string, unknown>;
  geometry: { type: string; coordinates: unknown };
};
const STORAGE_KEY = "traffic-esg-vector-layers-v1";
export function parseGeoJson(
  text: string,
  name: string,
  color = "#35d7ff",
): VectorLayerRecord {
  const source = JSON.parse(text) as
    { type: string; features?: GeoJsonFeature[] } | GeoJsonFeature;
  const items =
    source.type === "FeatureCollection"
      ? source.features || []
      : [source as GeoJsonFeature];
  if (!items.length) throw new Error("矢量文件中没有要素");
  const geometries = items.map((item) => item.geometry.type);
  const unique = [...new Set(geometries)];
  if (
    unique.length !== 1 ||
    !["Point", "LineString", "Polygon"].includes(unique[0])
  )
    throw new Error("一个图层只支持一种几何类型：Point、LineString 或 Polygon");
  const layerId = `vector-${Date.now()}-${Math.random().toString(36).slice(2, 7)}`;
  const geometryType =
    unique[0] === "Point"
      ? "point"
      : unique[0] === "LineString"
        ? "line"
        : "polygon";
  const features = items.map((item, index): TrafficMapFeature => ({
    id: String(item.id ?? `${layerId}-${index}`),
    layerId,
    objectType: "vector",
    name: String(
      item.properties?.name ?? item.properties?.NAME ?? `${name} ${index + 1}`,
    ),
    geometry: item.geometry as TrafficGeometry,
    properties: item.properties || {},
    status: "normal",
  }));
  return {
    id: layerId,
    name,
    color,
    visible: true,
    definition: {
      id: layerId,
      name,
      geometryType,
      enabled: true,
      source: { type: "mock" },
      style: {
        color,
        width: geometryType === "point" ? 12 : 4,
        opacity: 0.18,
        showLabel: geometryType === "point",
        labelColor: "#ffffff",
        labelSize: 12,
      },
    },
    features,
  };
}
export class VectorLayerStore {
  async load(): Promise<VectorLayerRecord[]> {
    try {
      return (await loadGisConfiguration<VectorLayerRecord[]>(STORAGE_KEY)) ?? JSON.parse(
        localStorage.getItem(STORAGE_KEY) || "[]",
      ) as VectorLayerRecord[];
    } catch {
      try {
        return JSON.parse(localStorage.getItem(STORAGE_KEY) || "[]") as VectorLayerRecord[];
      } catch {
        return [];
      }
    }
  }
  async save(records: VectorLayerRecord[]) {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(records));
    try {
      await saveGisConfiguration(STORAGE_KEY, records);
    } catch {
      // 后端恢复后再次保存即可同步；本机配置仍可继续使用。
    }
  }
  async add(records: VectorLayerRecord[], record: VectorLayerRecord) {
    const next = [...records, record];
    await this.save(next);
    return next;
  }
  async remove(records: VectorLayerRecord[], id: string) {
    const next = records.filter((item) => item.id !== id);
    await this.save(next);
    return next;
  }
}
