# 罗宜高速ESG数字化管理平台 · 前端改造计划与涉及文件清单 V1.1

> 日期：2026-08-04  
> **本阶段仅出计划，不修改代码。**  
> 依据：任务书 V1.1（实施版）、AI 开发冻结基线 V1.0、前端现状分析 V1.0、仓库源码 spot-check  
> 任务书摘录：`_handoff/罗宜高速ESG数字化管理平台_Cursor前端开发任务书_V1.1_实施版.md`

---

## 0. 依据与边界

### 0.1 任务书 V1.1 目标摘要

任务书定位为**前端增量开发**说明，明确：

- 基于现有前端，**不重新设计平台、不替换现有架构**。
- 目标：在保持视觉、布局和技术架构不变的基础上，实现 **ESG 指标体系、业务对象展示、风险预警和闭环管理**。
- 展示三种模式（与现状一致）：
  - **工作台模式**：E01、E02、E03、E04、S02（首页指标 → 右侧工作台 → 对象列表 → 详情 → 风险 → 整改闭环）
  - **弹窗模式**：S01、S03、S04、G01–G04
  - **Workspace 模式**：填报、智能入库、审核、资料中心
- 首页改造仅限：E/S/G 数据接入、红黄蓝风险数量、指标下钻、与业务对象关联；**禁止新增首页大模块、修改原有栅格**。
- 开发优先级（任务书第十章）：① 首页指标接入 → ② 完善 E01–E04 工作台 → ③ 完善 S/G 详情 → ④ 风险预警闭环。
- 数据要求：禁止页面硬编码业务指标；Mock 与 API 结构一致；未来 Mock → 真实接口。

### 0.2 冻结约束（必须遵守）

对齐 `_handoff/罗宜高速ESG数字化管理平台_AI开发冻结基线说明_V1.0.md` 与任务书第二章：

| 冻结项 | 含义 |
|--------|------|
| 首页整体布局 | 左 66% / 右 34%，KPI / GIS / 时序 / 右栏结构不变 |
| 1920×1080 驾驶舱比例 | `DashboardPage` 缩放壳与关键高度变量不动 |
| 颜色 / 字体 / 组件风格 | `tokens.scss` 与现有组件视觉体系 |
| 一级导航结构 | 工作台首页 / ESG智能助手 / ESG智能数据填报 |
| 技术框架与目录结构 | Vue3 + TS + Vite；不引入新 UI 框架重构 |
| **碳足迹独立模块** | **不纳入 E 组**；不走 E04 |
| **E4 = 文物保护管控** | 禁止把 E04 改回碳排放 |
| 未经确认 | 不得新增指标、不得改导航、不得改整体视觉结构 |

### 0.3 与现状分析文档的对齐说明

基线文档：`_handoff/罗宜高速ESG数字化管理平台前端现状分析与设计说明_V1.0_20260804.md`。

本计划**以该文档 + 2026-08-04 仓库 spot-check 为当前态**，不以历史「E04=碳排放」交付包为准。已核实：

| 事实 | 路径 / 证据 |
|------|-------------|
| E04 现行 = 文物工作台 | `src/components/e04/E04CulturalRelicWorkspacePanel.vue`；`DashboardPage` 中 `kpiKey === 'E04'` → `openE04Workspace()` |
| E04 API | `getE04CulturalObjects` / `getE04CulturalObjectDetail` → `/api/environment/e04/cultural-objects` |
| KPI 目录 E04 文案 | `src/data/kpi-catalog.ts` →「文物保护管控」 |
| 碳为独立模块 | `CarbonBenefitPanel` + `CarbonBenefitModal`；`handleTopicSelect('CARBON')` |
| G02 错绑仍在 | `KpiDetailModal.vue`：`detail.key === 'G02'` → `G03RectificationModal` |
| 未接线遗留 | `E04CarbonEmissionModal.vue`、`G02LicenseModal.vue`（未挂主路径）、`CarbonPage.vue`（无路由） |

因此对 E04 的改造表述为：**巩固 / 补齐**（空态文案、GIS、风险闭环），**不是从零替换**。

### 0.4 OUT OF SCOPE / 禁止事项

**本计划阶段与后续实施均禁止：**

1. 修改首页栅格、字号体系、主题色、一级导航。
2. 把碳足迹塞回 E 组或恢复 `E04CarbonEmissionModal` 为主路径。
3. 用 Master 页（`MasterDashboardPage`）替换正式驾驶舱。
4. 擅自挂载碳/月报独立页路由（触及导航冻结，需产品单独解冻）。
5. 为演示在页面硬编码新业务指标数值作为「正式结论」。
6. 扩大任务书未列指标（如新增 E05 等）。
7. 本计划文档阶段：**不修改任何应用源码**；仅允许 `_handoff/` 计划与任务书摘录。

**本计划不包含（可记依赖，但不做前端范围扩张）：**

- 后端表结构 / 迁移 / 规则引擎实现细节（仅列前端契约缺口）。
- Workspace 智能入库从 Demo 到生产的完整后端解析服务（Phase F 仅列前端侧替换点）。
- 助手页全量业务问答覆盖。

---

## 1. 差距分析（任务书 vs 现状）

| 任务要求（摘自 V1.1） | 现状结论 | 差距 | 优先级 |
|----------------------|----------|------|--------|
| 首页保持结构；E/S/G 数据接入 | 壳与分流已就绪；`getDashboardKpis` + mock 兜底 | API 可用时 mock 数值仍可能漂移；需「API 优先 + 可见失败」收敛 | **P0** |
| 指标可点击下钻 | E01–E04/S02→工作台；S01/S03/S04/G→弹窗 | 主路径已通；个别弹窗字段未对齐任务书 | P1 |
| E01 工作台：监测点/异常/未闭环/风险；列表+详情；GIS | `E01WorkspacePanel` + GIS 联动，完成度高 | 督办写回、告警闭环回写未完；顶部口径文案与任务书「环保风险预警」命名可能不一致 | P1 |
| E02 工作台：弃土场/临时用地/表土/边坡等对象 | 现状为「未闭环环境问题」台账工作台（`E02WorkspacePanel`） | **对象语义与任务书/冻结「水保风险预警」错位**；水保对象更接近现状 E03 内容域 | **P0（口径确认）** |
| E03 工作台：生态敏感区/保护对象 | `E03WorkspacePanel` 同构工作台，完成度高 | 对象级追溯若后端未齐则只能问题台账；命名「生态保护事项」vs「生态保护管控」 | P1 |
| E04 文物工作台；不再展示碳排放；0 对象文案 | 文物工作台已接 API；碳已独立 | 空态仅「暂无文物保护对象」，缺「已完成文物调查」「风险状态正常」；GIS 文物层未接；遗留碳 Modal 仍在仓库 | **P0（文案）** / P1（GIS） |
| S01 弹窗：连续天数/事件/趋势/事故 | `S01SafetyProductionModal` + `/api/dashboard/kpi/S01`，完成度高 | 中断事件写回、与安全台账深度联动不足 | P2 |
| S02 工作台：重大/较大/一般 + GIS | `S02WorkspacePanel` 可用 | 「一般风险」分层与销号写操作；遗留 `S02SafetyRiskModal` 双轨 | P1 |
| S03 弹窗：工资达标率/纠纷数/闭环率 | `S03LaborDisputeModal` 中等 | 字段与台账对齐不足；首页 hint 多为「暂无评价数据」 | P1 |
| S04 弹窗：诉求数/处理中/已关闭/响应率 | `S04MassAppealModal` 中等 | 闭环写回、时限与风险面板打通不足 | P1 |
| G01：审批总数/完成/缺失/异常 | `G01ApprovalModal` | 统计卡与任务书四象限对齐需核对 API payload | P1 |
| G02：许可证总数/有效/临期/逾期；**修正 G02/G03 错绑** | 首页 G02 点开 `G03RectificationModal`（整改）；`G02LicenseModal` 未挂载 | **组件与接口错绑 = 任务书点名缺陷**；且首页文案「合规问题闭环」与任务书/冻结「许可及施工管控」不一致 | **P0** |
| G03：设计变更许可（变更数/审批/实施/异常） | 现状 G03 =「参建单位履约评价」+ `G03ContractorEvalModal` 诚实空态 | **口径三重冲突**：任务书/冻结 vs 现状 catalog vs 整改 Modal 命名 | **P0（产品裁定）** |
| G04：事项数/风险/未闭环 | `G04ComplianceModal` | 与任务书「内控廉洁」字段对齐；部分与许可缺口混计 | P1 |
| 综合风险：红黄蓝数量 + 列表（等级/领域/指标/对象/责任单位/状态）+ 点击跳转 | `ComplianceRiskPanel` 有红黄蓝语义与列表展示 | **无点击下钻 emit**；未稳定绑 `biz_risk_warning`；非任务书完整清单交互 | **P0** |
| GIS 定位（E01/E02/S02 等） | E01/E02/E03/S02 业务链已有；`openKpiFromBusinessLink` 仅 E02/E03/S02 | E04 文物无 GIS 层；E01 业务链入口弱于 E02 | P1 |
| 禁止硬编码指标；Mock≈API | 大量 `dashboard.mock` 兜底 | Demo 允许但需结构同构；逐步去掉静默假数冒充正式结论 | P1 |
| 碳足迹独立模块 | 右栏面板+专题弹窗已有；独立页未挂路由 | **符合冻结**；本计划不接线独立页 | —（保持） |
| 文物 0 对象演示文案（冻结+任务书） | 空态不完整 | 见上 E04 | **P0** |
| Workspace 填报/入库/审核 | 壳存在；智能入库为 Demo | 非任务书四阶段主线；仅作后续绑定备注 | P2 |

### 1.1 关键口径冲突（实施前必须裁定）

| # | 冲突 | 任务书 / 冻结 | 现状代码 | 建议 |
|---|------|---------------|----------|------|
| C1 | G02 业务语义 | 许可及施工管控（证照临期/逾期） | 首页标签「合规问题闭环」+ 打开整改 Modal | **按任务书改绑到 `G02LicenseModal` + G02 API**；整改类指标归属需产品确认（可能并入风险或 G04） |
| C2 | G03 业务语义 | 设计变更许可 | 「参建单位履约评价」空态 Modal | 产品二选一或分期；**不得在未确认前同时改名又改组件** |
| C3 | E01–E03 命名 | 环保风险预警 / 水保风险预警 / 生态保护管控 | 环境影响事件 / 未闭环环境问题 / 生态保护事项 | 文案是否回冻基线，还是保留「现场调研优化」名、仅补对象字段 |
| C4 | E02 对象域 | 水保四类对象 | 环境问题台账 | 确认是否「换皮」E02/E03 数据源，或仅改展示标签 |

---

## 2. 分阶段改造计划

阶段划分对齐任务书第十章，并吸收 GIS / 接口收敛为独立可验收切片。

### Phase A — 首页指标口径与文案对齐（任务书第一阶段）

**目标：** 首页 KPI 展示与任务书/冻结口径一致（在 C1–C4 裁定后落地）；数据走 API，失败可见。

**步骤：**

1. 产品确认 C1–C4（阻塞后续改 catalog）。
2. 更新 `kpi-catalog.ts` / `dashboard.mock.ts` 中与裁定一致的 label、caliber、source（**不改卡片布局**）。
3. 核对 `dashboard.store.ts`：`getDashboardKpis` / `getDashboardPanels` 成功路径覆盖 mock；失败保留空态或 `loadError`，禁止静默用过期 mock 冒充正式值（演示开关可另议）。
4. 确认 E04 首页 hint 在 0 对象时符合「调查完成 / 无对象 / 风险正常」。

**验收：**

- [ ] 12 项 KPI 名称与裁定后口径一致，E04 仍为文物、碳不在 E 组。
- [ ] 后端可用时，首页数值来自 `/api/dashboard/kpis`（或明确标注 Demo）。
- [ ] 布局 / 导航 / 主题无变更。

**风险：** 口径未裁定时改文案会造成二次返工。  
**依赖：** `/api/dashboard/kpis`、`/api/dashboard/panels`；G/E 指标计算与对象表。

---

### Phase B — E 组工作台巩固（任务书第二阶段，含 E04）

**目标：** E01–E04 工作台内容对齐任务书字段；E04 **巩固补齐**而非重做。

**步骤：**

1. **E01**：对照任务书顶部四指标与列表列；补详情中整改记录/关联资料展示（只读优先）；保持 GIS。
2. **E02 / E03**：按 C3/C4 裁定调整对象列表字段与筛选；保持工作台壳与 Esc/选中交互。
3. **E04**：
   - 巩固空态为三句：已完成文物调查；当前无文物保护对象；风险状态正常。
   - 摘要区补「文物调查状态」。
   - 隔离遗留：确保主路径永不打开 `E04CarbonEmissionModal`；`KpiDetailModal` 内旧 E04 碳壳标注废弃（可不删文件）。
4. 列表→详情→风险状态链路可追溯到业务对象 ID。

**验收：**

- [ ] E01–E04 均可从首页 KPI 打开右侧工作台。
- [ ] E04 无对象时文案满足任务书/冻结示例。
- [ ] E04 不再出现碳排放 UI。
- [ ] 工作台宽度仍为右栏 34%，无布局重做。

**风险：** E02/E03 数据源对调会牵动后端与 GIS feature 映射。  
**依赖：** `/api/environment/e01/*`、`e02/*`、`e03/*`、`e04/cultural-objects`；表 `biz_cultural_relic_object` 等。

---

### Phase C — S/G 二级弹窗对齐（任务书第三阶段）

**目标：** 弹窗模式指标统计卡与明细对齐任务书；**优先修复 G02/G03 错绑**。

**步骤：**

1. **P0**：`KpiDetailModal` 将 `G02` 改绑至 `G02LicenseModal`（或裁定后的正确组件）；修正其内部 `getDashboardKpiDetail('G02')`。
2. 按裁定处理 G03：设计变更 Modal（可能新建）或保留履约空态并改任务书验收表述（需 Codex/产品书面确认）。
3. S01：核对事故记录/趋势是否 API 全量。
4. S03/S04：补齐达标率、闭环率、处理中/已关闭等统计卡；明细行绑定对象 ID。
5. G01/G04：统计卡对齐任务书字段；空台账学 G03「不编造」。

**验收：**

- [ ] 点击 G02 看到许可临期/逾期类内容（若按任务书裁定），不再误开整改数据。
- [ ] S01/S03/S04/G01/G04 弹窗可打开，关键统计可见或诚实空态。
- [ ] 无新增一级导航、无布局破坏。

**风险：** G03 历史「履约评价」空态已被演示接受，回切「设计变更」需同步后端与话术。  
**依赖：** `/api/dashboard/kpi/G01`–`G04`、`S01`、`S03`、`S04`；许可/变更/劳务/诉求台账。

---

### Phase D — 红黄蓝风险与清单下钻（任务书第四阶段）

**目标：** 综合风险面板满足：红/黄/蓝数量 + 风险列表字段 + 点击跳转对应指标详情/工作台。

**步骤：**

1. 扩展 `ComplianceRiskPanel`：列表项可点击；通过 emit 交由 `DashboardPage` 调用现有 `openE0xWorkspace` / `handleKpiSelect`。
2. panels API / mock 的 `warningList` 结构对齐：等级、领域、指标、对象、责任单位、状态。
3. 前端不实现规则引擎；只消费 `biz_risk_warning` 投影结果。
4. 红黄蓝语义文案对齐冻结（红=立即处理，黄=重点关注，蓝=提醒）。

**验收：**

- [ ] 首页可见红/黄/蓝数量。
- [ ] 列表字段齐全（或缺字段时显式「—」）。
- [ ] 点击一条风险可打开对应 E/S/G 工作台或弹窗。
- [ ] 面板尺寸与 `PanelCard` 壳不变。

**风险：** 指标键缺失时跳转失败；需默认降级提示。  
**依赖：** `/api/dashboard/panels`（或专用 warnings API）；后端规则 → `biz_risk_warning`。

---

### Phase E — GIS 图层入口补齐

**目标：** 任务书要求的 GIS 定位在 E01/E02/S02（及裁定后的 E03/E04）可从地图进入业务对象。

**步骤：**

1. 扩展 `openKpiFromBusinessLink` 支持 `E01`、`E04`（若有图层）。
2. `GisOverviewCesiumPanel` / traffic-gis 图层配置：文物点位（只读展示 + 选中反传 `e04SelectedObjectId`）。
3. 不改首页 GIS 区域尺寸与 Cesium 壳。

**验收：**

- [ ] E01/E02/E03/S02 现有链路回归通过。
- [ ] E04 有对象时可选中地图点并打开工作台详情（无对象时不报错）。
- [ ] 无新增大屏模块。

**风险：** 文物缺坐标时仅列表可用。  
**依赖：** 空间字段 / GIS 图层配置；后端对象坐标。

---

### Phase F — 接口绑定与 Demo 去假数（任务书第九章收敛）

**目标：** Mock 与 API 同构；演示可开关；禁止页面散落硬编码业务结论。

**步骤：**

1. 梳理 `dashboard.mock.ts` 拆分建议（不必强行新建 `mock/eData` 物理目录若与现工程冲突——**优先在 `src/data/` 内按域拆分文件**，满足「结构一致」意图即可；若产品坚持任务书目录名，再评估别名导出）。
2. Workspace 智能入库：`esgSmartEntryDemo.ts` → 逐步切 `api.ts` 已有 `/api/workspace/ai/*` 方法。
3. 统一失败态：组件级 `error` / 空态，G03 式诚实空态为范例。
4. 文档化环境：`VITE_API_BASE`、Vite proxy → `:8765`。

**验收：**

- [ ] 关键业务数不在 `.vue` 模板字面量中作为正式 KPI。
- [ ] Mock 类型与 API 响应类型共用或兼容。
- [ ] `npm run check` / `npm run build` 在实施 PR 中通过（实施阶段，非本计划阶段）。

**风险：** 大拆 mock 易产生无关 diff；应按 Phase 切片提交。  
**依赖：** 后端 Demo 数据与真实接口并存策略。

---

## 3. 涉及文件清单（核心交付）

### 3.1 必改文件（按阶段）

#### Phase A — 首页口径

| 路径 | 改什么 |
|------|--------|
| `src/data/kpi-catalog.ts` | 按裁定更新 E/S/G 正式名称、口径、来源；E04 保持文物 |
| `src/data/dashboard.mock.ts` | KPI 文案/演示值与 catalog 一致；风险 mock 结构预留下钻键 |
| `src/stores/dashboard.store.ts` | KPI/panels 加载策略：API 优先、失败可见 |
| `src/components/kpi/KpiCard.vue` | 仅必要时支持 0 对象 hint/displayText（不改布局） |
| `src/components/kpi/TopKpiGroups.vue` / `KpiGroupPanel.vue` | 通常只读复用；若需传 catalog 元数据则小改 |

#### Phase B — E 组工作台

| 路径 | 改什么 |
|------|--------|
| `src/components/e01/E01WorkspacePanel.vue` | 顶部统计/列表列/详情块对齐任务书 |
| `src/components/e02/E02WorkspacePanel.vue` | 按 C4 调整对象域展示 |
| `src/components/e02/E02ClosureAnalysisPopover.vue` | 闭环分析文案与字段 |
| `src/components/e03/E03WorkspacePanel.vue` | 敏感区/保护对象展示 |
| `src/components/e03/E03ClosureAnalysisPopover.vue` | 同上 |
| `src/components/e04/E04CulturalRelicWorkspacePanel.vue` | **空态三句文案**、调查状态、摘要巩固 |
| `src/views/DashboardPage.vue` | E04 打开/选中/Esc；与面板事件对接（小改） |
| `src/types/e01*.ts` / `e02*` / `e03*` / `e04-cultural.ts` | 类型与 API 对齐 |
| `src/services/api.ts` | 仅当契约增字段时扩展 client（不改后端） |

#### Phase C — S/G 弹窗

| 路径 | 改什么 |
|------|--------|
| `src/components/modal/KpiDetailModal.vue` | **G02 分发改绑**；避免误用旧 E04 碳壳 |
| `src/components/modal/G02LicenseModal.vue` | 挂上主路径；统计卡对齐「总数/有效/临期/逾期」 |
| `src/components/modal/G03RectificationModal.vue` | 从 G02 解绑；或改用途（待裁定） |
| `src/components/modal/G03ContractorEvalModal.vue` | 若 G03 改设计变更则替换/新建；否则保持空态 |
| `src/components/modal/G01ApprovalModal.vue` | 四象限统计 |
| `src/components/modal/G04ComplianceModal.vue` | 事项/风险/未闭环 |
| `src/components/modal/S01SafetyProductionModal.vue` | 事故记录等补齐 |
| `src/components/modal/S03LaborDisputeModal.vue` | 达标率/纠纷/闭环率 |
| `src/components/modal/S04MassAppealModal.vue` | 数量/处理中/已关闭/响应率 |
| `src/components/s02/S02WorkspacePanel.vue` | 重大/较大/一般分层 |

#### Phase D — 风险

| 路径 | 改什么 |
|------|--------|
| `src/components/panels/ComplianceRiskPanel.vue` | 列表点击、字段展示、emit 下钻 |
| `src/views/DashboardPage.vue` | 接收下钻 → 打开对应工作台/弹窗 |
| `src/types/dashboard.ts` | `WarningListItem` 等类型补全 |
| `src/data/dashboard.mock.ts` | warning 列表 Demo 同构 |
| `src/stores/dashboard.store.ts` | panels 中 compliance/warnings 映射 |

#### Phase E — GIS

| 路径 | 改什么 |
|------|--------|
| `src/components/gis/GisOverviewCesiumPanel.vue` | E04/E01 业务链与选中同步 |
| `src/modules/traffic-gis-overview/**`（图层配置/业务链） | 文物层或 E01 链配置（最小改动） |
| `src/views/DashboardPage.vue` | `openKpiFromBusinessLink` 扩展 targetType |
| `src/config/gis.config.ts` | 仅开关/配置，不改布局 |

#### Phase F — 数据层

| 路径 | 改什么 |
|------|--------|
| `src/services/api.ts` | 契约注释与缺口方法 |
| `src/data/*.mock.ts` | 按域拆分或标注同构 |
| `src/services/esgSmartEntryDemo.ts` / `WorkspaceSmartEntry.vue` | Demo→API 切换点（P2） |

### 3.2 只读复用文件（禁止改布局/视觉）

| 路径 | 为何复用 | 禁止改什么 |
|------|----------|------------|
| `src/views/DashboardPage.vue` 布局模板与 scale 壳 | 正式驾驶舱 | 66/34 栅格、缩放逻辑大改 |
| `src/styles/layout.scss` / `tokens.scss` / `dashboard.scss` | 设计 token | 字号体系、主题色、栅格变量 |
| `src/components/layout/HeaderNav.vue` | 一级导航 | 增删主导航项、改平台信息架构 |
| `src/components/layout/PanelCard.vue` | 右栏壳 | 尺寸体系推倒重来 |
| `src/components/kpi/TopKpiGroups.vue` 等 | KPI 渲染范式 | 卡片栅格重设计 |
| `src/components/panels/CarbonBenefitPanel.vue` | 碳独立模块 | 并入 E 组、改 E04 |
| `src/components/modal/CarbonBenefitModal.vue` | 碳专题 | 当作 E04 |
| `src/components/charts/*` | ECharts 封装 | 无必要换库 |
| `src/modules/traffic-gis-overview/cesium/**` | Viewer 核心 | 大重构 Viewer |

### 3.3 建议新增文件

| 路径 | 职责 |
|------|------|
| `src/components/modal/G03DesignChangeModal.vue`（**仅当**裁定 G03=设计变更） | 设计变更许可弹窗 |
| `src/composables/useRiskDrilldown.ts`（可选） | 风险列表 → KPI 打开的适配器，避免 `DashboardPage` 膨胀 |
| `src/data/mock/eData.ts` 等（可选） | 若执行任务书 mock 目录建议；否则用 `dashboard.e.mock.ts` 命名亦可 |
| `src/types/risk-warning.ts`（可选） | 红黄蓝列表与下钻载荷类型 |

### 3.4 明确不碰 / 勿当现行基线

| 路径 | 原因 |
|------|------|
| `src/components/modal/E04CarbonEmissionModal.vue` | 遗留碳排放；禁止恢复主路径 |
| `src/views/CarbonPage.vue` + `src/components/carbon/*` 独立页接线 | 未挂路由；接线需解冻导航 |
| `src/views/MasterDashboardPage.vue` + `src/components/master/*` | 实验母版，勿替换正式首页 |
| `src/components/modal/S02SafetyRiskModal.vue` | 首页主路径已是工作台；除非统一内容，否则不优先改 |
| `KpiDetailModal` 内旧 E01–E03 通用大壳 | 主路径已走工作台；勿再激活为首页主交互 |
| `backup-20260717/**`、`交付_*实施包/**` | 历史包，不作为改造目标 |
| `_handoff/碳核算与月报独立页/**` 实施任务 | 碳/月报独立页非本 V1.1 四阶段主线 |
| 后端 `server/**` | 本计划前端焦点；仅列依赖 |

---

## 4. 接口绑定计划（前端侧 · 不实施）

| 指标/页面 | 现有前端 API（`src/services/api.ts`） | 缺口 | 建议契约（草案） |
|-----------|--------------------------------------|------|------------------|
| 首页 KPI 组 | `getDashboardKpis()` → `GET /api/dashboard/kpis` | 返回是否覆盖 12 项正式口径；失败时 mock 漂移 | `{ groups: KpiGroup[] }`，含 `key/label/value/unit/hint/displayText` |
| 首页 panels（风险/碳摘要/时序等） | `getDashboardPanels()` → `GET /api/dashboard/panels` | 风险列表缺下钻键（kpiKey/objectId） | `compliance[]` + `warnings[]`：`level,domain,kpiKey,objectId,objectName,unit,status` |
| S01 | `getDashboardKpiS01()` → `GET /api/dashboard/kpi/S01` | 事故记录完整性 | 保持专用结构 |
| S03/S04/G01/G02/G03/G04 详情 | `getDashboardKpiDetail(key)` → `GET /api/dashboard/kpi/{key}` | G02/G03 后端键与前端错绑同源；payload 字段与任务书统计卡不一致 | **G02 返回许可汇总**；G03 按裁定返回变更或履约；禁止混用 |
| E01 | `getE01Events` / `getE01EventDetail` / `getE01PointTrend` | 督办写 API 未接前端 | 写接口另立项；本阶段只读巩固 |
| E02 | `getE02Issues(scope?)` / detail | formal/demo scope 需文档化 | 保持 scope 查询参数 |
| E03 | `getE03Issues` / detail | 对象表 vs 问题表 | 响应含 `objectId` 可追溯 |
| E04 | `getE04CulturalObjects` / detail | 0 对象时 overview 需带调查状态、风险正常 | `overview: { objectCount, surveyStatus, measureRate, riskCount, status }` |
| S02 | `getS02Risks` / detail | 一般风险分层 | `level: major\|larger\|general` |
| 碳专题 | `getDashboardTopic('carbon')` | 独立页未用 | **保持独立**；勿挂 E04 |
| 月报 | `getMonthlyReportReadiness` / topic | 非本阶段主线 | 维持右栏 |
| 风险闭环写回 | 无统一前端方法 | 整改提交 API | `POST /api/risks/{id}/actions`（建议，待后端） |
| Workspace AI | `upload*` / `startParseFile` / … 已有 | SmartEntry 仍走 Demo | Phase F 切换 |

**原则：** 前端只消费契约；指标计算与红黄蓝规则在后端；页面禁止写死业务结论数。

---

## 5. 验收清单（对照任务书第十一章 + 分项）

### 5.1 任务书必须项

- [ ] 1. 首页可展示 ESG 状态（E/S/G KPI 可见）。
- [ ] 2. 指标可点击。
- [ ] 3. 页面可下钻（工作台或弹窗）。
- [ ] 4. 数据可追溯到业务对象（有 objectId/台账来源，或诚实空态）。
- [ ] 5. 风险可展示（红黄蓝数量 + 列表）。
- [ ] 6. 不破坏原有系统（布局/导航/主题/技术栈不变）。

### 5.2 冻结与专项

- [ ] E04 为文物保护管控；主路径无碳排放。
- [ ] 碳足迹仍为首页独立模块。
- [ ] E04 对象数为 0 时展示：已完成文物调查；当前无文物保护对象；风险状态正常。
- [ ] G02/G03 组件与接口错绑已按产品裁定修正。
- [ ] 未新增未经确认指标；未改一级导航。
- [ ] 综合风险条目可跳转对应指标详情。
- [ ] Mock 与 API 结构一致；无页面硬编码正式业务指标。

### 5.3 模式覆盖

- [ ] 工作台：E01、E02、E03、E04、S02。
- [ ] 弹窗：S01、S03、S04、G01、G02、G03、G04。
- [ ] Workspace 现有入口可用（不要求本轮做完真实入库）。

---

## 6. 风险与待确认项

### 6.1 实施前阻塞确认（给产品 / Codex）

1. **G 组最终口径**：执行任务书/冻结（G02 许可、G03 设计变更、G04 内控）还是保留现状「现场调研」命名（G02 合规问题闭环、G03 履约评价）？任务书已写「修正错绑」，但未写是否同步改 G03 业务定义。
2. **E01–E03 命名与 E02 对象域**：回冻基线（环保/水保/生态）还是保留现状文案与现网数据源？
3. **风险下钻**：点击后仅打开指标壳，还是必须定位到具体对象行？
4. **Demo 策略**：演示环境是否允许「明显 Demo 角标」以便彻底去掉静默假数？
5. **碳/月报独立页**：本轮是否明确继续不上导航？（建议：是）

### 6.2 技术风险

| 风险 | 影响 | 缓解 |
|------|------|------|
| G02/G03 历史命名债 | 改绑后演示话术与截图失效 | 先出对照表再改；同 PR 更新 mock |
| E02/E03 数据源对调 | GIS 与 API 大面积回归 | 未确认前只改文案不改接口 |
| panels 无 objectId | 风险无法深链 | 后端补字段；前端降级到仅开 KPI |
| E04 无坐标 | GIS 阶段无法演示文物点 | 列表工作台仍可验收 |
| 大 PR 混杂布局无关 diff | 审查失败 | 严格按 Phase 开 `trae/<issue>-*` 分支 |

### 6.3 文档与代码冲突摘要（计划层结论）

| 项 | 结论 |
|----|------|
| 任务书 E04=文物 vs 旧碳交付包 | **以任务书+冻结+现行代码为准**；旧包忽略 |
| 任务书禁止改布局 vs 内容增强 | **允许换数据与下钻内容，禁止重做壳** |
| 现状分析建议顺序 vs 任务书四阶段 | 一致；G02 错绑同为 P0 |
| 任务书 mock/ 目录 vs 现 `src/data` | 意图优先（同构）；物理路径可兼容现工程 |

---

## 文档修订记录

| 版本 | 日期 | 说明 |
|------|------|------|
| V1.1 | 2026-08-04 | 首版计划：对照任务书 V1.1 + 冻结基线 + 现状分析 + 仓库 spot-check；**不修改应用源码** |
