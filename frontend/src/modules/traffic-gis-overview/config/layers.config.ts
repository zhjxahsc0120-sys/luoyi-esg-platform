import type { TrafficLayerDefinition } from "../types";
import { tokens } from "./style-tokens";
export const layerDefinitions: TrafficLayerDefinition[] = [
  {
    id: "highway-main",
    name: "高速主线",
    geometryType: "line",
    enabled: true,
    source: { type: "mock" },
    style: { color: tokens.cyan, width: 5 },
  },
  {
    id: "milestones",
    name: "里程桩",
    geometryType: "point",
    enabled: true,
    source: { type: "mock" },
    style: { color: tokens.blue },
  },
  {
    id: "facilities",
    name: "桥梁与服务设施",
    geometryType: "point",
    enabled: true,
    source: { type: "mock" },
    style: { color: tokens.green },
  },
  {
    id: "risks",
    name: "风险点",
    geometryType: "point",
    enabled: true,
    source: { type: "mock" },
    style: { color: tokens.orange },
  },
  {
    id: "monitors",
    name: "监测点",
    geometryType: "point",
    enabled: true,
    source: { type: "mock" },
    style: { color: tokens.green },
  },
  {
    id: "work-zones",
    name: "施工及生态范围",
    geometryType: "polygon",
    enabled: true,
    source: { type: "mock" },
    style: { color: tokens.yellow, opacity: 0.1 },
  },
];
