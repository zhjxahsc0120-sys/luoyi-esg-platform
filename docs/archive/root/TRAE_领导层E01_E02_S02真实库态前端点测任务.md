# TRAE 任务：领导层 E01/E02/S02 真实库态前端点测

## 背景

Codex 已完成后端与 MySQL 侧改造：

- E01 从 `env_monitoring_record` 聚合；
- E02 从 `env_issue_record` 聚合；
- S02 从 `safety_risk_point` 聚合；
- 接口路径和前端字段保持不变。

请 Trae 只做前端点测和必要的文案/样式适配，不要重构接口逻辑。

## 访问地址

- 领导层 ESG 看板：http://127.0.0.1:5174/#/
- 后端健康检查：http://127.0.0.1:8765/health

## 不允许修改

不要修改以下接口接入逻辑：

- `src/services/api.ts`
- `src/views/DashboardPage.vue` 中 `handleKpiSelect`
- `src/stores/dashboard.store.ts` 中 `loadPanels`
- `src/components/modal/KpiDetailModal.vue` 中 `topicData` computed 映射

如因样式调整必须改组件，请保持字段兼容。

## 点测范围

点击首页对应 KPI 卡片，逐项检查弹窗：

### E01 环境监测超标项

期望：

- 数据来源来自：`env_monitoring_record`
- 当前超标项：2
- 本月新增：2
- 已复测：1
- 待复测：1
- 涉及监测点：2
- 明细 2 条
- `categoryData` 口径：扬尘 1、噪声 1、合计 2
- 如果前端展示“全部”状态图表，应同时体现扬尘、噪声分类和合计，不得只显示 dust 数据。

### E02 当前未闭环环保问题事项数

期望：

- 数据来源来自：`env_issue_record`
- 当前未闭环：5
- 本月新增：2
- 本月闭环：3
- 逾期未闭环：1
- 平均处置时长：15 天
- 明细 5 条
- 主状态构成只包含：整改中 2、待复查 2、待销项 1
- 不得把“逾期”作为主状态；逾期只通过 `overdue` 字段或行状态提示表达。

### S02 当前在管较大及以上安全风险点

期望：

- 数据来源来自：`safety_risk_point`
- 较大风险点：4
- 重大风险点：2
- 本月新增：1
- 本月销号：2
- 涉及工点：4
- 明细 6 条
- 管控状态统一为“持续管控”或“正常管控”，不得出现“治理中”。

## 样式/文案可优化点

- 如数据来源文案过长，例如 `环境监测明细表 env_monitoring_record`，页面上可显示为 `环境监测明细表`；
- 如表格列宽不适配，可只调整样式，不改字段；
- 如 E01 图表仍只显示 dust，请修正图表数据映射，优先使用接口返回的 `categoryData`。

## 验收命令

```powershell
$env:PYTHONIOENCODING='utf-8'
$py='C:\Users\TB\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'

& $py server\environment_safety_kpi_mysql_test.py
& $py server\dashboard_acceptance_test.py
& 'C:\Program Files\nodejs\npm.cmd' run check
& 'C:\Program Files\nodejs\npm.cmd' run build
```

## 回报格式

请回报：

1. E01/E02/S02 弹窗是否均可打开；
2. 三个弹窗摘要数字是否符合上述口径；
3. E01 是否同时展示扬尘、噪声和合计；
4. E02 是否没有把“逾期”作为主状态；
5. S02 是否没有出现“治理中”；
6. 是否存在布局溢出、字段遮挡、表格横向滚动；
7. 如做了样式或文案调整，列出修改文件；
8. `npm run check` 和 `npm run build` 结果。

