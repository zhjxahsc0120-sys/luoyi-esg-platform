export type BasemapId = "dark" | "street" | "satellite";

export interface BasemapDefinition {
  id: BasemapId;
  name: string;
  description: string;
  url: string;
  type: "osm" | "xyz";
  brightness: number;
  contrast: number;
  saturation: number;
  alpha?: number;
  globeBaseColor: string;
  credit: string;
  coordinateSystem: "wgs84" | "gcj02";
}

/**
 * 首页正式底图默认使用在线卫星影像。
 * SVG 地图只作为领导首页的应急回退组件，不作为 GIS 模块默认底图。
 */
export const defaultBasemapId: BasemapId = "satellite";

export const basemapDefinitions: BasemapDefinition[] = [
  {
    id: "dark",
    name: "深蓝专题地图",
    description: "深蓝灰路网，适合大屏弱背景叠加",
    url: "https://server.arcgisonline.com/ArcGIS/rest/services/Canvas/World_Dark_Gray_Base/MapServer/tile/{z}/{y}/{x}",
    type: "xyz",
    brightness: 0.72,
    contrast: 1.08,
    saturation: 0.32,
    alpha: 0.8,
    globeBaseColor: "#08243b",
    credit: "Tiles © Esri",
    coordinateSystem: "wgs84",
  },
  {
    id: "street",
    name: "街道地图",
    description: "道路、地名和基础交通网络",
    url: "https://tile.openstreetmap.org/",
    type: "osm",
    brightness: 0.86,
    contrast: 1.05,
    saturation: 0.62,
    globeBaseColor: "#dce6ec",
    credit: "© OpenStreetMap contributors",
    coordinateSystem: "wgs84",
  },
  {
    id: "satellite",
    name: "卫星影像",
    description: "WGS84 全球卫星影像，与 S1-6 设计 KML 坐标直接叠加",
    url: "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
    type: "xyz",
    brightness: 0.9,
    contrast: 1.08,
    saturation: 0.9,
    globeBaseColor: "#263a2d",
    credit: "Tiles © Esri",
    coordinateSystem: "wgs84",
  },
];
