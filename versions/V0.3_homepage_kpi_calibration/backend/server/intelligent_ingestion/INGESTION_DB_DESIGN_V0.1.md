# 罗宜高速 ESG 智能体资料自动解析入库数据库设计 V0.1

## 1. 设计目标

当前页面联调库已经能够支撑资料上传工作台的展示与基础交互，但智能体资料自动解析入库需要进一步支撑：

- 文件接收与去重；
- AI 解析任务状态管理；
- 字段抽取与标准化；
- 字段到数据库表字段的映射；
- 候选任务智能匹配；
- 人工确认与修正；
- 资料正式入库；
- 资料复用与版本管理；
- 全流程审计留痕。

## 2. 数据流

```text
file_asset
→ ai_parse_job
→ ai_parse_field_result
→ ai_field_mapping_rule
→ task_match_candidate
→ manual_confirmation_log
→ document_record / document_version / document_task_relation
→ audit_log
```

## 3. 为什么不能直接 AI 写业务表

AI 抽取存在误差，因此需要先把原始抽取值、标准化值、置信度、来源页码和人工确认值保留下来。

推荐策略：

```text
AI 原始值进入 ai_parse_field_result
人工确认后进入 document_record 和业务明细表
```

这样可以保证：

- 可追溯；
- 可人工修正；
- 可比较模型版本；
- 可用于后续质量评估；
- 避免低置信度字段污染正式业务数据。

## 4. 表职责

| 表 | 作用 |
|---|---|
| `file_asset` | 管理原始文件资产和文件 hash |
| `ai_parse_job` | 管理一次 AI 解析任务 |
| `ai_parse_field_result` | 保存 AI 抽取字段 |
| `ai_field_mapping_rule` | 定义字段应写入目标表和目标字段 |
| `task_match_candidate` | 保存 AI 推荐的候选任务 |
| `document_task_relation` | 保存正式资料与任务的关联 |
| `document_version` | 支撑资料多版本 |
| `manual_confirmation_log` | 记录人工确认和修正 |
| `deduplication_record` | 保存重复检测结果 |
| `audit_log` | 保存关键操作审计 |

## 5. 字段入库分层

### 5.1 文件层

进入 `file_asset`：

- 文件名；
- 文件格式；
- 文件大小；
- 存储路径；
- hash；
- 上传来源；
- 上传人；
- 上传时间；
- 去重状态；
- 解析状态。

### 5.2 解析层

进入 `ai_parse_field_result`：

- `field_key`
- `field_name`
- `field_value`
- `normalized_value`
- `confidence`
- `source_page`
- `confirm_status`
- `confirmed_value`

### 5.3 资料主档层

确认后进入 `document_record`：

- 资料名称；
- 资料类型；
- ESG 模块；
- 资料周期；
- 责任单位；
- 有效期；
- 关联文件；
- 关联解析任务；
- 确认状态；
- 资料状态。

### 5.4 业务明细层

按资料类型进入业务明细表，例如：

| 资料类型 | 目标业务表 |
|---|---|
| 水保监测月报 | `env_monitoring_record` / `env_issue_record` |
| 碳排放活动数据表 | `carbon_emission_activity` |
| 高风险作业审批资料 | `safety_risk_point` |
| 工资支付资料 | `salary_payment_record` |
| 临时用地合规资料 | `permit_record` |
| NCR整改关闭资料 | `rectification_record` |

## 6. 最小实施版本

建议第一阶段只落这 5 张核心表：

```text
file_asset
ai_parse_job
ai_parse_field_result
ai_field_mapping_rule
task_match_candidate
```

第二阶段再落：

```text
document_task_relation
document_version
manual_confirmation_log
deduplication_record
audit_log
```

## 7. 与当前前端页面关系

| 前端区域 | 需要的后端表 |
|---|---|
| P03 解析队列 | `file_asset` + `ai_parse_job` |
| P03 AI 解析摘要 | `ai_parse_field_result` |
| P03 疑似重复 | `deduplication_record` |
| P03 建议关联任务 | `task_match_candidate` |
| P05 资料中心 | `document_record` + `document_version` |
| S01 任务办理弹窗候选资料 | `document_task_relation` + `task_match_candidate` |

## 8. 后续落地建议

下一步可把本扩展包转为两类任务：

1. 后端数据库任务：按 `schema_extension_v0.1.sql` 建表并补种子数据；
2. 后端接口任务：按 `INGESTION_API_CONTRACT_V0.1.md` 暴露智能入库接口；
3. 前端任务：Trae 将 P03 智能入库页面从 mock 切到新接口。
