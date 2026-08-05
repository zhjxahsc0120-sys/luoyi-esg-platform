# 罗宜高速 ESG 领导层首页专题与 KPI 入库扩展设计 V1.2

更新时间：2026-07-16

## 1. 本阶段目标

把领导层首页剩余内容从纯 `dashboard_payload.json` 原型数据，推进到 MySQL 可管理数据层，同时保持前端接口字段不变。

本阶段覆盖：

- E01-E04、S02-S04、G01-G04 共 11 个 KPI 通用详情弹窗；
- 合规保障与风险防控成效首页面板；
- 碳足迹与低碳增益专题弹窗及首页面板；
- 月报准备与输出专题弹窗及首页面板；
- 首页 GIS 点位、建设时间线、敏感区等组合数据。

S01「连续安全生产天数」已走专属数据库结构，不纳入本次快照扩展。

## 2. 设计原则

本阶段采用“两层结构”：

| 层级 | 作用 | 当前状态 |
| --- | --- | --- |
| 业务明细层 | 环保、安全、合规、碳、月报等真实台账 | V0.1 已建部分表，数据还不完整 |
| 页面快照层 | 直接支撑当前前端展示结构 | V1.2 已落库 |

这样做有三个好处：

1. 不破坏现有前端页面和 Trae 样式工作；
2. 后端接口从 MySQL 读取，不再只依赖本地 JSON；
3. 后续可以逐项把快照数据替换为业务明细表实时聚合。

## 3. 新增 MySQL 表

| 表名 | 用途 | 当前记录数 |
| --- | --- | --- |
| `dashboard_kpi_detail_snapshot` | 存 11 项 KPI 弹窗完整 JSON 结构 | 11 |
| `dashboard_topic_snapshot` | 存碳足迹、月报两个专题弹窗完整 JSON 结构 | 2 |
| `dashboard_panel_snapshot` | 存首页右侧面板、GIS、时间线组合 JSON | 1 |

建表脚本：

`server/mysql_build_v0.2_dashboard/01_dashboard_snapshot_extension.sql`

导入脚本：

`server/seed_dashboard_snapshots_v0_2.py`

## 4. API 读取策略

| 接口 | 当前读取策略 |
| --- | --- |
| `GET /api/dashboard/kpi/{code}` | MySQL `dashboard_kpi_detail_snapshot` 优先，失败 fallback 到 `dashboard_payload.json` |
| `GET /api/dashboard/topics/carbon` | MySQL `dashboard_topic_snapshot` 优先，失败 fallback 到 JSON |
| `GET /api/dashboard/topics/monthly-report` | MySQL `dashboard_topic_snapshot` 优先，失败 fallback 到 JSON |
| `GET /api/dashboard/panels` | MySQL `dashboard_panel_snapshot` 优先，失败 fallback 到 JSON |

前端无需改字段。

其中碳足迹首页面板同时保留两个字段：

- `carbon.reductions`：兼容当前前端 `CarbonBenefitPanel.vue`；
- `carbon.measures`：作为后续“主要低碳措施”语义字段预留。

## 5. 后续从快照转实时聚合的建议顺序

### 第一优先级：合规类

| 模块 | 当前快照 | 后续明细表 |
| --- | --- | --- |
| G02 临期及逾期许可 | `dashboard_kpi_detail_snapshot` | `permit_record` |
| G03 未关闭整改事项 | `dashboard_kpi_detail_snapshot` | `rectification_record` |
| G01 未完成合规手续 | `dashboard_kpi_detail_snapshot` | `compliance_procedure` |
| G04 待补齐合规资料 | `dashboard_kpi_detail_snapshot` | `compliance_material_gap` |

原因：字段边界清晰，最容易从台账直接聚合。

### 第二优先级：环境与安全类

| 模块 | 当前快照 | 后续明细表 |
| --- | --- | --- |
| E01 环境监测超标项次 | `dashboard_kpi_detail_snapshot` | `env_monitoring_record` |
| E02 未闭环环保问题 | `dashboard_kpi_detail_snapshot` | `env_issue_record` |
| S02 较大及以上安全风险点 | `dashboard_kpi_detail_snapshot` | `safety_risk_point` |
| S03 劳务纠纷 | `dashboard_kpi_detail_snapshot` | `labor_dispute_record` |
| S04 群众诉求 | `dashboard_kpi_detail_snapshot` | `appeal_record` |

### 第三优先级：碳与月报专题

| 模块 | 当前快照 | 后续明细表 |
| --- | --- | --- |
| 碳足迹与低碳增益 | `dashboard_topic_snapshot` | `carbon_emission_activity`、`carbon_material_usage`、后续新增 `low_carbon_measure` |
| 月报准备与输出 | `dashboard_topic_snapshot` | 后续新增 `monthly_report_chapter`、`monthly_report_missing_item`、`monthly_report_status_chain` |

## 6. 给 Trae / 前端样式同事的边界

可以改：

- 弹窗样式；
- 字号、间距、颜色、图表布局；
- 面板视觉层级；
- tab 样式；
- 空状态样式。

不要改：

- `src/services/api.ts` 中 dashboard API 方法；
- `src/views/DashboardPage.vue` 中 `handleKpiSelect`、`handleTopicSelect`；
- `src/stores/dashboard.store.ts` 中 `loadPanels()`；
- `src/components/modal/KpiDetailModal.vue` 中 `topicData` computed 映射。

如果要重构组件，必须保持：

- `KpiDetailConfig` 字段兼容；
- `topicData` 字段兼容；
- `/api/dashboard/panels` 返回结构兼容。

## 7. 本轮验证命令

```powershell
$env:PYTHONIOENCODING='utf-8'
$py='C:\Users\TB\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'

& $py server\seed_dashboard_snapshots_v0_2.py
& $py server\dashboard_mysql_snapshot_test.py
& $py server\dashboard_acceptance_test.py
& $py server\mysql_smoke_test.py
& $py server\smoke_test.py
& $py server\workspace_acceptance_test.py
& $py server\review_action_flow_test.py
& 'C:\Program Files\nodejs\npm.cmd' run check
& 'C:\Program Files\nodejs\npm.cmd' run build
```

## 8. 本轮验收结果

已通过：

- MySQL 快照导入；
- 领导层首页 MySQL 快照验收；
- 领导层首页 API 验收；
- MySQL 冒烟测试；
- 后端 API 冒烟测试；
- 工作台只读验收；
- 审核处理写闭环；
- `npm run check`；
- `npm run build`。

当前结论：

领导层首页剩余 KPI 弹窗、合规保障、碳足迹与低碳增益、月报准备与输出，已经从“仅 JSON 原型数据”推进到“MySQL 快照支撑 + JSON fallback”的可联调状态。

## 9. V0.3 补充：G01-G04 合规类已改为业务明细表聚合

在 V0.2 快照层基础上，已优先把 G 组 4 个合规类 KPI 从快照读取推进到业务明细表聚合。

| KPI | 当前接口数据来源 | 明细行数 | 关键口径 |
| --- | --- | ---: | --- |
| G01 当前未完成法定报批报建 | `compliance_procedure` | 5 | 未完成 5、本月新增 1、本月完成 2、逾期未办 1 |
| G02 当前临期及逾期许可事项数 | `permit_record` | 5 | 临期 4、逾期 1、30日内到期 4、30日以上 0 |
| G03 当前未关闭整改事项数 | `rectification_record` | 6 | 未关闭 6、本月新增 2、本月关闭 3、逾期未关闭 2 |
| G04 当前待补齐合规资料项数 | `compliance_material_gap` | 4 | 待补齐 4、本月需提交 3、逾期未提交 1 |

新增脚本：

- `server/seed_governance_detail_v0_3.py`
- `server/governance_kpi_mysql_test.py`

说明：

- G01-G04 接口路径未变，仍然是 `GET /api/dashboard/kpi/{code}`；
- 前端字段未变，仍返回 `KpiDetailConfig`；
- 若业务表为空或 MySQL 不可用，仍可 fallback 到快照层；
- G02 已按前期验收口径调整为：已逾期 1、7日内 1、8-15日 1、16-30日 2、30日以上 0。

V0.3 验收命令：

```powershell
$env:PYTHONIOENCODING='utf-8'
$py='C:\Users\TB\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'

& $py server\seed_governance_detail_v0_3.py
& $py server\governance_kpi_mysql_test.py
& $py server\dashboard_acceptance_test.py
& 'C:\Program Files\nodejs\npm.cmd' run check
& 'C:\Program Files\nodejs\npm.cmd' run build
```

## 10. V0.4 补充：E01/E02/S02 已改为业务明细表聚合

在 V0.3 G 组合规类基础上，继续将 E01、E02、S02 三个高频指标推进到业务明细表聚合。

| KPI | 当前接口数据来源 | 明细行数 | 关键口径 |
| --- | --- | ---: | --- |
| E01 环境监测超标项 | `env_monitoring_record` | 2 | 当前超标 2、本月新增 2、已复测 1、待复测 1、涉及监测点 2 |
| E02 当前未闭环环保问题事项数 | `env_issue_record` | 5 | 未闭环 5、本月新增 2、本月闭环 3、逾期未闭环 1、平均处置 15 天 |
| S02 当前在管较大及以上安全风险点 | `safety_risk_point` | 6 | 较大 4、重大 2、本月新增 1、本月销号 2、涉及工点 4 |

新增脚本：

- `server/seed_environment_safety_detail_v0_4.py`
- `server/environment_safety_kpi_mysql_test.py`

重要口径：

- E01 额外返回 `categoryData`：扬尘 1、噪声 1、合计 2，用于支撑“全部状态同时展示扬尘、噪声分类柱及合计折线”的前端展示；
- E02 额外返回 `statusData`：整改中 2、待复查 2、待销项 1；逾期只通过 `overdue: true` 标记，不作为主状态；
- S02 管控状态统一为“持续管控”，不再使用“治理中”。

V0.4 验收命令：

```powershell
$env:PYTHONIOENCODING='utf-8'
$py='C:\Users\TB\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'

& $py server\seed_environment_safety_detail_v0_4.py
& $py server\environment_safety_kpi_mysql_test.py
& $py server\dashboard_acceptance_test.py
& 'C:\Program Files\nodejs\npm.cmd' run check
& 'C:\Program Files\nodejs\npm.cmd' run build
```

## 11. V0.5 补充：S03/S04 已改为业务明细表聚合

在 V0.4 基础上，继续将 S03、S04 两个社会责任指标推进到业务明细表聚合。

| KPI | 当前接口数据来源 | 明细行数 | 关键口径 |
| --- | --- | ---: | --- |
| S03 当前未办结劳务纠纷 | `labor_dispute_record` | 4 | 未办结 4、本月新增 2、本月办结 1、涉及人数 18、涉及金额 68 万元 |
| S04 当前未办结群众诉求 | `appeal_record` | 3 | 未办结 3、本月新增 2、本月办结 4、逾期未办 1、平均办理 7 天 |

新增脚本：

- `server/seed_social_detail_v0_5.py`
- `server/social_kpi_mysql_test.py`

说明：

- S03/S04 接口路径未变，仍然是 `GET /api/dashboard/kpi/{code}`；
- 前端字段未变，仍返回 `KpiDetailConfig`；
- S03 明细字段仍为：`name`、`time`、`people`、`amount`、`department`、`status`；
- S04 明细字段仍为：`content`、`time`、`source`、`location`、`deadline`、`status`；
- 若业务表为空或 MySQL 不可用，仍可 fallback 到快照层。

V0.5 验收命令：

```powershell
$env:PYTHONIOENCODING='utf-8'
$py='C:\Users\TB\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'

& $py server\seed_social_detail_v0_5.py
& $py server\social_kpi_mysql_test.py
& $py server\dashboard_acceptance_test.py
& 'C:\Program Files\nodejs\npm.cmd' run check
& 'C:\Program Files\nodejs\npm.cmd' run build
```
