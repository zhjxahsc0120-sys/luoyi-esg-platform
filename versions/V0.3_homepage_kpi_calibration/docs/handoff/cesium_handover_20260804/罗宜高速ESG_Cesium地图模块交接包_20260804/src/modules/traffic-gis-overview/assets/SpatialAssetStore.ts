import {
  loadGisConfiguration,
  saveGisConfiguration,
} from "../config/configuration-api";
export type SpatialAssetType = "imagery" | "terrain" | "tileset" | "pointcloud";
export interface SpatialAssetRecord {
  id: string;
  name: string;
  type: SpatialAssetType;
  url: string;
  visible: boolean;
  opacity: number;
  terrainProvider?: "cesium" | "arcgis";
  placement?: {
    longitude: number;
    latitude: number;
    height: number;
    labelHeight?: number;
  };
  label?: string;
  properties?: Record<string, unknown>;
}
const KEY = "traffic-esg-spatial-assets-v1";
const FACTORY_ASSET: SpatialAssetRecord = {
  id: "demo-hazardous-chemical-factory",
  name: "重大危化品工厂（三维模型测试）",
  type: "tileset",
  url: "/models/18/tileset.json",
  visible: true,
  opacity: 1,
  placement: {
    longitude: 109.7,
    latitude: 24.4435,
    height: 0,
    labelHeight: 130,
  },
  label: "重大危化品工厂",
  properties: {
    设施编号: "WH-CQ-001",
    设施类型: "重大危险源（危化品生产设施）",
    所属标段: "2标段",
    风险等级: "重大风险",
    当前状态: "演示运行",
    管控要求: "重点巡查、视频监控、气体监测和应急联动",
    数据用途: "3D Tiles 模型加载及空间定位测试",
    资料说明: "演示模型与模拟属性，不代表项目现场真实设施",
  },
};
export class SpatialAssetStore {
  async load(): Promise<SpatialAssetRecord[]> {
    let saved: SpatialAssetRecord[] = [];
    try {
      const remote = await loadGisConfiguration<SpatialAssetRecord[]>(KEY);
      saved = remote ?? [];
    } catch {
      try {
        saved = JSON.parse(localStorage.getItem(KEY) || "[]") as SpatialAssetRecord[];
      } catch {
        saved = [];
      }
    }
    const merged = saved.filter((item) => item.id !== "online-arcgis-world-terrain");
    if (!merged.some((item) => item.id === FACTORY_ASSET.id)) merged.unshift(FACTORY_ASSET);
    return merged;
  }
  async save(items: SpatialAssetRecord[]) {
    localStorage.setItem(KEY, JSON.stringify(items));
    try {
      await saveGisConfiguration(KEY, items);
    } catch {
      // 后端恢复后再次保存即可同步；本机配置仍可继续使用。
    }
  }
  async add(items: SpatialAssetRecord[], input: Omit<SpatialAssetRecord, "id">) {
    const next = [...items, { ...input, id: `asset-${Date.now()}` }];
    await this.save(next);
    return next;
  }
  async remove(items: SpatialAssetRecord[], id: string) {
    const next = items.filter((item) => item.id !== id);
    await this.save(next);
    return next;
  }
}
