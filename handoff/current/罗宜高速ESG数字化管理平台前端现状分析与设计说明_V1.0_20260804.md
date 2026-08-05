# 罗宜高速ESG数字化管理平台前端现状分析与设计说明 V1.0

> 日期：2026-08-04  
> 范围：基于仓库现有前端代码（`package.json`、`src/`、路由、视图、组件、stores、`services/api.ts`）的现状盘点  
> 约束对齐：`_handoff/罗宜高速ESG数字化管理平台_AI开发冻结基线说明_V1.0.md`  
> 说明：本文档仅作分析与改造建议，不修改应用源码。

---

## 目录

1. [一、项目技术架构](#一项目技术架构)
2. [二、现有页面结构分析](#二现有页面结构分析)
3. [三、首页设计分析](#三首页设计分析)
4. [四、现有 ESG 相关页面分析](#四现有-esg-相关页面分析)
5. [五、组件复用分析](#五组件复用分析)
6. [六、后续 ESG 功能改造建议](#六后续-esg-功能改造建议)
7. [附录：不确定项与数据通路说明](#附录不确定项与数据通路说明)

---

## 一、项目技术架构

### 1.1 前端框架与工程

| 项 | 现状（来自 `package.json`） |
|----|---------------------------|
| 项目名 | `luoyi-esg-dashboard` |
| 框架 | Vue `^3.4.15` |
| 构建 | Vite `^5.0.12`（`@vitejs/plugin-vue`） |
| 语言 | TypeScript `~5.3.3` + `vue-tsc` |
| 状态 | Pinia `^2.1.7`（实际仅 `src/stores/dashboard.store.ts`） |
| 路由 | vue-router `^4.2.5`，**Hash 模式**（`createWebHashHistory`） |
| HTTP | axios 已依赖，但业务请求主路径为 `fetch`（`src/services/api.ts`） |
| 样式 | SCSS（`sass`）+ 设计 token（`src/styles/tokens.scss`） |
| 脚本 | `dev` / `build`（`vue-tsc -b && vite build`）/ `check` / `preview` |

入口：`src/main.ts`（创建 Vue + Pinia + Router，引入 Cesium Widgets CSS、`layout.scss`、`dashboard.scss`）。  
根组件：`src/App.vue` 仅渲染 `<RouterView />`。

### 1.2 UI 组件库

**未使用 Element Plus / Ant Design Vue 等第三方 UI 库。**

实际 UI 形态：

- 自研布局与面板：`HeaderNav`、`PanelCard`、`ProjectStatusBar` 等
- 图标：`lucide-vue-next`
- 图表封装：自研 `BarMetricChart` / `RingChart` / `ProgressRing`（底层 ECharts）
- 弹窗 / 工作台面板：大量业务专用 Vue SFC

### 1.3 图表库

- **ECharts `^5.4.3`**：KPI 弹窗、碳专题、月报、S01 等均直接或间接使用
- 首页右侧碳环图：`src/components/charts/RingChart.vue`
- 风险柱状：`src/components/charts/BarMetricChart.vue`

### 1.4 地图库

- **Cesium `^1.143.0`**，构建期静态拷贝 Workers/Assets/Widgets（`vite.config.ts` + `vite-plugin-static-copy`）
- 业务模块：`src/modules/traffic-gis-overview/`（Viewer、图层、拾取、高亮、业务链跳转）
- 首页封装：`src/components/gis/GisOverviewCesiumPanel.vue`
- 应急 SVG 回退：`src/components/gis/GisOverviewPanel.vue`（由 `src/config/gis.config.ts` 的 `useRealGisOnDashboard` 控制；当前为 `true`，默认 Cesium）
- 独立预览路由：`/gis-preview` → `GisPreviewPage.vue`

### 1.5 `src/` 顶层目录结构（摘要）

```
src/
├── App.vue / main.ts / vite-env.d.ts
├── router/index.ts
├── views/                 # 页面壳
├── components/            # layout / kpi / panels / modal / e01–e04 / s02 / workspace / assistant / carbon / master / charts / gis
├── modules/traffic-gis-overview/  # Cesium GIS 子系统
├── stores/dashboard.store.ts
├── services/api.ts / esgSmartEntryDemo.ts
├── data/                  # dashboard / workspace / assistant / master / kpi-catalog / mocks
├── types/                 # dashboard / e01–e04 / s02 / workspace / assistant / monthly-report …
├── styles/                # tokens / layout / dashboard / workspace / master
├── config/gis.config.ts
├── composables/ / utils/
└── assets/
```

### 1.6 路由设计

文件：`src/router/index.ts`

| path | name | 组件 | 是否一级导航可达 |
|------|------|------|------------------|
| `/` | `dashboard` | `DashboardPage.vue` | 是（工作台首页） |
| `/assistant` | `assistant` | `AssistantPage.vue` | 是（ESG智能助手） |
| `/workspace` | `workspace` | `WorkspacePage.vue` | 是（ESG智能数据填报） |
| `/gis-preview` | `gis-preview` | `GisPreviewPage.vue` | 否（开发/预览） |

**未挂路由但已有页面文件：**

| 文件 | 状态 |
|------|------|
| `src/views/CarbonPage.vue` | 已实现碳独立页壳与 Tab，**未注册路由**，一级导航也未指向 |
| `src/views/MasterDashboardPage.vue` | 母版/实验布局，**未注册路由** |

API 代理：`vite.config.ts` 将 `/api` 代理到 `http://127.0.0.1:8765`；`api.ts` 默认 `VITE_API_BASE || 'http://127.0.0.1:8765'`。

---

## 二、现有页面结构分析

### 2.1 一级菜单

来源：`src/data/dashboard.mock.ts` → `navItems`，由 `HeaderNav.vue` 读取 `store.navs` 渲染。

| key | 文案 | 跳转 |
|-----|------|------|
| `dashboard` | 工作台首页 | `/#/` |
| `assistant` | ESG智能助手 | `/#/assistant` |
| `workspace` | ESG智能数据填报 | `/#/workspace` |

平台标题文案：`宜罗高速 ESG 数字化看板`（`HeaderNav.vue`）。

### 2.2 二级结构

#### 首页（Dashboard）

无独立二级路由。二级交互为：

- KPI 点击 → **右侧工作台面板**（E01/E02/E03/E04/S02）或 **居中弹窗**（S01/S03/S04/G01–G04）
- 右侧碳 / 月报卡片 → 专题弹窗（`CARBON` / `MONTHLY`）

#### 工作台（Workspace）

默认 Tab：`smart-upload`（ESG智能入库）。  
二级 Tab 定义：`WorkspaceNav.vue`（在智能入库态隐藏二级导航条）。

| Tab key | 文案 | 组件 | URL |
|---------|------|------|-----|
| `workspace` | 填报概览 | `WorkspaceHome.vue` | `?t=workspace` |
| `tasks` | 我的上传任务 | `WorkspaceTasks.vue` | `?t=tasks` |
| `smart-upload` | ESG智能入库 | `WorkspaceSmartEntry.vue` | `?t=smart-upload`（默认） |
| `review` | 审核管理 | `WorkspaceReview.vue` | `?t=review` |
| `documents` | 资料中心与档案 | `WorkspaceDocuments.vue` | `?t=documents` |

另有遗留组件 `WorkspaceSmartUpload.vue`（旧上传流），当前主入口已切到 `WorkspaceSmartEntry`。

#### 碳独立页（未接线）

`CarbonPage.vue` + `CarbonNav`：`overview` / `boundary` / `detail`（`?t=`）。

#### 母版页（未接线）

`MasterDashboardPage.vue`：左右 66%/34% 母版骨架，数据来自 `master.mock.ts`。

### 2.3 页面文件位置与功能

| 页面 | 路径 | 功能说明 |
|------|------|----------|
| 驾驶舱首页 | `src/views/DashboardPage.vue` | 1920×1080 缩放壳；E/S/G KPI + Cesium GIS + 右栏风险/碳/月报；KPI 下钻 |
| ESG 智能助手 | `src/views/AssistantPage.vue` | 侧栏会话 + 聊天区 + 数据依据抽屉；API + mock 回退 |
| ESG 智能数据填报 | `src/views/WorkspacePage.vue` | 填报/任务/智能入库/审核/资料 |
| GIS 预览 | `src/views/GisPreviewPage.vue` | 独立 TrafficGisOverview，调试业务链 |
| 碳独立页 | `src/views/CarbonPage.vue` | 碳概览/边界/明细（**未挂路由**） |
| 母版驾驶舱 | `src/views/MasterDashboardPage.vue` | 布局实验（**未挂路由**） |

---

## 三、首页设计分析

### 3.1 页面布局

设计稿尺寸：**1920×1080**，整页 `scale` 适配视口（`DashboardPage.vue`）。

栅格（`src/styles/layout.scss`）：

| 区域 | 占比 / 高度 | 内容 |
|------|-------------|------|
| Header | `--dashboard-header-h` | `HeaderNav` |
| 左列 | **66%** | E+S KPI → GIS → 建设时序 |
| 右列 | **34%** | G KPI →（默认）综合风险 / 碳 / 月报；或工作台面板槽位 |

工作台激活时：右栏替换为 `E01/E02/E03/E04/S02` 面板，**仍占用 34% 列宽**，不改整体布局。

### 3.2 模块划分

| 模块 | 组件 | 说明 |
|------|------|------|
| E/S KPI | `TopKpiGroups`（`group-keys=['E','S']`） | 左上 |
| G KPI | `TopKpiGroups`（`group-keys=['G']`） | 右上 |
| GIS | `GisOverviewCesiumPanel` / 回退 `GisOverviewPanel` | 中左 |
| 建设时序 | `ConstructionTimeline` | 左下 |
| 综合风险态势 | `ComplianceRiskPanel` | 右栏默认 |
| 碳足迹与低碳增益 | `CarbonBenefitPanel` | **独立模块，不属于 E 组** |
| 月报资料归集 | `MonthlyReportPanel` | 右栏默认 |

KPI 正式口径目录：`src/data/kpi-catalog.ts`（E04 已为 **文物保护管控**）。

首页 KPI 文案（mock / catalog 一致）：

| 组 | 指标 |
|----|------|
| E | E01 环境影响事件；E02 未闭环环境问题；E03 生态保护事项；**E04 文物保护管控** |
| S | S01 连续安全生产天数；S02 重大风险源管控；S03 农民工权益保障；S04 群众诉求闭环 |
| G | G01 合规审批事项；G02 合规问题闭环；G03 参建单位履约评价；G04 治理内控风险 |

> 冻结基线一致：**碳足迹不纳入 E 组**；E4 = 文物保护管控。代码中 E04 已按文物实现，旧「累计碳排放」弹窗 `E04CarbonEmissionModal.vue` 为遗留文件。

### 3.3 卡片组件

| 组件 | 路径 | 职责 |
|------|------|------|
| `TopKpiGroups` | `components/kpi/TopKpiGroups.vue` | 按组过滤渲染 |
| `KpiGroupPanel` | `components/kpi/KpiGroupPanel.vue` | E/S/G 分组容器 |
| `KpiCard` | `components/kpi/KpiCard.vue` | 单指标卡 |
| `PanelCard` | `components/layout/PanelCard.vue` | 右栏面板壳 |

### 3.4 数据展示方式

| 数据域 | 加载策略 | 关键文件 |
|--------|----------|----------|
| KPI 组数值 | `getDashboardKpis()`，失败保留 `dashboard.mock` | `dashboard.store.ts` |
| 右栏 panels（风险/碳/GIS/时序/月报摘要） | `getDashboardPanels()`，失败保留 mock | 同上 |
| 月报归集率 | `getMonthlyReportReadiness()`，失败 mock + error 标记 | 同上 |
| KPI 详情弹窗 | 点击时 `getDashboardKpiDetail(key)`；失败 `loadError` 壳 | `DashboardPage.vue` |
| E01–E04 / S02 工作台 | 专用 REST（如 `/api/environment/e01/events`） | 各 `*WorkspacePanel.vue` |
| 碳 / 月报专题弹窗 | `getDashboardTopic('carbon'|'monthly-report')`，失败用 mock topic | `DashboardPage.vue` |

整体模式：**API 优先 + mock 兜底**。后端是否连上 MySQL，取决于本机 `8765` 服务；前端本身无法证明库是否 live。

### 3.5 弹窗 vs 工作台交互

| 触发 | 交互形态 | 说明 |
|------|----------|------|
| E01 / E02 / E03 / E04 / S02 | **右侧工作台面板** + GIS 联动 | 不打开 `KpiDetailModal` |
| S01 / S03 / S04 / G01–G04 | **`KpiDetailModal` 分发到专用 Modal** | Teleport 到 body |
| 碳 / 月报卡片 | `CarbonBenefitModal` / `MonthlyReportModal` | 经 `KpiDetailModal` 分支 |
| GIS 业务链 | `openKpiFromBusinessLink` → E02/E03/S02 工作台 | `GisOverviewCesiumPanel` |

`KpiDetailModal.vue` 内仍保留 E01/E02/E03/E04 的通用详情 UI（历史遗留），但首页主路径对 E01–E04/S02 已改为工作台，**不再走该通用壳**。

---

## 四、现有 ESG 相关页面分析

完成程度口径：

- **高**：主路径可用，API 契约已接，失败有明确错误/空态  
- **中**：UI 完整，数据部分 API / 部分 mock，或业务闭环未完  
- **低**：仅 UI/Demo，或未接线 / 口径错位  
- **遗留**：文件存在但主路径不使用  

### 4.1 总览表

| 表面 | 完成度 | 数据 | 主入口 |
|------|--------|------|--------|
| 首页壳 + 布局 | 高 | mock+API | `/` |
| E01 工作台 | 高 | API | KPI E01 |
| E02 工作台 | 高 | API（formal/demo scope） | KPI E02 |
| E03 工作台 | 高 | API | KPI E03 |
| E04 文物工作台 | 中–高 | API；依赖后端文物表 | KPI E04 |
| S01 弹窗 | 高 | `/api/dashboard/kpi/S01` | KPI S01 |
| S02 工作台 | 高 | `/api/social/s02/risks` | KPI S02 |
| S02 弹窗 | 遗留 | API 能力在，但首页不打开 | `S02SafetyRiskModal` |
| S03 / S04 弹窗 | 中 | KPI detail API + 本地展示 | KPI |
| G01 / G04 弹窗 | 中 | KPI detail API | KPI |
| G02 弹窗路由 | **中偏低（口径风险）** | 见下 | KPI G02 |
| G03 履约评价 | 中（诚实空态） | 台账未建，不编造 | KPI G03 |
| 综合风险面板 | 中 | panels API / mock | 首页右栏 |
| 碳首页面板 + 弹窗 | 中 | panels + topic API / mock | 右栏点击 |
| 碳独立页 | 低（未接线） | 页内组件 | 无路由 |
| 月报面板 + 弹窗 | 中 | readiness API + topic | 右栏点击 |
| 助手页 | 中 | `askAssistant` + mock 回退 | `/assistant` |
| 智能入库 | 中（Demo 闭环） | 前端 mock/JSON + demo 资源 | Workspace 默认 Tab |
| 填报任务/审核/资料 | 中 | 部分 API、部分 mock | Workspace 各 Tab |
| Master 页 | 低 | 纯 mock | 无路由 |

### 4.2 首页 E01–E04

#### E01 环境影响事件

- **已实现**：`E01WorkspacePanel`；列表/分类筛选；与 Cesium 点位选中、fit、联动；`getE01Events` / 详情 / 趋势接口在 `api.ts`
- **缺失**：督办真实写回（原型按钮）；完整告警闭环回写 `biz_risk_warning`
- **建议**：保持壳与尺寸冻结；补写接口与证据链，不改布局

#### E02 未闭环环境问题

- **已实现**：`E02WorkspacePanel` + `E02ClosureAnalysisPopover`；状态分组（整改中/待复查/待销项）；GIS 联动；`getE02Issues(scope?)`
- **缺失**：真实督办/销项写操作；部分 GIS demo 元数据需后端配合
- **建议**：延续 formal/demo 双 scope 策略；首页壳不动

#### E03 生态保护事项

- **已实现**：`E03WorkspacePanel` + popover；与 E02 同构的工作台模式；`getE03Issues`
- **缺失**：与冻结口径「生态敏感区/保护对象」的对象级追溯若后端未齐，前端只能展示问题台账
- **建议**：对象表齐备后强化对象→事项→风险链路，UI 壳复用 E02

#### E04 文物保护管控（**当前代码事实**）

- **现状**：KPI 标签为「文物保护管控」；点击打开 `E04CulturalRelicWorkspacePanel.vue`；调用 `/api/environment/e04/cultural-objects`
- **已实现**：对象列表、概览指标（对象数/措施落实率/风险/状态）、详情拉取、空态友好
- **缺失**：GIS 文物图层联动（首页 GIS props 目前主要服务 E01/E02/E03/S02）；与风险预警表深度闭环
- **遗留**：`E04CarbonEmissionModal.vue`、`KpiDetailModal` 内旧 E04 碳排放分支 —— **勿再当作现行 E04**
- **建议**：按冻结基线把 E04 定位为文物；碳只走独立模块；可补 GIS 图层但不改首页栅格

### 4.3 S01–S04

| 指标 | 交互 | 已实现 | 缺失 | 建议 |
|------|------|--------|------|------|
| S01 | `S01SafetyProductionModal` | 连续天数、阶段、图表；`getDashboardKpiS01` | 中断事件写回、与安全台账深度联动 | 维持弹窗；继续 API 驱动 |
| S02 | **工作台** `S02WorkspacePanel` | 重大/较大筛选、GIS 落点、`getS02Risks` | 销号写操作；`S02SafetyRiskModal` 与工作台双轨未统一 | 以工作台为主；弹窗标遗留或复用内容 |
| S03 | `S03LaborDisputeModal` | 详情弹窗 + KPI API | 工资/纠纷对象级闭环、填报联动不足 | 弹窗内容增强；数据绑台账 |
| S04 | `S04MassAppealModal` | 同上 | 诉求闭环写回、时限预警与风险面板打通 | 同 S03 |

### 4.4 G01–G04

| 指标 | `KpiDetailModal` 分发 | 实际拉数 | 说明 |
|------|----------------------|----------|------|
| G01 | `G01ApprovalModal` | `/api/dashboard/kpi/G01` | 合规审批 |
| G02 | **`G03RectificationModal`** | 该 Modal 内请求 **`G03`** | **路由键与接口键不一致**；另有未接线的 `G02LicenseModal`（请求 G02） |
| G03 | `G03ContractorEvalModal` | 空态「待评价 / 台账未接入」 | 符合「不编造」口径 |
| G04 | `G04ComplianceModal` | `/api/dashboard/kpi/G04` | 许可+关键合规资料 |

**修改建议（高优先级）：** 理清 G02「合规问题闭环」应对 `G02` 接口还是整改 Modal；将 `G02LicenseModal` 与 `G03RectificationModal` 的职责对齐冻结口径，避免 G02 点击拿到 G03 数据。

### 4.5 综合风险态势（ComplianceRiskPanel）

- **已实现**：红黄蓝语义卡片、预警构成图、保障措施列表；数据来自 store（API panels 或 mock）
- **缺失**：与 `biz_risk_warning` 逐条下钻、点击跳转对应 E/S/G 工作台的稳定链路
- **建议**：保持面板尺寸；指标替换为规则计算结果；点击跳转复用现有 workspace/modal 模式

### 4.6 碳足迹与低碳增益（独立模块）

- **首页**：`CarbonBenefitPanel` → 点击 `handleTopicSelect('CARBON')` → `CarbonBenefitModal`
- **独立页**：`CarbonPage` + `CarbonOverview/Boundary/Detail` **未挂路由、未进 HeaderNav**
- **已实现**：首页展示与专题弹窗；API topic 可选
- **缺失**：独立页接线；与核算明细库的完整绑定；勿再挂回 E04
- **建议**：碳保持独立；若需要二级页，新增路由与导航需**单独确认**（冻结基线禁止擅自改导航结构）

### 4.7 E01/E02/E03/E04/S02 工作台面板

共性模式（推荐复用范式）：

1. 右栏替换默认三面板  
2. 拉取 overview + list  
3. 与 GIS 选中态双向绑定  
4. Esc 分层关闭（先清选中，再关面板）

### 4.8 助手页（AssistantPage）

- **已实现**：欢迎问题、会话区、数据依据抽屉、`askAssistant`（POST `/api/assistant/ask`，回退 GET `/api/assistant/qa`）；失败用 `assistant.mock` / `demoBusinessAnswers`
- **缺失**：全量业务问答覆盖、与各指标工作台深链、鉴权与审计
- **建议**：优先把高频问题绑到真实指标计算；UI 壳保持

### 4.9 ESG 智能入库（WorkspaceSmartEntry）

- **已实现**：一页式上传 → AI 分析动效 → 人工核对 → Demo 入库清单；本地 `esg-smart-entry-analysis.mock.json` + `esgSmartEntryDemo.ts`
- **缺失**：真实解析服务、入库写库、与 WorkspaceTasks/审核流的硬绑定
- **建议**：Demo 可演示；正式化时对接 `/api/workspace/ai/*` 已有客户端方法，替换 mock 阶段机

### 4.10 月报模块

- **首页**：`MonthlyReportPanel`（归集率 readiness）+ 点击 `MonthlyReportModal`
- **已实现**：readiness 校验工具、API/mock 回退
- **缺失**：月报独立页若设计存在于 `_handoff/碳核算与月报独立页/`，当前前端路由未体现
- **建议**：首页模块保留；独立页同样需确认导航冻结边界

### 4.11 工作台其余 Tab

| Tab | 完成度 | 备注 |
|-----|--------|------|
| 填报概览 | 中 | `getWorkspaceSummary/Tasks`，失败用 mock |
| 我的上传任务 | 中 | API 列表 + 本地筛选；`TaskModal` |
| 审核管理 | 中偏低 | 大量 `workspace.mock` 时间线/要求 |
| 资料中心 | 中偏低 | 列表可 API，细节常 mock |

---

## 五、组件复用分析

### 5.1 可复用（优先）

| 类别 | 组件 / 模块 | 复用场景 |
|------|-------------|----------|
| 布局壳 | `HeaderNav`、1920 缩放壳、`PanelCard` | 所有一级页 |
| KPI | `TopKpiGroups` / `KpiGroupPanel` / `KpiCard` | 首页指标；Master 勿反向污染正式首页 |
| 工作台范式 | `E01/E02/E03/E04/S02 *WorkspacePanel` | S03/S04/G 若升级为右栏下钻可抄结构 |
| 弹窗范式 | `S01/S03/S04/G0x *Modal` | 轻量指标详情 |
| 图表 | ECharts 封装、`RingChart`/`BarMetricChart` | 专题与风险 |
| GIS | `traffic-gis-overview`、`GisOverviewCesiumPanel` | 对象落点与业务链 |
| API 层 | `services/api.ts` | 统一 base、空失败返回 null |
| 口径目录 | `kpi-catalog.ts` | 文案与追溯元数据 |

### 5.2 建议新增（在不改布局前提下）

| 新增项 | 原因 |
|--------|------|
| 统一「风险下钻」适配器 | 综合风险 → 各 KPI 工作台/弹窗 |
| G02 专用整改 Modal 与接口对齐层 | 消除 G02/G03 错绑 |
| E04 GIS 图层适配 | 文物对象空间表达 |
| Workspace 智能入库真实解析客户端 | 替换 Demo 时序 |
| （可选）碳/月报路由 —— **须先解冻导航** | 文件已存在但未接线 |

### 5.3 不能修改（对齐冻结基线）

依据 `_handoff/罗宜高速ESG数字化管理平台_AI开发冻结基线说明_V1.0.md`：

| 冻结项 | 含义 |
|--------|------|
| 首页整体布局 | 左 66% / 右 34%、KPI/GIS/时序/右栏结构 |
| 原有页面尺寸 | 1920×1080 壳与关键 CSS 高度变量 |
| 字体大小体系 / 颜色主题 | `tokens.scss` 体系 |
| 导航结构 | 三个一级入口文案与结构 |
| 碳不入 E 组 | 碳保持独立模块 |
| E4 = 文物 | 禁止把 E04 改回碳排放 |
| E01–E03（及已成型的 E04/S02）工作台壳 | 允许换数据与下钻内容，禁止重做布局 |

**允许**：替换指标数据、增加详情/下钻内容、Demo 数据展示（结构须可追溯）。

**遗留勿当基线**：`E04CarbonEmissionModal`、未接线 `CarbonPage`/`MasterDashboardPage`、`G02LicenseModal` 未挂载、`KpiDetailModal` 内旧 E01–E04 通用壳。

---

## 六、后续 ESG 功能改造建议

### 6.1 首页如何接入 E/S/G

保持现有交互分流，只换数据与补闭环：

```
KPI 点击
 ├─ E01/E02/E03/E04/S02 → 右栏 WorkspacePanel + GIS
 ├─ S01/S03/S04/G01–G04 → 专用 Modal（经 KpiDetailModal 分发）
 └─ 碳/月报卡片 → 专题 Modal（独立模块）
```

建议顺序（对齐冻结「库表 → 接口 → 页面 → 风险闭环」）：

1. 校正 G02/G03 分发与接口键  
2. 首页 KPI 组全面走 `/api/dashboard/kpis`（去掉静默 mock 偏差）  
3. 综合风险面板绑定 `biz_risk_warning` 并支持下钻  
4. S03/S04/G 弹窗明细对齐对象表  
5. E04 补 GIS；碳保持独立

### 6.2 二级页面如何设计

| 场景 | 推荐模式 | 理由 |
|------|----------|------|
| 需地图联动、列表+详情 | **右栏 WorkspacePanel**（E01 范式） | 不破布局，已验证 |
| 强叙事/单主题（S01、履约空态） | **居中 Modal** | 信息密度适合弹层 |
| 填报/入库/审核 | **Workspace Tab** | 已有壳与 `?t=` 深链 |
| 碳/月报重核算页 | 独立页（需解冻导航后接线） | 文件已备，勿塞进 E 组 |

避免再开第三套布局（Master 页仅作参考，不要替换正式 Dashboard）。

### 6.3 数据接口如何绑定

| 层级 | 路径 | 说明 |
|------|------|------|
| 前端客户端 | `src/services/api.ts` | `apiGet`/`apiPost`，失败返回 `null` |
| 本地开发 | Vite proxy `/api` → `:8765` | 与 `VITE_API_BASE` 双通道 |
| Store | `dashboard.store.ts` | 首页聚合态；KPI 详情按需拉取 |
| 工作台面板 | 组件内直接调专用 API | 如 E01 events、E04 cultural-objects、S02 risks |
| Mock | `src/data/*.mock.ts` | 离线演示与 API 失败兜底 |
| 口径 | `kpi-catalog.ts` | 文案/单位/来源，改口径优先改目录 |

推荐改造约束：

1. **禁止**为演示在页面硬编码新业务指标（冻结约束）  
2. API 失败必须可见（`loadError` / 空态），禁止静默假数据冒充正式结论（G03 空态是正确范例）  
3. 新指标先对象表 → 计算接口 → 再挂 KPI 卡  
4. 风险统一：事实 → 规则 → `biz_risk_warning` → 红黄蓝 → 整改闭环  

### 6.4 短期改造清单（建议）

| 优先级 | 项 |
|--------|----|
| P0 | 修复 G02 Modal/API 错绑；确认 E04 文物为唯一现行语义 |
| P0 | 首页 KPI/panels 在后端可用时避免过期 mock 数值漂移 |
| P1 | 综合风险 → 各指标工作台/弹窗下钻 |
| P1 | S03/S04/G01/G04 明细对齐台账字段 |
| P2 | 智能入库 Demo → 真实解析/入库 API |
| P2 | E04 GIS；清理或隔离 `E04CarbonEmissionModal` 等遗留 |
| P3 | 碳/月报独立页是否入导航（需产品确认，触及冻结导航） |

---

## 附录：不确定项与数据通路说明

| 项 | 说明 |
|----|------|
| MySQL 是否 live | 前端仅请求 `:8765`；库是否接通取决于后端进程与配置，**本文未启动后端验证** |
| panels/KPI 接口返回质量 | 代码路径存在；未做联调快照断言 |
| G02 业务真值 | 存在组件/接口命名历史债，以产品口径最终裁定为准 |
| `WorkspaceSmartUpload` | 仍在仓库，主路径已是 `WorkspaceSmartEntry` |
| 冻结基线「禁止用页面模拟数据替代数据库逻辑」 | 当前工程仍大量 mock 兜底，属演示现实；后续应以 API+库为准逐步收敛 |

---

## 文档修订记录

| 版本 | 日期 | 说明 |
|------|------|------|
| V1.0 | 2026-08-04 | 首版：基于仓库源码盘点的前端现状分析与改造建议 |
