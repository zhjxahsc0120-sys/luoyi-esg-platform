# 罗宜高速 ESG 数据库模块与表分层蓝图 V0.1

## 1. 总体分层

建议数据库分为 9 个模块：

| 模块 | 作用 |
|---|---|
| 基础字典 | ESG 模块、资料类型、状态、阶段等 |
| 用户与组织 | 用户、部门、角色、责任单位 |
| 上传任务 | 数据填报任务、资料要求、任务状态 |
| 智能入库 | 文件、AI 解析、字段抽取、候选匹配 |
| 资料中心 | 正式资料、版本、关联、有效期 |
| 审核流转 | 审核记录、退回、补正、轨迹 |
| E/S/G 业务明细 | 支撑指标计算的业务事实表 |
| 指标计算 | KPI 结果、快照、计算任务 |
| 审计日志 | 操作留痕与数据追溯 |

## 2. 表清单建议

### 2.1 基础字典

```text
dict_esg_module
dict_document_type
dict_task_status
dict_review_status
dict_indicator
dict_construction_stage
```

### 2.2 用户与组织

```text
org_unit
user_account
role_definition
user_role
```

### 2.3 上传任务

当前已有原型表：

```text
upload_task
task_document_requirement
task_candidate_document
task_review_timeline
workspace_summary
```

正式化建议保留并增强：

```text
upload_task
upload_task_requirement
upload_task_status_log
upload_task_deadline_rule
```

### 2.4 智能入库

来自智能入库扩展包：

```text
file_asset
ai_parse_job
ai_parse_field_result
ai_field_mapping_rule
task_match_candidate
deduplication_record
manual_confirmation_log
```

### 2.5 资料中心

```text
document_record
document_version
document_task_relation
document_tag
document_access_log
document_summary_snapshot
```

### 2.6 审核流转

```text
review_record
review_timeline
review_requirement
correction_request
```

### 2.7 E/S/G 业务明细表

环境 E：

```text
env_monitoring_record
env_issue_record
water_protection_issue
carbon_emission_activity
carbon_material_usage
low_carbon_measure
```

社会 S：

```text
safety_production_record
safety_risk_point
labor_dispute_record
appeal_record
salary_payment_record
training_record
```

治理 G：

```text
compliance_procedure
permit_record
rectification_record
compliance_material_gap
risk_control_action
```

### 2.8 指标计算

当前已有：

```text
indicator_result
indicator_snapshot
```

正式化建议补充：

```text
indicator_definition
indicator_calculation_rule
indicator_calculation_job
indicator_result
indicator_snapshot
indicator_detail_snapshot
```

### 2.9 审计日志

```text
audit_log
data_change_log
api_access_log
```

## 3. 首页 12 项 KPI 来源建议

| KPI | 来源建议 |
|---|---|
| E01 环境监测超标项次 | `env_monitoring_record` |
| E02 未闭环环保问题 | `env_issue_record` |
| E03 未闭环水保问题 | `water_protection_issue` |
| E04 碳排放强度 | `carbon_emission_activity` + 投资/产值口径 |
| S01 连续安全生产天数 | `safety_production_record` |
| S02 较大及以上安全风险点 | `safety_risk_point` |
| S03 未办结劳务纠纷 | `labor_dispute_record` |
| S04 未办结群众诉求 | `appeal_record` |
| G01 未完成合规手续 | `compliance_procedure` |
| G02 临期及逾期许可 | `permit_record` |
| G03 未关闭整改事项 | `rectification_record` |
| G04 待补齐合规资料 | `compliance_material_gap` |

## 4. 当前阶段建议

下一阶段优先设计并落地：

```text
智能入库表
资料中心表
上传任务表
指标定义表
E/S/G 业务明细核心表
```

暂不优先做：

```text
复杂权限体系
复杂工作流引擎
全量指标自动计算引擎
```
