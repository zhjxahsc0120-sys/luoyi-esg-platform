# NEXT_FOR_TRAE

**状态：** Cesium 地图 **Phase 1 底座替换已落地**；ESG 业务 GIS 融合 **未启动**。  
**更新日期：** 2026-08-04  
**本轮说明：** `_handoff/Cesium地图模块替换实施说明_V1.0_20260804.md`  
**交接包归档：** `_handoff/cesium_handover_20260804/`  
**首页保护基线：** `baseline/l1-l2-gis-20260726`（勿删；本轮未改布局比例）

**当前任务单（主指针）：**

| 工作项 | 任务单 | 校核结论 |
|--------|--------|----------|
| **Cesium 地图 Phase 1 · 底座升级** | `_handoff/Cesium地图模块替换实施说明_V1.0_20260804.md` | **IMPLEMENTED** — KML+SPX Worker/Primitive；保留首页 ESG panel |
| ESG Demo Phase C · G 组 | `_handoff/ESG演示_PhaseC_G组_20260804.md` | IMPLEMENTED |
| ESG Demo Phase C · S 组 | 改造计划 Phase C（S） | **NOT STARTED** |
| Cesium Phase 2 · 业务 GIS 融合 | 交接说明 §7 | **NOT STARTED** |

---

## 本轮要点（Cesium Phase 1）

- 正式 `public/gis/s1-6` KML + SPX；停用 `real-layers` 1/2/3 标段演示线
- `TrafficGisOverview` 以交接包为基并回植 E01/E02/E03/S02 hooks；`GisOverviewCesiumPanel` 未改版
- 未改后端接口；`npm run check` / `npm run build` 通过

## 红线（仍有效）

不得改坏：工作台首页 GIS/KPI 布局比例、正式库口径、碳模块。禁止页面硬编码业务结论数（走 service）。**S 组未授权前勿深改 S 弹窗。** Phase 2 前勿扩展 ESG 业务点落图。
