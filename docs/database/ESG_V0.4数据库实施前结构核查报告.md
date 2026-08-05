# ESG V0.4 数据库实施前结构核查报告

**核查日期：** 2026-08-04  
**工作区：** `C:\ESG_Project`  
**数据库：** MySQL 8.4.9，`127.0.0.1:3307/luoyi_esg`  
**核查方式：** 只读查询（`SHOW`、`information_schema`、`COUNT(*)`）

> 本次未执行 `CREATE TABLE`、`ALTER TABLE`、`DROP TABLE`、INSERT、UPDATE、DELETE、数据迁移或视图修改。

## 一、核查结论

1. 数据库连接正常，真实库为 `luoyi_esg`，MySQL 版本 8.4.9。
2. 当前真实数据库共有 **128 张 BASE TABLE、21 个 VIEW**。
3. `biz_worker_payment_summary` 存在，2 条 Demo 数据；`biz_labor_payment_record` 不存在。
4. `biz_project_approval`、`biz_permit`、`biz_safety_risk_point` 均不存在，真实库中分别有同类表 `compliance_procedure`、`permit_record`、`safety_risk_point`。
5. `biz_governance_control_item`、`biz_inspection_finding`、`biz_governance_inspection`、`biz_governance_rectification` 均不存在。
6. 治理/整改领域存在多套重叠模型：`biz_internal_control_issue`、`rectification_record`，以及更完整的 `e_closure_case`、`e_rectification_task`、`e_case_status_history`、`e_case_evidence`、`e_case_rectification_link`。
7. `e_closure_case` 是当前最接近 `cl_case` 的真实模型，但其 `case_domain` 检查约束目前只允许 E01/E02/E03，不包含 G04 内控域。
8. 所有重点模型均未发现 `rectification_completed_date` 字段；这是 V0.4 实施前必须解决的结构缺口。

## 二、真实表和视图清单

### 1. BASE TABLE（128 张）

```text
ai_document_analysis, ai_extracted_environment, ai_extracted_progress,
ai_extracted_project_info, ai_extracted_resource, ai_extracted_safety,
ai_field_mapping_rule, ai_parse_field_result, ai_parse_job, appeal_record,
audit_log, biz_construction_slope, biz_cultural_relic_object, biz_design_change,
biz_ecological_protection_object, biz_ecological_sensitive_area,
biz_env_monitor_point, biz_env_monitor_result, biz_internal_control_issue,
biz_night_construction_record, biz_risk_disposal, biz_risk_warning,
biz_soil_disposal_site, biz_temporary_land_use, biz_topsoil_stripping,
biz_worker_payment_summary, carbon_accounting_batch, carbon_accounting_boundary,
carbon_accounting_evidence_link, carbon_emission_activity, carbon_emission_baseline,
carbon_emission_factor, carbon_emission_factor_snapshot,
carbon_emission_segment_detail, carbon_material_usage,
carbon_measure_monthly_performance, carbon_reduction_accounting,
carbon_reduction_measure, cfg_warning_rule, compliance_material_gap,
compliance_procedure, construction_stage_record, dashboard_kpi_detail_snapshot,
dashboard_panel_snapshot, dashboard_topic_snapshot, data_ingestion_job,
data_mapping_rule, data_quality_check_result, data_source_registry,
deduplication_record, dict_document_type, dict_esg_module, document_record,
document_task_relation, document_version, e01_exceed_event,
e01_factor_definition, e01_factor_result, e01_legacy_record_mapping,
e01_monitor_batch, e01_monitor_plan, e01_monitor_plan_item, e01_monitor_point,
e01_monitor_sample, e01_rectification_round, e01_retest_result_link,
e01_retest_round, e01_standard_limit, e01_standard_version, e_case_evidence,
e_case_party, e_case_rectification_link, e_case_relation,
e_case_status_history, e_closure_case, e_rectification_task,
engineering_object_phase, env_issue_record, env_monitoring_record,
esg_demo_indicator_detail, esg_demo_indicator_result,
esg_schema_migration_history, file_asset, gis_feature,
gis_feature_business_relation, gis_feature_business_summary, gis_layer,
indicator_calculation_job, indicator_definition, indicator_history,
indicator_result, indicator_snapshot, indicator_source_dependency,
labor_dispute_record, manual_confirmation_log, monitor_frequency_rule,
monitor_point_object_relation, monthly_report_chapter, monthly_report_cycle,
monthly_report_gap, monthly_report_group_progress, monthly_report_status_chain,
monthly_report_task_instance, monthly_report_task_material_link,
monthly_report_task_validation, org_unit, permit_record,
project_engineering_object, project_phase_period, project_section,
rectification_record, review_record, review_requirement, review_timeline,
s01_confirmation_batch, safety_incident_record, safety_production_record,
safety_risk_point, salary_payment_record, source_record_trace,
task_candidate_document, task_match_candidate, task_review_timeline,
upload_task, upload_task_requirement, user_account, water_protection_issue,
workspace_summary
```

### 2. VIEW（21 个）

```text
v_ai_parse_queue_current, v_dashboard_kpi_current, v_document_summary_current,
v_e01_configuration_data_nature_inconsistency,
v_e01_core_data_nature_inconsistency, v_e01_cross_month_retest_trace,
v_e01_event_result_inconsistency, v_e01_monthly_exceed_count,
v_e01_monthly_exceed_item, v_e01_open_exceed_count, v_e01_open_exceed_event,
v_e01_retest_chain_inconsistency, v_e01_time_quarter_inconsistency,
v_e_case_current_history, v_e_case_effective_history_leaf,
v_e_case_status_inconsistency, v_esg_demo_dashboard_kpis,
v_esg_demo_kpi_detail, v_esg_demo_risk_list, v_task_detail_validation,
v_workspace_summary_current
```

## 三、重点表真实结构

### 1. `biz_worker_payment_summary`

**存在：** 是  
**数据量：** 2 条  
**性质：** 表注释和来源编号表明为当前 S03 Demo 工资统计事实。

| 字段 | 类型 | 说明 |
|---|---|---|
| `id` | bigint unsigned | 主键 |
| `project_id` | bigint unsigned | 项目 |
| `section_id` | bigint unsigned | 标段，可空 |
| `period_start` / `period_end` | date | 统计周期 |
| `responsible_org_id` | bigint unsigned | 责任组织，可空 |
| `worker_count` | int unsigned | 人数 |
| `payable_amount` / `paid_amount` | decimal(18,2) | 应付/已付金额 |
| `payment_rate` | decimal(5,2) | 支付比例 |
| `payment_status` | varchar(32) | 支付状态 |
| `overdue_amount` / `dispute_count` | decimal/int | 逾期金额/争议数 |
| `risk_status` | varchar(16) | 风险状态 |
| `source_doc_ref` | varchar(255) | 来源资料 |
| `updated_at` | datetime | 更新时间 |
| `is_deleted` | tinyint unsigned | 软删除标识 |

当前两条 Demo 记录均为项目 1001、2026-07-01 至 2026-07-31，人数分别为 168 和 152，`payment_rate` 分别为 100.00 和 98.50。

**与 `biz_labor_payment_record` 的关系：**

- 当前不能直接判断新表已被替代，因为 `biz_labor_payment_record` 不存在。
- 该表可以复用为当前 V0.3/V0.4 S03 的事实来源，但字段与 V0.4 设计不完全一致：缺少明确的 `source_type`、`record_date`、`created_time` 和 `paid_on_time_rate` 命名。
- 表中保留金额字段；V0.4 展示和模板不应向前端或模板暴露个人工资明细，金额字段是否继续保留由数据治理确认。
- **建议：** 优先评审“兼容复用/视图映射”方案，不要直接新建重复工资事实表。

### 2. `biz_project_approval`

**存在：** 否。  
**当前同类表：** `compliance_procedure`，7 条。

`compliance_procedure` 当前字段包括：

```text
id, document_id, procedure_name, status, impact_node, overdue,
created_at, procedure_type, deadline, responsible_department,
progress_percent, completed_date, expected_complete_date
```

**差异：**

- `procedure_type` 可作为审批类型候选，但不是已确认的 `approval_type`。
- 有 `status`，但没有已确认的 `approval_status` 命名。
- 有 `completed_date`，没有明确的 `approval_date`。
- 没有 `project_id`，当前更依赖 `document_id` 关联。

**结论：** 不能直接对不存在的 `biz_project_approval` 执行 `ALTER TABLE`。应先确认 V0.4 是复用 `compliance_procedure`，还是建立独立审批事实表。

### 3. `biz_permit`

**存在：** 否。  
**当前同类表：** `permit_record`，5 条。

`permit_record` 字段包括：

```text
id, document_id, permit_name, permit_no, expire_date, status,
created_at, permit_type, responsible_department
```

**与 G01/G02 合并的关系：**

- `permit_type`、`status`、`expire_date` 可支持许可证事实和有效期判断。
- 当前没有 `project_id`、`approval_date` 和明确的施工管控关联字段。
- G01/G02 合并后的分母不能直接等于 `permit_record` 全表数量，必须先定义纳入范围、有效状态和与 `compliance_procedure` 的去重关系。

### 4. `biz_safety_risk_point`

**存在：** 否。  
**当前同类表：** `safety_risk_point`，10 条。

| 字段 | 类型 | V0.4 可用性 |
|---|---|---|
| `id` | bigint | 可作为风险源主键候选 |
| `risk_name` | varchar(255) | 风险对象名称 |
| `risk_level` | varchar(50) | 已有风险等级字段，沿用其值域 |
| `control_status` | varchar(50) | 管控状态 |
| `control_measure` | text | 管控措施 |
| `location` | varchar(255) | 位置 |
| `risk_type` | varchar(100) | 风险类型 |
| `control_start_date` / `cancelled_date` | date | 管控起止信息 |
| `document_id` | bigint | 当前资料关联 |

当前表没有 `project_id`，也没有任何专项方案审批外键关系。其 `id` 可以作为未来 `risk_point_id` 的关联目标候选，但不能在未确认模型前直接增加外键。

### 5. 治理和整改相关表

#### 5.1 指定表存在性

| 表名 | 是否存在 | 数据量 |
|---|---:|---:|
| `biz_governance_control_item` | 否 | — |
| `biz_inspection_finding` | 否 | — |
| `biz_governance_inspection` | 否 | — |
| `biz_governance_rectification` | 否 | — |
| `biz_internal_control_issue` | 是 | 2 |
| `rectification_record` | 是 | 9 |
| `e_closure_case` | 是 | 17 |
| `e_rectification_task` | 是 | 2 |
| `e_case_status_history` | 是 | 64 |
| `e_case_evidence` | 是 | 29 |
| `e_case_rectification_link` | 是 | 2 |

#### 5.2 `biz_internal_control_issue`

当前字段包括：

```text
id, project_id, section_id, issue_code, issue_type, issue_level,
issue_description, found_at, responsible_org_id, current_status,
deadline, closed_at, recurrence_flag, evidence_status, risk_status,
source_doc_ref, updated_at, is_deleted
```

当前有 1 条 `OPEN`、1 条 `CLOSED`。它具备发现时间、期限和关闭时间，但没有整改要求、整改完成时间和复核时间。

#### 5.3 `rectification_record`

当前字段包括：

```text
id, document_id, item_name, status, source_type, overdue,
closed_date, created_at, issue_level, deadline,
responsible_department, check_batch
```

它具备通用整改记录、期限、状态和关闭日期，但缺少：

- `problem_code`；
- `problem_description`；
- `rectification_requirement`；
- `discovered_date`；
- `rectification_completed_date`；
- `verification_date`。

#### 5.4 `e_closure_case` 及配套闭环模型

`e_closure_case` 是当前最接近 `cl_case` 的真实模型，具备：

- `case_code`、`case_domain`、来源表/来源记录；
- `current_status`、`deadline`、`opened_at`、`closed_at`；
- 责任组织、复核组织、关闭组织；
- `data_nature`、`is_demo`、审核/生效状态；
- 状态历史、证据材料和整改任务关联。

配套表：

```text
e_rectification_task
e_case_status_history
e_case_evidence
e_case_rectification_link
e_case_party
e_case_relation
```

当前约束显示：

- `case_domain` 仅允许 `E01_EXCEED`、`E02_ENV`、`E03_WATER`；
- 当前没有 G04 内控检查域；
- `e_closure_case`、`e_rectification_task` 均没有 `rectification_completed_date`；
- 状态模型比 V0.4 任务书的五状态更细，包含 `DISCOVERED`、`PENDING_RECTIFICATION`、`RECTIFYING`、`PENDING_REVIEW`、`PENDING_CLOSURE`、`CLOSED` 等。

**结论：** 数据库已经存在一个较完整的 E 组闭环模型。V0.4 不应再直接创建一个孤立的 `cl_case`；应先评审是否扩展 `e_closure_case` 的域和值域，或建立跨域通用模型。

## 四、与 V0.4 设计差异

| V0.4 设计对象/要求 | 真实数据库现状 | 差异判断 |
|---|---|---|
| `biz_labor_payment_record` | 不存在；有 `biz_worker_payment_summary` | 可复用但字段需映射/评审 |
| `biz_project_approval` | 不存在；有 `compliance_procedure` | 不能直接 ALTER，需确定事实来源 |
| `biz_permit` | 不存在；有 `permit_record` | 可作为许可证事实候选，但缺项目/审批关联 |
| `biz_safety_risk_point` | 不存在；有 `safety_risk_point` | 有风险等级和主键，但缺项目字段和方案关联 |
| `biz_special_plan_approval` | 不存在 | 需要新增或寻找现有专项方案模型 |
| `biz_governance_inspection` | 不存在 | 需要新增或映射检查事实来源 |
| `biz_governance_rectification` | 不存在 | 需要新增或复用现有闭环模型 |
| `cl_case` | 不存在；有 `e_closure_case` | 不建议直接新建，先评审既有模型 |
| 整改完成时间 | 所有重点表均未发现 `rectification_completed_date` | 明确结构缺口 |
| 状态机 | E 组已有更细状态机；旧表状态较粗 | 不能直接用字符串覆盖，需要状态映射 |
| G01/G02 合并 | `compliance_procedure`、`permit_record` 分离 | 需先定义分母、去重和有效状态 |

## 五、可直接复用的表/模型

### 可优先复用

1. `biz_worker_payment_summary`：当前 S03 Demo 事实来源，优先做字段映射或兼容视图评审。
2. `compliance_procedure`：审批/合规手续候选事实，但需补齐或映射审批日期、项目归属和状态口径。
3. `permit_record`：许可证事实候选，需补充项目范围和 G01/G02 关系设计后再用。
4. `safety_risk_point`：风险事实候选，已有 `risk_level`、`control_status`、`location`。
5. `e_closure_case` 及其状态历史、证据、整改任务配套表：已有最完整闭环能力，但当前只覆盖 E01/E02/E03。
6. `biz_internal_control_issue`：G04 现有 Demo 内控问题事实，可作为历史映射来源。

### 不宜直接复用为 V0.4 最终模型

- `salary_payment_record`：0 条数据，含金额字段，不能直接表达按时发放率。
- `rectification_record`：字段过少，缺少 V0.4 要求的完成时间和复核时间。
- `e_closure_case`：虽结构完整，但当前域约束不含 G04，且缺少整改完成日期；需先做扩展设计。

## 六、需要新增或修改的对象

### 1. 需要新增的候选对象

在业务确认后再决定是否执行：

- `biz_special_plan_approval`：若没有现有专项方案审批事实表，建议新增。
- `biz_governance_inspection`：若检查事实不能由现有表映射，建议新增。
- `biz_governance_rectification`：若不扩展既有 E 闭环模型，建议新增跨域整改表。

`cl_case` 不列入直接新增项，优先评审 `e_closure_case` 是否可扩展为跨域闭环模型。

### 2. 需要修改/扩展评审的对象

| 对象 | 可能变更 | 前置条件 |
|---|---|---|
| `biz_worker_payment_summary` 或兼容视图 | 映射 `period`、`total_workers`、`paid_on_time_rate`、`source_type`、`record_date` | S03 事实表取舍确认 |
| `compliance_procedure` | 审批类型、审批状态、审批日期、项目关联 | 是否作为 `biz_project_approval` 替代物 |
| `permit_record` | 项目关联、施工管控关系、有效状态口径 | G01/G02 分母确认 |
| `safety_risk_point` | 项目关联、专项方案关系 | 是否以其作为风险事实主表 |
| `e_closure_case` / `e_rectification_task` | G04 域、整改完成时间、状态映射 | 是否复用现有 E 闭环模型 |
| `biz_internal_control_issue` | 整改要求、完成时间、复核时间的映射或关联 | 是否保留为 G04 历史事实表 |
| `rectification_record` | 统一问题字段和时间链，或仅保留历史兼容 | 是否被既有接口使用 |

## 七、风险项

1. **模型重复风险：** 新设计的 `biz_governance_*` 与现有 `e_*` 闭环模型可能形成两套状态、证据和整改任务。
2. **`cl_case` 误建风险：** 当前已有 `e_closure_case`，直接新增同义表会破坏事实链和历史追溯。
3. **完成时间缺失风险：** 当前表普遍只有 `closed_at/closed_date`，没有甲方填报的 `rectification_completed_date`，不能用关闭时间替代。
4. **G01/G02 统计重复风险：** `compliance_procedure` 和 `permit_record` 可能存在同一事项不同记录，合并前必须定义去重键。
5. **项目隔离风险：** `compliance_procedure`、`permit_record`、`safety_risk_point` 当前结构未显示 `project_id`，不能直接作为多项目正式事实主链。
6. **状态不一致风险：** 旧表使用中文状态或粗粒度状态，E 闭环使用英文状态码和更细状态机，必须建立映射表或明确兼容层。
7. **敏感数据风险：** 工资表保留应付/实付金额字段，V0.4 S03 设计要求不采集和不展示工资金额明细，需要明确访问权限和 API 出参边界。
8. **Demo/正式混用风险：** 多张表同时存在 `data_nature`、`is_demo` 或来源编号，实施时必须保持 Demo 与正式数据隔离。
9. **视图回归风险：** 当前 `v_esg_demo_dashboard_kpis` 直接读取 `esg_demo_indicator_result`，并对 S01 做日期计算；未经 V0.4 KPI key 和口径确认不得修改。

## 八、建议迁移顺序

### 第 0 步：模型决策冻结

先确认：

- S03 是否复用 `biz_worker_payment_summary`，还是另建 `biz_labor_payment_record`；
- `compliance_procedure`/`permit_record` 是否作为 G01/G02 合并事实源；
- `safety_risk_point` 是否作为风险源主表；
- `e_closure_case` 是否扩展 G04，还是建立新的跨域整改模型；
- `cl_case` 是否放弃新建；
- `rectification_completed_date` 的存储位置、填报权限和状态规则。

### 第 1 步：真实结构和来源脚本对齐

为每个决定复用的表补齐：线上 DDL、来源脚本、数据字典、外键、已有 API 使用点和回滚方案。当前工作区 SQL 与真实库存在命名不一致，不能仅按设计稿生成 `ALTER`。

### 第 2 步：先扩展闭环核心

优先解决整改完成时间、复核时间、关闭时间和状态历史，再处理 G01/G02 统计合并。原因是整改闭环是跨 E/S/G 的基础能力，且当前已有 `e_closure_case` 配套模型可供评审。

### 第 3 步：补齐专项方案审批关系

在风险主表和风险等级字典确认后，再决定是否新增 `biz_special_plan_approval`，并建立与风险源的关系；不得先建空壳表。

### 第 4 步：迁移/映射事实数据

仅在结构和字段确认后，编写可回滚的数据映射脚本。此步骤必须单独审批，本次未执行。

### 第 5 步：更新指标视图和 API

数据库事实和闭环验收后，才更新 `v_esg_demo_dashboard_kpis`、详情查询和新接口；首页和 Cursor 页面最后调整。

## 九、最终状态

| 阶段 | 状态 |
|---|---|
| 工作区迁移 | 已完成 |
| V0.3 基线 | 已冻结 |
| V0.4 业务设计 | 已完成 |
| V0.4 数据库实施清单 | 已完成 |
| MySQL 真实结构核查 | **本报告已完成** |
| 数据库实施 | 未开始，等待确认 |
| API 调整 | 未开始 |
| Cursor 页面调整 | 未开始 |

**核查结论：** 当前真实 MySQL 不是一套全新的 `biz_*` V0.4 结构，而是 V0.3 Demo 事实表、通用旧表和 E 组闭环模型并存。下一步应先确认复用/扩展/新增边界，尤其是 `e_closure_case` 与 `cl_case` 的关系，以及 `rectification_completed_date` 的最终落点，再允许任何数据库实施。
