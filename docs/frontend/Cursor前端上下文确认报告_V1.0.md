# Cursor前端上下文确认报告 V1.0

| 项 | 内容 |
|---|---|
| 日期 | 2026-08-04 |
| 任务性质 | 仅建立前端上下文；**未改**代码 / 页面 / 样式 / API |
| 唯一工作区 | `C:\ESG_Project` |
| Cursor 前端工作根 | `C:\ESG_Project\frontend`（已执行 `move_agent_to_root`） |
| 基线版本 | ESG Demo **V0.3**：首页一级指标业务事实校正版 |

---

## 1. 前端技术栈（Vue / Vite / TS / UI / 图表 / GIS）

来源：`frontend/package.json`、`vite.config.ts`、`src/main.ts`。

| 类别 | 选型与版本（package.json 声明） |
|---|---|
| 框架 | Vue `^3.4.15` |
| 构建 | Vite `^5.0.12`（`@vitejs/plugin-vue` `^5.0.3`） |
| 语言 | TypeScript `~5.3.3`（`vue-tsc` `^1.8.27`） |
| 路由 / 状态 | vue-router `^4.2.5`；Pinia `^2.1.7` |
| HTTP | axios `^1.6.7`（首页主链路实际多用 `fetch`，见 `services/api.ts`） |
| UI | **无** Element Plus / Ant Design 等组件库；自研 SCSS + `lucide-vue-next` `^0.511.0` |
| 图表 | ECharts `^5.4.3`（`components/charts/*`） |
| GIS | Cesium `^1.143.0`；运行模块 `src/modules/traffic-gis-overview/` |
| 样式 | Sass `^1.70.0`；入口引入 `styles/layout.scss`、`styles/dashboard.scss` |

脚本：`dev` / `build`（`vue-tsc -b && vite build`）/ `check`（`vue-tsc -b`）/ `preview`。

- 包名：`luoyi-esg-dashboard`（`version: 0.0.0`）。
- **无**独立 `frontend/README.md`。
- 开发代理：`vite.config.ts` 将 `/api` 代理到 `http://127.0.0.1:8765`。
- API 基址：`VITE_API_BASE` 默认 `http://127.0.0.1:8765`（`services/api.ts`）。
- Cesium 静态资源：`vite-plugin-static-copy` 复制 Workers/Assets/Widgets/ThirdParty；`CESIUM_BASE_URL` 区分 serve/build。

源码规模（约）：`src` 下非 GIS 模块约 124 个 `.vue/.ts/.scss`；`traffic-gis-overview` 约 46 个。

---

## 2. 页面结构（首页驾驶舱、ESG、GIS）与 views / components / router / services

### 2.1 路由（`src/router/index.ts`，Hash History）

| 路径 | name | 视图 | 说明 |
|---|---|---|---|
| `/` | `dashboard` | `views/DashboardPage.vue` | 领导层首页驾驶舱（主入口） |
| `/assistant` | `assistant` | `views/AssistantPage.vue` | ESG 智能助手 |
| `/workspace` | `workspace` | `views/WorkspacePage.vue` | ESG 工作台 |
| `/gis-preview` | `gis-preview` | `views/GisPreviewPage.vue` | GIS / Cesium 预览页 |

浏览器入口：`http://localhost:5173/#/`（根 `README.md`）。

### 2.2 views

| 文件 | 路由挂载 | 备注 |
|---|---|---|
| `DashboardPage.vue` | 是 | 首页 |
| `WorkspacePage.vue` | 是 | ESG 工作台壳 |
| `AssistantPage.vue` | 是 | 助手 |
| `GisPreviewPage.vue` | 是 | 异步加载 `TrafficGisOverview` |
| `CarbonPage.vue` | **否** | 源码存在，router 未注册 |
| `MasterDashboardPage.vue` | **否** | 源码存在，router 未注册 |

### 2.3 components 分组

| 目录 | 用途 |
|---|---|
| `components/kpi/` | `TopKpiGroups` → `KpiGroupPanel` → `KpiCard` |
| `components/layout/` | `HeaderNav`、`PanelCard`、`ProjectStatusBar` |
| `components/panels/` | 合规风险、碳效益、月报、施工进度、GIS SVG 等 |
| `components/gis/` | `GisOverviewCesiumPanel`、`GisOverviewPanel`（SVG）、图例/图层 |
| `components/e01`–`e04`、`s02` | KPI 右侧工作台面板 |
| `components/modal/` | KPI / S / G / 专题详情弹窗 |
| `components/workspace/` | 工作台子页（Home/Tasks/SmartEntry/Review/Documents 等） |
| `components/assistant/` | 助手聊天 UI |
| `components/carbon/`、`components/master/` | 碳专题 / Master 布局（部分对应未挂路由视图） |
| `components/charts/` | ECharts 封装（`BarMetricChart`、`RingChart` 等） |

### 2.4 services / stores / 配置

| 路径 | 作用 |
|---|---|
| `services/api.ts` | 统一 API（首页 KPI、panels、risk-warnings、E/S/G 明细、工作台、助手等） |
| `services/esgSmartEntryDemo.ts` | ESG 智能入库 Demo 流程 |
| `stores/dashboard.store.ts` | 初始化时 `bootstrapHome()`：`loadKpis` + `loadPanels` + `loadEsgHomeStatus` |
| `config/gis.config.ts` | `useRealGisOnDashboard: true`（首页默认 Cesium；SVG 应急回退） |
| `data/kpi-catalog.ts` | 首页 12 项 KPI 正式名称/单位目录 |
| `utils/esg-home.ts` | 将 catalog / ESG home 状态合并进 KPI 展示 |

GIS 运行时：`src/modules/traffic-gis-overview/`（Cesium Viewer、图层、适配器、配置）。首页经 `GisOverviewCesiumPanel` 嵌入；独立页为 `/gis-preview`。

`src` 顶层目录：`assets`、`components`、`composables`、`config`、`data`、`modules`、`router`、`services`、`stores`、`styles`、`types`、`utils`、`views`。

---

## 3. 当前首页结构确认（入口、KPI 卡、API、样式）

### 3.1 入口与布局

- **入口页**：`DashboardPage.vue`（路由 `/`）。
- **画布**：1920×1080 等比缩放（`screen-wrapper` / `screen-canvas`）。
- **顶栏**：`HeaderNav` — 标题「宜罗高速 ESG 数字化看板」+ store.navs。
- **左侧**：E/S KPI（`TopKpiGroups group-keys=['E','S']`）→ 中央 GIS（Cesium 或 SVG）→ `ConstructionTimeline`。
- **右侧**：G 组 KPI → 默认合规/碳/月报三面板；选中 E01/E02/E03/E04/S02 时切换对应 WorkspacePanel；其它 KPI / 专题走 `KpiDetailModal`。

### 3.2 KPI 卡（V0.3 冻结 12 项）

目录：`data/kpi-catalog.ts`（`KPI_HOME_CATALOG`）。

| 组 | 代码 | 正式名称（目录） | 单位要点 |
|---|---|---|---|
| E | E01–E04 | 环保风险预警 / 水保风险预警 / 生态保护管控 / 文物保护管控 | E04：0 处可展示调查完成/风险正常 |
| S | S01–S04 | 连续安全生产天数 / 重大风险源管控 / 农民工权益保障 / 群众诉求闭环 | S01：天；S03：`%` |
| G | G01–G04 | 合规审批事项 / 许可及施工管控 / 设计变更管理 / 内控与廉洁 | 合规率/完成率/受控率等表达（业务事实见 V0.3 README） |

组件链：`TopKpiGroups` ← Pinia `kpis` ← API 或 `data/dashboard.mock.ts` / `esg-home.mock.ts`（失败回落）。

### 3.3 首页相关 API 调用点（只读确认，未改）

| 调用 | 路径 / 行为 |
|---|---|
| `getDashboardKpis` / Raw | `GET /api/dashboard/kpis` |
| `getDashboardRiskWarnings` | `GET /api/dashboard/risk-warnings?...` |
| `getDashboardPanels` | `GET /api/dashboard/panels` |
| `getEsgHomeStatus` | 组合上述接口并规范化；失败回落 mock |
| `getDashboardKpiDetail` | `GET /api/dashboard/kpi/{key}` |
| `getDashboardTopic` | carbon / monthly-report 专题 |
| 健康检查 | `GET /health` |

运行链路（根 README / V0.3 README）：

```text
浏览器 http://localhost:5173/#/
  → Vite /api 代理或 VITE_API_BASE
  → Python API 127.0.0.1:8765
  → MySQL 127.0.0.1:3307 / luoyi_esg
  → v_esg_demo_dashboard_kpis
```

### 3.4 样式文件

| 文件 | 用途 |
|---|---|
| `styles/tokens.scss` | 设计令牌 |
| `styles/layout.scss` | 全局布局（main 引入） |
| `styles/dashboard.scss` | 首页驾驶舱（main 引入） |
| `styles/workspace.scss` | 工作台 |
| `styles/master.scss` | Master 相关 |
| `styles/partials/_button|_modal|_tag|_table.scss` | 局部 partial |
| `App.vue` | 根背景 `#020b18`、全屏 overflow hidden |

---

## 4. 基线与冻结范围 / 禁止操作（引用 PROJECT_RULES）

依据：`C:\ESG_Project\PROJECT_RULES.md`、`README.md`、`versions/V0.3_homepage_kpi_calibration/README.md`。

### 4.1 当前基线

- **版本**：ESG Demo V0.3 — 首页一级指标业务事实校正版（冻结日 2026-08-04）。
- **已冻结要点**：首页 12 项 E/S/G 一级 KPI 业务展示方向；E04 无对象显示 0 处；S01 自 2026-05-08 起算；S03 百分比；G 组合规率/完成率/受控率/合规状态表达。
- **归档位置**：`versions/V0.3_homepage_kpi_calibration/`（只读理解基线；**不**在 `versions/` 内改代码）。

### 4.2 唯一工作区与禁止项

- 唯一开发工作区：`C:\ESG_Project`；禁止在旧 TRAE 工作区开发、建第二套项目、临时目录改项目、旧目录全量覆盖新工作区。
- 修改前须说明：文件、原因、影响范围、验证方式。
- 禁止未经确认：自动重构架构、自动优化首页、改 API 路径/字段、改未确认业务模块、删历史资料、把 Demo 当正式数据。
- **首页一级指标及 V0.3 业务事实已冻结**：名称/数值/单位/口径/描述/风险等级调整须人工确认并记录来源。
- 迁移验收完成前禁止：S 组详细页深化、G 组深化、E 组一级指标口径调整、GIS 替换或新数据源、正式库迁移。
- 数据：禁止编造真实业务数据、改已确认口径、删事实链/已确认字段；Demo 须标识 `demo`。

### 4.3 验证要求（若后续改前端）

```powershell
npm.cmd ci --prefix frontend
npm.cmd run check --prefix frontend
npm.cmd run build --prefix frontend
```

---

## 5. 工作区确认

| 项 | 确认 |
|---|---|
| 当前唯一工作区 | `C:\ESG_Project` |
| 前端目录（Cursor 主战场） | `C:\ESG_Project\frontend` |
| `move_agent_to_root` | **已成功**切换至 `C:\ESG_Project\frontend` |
| 旧 TRAE 路径 | `...\work-mode-projects\6a53a1b3d0f497e311ecc95f` — **已停止作为开发工作区**；仅作历史追溯/只读对照 |
| Git | `C:\ESG_Project` 与 `frontend` **均无** `.git`；版本追溯依赖迁移清单与 `versions/V0.3_*` |
| 项目级文档目录 | `C:\ESG_Project\docs\frontend\`（本报告主路径） |
| 同步副本 | `C:\ESG_Project\frontend\docs\frontend\`（便于前端工作根内发现） |

### 路径备注

1. `frontend/README.md` 缺失；说明分散在根 `README.md`、`docs/`、本报告。
2. `views/CarbonPage.vue`、`views/MasterDashboardPage.vue` 未挂路由。
3. `public/` 含 shp GeoJSON 与 `gis/s1-6` KML 等静态 GIS 资源（只读扫描确认存在）。

---

## 6. 状态

| 角色 | 状态 |
|---|---|
| Cursor | ✅ 前端上下文确认完成 |
| 代码 / 页面 / 样式 / API | 无改动 |
| 本文件 | 仅新增/更新上下文确认报告 |
| 下一步 | **等待 V0.4** 业务调整影响分析后再动手改前端 |

---

*报告生成方式：只读扫描 `C:\ESG_Project` 基线文档与 `frontend` 源码结构；未执行 commit；未修改业务代码。*
