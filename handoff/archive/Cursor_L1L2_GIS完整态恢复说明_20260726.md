# Cursor · L1/L2 + GIS 完整态恢复说明（2026-07-26）

| 项 | 内容 |
| --- | --- |
| **日期** | 2026-07-26 |
| **执行方** | Cursor |
| **分支** | `trae/workspace-nav-s02s03`（仅工作区恢复，**未提交**） |
| **恢复来源** | `git stash@{0}`（`WIP on codex/3-full-stack-mysql-update: 052112a`） |
| **未覆盖** | 未 tracked 的 `src/components/e01|e02|e03|s02/*` 面板与类型（磁盘上仍在，已与 Dashboard 接线） |

## 道歉与根因

上一轮「首页回归」误用 `codex/3-full-stack-mysql-update` **瘦壳**作为对照基线：该 tip 只有 Cesium 开关级 GIS 壳，**没有** E01/E02/E03/S02 工作台 L1/L2 接线，也把已落地的富化 GIS / 模态从工作树盖成瘦实现。

正确完整态实际在 **stash**（以及磁盘未提交的 e01/e02/e03/s02 组件），不在 `codex/3` tip，也不在当前 `main` tip。

## 本轮恢复动作

1. 从 `stash@{0}` checkout 回完整产品文件（含 Dashboard L1/L2 接线、富化 `GisOverviewCesiumPanel`、`TrafficGisOverview`/`MapChrome`、E04/S01–S04/G01–G04 模态、后端 `mysql_api`/`app.py` 等）。
2. 保留磁盘上未跟踪的 L1/L2 组件：`E01/E02/E03/S02 WorkspacePanel` + Closure popovers + MapSummaryCard。
3. 安全回补顶栏第三项「数据填报」：`dashboard.mock` nav + Dashboard/Assistant `handleNavClick` → `/workspace`。
4. 回补 S03 展示映射（调查中→核查中；协调中→协商化解中）到 `S03LaborDisputeModal`。
5. 保留 Trae Workspace 壳（`WorkspacePage` / `WorkspaceNav` / `WorkspaceHome` 等本轮未从 stash 覆盖）。

## 关键文件对照（恢复前 → 恢复后）

| 文件 | 错误瘦壳 | stash 完整态 |
| --- | --- | --- |
| `src/views/DashboardPage.vue` | ~209 行，无 workspace panels | ~728 行，含 E01/E02/E03/S02 |
| `src/components/gis/GisOverviewCesiumPanel.vue` | ~32 行薄壳 | ~723 行 + E01/S02 摘要卡 + L2 popovers |
| `MapChrome.vue` / `TrafficGisOverview.vue` | 被盖瘦 | 标段 / 环境监测点 / 安全风险点 |
| `E04` / `S02–S04` / `G01–G04` 模态 | 缺失 | 已恢复 |
| `server/mysql_api.py` | ~3k 行瘦版 | ~7k 行完整 API |

## 验收方式（请用户手测）

1. `/#/`：Cesium GIS；MapChrome 可见 **标段 / 环境监测点 / 安全风险点**。
2. 顶栏：**工作台首页 / ESG智能助手 / 数据填报**。
3. 点击 KPI **E01 / E02 / E03 / S02** → 进入右侧工作台 L1；地图点选可出 L2 闭环分析弹层。
4. E04 / S01 / S03–G04 仍走对应专题/明细模态。
5. 顶栏「数据填报」进 Workspace，无双顶栏。

## 未做

- 未 `git commit`、未 push、未 force-push。
- `npm run check`：**已通过**（`vue-tsc -b` exit 0，本轮恢复后）。

## 二次补齐（同轮）

因首次只 checkout 了 stash diff 列表，部分「磁盘已瘦、但 stash tree 仍完整」的同伴文件未带上，导致 `vue-tsc` 报错。已追加从 `stash@{0}` 恢复：

- `CoordinateAdapter.ts`、`BusinessLinksPanel.vue`、`FeatureCard.vue`、`basemaps.config.ts`
- `MonthlyReportModal.vue`、Panel/Master 相关、月报后端模块等
- Workspace 壳（`WorkspacePage` / `WorkspaceNav` / `WorkspaceHome`）保留 Trae 改动，未用 stash 覆盖
- `TaskStatus` 补回 `'审核退回'` 以兼容现有 Workspace UI 字符串
