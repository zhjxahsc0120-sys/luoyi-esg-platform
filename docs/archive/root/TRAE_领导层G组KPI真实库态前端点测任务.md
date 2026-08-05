# TRAE 任务：领导层 G 组 KPI 真实库态前端点测

## 背景

Codex 已完成后端与 MySQL 侧改造：

- G01、G02、G03、G04 不再只从快照 JSON 返回；
- 当前优先从 MySQL 业务明细表聚合；
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

点击首页 G 组四个 KPI 卡片，逐项检查弹窗：

### G01 当前未完成法定报批报建

期望：

- 数据来源显示或内部数据来自：`compliance_procedure`
- 未完成事项：5
- 本月新增：1
- 本月完成：2
- 逾期未办：1
- 明细 5 条

### G02 当前临期及逾期许可事项数

期望：

- 数据来源显示或内部数据来自：`permit_record`
- 临期许可：4
- 逾期许可：1
- 30日内到期：4
- 涉及部门：3
- 明细 5 条
- 不应再出现“剩余36天”或 30 日以上记录

### G03 当前未关闭整改事项数

期望：

- 数据来源显示或内部数据来自：`rectification_record`
- 未关闭事项：6
- 本月新增：2
- 本月关闭：3
- 逾期未关闭：2
- 涉及检查：3
- 明细 6 条

### G04 当前待补齐合规资料项数

期望：

- 数据来源显示或内部数据来自：`compliance_material_gap`
- 待补齐资料：4
- 本月需提交：3
- 逾期未提交：1
- 涉及模块：3
- 资料完备率：85%
- 明细 4 条

## 样式/文案可优化点

如页面上仍显示“本月到期”，请统一改为“30日内到期”。

如数据来源文案过长，例如：

`证照许可明细表 permit_record`

可显示为：

`证照许可明细表`

但不要修改后端返回字段结构。

## 验收命令

```powershell
$env:PYTHONIOENCODING='utf-8'
$py='C:\Users\TB\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'

& $py server\governance_kpi_mysql_test.py
& $py server\dashboard_acceptance_test.py
& 'C:\Program Files\nodejs\npm.cmd' run check
& 'C:\Program Files\nodejs\npm.cmd' run build
```

## 回报格式

请回报：

1. 四个 G 组弹窗是否均可打开；
2. 四个弹窗摘要数字是否符合上述口径；
3. G02 是否显示“30日内到期 4”；
4. 是否存在布局溢出、字段遮挡、表格横向滚动；
5. 如做了样式或文案调整，列出修改文件；
6. `npm run check` 和 `npm run build` 结果。

