# 罗宜高速 ESG 全局数据流设计 V0.1

## 1. 总体链路

罗宜高速 ESG 平台的数据链路建议按“数据产生端 → 数据确认端 → 数据沉淀端 → 指标汇总端 → 领导展示端”分层。

```text
数据上传工作台
→ 智能体资料自动解析入库
→ 人工确认 / 审核
→ 资料中心与业务明细表
→ 指标计算与快照
→ 领导层 ESG 看板
```

## 2. 关键链路

### 2.1 资料上传与智能解析

```text
用户上传文件
→ file_asset
→ deduplication_record
→ ai_parse_job
→ ai_parse_field_result
→ task_match_candidate
```

用途：

- 保存原始文件；
- 检测重复；
- AI 抽取资料类型、周期、模块、责任单位等；
- 推荐可关联任务。

### 2.2 人工确认与正式入库

```text
ai_parse_field_result
→ manual_confirmation_log
→ document_record
→ document_version
→ document_task_relation
```

用途：

- 人工确认 AI 抽取结果；
- 生成资料中心正式资料；
- 建立资料与上传任务的多对多关系；
- 记录版本和确认痕迹。

### 2.3 资料进入业务明细

确认后的资料按类型进入 E/S/G 业务明细表。

```text
document_record
→ env_monitoring_record / env_issue_record / carbon_emission_activity
→ safety_risk_point / labor_dispute_record / appeal_record
→ compliance_procedure / permit_record / rectification_record
```

用途：

- 支撑 KPI 自动计算；
- 支撑 KPI 详情弹窗；
- 支撑专题模块和月报输出。

### 2.4 指标计算与快照

```text
业务明细表
→ indicator_calculation_job
→ indicator_result
→ indicator_snapshot
→ dashboard API
```

用途：

- 首页 12 项 KPI 不直接来自 mock；
- KPI 详情弹窗来自业务明细表和指标快照；
- 支持按日、按月、按阶段留存历史结果。

## 3. 数据责任边界

| 层级 | 职责 | 示例 |
|---|---|---|
| 文件层 | 管理原始文件 | `file_asset` |
| 解析层 | 管理 AI 输出 | `ai_parse_job`, `ai_parse_field_result` |
| 确认层 | 管理人工确认 | `manual_confirmation_log` |
| 资料层 | 管理正式资料 | `document_record`, `document_version` |
| 关联层 | 管理资料复用 | `document_task_relation` |
| 业务层 | 管理业务明细 | E/S/G 明细表 |
| 指标层 | 管理 KPI 结果 | `indicator_result`, `indicator_snapshot` |
| 展示层 | 面向页面 API | dashboard/workspace APIs |

## 4. 设计判断

当前 S01 已完成 API 接入，证明技术路径可行。后续不建议直接接剩余 11 个 KPI 弹窗，而应先补齐业务明细表和指标汇总逻辑。

否则会出现：

```text
前端接口已接入
但接口数据仍是为了展示手工拼装
无法支撑真实业务汇总
```

正确顺序是：

```text
先业务数据结构
再指标计算
再页面接口
```
