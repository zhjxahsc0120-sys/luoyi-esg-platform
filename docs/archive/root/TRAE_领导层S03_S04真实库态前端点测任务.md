# TRAE 任务：领导层 S03/S04 真实库态前端点测

## 背景

Codex 已完成后端与 MySQL 侧改造：

- S03 从 `labor_dispute_record` 聚合；
- S04 从 `appeal_record` 聚合；
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

### S03 当前未办结劳务纠纷

期望：

- 数据来源来自：`labor_dispute_record`
- 未办结纠纷：4
- 本月新增：2
- 本月办结：1
- 涉及人数：18
- 涉及金额：68 万元
- 明细 4 条
- 明细字段包含：纠纷事项、发生时间、涉及人数、涉及金额、责任部门、办理状态。

### S04 当前未办结群众诉求

期望：

- 数据来源来自：`appeal_record`
- 未办结诉求：3
- 本月新增：2
- 本月办结：4
- 逾期未办：1
- 平均办理时长：7 天
- 明细 3 条
- 明细字段包含：诉求内容、受理时间、诉求来源、涉及地点、办结期限、办理状态。

## 样式/文案可优化点

3. S03 金额、人数、状态是否显示正常；
4. S04 逾期记录是否有清楚但不过度的提示；
5. 是否存在布局溢出、字段遮挡、表格横向滚动；
6. 如做了样式或文案调整，列出修改文件；
- 如数据来源文案过长，例如 `劳务纠纷明细表 labor_dispute_record`，页面上可显示为 `劳务纠纷明细表`；
- S03 涉及金额建议统一显示为 `xx万元`；
- S04 逾期状态建议使用橙/红色弱强调，但不要新增督办或办理操作；
- 如表格列宽不适配，可只调整样式，不改字段。

## 验收命令

```powershell
$env:PYTHONIOENCODING='utf-8'
$py='C:\Users\TB\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'

& $py server\social_kpi_mysql_test.py
& $py server\dashboard_acceptance_test.py
& 'C:\Program Files\nodejs\npm.cmd' run check
& 'C:\Program Files\nodejs\npm.cmd' run build
```

## 回报格式

请回报：

1. S03/S04 弹窗是否均可打开；
2. 两个弹窗摘要数字是否符合上述口径；
7. `npm run check` 和 `npm run build` 结果。

