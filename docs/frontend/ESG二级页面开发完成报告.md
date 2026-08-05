# ESG 二级页面开发完成报告（V1.0）

**日期**：2026-08-05  
**范围**：E/S/G 二级模块框架 + 交互闭环 + Demo 数据展示（统一评审态，非单页深打磨）  
**约束遵守**：未改首页 12 KPI 定义 / DB / 正式 API 协议；未引入新 UI 框架；展示 Demo 与前端归一化允许。

---

## 1. 完成模块矩阵

| 模块 | 分类 | 状态 | 说明 |
|------|------|------|------|
| E01 环境监测与风险预警 | A | **DONE** | 沿用 V1.0/V1.1；未回归改动 |
| E02 环保问题整改 | A | **DONE（框架+Demo）** | 由 Phase B「水保对象」纠回环保问题整改；列表+地图弹窗 |
| E03 水保与复绿 | A | **DONE（框架+Demo）** | 由「生态对象」纠回水保与复绿；列表+地图弹窗 |
| S02 重大风险源管控 | A | **DONE（框架+Demo）** | 分类/重点切换/弹窗字段对齐；去掉重复 L2 弹窗 |
| S01 安全生产管理 | B | **DONE（框架+Demo）** | 统一 Class B 列表+五段详情壳 |
| S03 工资支付管理 | B | **DONE（框架+Demo）** | 标段/单位/支付/达标率；无个人敏感字段 |
| S04 群众诉求 | B | **DONE（框架+Demo）** | 事项/来源/状态/进展 + 五段详情 |
| G01 合规审批与许可 | B | **DONE（框架+Demo）** | 批复/许可/完成情况合并展示 |
| G02 重大风险专项方案 | B | **DONE（框架+Demo）** | **已脱离旧许可逻辑**；专项方案/审查/审批/文件 |
| G03 设计变更管理 | B | **DONE（框架+Demo）** | 变更项/审批/影响范围/时间 |
| G04 合规管理 | B | **DONE（框架+Demo）** | 合规管理天数/检查事项/整改通知/完成率；不展示「正常」 |

---

## 2. 页面入口

| 模块 | 入口 | 路由/视图 |
|------|------|-----------|
| E01/E02/E03/S02 | 首页对应 KPI 点击 → 右侧工作台 + 左 GIS | `/` `DashboardPage.vue`（无独立路由） |
| E04 | 首页 KPI → 文物工作台（既有，非本次 Class A 范围） | 同上 |
| S01/S03/S04/G01–G04 | 首页 KPI 点击 → `KpiDetailModal` → `ClassBMatterModal` | 同上 |
| G02 从 S02 | S02 地图弹窗「查看重大风险专项方案」→ 打开 G02 事项弹窗 | 同上 |
| Workspace 专项方案页 | `/workspace` 既有治理页（与首页 G02 弹窗并行存在） | `WorkspacePage` |

**未改**：首页 KPI 卡片文案/口径、KPI 数量定义。

---

## 3. 数据来源

| 模块 | 优先来源 | Demo/回退 |
|------|----------|-----------|
| E01 | `GET /api/environment/e01/events` 等（既有） | 既有 mock 链路 |
| E02 | `GET /api/environment/e02/issues`（有数据则归一化） | `src/data/e02-issues.mock.ts` |
| E03 | 复用 Phase B `GET /api/environment/e02/objects` **映射**为水保对象 | `src/data/e03-water.mock.ts` |
| S02 | `GET /api/social/s02/risks`（有数据则归一化） | `src/data/s02-risks.mock.ts` |
| Class B（S01/S03/S04/G01–G04） | 前端展示 Demo | `src/data/class-b-matters.mock.ts` |
| G02 联调补充 | Workspace 仍可调 `governance/special-plans*` | 首页弹窗当前以 Demo 台账为主 |

---

## 4. 使用的 API 调用

**Class A**

- `getE01Events` / `getE01PointTrend`（E01，未改契约）
- `getE02Issues` / `getE02IssueDetail`（E02 主路径；失败回退前端 Demo）
- `getE02Objects` / `getE02ObjectDetail`（E03 映射数据源；非正式新契约）
- `getE03WaterObjects` / `getE03WaterObjectDetail`（前端组装函数，**非新增后端路径**）
- `getS02Risks` / `getS02RiskDetail`

**Class B**

- 首页弹窗主体：`class-b-matters.mock`（展示 Demo）
- 仍可能触发：`getDashboardKpiDetail(kpiKey)`（Dashboard 打开弹窗前的既有拉取；不作为五段详情权威源）
- Workspace：`getSpecialPlans` 等（治理页，未改协议）

---

## 5. Class A 统一规则落实

| 规则 | E01 | E02 | E03 | S02 |
|------|-----|-----|-----|-----|
| 顶栏统计 + 左 GIS + 右列表 | ✓ | ✓ | ✓ | ✓ |
| 默认重点对象 | 风险点 | 未闭环问题 | isKey 水保对象 | 重大风险源 |
| 重点/全部切换 | ✓（风险/全部监测点） | ✓ | ✓ | ✓ |
| 业务分类筛选 | 空气/水质/噪声 | 环境污染/水保/生态/其他 | 弃土场/临时占地/表土剥离/复绿 | 重大源/危大/一般 |
| 详情仅地图弹窗 | ✓ | ✓ `E02MapSummaryCard` | ✓ `E03MapSummaryCard` | ✓ `S02MapSummaryCard` |
| 禁止右侧详情栏 | ✓ | ✓（已移除） | ✓（已移除） | ✓ |
| 禁止重复详情 | ✓ | ✓ | ✓ | ✓（已卸 L2 popover） |

**E02 弹窗完成时间**：仅展示接口/客户端回报的 `closedDate`，不前端推算。

---

## 6. Class B 统一结构落实

统一壳：`ClassBMatterModal.vue`

- 顶部统计
- 主业务列表（点击选中）
- 详情五段：**基础信息 / 业务状态 / 关键指标 / 关联资料 / 操作记录**

旧弹窗（`S01SafetyProductionModal`、`S03LaborDisputeModal`、`G02LicenseModal` 等）仍保留在仓库，**首页 KPI 入口已切换到 Class B 壳**，避免继续走旧许可/纠纷口径。

---

## 7. 关键文件路径

### Class A
- `frontend/src/components/e02/E02WorkspacePanel.vue`
- `frontend/src/components/e02/E02MapSummaryCard.vue`
- `frontend/src/components/e03/E03WorkspacePanel.vue`
- `frontend/src/components/e03/E03MapSummaryCard.vue`
- `frontend/src/components/s02/S02WorkspacePanel.vue`
- `frontend/src/components/s02/S02MapSummaryCard.vue`
- `frontend/src/types/e02.ts` / `e03.ts` / `s02.ts`
- `frontend/src/data/e02-issues.mock.ts` / `e03-water.mock.ts` / `s02-risks.mock.ts`
- `frontend/src/components/gis/GisOverviewCesiumPanel.vue`
- `frontend/src/views/DashboardPage.vue`
- `frontend/src/services/api.ts`（回退与映射，未改正式契约）

### Class B
- `frontend/src/components/modal/ClassBMatterModal.vue`
- `frontend/src/components/modal/KpiDetailModal.vue`（入口切换）
- `frontend/src/data/class-b-matters.mock.ts`
- `frontend/src/types/matter.ts`

### 本报告
- `docs/frontend/ESG二级页面开发完成报告.md`

---

## 8. 未完成 / 已知缺口（诚实清单）

1. **Class B 正式 API 深接**：五段详情当前以前端 Demo 为主，未把各模块正式明细接口字段完整灌入五段结构。  
2. **S01 连续天数口径弹窗**：旧 `S01SafetyProductionModal`（天数趋势/计数规则）被 Class B 事项壳替换；首页 KPI 天数不变，但二级页更偏「事件/隐患事项」，天数趋势图未并入新壳。  
3. **E03 面积/审批/影像**：当数据来自 E02 objects 映射时，面积等字段为展示补全/占位，正式水保对象 API 到位后需替换。  
4. **GIS 真实定位**：Demo 空间链多为标段级 `featureId`；无精确几何时定位能力依赖现有设计图层匹配。  
5. **G02 与 Workspace 双入口**：首页弹窗 Demo 与 Workspace 专项方案 CRUD 尚未完全同源合并。  
6. **E01 文案**：范围切换仍为「风险监测点/全部监测点」（行为符合重点/全部，文案未强行改成「重点对象」以免回归 V1.1）。  
7. **自动化测试**：仅跑通 `vue-tsc --noEmit`；未做全模块浏览器 E2E。  
8. **旧弹窗清理**：遗留 modal 文件未删除，避免大范围无关 diff；后续可归档。

---

## 9. 统一问题列表（跨模块）

| ID | 问题 | 影响 | 建议 |
|----|------|------|------|
| U1 | Class B Demo 与后端明细字段未对齐 | 评审可用，联调不足 | 按模块补 API adapter |
| U2 | E03 依赖 E02 objects 映射 | 数据语义易混淆 | 后端提供正式水保对象接口后再切主路径 |
| U3 | S01 天数叙事与事项列表拆分 | 二级页信息重心变化 | 新壳顶部并入 continuousDays API 摘要 |
| U4 | 空间定位精度 | 列表可点但 flyTo 可能偏弱 | 补业务空间对象主键 |
| U5 | G02 双通道 | 展示与录入不一致 | 首页弹窗改读 special-plans API |

---

## 10. 自检

- [x] Class A 四模块可达（首页 KPI）  
- [x] Class B 七模块可达（首页 KPI）  
- [x] 未改首页 KPI 定义  
- [x] `vue-tsc --noEmit` 通过  
- [x] 完成报告落盘  

**结论**：V1.0 二级页面「框架 + 交互闭环 + Demo 展示」目标已达成，可供统一评审；深度业务联调与单页打磨列入缺口清单。
