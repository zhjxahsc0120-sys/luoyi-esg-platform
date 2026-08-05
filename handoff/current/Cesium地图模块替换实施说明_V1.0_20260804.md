# Cesium 地图模块替换实施说明 V1.0

**日期：** 2026-08-04  
**阶段：** Phase 1 — 地图底座升级（不做 ESG 业务 GIS 融合扩展）  
**交接包：** `罗宜高速ESG_Cesium地图模块交接包_20260804.zip`  
**解压位置：** `_handoff/cesium_handover_20260804/`

---

## 1. 目标与边界

### 已完成目标

- 用交接包正式 KML + SPX（WebWorker → Primitive）替换首页旧演示标段线地图底座。
- 保留首页布局 / 主题 / 右侧 ESG 面板 / KPI API / DB 不变。
- 保留现有 `GisOverviewCesiumPanel.vue` 的 E01/E02/E03/S02 挂接（不替换为交接包精简版包装组件）。

### 本阶段明确不做

- `/api/esg/gis/features` 正式业务 API 开发与联调扩展
- ESG 环境/水土/安全/治理业务点位融合扩展
- 首页导航、卡片布局、字体颜色比例改版
- DB schema / KPI 计算 / 预警逻辑 / 碳模块改动

---

## 2. 交接包 vs 仓库现状（合并策略）

| 项 | 交接包 | 合并前仓库 | 本轮处理 |
| --- | --- | --- | --- |
| `DesignKmlLayerManager` / SPX Worker+Primitive | 有 | 无 | **新增** |
| `public/gis/s1-6` 正式 KML | 有 | 无 | **复制** |
| `real-layers.json` 1/2/3 标段演示线 | 明确禁止 | 有 | **停用**（改名 `.disabled-demo`） |
| `GisOverviewCesiumPanel` | 精简包装 | 含 E01/E02/E03/S02 | **保留仓库版** |
| `TrafficGisOverview` | 设计图层完整 | ESG 挂接完整 | **交接包为基，回植 ESG hooks** |
| `vite.config.ts` / Cesium 依赖 | 参考配置 | 已具备 | **无需改**（已有 CESIUM_BASE_URL + static-copy） |
| 业务 GIS API | 文档示例 | adapter 已有 | **未改后端**；dashboard 仅收纯 API 图层 |

---

## 3. 修改 / 新增文件列表

### 新增

- `public/gis/s1-6/layer-config.json`
- `public/gis/s1-6/README.md`
- `public/gis/s1-6/layers/高速公路首页_道路生态关键要素_不含SPX.kml`
- `public/gis/s1-6/layers/高速公路首页_SPX边坡_独立图层.kml`
- `src/modules/traffic-gis-overview/cesium/layers/DesignKmlLayerManager.ts`
- `src/modules/traffic-gis-overview/cesium/layers/SpxPrimitiveLayer.ts`
- `src/modules/traffic-gis-overview/cesium/layers/spx-kml.worker.ts`
- `src/modules/traffic-gis-overview/cesium/layers/HistoricalCompareManager.ts`
- `src/modules/traffic-gis-overview/components/DesignLayerTree.vue`
- `src/modules/traffic-gis-overview/config/design-map.config.ts`
- `src/modules/traffic-gis-overview/config/historical-imagery.config.ts`
- `src/modules/traffic-gis-overview/config/configuration-api.ts`
- `src/modules/traffic-gis-overview/types/design-layers.ts`
- `src/modules/traffic-gis-overview/README.md`
- `_handoff/cesium_handover_20260804/**`（交接包解压归档）
- `_handoff/Cesium地图模块替换实施说明_V1.0_20260804.md`（本文件）

### 升级 / 替换（来自交接包）

- `src/modules/traffic-gis-overview/components/TrafficGisOverview.vue`（交接包基线 + ESG hooks）
- `src/modules/traffic-gis-overview/components/MapChrome.vue`
- `src/modules/traffic-gis-overview/components/LayerControl.vue`
- `src/modules/traffic-gis-overview/components/FeatureCard.vue`
- `src/modules/traffic-gis-overview/components/TrafficLegend.vue`
- `src/modules/traffic-gis-overview/cesium/core/ViewerManager.ts`
- `src/modules/traffic-gis-overview/cesium/layers/BasemapManager.ts`
- `src/modules/traffic-gis-overview/cesium/layers/SpatialAssetManager.ts`
- `src/modules/traffic-gis-overview/assets/SpatialAssetStore.ts`
- `src/modules/traffic-gis-overview/vector/VectorLayerStore.ts`
- `src/modules/traffic-gis-overview/adapters/http-adapter.ts`
- `src/modules/traffic-gis-overview/config/basemaps.config.ts`（默认卫星影像 WGS84，便于与 KML 叠加）
- `src/modules/traffic-gis-overview/mock/features.ts`（清空演示要素）

### 仓库侧增量调整

- `src/modules/traffic-gis-overview/config/traffic-gis.config.ts`（视角/走廊锁定对齐正式道路 `overviewRectangle`）
- `src/modules/traffic-gis-overview/types/index.ts`（增加 `designOnly`，保留 E01/E02/E03/S02 props）
- `src/views/GisPreviewPage.vue`（`design-only=true` 便于独立验收设计底图）
- `src/modules/traffic-gis-overview/data/real-layers.json` → `real-layers.json.disabled-demo`

### 未改（刻意保留）

- `src/components/gis/GisOverviewCesiumPanel.vue`
- `src/views/DashboardPage.vue` 布局与右侧 KPI
- `vite.config.ts` / `package.json`（Cesium 与 static-copy 已就绪）
- 后端 API / DB / 碳模块 / ESG 计算

---

## 4. 是否修改接口

**否（业务接口未改）。**

仅使用前端静态资源：

- `/gis/s1-6/layer-config.json`
- `/gis/s1-6/layers/*.kml`

首页 `data-mode="api"` 仍走既有 `/api/esg/gis/*`；接口失败只影响业务图层，不阻断 KML/SPX 底座。本阶段不扩展正式 GIS features API。

---

## 5. 启动与验证命令

```bash
npm ci
npm run check
npm run build
npm run dev -- --host 127.0.0.1 --port 5174
```

浏览器验收：

1. 打开领导首页：布局、右侧 KPI 不变。
2. 地图加载正式道路生态 KML + SPX；无彩色 1/2/3 标段演示线。
3. 缩放 / 拖动 / 旋转可用；SPX 不造成 Entity 洪水卡死。
4. 复位视角回到正式道路中心线范围。
5. （可选）打开 `/gis-preview`：`design-only` 仅验证设计图层。

本轮已执行：

- `npm run check` — **通过**
- `npm run build` — **通过**（产物含 `spx-kml.worker-*.js` 与 `dist/gis/s1-6`）

---

## 6. 已完成能力

- Cesium Viewer 初始化 + 在线卫星底图（WGS84）
- 正式道路生态关键要素 KML（`KmlDataSource`，保留原样式）
- SPX 边坡：WebWorker 解析 → Primitive 批量渲染 + 缓存显隐
- 设计图层管理、堆渣区编号、取弃土场隐藏策略（交接包逻辑）
- 历史对比 / 全屏快捷操作（交接包能力）
- 首页 `GisOverviewCesiumPanel` E01/E02/E03/S02 挂接点位与空白点击仍可用
- dashboard 模式过滤静态演示图层（仅纯 API 业务层）

---

## 7. 未完成 / 后续事项（Phase 2+）

- ESG 业务 GIS 融合：环境/土壤/安全/治理/RYB 正式落图与图层开关产品化
- `/api/esg/gis` 正式 features 数据与坐标补齐（无坐标则不出图）
- E02/S02 旧 `section-*` 演示 featureId 与正式 KML 对象 ID 映射（本阶段底座替换后，旧演示 ID 飞入可能空操作）
- 内网瓦片 / 地形替换；历史影像正式 URL
- 取弃土场源数据质量修复后再解隐
- 演示三维工厂资产坐标仍在旧走廊附近，需按正式线路重定位或关闭

---

## 8. 风险与注意

- 两份 KML 合计约 37MB，首屏加载需网络与内存预算；勿改回 Entity 全量加载 SPX。
- 勿把 `real-layers.json.disabled-demo` 重新挂回首页。
- 勿覆盖 `GisOverviewCesiumPanel.vue` 为交接包精简版，否则丢失工作台联动。
