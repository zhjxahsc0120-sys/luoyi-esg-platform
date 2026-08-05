import type { BasemapId } from "./basemaps.config";

export interface HistoricalImagerySnapshot {
  id: string;
  label: string;
  date: string;
  basemapId: BasemapId;
  placeholder: boolean;
}

// 历史正射影像上传后，只需把对应节点映射到新增的影像服务定义。
export const historicalImagerySnapshots: HistoricalImagerySnapshot[] = [
  { id: "baseline", label: "初始配置", date: "2026-02", basemapId: "dark", placeholder: true },
  { id: "midterm", label: "阶段影像", date: "2026-05", basemapId: "street", placeholder: true },
  { id: "latest", label: "最新影像", date: "当前", basemapId: "satellite", placeholder: false },
];

