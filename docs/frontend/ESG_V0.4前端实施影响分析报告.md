# ESG V0.4 前端实施影响分析报告

| 项 | 内容 |
|---|---|
| 文档版本 | V1.0 |
| 日期 | 2026-08-05 |
| 分析性质 | **只读分析**；未修改任何前端代码 / 首页 / KPI / 主题样式 / API |
| 前置状态 | V0.4 数据库迁移已完成；V0.4 API 已开发并通过测试 |
| 当前阶段 | 前端实施准备（本报告完成后等待下一步开发指令） |
| 基线 | ESG Demo V0.3 首页一级指标业务事实校正版（首页 KPI 继续冻结） |
| 前端工作根 | `C:\ESG_Project\frontend` |

---

## 0. 结论摘要

1. 前端仍是 **领导层首页驾驶舱 + 工作台 + 助手 + GIS 预览** 四路由结构；V0.4 治理类新 API **尚未被前端引用**。
2. **G04 治理整改**：首页已有 `G04ComplianceModal`（读 `/api/dashboard/kpi/G04`），但与 V0.4 `/api/governance/rectification-tasks` **不是同一条链路**；整改完成日期填报能力目前无页面承载。
3. **专项方案审批**：无路由、无页面、无组件、无 `services/api.ts` 封装；需新增承载，且禁止物理删除 UI。
4. **S03 工资支付**：**已有页面承载**——首页 KPI 弹窗 `S03LaborDisputeModal`；但当前内容以劳务纠纷明细为主，尚未对接 `biz_worker_payment_summary` 周期汇总事实。首页 KPI 口径本次分析阶段保持冻结，不得改首页。
5. 实施建议：在**不改首页布局/KPI/主题样式**前提下，优先新增治理子能力（工作台 Tab 或独立 Hash 路由），通过新增 API 封装接入；首页现有弹窗仅作只读入口或后续单独评审。

---

## 1. 当前前端结构确认

### 1.1 路由（`src/router/index.ts`，Hash History）

| 路径 | name | 视图组件 | 用途 |
|---|---|---|---|
| `/` | `dashboard` | `views/DashboardPage.vue` | 领导层首页驾驶舱（主入口） |
| `/assistant` | `assistant` | `views/AssistantPage.vue` | ESG 智能助手 |
| `/workspace` | `workspace` | `views/WorkspacePage.vue` | ESG 工作台（资料上传/任务/审核） |
| `/gis-preview` | `gis-preview` | `views/GisPreviewPage.vue` | Cesium GIS 预览 |

未挂路由但仍存在的视图：

| 文件 | 状态 |
|---|---|
| `views/CarbonPage.vue` | 未注册 |
| `views/MasterDashboardPage.vue` | 未注册 |

工作台内部 Tab（query `?t=`，非独立路由）：`workspace` / `tasks` / `smart-upload` / `review` / `documents`。

### 1.2 页面与首页交互形态

**首页 `DashboardPage.vue` KPI 点击分流：**

| KPI | 交互形态 | 主要组件 |
|---|---|---|
| E01 / E02 / E03 / E04 | 右侧工作台面板 | `E01/E02/E03/E04*WorkspacePanel` |
| S02 | 右侧工作台面板 | `S02WorkspacePanel` |
| S01 / S03 / S04 / G01 / G02 / G03 / G04 | 详情弹窗 | `KpiDetailModal` → 各专用 Modal |
| 碳/月报专题 | 弹窗 | `CarbonBenefitModal` / `MonthlyReportModal` |

**顶栏导航**由 `HeaderNav` + Pinia `dashboard.store` 的 `navs` 驱动（驾驶舱 / 工作台 / 助手等），不新增路由不会自动出现导航项。

### 1.3 组件分层（与 V0.4 相关）

| 目录 | 与 V0.4 相关性 |
|---|---|
| `components/kpi/` | 首页 KPI 卡；**本次禁止改首页 KPI** |
| `components/modal/` | S03/G01–G04 等弹窗；可复用列表/详情交互模式 |
| `components/e01`–`e04`、`s02` | 右侧工作台面板模式；G04/专项方案可参考，但不可复用其业务 API |
| `components/workspace/` | 上传/任务/审核；文件关联可复用上传能力 |
| `components/panels/`、`gis/`、`charts/` | 首页面板/GIS/图表；本次不改主题与首页布局 |
| `components/master/`、`carbon/` | 未挂路由或专题相关，非 V0.4 首批必改 |

与 V0.4 直接相关的现有弹窗：

| 组件 | 当前数据接口 | 业务对象 |
|---|---|---|
| `G04ComplianceModal.vue` | `GET /api/dashboard/kpi/G04` | 内控廉洁问题清单（首页详情） |
| `S03LaborDisputeModal.vue` | `GET /api/dashboard/kpi/S03` | 劳务纠纷/工资相关纠纷明细 |
| `G01ApprovalModal.vue` | `GET /api/dashboard/kpi/G01` | 合规审批事项 |
| `G02LicenseModal.vue` | `GET /api/dashboard/kpi/G02` | 许可及施工管控 |
| `G03DesignChangeModal.vue` / `G03RectificationModal.vue` | G03 KPI 详情 | 设计变更（含历史整改弹窗组件，**不是** V0.4 `rectification-tasks` API） |
| `S02WorkspacePanel.vue` | `/api/social/s02/risks` | 安全风险点（专项方案的风险源关联候选） |

### 1.4 API 调用方式

| 项 | 现状 |
|---|---|
| 封装文件 | `src/services/api.ts` |
| 基址 | `import.meta.env.VITE_API_BASE \|\| http://127.0.0.1:8765` |
| 传输 | 主要为 `fetch`（`apiGet` / `apiPost`）；axios 在依赖中但首页主链路未作为统一层 |
| 开发代理 | `vite.config.ts`：`/api` → `127.0.0.1:8765` |
| 状态引导 | `stores/dashboard.store.ts`：`bootstrapHome()` → KPIs / panels / ESG home |
| PATCH | **前端无通用 `apiPatch`**；V0.4 整改/专项方案更新需要新增 |
| V0.4 治理 API | **`api.ts` 中无** `rectification-tasks` / `special-plans` 任何引用 |

首页 KPI 相关调用（保持不动）：

- `GET /api/dashboard/kpis`
- `GET /api/dashboard/risk-warnings`
- `GET /api/dashboard/panels`
- `GET /api/dashboard/kpi/{key}`

后端已具备、前端未接的 V0.4 API：

| 方法 | 路径 | 前端状态 |
|---|---|---|
| GET | `/api/governance/rectification-tasks` | 未封装、未调用 |
| GET | `/api/governance/rectification-tasks/{id}` | 未封装、未调用 |
| PATCH | `/api/governance/rectification-tasks/{id}` | 未封装、未调用 |
| GET | `/api/governance/special-plans` | 未封装、未调用 |
| GET | `/api/governance/special-plans/{id}` | 未封装、未调用 |
| POST | `/api/governance/special-plans` | 未封装、未调用 |
| PATCH | `/api/governance/special-plans/{id}` | 未封装、未调用 |
| DELETE | `/api/governance/special-plans/{id}` | 后端禁止；前端也不得做删除按钮 |

---

## 2. V0.4 新增功能映射

### 2.1 G04 治理整改（`e_rectification_task` / rectification-tasks API）

#### 业务目标（相对现有前端）

- V0.4 重点是：**整改任务查询 + 甲方填报完成日期/填报人**（`rectificationCompletedDate` / `rectificationCompletedBy`）。
- 禁止：自动填完成时间；`closed_at` 映射为完成日期。
- 现有首页 G04 弹窗展示的是 **内控问题 KPI 详情**，不是治理整改任务台账。

#### 页面位置建议

| 方案 | 位置 | 是否改首页 | 推荐度 |
|---|---|---|---|
| A. 工作台新 Tab | `/workspace?t=rectification` 或治理子页 | 否 | **推荐**（不碰首页 KPI） |
| B. 独立 Hash 路由 | 如 `/governance/rectification-tasks` | 否（仅加路由/导航项需确认） | 可选 |
| C. 扩展 `G04ComplianceModal` | 首页 G04 弹窗内嵌整改任务 | 易触及首页交互与 KPI 详情语义 | **不推荐作为首步**（边界风险高） |

**结论：** 首期页面位置放在 **工作台治理能力** 或 **独立治理路由**，不要改首页 KPI 卡与 G04 首页口径。

#### 路由

| 项 | 建议 |
|---|---|
| 现有可复用路由 | `/workspace`（扩展内部 Tab，不必立刻改 `router/index.ts`） |
| 若需深链 | 新增 `name: governance-rectification`，path 如 `/governance/rectification`（待开发指令确认） |
| 禁止 | 修改 `/` 首页路由行为来承载填报 |

#### 组件复用

| 可复用 | 复用点 | 不可直接复用 |
|---|---|---|
| `G04ComplianceModal` | 列表+筛选+详情侧栏交互模式、加载/空态 | 其数据源与字段模型（KPI G04 ≠ rectification-tasks） |
| `E01WorkspacePanel` 整改轮次区块 | “待甲方填报”空值展示思路 | E01 领域 API |
| `WorkspaceTasks` / `TaskModal` | 工作台列表/办理壳 | 上传任务模型 |
| `G03RectificationModal` | 仅 UI 表格经验 | 名称含 Rectification，但绑定 G03/KPI，**不是** V0.4 API |

建议新建（实施阶段，非本报告修改）：

- `services`：`getRectificationTasks` / `getRectificationTask` / `patchRectificationTask`（需 `apiPatch`）
- `components/governance/`：列表页 + 完成日期填报表单（仅两字段可写）

#### 与首页 G04 的边界

| 对象 | 现状 | V0.4 前端实施 |
|---|---|---|
| 首页 G04 KPI 卡 | `kpi-catalog`：内控与廉洁 | **冻结，不改** |
| `G04ComplianceModal` | `/api/dashboard/kpi/G04` | 可保持只读；是否展示闭环字段另开评审 |
| 整改任务台账 | 无 | 新页面 + governance API |

---

### 2.2 专项方案审批（`special_plan_approval` / special-plans API）

#### 业务目标

- 查询 / 新增 / 修改审批状态、审批信息、文件关联。
- 属于风险管控专项方案 + 审批事实 + 合规证据链。
- **禁止物理删除**（无 DELETE UI、无删除确认框）。

#### 页面位置建议

| 方案 | 位置 | 说明 |
|---|---|---|
| A. 工作台治理 Tab | `/workspace` 下「专项方案」 | 与整改任务同层，便于资料上传关联 |
| B. 独立路由 | `/governance/special-plans` | 列表+详情+编辑表单 |
| C. 挂在 S02 风险工作台 | `S02WorkspacePanel` 内嵌 | 利于按 `riskPointId` 关联，但扩大 S 组面板范围，需单独确认 |
| D. 挂在 G01/G02 弹窗 | 首页弹窗 | **不推荐**：易改首页 G 组详情语义 |

**结论：** 推荐 **独立治理列表页（工作台或新路由）**；风险点下拉数据可只读复用 S02 风险列表 API。

#### 路由

| 项 | 建议 |
|---|---|
| 新建路由（可选） | `/governance/special-plans`、`/governance/special-plans/:id`（或 query 详情） |
| 或工作台 Tab | `/workspace?t=special-plans` |
| 导航 | `HeaderNav` / 工作台 `WorkspaceNav` 增加入口前需产品确认文案；**不改首页 KPI 区** |

#### 组件

| 现状 | 结论 |
|---|---|
| 专用组件 | **无** |
| 可参考 | `G01ApprovalModal`（审批列表）、`G02LicenseModal`（许可/文件感）、工作台上传组件 |
| 文件关联 | 复用既有 `POST /api/workspace/files/upload`，页面只保存 `approvalFileId`；**不改上传接口** |
| 删除 | UI 层明确不提供删除；作废仅通过 `approvalStatus` PATCH |

建议新建：

- API 封装：list / detail / create / patch（无 delete）
- 页面：列表筛选（projectId、riskPointId、approvalStatus、riskLevel）
- 表单：新增必填字段与 PATCH 允许字段对齐 API 实施说明
- 详情：展示 `approvalFile` 元数据；缺失时显示空，不删业务行

#### 与 G01/G02 首页的边界

- G01/G02 首页弹窗继续走 `/api/dashboard/kpi/G01|G02`。
- 专项方案是 V0.4 **第三类审批事实**，不应用前端硬塞进首页 KPI 分子分母（KPI 合并属另案，本阶段禁止改首页 KPI）。

---

### 2.3 S03 工资支付

#### 是否已有页面承载？

**有。**

| 承载点 | 路径/组件 | 说明 |
|---|---|---|
| 首页 KPI 卡 | `TopKpiGroups` → S03 | 目录名：农民工权益保障；单位 `%`（`kpi-catalog.ts`） |
| 详情弹窗 | `S03LaborDisputeModal.vue` | 经 `KpiDetailModal` 在 `detail.key === 'S03'` 时打开 |
| 数据接口 | `getDashboardKpiDetail('S03')` → `GET /api/dashboard/kpi/S03` | 后端当前以**农民工工资类劳务纠纷**明细为主（非独立支付汇总 API） |

#### 与 V0.4 工资支付事实的差距

| 维度 | 现状前端 | V0.4 数据/业务方向 |
|---|---|---|
| 主展示 | 纠纷台账列表、人数/金额摘要 | `biz_worker_payment_summary` 周期汇总、按时发放率 |
| 页面 | 仅首页弹窗 | 弹窗可承载只读扩展，但 **改首页 KPI 名称/口径需单独确认** |
| 独立路由 | 无 | 非必须；若仅核对汇总，可后续加工作台只读页 |
| 敏感信息 | 弹窗含涉及金额等展示 | V0.4 要求不采集个人姓名/工资明细；前端扩展时需遵守 |

#### 实施影响判断（本阶段）

| 动作 | 是否允许（按本任务禁令） |
|---|---|
| 修改首页 S03 卡文案/单位/口径 | **禁止** |
| 修改主题样式 | **禁止** |
| 在现有 `S03LaborDisputeModal` 增加支付汇总只读区块 | 属开发阶段评审项；可能触及首页弹窗，需单独批准 |
| 新建工作台「工资支付汇总」只读页对接未来 API | 不改首页 KPI，风险较低 |
| 期待前端直接改 KPI key 或首页 12 项结构 | **禁止** |

**结论：** S03 **已有首页弹窗承载**；V0.4 工资支付周期事实尚未有专用前端页/API 封装。首页展示口径冻结期间，支付汇总能力建议作为**非首页**只读能力规划，或待 KPI 口径变更单批准后再改弹窗。

---

## 3. 影响矩阵（实施准备）

| 功能 | 改首页 | 改 KPI | 改主题样式 | 新路由/Tab | 新组件 | 新 API 封装 | 复用重点 |
|---|---|---|---|---|---|---|---|
| G04 治理整改台账/填报 | 否 | 否 | 否 | 建议是 | 是 | 是（含 PATCH） | 工作台壳、G04 弹窗交互模式 |
| 专项方案审批 | 否 | 否 | 否 | 建议是 | 是 | 是（GET/POST/PATCH） | 上传接口、G01/G02 列表模式、S02 风险点 |
| S03 工资支付 | 否（冻结） | 否（冻结） | 否 | 可选 | 可选 | 视后端是否新增汇总 API | 现有 `S03LaborDisputeModal` |

---

## 4. 前端缺口清单（供下一步开发任务拆分）

### 4.1 必须新建（相对 V0.4 已通 API）

1. `apiPatch`（或等价 PATCH 封装）及错误码处理（400/404/405/409/422）。
2. 整改任务：列表 / 详情 / 完成日期与填报人编辑（仅两字段）。
3. 专项方案：列表 / 详情 / 新增 / 编辑；无删除；文件关联走既有上传。
4. 治理入口（工作台 Tab 或新路由 + 导航文案确认）。

### 4.2 明确不做（本准备阶段 / 冻结边界）

1. 不修改首页布局、KPI 卡、12 项口径、主题样式。
2. 不修改 `/api/dashboard/kpis` 调用契约与 `kpi-catalog` 冻结文案（除非另发 KPI 变更单）。
3. 不修改文件上传接口。
4. 不为专项方案做物理删除。
5. 不把 `closed_at` 或当前日期写入整改完成日期。

### 4.3 待产品/业务确认后再做

1. G04 首页弹窗是否只读展示闭环摘要，还是与整改台账完全分离。
2. 专项方案入口挂在工作台、独立路由，还是 S02 风险下钻。
3. S03 支付汇总是否进入现有弹窗，或新建非首页页；以及是否批准首页口径从“纠纷项”叙事切到“按时发放率”叙事。
4. `HeaderNav` 是否增加「治理」导航项。

---

## 5. 建议实施顺序（等待指令后执行）

```text
1) services/api.ts：治理 API + apiPatch（不碰 dashboard KPI API）
2) 治理整改列表/填报页（工作台或新路由）
3) 专项方案列表/表单页（含文件关联，无删除）
4) 导航入口与联调
5) 回归：首页 12 KPI、主题、上传接口零回归
```

S03 工资支付汇总：**排在 KPI 口径变更确认之后**，或作为非首页只读页并行，避免误改首页。

---

## 6. 回归保护要求（开发阶段执行）

| 检查项 | 期望 |
|---|---|
| 首页 `/#/` 布局与样式 | 与 V0.3 一致 |
| 12 项 KPI 名称/单位/口径 | 不变 |
| `GET /api/dashboard/kpis` 前端调用 | 不变 |
| 文件上传 | 行为不变 |
| 专项方案 DELETE | 前端无入口；后端 405 |
| 整改 PATCH | 仅两字段；空完成日期展示“待甲方填报” |

---

## 7. 状态

| 项 | 状态 |
|---|---|
| 本报告 | 已完成（只读） |
| 前端代码 | **未修改** |
| 下一步 | **等待开发指令**后再实施治理页/API 封装 |

---

*分析依据：`frontend/src/router`、`views`、`components/modal`、`services/api.ts`、`stores/dashboard.store.ts`；后端已存在的 `/api/governance/*`；`docs/api/ESG_V0.4_API实施说明.md` 与 V0.4 业务方案中的前端影响条款。未执行代码变更。*
