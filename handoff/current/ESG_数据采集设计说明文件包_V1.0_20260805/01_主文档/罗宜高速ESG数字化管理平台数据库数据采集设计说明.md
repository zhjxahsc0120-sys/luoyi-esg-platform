# 罗宜高速 ESG 数字化管理平台数据库数据采集设计说明

> 面向业务人员与 Excel 录入模板设计人员。内容来自**当前运行库只读扫描**，不是历史设计稿推断。

## 0. 文档信息

| 项 | 内容 |
|---|---|
| 生成日期 | 2026-08-05 08:53 |
| 数据库类型 | MySQL 8.4.9 |
| 地址 / 端口 | `127.0.0.1:3307` |
| Schema | `luoyi_esg` |
| 当前连接账号 | `luoyi_app`（会话 `luoyi_app@localhost` / 权限用户 `luoyi_app@127.0.0.1`） |
| 配置来源 | 项目根 `.env.example`（无本地 `.env`）；运行中 API 实际使用旧工作区 `.env` 连接同一 MySQL |
| 基表数量 | 129 |
| 视图数量 | 21 |
| 字段总数 | 1981 |
| 外键数量 | 84 |
| 操作边界 | 只读分析；未改代码、未改库、未执行 DDL |

### 0.1 配置定位结果（第一阶段）

| 检查项 | 结果 |
|---|---|
| `C:\ESG_Project\.env` | 不存在（未纳入版本库） |
| `C:\ESG_Project\.env.example` | 存在：`LUOYI_MYSQL_HOST/PORT/DATABASE/USER`，密码占位 |
| `application.yml` / `docker-compose.yml` | 未发现 |
| 后端默认配置 | `backend/mysql_db.py`：默认 `127.0.0.1:3307` / `luoyi_esg` / `luoyi_app` |
| 初始化 / migration | `database/current/`、`database/migration/v0.4/`、`database/archive/` |
| 当前运行 API `/health` | MySQL 已连通：`127.0.0.1:3307` / `luoyi_esg` / `8.4.9` |

说明：本文**不写入数据库密码**。现场如需连接，请使用本地受控 `.env`。

## 1. 数据库总体结构

当前库同时包含：

1. **现场业务事实表**（监测、问题、风险、许可、诉求等，供人工录入/文件挂接）；
2. **闭环与整改底座**（`e_closure_case`、`e_rectification_task` 等）；
3. **指标与看板结果**（`indicator_*`、`esg_demo_*`、dashboard 快照与视图）；
4. **文件资料与工作台**（`file_asset`、`document_*`、上传/审核）；
5. **GIS 关联**（`gis_layer` / `gis_feature` / 业务关联）；
6. **AI 解析与数据接入**（自动抽取，人工确认后入库）；
7. **视图**（用于首页 KPI、工作台摘要、E01 一致性检查等，**不作为 Excel 录入目标**）。

```text
业务人员 Excel / 现场采集
        ↓ 人工录入或文件上传
业务事实表 / 文件资料表 / GIS 关联
        ↓ 系统计算或任务调度
闭环状态 / 风险预警 / 指标结果 / 首页视图
```

## 2. 全部数据表清单（按 ESG 业务分类）

下表覆盖当前 schema 全部基表。`中文用途`优先取库表注释；无注释时使用业务归类名称。`当前行数`为扫描时精确计数。

### 2.1 E 类

| 表名 | 中文用途 | 类型 | 录入属性 | 当前行数 |
|---|---|---|---|---:|
| `biz_construction_slope` | Demo E02 施工边坡对象 | 业务事实表 | 必须人工录入 | 2 |
| `biz_cultural_relic_object` | E04 文物保护管控对象演示台账 | 业务事实表 | 必须人工录入 | 4 |
| `biz_ecological_protection_object` | Demo E03 生态保护对象 | 业务事实表 | 必须人工录入 | 2 |
| `biz_ecological_sensitive_area` | Demo E03 生态敏感区 | 业务事实表 | 必须人工录入 | 2 |
| `biz_env_monitor_point` | 环境监测点 | 业务事实表 | 必须人工录入 | 3 |
| `biz_env_monitor_result` | 环境监测结果 | 业务事实表 | 必须人工录入 | 12 |
| `biz_soil_disposal_site` | Demo E02 弃土弃渣场对象 | 业务事实表 | 必须人工录入 | 2 |
| `biz_temporary_land_use` | Demo E02 临时用地对象 | 业务事实表 | 必须人工录入 | 2 |
| `biz_topsoil_stripping` | Demo E02 表土剥离对象 | 业务事实表 | 必须人工录入 | 2 |
| `carbon_accounting_batch` | 碳排放核算批次（§5.3） | 业务事实表 | 必须人工录入 | 1 |
| `carbon_accounting_boundary` | 碳排放核算边界配置（按来源维度，§5.2） | 配置表 | 必须人工录入 | 4 |
| `carbon_accounting_evidence_link` | 碳核算与既有资料关联 | 关联表 | 文件上传关联 | 0 |
| `carbon_emission_activity` | 碳排放活动数据 | 业务事实表 | 必须人工录入 | 6 |
| `carbon_emission_baseline` | 碳排放基准方案 | 业务事实表 | 必须人工录入 | 6 |
| `carbon_emission_factor` | 碳排放因子元数据（含演示测试因子） | 配置表 | 必须人工录入 | 6 |
| `carbon_emission_factor_snapshot` | 碳排放因子不可变快照（行级，§5.4） | 业务事实表 | 系统自动生成/计算 | 6 |
| `carbon_emission_segment_detail` | 碳排放月度-标段-来源-材料演示明细 | 业务事实表 | 必须人工录入 | 108 |
| `carbon_material_usage` | 碳排放材料用量 | 业务事实表 | 必须人工录入 | 18 |
| `carbon_measure_monthly_performance` | 低碳措施月度成效 | 业务事实表 | 必须人工录入 | 4 |
| `carbon_reduction_accounting` | 月度低碳增益核算 | 业务事实表 | 必须人工录入 | 6 |
| `carbon_reduction_measure` | 低碳措施及成本台账 | 业务事实表 | 必须人工录入 | 4 |
| `e01_exceed_event` | E01超标事件 | 业务事实表 | 系统自动生成/计算 | 3 |
| `e01_factor_definition` | E01监测因子定义 | 配置表 | 必须人工录入 | 6 |
| `e01_factor_result` | E01因子监测结果 | 业务事实表 | 必须人工录入 | 37 |
| `e01_legacy_record_mapping` | E01历史映射 | 关联表 | 系统自动生成/计算 | 0 |
| `e01_monitor_batch` | E01监测批次 | 业务事实表 | 必须人工录入 | 19 |
| `e01_monitor_plan` | E01监测计划 | 业务事实表 | 必须人工录入 | 3 |
| `e01_monitor_plan_item` | E01监测计划明细 | 关联表 | 必须人工录入 | 4 |
| `e01_monitor_point` | E01监测点主数据 | 业务事实表 | 必须人工录入 | 4 |
| `e01_monitor_sample` | E01监测样品 | 业务事实表 | 必须人工录入 | 19 |
| `e01_rectification_round` | E01整改轮次 | 业务事实表 | 必须人工录入 | 3 |
| `e01_retest_result_link` | E01复测结果关联 | 关联表 | 系统自动生成/计算 | 1 |
| `e01_retest_round` | E01复测轮次 | 业务事实表 | 必须人工录入 | 1 |
| `e01_standard_limit` | E01标准限值 | 配置表 | 必须人工录入 | 6 |
| `e01_standard_version` | E01标准版本 | 配置表 | 必须人工录入 | 3 |
| `env_issue_record` | 环保问题记录 | 业务事实表 | 必须人工录入 | 10 |
| `env_monitoring_record` | 环境监测记录 | 业务事实表 | 必须人工录入 | 3 |
| `monitor_frequency_rule` | 监测频次规则 | 配置表 | 必须人工录入 | 5 |
| `monitor_point_object_relation` | 监测点与对象关联 | 关联表 | 必须人工录入 | 4 |
| `water_protection_issue` | 水保问题记录 | 业务事实表 | 必须人工录入 | 16 |

### 2.2 S 类

| 表名 | 中文用途 | 类型 | 录入属性 | 当前行数 |
|---|---|---|---|---:|
| `appeal_record` | 群众诉求记录 | 业务事实表 | 必须人工录入 | 7 |
| `biz_worker_payment_summary` | Demo S03 工资支付周期汇总 | 业务事实表 | 必须人工录入 | 2 |
| `labor_dispute_record` | 劳务纠纷记录 | 业务事实表 | 必须人工录入 | 3 |
| `s01_confirmation_batch` | S01 建设单位确认批次 | 业务事实表 | 必须人工录入 | 1 |
| `safety_incident_record` | 安全生产事故台账 | 业务事实表 | 必须人工录入 | 0 |
| `safety_production_record` | 连续安全生产记录 | 业务事实表 | 必须人工录入 | 2 |
| `safety_risk_point` | 安全风险点 | 业务事实表 | 必须人工录入 | 10 |
| `salary_payment_record` | 工资支付记录 | 业务事实表 | 必须人工录入 | 0 |

### 2.3 G 类

| 表名 | 中文用途 | 类型 | 录入属性 | 当前行数 |
|---|---|---|---|---:|
| `biz_design_change` | Demo G03 设计变更 | 业务事实表 | 必须人工录入 | 4 |
| `biz_internal_control_issue` | Demo G04 内控廉洁问题 | 业务事实表 | 必须人工录入 | 2 |
| `biz_night_construction_record` | Demo G02 夜间施工记录 | 业务事实表 | 必须人工录入 | 2 |
| `compliance_material_gap` | 待补齐合规资料 | 业务事实表 | 必须人工录入 | 4 |
| `compliance_procedure` | 合规手续 | 业务事实表 | 必须人工录入 | 7 |
| `permit_record` | 许可事项 | 业务事实表 | 必须人工录入 | 5 |
| `rectification_record` | 整改事项 | 业务事实表 | 必须人工录入 | 9 |
| `special_plan_approval` | 风险专项方案审批事实（库注释：ESG risk special-plan approval facts） | 业务事实表 | 必须人工录入 | 0 |

### 2.4 综合 类

| 表名 | 中文用途 | 类型 | 录入属性 | 当前行数 |
|---|---|---|---|---:|
| `ai_document_analysis` | AI文档分析 | 业务事实表 | 系统自动生成/计算 | 3 |
| `ai_extracted_environment` | AI抽取-环境 | 业务事实表 | 系统自动生成/计算 | 3 |
| `ai_extracted_progress` | AI抽取-进度 | 业务事实表 | 系统自动生成/计算 | 12 |
| `ai_extracted_project_info` | AI抽取-项目信息 | 业务事实表 | 系统自动生成/计算 | 3 |
| `ai_extracted_resource` | AI抽取-资源 | 业务事实表 | 系统自动生成/计算 | 3 |
| `ai_extracted_safety` | AI抽取-安全 | 业务事实表 | 系统自动生成/计算 | 3 |
| `ai_field_mapping_rule` | AI字段入库映射规则 | 配置表 | 必须人工录入 | 27 |
| `ai_parse_field_result` | AI字段抽取结果 | 业务事实表 | 系统自动生成/计算 | 1916 |
| `ai_parse_job` | AI解析任务 | 业务事实表 | 系统自动生成/计算 | 207 |
| `audit_log` | 操作审计日志 | 业务事实表 | 系统自动生成/计算 | 2 |
| `biz_risk_disposal` | Demo ESG 风险处置 | 业务事实表 | 必须人工录入 | 4 |
| `biz_risk_warning` | Demo ESG 风险预警 | 业务事实表 | 系统自动生成/计算 | 6 |
| `cfg_warning_rule` | Demo 风险规则 | 配置表 | 必须人工录入 | 7 |
| `construction_stage_record` | 项目工期主阶段 | 业务事实表 | 必须人工录入 | 5 |
| `dashboard_kpi_detail_snapshot` | 领导层 KPI 详情弹窗快照 | 业务事实表 | 系统自动生成/计算 | 11 |
| `dashboard_panel_snapshot` | 领导层首页面板快照 | 业务事实表 | 系统自动生成/计算 | 1 |
| `dashboard_topic_snapshot` | 领导层专题弹窗快照 | 业务事实表 | 系统自动生成/计算 | 2 |
| `data_ingestion_job` | 数据接入任务表 | 业务事实表 | 系统自动生成/计算 | 91 |
| `data_mapping_rule` | 多源字段映射规则表 | 配置表 | 必须人工录入 | 14 |
| `data_quality_check_result` | 数据质量校验结果表 | 业务事实表 | 系统自动生成/计算 | 92 |
| `data_source_registry` | 数据来源登记表 | 配置表 | 必须人工录入 | 11 |
| `deduplication_record` | 文件去重记录 | 业务事实表 | 系统自动生成/计算 | 39 |
| `dict_document_type` | 资料类型字典 | 配置表 | 必须人工录入 | 11 |
| `dict_esg_module` | ESG模块字典 | 配置表 | 必须人工录入 | 3 |
| `document_record` | 资料主档 | 业务事实表 | 文件上传关联 | 199 |
| `document_task_relation` | 资料任务关联 | 关联表 | 文件上传关联 | 53 |
| `document_version` | 资料版本 | 业务事实表 | 文件上传关联 | 137 |
| `e_case_evidence` | 案件证据 | 关联表 | 文件上传关联 | 29 |
| `e_case_party` | 案件相关方 | 关联表 | 必须人工录入 | 41 |
| `e_case_rectification_link` | 案件-整改任务关联 | 关联表 | 系统自动生成/计算 | 3 |
| `e_case_relation` | 案件关联 | 关联表 | 系统自动生成/计算 | 0 |
| `e_case_status_history` | 案件状态历史 | 业务事实表 | 系统自动生成/计算 | 64 |
| `e_closure_case` | 事项闭环案件 | 业务事实表 | 必须人工录入 | 17 |
| `e_rectification_task` | 整改任务 | 业务事实表 | 必须人工录入 | 3 |
| `engineering_object_phase` | 工程对象阶段 | 关联表 | 必须人工录入 | 4 |
| `esg_demo_indicator_detail` | Demo 指标对象明细 | 业务事实表 | 系统自动生成/计算 | 12 |
| `esg_demo_indicator_result` | Demo 指标结果适配层 | 业务事实表 | 系统自动生成/计算 | 12 |
| `esg_schema_migration_history` | ESG 项目 Schema 迁移历史记录表（V1.1 引导） | 配置表 | 系统自动生成/计算 | 104 |
| `file_asset` | 文件资产 | 业务事实表 | 文件上传关联 | 236 |
| `gis_feature` | GIS要素 | 业务事实表 | 必须人工录入 | 10 |
| `gis_feature_business_relation` | GIS要素业务关联 | 关联表 | 必须人工录入 | 29 |
| `gis_feature_business_summary` | GIS要素业务摘要 | 业务事实表 | 系统自动生成/计算 | 10 |
| `gis_layer` | GIS图层 | 配置表 | 必须人工录入 | 10 |
| `indicator_calculation_job` | 指标计算任务表 | 业务事实表 | 系统自动生成/计算 | 2 |
| `indicator_definition` | 指标定义 | 配置表 | 必须人工录入 | 12 |
| `indicator_history` | 指标历史结果表 | 业务事实表 | 系统自动生成/计算 | 2 |
| `indicator_result` | 指标当前结果 | 业务事实表 | 系统自动生成/计算 | 12 |
| `indicator_snapshot` | 指标/页面快照 | 业务事实表 | 系统自动生成/计算 | 0 |
| `indicator_source_dependency` | 指标数据源依赖表 | 配置表 | 必须人工录入 | 15 |
| `manual_confirmation_log` | 人工确认记录 | 业务事实表 | 必须人工录入 | 181 |
| `monthly_report_chapter` | 月报章节清单 | 配置表 | 必须人工录入 | 6 |
| `monthly_report_cycle` | 月报周期主表 | 配置表 | 必须人工录入 | 1 |
| `monthly_report_gap` | 月报缺项清单 | 业务事实表 | 系统自动生成/计算 | 6 |
| `monthly_report_group_progress` | 月报分组完成进度 | 业务事实表 | 系统自动生成/计算 | 3 |
| `monthly_report_status_chain` | 月报状态链 | 业务事实表 | 系统自动生成/计算 | 5 |
| `monthly_report_task_instance` | 月报资料任务实例统计扩展表 | 业务事实表 | 必须人工录入 | 22 |
| `monthly_report_task_material_link` | 月报任务所需资料及资料关联 | 关联表 | 文件上传关联 | 22 |
| `monthly_report_task_validation` | 月报任务完整性校验与补正记录 | 业务事实表 | 系统自动生成/计算 | 22 |
| `org_unit` | 组织机构 | 配置表 | 必须人工录入 | 5 |
| `project_engineering_object` | 工程对象 | 业务事实表 | 必须人工录入 | 4 |
| `project_phase_period` | 项目阶段周期 | 配置表 | 必须人工录入 | 3 |
| `project_section` | 工程标段 | 配置表 | 必须人工录入 | 3 |
| `review_record` | 审核记录 | 业务事实表 | 必须人工录入 | 61 |
| `review_requirement` | 审核补正要求 | 业务事实表 | 必须人工录入 | 39 |
| `review_timeline` | 审核轨迹 | 业务事实表 | 系统自动生成/计算 | 174 |
| `source_record_trace` | 业务记录来源追溯表 | 业务事实表 | 系统自动生成/计算 | 92 |
| `task_candidate_document` | 任务办理候选关联资料 | 关联表 | 文件上传关联 | 5 |
| `task_match_candidate` | AI候选任务匹配 | 业务事实表 | 系统自动生成/计算 | 205 |
| `task_review_timeline` | 任务办理审核时间线 | 业务事实表 | 系统自动生成/计算 | 201 |
| `upload_task` | 上传任务 | 业务事实表 | 文件上传关联 | 54 |
| `upload_task_requirement` | 上传任务资料要求 | 配置表 | 必须人工录入 | 91 |
| `user_account` | 用户账号 | 配置表 | 必须人工录入 | 5 |
| `workspace_summary` | 工作台摘要快照 | 业务事实表 | 系统自动生成/计算 | 1 |

### 2.5 视图清单（只读，不录入）

| 视图名 | 用途说明 |
|---|---|
| `v_ai_parse_queue_current` | 工作台/资料/解析队列视图 |
| `v_dashboard_kpi_current` | 看板/KPI/风险列表视图 |
| `v_document_summary_current` | 工作台/资料/解析队列视图 |
| `v_e01_configuration_data_nature_inconsistency` | E01 统计或一致性检查视图 |
| `v_e01_core_data_nature_inconsistency` | E01 统计或一致性检查视图 |
| `v_e01_cross_month_retest_trace` | E01 统计或一致性检查视图 |
| `v_e01_event_result_inconsistency` | E01 统计或一致性检查视图 |
| `v_e01_monthly_exceed_count` | E01 统计或一致性检查视图 |
| `v_e01_monthly_exceed_item` | E01 统计或一致性检查视图 |
| `v_e01_open_exceed_count` | E01 统计或一致性检查视图 |
| `v_e01_open_exceed_event` | E01 统计或一致性检查视图 |
| `v_e01_retest_chain_inconsistency` | E01 统计或一致性检查视图 |
| `v_e01_time_quarter_inconsistency` | E01 统计或一致性检查视图 |
| `v_e_case_current_history` | 闭环案件状态视图 |
| `v_e_case_effective_history_leaf` | 闭环案件状态视图 |
| `v_e_case_status_inconsistency` | 闭环案件状态视图 |
| `v_esg_demo_dashboard_kpis` | 首页 Demo KPI 汇总视图 |
| `v_esg_demo_kpi_detail` | 看板/KPI/风险列表视图 |
| `v_esg_demo_risk_list` | 看板/KPI/风险列表视图 |
| `v_task_detail_validation` | VIEW |
| `v_workspace_summary_current` | 工作台/资料/解析队列视图 |

## 3. 人工录入数据范围（给模板设计）

### A. 必须人工录入（或由业务人员确认后入库）

| 业务主题 | 建议主表 | Excel 模板建议 |
|---|---|---|
| 环境监测点与结果 | `e01_monitor_point` / `e01_factor_result` / `biz_env_monitor_*` | 一表一点位主数据；一表一批次/因子结果 |
| 环保问题 | `env_issue_record` | 问题编号、位置、类型、责任单位、状态、期限 |
| 水保复绿 / E02 对象 | `water_protection_issue`、`biz_soil_disposal_site`、`biz_temporary_land_use`、`biz_topsoil_stripping`、`biz_construction_slope` | 按对象类型分 Sheet |
| 生态与文物 | `biz_ecological_*`、`biz_cultural_relic_object` | 对象清单 + 状态 + 责任单位 |
| 碳相关活动/材料/措施 | `carbon_emission_activity`、`carbon_material_usage`、`carbon_reduction_measure` | 月度活动量、材料量、措施成效分表 |
| 安全风险点 / 事故 | `safety_risk_point`、`safety_incident_record` | 风险点台账；事故台账（当前事故表 0 行） |
| 连续安全生产确认 | `s01_confirmation_batch`、`safety_production_record` | 建设单位确认批次；起算/统计日期 |
| 劳务与工资 | `labor_dispute_record`、`biz_worker_payment_summary`、`salary_payment_record` | 纠纷事项；周期汇总（优先）；明细表可空 |
| 群众诉求 | `appeal_record` | 诉求编号、类型、受理、办结 |
| 审批许可 / 专项方案 | `compliance_procedure`、`permit_record`、`special_plan_approval` | 手续过程、许可证、专项方案审批分表 |
| 设计变更 / 内控问题 / 夜施 | `biz_design_change`、`biz_internal_control_issue`、`biz_night_construction_record` | 独立 Sheet |
| 闭环案件与整改完成填报 | `e_closure_case`、`e_rectification_task` | 案件主信息；整改完成日期/填报人必须由甲方填写 |
| 组织标段 | `org_unit`、`project_section` | 主数据，模板下拉来源 |

### B. 系统自动生成（不要作为主录入表）

| 类型 | 代表对象 | 说明 |
|---|---|---|
| KPI / 指标结果 | `indicator_result`、`esg_demo_indicator_result`、`v_esg_demo_dashboard_kpis` | 由规则/任务计算，禁止手工改首页口径 |
| 红黄蓝/风险列表 | `biz_risk_warning`、`cfg_warning_rule`、相关视图 | 规则触发或系统汇总 |
| 超标事件推导 | `e01_exceed_event` | 可由监测结果与限值比较生成后人工确认 |
| 状态轨迹 | `e_case_status_history`、`review_timeline` | 流程自动落库 |
| AI 抽取结果 | `ai_parse_*`、`ai_extracted_*` | 需人工确认后再写业务表 |
| Dashboard 快照 | `dashboard_*_snapshot` | 展示缓存 |

### C. 文件上传关联

| 资料类型 | 建议挂接 | 关键表 |
|---|---|---|
| 批复 / 许可扫描件 | `permit_record` / `compliance_procedure` / `special_plan_approval` | `approval_file_id` 或资料关联表 → `file_asset` |
| 检测报告 | E01 批次/样品/复测 | `source_file_id`、`source_document_id`、`report_document_id` |
| 整改证明 | `e_case_evidence`、`rectification_record`、上传任务 | 证据类型 + 文件 ID |
| 图片 / 现场影像 | `file_asset` + 业务关联 | 先上传文件，再填业务表文件 ID 或走工作台关联 |

**录入原则：** Excel 只设计 A/C 类字段；B 类由系统生成后用于核对，不要求业务人员在 Excel 中维护。

## 4. 重点外键关系（真实库）

| 主表 | 字段 | 关联表 | 关联字段 | 用途 |
|---|---|---|---|---|
| `e01_exceed_event` | `case_id` | `e_closure_case` | `id` | 闭环事项关联 |
| `e01_exceed_event` | `original_result_id` | `e01_factor_result` | `id` | 业务关联 |
| `e01_factor_result` | `factor_id` | `e01_factor_definition` | `id` | 业务关联 |
| `e01_factor_result` | `sample_id` | `e01_monitor_sample` | `id` | 业务关联 |
| `e01_factor_result` | `standard_version_id` | `e01_standard_version` | `id` | 业务关联 |
| `e01_monitor_batch` | `source_document_id` | `document_record` | `id` | 资料记录关联 |
| `e01_monitor_batch` | `source_file_id` | `file_asset` | `id` | 文件资料关联 |
| `e01_monitor_batch` | `ingestion_job_id` | `data_ingestion_job` | `id` | 业务关联 |
| `e01_monitor_batch` | `plan_id` | `e01_monitor_plan` | `id` | 业务关联 |
| `e01_monitor_batch` | `testing_provider_org_id` | `org_unit` | `id` | 组织单位关联 |
| `e01_monitor_point` | `coordinate_source_document_id` | `document_record` | `id` | 资料记录关联 |
| `e01_monitor_point` | `gis_feature_id` | `gis_feature` | `id` | GIS 空间关联 |
| `e_case_evidence` | `case_id` | `e_closure_case` | `id` | 闭环事项关联 |
| `e_case_evidence` | `document_id` | `document_record` | `id` | 资料记录关联 |
| `e_case_evidence` | `file_id` | `file_asset` | `id` | 文件资料关联 |
| `e_case_evidence` | `status_history_id` | `e_case_status_history` | `id` | 业务关联 |
| `e_closure_case` | `close_org_id` | `org_unit` | `id` | 组织单位关联 |
| `e_closure_case` | `current_status_history_id` | `e_case_status_history` | `id` | 业务关联 |
| `e_closure_case` | `discovery_org_id` | `org_unit` | `id` | 组织单位关联 |
| `e_closure_case` | `gis_feature_id` | `gis_feature` | `id` | GIS 空间关联 |
| `e_closure_case` | `merged_into_case_id` | `e_closure_case` | `id` | 闭环事项关联 |
| `e_closure_case` | `responsible_org_id` | `org_unit` | `id` | 组织单位关联 |
| `e_closure_case` | `review_org_id` | `org_unit` | `id` | 组织单位关联 |
| `e_closure_case` | `source_document_id` | `document_record` | `id` | 资料记录关联 |
| `e_rectification_task` | `rectification_completed_by` | `user_account` | `id` | 用户账号关联 |
| `e_rectification_task` | `responsible_org_id` | `org_unit` | `id` | 组织单位关联 |
| `gis_feature_business_relation` | `feature_id` | `gis_feature` | `id` | GIS 空间关联 |
| `special_plan_approval` | `approval_file_id` | `file_asset` | `id` | 文件资料关联 |
| `special_plan_approval` | `risk_point_id` | `safety_risk_point` | `id` | 风险/预警关联 |
| `ai_extracted_environment` | `analysis_id` | `ai_document_analysis` | `id` | 业务关联 |
| `ai_extracted_progress` | `analysis_id` | `ai_document_analysis` | `id` | 业务关联 |
| `ai_extracted_project_info` | `analysis_id` | `ai_document_analysis` | `id` | 业务关联 |
| `ai_extracted_resource` | `analysis_id` | `ai_document_analysis` | `id` | 业务关联 |
| `ai_extracted_safety` | `analysis_id` | `ai_document_analysis` | `id` | 业务关联 |
| `carbon_emission_factor_snapshot` | `factor_id` | `carbon_emission_factor` | `id` | 业务关联 |
| `carbon_emission_segment_detail` | `emission_factor_id` | `carbon_emission_factor` | `id` | 业务关联 |
| `carbon_measure_monthly_performance` | `measure_id` | `carbon_reduction_measure` | `id` | 业务关联 |
| `carbon_reduction_accounting` | `baseline_id` | `carbon_emission_baseline` | `id` | 业务关联 |
| `e01_monitor_plan` | `plan_document_id` | `document_record` | `id` | 资料记录关联 |
| `e01_monitor_plan` | `owner_department_org_id` | `org_unit` | `id` | 组织单位关联 |
| `e01_monitor_plan` | `testing_provider_org_id` | `org_unit` | `id` | 组织单位关联 |
| `e01_monitor_plan_item` | `plan_id` | `e01_monitor_plan` | `id` | 业务关联 |
| `e01_monitor_plan_item` | `point_id` | `e01_monitor_point` | `id` | 业务关联 |
| `e01_monitor_sample` | `batch_id` | `e01_monitor_batch` | `id` | 业务关联 |
| `e01_monitor_sample` | `duplicate_of_sample_id` | `e01_monitor_sample` | `id` | 业务关联 |
| `e01_monitor_sample` | `plan_item_id` | `e01_monitor_plan_item` | `id` | 业务关联 |
| `e01_monitor_sample` | `point_id` | `e01_monitor_point` | `id` | 业务关联 |
| `e01_monitor_sample` | `raw_record_document_id` | `document_record` | `id` | 资料记录关联 |
| `e01_rectification_round` | `event_id` | `e01_exceed_event` | `id` | 业务关联 |
| `e01_rectification_round` | `task_id` | `e_rectification_task` | `id` | 业务关联 |
| `e01_retest_result_link` | `event_id` | `e01_exceed_event` | `id` | 业务关联 |
| `e01_retest_result_link` | `original_result_id` | `e01_factor_result` | `id` | 业务关联 |
| `e01_retest_result_link` | `factor_result_id` | `e01_factor_result` | `id` | 业务关联 |
| `e01_retest_result_link` | `retest_round_id` | `e01_retest_round` | `id` | 业务关联 |
| `e01_retest_round` | `retest_batch_id` | `e01_monitor_batch` | `id` | 业务关联 |
| `e01_retest_round` | `report_document_id` | `document_record` | `id` | 资料记录关联 |
| `e01_retest_round` | `event_id` | `e01_exceed_event` | `id` | 业务关联 |
| `e01_standard_limit` | `factor_id` | `e01_factor_definition` | `id` | 业务关联 |
| `e01_standard_limit` | `standard_version_id` | `e01_standard_version` | `id` | 业务关联 |
| `e01_standard_version` | `source_document_id` | `document_record` | `id` | 资料记录关联 |
| `e_case_party` | `case_id` | `e_closure_case` | `id` | 闭环事项关联 |
| `e_case_party` | `org_id` | `org_unit` | `id` | 组织单位关联 |
| `e_case_rectification_link` | `case_id` | `e_closure_case` | `id` | 闭环事项关联 |
| `e_case_rectification_link` | `task_id` | `e_rectification_task` | `id` | 业务关联 |
| `e_case_relation` | `from_case_id` | `e_closure_case` | `id` | 闭环事项关联 |
| `e_case_relation` | `to_case_id` | `e_closure_case` | `id` | 闭环事项关联 |
| `e_case_status_history` | `case_id` | `e_closure_case` | `id` | 闭环事项关联 |
| `e_case_status_history` | `correction_of_history_id` | `e_case_status_history` | `id` | 业务关联 |
| `e_case_status_history` | `source_document_id` | `document_record` | `id` | 资料记录关联 |
| `engineering_object_phase` | `object_id` | `project_engineering_object` | `id` | 业务关联 |
| `engineering_object_phase` | `phase_id` | `project_phase_period` | `id` | 业务关联 |
| `gis_feature` | `layer_id` | `gis_layer` | `id` | 业务关联 |
| `gis_feature_business_summary` | `feature_id` | `gis_feature` | `id` | GIS 空间关联 |
| `monitor_frequency_rule` | `plan_item_id` | `e01_monitor_plan_item` | `id` | 业务关联 |
| `monitor_point_object_relation` | `object_id` | `project_engineering_object` | `id` | 业务关联 |
| `monitor_point_object_relation` | `object_phase_id` | `engineering_object_phase` | `id` | 业务关联 |
| `monitor_point_object_relation` | `phase_id` | `project_phase_period` | `id` | 业务关联 |
| `monitor_point_object_relation` | `point_id` | `e01_monitor_point` | `id` | 业务关联 |
| `monitor_point_object_relation` | `section_id` | `project_section` | `id` | 业务关联 |
| `monthly_report_task_instance` | `report_cycle_id` | `monthly_report_cycle` | `id` | 业务关联 |
| `monthly_report_task_material_link` | `task_instance_id` | `monthly_report_task_instance` | `id` | 业务关联 |
| `monthly_report_task_validation` | `task_instance_id` | `monthly_report_task_instance` | `id` | 业务关联 |
| `project_engineering_object` | `gis_feature_id` | `gis_feature` | `id` | GIS 空间关联 |
| `project_engineering_object` | `section_id` | `project_section` | `id` | 业务关联 |

### 4.1 GIS 关联字段重点

| 表 | 字段 | 类型 | 说明 |
|---|---|---|---|
| `biz_cultural_relic_object` | `longitude` | `decimal(12,8)` | GIS/坐标相关字段 |
| `biz_cultural_relic_object` | `latitude` | `decimal(12,8)` | GIS/坐标相关字段 |
| `biz_env_monitor_point` | `longitude` | `decimal(10,7)` | GIS/坐标相关字段 |
| `biz_env_monitor_point` | `latitude` | `decimal(10,7)` | GIS/坐标相关字段 |
| `biz_soil_disposal_site` | `longitude` | `decimal(10,7)` | GIS/坐标相关字段 |
| `biz_soil_disposal_site` | `latitude` | `decimal(10,7)` | GIS/坐标相关字段 |
| `e01_monitor_point` | `longitude` | `decimal(11,8)` | GIS/坐标相关字段 |
| `e01_monitor_point` | `latitude` | `decimal(10,8)` | GIS/坐标相关字段 |
| `e01_monitor_point` | `gis_feature_id` | `varchar(96)` | GIS/坐标相关字段 |
| `e_closure_case` | `gis_feature_id` | `varchar(96)` | GIS/坐标相关字段 |
| `project_engineering_object` | `longitude` | `decimal(11,8)` | GIS/坐标相关字段 |
| `project_engineering_object` | `latitude` | `decimal(10,8)` | GIS/坐标相关字段 |
| `project_engineering_object` | `gis_feature_id` | `varchar(96)` | GIS/坐标相关字段 |

## 5. 索引设计（真实库）

下列为全部基表索引汇总（含主键/唯一/普通索引）。

| 表 | 索引名称 | 字段 | 用途 |
|---|---|---|---|
| `ai_document_analysis` | `PRIMARY` | `id` | 主键 |
| `ai_document_analysis` | `idx_ai_document_period_status` | `report_period, analysis_status` | 查询索引（report_period,analysis_status） |
| `ai_document_analysis` | `idx_ai_document_source_file` | `source_file_id` | 查询索引（source_file_id） |
| `ai_extracted_environment` | `PRIMARY` | `id` | 主键 |
| `ai_extracted_environment` | `uk_ai_environment_analysis` | `analysis_id` | 唯一约束（analysis_id） |
| `ai_extracted_progress` | `PRIMARY` | `id` | 主键 |
| `ai_extracted_progress` | `idx_ai_progress_analysis` | `analysis_id` | 查询索引（analysis_id） |
| `ai_extracted_progress` | `idx_ai_progress_period_section` | `period, section_code` | 查询索引（period,section_code） |
| `ai_extracted_project_info` | `PRIMARY` | `id` | 主键 |
| `ai_extracted_project_info` | `uk_ai_project_analysis` | `analysis_id` | 唯一约束（analysis_id） |
| `ai_extracted_resource` | `PRIMARY` | `id` | 主键 |
| `ai_extracted_resource` | `uk_ai_resource_analysis` | `analysis_id` | 唯一约束（analysis_id） |
| `ai_extracted_safety` | `PRIMARY` | `id` | 主键 |
| `ai_extracted_safety` | `uk_ai_safety_analysis` | `analysis_id` | 唯一约束（analysis_id） |
| `ai_field_mapping_rule` | `PRIMARY` | `id` | 主键 |
| `ai_field_mapping_rule` | `idx_mapping_doc_field` | `document_type, field_key, enabled` | 查询索引（document_type,field_key,enabled） |
| `ai_field_mapping_rule` | `uk_mapping_doc_field` | `document_type, field_key, target_table, target_column` | 唯一约束（document_type,field_key,target_table,target_column） |
| `ai_parse_field_result` | `PRIMARY` | `id` | 主键 |
| `ai_parse_field_result` | `idx_parse_field_confirm` | `confirm_status` | 查询索引（confirm_status） |
| `ai_parse_field_result` | `idx_parse_field_job` | `parse_job_id` | 查询索引（parse_job_id） |
| `ai_parse_field_result` | `idx_parse_field_key` | `field_key` | 查询索引（field_key） |
| `ai_parse_job` | `PRIMARY` | `id` | 主键 |
| `ai_parse_job` | `idx_parse_job_file` | `file_id` | 查询索引（file_id） |
| `ai_parse_job` | `idx_parse_job_status` | `job_status` | 查询索引（job_status） |
| `ai_parse_job` | `job_code` | `job_code` | 唯一约束（job_code） |
| `appeal_record` | `PRIMARY` | `id` | 主键 |
| `appeal_record` | `idx_appeal_status` | `status` | 查询索引（status） |
| `audit_log` | `PRIMARY` | `id` | 主键 |
| `audit_log` | `idx_audit_entity` | `entity_type, entity_id` | 查询索引（entity_type,entity_id） |
| `audit_log` | `idx_audit_operator` | `operator_id, created_at` | 查询索引（operator_id,created_at） |
| `biz_construction_slope` | `PRIMARY` | `id` | 主键 |
| `biz_construction_slope` | `idx_demo_slope_status` | `project_id, stability_status, risk_status` | 查询索引（project_id,stability_status,risk_status） |
| `biz_construction_slope` | `uk_demo_slope` | `project_id, object_code` | 唯一约束（project_id,object_code） |
| `biz_cultural_relic_object` | `PRIMARY` | `id` | 主键 |
| `biz_cultural_relic_object` | `idx_biz_cultural_relic_risk` | `risk_status` | 查询索引（risk_status） |
| `biz_cultural_relic_object` | `idx_biz_cultural_relic_section` | `section_id` | 查询索引（section_id） |
| `biz_cultural_relic_object` | `uk_biz_cultural_relic_code` | `project_id, relic_code` | 唯一约束（project_id,relic_code） |
| `biz_design_change` | `PRIMARY` | `id` | 主键 |
| `biz_design_change` | `idx_demo_design_change_status` | `project_id, approve_status, implementation_status, risk_status` | 查询索引（project_id,approve_status,implementation_status,risk_status） |
| `biz_design_change` | `uk_demo_design_change` | `project_id, change_code` | 唯一约束（project_id,change_code） |
| `biz_ecological_protection_object` | `PRIMARY` | `id` | 主键 |
| `biz_ecological_protection_object` | `idx_demo_eco_object_status` | `project_id, inspection_status, risk_status` | 查询索引（project_id,inspection_status,risk_status） |
| `biz_ecological_protection_object` | `uk_demo_eco_object` | `project_id, object_code` | 唯一约束（project_id,object_code） |
| `biz_ecological_sensitive_area` | `PRIMARY` | `id` | 主键 |
| `biz_ecological_sensitive_area` | `idx_demo_sensitive_status` | `project_id, monitoring_status, risk_status` | 查询索引（project_id,monitoring_status,risk_status） |
| `biz_ecological_sensitive_area` | `uk_demo_sensitive_area` | `project_id, object_code` | 唯一约束（project_id,object_code） |
| `biz_env_monitor_point` | `PRIMARY` | `id` | 主键 |
| `biz_env_monitor_point` | `uk_demo_env_point` | `project_id, point_code` | 唯一约束（project_id,point_code） |
| `biz_env_monitor_result` | `PRIMARY` | `id` | 主键 |
| `biz_env_monitor_result` | `idx_demo_env_result_point` | `project_id, point_id, judgement` | 查询索引（project_id,point_id,judgement） |
| `biz_internal_control_issue` | `PRIMARY` | `id` | 主键 |
| `biz_internal_control_issue` | `idx_demo_control_issue_status` | `project_id, current_status, issue_level, risk_status` | 查询索引（project_id,current_status,issue_level,risk_status） |
| `biz_internal_control_issue` | `uk_demo_control_issue` | `project_id, issue_code` | 唯一约束（project_id,issue_code） |
| `biz_night_construction_record` | `PRIMARY` | `id` | 主键 |
| `biz_night_construction_record` | `idx_demo_night_status` | `project_id, construction_date, permit_status, risk_status` | 查询索引（project_id,construction_date,permit_status,risk_status） |
| `biz_night_construction_record` | `uk_demo_night_record` | `project_id, record_code` | 唯一约束（project_id,record_code） |
| `biz_risk_disposal` | `PRIMARY` | `id` | 主键 |
| `biz_risk_disposal` | `idx_demo_disposal_warning` | `warning_id, disposal_status` | 查询索引（warning_id,disposal_status） |
| `biz_risk_warning` | `PRIMARY` | `id` | 主键 |
| `biz_risk_warning` | `idx_demo_warning_list` | `project_id, status, warning_level, kpi_key` | 查询索引（project_id,status,warning_level,kpi_key） |
| `biz_risk_warning` | `idx_demo_warning_object` | `object_type, object_id` | 查询索引（object_type,object_id） |
| `biz_risk_warning` | `uk_demo_warning_code` | `warning_code` | 唯一约束（warning_code） |
| `biz_soil_disposal_site` | `PRIMARY` | `id` | 主键 |
| `biz_soil_disposal_site` | `idx_demo_soil_site_status` | `project_id, disposal_status, risk_status` | 查询索引（project_id,disposal_status,risk_status） |
| `biz_soil_disposal_site` | `uk_demo_soil_site` | `project_id, object_code` | 唯一约束（project_id,object_code） |
| `biz_temporary_land_use` | `PRIMARY` | `id` | 主键 |
| `biz_temporary_land_use` | `idx_demo_temp_land_status` | `project_id, approval_status, restore_status, risk_status` | 查询索引（project_id,approval_status,restore_status,risk_status） |
| `biz_temporary_land_use` | `uk_demo_temp_land` | `project_id, object_code` | 唯一约束（project_id,object_code） |
| `biz_topsoil_stripping` | `PRIMARY` | `id` | 主键 |
| `biz_topsoil_stripping` | `idx_demo_topsoil_status` | `project_id, current_status, risk_status` | 查询索引（project_id,current_status,risk_status） |
| `biz_topsoil_stripping` | `uk_demo_topsoil` | `project_id, object_code` | 唯一约束（project_id,object_code） |
| `biz_worker_payment_summary` | `PRIMARY` | `id` | 主键 |
| `biz_worker_payment_summary` | `idx_demo_payment_status` | `project_id, payment_status, risk_status` | 查询索引（project_id,payment_status,risk_status） |
| `biz_worker_payment_summary` | `uk_demo_payment_period` | `project_id, section_id, period_start, period_end` | 唯一约束（project_id,section_id,period_start,period_end） |
| `carbon_accounting_batch` | `PRIMARY` | `id` | 主键 |
| `carbon_accounting_batch` | `batch_code` | `batch_code` | 唯一约束（batch_code） |
| `carbon_accounting_batch` | `idx_batch_boundary` | `boundary_version` | 查询索引（boundary_version） |
| `carbon_accounting_batch` | `idx_batch_current` | `is_current, data_nature` | 查询索引（is_current,data_nature） |
| `carbon_accounting_batch` | `idx_batch_nature` | `data_nature` | 查询索引（data_nature） |
| `carbon_accounting_boundary` | `PRIMARY` | `id` | 主键 |
| `carbon_accounting_boundary` | `idx_boundary_nature` | `data_nature` | 查询索引（data_nature） |
| `carbon_accounting_boundary` | `idx_boundary_status` | `boundary_status` | 查询索引（boundary_status） |
| `carbon_accounting_boundary` | `idx_boundary_version` | `boundary_version` | 查询索引（boundary_version） |
| `carbon_accounting_boundary` | `uk_boundary_version_source` | `boundary_version, source_code` | 唯一约束（boundary_version,source_code） |
| `carbon_accounting_evidence_link` | `PRIMARY` | `id` | 主键 |
| `carbon_accounting_evidence_link` | `idx_carbon_evidence_document` | `document_id` | 查询索引（document_id） |
| `carbon_accounting_evidence_link` | `uk_carbon_evidence_business_document` | `business_type, business_id, document_id` | 唯一约束（business_type,business_id,document_id） |
| `carbon_emission_activity` | `PRIMARY` | `id` | 主键 |
| `carbon_emission_activity` | `idx_carbon_period` | `period_value` | 查询索引（period_value） |
| `carbon_emission_baseline` | `PRIMARY` | `id` | 主键 |
| `carbon_emission_baseline` | `idx_carbon_baseline_demo` | `is_demo, data_nature` | 查询索引（is_demo,data_nature） |
| `carbon_emission_baseline` | `uk_carbon_baseline_code` | `baseline_code` | 唯一约束（baseline_code） |
| `carbon_emission_baseline` | `uk_carbon_baseline_period_boundary` | `accounting_period, boundary_code` | 唯一约束（accounting_period,boundary_code） |
| `carbon_emission_factor` | `PRIMARY` | `id` | 主键 |
| `carbon_emission_factor` | `factor_code` | `factor_code` | 唯一约束（factor_code） |
| `carbon_emission_factor` | `idx_carbon_factor_nature` | `data_nature` | 查询索引（data_nature） |
| `carbon_emission_factor_snapshot` | `PRIMARY` | `id` | 主键 |
| `carbon_emission_factor_snapshot` | `idx_factor_snapshot_code` | `snapshot_code` | 查询索引（snapshot_code） |
| `carbon_emission_factor_snapshot` | `idx_factor_snapshot_factor` | `factor_id` | 查询索引（factor_id） |
| `carbon_emission_factor_snapshot` | `snapshot_code` | `snapshot_code` | 唯一约束（snapshot_code） |
| `carbon_emission_segment_detail` | `PRIMARY` | `id` | 主键 |
| `carbon_emission_segment_detail` | `fk_carbon_segment_factor` | `emission_factor_id` | 外键索引（emission_factor_id） |
| `carbon_emission_segment_detail` | `idx_carbon_segment_month` | `accounting_month, segment_sort_order, source_sort_order` | 查询索引（accounting_month,segment_sort_order,source_sort_order） |
| `carbon_emission_segment_detail` | `idx_carbon_segment_source` | `emission_source_code, material_type_code` | 查询索引（emission_source_code,material_type_code） |
| `carbon_emission_segment_detail` | `uk_carbon_segment_detail_code` | `detail_code` | 唯一约束（detail_code） |
| `carbon_emission_segment_detail` | `uk_carbon_segment_dimension` | `accounting_month, segment_code, emission_source_code, material_type_code, boundary_code` | 唯一约束（accounting_month,segment_code,emission_source_code,material_type_code,boundary_code） |
| `carbon_material_usage` | `PRIMARY` | `id` | 主键 |
| `carbon_material_usage` | `idx_carbon_material_period` | `period_value` | 查询索引（period_value） |
| `carbon_measure_monthly_performance` | `PRIMARY` | `id` | 主键 |
| `carbon_measure_monthly_performance` | `uk_carbon_performance_code` | `performance_code` | 唯一约束（performance_code） |
| `carbon_measure_monthly_performance` | `uk_carbon_performance_measure_month` | `measure_id, accounting_month` | 唯一约束（measure_id,accounting_month） |
| `carbon_reduction_accounting` | `PRIMARY` | `id` | 主键 |
| `carbon_reduction_accounting` | `idx_carbon_reduction_baseline` | `baseline_id` | 查询索引（baseline_id） |
| `carbon_reduction_accounting` | `uk_carbon_reduction_code` | `accounting_code` | 唯一约束（accounting_code） |
| `carbon_reduction_accounting` | `uk_carbon_reduction_month_boundary` | `accounting_month, boundary_code` | 唯一约束（accounting_month,boundary_code） |
| `carbon_reduction_measure` | `PRIMARY` | `id` | 主键 |
| `carbon_reduction_measure` | `idx_carbon_measure_demo` | `is_demo, data_nature` | 查询索引（is_demo,data_nature） |
| `carbon_reduction_measure` | `idx_carbon_measure_status` | `implementation_status` | 查询索引（implementation_status） |
| `carbon_reduction_measure` | `uk_carbon_measure_code` | `measure_code` | 唯一约束（measure_code） |
| `cfg_warning_rule` | `PRIMARY` | `id` | 主键 |
| `cfg_warning_rule` | `idx_demo_warning_rule_kpi` | `kpi_key, enabled` | 查询索引（kpi_key,enabled） |
| `cfg_warning_rule` | `uk_demo_warning_rule` | `rule_code, version_no` | 唯一约束（rule_code,version_no） |
| `compliance_material_gap` | `PRIMARY` | `id` | 主键 |
| `compliance_material_gap` | `idx_material_gap_status` | `status` | 查询索引（status） |
| `compliance_procedure` | `PRIMARY` | `id` | 主键 |
| `compliance_procedure` | `idx_compliance_status` | `status` | 查询索引（status） |
| `construction_stage_record` | `PRIMARY` | `id` | 主键 |
| `construction_stage_record` | `idx_csr_project_current` | `project_id, stage_status, is_current` | 查询索引（project_id,stage_status,is_current） |
| `construction_stage_record` | `idx_csr_sequence` | `sequence_no` | 查询索引（sequence_no） |
| `construction_stage_record` | `idx_csr_stage_status` | `stage_status` | 查询索引（stage_status） |
| `construction_stage_record` | `uk_construction_stage_key` | `stage_key` | 唯一约束（stage_key） |
| `dashboard_kpi_detail_snapshot` | `PRIMARY` | `indicator_code` | 主键 |
| `dashboard_panel_snapshot` | `PRIMARY` | `panel_key` | 主键 |
| `dashboard_topic_snapshot` | `PRIMARY` | `topic_key` | 主键 |
| `data_ingestion_job` | `PRIMARY` | `id` | 主键 |
| `data_ingestion_job` | `idx_ingestion_source` | `source_id, created_at` | 查询索引（source_id,created_at） |
| `data_ingestion_job` | `idx_ingestion_status` | `job_status, created_at` | 查询索引（job_status,created_at） |
| `data_ingestion_job` | `idx_ingestion_target` | `target_table, created_at` | 查询索引（target_table,created_at） |
| `data_mapping_rule` | `PRIMARY` | `id` | 主键 |
| `data_mapping_rule` | `idx_mapping_source` | `source_id, source_object` | 查询索引（source_id,source_object） |
| `data_mapping_rule` | `idx_mapping_target` | `target_table` | 查询索引（target_table） |
| `data_quality_check_result` | `PRIMARY` | `id` | 主键 |
| `data_quality_check_result` | `idx_quality_job` | `ingestion_job_id` | 查询索引（ingestion_job_id） |
| `data_quality_check_result` | `idx_quality_status` | `check_status` | 查询索引（check_status） |
| `data_quality_check_result` | `idx_quality_target` | `target_table, target_record_id` | 查询索引（target_table,target_record_id） |
| `data_source_registry` | `PRIMARY` | `id` | 主键 |
| `data_source_registry` | `source_code` | `source_code` | 唯一约束（source_code） |
| `deduplication_record` | `PRIMARY` | `id` | 主键 |
| `deduplication_record` | `idx_dedup_file` | `file_id` | 查询索引（file_id） |
| `deduplication_record` | `idx_dedup_status` | `decision_status` | 查询索引（decision_status） |
| `dict_document_type` | `PRIMARY` | `id` | 主键 |
| `dict_document_type` | `idx_doc_type_module` | `module_code` | 查询索引（module_code） |
| `dict_document_type` | `type_code` | `type_code` | 唯一约束（type_code） |
| `dict_esg_module` | `PRIMARY` | `module_code` | 主键 |
| `document_record` | `PRIMARY` | `id` | 主键 |
| `document_record` | `document_code` | `document_code` | 唯一约束（document_code） |
| `document_record` | `idx_document_module` | `module_code` | 查询索引（module_code） |
| `document_record` | `idx_document_period` | `period_value` | 查询索引（period_value） |
| `document_record` | `idx_document_status` | `document_status, validity_status` | 查询索引（document_status,validity_status） |
| `document_record` | `idx_document_type` | `document_type` | 查询索引（document_type） |
| `document_task_relation` | `PRIMARY` | `id` | 主键 |
| `document_task_relation` | `idx_relation_status` | `relation_status` | 查询索引（relation_status） |
| `document_task_relation` | `idx_relation_task` | `task_id` | 查询索引（task_id） |
| `document_task_relation` | `uk_doc_task` | `document_id, task_id` | 唯一约束（document_id,task_id） |
| `document_version` | `PRIMARY` | `id` | 主键 |
| `document_version` | `idx_doc_version_current` | `document_id, is_current` | 查询索引（document_id,is_current） |
| `document_version` | `idx_doc_version_doc` | `document_id` | 查询索引（document_id） |
| `e01_exceed_event` | `PRIMARY` | `id` | 主键 |
| `e01_exceed_event` | `fk_e01_event_original` | `original_result_id` | 外键索引（original_result_id） |
| `e01_exceed_event` | `idx_e01_event_open` | `effective_status, data_nature, is_demo, current_retest_round` | 查询索引（effective_status,data_nature,is_demo,current_retest_round） |
| `e01_exceed_event` | `uk_e01_event_active_result` | `active_original_result_id` | 唯一约束（active_original_result_id） |
| `e01_exceed_event` | `uk_e01_event_case` | `case_id` | 唯一约束（case_id） |
| `e01_exceed_event` | `uk_e01_event_code` | `event_code` | 唯一约束（event_code） |
| `e01_factor_definition` | `PRIMARY` | `id` | 主键 |
| `e01_factor_definition` | `uk_e01_factor_code` | `factor_code` | 唯一约束（factor_code） |
| `e01_factor_result` | `PRIMARY` | `id` | 主键 |
| `e01_factor_result` | `fk_e01_factor_result_standard` | `standard_version_id` | 外键索引（standard_version_id） |
| `e01_factor_result` | `idx_e01_factor_result_factor` | `factor_id, standard_version_id` | 查询索引（factor_id,standard_version_id） |
| `e01_factor_result` | `idx_e01_factor_result_kpi` | `test_stage, judgement, result_validity, effective_status, data_nature, is_demo` | 查询索引（test_stage,judgement,result_validity,effective_status,data_nature,is_demo） |
| `e01_factor_result` | `idx_e01_factor_result_sample` | `sample_id, test_stage, data_nature, is_demo` | 查询索引（sample_id,test_stage,data_nature,is_demo） |
| `e01_factor_result` | `uk_e01_factor_result_code` | `result_code` | 唯一约束（result_code） |
| `e01_legacy_record_mapping` | `PRIMARY` | `id` | 主键 |
| `e01_legacy_record_mapping` | `uk_e01_legacy_mapping` | `legacy_table, legacy_record_id, target_table, target_record_id, migration_version` | 唯一约束（legacy_table,legacy_record_id,target_table,target_record_id,migration_version） |
| `e01_monitor_batch` | `PRIMARY` | `id` | 主键 |
| `e01_monitor_batch` | `fk_e01_batch_document` | `source_document_id` | 外键索引（source_document_id） |
| `e01_monitor_batch` | `fk_e01_batch_file` | `source_file_id` | 外键索引（source_file_id） |
| `e01_monitor_batch` | `fk_e01_batch_job` | `ingestion_job_id` | 外键索引（ingestion_job_id） |
| `e01_monitor_batch` | `fk_e01_batch_plan` | `plan_id` | 外键索引（plan_id） |
| `e01_monitor_batch` | `fk_e01_batch_provider` | `testing_provider_org_id` | 外键索引（testing_provider_org_id） |
| `e01_monitor_batch` | `idx_e01_batch_quarter` | `quarter_code, effective_status, data_nature` | 查询索引（quarter_code,effective_status,data_nature） |
| `e01_monitor_batch` | `uk_e01_batch_code` | `batch_code` | 唯一约束（batch_code） |
| `e01_monitor_batch` | `uk_e01_batch_idempotency` | `idempotency_key` | 唯一约束（idempotency_key） |
| `e01_monitor_plan` | `PRIMARY` | `id` | 主键 |
| `e01_monitor_plan` | `fk_e01_plan_document` | `plan_document_id` | 外键索引（plan_document_id） |
| `e01_monitor_plan` | `fk_e01_plan_owner` | `owner_department_org_id` | 外键索引（owner_department_org_id） |
| `e01_monitor_plan` | `fk_e01_plan_provider` | `testing_provider_org_id` | 外键索引（testing_provider_org_id） |
| `e01_monitor_plan` | `uk_e01_plan_code` | `plan_code` | 唯一约束（plan_code） |
| `e01_monitor_plan_item` | `PRIMARY` | `id` | 主键 |
| `e01_monitor_plan_item` | `fk_e01_plan_item_point` | `point_id` | 外键索引（point_id） |
| `e01_monitor_plan_item` | `uk_e01_plan_item` | `plan_id, point_id, monitor_category` | 唯一约束（plan_id,point_id,monitor_category） |
| `e01_monitor_point` | `PRIMARY` | `id` | 主键 |
| `e01_monitor_point` | `fk_e01_point_coordinate_doc` | `coordinate_source_document_id` | 外键索引（coordinate_source_document_id） |
| `e01_monitor_point` | `idx_e01_point_gis` | `gis_feature_id` | 查询索引（gis_feature_id） |
| `e01_monitor_point` | `uk_e01_point_code` | `point_code` | 唯一约束（point_code） |
| `e01_monitor_sample` | `PRIMARY` | `id` | 主键 |
| `e01_monitor_sample` | `fk_e01_sample_batch` | `batch_id` | 外键索引（batch_id） |
| `e01_monitor_sample` | `fk_e01_sample_duplicate` | `duplicate_of_sample_id` | 外键索引（duplicate_of_sample_id） |
| `e01_monitor_sample` | `fk_e01_sample_plan_item` | `plan_item_id` | 外键索引（plan_item_id） |
| `e01_monitor_sample` | `fk_e01_sample_point` | `point_id` | 外键索引（point_id） |
| `e01_monitor_sample` | `fk_e01_sample_raw_doc` | `raw_record_document_id` | 外键索引（raw_record_document_id） |
| `e01_monitor_sample` | `idx_e01_sample_kpi` | `sampled_at, monitor_category, sample_status, effective_status, data_nature, is_demo` | 查询索引（sampled_at,monitor_category,sample_status,effective_status,data_nature,is_demo） |
| `e01_monitor_sample` | `uk_e01_sample_code` | `sample_code` | 唯一约束（sample_code） |
| `e01_monitor_sample` | `uk_e01_sample_idempotency` | `idempotency_key` | 唯一约束（idempotency_key） |
| `e01_rectification_round` | `PRIMARY` | `id` | 主键 |
| `e01_rectification_round` | `fk_e01_rect_round_task` | `task_id` | 外键索引（task_id） |
| `e01_rectification_round` | `uk_e01_rect_round` | `event_id, round_no` | 唯一约束（event_id,round_no） |
| `e01_retest_result_link` | `PRIMARY` | `id` | 主键 |
| `e01_retest_result_link` | `fk_e01_retest_link_event` | `event_id` | 外键索引（event_id） |
| `e01_retest_result_link` | `fk_e01_retest_link_original` | `original_result_id` | 外键索引（original_result_id） |
| `e01_retest_result_link` | `uk_e01_retest_link_result` | `factor_result_id` | 唯一约束（factor_result_id） |
| `e01_retest_result_link` | `uk_e01_retest_link_round_result` | `retest_round_id, factor_result_id` | 唯一约束（retest_round_id,factor_result_id） |
| `e01_retest_round` | `PRIMARY` | `id` | 主键 |
| `e01_retest_round` | `fk_e01_retest_round_batch` | `retest_batch_id` | 外键索引（retest_batch_id） |
| `e01_retest_round` | `fk_e01_retest_round_document` | `report_document_id` | 外键索引（report_document_id） |
| `e01_retest_round` | `uk_e01_retest_round` | `event_id, round_no` | 唯一约束（event_id,round_no） |
| `e01_standard_limit` | `PRIMARY` | `id` | 主键 |
| `e01_standard_limit` | `fk_e01_limit_factor` | `factor_id` | 外键索引（factor_id） |
| `e01_standard_limit` | `idx_e01_limit_standard_factor` | `standard_version_id, factor_id` | 查询索引（standard_version_id,factor_id） |
| `e01_standard_version` | `PRIMARY` | `id` | 主键 |
| `e01_standard_version` | `fk_e01_standard_document` | `source_document_id` | 外键索引（source_document_id） |
| `e01_standard_version` | `uk_e01_standard_version` | `standard_code, version_no` | 唯一约束（standard_code,version_no） |
| `e_case_evidence` | `PRIMARY` | `id` | 主键 |
| `e_case_evidence` | `fk_e_case_evidence_document` | `document_id` | 外键索引（document_id） |
| `e_case_evidence` | `fk_e_case_evidence_file` | `file_id` | 外键索引（file_id） |
| `e_case_evidence` | `fk_e_case_evidence_history` | `status_history_id` | 外键索引（status_history_id） |
| `e_case_evidence` | `idx_e_case_evidence_case` | `case_id, evidence_role, is_current` | 查询索引（case_id,evidence_role,is_current） |
| `e_case_party` | `PRIMARY` | `id` | 主键 |
| `e_case_party` | `fk_e_case_party_org` | `org_id` | 外键索引（org_id） |
| `e_case_party` | `idx_e_case_party_case` | `case_id, party_role, is_current` | 查询索引（case_id,party_role,is_current） |
| `e_case_rectification_link` | `PRIMARY` | `id` | 主键 |
| `e_case_rectification_link` | `fk_e_case_rect_task` | `task_id` | 外键索引（task_id） |
| `e_case_rectification_link` | `uk_e_case_rect_link` | `case_id, task_id` | 唯一约束（case_id,task_id） |
| `e_case_relation` | `PRIMARY` | `id` | 主键 |
| `e_case_relation` | `fk_e_case_relation_to` | `to_case_id` | 外键索引（to_case_id） |
| `e_case_relation` | `uk_e_case_relation` | `from_case_id, to_case_id, relation_type` | 唯一约束（from_case_id,to_case_id,relation_type） |
| `e_case_status_history` | `PRIMARY` | `id` | 主键 |
| `e_case_status_history` | `fk_e_case_history_correction` | `correction_of_history_id` | 外键索引（correction_of_history_id） |
| `e_case_status_history` | `fk_e_case_history_document` | `source_document_id` | 外键索引（source_document_id） |
| `e_case_status_history` | `idx_e_case_history_correction` | `case_id, correction_of_history_id` | 查询索引（case_id,correction_of_history_id） |
| `e_case_status_history` | `uk_e_case_history_request` | `case_id, client_request_id` | 唯一约束（case_id,client_request_id） |
| `e_case_status_history` | `uk_e_case_history_sequence` | `case_id, sequence_no` | 唯一约束（case_id,sequence_no） |
| `e_closure_case` | `PRIMARY` | `id` | 主键 |
| `e_closure_case` | `fk_e_case_close_org` | `close_org_id` | 外键索引（close_org_id） |
| `e_closure_case` | `fk_e_case_current_history` | `current_status_history_id` | 外键索引（current_status_history_id） |
| `e_closure_case` | `fk_e_case_discovery_org` | `discovery_org_id` | 外键索引（discovery_org_id） |
| `e_closure_case` | `fk_e_case_gis` | `gis_feature_id` | 外键索引（gis_feature_id） |
| `e_closure_case` | `fk_e_case_merged_into` | `merged_into_case_id` | 外键索引（merged_into_case_id） |
| `e_closure_case` | `fk_e_case_responsible_org` | `responsible_org_id` | 外键索引（responsible_org_id） |
| `e_closure_case` | `fk_e_case_review_org` | `review_org_id` | 外键索引（review_org_id） |
| `e_closure_case` | `fk_e_case_source_document` | `source_document_id` | 外键索引（source_document_id） |
| `e_closure_case` | `idx_e_case_open` | `case_domain, current_status, effective_status, data_nature, is_demo` | 查询索引（case_domain,current_status,effective_status,data_nature,is_demo） |
| `e_closure_case` | `uk_e_case_code` | `case_code` | 唯一约束（case_code） |
| `e_closure_case` | `uk_e_case_source_key` | `case_domain, source_business_key` | 唯一约束（case_domain,source_business_key） |
| `e_rectification_task` | `PRIMARY` | `id` | 主键 |
| `e_rectification_task` | `fk_e_rect_task_completed_by` | `rectification_completed_by` | 外键索引（rectification_completed_by） |
| `e_rectification_task` | `fk_e_rect_task_org` | `responsible_org_id` | 外键索引（responsible_org_id） |
| `e_rectification_task` | `uk_e_rect_task_code` | `task_code` | 唯一约束（task_code） |
| `engineering_object_phase` | `PRIMARY` | `id` | 主键 |
| `engineering_object_phase` | `fk_object_phase_phase` | `phase_id` | 外键索引（phase_id） |
| `engineering_object_phase` | `idx_object_phase_time` | `object_id, process_start_at, process_end_at` | 查询索引（object_id,process_start_at,process_end_at） |
| `engineering_object_phase` | `uk_object_phase_process` | `object_id, phase_id, process_code` | 唯一约束（object_id,phase_id,process_code） |
| `env_issue_record` | `PRIMARY` | `id` | 主键 |
| `env_issue_record` | `idx_env_issue_biz_code` | `business_code` | 查询索引（business_code） |
| `env_issue_record` | `idx_env_issue_scope` | `is_demo, data_nature, issue_status` | 查询索引（is_demo,data_nature,issue_status） |
| `env_issue_record` | `idx_env_issue_status` | `issue_status` | 查询索引（issue_status） |
| `env_monitoring_record` | `PRIMARY` | `id` | 主键 |
| `env_monitoring_record` | `idx_env_monitor_date` | `monitor_date` | 查询索引（monitor_date） |
| `esg_demo_indicator_detail` | `PRIMARY` | `id` | 主键 |
| `esg_demo_indicator_detail` | `idx_demo_detail_kpi` | `project_id, kpi_key, object_id` | 查询索引（project_id,kpi_key,object_id） |
| `esg_demo_indicator_result` | `PRIMARY` | `id` | 主键 |
| `esg_demo_indicator_result` | `idx_demo_result_latest` | `project_id, period_end, kpi_key, result_status` | 查询索引（project_id,period_end,kpi_key,result_status） |
| `esg_demo_indicator_result` | `uk_demo_result` | `project_id, period_end, kpi_key` | 唯一约束（project_id,period_end,kpi_key） |
| `esg_schema_migration_history` | `PRIMARY` | `id` | 主键 |
| `esg_schema_migration_history` | `idx_migration_version_status` | `version_key, status` | 查询索引（version_key,status） |
| `esg_schema_migration_history` | `uk_migration_version_execution` | `version_key, execution_id` | 唯一约束（version_key,execution_id） |
| `file_asset` | `PRIMARY` | `id` | 主键 |
| `file_asset` | `file_code` | `file_code` | 唯一约束（file_code） |
| `file_asset` | `idx_file_hash` | `sha256_hash` | 查询索引（sha256_hash） |
| `file_asset` | `idx_file_parse_status` | `parse_status` | 查询索引（parse_status） |
| `file_asset` | `idx_file_upload_time` | `upload_time` | 查询索引（upload_time） |
| `gis_feature` | `PRIMARY` | `id` | 主键 |
| `gis_feature` | `idx_gis_feature_layer` | `layer_id` | 查询索引（layer_id） |
| `gis_feature` | `idx_gis_feature_section` | `section_id` | 查询索引（section_id） |
| `gis_feature_business_relation` | `PRIMARY` | `id` | 主键 |
| `gis_feature_business_relation` | `idx_gis_relation_feature` | `feature_id` | 查询索引（feature_id） |
| `gis_feature_business_relation` | `idx_gis_relation_type` | `relation_type` | 查询索引（relation_type） |
| `gis_feature_business_summary` | `PRIMARY` | `feature_id` | 主键 |
| `gis_feature_business_summary` | `idx_gis_business_project` | `project_id` | 查询索引（project_id） |
| `gis_layer` | `PRIMARY` | `id` | 主键 |
| `indicator_calculation_job` | `PRIMARY` | `id` | 主键 |
| `indicator_calculation_job` | `idx_indicator_job_code` | `indicator_code, created_at` | 查询索引（indicator_code,created_at） |
| `indicator_calculation_job` | `idx_indicator_job_status` | `job_status` | 查询索引（job_status） |
| `indicator_definition` | `PRIMARY` | `indicator_code` | 主键 |
| `indicator_history` | `PRIMARY` | `id` | 主键 |
| `indicator_history` | `idx_indicator_history_code` | `indicator_code, result_date` | 查询索引（indicator_code,result_date） |
| `indicator_history` | `uk_indicator_history` | `indicator_code, result_date` | 唯一约束（indicator_code,result_date） |
| `indicator_result` | `PRIMARY` | `indicator_code` | 主键 |
| `indicator_result` | `idx_indicator_group` | `group_code, display_order` | 查询索引（group_code,display_order） |
| `indicator_snapshot` | `PRIMARY` | `snapshot_type, snapshot_date` | 主键 |
| `indicator_source_dependency` | `PRIMARY` | `id` | 主键 |
| `indicator_source_dependency` | `uk_indicator_source` | `indicator_code, source_table` | 唯一约束（indicator_code,source_table） |
| `labor_dispute_record` | `PRIMARY` | `id` | 主键 |
| `labor_dispute_record` | `idx_labor_status` | `status` | 查询索引（status） |
| `manual_confirmation_log` | `PRIMARY` | `id` | 主键 |
| `manual_confirmation_log` | `idx_confirm_operator` | `operator_id, operated_at` | 查询索引（operator_id,operated_at） |
| `manual_confirmation_log` | `idx_confirm_target` | `target_type, target_id` | 查询索引（target_type,target_id） |
| `monitor_frequency_rule` | `PRIMARY` | `id` | 主键 |
| `monitor_frequency_rule` | `idx_monitor_frequency_plan_item` | `plan_item_id, active_status, effective_from` | 查询索引（plan_item_id,active_status,effective_from） |
| `monitor_frequency_rule` | `uk_monitor_frequency_rule` | `rule_code` | 唯一约束（rule_code） |
| `monitor_point_object_relation` | `PRIMARY` | `id` | 主键 |
| `monitor_point_object_relation` | `fk_monitor_relation_object_phase` | `object_phase_id` | 外键索引（object_phase_id） |
| `monitor_point_object_relation` | `fk_monitor_relation_phase` | `phase_id` | 外键索引（phase_id） |
| `monitor_point_object_relation` | `fk_monitor_relation_section` | `section_id` | 外键索引（section_id） |
| `monitor_point_object_relation` | `idx_monitor_object_point` | `object_id, point_id` | 查询索引（object_id,point_id） |
| `monitor_point_object_relation` | `idx_monitor_point_object_time` | `point_id, valid_from, valid_to` | 查询索引（point_id,valid_from,valid_to） |
| `monitor_point_object_relation` | `uk_monitor_point_object_relation` | `relation_code` | 唯一约束（relation_code） |
| `monthly_report_chapter` | `PRIMARY` | `id` | 主键 |
| `monthly_report_chapter` | `idx_monthly_chapter_cycle` | `cycle_id` | 查询索引（cycle_id） |
| `monthly_report_cycle` | `PRIMARY` | `id` | 主键 |
| `monthly_report_gap` | `PRIMARY` | `id` | 主键 |
| `monthly_report_gap` | `idx_monthly_gap_cycle` | `cycle_id` | 查询索引（cycle_id） |
| `monthly_report_group_progress` | `PRIMARY` | `id` | 主键 |
| `monthly_report_group_progress` | `idx_monthly_progress_cycle` | `cycle_id` | 查询索引（cycle_id） |
| `monthly_report_status_chain` | `PRIMARY` | `id` | 主键 |
| `monthly_report_status_chain` | `idx_monthly_chain_cycle` | `cycle_id` | 查询索引（cycle_id） |
| `monthly_report_task_instance` | `PRIMARY` | `id` | 主键 |
| `monthly_report_task_instance` | `idx_monthly_task_code` | `task_code` | 查询索引（task_code） |
| `monthly_report_task_instance` | `idx_monthly_task_period_status` | `report_cycle_id, include_in_denominator, monthly_status` | 查询索引（report_cycle_id,include_in_denominator,monthly_status） |
| `monthly_report_task_instance` | `idx_monthly_task_upload` | `upload_task_id` | 查询索引（upload_task_id） |
| `monthly_report_task_instance` | `uk_monthly_task_dedup` | `report_cycle_id, dedup_key` | 唯一约束（report_cycle_id,dedup_key） |
| `monthly_report_task_material_link` | `PRIMARY` | `id` | 主键 |
| `monthly_report_task_material_link` | `idx_monthly_material_document` | `document_id` | 查询索引（document_id） |
| `monthly_report_task_material_link` | `idx_monthly_material_task` | `task_instance_id` | 查询索引（task_instance_id） |
| `monthly_report_task_material_link` | `uk_monthly_material_link_code` | `link_code` | 唯一约束（link_code） |
| `monthly_report_task_validation` | `PRIMARY` | `id` | 主键 |
| `monthly_report_task_validation` | `uk_monthly_validation_code` | `validation_code` | 唯一约束（validation_code） |
| `monthly_report_task_validation` | `uk_monthly_validation_task` | `task_instance_id` | 唯一约束（task_instance_id） |
| `org_unit` | `PRIMARY` | `id` | 主键 |
| `org_unit` | `org_code` | `org_code` | 唯一约束（org_code） |
| `permit_record` | `PRIMARY` | `id` | 主键 |
| `permit_record` | `idx_permit_expire` | `expire_date` | 查询索引（expire_date） |
| `permit_record` | `idx_permit_status` | `status` | 查询索引（status） |
| `project_engineering_object` | `PRIMARY` | `id` | 主键 |
| `project_engineering_object` | `idx_project_object_gis` | `gis_feature_id` | 查询索引（gis_feature_id） |
| `project_engineering_object` | `idx_project_object_section` | `section_id, object_type, active_status` | 查询索引（section_id,object_type,active_status） |
| `project_engineering_object` | `uk_project_object_code` | `project_id, object_code` | 唯一约束（project_id,object_code） |
| `project_phase_period` | `PRIMARY` | `id` | 主键 |
| `project_phase_period` | `idx_project_phase_time` | `project_id, start_at, end_at` | 查询索引（project_id,start_at,end_at） |
| `project_phase_period` | `uk_project_phase_code` | `project_id, phase_code` | 唯一约束（project_id,phase_code） |
| `project_section` | `PRIMARY` | `id` | 主键 |
| `project_section` | `idx_project_section_range` | `project_id, start_km, end_km` | 查询索引（project_id,start_km,end_km） |
| `project_section` | `uk_project_section_code` | `project_id, section_code` | 唯一约束（project_id,section_code） |
| `rectification_record` | `PRIMARY` | `id` | 主键 |
| `rectification_record` | `idx_rectification_status` | `status` | 查询索引（status） |
| `review_record` | `PRIMARY` | `id` | 主键 |
| `review_record` | `idx_review_status` | `status` | 查询索引（status） |
| `review_record` | `idx_review_task` | `task_id` | 查询索引（task_id） |
| `review_requirement` | `PRIMARY` | `id` | 主键 |
| `review_requirement` | `idx_review_requirement_review` | `review_id` | 查询索引（review_id） |
| `review_timeline` | `PRIMARY` | `id` | 主键 |
| `review_timeline` | `idx_review_timeline_review` | `review_id` | 查询索引（review_id） |
| `s01_confirmation_batch` | `PRIMARY` | `id` | 主键 |
| `s01_confirmation_batch` | `idx_confirmation_month` | `confirmation_month` | 查询索引（confirmation_month） |
| `s01_confirmation_batch` | `idx_data_nature` | `data_nature` | 查询索引（data_nature） |
| `s01_confirmation_batch` | `idx_is_demo` | `is_demo` | 查询索引（is_demo） |
| `s01_confirmation_batch` | `uk_batch_code` | `batch_code` | 唯一约束（batch_code） |
| `s01_confirmation_batch` | `uk_project_nature_current` | `project_id, data_nature, is_demo, effective_status` | 唯一约束（project_id,data_nature,is_demo,effective_status） |
| `safety_incident_record` | `PRIMARY` | `id` | 主键 |
| `safety_incident_record` | `idx_safety_incident_date` | `incident_date` | 查询索引（incident_date） |
| `safety_incident_record` | `idx_safety_incident_interrupt` | `interrupt_counting` | 查询索引（interrupt_counting） |
| `safety_incident_record` | `idx_sir_data_nature` | `data_nature` | 查询索引（data_nature） |
| `safety_incident_record` | `idx_sir_determination_status` | `responsibility_determination_status` | 查询索引（responsibility_determination_status） |
| `safety_incident_record` | `idx_sir_effective_current` | `effective_status, is_current` | 查询索引（effective_status,is_current） |
| `safety_incident_record` | `idx_sir_is_demo` | `is_demo` | 查询索引（is_demo） |
| `safety_incident_record` | `idx_sir_occurred_date` | `occurred_date` | 查询索引（occurred_date） |
| `safety_incident_record` | `idx_sir_project_occurred` | `project_id, occurred_date` | 查询索引（project_id,occurred_date） |
| `safety_production_record` | `PRIMARY` | `id` | 主键 |
| `safety_production_record` | `idx_spr_confirmation_status` | `confirmation_status` | 查询索引（confirmation_status） |
| `safety_production_record` | `idx_spr_nature_current` | `data_nature, is_demo, is_current` | 查询索引（data_nature,is_demo,is_current） |
| `safety_production_record` | `idx_spr_project_id` | `project_id` | 查询索引（project_id） |
| `safety_risk_point` | `PRIMARY` | `id` | 主键 |
| `safety_risk_point` | `idx_safety_risk_level` | `risk_level` | 查询索引（risk_level） |
| `safety_risk_point` | `idx_safety_risk_status` | `control_status` | 查询索引（control_status） |
| `salary_payment_record` | `PRIMARY` | `id` | 主键 |
| `salary_payment_record` | `idx_salary_payment_month` | `payment_month` | 查询索引（payment_month） |
| `source_record_trace` | `PRIMARY` | `id` | 主键 |
| `source_record_trace` | `idx_trace_job` | `ingestion_job_id` | 查询索引（ingestion_job_id） |
| `source_record_trace` | `idx_trace_source` | `source_id, source_record_key` | 查询索引（source_id,source_record_key） |
| `source_record_trace` | `idx_trace_target` | `target_table, target_record_id` | 查询索引（target_table,target_record_id） |
| `special_plan_approval` | `PRIMARY` | `id` | 主键 |
| `special_plan_approval` | `fk_special_plan_approval_file` | `approval_file_id` | 外键索引（approval_file_id） |
| `special_plan_approval` | `idx_special_plan_date` | `project_id, approval_date` | 查询索引（project_id,approval_date） |
| `special_plan_approval` | `idx_special_plan_level` | `project_id, risk_level` | 查询索引（project_id,risk_level） |
| `special_plan_approval` | `idx_special_plan_risk_point` | `risk_point_id` | 查询索引（risk_point_id） |
| `special_plan_approval` | `idx_special_plan_status` | `project_id, approval_status` | 查询索引（project_id,approval_status） |
| `special_plan_approval` | `uk_special_plan_project_code` | `project_id, plan_code` | 唯一约束（project_id,plan_code） |
| `task_candidate_document` | `PRIMARY` | `id` | 主键 |
| `task_candidate_document` | `idx_candidate_document_task` | `task_id` | 查询索引（task_id） |
| `task_match_candidate` | `PRIMARY` | `id` | 主键 |
| `task_match_candidate` | `idx_candidate_job` | `parse_job_id` | 查询索引（parse_job_id） |
| `task_match_candidate` | `idx_candidate_status` | `candidate_status` | 查询索引（candidate_status） |
| `task_match_candidate` | `idx_candidate_task` | `task_id` | 查询索引（task_id） |
| `task_review_timeline` | `PRIMARY` | `id` | 主键 |
| `task_review_timeline` | `idx_task_review_timeline_task` | `task_id` | 查询索引（task_id） |
| `upload_task` | `PRIMARY` | `id` | 主键 |
| `upload_task` | `idx_upload_task_deadline` | `deadline` | 查询索引（deadline） |
| `upload_task` | `idx_upload_task_module` | `module_code` | 查询索引（module_code） |
| `upload_task` | `idx_upload_task_status` | `status` | 查询索引（status） |
| `upload_task_requirement` | `PRIMARY` | `id` | 主键 |
| `upload_task_requirement` | `idx_requirement_status` | `status` | 查询索引（status） |
| `upload_task_requirement` | `idx_requirement_task` | `task_id` | 查询索引（task_id） |
| `user_account` | `PRIMARY` | `id` | 主键 |
| `user_account` | `idx_user_org` | `org_id` | 查询索引（org_id） |
| `user_account` | `username` | `username` | 唯一约束（username） |
| `water_protection_issue` | `PRIMARY` | `id` | 主键 |
| `water_protection_issue` | `idx_water_issue_status` | `issue_status` | 查询索引（issue_status） |
| `workspace_summary` | `PRIMARY` | `id` | 主键 |

## 6. 核心业务表字段级数据字典（录入模板用）

以下字段全部来自 `information_schema.COLUMNS`，**未自行补充不存在字段**。
建议 Excel 列名优先使用「业务用途/说明」；系统字段（id、created_at、updated_at、is_deleted 等）一般不要求业务人员填写。

### 6.1 `biz_env_monitor_point` — 环境监测点

- **分类：** E / 业务事实表 / 必须人工录入
- **当前行数：** 3

| 字段名 | 类型 | 是否为空 | 默认值 | 说明（库注释） | 业务用途（模板建议） |
|---|---|---|---|---|---|
| `id` | `bigint unsigned` | 否 | `NULL` | （库无注释） | 系统主键，勿填 |
| `project_id` | `bigint unsigned` | 否 | `NULL` | （库无注释） | 项目归属，模板建议下拉/固定项目编号映射 |
| `section_id` | `bigint unsigned` | 是 | `NULL` | （库无注释） | 标段，建议下拉 |
| `point_code` | `varchar(64)` | 否 | `NULL` | （库无注释） | 业务编号，建议人工或按规则编制 |
| `point_name` | `varchar(200)` | 否 | `NULL` | （库无注释） | 名称/标题，人工填写 |
| `monitor_category` | `varchar(32)` | 否 | `NULL` | （库无注释） | 按业务台账填写（详见字段名） |
| `location_desc` | `varchar(500)` | 是 | `NULL` | （库无注释） | 备注说明 |
| `longitude` | `decimal(10,7)` | 是 | `NULL` | （库无注释） | GIS/坐标 |
| `latitude` | `decimal(10,7)` | 是 | `NULL` | （库无注释） | GIS/坐标 |
| `active_status` | `varchar(16)` | 否 | `ACTIVE` | （库无注释） | 业务状态 |
| `risk_status` | `varchar(16)` | 否 | `NORMAL` | （库无注释） | 业务状态 |
| `case_status` | `varchar(32)` | 是 | `NULL` | （库无注释） | 业务状态 |
| `responsible_unit` | `varchar(200)` | 是 | `NULL` | （库无注释） | 组织/单位，建议下拉 |
| `updated_at` | `datetime` | 否 | `CURRENT_TIMESTAMP` | （库无注释） | 日期时间；按字段语义由人工或系统填写 |
| `is_deleted` | `tinyint unsigned` | 否 | `0` | （库无注释） | 逻辑删除标记，模板通常不填 |

### 6.2 `biz_env_monitor_result` — 环境监测结果

- **分类：** E / 业务事实表 / 必须人工录入
- **当前行数：** 12

| 字段名 | 类型 | 是否为空 | 默认值 | 说明（库注释） | 业务用途（模板建议） |
|---|---|---|---|---|---|
| `id` | `bigint unsigned` | 否 | `NULL` | （库无注释） | 系统主键，勿填 |
| `project_id` | `bigint unsigned` | 否 | `NULL` | （库无注释） | 项目归属，模板建议下拉/固定项目编号映射 |
| `point_id` | `bigint unsigned` | 否 | `NULL` | （库无注释） | 按业务台账填写（详见字段名） |
| `factor_code` | `varchar(64)` | 否 | `NULL` | （库无注释） | 业务编号，建议人工或按规则编制 |
| `factor_name` | `varchar(128)` | 否 | `NULL` | （库无注释） | 名称/标题，人工填写 |
| `detected_value` | `decimal(18,4)` | 是 | `NULL` | （库无注释） | 按业务台账填写（详见字段名） |
| `limit_value` | `decimal(18,4)` | 是 | `NULL` | （库无注释） | 按业务台账填写（详见字段名） |
| `unit` | `varchar(32)` | 是 | `NULL` | （库无注释） | 组织/单位，建议下拉 |
| `judgement` | `varchar(20)` | 否 | `NULL` | （库无注释） | 按业务台账填写（详见字段名） |
| `exceed_multiple` | `decimal(12,4)` | 是 | `NULL` | （库无注释） | 按业务台账填写（详见字段名） |
| `sampled_at` | `datetime` | 是 | `NULL` | （库无注释） | 日期时间；按字段语义由人工或系统填写 |
| `case_status` | `varchar(32)` | 是 | `NULL` | （库无注释） | 业务状态 |
| `is_closed` | `tinyint unsigned` | 否 | `0` | （库无注释） | 按业务台账填写（详见字段名） |
| `rectification_note` | `varchar(500)` | 是 | `NULL` | （库无注释） | 备注说明 |
| `updated_at` | `datetime` | 否 | `CURRENT_TIMESTAMP` | （库无注释） | 日期时间；按字段语义由人工或系统填写 |
| `is_deleted` | `tinyint unsigned` | 否 | `0` | （库无注释） | 逻辑删除标记，模板通常不填 |

### 6.3 `env_monitoring_record` — 环境监测记录

- **分类：** E / 业务事实表 / 必须人工录入
- **当前行数：** 3
- **库表注释：** 环境监测记录

| 字段名 | 类型 | 是否为空 | 默认值 | 说明（库注释） | 业务用途（模板建议） |
|---|---|---|---|---|---|
| `id` | `bigint` | 否 | `NULL` | （库无注释） | 系统主键，勿填 |
| `document_id` | `bigint` | 是 | `NULL` | （库无注释） | 文件/资料关联编号 |
| `monitor_date` | `date` | 是 | `NULL` | （库无注释） | 日期时间；按字段语义由人工或系统填写 |
| `monitor_type` | `varchar(50)` | 是 | `NULL` | （库无注释） | 按业务台账填写（详见字段名） |
| `exceed_count` | `int` | 否 | `0` | （库无注释） | 按业务台账填写（详见字段名） |
| `dust_exceed_count` | `int` | 否 | `0` | （库无注释） | 按业务台账填写（详见字段名） |
| `noise_exceed_count` | `int` | 否 | `0` | （库无注释） | 按业务台账填写（详见字段名） |
| `module_code` | `varchar(10)` | 否 | `E` | （库无注释） | 业务编号，建议人工或按规则编制 |
| `created_at` | `datetime` | 否 | `CURRENT_TIMESTAMP` | （库无注释） | 日期时间；按字段语义由人工或系统填写 |
| `monitor_point` | `varchar(255)` | 是 | `NULL` | 监测点 | 监测点 |
| `factor_name` | `varchar(100)` | 是 | `NULL` | 监测因子 | 监测因子 |
| `detected_value` | `varchar(50)` | 是 | `NULL` | 检测值 | 检测值 |
| `initial_detected_value` | `varchar(50)` | 是 | `NULL` | 初检值 | 初检值 |
| `recheck_detected_value` | `varchar(50)` | 是 | `NULL` | 复测值 | 复测值 |
| `limit_value` | `varchar(50)` | 是 | `NULL` | 标准限值 | 标准限值 |
| `exceed_multiple` | `decimal(10,2)` | 是 | `NULL` | 超标倍数 | 超标倍数 |
| `recheck_status` | `varchar(30)` | 是 | `NULL` | 复测状态 | 复测状态 |

### 6.4 `env_issue_record` — 环保问题记录

- **分类：** E / 业务事实表 / 必须人工录入
- **当前行数：** 10
- **库表注释：** 环保问题记录

| 字段名 | 类型 | 是否为空 | 默认值 | 说明（库注释） | 业务用途（模板建议） |
|---|---|---|---|---|---|
| `id` | `bigint` | 否 | `NULL` | （库无注释） | 系统主键，勿填 |
| `document_id` | `bigint` | 是 | `NULL` | （库无注释） | 文件/资料关联编号 |
| `issue_type` | `varchar(100)` | 是 | `NULL` | （库无注释） | 按业务台账填写（详见字段名） |
| `issue_count` | `int` | 否 | `1` | （库无注释） | 按业务台账填写（详见字段名） |
| `issue_status` | `varchar(30)` | 是 | `NULL` | （库无注释） | 业务状态 |
| `overdue` | `tinyint` | 否 | `0` | （库无注释） | 按业务台账填写（详见字段名） |
| `found_date` | `date` | 是 | `NULL` | （库无注释） | 日期时间；按字段语义由人工或系统填写 |
| `closed_date` | `date` | 是 | `NULL` | （库无注释） | 日期时间；按字段语义由人工或系统填写 |
| `created_at` | `datetime` | 否 | `CURRENT_TIMESTAMP` | （库无注释） | 日期时间；按字段语义由人工或系统填写 |
| `issue_name` | `varchar(255)` | 是 | `NULL` | 问题名称 | 问题名称 |
| `issue_level` | `varchar(50)` | 是 | `NULL` | 问题等级 | 问题等级 |
| `responsible_department` | `varchar(100)` | 是 | `NULL` | 责任部门 | 责任部门 |
| `deadline` | `date` | 是 | `NULL` | 整改截止 | 整改截止 |
| `duration_days` | `int` | 是 | `NULL` | 处置时长 | 处置时长 |
| `is_demo` | `tinyint(1)` | 否 | `0` | 是否演示数据 | 是否演示数据 |
| `data_nature` | `varchar(20)` | 否 | `formal` | 数据性质 | 数据性质 |
| `business_code` | `varchar(80)` | 是 | `NULL` | 业务编号 | 业务编号 |
| `responsible_org_name` | `varchar(100)` | 是 | `NULL` | 责任单位名称 | 责任单位名称 |
| `location_text` | `varchar(255)` | 是 | `NULL` | 位置描述 | 位置描述 |

### 6.5 `water_protection_issue` — 水保问题记录

- **分类：** E / 业务事实表 / 必须人工录入
- **当前行数：** 16
- **库表注释：** 水保问题记录

| 字段名 | 类型 | 是否为空 | 默认值 | 说明（库注释） | 业务用途（模板建议） |
|---|---|---|---|---|---|
| `id` | `bigint` | 否 | `NULL` | （库无注释） | 系统主键，勿填 |
| `document_id` | `bigint` | 是 | `NULL` | （库无注释） | 文件/资料关联编号 |
| `issue_status` | `varchar(30)` | 是 | `NULL` | （库无注释） | 业务状态 |
| `found_date` | `date` | 是 | `NULL` | （库无注释） | 日期时间；按字段语义由人工或系统填写 |
| `closed_date` | `date` | 是 | `NULL` | （库无注释） | 日期时间；按字段语义由人工或系统填写 |
| `created_at` | `datetime` | 否 | `CURRENT_TIMESTAMP` | （库无注释） | 日期时间；按字段语义由人工或系统填写 |
| `issue_name` | `varchar(255)` | 是 | `NULL` | 水保问题名称 | 水保问题名称 |
| `issue_type` | `varchar(100)` | 是 | `NULL` | 问题类型 | 问题类型 |
| `segment_name` | `varchar(100)` | 是 | `NULL` | 所属标段 | 所属标段 |
| `deadline` | `date` | 是 | `NULL` | 整改时限 | 整改时限 |
| `overdue` | `tinyint` | 否 | `0` | 是否逾期 | 是否逾期 |
| `responsible_department` | `varchar(100)` | 是 | `NULL` | 责任部门 | 责任部门 |
| `is_demo` | `tinyint(1)` | 否 | `0` | demo data flag | demo data flag |
| `data_nature` | `varchar(20)` | 否 | `formal` | formal, demo, or platform_calc | formal, demo, or platform_calc |
| `effective_status` | `varchar(30)` | 否 | `EFFECTIVE` | EFFECTIVE, INEFFECTIVE, or DRAFT | EFFECTIVE, INEFFECTIVE, or DRAFT |
| `business_code` | `varchar(80)` | 是 | `NULL` | business code, for example E03-D01 | business code, for example E03-D01 |
| `responsible_org_name` | `varchar(100)` | 是 | `NULL` | responsible organization | responsible organization |
| `location_text` | `varchar(255)` | 是 | `NULL` | location description | location description |
| `description` | `text` | 是 | `NULL` | issue description | issue description |
| `discovery_basis` | `varchar(100)` | 是 | `NULL` | discovery basis | discovery basis |

### 6.6 `biz_soil_disposal_site` — Demo E02 弃土弃渣场对象

- **分类：** E / 业务事实表 / 必须人工录入
- **当前行数：** 2
- **库表注释：** Demo E02 弃土弃渣场对象

| 字段名 | 类型 | 是否为空 | 默认值 | 说明（库注释） | 业务用途（模板建议） |
|---|---|---|---|---|---|
| `id` | `bigint unsigned` | 否 | `NULL` | （库无注释） | 系统主键，勿填 |
| `project_id` | `bigint unsigned` | 否 | `NULL` | （库无注释） | 项目归属，模板建议下拉/固定项目编号映射 |
| `section_id` | `bigint unsigned` | 是 | `NULL` | （库无注释） | 标段，建议下拉 |
| `work_point_id` | `bigint unsigned` | 是 | `NULL` | （库无注释） | 按业务台账填写（详见字段名） |
| `object_code` | `varchar(64)` | 否 | `NULL` | （库无注释） | 业务编号，建议人工或按规则编制 |
| `object_name` | `varchar(200)` | 否 | `NULL` | （库无注释） | 名称/标题，人工填写 |
| `location_desc` | `varchar(500)` | 是 | `NULL` | （库无注释） | 备注说明 |
| `longitude` | `decimal(10,7)` | 是 | `NULL` | （库无注释） | GIS/坐标 |
| `latitude` | `decimal(10,7)` | 是 | `NULL` | （库无注释） | GIS/坐标 |
| `approved_flag` | `tinyint unsigned` | 否 | `0` | （库无注释） | 按业务台账填写（详见字段名） |
| `capacity_m3` | `decimal(18,2)` | 是 | `NULL` | （库无注释） | 按业务台账填写（详见字段名） |
| `disposal_status` | `varchar(32)` | 否 | `NULL` | （库无注释） | 业务状态 |
| `control_measure` | `varchar(500)` | 是 | `NULL` | （库无注释） | 按业务台账填写（详见字段名） |
| `measure_rate` | `decimal(5,2)` | 是 | `NULL` | （库无注释） | 按业务台账填写（详见字段名） |
| `risk_status` | `varchar(16)` | 否 | `NORMAL` | （库无注释） | 业务状态 |
| `responsible_org_id` | `bigint unsigned` | 是 | `NULL` | （库无注释） | 组织/单位，建议下拉 |
| `source_doc_ref` | `varchar(255)` | 是 | `NULL` | （库无注释） | 按业务台账填写（详见字段名） |
| `updated_at` | `datetime` | 否 | `CURRENT_TIMESTAMP` | （库无注释） | 日期时间；按字段语义由人工或系统填写 |
| `is_deleted` | `tinyint unsigned` | 否 | `0` | （库无注释） | 逻辑删除标记，模板通常不填 |

### 6.7 `biz_temporary_land_use` — Demo E02 临时用地对象

- **分类：** E / 业务事实表 / 必须人工录入
- **当前行数：** 2
- **库表注释：** Demo E02 临时用地对象

| 字段名 | 类型 | 是否为空 | 默认值 | 说明（库注释） | 业务用途（模板建议） |
|---|---|---|---|---|---|
| `id` | `bigint unsigned` | 否 | `NULL` | （库无注释） | 系统主键，勿填 |
| `project_id` | `bigint unsigned` | 否 | `NULL` | （库无注释） | 项目归属，模板建议下拉/固定项目编号映射 |
| `section_id` | `bigint unsigned` | 是 | `NULL` | （库无注释） | 标段，建议下拉 |
| `work_point_id` | `bigint unsigned` | 是 | `NULL` | （库无注释） | 按业务台账填写（详见字段名） |
| `object_code` | `varchar(64)` | 否 | `NULL` | （库无注释） | 业务编号，建议人工或按规则编制 |
| `object_name` | `varchar(200)` | 否 | `NULL` | （库无注释） | 名称/标题，人工填写 |
| `land_type` | `varchar(64)` | 否 | `NULL` | （库无注释） | 按业务台账填写（详见字段名） |
| `area_mu` | `decimal(18,2)` | 是 | `NULL` | （库无注释） | 按业务台账填写（详见字段名） |
| `approval_status` | `varchar(32)` | 否 | `NULL` | （库无注释） | 业务状态 |
| `restore_status` | `varchar(32)` | 否 | `NULL` | （库无注释） | 业务状态 |
| `measure_rate` | `decimal(5,2)` | 是 | `NULL` | （库无注释） | 按业务台账填写（详见字段名） |
| `risk_status` | `varchar(16)` | 否 | `NORMAL` | （库无注释） | 业务状态 |
| `responsible_org_id` | `bigint unsigned` | 是 | `NULL` | （库无注释） | 组织/单位，建议下拉 |
| `source_doc_ref` | `varchar(255)` | 是 | `NULL` | （库无注释） | 按业务台账填写（详见字段名） |
| `updated_at` | `datetime` | 否 | `CURRENT_TIMESTAMP` | （库无注释） | 日期时间；按字段语义由人工或系统填写 |
| `is_deleted` | `tinyint unsigned` | 否 | `0` | （库无注释） | 逻辑删除标记，模板通常不填 |

### 6.8 `biz_topsoil_stripping` — Demo E02 表土剥离对象

- **分类：** E / 业务事实表 / 必须人工录入
- **当前行数：** 2
- **库表注释：** Demo E02 表土剥离对象

| 字段名 | 类型 | 是否为空 | 默认值 | 说明（库注释） | 业务用途（模板建议） |
|---|---|---|---|---|---|
| `id` | `bigint unsigned` | 否 | `NULL` | （库无注释） | 系统主键，勿填 |
| `project_id` | `bigint unsigned` | 否 | `NULL` | （库无注释） | 项目归属，模板建议下拉/固定项目编号映射 |
| `section_id` | `bigint unsigned` | 是 | `NULL` | （库无注释） | 标段，建议下拉 |
| `work_point_id` | `bigint unsigned` | 是 | `NULL` | （库无注释） | 按业务台账填写（详见字段名） |
| `object_code` | `varchar(64)` | 否 | `NULL` | （库无注释） | 业务编号，建议人工或按规则编制 |
| `object_name` | `varchar(200)` | 否 | `NULL` | （库无注释） | 名称/标题，人工填写 |
| `planned_area_mu` | `decimal(18,2)` | 是 | `NULL` | （库无注释） | 按业务台账填写（详见字段名） |
| `completed_area_mu` | `decimal(18,2)` | 是 | `NULL` | （库无注释） | 按业务台账填写（详见字段名） |
| `completion_rate` | `decimal(5,2)` | 是 | `NULL` | （库无注释） | 按业务台账填写（详见字段名） |
| `storage_measure` | `varchar(500)` | 是 | `NULL` | （库无注释） | 按业务台账填写（详见字段名） |
| `current_status` | `varchar(32)` | 否 | `NULL` | （库无注释） | 业务状态 |
| `risk_status` | `varchar(16)` | 否 | `NORMAL` | （库无注释） | 业务状态 |
| `responsible_org_id` | `bigint unsigned` | 是 | `NULL` | （库无注释） | 组织/单位，建议下拉 |
| `source_doc_ref` | `varchar(255)` | 是 | `NULL` | （库无注释） | 按业务台账填写（详见字段名） |
| `updated_at` | `datetime` | 否 | `CURRENT_TIMESTAMP` | （库无注释） | 日期时间；按字段语义由人工或系统填写 |
| `is_deleted` | `tinyint unsigned` | 否 | `0` | （库无注释） | 逻辑删除标记，模板通常不填 |

### 6.9 `biz_construction_slope` — Demo E02 施工边坡对象

- **分类：** E / 业务事实表 / 必须人工录入
- **当前行数：** 2
- **库表注释：** Demo E02 施工边坡对象

| 字段名 | 类型 | 是否为空 | 默认值 | 说明（库注释） | 业务用途（模板建议） |
|---|---|---|---|---|---|
| `id` | `bigint unsigned` | 否 | `NULL` | （库无注释） | 系统主键，勿填 |
| `project_id` | `bigint unsigned` | 否 | `NULL` | （库无注释） | 项目归属，模板建议下拉/固定项目编号映射 |
| `section_id` | `bigint unsigned` | 是 | `NULL` | （库无注释） | 标段，建议下拉 |
| `work_point_id` | `bigint unsigned` | 是 | `NULL` | （库无注释） | 按业务台账填写（详见字段名） |
| `object_code` | `varchar(64)` | 否 | `NULL` | （库无注释） | 业务编号，建议人工或按规则编制 |
| `object_name` | `varchar(200)` | 否 | `NULL` | （库无注释） | 名称/标题，人工填写 |
| `slope_type` | `varchar(64)` | 否 | `NULL` | （库无注释） | 按业务台账填写（详见字段名） |
| `chainage` | `varchar(64)` | 是 | `NULL` | （库无注释） | 按业务台账填写（详见字段名） |
| `greening_rate` | `decimal(5,2)` | 是 | `NULL` | （库无注释） | 按业务台账填写（详见字段名） |
| `stability_status` | `varchar(32)` | 否 | `NULL` | （库无注释） | 业务状态 |
| `protection_measure` | `varchar(500)` | 是 | `NULL` | （库无注释） | 按业务台账填写（详见字段名） |
| `risk_status` | `varchar(16)` | 否 | `NORMAL` | （库无注释） | 业务状态 |
| `responsible_org_id` | `bigint unsigned` | 是 | `NULL` | （库无注释） | 组织/单位，建议下拉 |
| `source_doc_ref` | `varchar(255)` | 是 | `NULL` | （库无注释） | 按业务台账填写（详见字段名） |
| `updated_at` | `datetime` | 否 | `CURRENT_TIMESTAMP` | （库无注释） | 日期时间；按字段语义由人工或系统填写 |
| `is_deleted` | `tinyint unsigned` | 否 | `0` | （库无注释） | 逻辑删除标记，模板通常不填 |

### 6.10 `biz_ecological_protection_object` — Demo E03 生态保护对象

- **分类：** E / 业务事实表 / 必须人工录入
- **当前行数：** 2
- **库表注释：** Demo E03 生态保护对象

| 字段名 | 类型 | 是否为空 | 默认值 | 说明（库注释） | 业务用途（模板建议） |
|---|---|---|---|---|---|
| `id` | `bigint unsigned` | 否 | `NULL` | （库无注释） | 系统主键，勿填 |
| `project_id` | `bigint unsigned` | 否 | `NULL` | （库无注释） | 项目归属，模板建议下拉/固定项目编号映射 |
| `section_id` | `bigint unsigned` | 是 | `NULL` | （库无注释） | 标段，建议下拉 |
| `object_code` | `varchar(64)` | 否 | `NULL` | （库无注释） | 业务编号，建议人工或按规则编制 |
| `object_name` | `varchar(200)` | 否 | `NULL` | （库无注释） | 名称/标题，人工填写 |
| `object_type` | `varchar(64)` | 否 | `NULL` | （库无注释） | 按业务台账填写（详见字段名） |
| `importance_level` | `varchar(32)` | 是 | `NULL` | （库无注释） | 按业务台账填写（详见字段名） |
| `location_desc` | `varchar(500)` | 是 | `NULL` | （库无注释） | 备注说明 |
| `identification_status` | `varchar(32)` | 否 | `NULL` | （库无注释） | 业务状态 |
| `inspection_status` | `varchar(32)` | 否 | `NULL` | （库无注释） | 业务状态 |
| `protection_measure` | `varchar(500)` | 是 | `NULL` | （库无注释） | 按业务台账填写（详见字段名） |
| `risk_status` | `varchar(16)` | 否 | `NORMAL` | （库无注释） | 业务状态 |
| `responsible_org_id` | `bigint unsigned` | 是 | `NULL` | （库无注释） | 组织/单位，建议下拉 |
| `source_doc_ref` | `varchar(255)` | 是 | `NULL` | （库无注释） | 按业务台账填写（详见字段名） |
| `updated_at` | `datetime` | 否 | `CURRENT_TIMESTAMP` | （库无注释） | 日期时间；按字段语义由人工或系统填写 |
| `is_deleted` | `tinyint unsigned` | 否 | `0` | （库无注释） | 逻辑删除标记，模板通常不填 |

### 6.11 `biz_ecological_sensitive_area` — Demo E03 生态敏感区

- **分类：** E / 业务事实表 / 必须人工录入
- **当前行数：** 2
- **库表注释：** Demo E03 生态敏感区

| 字段名 | 类型 | 是否为空 | 默认值 | 说明（库注释） | 业务用途（模板建议） |
|---|---|---|---|---|---|
| `id` | `bigint unsigned` | 否 | `NULL` | （库无注释） | 系统主键，勿填 |
| `project_id` | `bigint unsigned` | 否 | `NULL` | （库无注释） | 项目归属，模板建议下拉/固定项目编号映射 |
| `section_id` | `bigint unsigned` | 是 | `NULL` | （库无注释） | 标段，建议下拉 |
| `object_code` | `varchar(64)` | 否 | `NULL` | （库无注释） | 业务编号，建议人工或按规则编制 |
| `object_name` | `varchar(200)` | 否 | `NULL` | （库无注释） | 名称/标题，人工填写 |
| `sensitive_type` | `varchar(64)` | 否 | `NULL` | （库无注释） | 按业务台账填写（详见字段名） |
| `location_desc` | `varchar(500)` | 是 | `NULL` | （库无注释） | 备注说明 |
| `area_mu` | `decimal(18,2)` | 是 | `NULL` | （库无注释） | 按业务台账填写（详见字段名） |
| `protection_level` | `varchar(32)` | 是 | `NULL` | （库无注释） | 按业务台账填写（详见字段名） |
| `identification_status` | `varchar(32)` | 否 | `NULL` | （库无注释） | 业务状态 |
| `monitoring_status` | `varchar(32)` | 否 | `NULL` | （库无注释） | 业务状态 |
| `protection_measure` | `varchar(500)` | 是 | `NULL` | （库无注释） | 按业务台账填写（详见字段名） |
| `risk_status` | `varchar(16)` | 否 | `NORMAL` | （库无注释） | 业务状态 |
| `responsible_org_id` | `bigint unsigned` | 是 | `NULL` | （库无注释） | 组织/单位，建议下拉 |
| `source_doc_ref` | `varchar(255)` | 是 | `NULL` | （库无注释） | 按业务台账填写（详见字段名） |
| `updated_at` | `datetime` | 否 | `CURRENT_TIMESTAMP` | （库无注释） | 日期时间；按字段语义由人工或系统填写 |
| `is_deleted` | `tinyint unsigned` | 否 | `0` | （库无注释） | 逻辑删除标记，模板通常不填 |

### 6.12 `biz_cultural_relic_object` — E04 文物保护管控对象演示台账

- **分类：** E / 业务事实表 / 必须人工录入
- **当前行数：** 4
- **库表注释：** E04 文物保护管控对象演示台账

| 字段名 | 类型 | 是否为空 | 默认值 | 说明（库注释） | 业务用途（模板建议） |
|---|---|---|---|---|---|
| `id` | `bigint` | 否 | `NULL` | （库无注释） | 系统主键，勿填 |
| `project_id` | `varchar(64)` | 否 | `NULL` | （库无注释） | 项目归属，模板建议下拉/固定项目编号映射 |
| `section_id` | `bigint` | 是 | `NULL` | （库无注释） | 标段，建议下拉 |
| `relic_code` | `varchar(64)` | 否 | `NULL` | （库无注释） | 业务编号，建议人工或按规则编制 |
| `relic_name` | `varchar(200)` | 否 | `NULL` | （库无注释） | 名称/标题，人工填写 |
| `relic_type` | `varchar(64)` | 否 | `NULL` | （库无注释） | 按业务台账填写（详见字段名） |
| `protection_level` | `varchar(64)` | 是 | `NULL` | （库无注释） | 按业务台账填写（详见字段名） |
| `location_desc` | `varchar(200)` | 是 | `NULL` | （库无注释） | 备注说明 |
| `longitude` | `decimal(12,8)` | 是 | `NULL` | （库无注释） | GIS/坐标 |
| `latitude` | `decimal(12,8)` | 是 | `NULL` | （库无注释） | GIS/坐标 |
| `protection_scope` | `varchar(500)` | 是 | `NULL` | （库无注释） | 按业务台账填写（详见字段名） |
| `construction_impact` | `varchar(500)` | 是 | `NULL` | （库无注释） | 按业务台账填写（详见字段名） |
| `protection_measure` | `varchar(500)` | 是 | `NULL` | （库无注释） | 按业务台账填写（详见字段名） |
| `responsible_unit` | `varchar(200)` | 是 | `NULL` | （库无注释） | 组织/单位，建议下拉 |
| `risk_status` | `varchar(64)` | 否 | `正常` | （库无注释） | 业务状态 |
| `update_time` | `datetime` | 否 | `CURRENT_TIMESTAMP` | （库无注释） | 日期时间；按字段语义由人工或系统填写 |
| `survey_status` | `varchar(32)` | 否 | `COMPLETED` | （库无注释） | 业务状态 |
| `measure_rate` | `decimal(5,2)` | 是 | `NULL` | （库无注释） | 按业务台账填写（详见字段名） |
| `responsible_org_id` | `bigint unsigned` | 是 | `NULL` | （库无注释） | 组织/单位，建议下拉 |
| `source_doc_ref` | `varchar(255)` | 是 | `NULL` | （库无注释） | 按业务台账填写（详见字段名） |
| `impact_analysis` | `varchar(1000)` | 是 | `NULL` | （库无注释） | 按业务台账填写（详见字段名） |
| `is_deleted` | `tinyint unsigned` | 否 | `0` | （库无注释） | 逻辑删除标记，模板通常不填 |

### 6.13 `e01_monitor_point` — E01监测点主数据

- **分类：** E / 业务事实表 / 必须人工录入
- **当前行数：** 4

| 字段名 | 类型 | 是否为空 | 默认值 | 说明（库注释） | 业务用途（模板建议） |
|---|---|---|---|---|---|
| `id` | `bigint` | 否 | `NULL` | （库无注释） | 系统主键，勿填 |
| `point_code` | `varchar(80)` | 否 | `NULL` | （库无注释） | 业务编号，建议人工或按规则编制 |
| `point_name` | `varchar(160)` | 否 | `NULL` | （库无注释） | 名称/标题，人工填写 |
| `source_point_name` | `varchar(255)` | 是 | `NULL` | （库无注释） | 名称/标题，人工填写 |
| `chainage` | `varchar(60)` | 是 | `NULL` | （库无注释） | 按业务台账填写（详见字段名） |
| `segment_code` | `varchar(80)` | 是 | `NULL` | （库无注释） | 业务编号，建议人工或按规则编制 |
| `segment_name` | `varchar(160)` | 是 | `NULL` | （库无注释） | 名称/标题，人工填写 |
| `engineering_object_type` | `varchar(80)` | 是 | `NULL` | （库无注释） | 按业务台账填写（详见字段名） |
| `engineering_object_id` | `varchar(100)` | 是 | `NULL` | （库无注释） | 按业务台账填写（详见字段名） |
| `engineering_object_name` | `varchar(255)` | 是 | `NULL` | （库无注释） | 名称/标题，人工填写 |
| `longitude` | `decimal(11,8)` | 是 | `NULL` | （库无注释） | GIS/坐标 |
| `latitude` | `decimal(10,8)` | 是 | `NULL` | （库无注释） | GIS/坐标 |
| `coordinate_system` | `varchar(40)` | 是 | `NULL` | （库无注释） | GIS/坐标 |
| `coordinate_source_type` | `varchar(30)` | 否 | `NONE` | （库无注释） | GIS/坐标 |
| `coordinate_source_document_id` | `bigint` | 是 | `NULL` | （库无注释） | 文件/资料关联编号 |
| `coordinate_verification_status` | `varchar(30)` | 否 | `NOT_PROVIDED` | （库无注释） | 业务状态 |
| `coordinate_verified_at` | `datetime(6)` | 是 | `NULL` | （库无注释） | 日期时间；按字段语义由人工或系统填写 |
| `coordinate_verified_by` | `bigint` | 是 | `NULL` | （库无注释） | GIS/坐标 |
| `coordinate_accuracy` | `decimal(10,3)` | 是 | `NULL` | （库无注释） | GIS/坐标 |
| `gis_feature_id` | `varchar(96)` | 是 | `NULL` | （库无注释） | GIS/坐标 |
| `effective_from` | `datetime(6)` | 是 | `NULL` | （库无注释） | 按业务台账填写（详见字段名） |
| `effective_to` | `datetime(6)` | 是 | `NULL` | （库无注释） | 按业务台账填写（详见字段名） |
| `active_status` | `varchar(20)` | 否 | `ACTIVE` | （库无注释） | 业务状态 |
| `data_nature` | `varchar(20)` | 否 | `NULL` | （库无注释） | 数据性质（demo/正式） |
| `is_demo` | `tinyint(1)` | 否 | `0` | （库无注释） | 数据性质（demo/正式） |
| `verification_status` | `varchar(30)` | 否 | `PENDING_REVIEW` | （库无注释） | 业务状态 |
| `effective_status` | `varchar(30)` | 否 | `DRAFT` | （库无注释） | 业务状态 |
| `effective_at` | `datetime(6)` | 是 | `NULL` | （库无注释） | 日期时间；按字段语义由人工或系统填写 |
| `effective_by` | `bigint` | 是 | `NULL` | （库无注释） | 按业务台账填写（详见字段名） |
| `created_at` | `timestamp(6)` | 否 | `CURRENT_TIMESTAMP(6)` | （库无注释） | 日期时间；按字段语义由人工或系统填写 |
| `updated_at` | `timestamp(6)` | 否 | `CURRENT_TIMESTAMP(6)` | （库无注释） | 日期时间；按字段语义由人工或系统填写 |

外键：
- `coordinate_source_document_id` → `document_record.id`
- `gis_feature_id` → `gis_feature.id`

### 6.14 `e01_monitor_plan` — E01监测计划

- **分类：** E / 业务事实表 / 必须人工录入
- **当前行数：** 3

| 字段名 | 类型 | 是否为空 | 默认值 | 说明（库注释） | 业务用途（模板建议） |
|---|---|---|---|---|---|
| `id` | `bigint` | 否 | `NULL` | （库无注释） | 系统主键，勿填 |
| `plan_code` | `varchar(80)` | 否 | `NULL` | （库无注释） | 业务编号，建议人工或按规则编制 |
| `plan_year` | `smallint` | 否 | `NULL` | （库无注释） | 按业务台账填写（详见字段名） |
| `quarter_code` | `char(7)` | 否 | `NULL` | （库无注释） | 业务编号，建议人工或按规则编制 |
| `frequency_code` | `varchar(30)` | 否 | `QUARTERLY` | （库无注释） | 业务编号，建议人工或按规则编制 |
| `testing_provider_org_id` | `bigint` | 是 | `NULL` | （库无注释） | 组织/单位，建议下拉 |
| `testing_provider_name` | `varchar(160)` | 否 | `NULL` | （库无注释） | 名称/标题，人工填写 |
| `owner_department_org_id` | `bigint` | 是 | `NULL` | （库无注释） | 组织/单位，建议下拉 |
| `owner_department_name` | `varchar(160)` | 否 | `NULL` | （库无注释） | 组织/单位，建议下拉 |
| `plan_document_id` | `bigint` | 是 | `NULL` | （库无注释） | 文件/资料关联编号 |
| `version_no` | `varchar(30)` | 否 | `NULL` | （库无注释） | 系统审计字段，通常不填 |
| `plan_status` | `varchar(30)` | 否 | `DRAFT` | （库无注释） | 业务状态 |
| `data_nature` | `varchar(20)` | 否 | `NULL` | （库无注释） | 数据性质（demo/正式） |
| `is_demo` | `tinyint(1)` | 否 | `0` | （库无注释） | 数据性质（demo/正式） |
| `verification_status` | `varchar(30)` | 否 | `PENDING_REVIEW` | （库无注释） | 业务状态 |
| `effective_status` | `varchar(30)` | 否 | `DRAFT` | （库无注释） | 业务状态 |
| `effective_at` | `datetime(6)` | 是 | `NULL` | （库无注释） | 日期时间；按字段语义由人工或系统填写 |
| `effective_by` | `bigint` | 是 | `NULL` | （库无注释） | 按业务台账填写（详见字段名） |
| `created_at` | `timestamp(6)` | 否 | `CURRENT_TIMESTAMP(6)` | （库无注释） | 日期时间；按字段语义由人工或系统填写 |
| `updated_at` | `timestamp(6)` | 否 | `CURRENT_TIMESTAMP(6)` | （库无注释） | 日期时间；按字段语义由人工或系统填写 |

外键：
- `plan_document_id` → `document_record.id`
- `owner_department_org_id` → `org_unit.id`
- `testing_provider_org_id` → `org_unit.id`

### 6.15 `e01_monitor_batch` — E01监测批次

- **分类：** E / 业务事实表 / 必须人工录入
- **当前行数：** 19

| 字段名 | 类型 | 是否为空 | 默认值 | 说明（库注释） | 业务用途（模板建议） |
|---|---|---|---|---|---|
| `id` | `bigint` | 否 | `NULL` | （库无注释） | 系统主键，勿填 |
| `batch_code` | `varchar(80)` | 否 | `NULL` | （库无注释） | 业务编号，建议人工或按规则编制 |
| `plan_id` | `bigint` | 是 | `NULL` | （库无注释） | 按业务台账填写（详见字段名） |
| `quarter_code` | `char(7)` | 否 | `NULL` | （库无注释） | 业务编号，建议人工或按规则编制 |
| `report_no` | `varchar(120)` | 是 | `NULL` | （库无注释） | 按业务台账填写（详见字段名） |
| `testing_provider_org_id` | `bigint` | 是 | `NULL` | （库无注释） | 组织/单位，建议下拉 |
| `testing_provider_name` | `varchar(160)` | 否 | `NULL` | （库无注释） | 名称/标题，人工填写 |
| `sample_start_at` | `datetime(6)` | 否 | `NULL` | （库无注释） | 日期时间；按字段语义由人工或系统填写 |
| `sample_end_at` | `datetime(6)` | 否 | `NULL` | （库无注释） | 日期时间；按字段语义由人工或系统填写 |
| `report_issued_at` | `datetime(6)` | 是 | `NULL` | （库无注释） | 日期时间；按字段语义由人工或系统填写 |
| `received_at` | `datetime(6)` | 是 | `NULL` | （库无注释） | 日期时间；按字段语义由人工或系统填写 |
| `source_document_id` | `bigint` | 是 | `NULL` | （库无注释） | 文件/资料关联编号 |
| `source_file_id` | `bigint` | 是 | `NULL` | （库无注释） | 文件/资料关联编号 |
| `ingestion_job_id` | `bigint` | 是 | `NULL` | （库无注释） | 按业务台账填写（详见字段名） |
| `batch_status` | `varchar(30)` | 否 | `DRAFT` | （库无注释） | 业务状态 |
| `idempotency_key` | `varchar(160)` | 否 | `NULL` | （库无注释） | 按业务台账填写（详见字段名） |
| `data_nature` | `varchar(20)` | 否 | `NULL` | （库无注释） | 数据性质（demo/正式） |
| `is_demo` | `tinyint(1)` | 否 | `0` | （库无注释） | 数据性质（demo/正式） |
| `effective_status` | `varchar(30)` | 否 | `DRAFT` | （库无注释） | 业务状态 |
| `effective_at` | `datetime(6)` | 是 | `NULL` | （库无注释） | 日期时间；按字段语义由人工或系统填写 |
| `effective_by` | `bigint` | 是 | `NULL` | （库无注释） | 按业务台账填写（详见字段名） |
| `created_at` | `timestamp(6)` | 否 | `CURRENT_TIMESTAMP(6)` | （库无注释） | 日期时间；按字段语义由人工或系统填写 |
| `updated_at` | `timestamp(6)` | 否 | `CURRENT_TIMESTAMP(6)` | （库无注释） | 日期时间；按字段语义由人工或系统填写 |

外键：
- `source_document_id` → `document_record.id`
- `source_file_id` → `file_asset.id`
- `ingestion_job_id` → `data_ingestion_job.id`
- `plan_id` → `e01_monitor_plan.id`
- `testing_provider_org_id` → `org_unit.id`

### 6.16 `e01_monitor_sample` — E01监测样品

- **分类：** E / 业务事实表 / 必须人工录入
- **当前行数：** 19

| 字段名 | 类型 | 是否为空 | 默认值 | 说明（库注释） | 业务用途（模板建议） |
|---|---|---|---|---|---|
| `id` | `bigint` | 否 | `NULL` | （库无注释） | 系统主键，勿填 |
| `sample_code` | `varchar(100)` | 否 | `NULL` | （库无注释） | 业务编号，建议人工或按规则编制 |
| `batch_id` | `bigint` | 否 | `NULL` | （库无注释） | 按业务台账填写（详见字段名） |
| `plan_item_id` | `bigint` | 是 | `NULL` | （库无注释） | 按业务台账填写（详见字段名） |
| `point_id` | `bigint` | 否 | `NULL` | （库无注释） | 按业务台账填写（详见字段名） |
| `monitor_category` | `varchar(20)` | 否 | `NULL` | （库无注释） | 按业务台账填写（详见字段名） |
| `sampled_at` | `datetime(6)` | 否 | `NULL` | （库无注释） | 日期时间；按字段语义由人工或系统填写 |
| `sample_end_at` | `datetime(6)` | 是 | `NULL` | （库无注释） | 日期时间；按字段语义由人工或系统填写 |
| `planned_sample_at_snapshot` | `datetime(6)` | 是 | `NULL` | （库无注释） | 按业务台账填写（详见字段名） |
| `planned_actual_variance_minutes` | `int` | 是 | `NULL` | （库无注释） | 按业务台账填写（详见字段名） |
| `sample_no` | `varchar(100)` | 是 | `NULL` | （库无注释） | 按业务台账填写（详见字段名） |
| `idempotency_key` | `varchar(180)` | 否 | `NULL` | （库无注释） | 按业务台账填写（详见字段名） |
| `sample_status` | `varchar(30)` | 否 | `PENDING_REVIEW` | （库无注释） | 业务状态 |
| `void_reason` | `varchar(500)` | 是 | `NULL` | （库无注释） | 按业务台账填写（详见字段名） |
| `duplicate_of_sample_id` | `bigint` | 是 | `NULL` | （库无注释） | 按业务台账填写（详见字段名） |
| `raw_record_document_id` | `bigint` | 是 | `NULL` | （库无注释） | 文件/资料关联编号 |
| `data_nature` | `varchar(20)` | 否 | `NULL` | （库无注释） | 数据性质（demo/正式） |
| `is_demo` | `tinyint(1)` | 否 | `0` | （库无注释） | 数据性质（demo/正式） |
| `verification_status` | `varchar(30)` | 否 | `PENDING_REVIEW` | （库无注释） | 业务状态 |
| `effective_status` | `varchar(30)` | 否 | `DRAFT` | （库无注释） | 业务状态 |
| `effective_at` | `datetime(6)` | 是 | `NULL` | （库无注释） | 日期时间；按字段语义由人工或系统填写 |
| `effective_by` | `bigint` | 是 | `NULL` | （库无注释） | 按业务台账填写（详见字段名） |
| `created_at` | `timestamp(6)` | 否 | `CURRENT_TIMESTAMP(6)` | （库无注释） | 日期时间；按字段语义由人工或系统填写 |
| `updated_at` | `timestamp(6)` | 否 | `CURRENT_TIMESTAMP(6)` | （库无注释） | 日期时间；按字段语义由人工或系统填写 |

外键：
- `batch_id` → `e01_monitor_batch.id`
- `duplicate_of_sample_id` → `e01_monitor_sample.id`
- `plan_item_id` → `e01_monitor_plan_item.id`
- `point_id` → `e01_monitor_point.id`
- `raw_record_document_id` → `document_record.id`

### 6.17 `e01_factor_definition` — E01监测因子定义

- **分类：** E / 配置表 / 必须人工录入
- **当前行数：** 6

| 字段名 | 类型 | 是否为空 | 默认值 | 说明（库注释） | 业务用途（模板建议） |
|---|---|---|---|---|---|
| `id` | `bigint` | 否 | `NULL` | （库无注释） | 系统主键，勿填 |
| `factor_code` | `varchar(80)` | 否 | `NULL` | （库无注释） | 业务编号，建议人工或按规则编制 |
| `factor_name` | `varchar(160)` | 否 | `NULL` | （库无注释） | 名称/标题，人工填写 |
| `monitor_category` | `varchar(20)` | 否 | `NULL` | （库无注释） | 按业务台账填写（详见字段名） |
| `default_unit` | `varchar(60)` | 是 | `NULL` | （库无注释） | 组织/单位，建议下拉 |
| `effective_from` | `datetime(6)` | 是 | `NULL` | （库无注释） | 按业务台账填写（详见字段名） |
| `effective_to` | `datetime(6)` | 是 | `NULL` | （库无注释） | 按业务台账填写（详见字段名） |
| `data_nature` | `varchar(20)` | 否 | `NULL` | （库无注释） | 数据性质（demo/正式） |
| `is_demo` | `tinyint(1)` | 否 | `0` | （库无注释） | 数据性质（demo/正式） |
| `verification_status` | `varchar(30)` | 否 | `PENDING_REVIEW` | （库无注释） | 业务状态 |
| `effective_status` | `varchar(30)` | 否 | `DRAFT` | （库无注释） | 业务状态 |
| `effective_at` | `datetime(6)` | 是 | `NULL` | （库无注释） | 日期时间；按字段语义由人工或系统填写 |
| `effective_by` | `bigint` | 是 | `NULL` | （库无注释） | 按业务台账填写（详见字段名） |

### 6.18 `e01_factor_result` — E01因子监测结果

- **分类：** E / 业务事实表 / 必须人工录入
- **当前行数：** 37

| 字段名 | 类型 | 是否为空 | 默认值 | 说明（库注释） | 业务用途（模板建议） |
|---|---|---|---|---|---|
| `id` | `bigint` | 否 | `NULL` | （库无注释） | 系统主键，勿填 |
| `result_code` | `varchar(255)` | 否 | `NULL` | （库无注释） | 业务编号，建议人工或按规则编制 |
| `sample_id` | `bigint` | 否 | `NULL` | （库无注释） | 按业务台账填写（详见字段名） |
| `factor_id` | `bigint` | 否 | `NULL` | （库无注释） | 按业务台账填写（详见字段名） |
| `standard_version_id` | `bigint` | 否 | `NULL` | （库无注释） | 系统审计字段，通常不填 |
| `test_stage` | `varchar(30)` | 否 | `NULL` | （库无注释） | 按业务台账填写（详见字段名） |
| `judgement` | `varchar(30)` | 是 | `NULL` | （库无注释） | 按业务台账填写（详见字段名） |
| `result_validity` | `varchar(20)` | 是 | `NULL` | （库无注释） | 按业务台账填写（详见字段名） |
| `detected_value_raw` | `varchar(100)` | 是 | `NULL` | （库无注释） | 按业务台账填写（详见字段名） |
| `limit_value_raw` | `varchar(100)` | 是 | `NULL` | （库无注释） | 按业务台账填写（详见字段名） |
| `standard_name_snapshot` | `varchar(255)` | 是 | `NULL` | （库无注释） | 名称/标题，人工填写 |
| `reported_factor_name` | `varchar(160)` | 是 | `NULL` | （库无注释） | 名称/标题，人工填写 |
| `reported_unit` | `varchar(60)` | 是 | `NULL` | （库无注释） | 组织/单位，建议下拉 |
| `judgement_source` | `varchar(30)` | 是 | `NULL` | （库无注释） | 按业务台账填写（详见字段名） |
| `effective_status` | `varchar(30)` | 否 | `DRAFT` | （库无注释） | 业务状态 |
| `data_nature` | `varchar(20)` | 否 | `NULL` | （库无注释） | 数据性质（demo/正式） |
| `is_demo` | `tinyint(1)` | 否 | `0` | （库无注释） | 数据性质（demo/正式） |
| `created_at` | `timestamp(6)` | 否 | `CURRENT_TIMESTAMP(6)` | （库无注释） | 日期时间；按字段语义由人工或系统填写 |
| `updated_at` | `timestamp(6)` | 否 | `CURRENT_TIMESTAMP(6)` | （库无注释） | 日期时间；按字段语义由人工或系统填写 |

外键：
- `factor_id` → `e01_factor_definition.id`
- `sample_id` → `e01_monitor_sample.id`
- `standard_version_id` → `e01_standard_version.id`

### 6.19 `e01_standard_limit` — E01标准限值

- **分类：** E / 配置表 / 必须人工录入
- **当前行数：** 6

| 字段名 | 类型 | 是否为空 | 默认值 | 说明（库注释） | 业务用途（模板建议） |
|---|---|---|---|---|---|
| `id` | `bigint` | 否 | `NULL` | （库无注释） | 系统主键，勿填 |
| `standard_version_id` | `bigint` | 否 | `NULL` | （库无注释） | 系统审计字段，通常不填 |
| `factor_id` | `bigint` | 否 | `NULL` | （库无注释） | 按业务台账填写（详见字段名） |
| `applicable_scene` | `varchar(255)` | 是 | `NULL` | （库无注释） | 按业务台账填写（详见字段名） |
| `limit_operator` | `varchar(10)` | 否 | `NULL` | （库无注释） | 按业务台账填写（详见字段名） |
| `limit_value_raw` | `varchar(100)` | 否 | `NULL` | （库无注释） | 按业务台账填写（详见字段名） |
| `limit_value_num` | `decimal(24,10)` | 是 | `NULL` | （库无注释） | 按业务台账填写（详见字段名） |
| `unit` | `varchar(60)` | 否 | `NULL` | （库无注释） | 组织/单位，建议下拉 |
| `period_description` | `varchar(255)` | 是 | `NULL` | （库无注释） | 备注说明 |
| `data_nature` | `varchar(20)` | 否 | `NULL` | （库无注释） | 数据性质（demo/正式） |
| `is_demo` | `tinyint(1)` | 否 | `0` | （库无注释） | 数据性质（demo/正式） |
| `verification_status` | `varchar(30)` | 否 | `PENDING_REVIEW` | （库无注释） | 业务状态 |
| `effective_status` | `varchar(30)` | 否 | `DRAFT` | （库无注释） | 业务状态 |
| `effective_at` | `datetime(6)` | 是 | `NULL` | （库无注释） | 日期时间；按字段语义由人工或系统填写 |
| `effective_by` | `bigint` | 是 | `NULL` | （库无注释） | 按业务台账填写（详见字段名） |

外键：
- `factor_id` → `e01_factor_definition.id`
- `standard_version_id` → `e01_standard_version.id`

### 6.20 `e01_exceed_event` — E01超标事件

- **分类：** E / 业务事实表 / 系统自动生成/计算
- **当前行数：** 3

| 字段名 | 类型 | 是否为空 | 默认值 | 说明（库注释） | 业务用途（模板建议） |
|---|---|---|---|---|---|
| `id` | `bigint` | 否 | `NULL` | （库无注释） | 系统主键，勿填 |
| `event_code` | `varchar(100)` | 否 | `NULL` | （库无注释） | 业务编号，建议人工或按规则编制 |
| `case_id` | `bigint` | 否 | `NULL` | （库无注释） | 按业务台账填写（详见字段名） |
| `original_result_id` | `bigint` | 否 | `NULL` | （库无注释） | 按业务台账填写（详见字段名） |
| `first_exceeded_at` | `datetime(6)` | 否 | `NULL` | （库无注释） | 日期时间；按字段语义由人工或系统填写 |
| `event_category` | `varchar(20)` | 否 | `NULL` | （库无注释） | 按业务台账填写（详见字段名） |
| `current_retest_round` | `int` | 否 | `0` | （库无注释） | 按业务台账填写（详见字段名） |
| `latest_retest_outcome` | `varchar(30)` | 否 | `NOT_TESTED` | （库无注释） | GIS/坐标 |
| `closure_confirmed_at` | `datetime(6)` | 是 | `NULL` | （库无注释） | 日期时间；按字段语义由人工或系统填写 |
| `closure_confirmed_by` | `bigint` | 是 | `NULL` | （库无注释） | 按业务台账填写（详见字段名） |
| `effective_status` | `varchar(30)` | 否 | `DRAFT` | （库无注释） | 业务状态 |
| `effective_at` | `datetime(6)` | 是 | `NULL` | （库无注释） | 日期时间；按字段语义由人工或系统填写 |
| `effective_by` | `bigint` | 是 | `NULL` | （库无注释） | 按业务台账填写（详见字段名） |
| `data_nature` | `varchar(20)` | 否 | `NULL` | （库无注释） | 数据性质（demo/正式） |
| `is_demo` | `tinyint(1)` | 否 | `0` | （库无注释） | 数据性质（demo/正式） |
| `active_original_result_id` | `bigint` | 是 | `NULL` | （库无注释） | 按业务台账填写（详见字段名） |
| `created_at` | `timestamp(6)` | 否 | `CURRENT_TIMESTAMP(6)` | （库无注释） | 日期时间；按字段语义由人工或系统填写 |
| `updated_at` | `timestamp(6)` | 否 | `CURRENT_TIMESTAMP(6)` | （库无注释） | 日期时间；按字段语义由人工或系统填写 |

外键：
- `case_id` → `e_closure_case.id`
- `original_result_id` → `e01_factor_result.id`

### 6.21 `carbon_emission_activity` — 碳排放活动数据

- **分类：** E / 业务事实表 / 必须人工录入
- **当前行数：** 6
- **库表注释：** 碳排放活动数据

| 字段名 | 类型 | 是否为空 | 默认值 | 说明（库注释） | 业务用途（模板建议） |
|---|---|---|---|---|---|
| `id` | `bigint` | 否 | `NULL` | （库无注释） | 系统主键，勿填 |
| `document_id` | `bigint` | 是 | `NULL` | （库无注释） | 文件/资料关联编号 |
| `period_value` | `varchar(50)` | 是 | `NULL` | （库无注释） | 按业务台账填写（详见字段名） |
| `diesel_usage` | `decimal(24,8)` | 是 | `NULL` | （库无注释） | 按业务台账填写（详见字段名） |
| `electricity_usage` | `decimal(24,8)` | 是 | `NULL` | （库无注释） | 按业务台账填写（详见字段名） |
| `material_usage` | `decimal(24,8)` | 是 | `NULL` | （库无注释） | 按业务台账填写（详见字段名） |
| `carbon_emission` | `decimal(18,4)` | 是 | `NULL` | （库无注释） | 按业务台账填写（详见字段名） |
| `created_at` | `datetime` | 否 | `CURRENT_TIMESTAMP` | （库无注释） | 日期时间；按字段语义由人工或系统填写 |
| `output_value_wan` | `decimal(18,4)` | 是 | `NULL` | 完成产值，万元 | 完成产值，万元 |
| `baseline_emission` | `decimal(18,4)` | 是 | `NULL` | 基准情景排放量 | 基准情景排放量 |
| `diesel_emission` | `decimal(18,4)` | 是 | `NULL` | 施工用油排放量 | 施工用油排放量 |
| `electricity_emission` | `decimal(18,4)` | 是 | `NULL` | 施工用电排放量 | 施工用电排放量 |
| `material_emission` | `decimal(18,4)` | 是 | `NULL` | 主要材料排放量 | 主要材料排放量 |
| `other_emission` | `decimal(18,4)` | 是 | `NULL` | 其他排放量 | 其他排放量 |
| `diesel_unit` | `varchar(30)` | 是 | `NULL` | 施工用油活动单位 | 施工用油活动单位 |
| `electricity_unit` | `varchar(30)` | 是 | `NULL` | 施工用电活动单位 | 施工用电活动单位 |
| `transport_usage` | `decimal(24,8)` | 是 | `NULL` | 施工运输活动量 | 施工运输活动量 |
| `transport_unit` | `varchar(30)` | 是 | `NULL` | 施工运输活动单位 | 施工运输活动单位 |
| `diesel_factor_id` | `bigint` | 是 | `NULL` | 施工用油排放因子ID | 施工用油排放因子ID |
| `electricity_factor_id` | `bigint` | 是 | `NULL` | 施工用电排放因子ID | 施工用电排放因子ID |
| `transport_factor_id` | `bigint` | 是 | `NULL` | 施工运输排放因子ID | 施工运输排放因子ID |
| `data_nature` | `varchar(30)` | 是 | `NULL` | 数据性质 | 数据性质 |
| `verification_status` | `varchar(40)` | 是 | `NULL` | 核验状态 | 核验状态 |
| `demo_note` | `varchar(255)` | 是 | `NULL` | 演示数据说明 | 演示数据说明 |
| `updated_at` | `datetime` | 是 | `CURRENT_TIMESTAMP` | 更新时间 | 更新时间 |
| `is_demo` | `tinyint(1)` | 否 | `0` | demo data flag | demo data flag |
| `effective_status` | `varchar(30)` | 是 | `NULL` | EFFECTIVE | INEFFECTIVE | NULL=待核实；正式KPI禁止IFNULL默认 | EFFECTIVE | INEFFECTIVE | NULL=待核实；正式KPI禁止IFNULL默认 |
| `evidence_status` | `varchar(40)` | 否 | `MISSING` | MISSING | PENDING | VERIFIED；禁止占位文件冒充 | MISSING | PENDING | VERIFIED；禁止占位文件冒充 |
| `boundary_version` | `varchar(80)` | 是 | `NULL` | 写入时边界版本（审计冗余） | 写入时边界版本（审计冗余） |
| `accounting_batch_id` | `bigint` | 是 | `NULL` | 核算批次ID | 核算批次ID |
| `is_current` | `tinyint(1)` | 否 | `1` | 当前有效标志；0=被替代/作废 | 当前有效标志；0=被替代/作废 |
| `diesel_factor_snapshot_id` | `bigint` | 是 | `NULL` | 施工用油因子快照ID | 施工用油因子快照ID |
| `electricity_factor_snapshot_id` | `bigint` | 是 | `NULL` | 施工用电因子快照ID | 施工用电因子快照ID |
| `material_factor_snapshot_id` | `bigint` | 是 | `NULL` | 主要材料因子快照ID（汇总引用） | 主要材料因子快照ID（汇总引用） |
| `transport_factor_snapshot_id` | `bigint` | 是 | `NULL` | 施工运输因子快照ID | 施工运输因子快照ID |

### 6.22 `carbon_material_usage` — 碳排放材料用量

- **分类：** E / 业务事实表 / 必须人工录入
- **当前行数：** 18
- **库表注释：** 碳排放材料用量

| 字段名 | 类型 | 是否为空 | 默认值 | 说明（库注释） | 业务用途（模板建议） |
|---|---|---|---|---|---|
| `id` | `bigint` | 否 | `NULL` | （库无注释） | 系统主键，勿填 |
| `document_id` | `bigint` | 是 | `NULL` | （库无注释） | 文件/资料关联编号 |
| `period_value` | `varchar(50)` | 是 | `NULL` | （库无注释） | 按业务台账填写（详见字段名） |
| `material_name` | `varchar(100)` | 是 | `NULL` | （库无注释） | 名称/标题，人工填写 |
| `material_usage` | `decimal(24,8)` | 是 | `NULL` | （库无注释） | 按业务台账填写（详见字段名） |
| `material_unit` | `varchar(30)` | 是 | `NULL` | （库无注释） | 组织/单位，建议下拉 |
| `created_at` | `datetime` | 否 | `CURRENT_TIMESTAMP` | （库无注释） | 日期时间；按字段语义由人工或系统填写 |
| `carbon_activity_id` | `bigint` | 是 | `NULL` | 关联月度碳排活动记录ID | 关联月度碳排活动记录ID |
| `emission_factor_id` | `bigint` | 是 | `NULL` | 排放因子ID | 排放因子ID |
| `carbon_emission` | `decimal(18,6)` | 是 | `NULL` | 材料分项排放量，tCO₂e | 材料分项排放量，tCO₂e |
| `data_nature` | `varchar(30)` | 是 | `NULL` | 数据性质 | 数据性质 |
| `verification_status` | `varchar(40)` | 是 | `NULL` | 核验状态 | 核验状态 |
| `demo_note` | `varchar(255)` | 是 | `NULL` | 演示数据说明 | 演示数据说明 |
| `updated_at` | `datetime` | 是 | `CURRENT_TIMESTAMP` | 更新时间 | 更新时间 |
| `is_demo` | `tinyint(1)` | 否 | `0` | demo data flag | demo data flag |
| `effective_status` | `varchar(30)` | 是 | `NULL` | EFFECTIVE | INEFFECTIVE | NULL=待核实 | EFFECTIVE | INEFFECTIVE | NULL=待核实 |
| `evidence_status` | `varchar(40)` | 否 | `MISSING` | MISSING | PENDING | VERIFIED | MISSING | PENDING | VERIFIED |
| `factor_snapshot_id` | `bigint` | 是 | `NULL` | 材料因子快照ID | 材料因子快照ID |
| `accounting_batch_id` | `bigint` | 是 | `NULL` | 核算批次ID | 核算批次ID |
| `is_current` | `tinyint(1)` | 否 | `1` | 当前有效标志 | 当前有效标志 |

### 6.23 `carbon_reduction_measure` — 低碳措施及成本台账

- **分类：** E / 业务事实表 / 必须人工录入
- **当前行数：** 4
- **库表注释：** 低碳措施及成本台账

| 字段名 | 类型 | 是否为空 | 默认值 | 说明（库注释） | 业务用途（模板建议） |
|---|---|---|---|---|---|
| `id` | `bigint` | 否 | `NULL` | （库无注释） | 系统主键，勿填 |
| `measure_code` | `varchar(80)` | 否 | `NULL` | （库无注释） | 业务编号，建议人工或按规则编制 |
| `measure_name` | `varchar(160)` | 否 | `NULL` | （库无注释） | 名称/标题，人工填写 |
| `measure_category` | `varchar(80)` | 否 | `NULL` | （库无注释） | 按业务台账填写（详见字段名） |
| `application_scope` | `varchar(255)` | 否 | `NULL` | （库无注释） | 按业务台账填写（详见字段名） |
| `responsible_department` | `varchar(100)` | 是 | `NULL` | （库无注释） | 组织/单位，建议下拉 |
| `start_date` | `date` | 是 | `NULL` | （库无注释） | 日期时间；按字段语义由人工或系统填写 |
| `end_date` | `date` | 是 | `NULL` | （库无注释） | 日期时间；按字段语义由人工或系统填写 |
| `implementation_status` | `varchar(40)` | 否 | `NULL` | （库无注释） | 业务状态 |
| `estimated_reduction` | `decimal(18,4)` | 是 | `NULL` | （库无注释） | 按业务台账填写（详见字段名） |
| `accounted_reduction` | `decimal(18,4)` | 是 | `NULL` | （库无注释） | 按业务台账填写（详见字段名） |
| `verified_reduction` | `decimal(18,4)` | 是 | `NULL` | （库无注释） | 按业务台账填写（详见字段名） |
| `reduction_unit` | `varchar(30)` | 否 | `NULL` | （库无注释） | 组织/单位，建议下拉 |
| `investment_cost` | `decimal(18,4)` | 否 | `0.0000` | （库无注释） | 按业务台账填写（详见字段名） |
| `operating_saving` | `decimal(18,4)` | 否 | `0.0000` | （库无注释） | 按业务台账填写（详见字段名） |
| `avoided_cost` | `decimal(18,4)` | 否 | `0.0000` | （库无注释） | 按业务台账填写（详见字段名） |
| `net_cost_impact` | `decimal(18,4)` | 否 | `0.0000` | （库无注释） | 按业务台账填写（详见字段名） |
| `currency_unit` | `varchar(30)` | 否 | `NULL` | （库无注释） | 组织/单位，建议下拉 |
| `calculation_method` | `varchar(255)` | 否 | `NULL` | （库无注释） | GIS/坐标 |
| `data_nature` | `varchar(30)` | 否 | `NULL` | （库无注释） | 数据性质（demo/正式） |
| `verification_status` | `varchar(40)` | 否 | `NULL` | （库无注释） | 业务状态 |
| `evidence_status` | `varchar(40)` | 否 | `NULL` | （库无注释） | 业务状态 |
| `is_demo` | `tinyint(1)` | 否 | `0` | （库无注释） | 数据性质（demo/正式） |
| `created_at` | `datetime` | 否 | `CURRENT_TIMESTAMP` | （库无注释） | 日期时间；按字段语义由人工或系统填写 |
| `updated_at` | `datetime` | 否 | `CURRENT_TIMESTAMP` | （库无注释） | 日期时间；按字段语义由人工或系统填写 |

### 6.24 `safety_risk_point` — 安全风险点

- **分类：** S / 业务事实表 / 必须人工录入
- **当前行数：** 10
- **库表注释：** 安全风险点

| 字段名 | 类型 | 是否为空 | 默认值 | 说明（库注释） | 业务用途（模板建议） |
|---|---|---|---|---|---|
| `id` | `bigint` | 否 | `NULL` | （库无注释） | 系统主键，勿填 |
| `document_id` | `bigint` | 是 | `NULL` | （库无注释） | 文件/资料关联编号 |
| `risk_name` | `varchar(255)` | 是 | `NULL` | （库无注释） | 名称/标题，人工填写 |
| `risk_level` | `varchar(50)` | 是 | `NULL` | （库无注释） | 风险相关属性 |
| `control_status` | `varchar(50)` | 是 | `NULL` | （库无注释） | 业务状态 |
| `control_measure` | `text` | 是 | `NULL` | （库无注释） | 按业务台账填写（详见字段名） |
| `location` | `varchar(255)` | 是 | `NULL` | （库无注释） | 按业务台账填写（详见字段名） |
| `created_at` | `datetime` | 否 | `CURRENT_TIMESTAMP` | （库无注释） | 日期时间；按字段语义由人工或系统填写 |
| `risk_type` | `varchar(100)` | 是 | `NULL` | 风险类型 | 风险类型 |
| `control_start_date` | `date` | 是 | `NULL` | 管控起始日期 | 管控起始日期 |
| `cancelled_date` | `date` | 是 | `NULL` | 销号日期 | 销号日期 |

### 6.25 `safety_incident_record` — 安全生产事故台账

- **分类：** S / 业务事实表 / 必须人工录入
- **当前行数：** 0
- **库表注释：** 安全生产事故台账

| 字段名 | 类型 | 是否为空 | 默认值 | 说明（库注释） | 业务用途（模板建议） |
|---|---|---|---|---|---|
| `id` | `bigint` | 否 | `NULL` | （库无注释） | 系统主键，勿填 |
| `project_id` | `varchar(50)` | 否 | `LUOYI-ESG` | 项目标识 | 项目标识 |
| `incident_code` | `varchar(60)` | 是 | `NULL` | 事故编码 | 事故编码 |
| `occurred_date` | `date` | 是 | `NULL` | 事故发生日期（冻结稿口径） | 事故发生日期（冻结稿口径） |
| `document_id` | `bigint` | 是 | `NULL` | （库无注释） | 文件/资料关联编号 |
| `incident_date` | `date` | 否 | `NULL` | （库无注释） | 日期时间；按字段语义由人工或系统填写 |
| `incident_name` | `varchar(255)` | 是 | `NULL` | （库无注释） | 名称/标题，人工填写 |
| `incident_type` | `varchar(100)` | 是 | `NULL` | （库无注释） | 按业务台账填写（详见字段名） |
| `incident_category` | `varchar(50)` | 是 | `NULL` | 事故分类 | 事故分类 |
| `description` | `text` | 是 | `NULL` | 事故描述 | 事故描述 |
| `segment_name` | `varchar(100)` | 是 | `NULL` | 标段名称 | 标段名称 |
| `responsible_unit` | `varchar(200)` | 是 | `NULL` | 责任单位 | 责任单位 |
| `fatality_count` | `int` | 否 | `0` | 死亡人数 | 死亡人数 |
| `injury_count` | `int` | 否 | `0` | 受伤人数 | 受伤人数 |
| `responsibility_determination_status` | `varchar(30)` | 否 | `PENDING` | PENDING / RESPONSIBLE / NON_RESPONSIBLE | PENDING / RESPONSIBLE / NON_RESPONSIBLE |
| `determination_effective_date` | `date` | 是 | `NULL` | 认定生效日期 | 认定生效日期 |
| `determination_summary` | `varchar(500)` | 是 | `NULL` | 认定摘要 | 认定摘要 |
| `incident_level` | `varchar(50)` | 是 | `NULL` | （库无注释） | 按业务台账填写（详见字段名） |
| `interrupt_counting` | `tinyint` | 否 | `1` | （库无注释） | 按业务台账填写（详见字段名） |
| `responsible_department` | `varchar(100)` | 是 | `NULL` | （库无注释） | 组织/单位，建议下拉 |
| `handling_status` | `varchar(50)` | 是 | `NULL` | （库无注释） | 业务状态 |
| `interrupt_reason` | `varchar(255)` | 是 | `NULL` | （库无注释） | 按业务台账填写（详见字段名） |
| `effective_status` | `varchar(30)` | 否 | `DRAFT` | DRAFT / EFFECTIVE / INEFFECTIVE | DRAFT / EFFECTIVE / INEFFECTIVE |
| `is_current` | `tinyint(1)` | 否 | `1` | 当前有效版本 | 当前有效版本 |
| `effective_at` | `datetime(6)` | 是 | `NULL` | 生效时间 | 生效时间 |
| `effective_by` | `bigint` | 是 | `NULL` | 生效操作人 | 生效操作人 |
| `data_nature` | `varchar(20)` | 否 | `demo` | demo / formal | demo / formal |
| `is_demo` | `tinyint(1)` | 否 | `1` | 是否演示数据（旧行默认 demo） | 是否演示数据（旧行默认 demo） |
| `demo_batch_code` | `varchar(60)` | 是 | `NULL` | 关联演示批次编码 | 关联演示批次编码 |
| `source_document_id` | `bigint` | 是 | `NULL` | 来源资料ID | 来源资料ID |
| `remark` | `varchar(500)` | 是 | `NULL` | 备注 | 备注 |
| `created_at` | `datetime` | 否 | `CURRENT_TIMESTAMP` | （库无注释） | 日期时间；按字段语义由人工或系统填写 |
| `updated_at` | `timestamp(6)` | 否 | `CURRENT_TIMESTAMP(6)` | 更新时间 | 更新时间 |

### 6.26 `safety_production_record` — 连续安全生产记录

- **分类：** S / 业务事实表 / 必须人工录入
- **当前行数：** 2
- **库表注释：** 连续安全生产记录

| 字段名 | 类型 | 是否为空 | 默认值 | 说明（库注释） | 业务用途（模板建议） |
|---|---|---|---|---|---|
| `id` | `bigint` | 否 | `NULL` | （库无注释） | 系统主键，勿填 |
| `project_id` | `varchar(50)` | 否 | `LUOYI-ESG` | 项目标识 | 项目标识 |
| `project_start_date` | `date` | 否 | `NULL` | （库无注释） | 日期时间；按字段语义由人工或系统填写 |
| `current_date` | `date` | 否 | `NULL` | （库无注释） | 日期时间；按字段语义由人工或系统填写 |
| `statistics_as_of` | `date` | 是 | `NULL` | 统计期末 | 统计期末 |
| `cycle_start_date` | `date` | 是 | `NULL` | 当前安全生产周期起点 | 当前安全生产周期起点 |
| `continuous_days` | `int` | 否 | `NULL` | （库无注释） | 按业务台账填写（详见字段名） |
| `confirmation_batch_id` | `bigint` | 是 | `NULL` | 关联确认批次ID | 关联确认批次ID |
| `confirmation_status` | `varchar(30)` | 否 | `PENDING` | PENDING / CONFIRMED | PENDING / CONFIRMED |
| `verification_status` | `varchar(30)` | 否 | `PENDING_REVIEW` | PENDING_REVIEW / VERIFIED / REJECTED | PENDING_REVIEW / VERIFIED / REJECTED |
| `effective_status` | `varchar(30)` | 否 | `DRAFT` | DRAFT / EFFECTIVE / INEFFECTIVE | DRAFT / EFFECTIVE / INEFFECTIVE |
| `is_current` | `tinyint(1)` | 否 | `1` | 当前有效快照 | 当前有效快照 |
| `data_nature` | `varchar(20)` | 否 | `demo` | demo / formal | demo / formal |
| `is_demo` | `tinyint(1)` | 否 | `0` | 是否演示数据 | 是否演示数据 |
| `confirmed_at` | `datetime(6)` | 是 | `NULL` | 确认时间 | 确认时间 |
| `confirmed_by` | `varchar(100)` | 是 | `NULL` | 确认人 | 确认人 |
| `current_stage` | `varchar(100)` | 是 | `NULL` | （库无注释） | 按业务台账填写（详见字段名） |
| `current_stage_detail` | `varchar(255)` | 是 | `NULL` | （库无注释） | 按业务台账填写（详见字段名） |
| `counting_status` | `varchar(30)` | 否 | `NULL` | （库无注释） | 业务状态 |
| `update_time` | `datetime` | 否 | `NULL` | （库无注释） | 日期时间；按字段语义由人工或系统填写 |
| `created_at` | `datetime` | 否 | `CURRENT_TIMESTAMP` | （库无注释） | 日期时间；按字段语义由人工或系统填写 |
| `updated_at` | `timestamp(6)` | 否 | `CURRENT_TIMESTAMP(6)` | 更新时间 | 更新时间 |

### 6.27 `s01_confirmation_batch` — S01 建设单位确认批次

- **分类：** S / 业务事实表 / 必须人工录入
- **当前行数：** 1
- **库表注释：** S01 建设单位确认批次

| 字段名 | 类型 | 是否为空 | 默认值 | 说明（库注释） | 业务用途（模板建议） |
|---|---|---|---|---|---|
| `id` | `bigint` | 否 | `NULL` | （库无注释） | 系统主键，勿填 |
| `batch_code` | `varchar(60)` | 否 | `NULL` | 批次编码，如 DEMO-S01-20260724 | 批次编码，如 DEMO-S01-20260724 |
| `project_id` | `varchar(50)` | 否 | `LUOYI-ESG` | 项目标识 | 项目标识 |
| `confirmation_month` | `varchar(7)` | 否 | `NULL` | 确认月份，如 2026-07 | 确认月份，如 2026-07 |
| `statistics_as_of` | `date` | 否 | `NULL` | 统计期末业务日期 | 统计期末业务日期 |
| `cycle_start_date` | `date` | 否 | `NULL` | 当前安全生产周期起点 | 当前安全生产周期起点 |
| `continuous_days` | `int` | 否 | `NULL` | 后端按冻结算法生成的快照值 | 后端按冻结算法生成的快照值 |
| `counting_status` | `varchar(30)` | 否 | `NULL` | CONTINUOUS / PENDING_DETERMINATION / RESET_CYCLE | CONTINUOUS / PENDING_DETERMINATION / RESET_CYCLE |
| `confirmation_unit` | `varchar(200)` | 是 | `NULL` | 确认单位名称 | 确认单位名称 |
| `confirmed_by` | `varchar(100)` | 是 | `NULL` | 确认人 | 确认人 |
| `confirmed_at` | `datetime(6)` | 是 | `NULL` | 确认时间 | 确认时间 |
| `confirmation_status` | `varchar(30)` | 否 | `PENDING` | PENDING / CONFIRMED | PENDING / CONFIRMED |
| `verification_status` | `varchar(30)` | 否 | `PENDING_REVIEW` | PENDING_REVIEW / VERIFIED / REJECTED | PENDING_REVIEW / VERIFIED / REJECTED |
| `effective_status` | `varchar(30)` | 否 | `DRAFT` | DRAFT / EFFECTIVE / INEFFECTIVE | DRAFT / EFFECTIVE / INEFFECTIVE |
| `effective_at` | `datetime(6)` | 是 | `NULL` | 生效时间 | 生效时间 |
| `data_nature` | `varchar(20)` | 否 | `NULL` | demo / formal | demo / formal |
| `is_demo` | `tinyint(1)` | 否 | `0` | 是否演示数据 | 是否演示数据 |
| `version_no` | `int` | 否 | `1` | 批次版本号 | 批次版本号 |
| `remark` | `varchar(500)` | 是 | `NULL` | 备注 | 备注 |
| `created_at` | `timestamp(6)` | 否 | `CURRENT_TIMESTAMP(6)` | （库无注释） | 日期时间；按字段语义由人工或系统填写 |
| `updated_at` | `timestamp(6)` | 否 | `CURRENT_TIMESTAMP(6)` | （库无注释） | 日期时间；按字段语义由人工或系统填写 |

### 6.28 `labor_dispute_record` — 劳务纠纷记录

- **分类：** S / 业务事实表 / 必须人工录入
- **当前行数：** 3
- **库表注释：** 劳务纠纷记录

| 字段名 | 类型 | 是否为空 | 默认值 | 说明（库注释） | 业务用途（模板建议） |
|---|---|---|---|---|---|
| `id` | `bigint` | 否 | `NULL` | （库无注释） | 系统主键，勿填 |
| `document_id` | `bigint` | 是 | `NULL` | （库无注释） | 文件/资料关联编号 |
| `dispute_type` | `varchar(100)` | 是 | `NULL` | （库无注释） | 按业务台账填写（详见字段名） |
| `status` | `varchar(50)` | 是 | `NULL` | （库无注释） | 业务状态 |
| `involved_people` | `int` | 是 | `NULL` | （库无注释） | 按业务台账填写（详见字段名） |
| `overdue` | `tinyint` | 否 | `0` | （库无注释） | 按业务台账填写（详见字段名） |
| `created_at` | `datetime` | 否 | `CURRENT_TIMESTAMP` | （库无注释） | 日期时间；按字段语义由人工或系统填写 |
| `dispute_name` | `varchar(255)` | 是 | `NULL` | 纠纷事项 | 纠纷事项 |
| `occurred_date` | `date` | 是 | `NULL` | 发生时间 | 发生时间 |
| `amount_wan` | `decimal(18,2)` | 是 | `NULL` | 涉及金额，万元 | 涉及金额，万元 |
| `responsible_department` | `varchar(100)` | 是 | `NULL` | 责任部门 | 责任部门 |
| `closed_date` | `date` | 是 | `NULL` | 办结日期 | 办结日期 |
| `data_nature` | `varchar(30)` | 否 | `formal` | formal | demo | formal | demo |
| `is_demo` | `tinyint` | 否 | `0` | 0=formal 1=demo | 0=formal 1=demo |

### 6.29 `salary_payment_record` — 工资支付记录

- **分类：** S / 业务事实表 / 必须人工录入
- **当前行数：** 0
- **库表注释：** 工资支付记录

| 字段名 | 类型 | 是否为空 | 默认值 | 说明（库注释） | 业务用途（模板建议） |
|---|---|---|---|---|---|
| `id` | `bigint` | 否 | `NULL` | （库无注释） | 系统主键，勿填 |
| `document_id` | `bigint` | 是 | `NULL` | （库无注释） | 文件/资料关联编号 |
| `payment_month` | `varchar(50)` | 是 | `NULL` | （库无注释） | 按业务台账填写（详见字段名） |
| `worker_count` | `int` | 是 | `NULL` | （库无注释） | 按业务台账填写（详见字段名） |
| `payment_amount` | `decimal(18,2)` | 是 | `NULL` | （库无注释） | 按业务台账填写（详见字段名） |
| `payment_status` | `varchar(50)` | 是 | `NULL` | （库无注释） | 业务状态 |
| `created_at` | `datetime` | 否 | `CURRENT_TIMESTAMP` | （库无注释） | 日期时间；按字段语义由人工或系统填写 |

### 6.30 `biz_worker_payment_summary` — Demo S03 工资支付周期汇总

- **分类：** S / 业务事实表 / 必须人工录入
- **当前行数：** 2
- **库表注释：** Demo S03 工资支付周期汇总

| 字段名 | 类型 | 是否为空 | 默认值 | 说明（库注释） | 业务用途（模板建议） |
|---|---|---|---|---|---|
| `id` | `bigint unsigned` | 否 | `NULL` | （库无注释） | 系统主键，勿填 |
| `project_id` | `bigint unsigned` | 否 | `NULL` | （库无注释） | 项目归属，模板建议下拉/固定项目编号映射 |
| `section_id` | `bigint unsigned` | 是 | `NULL` | （库无注释） | 标段，建议下拉 |
| `period_start` | `date` | 否 | `NULL` | （库无注释） | 按业务台账填写（详见字段名） |
| `period_end` | `date` | 否 | `NULL` | （库无注释） | 按业务台账填写（详见字段名） |
| `responsible_org_id` | `bigint unsigned` | 是 | `NULL` | （库无注释） | 组织/单位，建议下拉 |
| `worker_count` | `int unsigned` | 否 | `0` | （库无注释） | 按业务台账填写（详见字段名） |
| `payable_amount` | `decimal(18,2)` | 否 | `0.00` | （库无注释） | 按业务台账填写（详见字段名） |
| `paid_amount` | `decimal(18,2)` | 否 | `0.00` | （库无注释） | 按业务台账填写（详见字段名） |
| `payment_rate` | `decimal(5,2)` | 否 | `0.00` | （库无注释） | 按业务台账填写（详见字段名） |
| `payment_status` | `varchar(32)` | 否 | `NULL` | （库无注释） | 业务状态 |
| `overdue_amount` | `decimal(18,2)` | 否 | `0.00` | （库无注释） | 按业务台账填写（详见字段名） |
| `dispute_count` | `int unsigned` | 否 | `0` | （库无注释） | 按业务台账填写（详见字段名） |
| `risk_status` | `varchar(16)` | 否 | `NORMAL` | （库无注释） | 业务状态 |
| `source_doc_ref` | `varchar(255)` | 是 | `NULL` | （库无注释） | 按业务台账填写（详见字段名） |
| `updated_at` | `datetime` | 否 | `CURRENT_TIMESTAMP` | （库无注释） | 日期时间；按字段语义由人工或系统填写 |
| `is_deleted` | `tinyint unsigned` | 否 | `0` | （库无注释） | 逻辑删除标记，模板通常不填 |
| `source_type` | `varchar(32)` | 是 | `NULL` | Data source type, such as finance system or manual entry | Data source type, such as finance system or manual entry |
| `record_date` | `date` | 是 | `NULL` | Actual entry or source record date; not derived from updated_at | Actual entry or source record date; not derived from updated_at |
| `created_at` | `datetime` | 是 | `NULL` | Technical creation time | Technical creation time |

### 6.31 `appeal_record` — 群众诉求记录

- **分类：** S / 业务事实表 / 必须人工录入
- **当前行数：** 7
- **库表注释：** 群众诉求记录

| 字段名 | 类型 | 是否为空 | 默认值 | 说明（库注释） | 业务用途（模板建议） |
|---|---|---|---|---|---|
| `id` | `bigint` | 否 | `NULL` | （库无注释） | 系统主键，勿填 |
| `document_id` | `bigint` | 是 | `NULL` | （库无注释） | 文件/资料关联编号 |
| `appeal_type` | `varchar(100)` | 是 | `NULL` | （库无注释） | 按业务台账填写（详见字段名） |
| `status` | `varchar(50)` | 是 | `NULL` | （库无注释） | 业务状态 |
| `source_channel` | `varchar(100)` | 是 | `NULL` | （库无注释） | 按业务台账填写（详见字段名） |
| `overdue` | `tinyint` | 否 | `0` | （库无注释） | 按业务台账填写（详见字段名） |
| `created_at` | `datetime` | 否 | `CURRENT_TIMESTAMP` | （库无注释） | 日期时间；按字段语义由人工或系统填写 |
| `appeal_content` | `varchar(500)` | 是 | `NULL` | 诉求内容 | 诉求内容 |
| `accepted_date` | `date` | 是 | `NULL` | 受理时间 | 受理时间 |
| `location` | `varchar(255)` | 是 | `NULL` | 涉及地点 | 涉及地点 |
| `deadline` | `date` | 是 | `NULL` | 办结期限 | 办结期限 |
| `closed_date` | `date` | 是 | `NULL` | 办结日期 | 办结日期 |
| `duration_days` | `int` | 是 | `NULL` | 办理时长 | 办理时长 |

### 6.32 `compliance_procedure` — 合规手续

- **分类：** G / 业务事实表 / 必须人工录入
- **当前行数：** 7
- **库表注释：** 合规手续

| 字段名 | 类型 | 是否为空 | 默认值 | 说明（库注释） | 业务用途（模板建议） |
|---|---|---|---|---|---|
| `id` | `bigint` | 否 | `NULL` | （库无注释） | 系统主键，勿填 |
| `document_id` | `bigint` | 是 | `NULL` | （库无注释） | 文件/资料关联编号 |
| `procedure_name` | `varchar(255)` | 是 | `NULL` | （库无注释） | 名称/标题，人工填写 |
| `status` | `varchar(50)` | 是 | `NULL` | （库无注释） | 业务状态 |
| `impact_node` | `varchar(100)` | 是 | `NULL` | （库无注释） | 按业务台账填写（详见字段名） |
| `overdue` | `tinyint` | 否 | `0` | （库无注释） | 按业务台账填写（详见字段名） |
| `created_at` | `datetime` | 否 | `CURRENT_TIMESTAMP` | （库无注释） | 日期时间；按字段语义由人工或系统填写 |
| `procedure_type` | `varchar(100)` | 是 | `NULL` | 审批类型 | 审批类型 |
| `deadline` | `date` | 是 | `NULL` | 完成时限 | 完成时限 |
| `responsible_department` | `varchar(100)` | 是 | `NULL` | 责任部门 | 责任部门 |
| `progress_percent` | `int` | 是 | `NULL` | 办理进度百分比 | 办理进度百分比 |
| `completed_date` | `date` | 是 | `NULL` | 完成日期 | 完成日期 |
| `expected_complete_date` | `date` | 是 | `NULL` | 预计完成日期 | 预计完成日期 |
| `project_id` | `bigint` | 是 | `NULL` | Project ownership; new API writes must provide this value | Project ownership; new API writes must provide this value |

### 6.33 `permit_record` — 许可事项

- **分类：** G / 业务事实表 / 必须人工录入
- **当前行数：** 5
- **库表注释：** 许可事项

| 字段名 | 类型 | 是否为空 | 默认值 | 说明（库注释） | 业务用途（模板建议） |
|---|---|---|---|---|---|
| `id` | `bigint` | 否 | `NULL` | （库无注释） | 系统主键，勿填 |
| `document_id` | `bigint` | 是 | `NULL` | （库无注释） | 文件/资料关联编号 |
| `permit_name` | `varchar(255)` | 是 | `NULL` | （库无注释） | 名称/标题，人工填写 |
| `permit_no` | `varchar(100)` | 是 | `NULL` | （库无注释） | 按业务台账填写（详见字段名） |
| `expire_date` | `date` | 是 | `NULL` | （库无注释） | 日期时间；按字段语义由人工或系统填写 |
| `status` | `varchar(50)` | 是 | `NULL` | （库无注释） | 业务状态 |
| `created_at` | `datetime` | 否 | `CURRENT_TIMESTAMP` | （库无注释） | 日期时间；按字段语义由人工或系统填写 |
| `permit_type` | `varchar(100)` | 是 | `NULL` | 许可类型 | 许可类型 |
| `responsible_department` | `varchar(100)` | 是 | `NULL` | 责任部门 | 责任部门 |
| `project_id` | `bigint` | 是 | `NULL` | Project ownership; new API writes must provide this value | Project ownership; new API writes must provide this value |

### 6.34 `special_plan_approval` — 风险专项方案审批事实

- **分类：** G / 业务事实表 / 必须人工录入
- **当前行数：** 0
- **库表注释：** ESG risk special-plan approval facts

| 字段名 | 类型 | 是否为空 | 默认值 | 说明（库注释） | 业务用途（模板建议） |
|---|---|---|---|---|---|
| `id` | `bigint` | 否 | `NULL` | （库无注释） | 系统主键，勿填 |
| `project_id` | `bigint` | 否 | `NULL` | Project ownership; required for every new fact | 项目归属（必填） |
| `risk_point_id` | `bigint` | 否 | `NULL` | Reference to safety_risk_point.id | 关联安全风险点 ID（下拉） |
| `plan_code` | `varchar(80)` | 否 | `NULL` | Project-scoped special-plan code | 项目内专项方案编号（唯一） |
| `plan_name` | `varchar(255)` | 否 | `NULL` | Special-plan name | 专项方案名称 |
| `risk_level` | `varchar(50)` | 否 | `NULL` | Existing project risk-level value; no new levels are defined here | 风险等级（沿用现有字典） |
| `approval_status` | `varchar(40)` | 否 | `NULL` | Existing project approval-status value | 审批状态（沿用现有字典） |
| `approval_date` | `date` | 是 | `NULL` | Approval completion date | 审批完成日期（人工填写，勿自动生成） |
| `approval_file_id` | `bigint` | 是 | `NULL` | Reference to file_asset.id | 审批文件关联（先上传再填文件 ID） |
| `source_doc_ref` | `varchar(255)` | 是 | `NULL` | Source document reference | 来源资料编号 |
| `data_nature` | `varchar(20)` | 否 | `demo` | demo/formal/platform_calc | 数据性质（demo/正式） |
| `is_demo` | `tinyint(1)` | 否 | `1` | （库无注释） | Demo 标识 |
| `created_at` | `datetime` | 否 | `CURRENT_TIMESTAMP` | （库无注释） | 系统创建时间，勿填 |
| `updated_at` | `datetime` | 否 | `CURRENT_TIMESTAMP` | （库无注释） | 系统更新时间，勿填 |

外键：
- `approval_file_id` → `file_asset.id`
- `risk_point_id` → `safety_risk_point.id`

### 6.35 `biz_design_change` — Demo G03 设计变更

- **分类：** G / 业务事实表 / 必须人工录入
- **当前行数：** 4
- **库表注释：** Demo G03 设计变更

| 字段名 | 类型 | 是否为空 | 默认值 | 说明（库注释） | 业务用途（模板建议） |
|---|---|---|---|---|---|
| `id` | `bigint unsigned` | 否 | `NULL` | （库无注释） | 系统主键，勿填 |
| `project_id` | `bigint unsigned` | 否 | `NULL` | （库无注释） | 项目归属，模板建议下拉/固定项目编号映射 |
| `section_id` | `bigint unsigned` | 是 | `NULL` | （库无注释） | 标段，建议下拉 |
| `work_point_id` | `bigint unsigned` | 是 | `NULL` | （库无注释） | 按业务台账填写（详见字段名） |
| `change_code` | `varchar(64)` | 否 | `NULL` | （库无注释） | 业务编号，建议人工或按规则编制 |
| `change_type` | `varchar(64)` | 否 | `NULL` | （库无注释） | 按业务台账填写（详见字段名） |
| `change_name` | `varchar(255)` | 否 | `NULL` | （库无注释） | 名称/标题，人工填写 |
| `location_desc` | `varchar(500)` | 是 | `NULL` | （库无注释） | 备注说明 |
| `change_reason` | `varchar(1000)` | 是 | `NULL` | （库无注释） | 按业务台账填写（详见字段名） |
| `apply_date` | `date` | 否 | `NULL` | （库无注释） | 日期时间；按字段语义由人工或系统填写 |
| `approve_status` | `varchar(32)` | 否 | `NULL` | （库无注释） | 业务状态 |
| `approve_date` | `date` | 是 | `NULL` | （库无注释） | 日期时间；按字段语义由人工或系统填写 |
| `implementation_status` | `varchar(32)` | 否 | `NULL` | （库无注释） | 业务状态 |
| `attachment_status` | `varchar(32)` | 否 | `NULL` | （库无注释） | 业务状态 |
| `responsible_org_id` | `bigint unsigned` | 是 | `NULL` | （库无注释） | 组织/单位，建议下拉 |
| `risk_status` | `varchar(16)` | 否 | `NORMAL` | （库无注释） | 业务状态 |
| `source_doc_ref` | `varchar(255)` | 是 | `NULL` | （库无注释） | 按业务台账填写（详见字段名） |
| `updated_at` | `datetime` | 否 | `CURRENT_TIMESTAMP` | （库无注释） | 日期时间；按字段语义由人工或系统填写 |
| `is_deleted` | `tinyint unsigned` | 否 | `0` | （库无注释） | 逻辑删除标记，模板通常不填 |

### 6.36 `biz_internal_control_issue` — Demo G04 内控廉洁问题

- **分类：** G / 业务事实表 / 必须人工录入
- **当前行数：** 2
- **库表注释：** Demo G04 内控廉洁问题

| 字段名 | 类型 | 是否为空 | 默认值 | 说明（库注释） | 业务用途（模板建议） |
|---|---|---|---|---|---|
| `id` | `bigint unsigned` | 否 | `NULL` | （库无注释） | 系统主键，勿填 |
| `project_id` | `bigint unsigned` | 否 | `NULL` | （库无注释） | 项目归属，模板建议下拉/固定项目编号映射 |
| `section_id` | `bigint unsigned` | 是 | `NULL` | （库无注释） | 标段，建议下拉 |
| `issue_code` | `varchar(64)` | 否 | `NULL` | （库无注释） | 业务编号，建议人工或按规则编制 |
| `issue_type` | `varchar(64)` | 否 | `NULL` | （库无注释） | 按业务台账填写（详见字段名） |
| `issue_level` | `varchar(16)` | 否 | `NULL` | （库无注释） | 按业务台账填写（详见字段名） |
| `issue_description` | `varchar(1000)` | 否 | `NULL` | （库无注释） | 备注说明 |
| `found_at` | `datetime` | 否 | `NULL` | （库无注释） | 日期时间；按字段语义由人工或系统填写 |
| `responsible_org_id` | `bigint unsigned` | 是 | `NULL` | （库无注释） | 组织/单位，建议下拉 |
| `current_status` | `varchar(32)` | 否 | `NULL` | （库无注释） | 业务状态 |
| `deadline` | `date` | 是 | `NULL` | （库无注释） | 按业务台账填写（详见字段名） |
| `closed_at` | `date` | 是 | `NULL` | （库无注释） | 日期时间；按字段语义由人工或系统填写 |
| `recurrence_flag` | `tinyint unsigned` | 否 | `0` | （库无注释） | 按业务台账填写（详见字段名） |
| `evidence_status` | `varchar(32)` | 否 | `NULL` | （库无注释） | 业务状态 |
| `risk_status` | `varchar(16)` | 否 | `NORMAL` | （库无注释） | 业务状态 |
| `source_doc_ref` | `varchar(255)` | 是 | `NULL` | （库无注释） | 按业务台账填写（详见字段名） |
| `updated_at` | `datetime` | 否 | `CURRENT_TIMESTAMP` | （库无注释） | 日期时间；按字段语义由人工或系统填写 |
| `is_deleted` | `tinyint unsigned` | 否 | `0` | （库无注释） | 逻辑删除标记，模板通常不填 |

### 6.37 `biz_night_construction_record` — Demo G02 夜间施工记录

- **分类：** G / 业务事实表 / 必须人工录入
- **当前行数：** 2
- **库表注释：** Demo G02 夜间施工记录

| 字段名 | 类型 | 是否为空 | 默认值 | 说明（库注释） | 业务用途（模板建议） |
|---|---|---|---|---|---|
| `id` | `bigint unsigned` | 否 | `NULL` | （库无注释） | 系统主键，勿填 |
| `project_id` | `bigint unsigned` | 否 | `NULL` | （库无注释） | 项目归属，模板建议下拉/固定项目编号映射 |
| `section_id` | `bigint unsigned` | 是 | `NULL` | （库无注释） | 标段，建议下拉 |
| `work_point_id` | `bigint unsigned` | 是 | `NULL` | （库无注释） | 按业务台账填写（详见字段名） |
| `record_code` | `varchar(64)` | 否 | `NULL` | （库无注释） | 业务编号，建议人工或按规则编制 |
| `construction_date` | `date` | 否 | `NULL` | （库无注释） | 日期时间；按字段语义由人工或系统填写 |
| `start_time` | `datetime` | 否 | `NULL` | （库无注释） | 日期时间；按字段语义由人工或系统填写 |
| `end_time` | `datetime` | 否 | `NULL` | （库无注释） | 日期时间；按字段语义由人工或系统填写 |
| `permit_id` | `bigint unsigned` | 是 | `NULL` | （库无注释） | 按业务台账填写（详见字段名） |
| `permit_status` | `varchar(32)` | 否 | `NULL` | （库无注释） | 业务状态 |
| `approval_status` | `varchar(32)` | 否 | `NULL` | （库无注释） | 业务状态 |
| `noise_measure` | `varchar(500)` | 是 | `NULL` | （库无注释） | 按业务台账填写（详见字段名） |
| `responsible_org_id` | `bigint unsigned` | 是 | `NULL` | （库无注释） | 组织/单位，建议下拉 |
| `risk_status` | `varchar(16)` | 否 | `NORMAL` | （库无注释） | 业务状态 |
| `source_doc_ref` | `varchar(255)` | 是 | `NULL` | （库无注释） | 按业务台账填写（详见字段名） |
| `updated_at` | `datetime` | 否 | `CURRENT_TIMESTAMP` | （库无注释） | 日期时间；按字段语义由人工或系统填写 |
| `is_deleted` | `tinyint unsigned` | 否 | `0` | （库无注释） | 逻辑删除标记，模板通常不填 |

### 6.38 `rectification_record` — 整改事项

- **分类：** G / 业务事实表 / 必须人工录入
- **当前行数：** 9
- **库表注释：** 整改事项

| 字段名 | 类型 | 是否为空 | 默认值 | 说明（库注释） | 业务用途（模板建议） |
|---|---|---|---|---|---|
| `id` | `bigint` | 否 | `NULL` | （库无注释） | 系统主键，勿填 |
| `document_id` | `bigint` | 是 | `NULL` | （库无注释） | 文件/资料关联编号 |
| `item_name` | `varchar(255)` | 是 | `NULL` | （库无注释） | 名称/标题，人工填写 |
| `status` | `varchar(50)` | 是 | `NULL` | （库无注释） | 业务状态 |
| `source_type` | `varchar(100)` | 是 | `NULL` | （库无注释） | 按业务台账填写（详见字段名） |
| `overdue` | `tinyint` | 否 | `0` | （库无注释） | 按业务台账填写（详见字段名） |
| `closed_date` | `date` | 是 | `NULL` | （库无注释） | 日期时间；按字段语义由人工或系统填写 |
| `created_at` | `datetime` | 否 | `CURRENT_TIMESTAMP` | （库无注释） | 日期时间；按字段语义由人工或系统填写 |
| `issue_level` | `varchar(50)` | 是 | `NULL` | 问题等级 | 问题等级 |
| `deadline` | `date` | 是 | `NULL` | 整改时限 | 整改时限 |
| `responsible_department` | `varchar(100)` | 是 | `NULL` | 责任部门 | 责任部门 |
| `check_batch` | `varchar(100)` | 是 | `NULL` | 检查批次，用于统计涉及检查次数 | 检查批次，用于统计涉及检查次数 |

### 6.39 `e_closure_case` — 事项闭环案件

- **分类：** 综合 / 业务事实表 / 必须人工录入
- **当前行数：** 17

| 字段名 | 类型 | 是否为空 | 默认值 | 说明（库注释） | 业务用途（模板建议） |
|---|---|---|---|---|---|
| `id` | `bigint` | 否 | `NULL` | （库无注释） | 系统主键，勿填 |
| `case_code` | `varchar(80)` | 否 | `NULL` | （库无注释） | 业务编号，建议人工或按规则编制 |
| `case_domain` | `varchar(30)` | 否 | `NULL` | （库无注释） | 按业务台账填写（详见字段名） |
| `source_table` | `varchar(80)` | 否 | `NULL` | （库无注释） | 按业务台账填写（详见字段名） |
| `source_record_id` | `bigint` | 否 | `NULL` | （库无注释） | 按业务台账填写（详见字段名） |
| `source_business_key` | `varchar(160)` | 是 | `NULL` | （库无注释） | 按业务台账填写（详见字段名） |
| `source_document_id` | `bigint` | 是 | `NULL` | （库无注释） | 文件/资料关联编号 |
| `title` | `varchar(255)` | 否 | `NULL` | （库无注释） | 名称/标题，人工填写 |
| `location_text` | `varchar(255)` | 是 | `NULL` | （库无注释） | 按业务台账填写（详见字段名） |
| `gis_feature_id` | `varchar(96)` | 是 | `NULL` | （库无注释） | GIS/坐标 |
| `current_status` | `varchar(40)` | 否 | `DISCOVERED` | （库无注释） | 业务状态 |
| `current_status_history_id` | `bigint` | 是 | `NULL` | （库无注释） | 业务状态 |
| `priority` | `varchar(30)` | 是 | `NULL` | （库无注释） | 按业务台账填写（详见字段名） |
| `severity` | `varchar(30)` | 是 | `NULL` | （库无注释） | 按业务台账填写（详见字段名） |
| `deadline` | `datetime(6)` | 是 | `NULL` | （库无注释） | 按业务台账填写（详见字段名） |
| `discovery_org_id` | `bigint` | 是 | `NULL` | （库无注释） | 组织/单位，建议下拉 |
| `responsible_org_id` | `bigint` | 是 | `NULL` | （库无注释） | 组织/单位，建议下拉 |
| `review_org_id` | `bigint` | 是 | `NULL` | （库无注释） | 组织/单位，建议下拉 |
| `close_org_id` | `bigint` | 是 | `NULL` | （库无注释） | 组织/单位，建议下拉 |
| `opened_at` | `datetime(6)` | 否 | `NULL` | （库无注释） | 日期时间；按字段语义由人工或系统填写 |
| `closed_at` | `datetime(6)` | 是 | `NULL` | （库无注释） | 日期时间；按字段语义由人工或系统填写 |
| `reopened_at` | `datetime(6)` | 是 | `NULL` | （库无注释） | 日期时间；按字段语义由人工或系统填写 |
| `closure_reason` | `varchar(500)` | 是 | `NULL` | （库无注释） | 按业务台账填写（详见字段名） |
| `merged_into_case_id` | `bigint` | 是 | `NULL` | （库无注释） | 按业务台账填写（详见字段名） |
| `data_nature` | `varchar(20)` | 否 | `NULL` | （库无注释） | 数据性质（demo/正式） |
| `is_demo` | `tinyint(1)` | 否 | `0` | （库无注释） | 数据性质（demo/正式） |
| `verification_status` | `varchar(30)` | 否 | `PENDING_REVIEW` | （库无注释） | 业务状态 |
| `effective_status` | `varchar(30)` | 否 | `DRAFT` | （库无注释） | 业务状态 |
| `effective_at` | `datetime(6)` | 是 | `NULL` | （库无注释） | 日期时间；按字段语义由人工或系统填写 |
| `effective_by` | `bigint` | 是 | `NULL` | （库无注释） | 按业务台账填写（详见字段名） |
| `row_version` | `int` | 否 | `0` | （库无注释） | 系统审计字段，通常不填 |
| `created_by` | `bigint` | 是 | `NULL` | （库无注释） | 系统审计字段，通常不填 |
| `updated_by` | `bigint` | 是 | `NULL` | （库无注释） | 日期时间；按字段语义由人工或系统填写 |
| `created_at` | `timestamp(6)` | 否 | `CURRENT_TIMESTAMP(6)` | （库无注释） | 日期时间；按字段语义由人工或系统填写 |
| `updated_at` | `timestamp(6)` | 否 | `CURRENT_TIMESTAMP(6)` | （库无注释） | 日期时间；按字段语义由人工或系统填写 |
| `project_id` | `bigint` | 是 | `NULL` | Project ownership; legacy rows may remain NULL | Project ownership; legacy rows may remain NULL |

外键：
- `close_org_id` → `org_unit.id`
- `current_status_history_id` → `e_case_status_history.id`
- `discovery_org_id` → `org_unit.id`
- `gis_feature_id` → `gis_feature.id`
- `merged_into_case_id` → `e_closure_case.id`
- `responsible_org_id` → `org_unit.id`
- `review_org_id` → `org_unit.id`
- `source_document_id` → `document_record.id`

### 6.40 `e_rectification_task` — 整改任务

- **分类：** 综合 / 业务事实表 / 必须人工录入
- **当前行数：** 3

| 字段名 | 类型 | 是否为空 | 默认值 | 说明（库注释） | 业务用途（模板建议） |
|---|---|---|---|---|---|
| `id` | `bigint` | 否 | `NULL` | （库无注释） | 系统主键，勿填 |
| `task_code` | `varchar(80)` | 否 | `NULL` | （库无注释） | 业务编号，建议人工或按规则编制 |
| `title` | `varchar(255)` | 否 | `NULL` | （库无注释） | 名称/标题，人工填写 |
| `responsible_org_id` | `bigint` | 是 | `NULL` | （库无注释） | 组织/单位，建议下拉 |
| `deadline` | `datetime(6)` | 是 | `NULL` | （库无注释） | 按业务台账填写（详见字段名） |
| `task_status` | `varchar(30)` | 否 | `PENDING` | （库无注释） | 业务状态 |
| `data_nature` | `varchar(20)` | 否 | `NULL` | （库无注释） | 数据性质（demo/正式） |
| `is_demo` | `tinyint(1)` | 否 | `0` | （库无注释） | 数据性质（demo/正式） |
| `effective_status` | `varchar(30)` | 否 | `DRAFT` | （库无注释） | 业务状态 |
| `effective_at` | `datetime(6)` | 是 | `NULL` | （库无注释） | 日期时间；按字段语义由人工或系统填写 |
| `effective_by` | `bigint` | 是 | `NULL` | （库无注释） | 按业务台账填写（详见字段名） |
| `created_at` | `timestamp(6)` | 否 | `CURRENT_TIMESTAMP(6)` | （库无注释） | 日期时间；按字段语义由人工或系统填写 |
| `updated_at` | `timestamp(6)` | 否 | `CURRENT_TIMESTAMP(6)` | （库无注释） | 日期时间；按字段语义由人工或系统填写 |
| `rectification_completed_date` | `date` | 是 | `NULL` | Client-entered actual rectification completion date; never generated by the system | 甲方填报的整改完成日期（禁止系统自动生成，禁止用 closed_at 顶替） |
| `rectification_completed_by` | `bigint` | 是 | `NULL` | User who entered the rectification completion date | 整改完成填报人（user_account.id） |

外键：
- `rectification_completed_by` → `user_account.id`
- `responsible_org_id` → `org_unit.id`

### 6.41 `e_case_evidence` — 案件证据

- **分类：** 综合 / 关联表 / 文件上传关联
- **当前行数：** 29

| 字段名 | 类型 | 是否为空 | 默认值 | 说明（库注释） | 业务用途（模板建议） |
|---|---|---|---|---|---|
| `id` | `bigint` | 否 | `NULL` | （库无注释） | 系统主键，勿填 |
| `case_id` | `bigint` | 否 | `NULL` | （库无注释） | 按业务台账填写（详见字段名） |
| `status_history_id` | `bigint` | 是 | `NULL` | （库无注释） | 业务状态 |
| `document_id` | `bigint` | 是 | `NULL` | （库无注释） | 文件/资料关联编号 |
| `file_id` | `bigint` | 是 | `NULL` | （库无注释） | 文件/资料关联编号 |
| `evidence_role` | `varchar(40)` | 否 | `NULL` | （库无注释） | 按业务台账填写（详见字段名） |
| `version_no` | `int` | 否 | `1` | （库无注释） | 系统审计字段，通常不填 |
| `is_current` | `tinyint(1)` | 否 | `1` | （库无注释） | 按业务台账填写（详见字段名） |
| `validity_status` | `varchar(20)` | 否 | `VALID` | （库无注释） | 业务状态 |
| `verification_status` | `varchar(30)` | 否 | `PENDING_REVIEW` | （库无注释） | 业务状态 |
| `data_nature` | `varchar(20)` | 否 | `NULL` | （库无注释） | 数据性质（demo/正式） |
| `is_demo` | `tinyint(1)` | 否 | `0` | （库无注释） | 数据性质（demo/正式） |
| `created_by` | `bigint` | 是 | `NULL` | （库无注释） | 系统审计字段，通常不填 |
| `created_at` | `timestamp(6)` | 否 | `CURRENT_TIMESTAMP(6)` | （库无注释） | 日期时间；按字段语义由人工或系统填写 |
| `rectification_round_id` | `int` | 是 | `NULL` | rectification round id | rectification round id |

外键：
- `case_id` → `e_closure_case.id`
- `document_id` → `document_record.id`
- `file_id` → `file_asset.id`
- `status_history_id` → `e_case_status_history.id`

### 6.42 `biz_risk_warning` — Demo ESG 风险预警

- **分类：** 综合 / 业务事实表 / 系统自动生成/计算
- **当前行数：** 6
- **库表注释：** Demo ESG 风险预警

| 字段名 | 类型 | 是否为空 | 默认值 | 说明（库注释） | 业务用途（模板建议） |
|---|---|---|---|---|---|
| `id` | `bigint unsigned` | 否 | `NULL` | （库无注释） | 系统主键，勿填 |
| `warning_code` | `varchar(64)` | 否 | `NULL` | （库无注释） | 业务编号，建议人工或按规则编制 |
| `project_id` | `bigint unsigned` | 否 | `NULL` | （库无注释） | 项目归属，模板建议下拉/固定项目编号映射 |
| `domain_code` | `varchar(8)` | 否 | `NULL` | （库无注释） | 业务编号，建议人工或按规则编制 |
| `kpi_key` | `varchar(16)` | 否 | `NULL` | （库无注释） | 按业务台账填写（详见字段名） |
| `object_type` | `varchar(64)` | 否 | `NULL` | （库无注释） | 按业务台账填写（详见字段名） |
| `object_id` | `bigint unsigned` | 否 | `NULL` | （库无注释） | 按业务台账填写（详见字段名） |
| `object_name_snapshot` | `varchar(255)` | 否 | `NULL` | （库无注释） | 名称/标题，人工填写 |
| `warning_level` | `varchar(16)` | 否 | `NULL` | （库无注释） | 按业务台账填写（详见字段名） |
| `warning_reason` | `varchar(1000)` | 否 | `NULL` | （库无注释） | 按业务台账填写（详见字段名） |
| `trigger_time` | `datetime` | 否 | `NULL` | （库无注释） | 日期时间；按字段语义由人工或系统填写 |
| `responsible_org_id` | `bigint unsigned` | 是 | `NULL` | （库无注释） | 组织/单位，建议下拉 |
| `responsible_unit` | `varchar(255)` | 是 | `NULL` | （库无注释） | 组织/单位，建议下拉 |
| `status` | `varchar(32)` | 否 | `NULL` | （库无注释） | 业务状态 |
| `source_rule_id` | `bigint unsigned` | 是 | `NULL` | （库无注释） | 按业务台账填写（详见字段名） |
| `created_at` | `datetime` | 否 | `CURRENT_TIMESTAMP` | （库无注释） | 日期时间；按字段语义由人工或系统填写 |
| `updated_at` | `datetime` | 否 | `CURRENT_TIMESTAMP` | （库无注释） | 日期时间；按字段语义由人工或系统填写 |

### 6.43 `biz_risk_disposal` — Demo ESG 风险处置

- **分类：** 综合 / 业务事实表 / 必须人工录入
- **当前行数：** 4
- **库表注释：** Demo ESG 风险处置

| 字段名 | 类型 | 是否为空 | 默认值 | 说明（库注释） | 业务用途（模板建议） |
|---|---|---|---|---|---|
| `id` | `bigint unsigned` | 否 | `NULL` | （库无注释） | 系统主键，勿填 |
| `warning_id` | `bigint unsigned` | 否 | `NULL` | （库无注释） | 按业务台账填写（详见字段名） |
| `project_id` | `bigint unsigned` | 否 | `NULL` | （库无注释） | 项目归属，模板建议下拉/固定项目编号映射 |
| `responsible_unit` | `varchar(255)` | 否 | `NULL` | （库无注释） | 组织/单位，建议下拉 |
| `action_content` | `varchar(1000)` | 是 | `NULL` | （库无注释） | 按业务台账填写（详见字段名） |
| `handler` | `varchar(100)` | 是 | `NULL` | （库无注释） | 按业务台账填写（详见字段名） |
| `disposal_status` | `varchar(32)` | 否 | `NULL` | （库无注释） | 业务状态 |
| `disposal_time` | `datetime` | 是 | `NULL` | （库无注释） | 日期时间；按字段语义由人工或系统填写 |
| `close_time` | `datetime` | 是 | `NULL` | （库无注释） | 日期时间；按字段语义由人工或系统填写 |
| `close_evidence` | `varchar(255)` | 是 | `NULL` | （库无注释） | 按业务台账填写（详见字段名） |
| `created_at` | `datetime` | 否 | `CURRENT_TIMESTAMP` | （库无注释） | 日期时间；按字段语义由人工或系统填写 |
| `updated_at` | `datetime` | 否 | `CURRENT_TIMESTAMP` | （库无注释） | 日期时间；按字段语义由人工或系统填写 |

### 6.44 `file_asset` — 文件资产

- **分类：** 综合 / 业务事实表 / 文件上传关联
- **当前行数：** 236
- **库表注释：** 文件资产

| 字段名 | 类型 | 是否为空 | 默认值 | 说明（库注释） | 业务用途（模板建议） |
|---|---|---|---|---|---|
| `id` | `bigint` | 否 | `NULL` | （库无注释） | 系统主键，勿填 |
| `file_code` | `varchar(64)` | 否 | `NULL` | （库无注释） | 文件/资料关联编号 |
| `original_name` | `varchar(255)` | 否 | `NULL` | （库无注释） | 名称/标题，人工填写 |
| `file_ext` | `varchar(20)` | 是 | `NULL` | （库无注释） | 文件/资料关联编号 |
| `mime_type` | `varchar(100)` | 是 | `NULL` | （库无注释） | 按业务台账填写（详见字段名） |
| `file_size` | `bigint` | 是 | `NULL` | （库无注释） | 文件/资料关联编号 |
| `storage_path` | `varchar(500)` | 否 | `NULL` | （库无注释） | 按业务台账填写（详见字段名） |
| `storage_bucket` | `varchar(100)` | 是 | `NULL` | （库无注释） | 按业务台账填写（详见字段名） |
| `sha256_hash` | `varchar(128)` | 否 | `NULL` | （库无注释） | 按业务台账填写（详见字段名） |
| `upload_source` | `varchar(50)` | 否 | `NULL` | （库无注释） | 按业务台账填写（详见字段名） |
| `uploader_id` | `bigint` | 是 | `NULL` | （库无注释） | 按业务台账填写（详见字段名） |
| `uploader_name` | `varchar(100)` | 是 | `NULL` | （库无注释） | 名称/标题，人工填写 |
| `upload_time` | `datetime` | 否 | `NULL` | （库无注释） | 日期时间；按字段语义由人工或系统填写 |
| `duplicate_status` | `varchar(30)` | 否 | `UNKNOWN` | （库无注释） | 业务状态 |
| `duplicate_of_file_id` | `bigint` | 是 | `NULL` | （库无注释） | 文件/资料关联编号 |
| `parse_status` | `varchar(30)` | 否 | `PENDING` | （库无注释） | 业务状态 |
| `is_deleted` | `tinyint` | 否 | `0` | （库无注释） | 逻辑删除标记，模板通常不填 |
| `created_at` | `datetime` | 否 | `CURRENT_TIMESTAMP` | （库无注释） | 日期时间；按字段语义由人工或系统填写 |
| `updated_at` | `datetime` | 否 | `CURRENT_TIMESTAMP` | （库无注释） | 日期时间；按字段语义由人工或系统填写 |

### 6.45 `document_record` — 资料主档

- **分类：** 综合 / 业务事实表 / 文件上传关联
- **当前行数：** 199
- **库表注释：** 资料主档

| 字段名 | 类型 | 是否为空 | 默认值 | 说明（库注释） | 业务用途（模板建议） |
|---|---|---|---|---|---|
| `id` | `bigint` | 否 | `NULL` | （库无注释） | 系统主键，勿填 |
| `document_code` | `varchar(64)` | 否 | `NULL` | （库无注释） | 文件/资料关联编号 |
| `document_name` | `varchar(255)` | 否 | `NULL` | （库无注释） | 文件/资料关联编号 |
| `document_type` | `varchar(100)` | 否 | `NULL` | （库无注释） | 文件/资料关联编号 |
| `module_code` | `varchar(10)` | 否 | `NULL` | （库无注释） | 业务编号，建议人工或按规则编制 |
| `period_value` | `varchar(50)` | 是 | `NULL` | （库无注释） | 按业务台账填写（详见字段名） |
| `version_no` | `varchar(20)` | 否 | `V1` | （库无注释） | 系统审计字段，通常不填 |
| `source_name` | `varchar(100)` | 是 | `NULL` | （库无注释） | 名称/标题，人工填写 |
| `relation_count` | `int` | 否 | `0` | （库无注释） | GIS/坐标 |
| `validity_status` | `varchar(30)` | 否 | `有效` | （库无注释） | 业务状态 |
| `document_status` | `varchar(30)` | 否 | `ACTIVE` | （库无注释） | 业务状态 |
| `confirm_status` | `varchar(30)` | 否 | `CONFIRMED` | （库无注释） | 业务状态 |
| `file_id` | `bigint` | 是 | `NULL` | （库无注释） | 文件/资料关联编号 |
| `parse_job_id` | `bigint` | 是 | `NULL` | （库无注释） | 按业务台账填写（详见字段名） |
| `responsible_unit` | `varchar(100)` | 是 | `NULL` | （库无注释） | 组织/单位，建议下拉 |
| `valid_start_date` | `date` | 是 | `NULL` | （库无注释） | 日期时间；按字段语义由人工或系统填写 |
| `valid_end_date` | `date` | 是 | `NULL` | （库无注释） | 日期时间；按字段语义由人工或系统填写 |
| `uploaded_at` | `datetime` | 是 | `NULL` | （库无注释） | 日期时间；按字段语义由人工或系统填写 |
| `created_by` | `bigint` | 是 | `NULL` | （库无注释） | 系统审计字段，通常不填 |
| `updated_by` | `bigint` | 是 | `NULL` | （库无注释） | 日期时间；按字段语义由人工或系统填写 |
| `created_at` | `datetime` | 否 | `CURRENT_TIMESTAMP` | （库无注释） | 日期时间；按字段语义由人工或系统填写 |
| `updated_at` | `datetime` | 否 | `CURRENT_TIMESTAMP` | （库无注释） | 日期时间；按字段语义由人工或系统填写 |

### 6.46 `gis_feature` — GIS要素

- **分类：** 综合 / 业务事实表 / 必须人工录入
- **当前行数：** 10

| 字段名 | 类型 | 是否为空 | 默认值 | 说明（库注释） | 业务用途（模板建议） |
|---|---|---|---|---|---|
| `id` | `varchar(96)` | 否 | `NULL` | （库无注释） | 系统主键，勿填 |
| `project_id` | `varchar(64)` | 否 | `LUOYI-ESG` | （库无注释） | 项目归属，模板建议下拉/固定项目编号映射 |
| `layer_id` | `varchar(64)` | 否 | `NULL` | （库无注释） | 按业务台账填写（详见字段名） |
| `section_id` | `varchar(64)` | 是 | `NULL` | （库无注释） | 标段，建议下拉 |
| `object_type` | `varchar(64)` | 否 | `NULL` | （库无注释） | 按业务台账填写（详见字段名） |
| `name` | `varchar(160)` | 否 | `NULL` | （库无注释） | 名称/标题，人工填写 |
| `geometry_json` | `json` | 否 | `NULL` | （库无注释） | 按业务台账填写（详见字段名） |
| `properties_json` | `json` | 否 | `NULL` | （库无注释） | 按业务台账填写（详见字段名） |
| `status` | `varchar(32)` | 是 | `NULL` | （库无注释） | 业务状态 |
| `risk_level` | `int` | 是 | `NULL` | （库无注释） | 风险相关属性 |
| `updated_at` | `datetime` | 否 | `CURRENT_TIMESTAMP` | （库无注释） | 日期时间；按字段语义由人工或系统填写 |

外键：
- `layer_id` → `gis_layer.id`

### 6.47 `gis_feature_business_relation` — GIS要素业务关联

- **分类：** 综合 / 关联表 / 必须人工录入
- **当前行数：** 29

| 字段名 | 类型 | 是否为空 | 默认值 | 说明（库注释） | 业务用途（模板建议） |
|---|---|---|---|---|---|
| `id` | `bigint` | 否 | `NULL` | （库无注释） | 系统主键，勿填 |
| `project_id` | `varchar(64)` | 否 | `LUOYI-ESG` | （库无注释） | 项目归属，模板建议下拉/固定项目编号映射 |
| `feature_id` | `varchar(96)` | 否 | `NULL` | （库无注释） | 按业务台账填写（详见字段名） |
| `relation_type` | `varchar(64)` | 否 | `NULL` | （库无注释） | GIS/坐标 |
| `relation_code` | `varchar(64)` | 是 | `NULL` | （库无注释） | GIS/坐标 |
| `relation_name` | `varchar(160)` | 否 | `NULL` | （库无注释） | GIS/坐标 |
| `relation_status` | `varchar(32)` | 是 | `NULL` | （库无注释） | 业务状态 |
| `risk_level` | `int` | 是 | `NULL` | （库无注释） | 风险相关属性 |
| `source_table` | `varchar(80)` | 是 | `NULL` | （库无注释） | 按业务台账填写（详见字段名） |
| `source_id` | `varchar(64)` | 是 | `NULL` | （库无注释） | 按业务台账填写（详见字段名） |
| `summary` | `text` | 是 | `NULL` | （库无注释） | 按业务台账填写（详见字段名） |
| `updated_at` | `datetime` | 否 | `CURRENT_TIMESTAMP` | （库无注释） | 日期时间；按字段语义由人工或系统填写 |

外键：
- `feature_id` → `gis_feature.id`

### 6.48 `org_unit` — 组织机构

- **分类：** 综合 / 配置表 / 必须人工录入
- **当前行数：** 5
- **库表注释：** 组织机构

| 字段名 | 类型 | 是否为空 | 默认值 | 说明（库注释） | 业务用途（模板建议） |
|---|---|---|---|---|---|
| `id` | `bigint` | 否 | `NULL` | （库无注释） | 系统主键，勿填 |
| `org_code` | `varchar(64)` | 否 | `NULL` | （库无注释） | 组织/单位，建议下拉 |
| `org_name` | `varchar(100)` | 否 | `NULL` | （库无注释） | 组织/单位，建议下拉 |
| `parent_id` | `bigint` | 是 | `NULL` | （库无注释） | 按业务台账填写（详见字段名） |
| `org_type` | `varchar(50)` | 是 | `NULL` | （库无注释） | 组织/单位，建议下拉 |
| `enabled` | `tinyint` | 否 | `1` | （库无注释） | 按业务台账填写（详见字段名） |
| `created_at` | `datetime` | 否 | `CURRENT_TIMESTAMP` | （库无注释） | 日期时间；按字段语义由人工或系统填写 |
| `updated_at` | `datetime` | 否 | `CURRENT_TIMESTAMP` | （库无注释） | 日期时间；按字段语义由人工或系统填写 |

### 6.49 `project_section` — 工程标段

- **分类：** 综合 / 配置表 / 必须人工录入
- **当前行数：** 3

| 字段名 | 类型 | 是否为空 | 默认值 | 说明（库注释） | 业务用途（模板建议） |
|---|---|---|---|---|---|
| `id` | `bigint` | 否 | `NULL` | （库无注释） | 系统主键，勿填 |
| `project_id` | `varchar(64)` | 否 | `LUOYI-ESG` | （库无注释） | 项目归属，模板建议下拉/固定项目编号映射 |
| `section_code` | `varchar(40)` | 否 | `NULL` | （库无注释） | 标段，建议下拉 |
| `section_name` | `varchar(160)` | 否 | `NULL` | （库无注释） | 标段，建议下拉 |
| `chainage_start` | `varchar(40)` | 否 | `NULL` | （库无注释） | 按业务台账填写（详见字段名） |
| `chainage_end` | `varchar(40)` | 否 | `NULL` | （库无注释） | 按业务台账填写（详见字段名） |
| `start_km` | `decimal(10,3)` | 否 | `NULL` | （库无注释） | 按业务台账填写（详见字段名） |
| `end_km` | `decimal(10,3)` | 否 | `NULL` | （库无注释） | 按业务台账填写（详见字段名） |
| `section_type` | `varchar(40)` | 否 | `CIVIL` | （库无注释） | 标段，建议下拉 |
| `active_status` | `varchar(20)` | 否 | `ACTIVE` | （库无注释） | 业务状态 |
| `data_nature` | `varchar(20)` | 否 | `NULL` | （库无注释） | 数据性质（demo/正式） |
| `is_demo` | `tinyint(1)` | 否 | `0` | （库无注释） | 数据性质（demo/正式） |
| `created_at` | `timestamp(6)` | 否 | `CURRENT_TIMESTAMP(6)` | （库无注释） | 日期时间；按字段语义由人工或系统填写 |
| `updated_at` | `timestamp(6)` | 否 | `CURRENT_TIMESTAMP(6)` | （库无注释） | 日期时间；按字段语义由人工或系统填写 |

### 6.50 `indicator_definition` — 指标定义

- **分类：** 综合 / 配置表 / 必须人工录入
- **当前行数：** 12
- **库表注释：** 指标定义

| 字段名 | 类型 | 是否为空 | 默认值 | 说明（库注释） | 业务用途（模板建议） |
|---|---|---|---|---|---|
| `indicator_code` | `varchar(20)` | 否 | `NULL` | （库无注释） | 业务编号，建议人工或按规则编制 |
| `group_code` | `varchar(10)` | 否 | `NULL` | （库无注释） | 业务编号，建议人工或按规则编制 |
| `indicator_name` | `varchar(100)` | 否 | `NULL` | （库无注释） | 名称/标题，人工填写 |
| `unit` | `varchar(30)` | 否 | `NULL` | （库无注释） | 组织/单位，建议下拉 |
| `source_table` | `varchar(100)` | 是 | `NULL` | （库无注释） | 按业务台账填写（详见字段名） |
| `calculation_desc` | `varchar(500)` | 是 | `NULL` | （库无注释） | GIS/坐标 |
| `display_order` | `int` | 否 | `NULL` | （库无注释） | 按业务台账填写（详见字段名） |
| `enabled` | `tinyint` | 否 | `1` | （库无注释） | 按业务台账填写（详见字段名） |
| `created_at` | `datetime` | 否 | `CURRENT_TIMESTAMP` | （库无注释） | 日期时间；按字段语义由人工或系统填写 |
| `updated_at` | `datetime` | 否 | `CURRENT_TIMESTAMP` | （库无注释） | 日期时间；按字段语义由人工或系统填写 |

### 6.51 `indicator_result` — 指标当前结果

- **分类：** 综合 / 业务事实表 / 系统自动生成/计算
- **当前行数：** 12
- **库表注释：** 指标当前结果

| 字段名 | 类型 | 是否为空 | 默认值 | 说明（库注释） | 业务用途（模板建议） |
|---|---|---|---|---|---|
| `indicator_code` | `varchar(20)` | 否 | `NULL` | （库无注释） | 业务编号，建议人工或按规则编制 |
| `group_code` | `varchar(10)` | 否 | `NULL` | （库无注释） | 业务编号，建议人工或按规则编制 |
| `label` | `varchar(100)` | 否 | `NULL` | （库无注释） | 按业务台账填写（详见字段名） |
| `full_name` | `varchar(100)` | 否 | `NULL` | （库无注释） | 名称/标题，人工填写 |
| `value` | `decimal(18,4)` | 否 | `NULL` | （库无注释） | 按业务台账填写（详见字段名） |
| `value_text` | `varchar(100)` | 是 | `NULL` | （库无注释） | 按业务台账填写（详见字段名） |
| `unit` | `varchar(30)` | 否 | `NULL` | （库无注释） | 组织/单位，建议下拉 |
| `display_order` | `int` | 否 | `NULL` | （库无注释） | 按业务台账填写（详见字段名） |
| `calculated_at` | `datetime` | 否 | `NULL` | （库无注释） | 日期时间；按字段语义由人工或系统填写 |
| `published_at` | `datetime` | 否 | `NULL` | （库无注释） | 日期时间；按字段语义由人工或系统填写 |

## 7. 全库字段附录（全部基表）

供核对完整结构。模板设计优先使用第 6 章核心表。

### `ai_document_analysis` — AI文档分析

| 字段名 | 类型 | 是否为空 | 默认值 | 说明 |
|---|---|---|---|---|
| `id` | `bigint` | 否 | `NULL` | （库无注释） |
| `source_file_id` | `bigint` | 否 | `NULL` | （库无注释） |
| `file_name` | `varchar(500)` | 否 | `NULL` | （库无注释） |
| `file_type` | `varchar(80)` | 否 | `NULL` | （库无注释） |
| `project_name` | `varchar(200)` | 否 | `NULL` | （库无注释） |
| `report_period` | `varchar(20)` | 否 | `NULL` | （库无注释） |
| `analysis_status` | `varchar(20)` | 否 | `uploaded` | （库无注释） |
| `summary_text` | `text` | 是 | `NULL` | （库无注释） |
| `confidence_score` | `decimal(5,4)` | 是 | `NULL` | （库无注释） |
| `ingestion_status` | `varchar(20)` | 否 | `pending` | （库无注释） |
| `excluded_from_dashboard` | `tinyint(1)` | 否 | `1` | （库无注释） |
| `created_at` | `datetime(6)` | 否 | `CURRENT_TIMESTAMP(6)` | （库无注释） |
| `updated_at` | `datetime(6)` | 否 | `CURRENT_TIMESTAMP(6)` | （库无注释） |

### `ai_extracted_environment` — AI抽取-环境

| 字段名 | 类型 | 是否为空 | 默认值 | 说明 |
|---|---|---|---|---|
| `id` | `bigint` | 否 | `NULL` | （库无注释） |
| `analysis_id` | `bigint` | 否 | `NULL` | （库无注释） |
| `environment_issue_count` | `int` | 否 | `0` | （库无注释） |
| `water_issue_count` | `int` | 否 | `0` | （库无注释） |
| `rectification_status` | `varchar(80)` | 是 | `NULL` | （库无注释） |
| `monitoring_abnormal_count` | `int` | 否 | `0` | （库无注释） |
| `period` | `varchar(20)` | 否 | `NULL` | （库无注释） |

### `ai_extracted_progress` — AI抽取-进度

| 字段名 | 类型 | 是否为空 | 默认值 | 说明 |
|---|---|---|---|---|
| `id` | `bigint` | 否 | `NULL` | （库无注释） |
| `analysis_id` | `bigint` | 否 | `NULL` | （库无注释） |
| `section_code` | `varchar(50)` | 否 | `NULL` | （库无注释） |
| `work_type` | `varchar(100)` | 否 | `NULL` | （库无注释） |
| `work_content` | `varchar(500)` | 否 | `NULL` | （库无注释） |
| `supervision_focus` | `varchar(500)` | 是 | `NULL` | （库无注释） |
| `period` | `varchar(20)` | 否 | `NULL` | （库无注释） |

### `ai_extracted_project_info` — AI抽取-项目信息

| 字段名 | 类型 | 是否为空 | 默认值 | 说明 |
|---|---|---|---|---|
| `id` | `bigint` | 否 | `NULL` | （库无注释） |
| `analysis_id` | `bigint` | 否 | `NULL` | （库无注释） |
| `project_name` | `varchar(200)` | 否 | `NULL` | （库无注释） |
| `construction_stage` | `varchar(100)` | 是 | `NULL` | （库无注释） |
| `route_length` | `decimal(10,2)` | 是 | `NULL` | （库无注释） |
| `section_count` | `int` | 是 | `NULL` | （库无注释） |
| `professional_type_count` | `int` | 是 | `NULL` | （库无注释） |
| `period` | `varchar(20)` | 否 | `NULL` | （库无注释） |

### `ai_extracted_resource` — AI抽取-资源

| 字段名 | 类型 | 是否为空 | 默认值 | 说明 |
|---|---|---|---|---|
| `id` | `bigint` | 否 | `NULL` | （库无注释） |
| `analysis_id` | `bigint` | 否 | `NULL` | （库无注释） |
| `person_count` | `int` | 否 | `0` | （库无注释） |
| `equipment_count` | `int` | 否 | `0` | （库无注释） |
| `equipment_type` | `varchar(500)` | 是 | `NULL` | （库无注释） |
| `period` | `varchar(20)` | 否 | `NULL` | （库无注释） |

### `ai_extracted_safety` — AI抽取-安全

| 字段名 | 类型 | 是否为空 | 默认值 | 说明 |
|---|---|---|---|---|
| `id` | `bigint` | 否 | `NULL` | （库无注释） |
| `analysis_id` | `bigint` | 否 | `NULL` | （库无注释） |
| `safe_days` | `int` | 否 | `0` | （库无注释） |
| `risk_point_count` | `int` | 否 | `0` | （库无注释） |
| `unfinished_issue_count` | `int` | 否 | `0` | （库无注释） |
| `inspection_count` | `int` | 否 | `0` | （库无注释） |
| `period` | `varchar(20)` | 否 | `NULL` | （库无注释） |

### `ai_field_mapping_rule` — AI字段入库映射规则

| 字段名 | 类型 | 是否为空 | 默认值 | 说明 |
|---|---|---|---|---|
| `id` | `bigint` | 否 | `NULL` | （库无注释） |
| `document_type` | `varchar(100)` | 否 | `NULL` | （库无注释） |
| `field_key` | `varchar(100)` | 否 | `NULL` | （库无注释） |
| `field_name` | `varchar(100)` | 否 | `NULL` | （库无注释） |
| `target_table` | `varchar(100)` | 否 | `NULL` | （库无注释） |
| `target_column` | `varchar(100)` | 否 | `NULL` | （库无注释） |
| `value_type` | `varchar(30)` | 是 | `NULL` | （库无注释） |
| `required` | `tinyint` | 否 | `0` | （库无注释） |
| `normalize_rule` | `varchar(255)` | 是 | `NULL` | （库无注释） |
| `enabled` | `tinyint` | 否 | `1` | （库无注释） |
| `created_at` | `datetime` | 否 | `CURRENT_TIMESTAMP` | （库无注释） |
| `updated_at` | `datetime` | 否 | `CURRENT_TIMESTAMP` | （库无注释） |

### `ai_parse_field_result` — AI字段抽取结果

| 字段名 | 类型 | 是否为空 | 默认值 | 说明 |
|---|---|---|---|---|
| `id` | `bigint` | 否 | `NULL` | （库无注释） |
| `parse_job_id` | `bigint` | 否 | `NULL` | （库无注释） |
| `field_key` | `varchar(100)` | 否 | `NULL` | （库无注释） |
| `field_name` | `varchar(100)` | 否 | `NULL` | （库无注释） |
| `field_value` | `text` | 是 | `NULL` | （库无注释） |
| `normalized_value` | `text` | 是 | `NULL` | （库无注释） |
| `value_type` | `varchar(30)` | 是 | `NULL` | （库无注释） |
| `confidence` | `decimal(5,2)` | 是 | `NULL` | （库无注释） |
| `source_page` | `int` | 是 | `NULL` | （库无注释） |
| `source_location` | `varchar(255)` | 是 | `NULL` | （库无注释） |
| `confirm_status` | `varchar(30)` | 否 | `PENDING` | （库无注释） |
| `confirmed_value` | `text` | 是 | `NULL` | （库无注释） |
| `confirmed_by` | `bigint` | 是 | `NULL` | （库无注释） |
| `confirmed_at` | `datetime` | 是 | `NULL` | （库无注释） |
| `created_at` | `datetime` | 否 | `CURRENT_TIMESTAMP` | （库无注释） |

### `ai_parse_job` — AI解析任务

| 字段名 | 类型 | 是否为空 | 默认值 | 说明 |
|---|---|---|---|---|
| `id` | `bigint` | 否 | `NULL` | （库无注释） |
| `job_code` | `varchar(64)` | 否 | `NULL` | （库无注释） |
| `file_id` | `bigint` | 否 | `NULL` | （库无注释） |
| `job_status` | `varchar(30)` | 否 | `NULL` | （库无注释） |
| `parse_engine` | `varchar(100)` | 是 | `NULL` | （库无注释） |
| `model_name` | `varchar(100)` | 是 | `NULL` | （库无注释） |
| `rule_version` | `varchar(50)` | 是 | `NULL` | （库无注释） |
| `started_at` | `datetime` | 是 | `NULL` | （库无注释） |
| `finished_at` | `datetime` | 是 | `NULL` | （库无注释） |
| `duration_ms` | `int` | 是 | `NULL` | （库无注释） |
| `confidence` | `decimal(5,2)` | 是 | `NULL` | （库无注释） |
| `error_code` | `varchar(50)` | 是 | `NULL` | （库无注释） |
| `error_message` | `text` | 是 | `NULL` | （库无注释） |
| `retry_count` | `int` | 否 | `0` | （库无注释） |
| `raw_result_json` | `json` | 是 | `NULL` | （库无注释） |
| `created_at` | `datetime` | 否 | `CURRENT_TIMESTAMP` | （库无注释） |
| `updated_at` | `datetime` | 否 | `CURRENT_TIMESTAMP` | （库无注释） |

### `audit_log` — 操作审计日志

| 字段名 | 类型 | 是否为空 | 默认值 | 说明 |
|---|---|---|---|---|
| `id` | `bigint` | 否 | `NULL` | （库无注释） |
| `module_name` | `varchar(100)` | 否 | `NULL` | （库无注释） |
| `entity_type` | `varchar(100)` | 否 | `NULL` | （库无注释） |
| `entity_id` | `varchar(100)` | 否 | `NULL` | （库无注释） |
| `action` | `varchar(100)` | 否 | `NULL` | （库无注释） |
| `action_desc` | `varchar(500)` | 是 | `NULL` | （库无注释） |
| `operator_id` | `bigint` | 是 | `NULL` | （库无注释） |
| `operator_name` | `varchar(100)` | 是 | `NULL` | （库无注释） |
| `ip_address` | `varchar(50)` | 是 | `NULL` | （库无注释） |
| `user_agent` | `varchar(500)` | 是 | `NULL` | （库无注释） |
| `created_at` | `datetime` | 否 | `CURRENT_TIMESTAMP` | （库无注释） |

### `carbon_accounting_batch` — 碳排放核算批次（§5.3）

| 字段名 | 类型 | 是否为空 | 默认值 | 说明 |
|---|---|---|---|---|
| `id` | `bigint` | 否 | `NULL` | （库无注释） |
| `batch_code` | `varchar(80)` | 否 | `NULL` | 批次代码 |
| `batch_label` | `varchar(200)` | 否 | `NULL` | 批次名称 |
| `boundary_version` | `varchar(80)` | 否 | `NULL` | 采用的边界版本（须 ACTIVE） |
| `statistics_as_of` | `date` | 否 | `NULL` | 统计截止日期 |
| `period_start` | `varchar(7)` | 是 | `NULL` | 核算起始月份 YYYY-MM |
| `period_end` | `varchar(7)` | 是 | `NULL` | 核算结束月份 YYYY-MM |
| `data_nature` | `varchar(30)` | 否 | `demo` | formal | demo |
| `is_current` | `tinyint(1)` | 否 | `0` | 当前生效批次指针 |
| `is_demo` | `tinyint(1)` | 否 | `0` | （库无注释） |
| `verification_status` | `varchar(40)` | 否 | `PENDING` | PENDING | VERIFIED |
| `boundary_snapshot_note` | `text` | 是 | `NULL` | 批次创建时边界快照说明 |
| `created_at` | `datetime` | 否 | `CURRENT_TIMESTAMP` | （库无注释） |
| `updated_at` | `datetime` | 否 | `CURRENT_TIMESTAMP` | （库无注释） |

### `carbon_accounting_boundary` — 碳排放核算边界配置（按来源维度，§5.2）

| 字段名 | 类型 | 是否为空 | 默认值 | 说明 |
|---|---|---|---|---|
| `id` | `bigint` | 否 | `NULL` | （库无注释） |
| `boundary_version` | `varchar(80)` | 否 | `NULL` | 边界版本标识，如 DEMO-BOUND-E04-20260718 |
| `boundary_label` | `varchar(200)` | 否 | `NULL` | 边界版本名称 |
| `boundary_status` | `varchar(30)` | 否 | `DRAFT` | DRAFT | CANDIDATE | ACTIVE | RETIRED |
| `source_code` | `varchar(30)` | 否 | `NULL` | 来源代码：diesel/electricity/material/transport/equipment |
| `source_label` | `varchar(100)` | 是 | `NULL` | 来源名称 |
| `in_boundary` | `tinyint(1)` | 否 | `1` | 是否计入当前边界 |
| `sort_order` | `int` | 否 | `0` | 展示排序 |
| `description` | `text` | 是 | `NULL` | 生效说明 |
| `is_demo` | `tinyint(1)` | 否 | `0` | 演示数据标识 |
| `data_nature` | `varchar(30)` | 否 | `formal` | formal | demo | platform_calc |
| `created_at` | `datetime` | 否 | `CURRENT_TIMESTAMP` | （库无注释） |
| `updated_at` | `datetime` | 否 | `CURRENT_TIMESTAMP` | （库无注释） |

### `carbon_accounting_evidence_link` — 碳核算与既有资料关联

| 字段名 | 类型 | 是否为空 | 默认值 | 说明 |
|---|---|---|---|---|
| `id` | `bigint` | 否 | `NULL` | （库无注释） |
| `business_type` | `varchar(60)` | 否 | `NULL` | （库无注释） |
| `business_id` | `bigint` | 否 | `NULL` | （库无注释） |
| `document_id` | `bigint` | 否 | `NULL` | （库无注释） |
| `evidence_role` | `varchar(60)` | 否 | `NULL` | （库无注释） |
| `verification_status` | `varchar(40)` | 否 | `NULL` | （库无注释） |
| `created_at` | `datetime` | 否 | `CURRENT_TIMESTAMP` | （库无注释） |

### `carbon_emission_baseline` — 碳排放基准方案

| 字段名 | 类型 | 是否为空 | 默认值 | 说明 |
|---|---|---|---|---|
| `id` | `bigint` | 否 | `NULL` | （库无注释） |
| `baseline_code` | `varchar(80)` | 否 | `NULL` | （库无注释） |
| `baseline_name` | `varchar(160)` | 否 | `NULL` | （库无注释） |
| `accounting_period` | `char(7)` | 否 | `NULL` | （库无注释） |
| `boundary_code` | `varchar(80)` | 否 | `NULL` | （库无注释） |
| `baseline_emission` | `decimal(18,4)` | 否 | `NULL` | （库无注释） |
| `unit` | `varchar(30)` | 否 | `NULL` | （库无注释） |
| `calculation_method` | `varchar(255)` | 否 | `NULL` | （库无注释） |
| `factor_version` | `varchar(80)` | 否 | `NULL` | （库无注释） |
| `data_nature` | `varchar(30)` | 否 | `NULL` | （库无注释） |
| `verification_status` | `varchar(40)` | 否 | `NULL` | （库无注释） |
| `evidence_status` | `varchar(40)` | 否 | `NULL` | （库无注释） |
| `is_demo` | `tinyint(1)` | 否 | `0` | （库无注释） |
| `created_at` | `datetime` | 否 | `CURRENT_TIMESTAMP` | （库无注释） |
| `updated_at` | `datetime` | 否 | `CURRENT_TIMESTAMP` | （库无注释） |

### `carbon_emission_factor` — 碳排放因子元数据（含演示测试因子）

| 字段名 | 类型 | 是否为空 | 默认值 | 说明 |
|---|---|---|---|---|
| `id` | `bigint` | 否 | `NULL` | （库无注释） |
| `factor_code` | `varchar(60)` | 否 | `NULL` | （库无注释） |
| `factor_name` | `varchar(160)` | 否 | `NULL` | （库无注释） |
| `factor_value` | `decimal(24,12)` | 否 | `NULL` | （库无注释） |
| `factor_unit` | `varchar(80)` | 否 | `NULL` | （库无注释） |
| `factor_version` | `varchar(80)` | 否 | `NULL` | （库无注释） |
| `factor_source` | `varchar(255)` | 否 | `NULL` | （库无注释） |
| `data_nature` | `varchar(30)` | 否 | `NULL` | （库无注释） |
| `verification_status` | `varchar(40)` | 否 | `NULL` | （库无注释） |
| `evidence_document_id` | `bigint` | 是 | `NULL` | （库无注释） |
| `created_at` | `datetime` | 否 | `CURRENT_TIMESTAMP` | （库无注释） |
| `updated_at` | `datetime` | 否 | `CURRENT_TIMESTAMP` | （库无注释） |

### `carbon_emission_factor_snapshot` — 碳排放因子不可变快照（行级，§5.4）

| 字段名 | 类型 | 是否为空 | 默认值 | 说明 |
|---|---|---|---|---|
| `id` | `bigint` | 否 | `NULL` | （库无注释） |
| `snapshot_code` | `varchar(80)` | 否 | `NULL` | 快照代码 |
| `factor_id` | `bigint` | 否 | `NULL` | 关联 carbon_emission_factor.id |
| `factor_code` | `varchar(60)` | 否 | `NULL` | 因子代码 |
| `factor_name` | `varchar(160)` | 否 | `NULL` | 因子名称 |
| `factor_value` | `decimal(24,12)` | 否 | `NULL` | 因子数值 |
| `factor_unit` | `varchar(80)` | 否 | `NULL` | 因子单位 |
| `numerator_unit` | `varchar(30)` | 是 | `NULL` | 分子单位 |
| `denominator_unit` | `varchar(30)` | 是 | `NULL` | 分母单位 |
| `activity_unit` | `varchar(30)` | 是 | `NULL` | 活动单位 |
| `conversion_factor` | `decimal(24,12)` | 是 | `NULL` | 单位换算系数 |
| `conversion_path` | `varchar(255)` | 是 | `NULL` | 换算路径 |
| `factor_version` | `varchar(80)` | 否 | `NULL` | 因子版本 |
| `factor_source` | `varchar(255)` | 否 | `NULL` | 因子来源文件/机构 |
| `gwp_version` | `varchar(80)` | 是 | `NULL` | GWP 或折算依据版本 |
| `precision_rule` | `varchar(100)` | 是 | `NULL` | 计算精度与舍入规则引用 |
| `effective_from` | `date` | 是 | `NULL` | 因子生效起始 |
| `effective_until` | `date` | 是 | `NULL` | 因子生效截止 |
| `snapshot_at` | `datetime` | 否 | `CURRENT_TIMESTAMP` | 快照时间 |
| `data_nature` | `varchar(30)` | 否 | `NULL` | formal | demo |
| `created_at` | `datetime` | 否 | `CURRENT_TIMESTAMP` | （库无注释） |

### `carbon_emission_segment_detail` — 碳排放月度-标段-来源-材料演示明细

| 字段名 | 类型 | 是否为空 | 默认值 | 说明 |
|---|---|---|---|---|
| `id` | `bigint` | 否 | `NULL` | （库无注释） |
| `detail_code` | `varchar(120)` | 否 | `NULL` | （库无注释） |
| `accounting_month` | `char(7)` | 否 | `NULL` | （库无注释） |
| `segment_code` | `varchar(30)` | 否 | `NULL` | （库无注释） |
| `segment_name` | `varchar(100)` | 否 | `NULL` | （库无注释） |
| `segment_sort_order` | `int` | 否 | `NULL` | （库无注释） |
| `emission_source_code` | `varchar(30)` | 否 | `NULL` | （库无注释） |
| `emission_source_name` | `varchar(100)` | 否 | `NULL` | （库无注释） |
| `source_sort_order` | `int` | 否 | `NULL` | （库无注释） |
| `material_type_code` | `varchar(30)` | 否 | `` | （库无注释） |
| `material_type_name` | `varchar(100)` | 是 | `NULL` | （库无注释） |
| `material_sort_order` | `int` | 是 | `NULL` | （库无注释） |
| `activity_amount` | `decimal(24,8)` | 否 | `NULL` | （库无注释） |
| `activity_unit` | `varchar(30)` | 否 | `NULL` | （库无注释） |
| `emission_factor_id` | `bigint` | 是 | `NULL` | （库无注释） |
| `emission_factor_value` | `decimal(24,12)` | 否 | `NULL` | （库无注释） |
| `factor_unit` | `varchar(80)` | 否 | `NULL` | （库无注释） |
| `emission_amount` | `decimal(18,8)` | 否 | `NULL` | （库无注释） |
| `emission_unit` | `varchar(30)` | 否 | `tCO₂e` | （库无注释） |
| `boundary_code` | `varchar(80)` | 否 | `NULL` | （库无注释） |
| `data_nature` | `varchar(30)` | 否 | `NULL` | （库无注释） |
| `verification_status` | `varchar(40)` | 否 | `NULL` | （库无注释） |
| `evidence_status` | `varchar(40)` | 否 | `NULL` | （库无注释） |
| `is_demo` | `tinyint(1)` | 否 | `0` | （库无注释） |
| `created_at` | `datetime` | 否 | `CURRENT_TIMESTAMP` | （库无注释） |
| `updated_at` | `datetime` | 否 | `CURRENT_TIMESTAMP` | （库无注释） |

### `carbon_measure_monthly_performance` — 低碳措施月度成效

| 字段名 | 类型 | 是否为空 | 默认值 | 说明 |
|---|---|---|---|---|
| `id` | `bigint` | 否 | `NULL` | （库无注释） |
| `performance_code` | `varchar(80)` | 否 | `NULL` | （库无注释） |
| `measure_id` | `bigint` | 否 | `NULL` | （库无注释） |
| `accounting_month` | `char(7)` | 否 | `NULL` | （库无注释） |
| `estimated_reduction` | `decimal(18,4)` | 是 | `NULL` | （库无注释） |
| `verified_reduction` | `decimal(18,4)` | 是 | `NULL` | （库无注释） |
| `investment_cost` | `decimal(18,4)` | 否 | `0.0000` | （库无注释） |
| `operating_saving` | `decimal(18,4)` | 否 | `0.0000` | （库无注释） |
| `avoided_cost` | `decimal(18,4)` | 否 | `0.0000` | （库无注释） |
| `verification_status` | `varchar(40)` | 否 | `NULL` | （库无注释） |
| `evidence_status` | `varchar(40)` | 否 | `NULL` | （库无注释） |
| `is_demo` | `tinyint(1)` | 否 | `0` | （库无注释） |
| `created_at` | `datetime` | 否 | `CURRENT_TIMESTAMP` | （库无注释） |
| `updated_at` | `datetime` | 否 | `CURRENT_TIMESTAMP` | （库无注释） |

### `carbon_reduction_accounting` — 月度低碳增益核算

| 字段名 | 类型 | 是否为空 | 默认值 | 说明 |
|---|---|---|---|---|
| `id` | `bigint` | 否 | `NULL` | （库无注释） |
| `accounting_code` | `varchar(80)` | 否 | `NULL` | （库无注释） |
| `accounting_month` | `char(7)` | 否 | `NULL` | （库无注释） |
| `baseline_id` | `bigint` | 否 | `NULL` | （库无注释） |
| `boundary_code` | `varchar(80)` | 否 | `NULL` | （库无注释） |
| `baseline_emission` | `decimal(18,4)` | 否 | `NULL` | （库无注释） |
| `actual_emission` | `decimal(18,4)` | 否 | `NULL` | （库无注释） |
| `accounted_reduction` | `decimal(18,4)` | 否 | `NULL` | （库无注释） |
| `unit` | `varchar(30)` | 否 | `NULL` | （库无注释） |
| `calculation_formula` | `varchar(255)` | 否 | `NULL` | （库无注释） |
| `data_nature` | `varchar(30)` | 否 | `NULL` | （库无注释） |
| `verification_status` | `varchar(40)` | 否 | `NULL` | （库无注释） |
| `evidence_status` | `varchar(40)` | 否 | `NULL` | （库无注释） |
| `is_demo` | `tinyint(1)` | 否 | `0` | （库无注释） |
| `created_at` | `datetime` | 否 | `CURRENT_TIMESTAMP` | （库无注释） |
| `updated_at` | `datetime` | 否 | `CURRENT_TIMESTAMP` | （库无注释） |

### `cfg_warning_rule` — Demo 风险规则

| 字段名 | 类型 | 是否为空 | 默认值 | 说明 |
|---|---|---|---|---|
| `id` | `bigint unsigned` | 否 | `NULL` | （库无注释） |
| `rule_code` | `varchar(64)` | 否 | `NULL` | （库无注释） |
| `kpi_key` | `varchar(16)` | 否 | `NULL` | （库无注释） |
| `domain_code` | `varchar(8)` | 否 | `NULL` | （库无注释） |
| `rule_name` | `varchar(255)` | 否 | `NULL` | （库无注释） |
| `trigger_condition_json` | `json` | 否 | `NULL` | （库无注释） |
| `warning_level` | `varchar(16)` | 否 | `NULL` | （库无注释） |
| `version_no` | `varchar(32)` | 否 | `NULL` | （库无注释） |
| `enabled` | `tinyint unsigned` | 否 | `1` | （库无注释） |
| `created_at` | `datetime` | 否 | `CURRENT_TIMESTAMP` | （库无注释） |

### `compliance_material_gap` — 待补齐合规资料

| 字段名 | 类型 | 是否为空 | 默认值 | 说明 |
|---|---|---|---|---|
| `id` | `bigint` | 否 | `NULL` | （库无注释） |
| `task_id` | `varchar(64)` | 是 | `NULL` | （库无注释） |
| `material_name` | `varchar(255)` | 是 | `NULL` | （库无注释） |
| `status` | `varchar(50)` | 是 | `NULL` | （库无注释） |
| `responsible_unit` | `varchar(100)` | 是 | `NULL` | （库无注释） |
| `created_at` | `datetime` | 否 | `CURRENT_TIMESTAMP` | （库无注释） |
| `module_code` | `varchar(10)` | 是 | `NULL` | 所属 ESG 模块 |
| `deadline` | `date` | 是 | `NULL` | 提交时限 |
| `action_text` | `varchar(30)` | 是 | `NULL` | 页面操作文案 |

### `construction_stage_record` — 项目工期主阶段

| 字段名 | 类型 | 是否为空 | 默认值 | 说明 |
|---|---|---|---|---|
| `id` | `bigint` | 否 | `NULL` | （库无注释） |
| `project_id` | `varchar(50)` | 否 | `LUOYI-ESG` | 项目标识 |
| `stage_key` | `varchar(50)` | 否 | `NULL` | （库无注释） |
| `stage_name` | `varchar(100)` | 否 | `NULL` | （库无注释） |
| `stage_status` | `varchar(30)` | 否 | `NULL` | （库无注释） |
| `stage_detail` | `varchar(255)` | 是 | `NULL` | （库无注释） |
| `sequence_no` | `int` | 否 | `NULL` | （库无注释） |
| `start_date` | `date` | 是 | `NULL` | （库无注释） |
| `end_date` | `date` | 是 | `NULL` | （库无注释） |
| `detail` | `varchar(500)` | 是 | `NULL` | 阶段详情 |
| `effective_status` | `varchar(30)` | 否 | `DRAFT` | DRAFT / EFFECTIVE / INEFFECTIVE |
| `is_current` | `tinyint(1)` | 否 | `1` | 当前有效 |
| `data_nature` | `varchar(20)` | 否 | `demo` | demo / formal |
| `is_demo` | `tinyint(1)` | 否 | `1` | 是否演示数据（旧行默认 demo） |
| `created_at` | `datetime` | 否 | `CURRENT_TIMESTAMP` | （库无注释） |
| `updated_at` | `timestamp(6)` | 否 | `CURRENT_TIMESTAMP(6)` | 更新时间 |

### `dashboard_kpi_detail_snapshot` — 领导层 KPI 详情弹窗快照

| 字段名 | 类型 | 是否为空 | 默认值 | 说明 |
|---|---|---|---|---|
| `indicator_code` | `varchar(20)` | 否 | `NULL` | KPI 编码，如 E01/S02/G03 |
| `detail_json` | `json` | 否 | `NULL` | 弹窗详情完整配置，兼容 KpiDetailConfig |
| `data_version` | `varchar(30)` | 否 | `V0.2` | （库无注释） |
| `data_source` | `varchar(100)` | 否 | `dashboard_payload_migration` | （库无注释） |
| `published_at` | `datetime` | 否 | `CURRENT_TIMESTAMP` | （库无注释） |
| `updated_at` | `datetime` | 否 | `CURRENT_TIMESTAMP` | （库无注释） |

### `dashboard_panel_snapshot` — 领导层首页面板快照

| 字段名 | 类型 | 是否为空 | 默认值 | 说明 |
|---|---|---|---|---|
| `panel_key` | `varchar(50)` | 否 | `NULL` | 面板编码：home-panels |
| `panel_json` | `json` | 否 | `NULL` | 首页右侧专题、GIS、时间线等组合数据 |
| `data_version` | `varchar(30)` | 否 | `V0.2` | （库无注释） |
| `data_source` | `varchar(100)` | 否 | `dashboard_payload_migration` | （库无注释） |
| `published_at` | `datetime` | 否 | `CURRENT_TIMESTAMP` | （库无注释） |
| `updated_at` | `datetime` | 否 | `CURRENT_TIMESTAMP` | （库无注释） |

### `dashboard_topic_snapshot` — 领导层专题弹窗快照

| 字段名 | 类型 | 是否为空 | 默认值 | 说明 |
|---|---|---|---|---|
| `topic_key` | `varchar(50)` | 否 | `NULL` | 专题编码：carbon/monthly-report |
| `detail_json` | `json` | 否 | `NULL` | 专题弹窗详情完整配置，含 topicData |
| `data_version` | `varchar(30)` | 否 | `V0.2` | （库无注释） |
| `data_source` | `varchar(100)` | 否 | `dashboard_payload_migration` | （库无注释） |
| `published_at` | `datetime` | 否 | `CURRENT_TIMESTAMP` | （库无注释） |
| `updated_at` | `datetime` | 否 | `CURRENT_TIMESTAMP` | （库无注释） |

### `data_ingestion_job` — 数据接入任务表

| 字段名 | 类型 | 是否为空 | 默认值 | 说明 |
|---|---|---|---|---|
| `id` | `bigint` | 否 | `NULL` | （库无注释） |
| `source_id` | `bigint` | 否 | `NULL` | （库无注释） |
| `job_type` | `varchar(30)` | 否 | `NULL` | FILE_PARSE/API_SYNC/MANUAL_IMPORT/BATCH_IMPORT/SCHEDULE_SYNC |
| `job_status` | `varchar(30)` | 否 | `NULL` | PENDING/RUNNING/SUCCESS/FAILED/PARTIAL_SUCCESS |
| `business_domain` | `varchar(50)` | 是 | `NULL` | ENV/SAFETY/SOCIAL/GOVERNANCE/CARBON/MONTHLY/GIS |
| `target_table` | `varchar(100)` | 是 | `NULL` | 目标业务表 |
| `started_at` | `datetime` | 是 | `NULL` | （库无注释） |
| `finished_at` | `datetime` | 是 | `NULL` | （库无注释） |
| `total_count` | `int` | 是 | `0` | （库无注释） |
| `success_count` | `int` | 是 | `0` | （库无注释） |
| `failed_count` | `int` | 是 | `0` | （库无注释） |
| `operator_id` | `bigint` | 是 | `NULL` | （库无注释） |
| `operator_name` | `varchar(100)` | 是 | `NULL` | （库无注释） |
| `error_message` | `text` | 是 | `NULL` | （库无注释） |
| `created_at` | `datetime` | 否 | `CURRENT_TIMESTAMP` | （库无注释） |

### `data_mapping_rule` — 多源字段映射规则表

| 字段名 | 类型 | 是否为空 | 默认值 | 说明 |
|---|---|---|---|---|
| `id` | `bigint` | 否 | `NULL` | （库无注释） |
| `source_id` | `bigint` | 否 | `NULL` | （库无注释） |
| `source_object` | `varchar(100)` | 是 | `NULL` | 来源对象，如接口资源、资料类型、sheet名称 |
| `source_field` | `varchar(100)` | 否 | `NULL` | 来源字段 |
| `target_table` | `varchar(100)` | 否 | `NULL` | 目标业务表 |
| `target_field` | `varchar(100)` | 否 | `NULL` | 目标字段 |
| `target_data_type` | `varchar(30)` | 是 | `NULL` | 目标数据类型 |
| `transform_rule` | `varchar(500)` | 是 | `NULL` | 转换规则 |
| `required` | `tinyint` | 否 | `0` | （库无注释） |
| `enabled` | `tinyint` | 否 | `1` | （库无注释） |
| `created_at` | `datetime` | 否 | `CURRENT_TIMESTAMP` | （库无注释） |
| `updated_at` | `datetime` | 否 | `CURRENT_TIMESTAMP` | （库无注释） |

### `data_quality_check_result` — 数据质量校验结果表

| 字段名 | 类型 | 是否为空 | 默认值 | 说明 |
|---|---|---|---|---|
| `id` | `bigint` | 否 | `NULL` | （库无注释） |
| `ingestion_job_id` | `bigint` | 否 | `NULL` | （库无注释） |
| `source_record_key` | `varchar(100)` | 是 | `NULL` | 来源记录主键或文件行号 |
| `target_table` | `varchar(100)` | 是 | `NULL` | （库无注释） |
| `target_record_id` | `varchar(100)` | 是 | `NULL` | （库无注释） |
| `check_type` | `varchar(50)` | 否 | `NULL` | REQUIRED/FORMAT/RANGE/CONSISTENCY/DUPLICATE/BUSINESS_RULE |
| `check_status` | `varchar(30)` | 否 | `NULL` | PASS/WARN/FAIL |
| `check_message` | `varchar(1000)` | 是 | `NULL` | （库无注释） |
| `created_at` | `datetime` | 否 | `CURRENT_TIMESTAMP` | （库无注释） |

### `data_source_registry` — 数据来源登记表

| 字段名 | 类型 | 是否为空 | 默认值 | 说明 |
|---|---|---|---|---|
| `id` | `bigint` | 否 | `NULL` | （库无注释） |
| `source_code` | `varchar(50)` | 否 | `NULL` | 来源编码 |
| `source_name` | `varchar(100)` | 否 | `NULL` | 来源名称 |
| `source_type` | `varchar(30)` | 否 | `NULL` | UPLOAD/API/MANUAL/BATCH/GIS/SCHEDULE |
| `owner_department` | `varchar(100)` | 是 | `NULL` | 来源责任部门 |
| `provider_name` | `varchar(100)` | 是 | `NULL` | 系统或供应商名称 |
| `endpoint_url` | `varchar(500)` | 是 | `NULL` | 接口地址，仅接口类来源使用 |
| `enabled` | `tinyint` | 否 | `1` | （库无注释） |
| `remark` | `varchar(500)` | 是 | `NULL` | （库无注释） |
| `created_at` | `datetime` | 否 | `CURRENT_TIMESTAMP` | （库无注释） |
| `updated_at` | `datetime` | 否 | `CURRENT_TIMESTAMP` | （库无注释） |

### `deduplication_record` — 文件去重记录

| 字段名 | 类型 | 是否为空 | 默认值 | 说明 |
|---|---|---|---|---|
| `id` | `bigint` | 否 | `NULL` | （库无注释） |
| `file_id` | `bigint` | 否 | `NULL` | （库无注释） |
| `matched_file_id` | `bigint` | 是 | `NULL` | （库无注释） |
| `matched_document_id` | `bigint` | 是 | `NULL` | （库无注释） |
| `match_type` | `varchar(30)` | 否 | `NULL` | （库无注释） |
| `match_score` | `decimal(5,2)` | 是 | `NULL` | （库无注释） |
| `hash_equal` | `tinyint` | 否 | `0` | （库无注释） |
| `name_similar` | `tinyint` | 否 | `0` | （库无注释） |
| `content_similar` | `tinyint` | 否 | `0` | （库无注释） |
| `decision_status` | `varchar(30)` | 否 | `PENDING` | （库无注释） |
| `decision_by` | `bigint` | 是 | `NULL` | （库无注释） |
| `decision_at` | `datetime` | 是 | `NULL` | （库无注释） |
| `created_at` | `datetime` | 否 | `CURRENT_TIMESTAMP` | （库无注释） |

### `dict_document_type` — 资料类型字典

| 字段名 | 类型 | 是否为空 | 默认值 | 说明 |
|---|---|---|---|---|
| `id` | `bigint` | 否 | `NULL` | （库无注释） |
| `type_code` | `varchar(64)` | 否 | `NULL` | （库无注释） |
| `type_name` | `varchar(100)` | 否 | `NULL` | （库无注释） |
| `module_code` | `varchar(10)` | 是 | `NULL` | （库无注释） |
| `enabled` | `tinyint` | 否 | `1` | （库无注释） |
| `created_at` | `datetime` | 否 | `CURRENT_TIMESTAMP` | （库无注释） |
| `updated_at` | `datetime` | 否 | `CURRENT_TIMESTAMP` | （库无注释） |

### `dict_esg_module` — ESG模块字典

| 字段名 | 类型 | 是否为空 | 默认值 | 说明 |
|---|---|---|---|---|
| `module_code` | `varchar(10)` | 否 | `NULL` | E/S/G |
| `module_name` | `varchar(50)` | 否 | `NULL` | 模块名称 |
| `display_order` | `int` | 否 | `NULL` | （库无注释） |
| `enabled` | `tinyint` | 否 | `1` | （库无注释） |
| `created_at` | `datetime` | 否 | `CURRENT_TIMESTAMP` | （库无注释） |
| `updated_at` | `datetime` | 否 | `CURRENT_TIMESTAMP` | （库无注释） |

### `document_task_relation` — 资料任务关联

| 字段名 | 类型 | 是否为空 | 默认值 | 说明 |
|---|---|---|---|---|
| `id` | `bigint` | 否 | `NULL` | （库无注释） |
| `document_id` | `bigint` | 否 | `NULL` | （库无注释） |
| `task_id` | `varchar(64)` | 否 | `NULL` | （库无注释） |
| `relation_type` | `varchar(30)` | 否 | `NULL` | （库无注释） |
| `relation_status` | `varchar(30)` | 否 | `NULL` | （库无注释） |
| `match_score` | `decimal(5,2)` | 是 | `NULL` | （库无注释） |
| `linked_by` | `bigint` | 是 | `NULL` | （库无注释） |
| `linked_at` | `datetime` | 是 | `NULL` | （库无注释） |
| `source` | `varchar(50)` | 是 | `NULL` | （库无注释） |
| `created_at` | `datetime` | 否 | `CURRENT_TIMESTAMP` | （库无注释） |

### `document_version` — 资料版本

| 字段名 | 类型 | 是否为空 | 默认值 | 说明 |
|---|---|---|---|---|
| `id` | `bigint` | 否 | `NULL` | （库无注释） |
| `document_id` | `bigint` | 否 | `NULL` | （库无注释） |
| `file_id` | `bigint` | 否 | `NULL` | （库无注释） |
| `version_no` | `varchar(20)` | 否 | `NULL` | （库无注释） |
| `version_desc` | `varchar(500)` | 是 | `NULL` | （库无注释） |
| `change_type` | `varchar(50)` | 是 | `NULL` | （库无注释） |
| `uploaded_by` | `bigint` | 是 | `NULL` | （库无注释） |
| `uploaded_at` | `datetime` | 否 | `NULL` | （库无注释） |
| `is_current` | `tinyint` | 否 | `0` | （库无注释） |
| `created_at` | `datetime` | 否 | `CURRENT_TIMESTAMP` | （库无注释） |

### `e01_legacy_record_mapping` — E01历史映射

| 字段名 | 类型 | 是否为空 | 默认值 | 说明 |
|---|---|---|---|---|
| `id` | `bigint` | 否 | `NULL` | （库无注释） |
| `legacy_table` | `varchar(80)` | 否 | `NULL` | （库无注释） |
| `legacy_record_id` | `bigint` | 否 | `NULL` | （库无注释） |
| `target_table` | `varchar(80)` | 是 | `NULL` | （库无注释） |
| `target_record_id` | `bigint` | 是 | `NULL` | （库无注释） |
| `mapping_status` | `varchar(40)` | 否 | `NULL` | （库无注释） |
| `reconciliation_class` | `varchar(60)` | 否 | `NULL` | （库无注释） |
| `difference_reason` | `varchar(1000)` | 是 | `NULL` | （库无注释） |
| `migration_version` | `varchar(64)` | 否 | `NULL` | （库无注释） |
| `created_at` | `timestamp(6)` | 否 | `CURRENT_TIMESTAMP(6)` | （库无注释） |

### `e01_monitor_plan_item` — E01监测计划明细

| 字段名 | 类型 | 是否为空 | 默认值 | 说明 |
|---|---|---|---|---|
| `id` | `bigint` | 否 | `NULL` | （库无注释） |
| `plan_id` | `bigint` | 否 | `NULL` | （库无注释） |
| `point_id` | `bigint` | 否 | `NULL` | （库无注释） |
| `monitor_category` | `varchar(20)` | 否 | `NULL` | （库无注释） |
| `planned_sample_at` | `datetime(6)` | 是 | `NULL` | （库无注释） |
| `planned_factor_scope` | `varchar(1000)` | 是 | `NULL` | （库无注释） |
| `execution_status` | `varchar(30)` | 否 | `PENDING` | （库无注释） |
| `data_nature` | `varchar(20)` | 否 | `NULL` | （库无注释） |
| `is_demo` | `tinyint(1)` | 否 | `0` | （库无注释） |
| `effective_status` | `varchar(30)` | 否 | `DRAFT` | （库无注释） |
| `effective_at` | `datetime(6)` | 是 | `NULL` | （库无注释） |
| `effective_by` | `bigint` | 是 | `NULL` | （库无注释） |
| `created_at` | `timestamp(6)` | 否 | `CURRENT_TIMESTAMP(6)` | （库无注释） |
| `updated_at` | `timestamp(6)` | 否 | `CURRENT_TIMESTAMP(6)` | （库无注释） |

### `e01_rectification_round` — E01整改轮次

| 字段名 | 类型 | 是否为空 | 默认值 | 说明 |
|---|---|---|---|---|
| `id` | `bigint` | 否 | `NULL` | （库无注释） |
| `event_id` | `bigint` | 否 | `NULL` | （库无注释） |
| `round_no` | `int` | 否 | `NULL` | （库无注释） |
| `task_id` | `bigint` | 是 | `NULL` | （库无注释） |
| `started_at` | `datetime(6)` | 是 | `NULL` | （库无注释） |
| `submitted_at` | `datetime(6)` | 是 | `NULL` | （库无注释） |
| `rectification_summary` | `varchar(1000)` | 是 | `NULL` | （库无注释） |
| `review_status` | `varchar(30)` | 否 | `PENDING_REVIEW` | （库无注释） |
| `data_nature` | `varchar(20)` | 否 | `NULL` | （库无注释） |
| `is_demo` | `tinyint(1)` | 否 | `0` | （库无注释） |
| `effective_status` | `varchar(30)` | 否 | `DRAFT` | （库无注释） |
| `effective_at` | `datetime(6)` | 是 | `NULL` | （库无注释） |
| `effective_by` | `bigint` | 是 | `NULL` | （库无注释） |
| `created_at` | `timestamp(6)` | 否 | `CURRENT_TIMESTAMP(6)` | （库无注释） |

### `e01_retest_result_link` — E01复测结果关联

| 字段名 | 类型 | 是否为空 | 默认值 | 说明 |
|---|---|---|---|---|
| `id` | `bigint` | 否 | `NULL` | （库无注释） |
| `event_id` | `bigint` | 否 | `NULL` | （库无注释） |
| `retest_round_id` | `bigint` | 否 | `NULL` | （库无注释） |
| `factor_result_id` | `bigint` | 否 | `NULL` | （库无注释） |
| `original_result_id` | `bigint` | 否 | `NULL` | （库无注释） |
| `data_nature` | `varchar(20)` | 否 | `NULL` | （库无注释） |
| `is_demo` | `tinyint(1)` | 否 | `0` | （库无注释） |
| `effective_status` | `varchar(30)` | 否 | `DRAFT` | （库无注释） |
| `effective_at` | `datetime(6)` | 是 | `NULL` | （库无注释） |
| `effective_by` | `bigint` | 是 | `NULL` | （库无注释） |
| `created_at` | `timestamp(6)` | 否 | `CURRENT_TIMESTAMP(6)` | （库无注释） |

### `e01_retest_round` — E01复测轮次

| 字段名 | 类型 | 是否为空 | 默认值 | 说明 |
|---|---|---|---|---|
| `id` | `bigint` | 否 | `NULL` | （库无注释） |
| `event_id` | `bigint` | 否 | `NULL` | （库无注释） |
| `round_no` | `int` | 否 | `NULL` | （库无注释） |
| `retest_batch_id` | `bigint` | 否 | `NULL` | （库无注释） |
| `requested_at` | `datetime(6)` | 是 | `NULL` | （库无注释） |
| `planned_sample_at` | `datetime(6)` | 是 | `NULL` | （库无注释） |
| `actual_sample_at` | `datetime(6)` | 是 | `NULL` | （库无注释） |
| `report_document_id` | `bigint` | 是 | `NULL` | （库无注释） |
| `outcome` | `varchar(30)` | 否 | `NULL` | （库无注释） |
| `review_status` | `varchar(30)` | 否 | `PENDING_REVIEW` | （库无注释） |
| `reviewed_at` | `datetime(6)` | 是 | `NULL` | （库无注释） |
| `reviewed_by` | `bigint` | 是 | `NULL` | （库无注释） |
| `data_nature` | `varchar(20)` | 否 | `NULL` | （库无注释） |
| `is_demo` | `tinyint(1)` | 否 | `0` | （库无注释） |
| `effective_status` | `varchar(30)` | 否 | `DRAFT` | （库无注释） |
| `effective_at` | `datetime(6)` | 是 | `NULL` | （库无注释） |
| `effective_by` | `bigint` | 是 | `NULL` | （库无注释） |
| `created_at` | `timestamp(6)` | 否 | `CURRENT_TIMESTAMP(6)` | （库无注释） |

### `e01_standard_version` — E01标准版本

| 字段名 | 类型 | 是否为空 | 默认值 | 说明 |
|---|---|---|---|---|
| `id` | `bigint` | 否 | `NULL` | （库无注释） |
| `standard_code` | `varchar(100)` | 否 | `NULL` | （库无注释） |
| `standard_name` | `varchar(255)` | 否 | `NULL` | （库无注释） |
| `version_no` | `varchar(80)` | 否 | `NULL` | （库无注释） |
| `issuing_authority` | `varchar(255)` | 是 | `NULL` | （库无注释） |
| `applicable_from` | `datetime(6)` | 是 | `NULL` | （库无注释） |
| `applicable_to` | `datetime(6)` | 是 | `NULL` | （库无注释） |
| `source_document_id` | `bigint` | 是 | `NULL` | （库无注释） |
| `data_nature` | `varchar(20)` | 否 | `NULL` | （库无注释） |
| `is_demo` | `tinyint(1)` | 否 | `0` | （库无注释） |
| `verification_status` | `varchar(30)` | 否 | `PENDING_REVIEW` | （库无注释） |
| `effective_status` | `varchar(30)` | 否 | `DRAFT` | （库无注释） |
| `effective_at` | `datetime(6)` | 是 | `NULL` | （库无注释） |
| `effective_by` | `bigint` | 是 | `NULL` | （库无注释） |

### `e_case_party` — 案件相关方

| 字段名 | 类型 | 是否为空 | 默认值 | 说明 |
|---|---|---|---|---|
| `id` | `bigint` | 否 | `NULL` | （库无注释） |
| `case_id` | `bigint` | 否 | `NULL` | （库无注释） |
| `party_role` | `varchar(30)` | 否 | `NULL` | （库无注释） |
| `org_id` | `bigint` | 是 | `NULL` | （库无注释） |
| `org_name` | `varchar(160)` | 是 | `NULL` | （库无注释） |
| `user_id` | `bigint` | 是 | `NULL` | （库无注释） |
| `user_name` | `varchar(100)` | 是 | `NULL` | （库无注释） |
| `valid_from` | `datetime(6)` | 否 | `NULL` | （库无注释） |
| `valid_to` | `datetime(6)` | 是 | `NULL` | （库无注释） |
| `is_current` | `tinyint(1)` | 否 | `1` | （库无注释） |
| `data_nature` | `varchar(20)` | 否 | `NULL` | （库无注释） |
| `is_demo` | `tinyint(1)` | 否 | `0` | （库无注释） |
| `created_at` | `timestamp(6)` | 否 | `CURRENT_TIMESTAMP(6)` | （库无注释） |

### `e_case_rectification_link` — 案件-整改任务关联

| 字段名 | 类型 | 是否为空 | 默认值 | 说明 |
|---|---|---|---|---|
| `id` | `bigint` | 否 | `NULL` | （库无注释） |
| `case_id` | `bigint` | 否 | `NULL` | （库无注释） |
| `task_id` | `bigint` | 否 | `NULL` | （库无注释） |
| `link_role` | `varchar(30)` | 否 | `PRIMARY` | （库无注释） |
| `data_nature` | `varchar(20)` | 否 | `NULL` | （库无注释） |
| `is_demo` | `tinyint(1)` | 否 | `0` | （库无注释） |
| `effective_status` | `varchar(30)` | 否 | `EFFECTIVE` | （库无注释） |
| `created_at` | `timestamp(6)` | 否 | `CURRENT_TIMESTAMP(6)` | （库无注释） |

### `e_case_relation` — 案件关联

| 字段名 | 类型 | 是否为空 | 默认值 | 说明 |
|---|---|---|---|---|
| `id` | `bigint` | 否 | `NULL` | （库无注释） |
| `from_case_id` | `bigint` | 否 | `NULL` | （库无注释） |
| `to_case_id` | `bigint` | 否 | `NULL` | （库无注释） |
| `relation_type` | `varchar(30)` | 否 | `NULL` | （库无注释） |
| `reason` | `varchar(500)` | 是 | `NULL` | （库无注释） |
| `data_nature` | `varchar(20)` | 否 | `NULL` | （库无注释） |
| `is_demo` | `tinyint(1)` | 否 | `0` | （库无注释） |
| `created_at` | `timestamp(6)` | 否 | `CURRENT_TIMESTAMP(6)` | （库无注释） |

### `e_case_status_history` — 案件状态历史

| 字段名 | 类型 | 是否为空 | 默认值 | 说明 |
|---|---|---|---|---|
| `id` | `bigint` | 否 | `NULL` | （库无注释） |
| `case_id` | `bigint` | 否 | `NULL` | （库无注释） |
| `sequence_no` | `int` | 否 | `NULL` | （库无注释） |
| `from_status` | `varchar(40)` | 是 | `NULL` | （库无注释） |
| `to_status` | `varchar(40)` | 否 | `NULL` | （库无注释） |
| `action_code` | `varchar(60)` | 否 | `NULL` | （库无注释） |
| `transition_result` | `varchar(30)` | 否 | `SUCCESS` | （库无注释） |
| `action_at` | `datetime(6)` | 否 | `NULL` | （库无注释） |
| `operator_id` | `bigint` | 是 | `NULL` | （库无注释） |
| `operator_name` | `varchar(100)` | 是 | `NULL` | （库无注释） |
| `operator_org_id` | `bigint` | 是 | `NULL` | （库无注释） |
| `operator_org_name` | `varchar(160)` | 是 | `NULL` | （库无注释） |
| `comment` | `varchar(1000)` | 是 | `NULL` | （库无注释） |
| `source_document_id` | `bigint` | 是 | `NULL` | （库无注释） |
| `client_request_id` | `varchar(100)` | 否 | `NULL` | （库无注释） |
| `correction_of_history_id` | `bigint` | 是 | `NULL` | （库无注释） |
| `data_nature` | `varchar(20)` | 否 | `NULL` | （库无注释） |
| `is_demo` | `tinyint(1)` | 否 | `0` | （库无注释） |
| `created_at` | `timestamp(6)` | 否 | `CURRENT_TIMESTAMP(6)` | （库无注释） |

### `engineering_object_phase` — 工程对象阶段

| 字段名 | 类型 | 是否为空 | 默认值 | 说明 |
|---|---|---|---|---|
| `id` | `bigint` | 否 | `NULL` | （库无注释） |
| `object_id` | `bigint` | 否 | `NULL` | （库无注释） |
| `phase_id` | `bigint` | 否 | `NULL` | （库无注释） |
| `process_code` | `varchar(80)` | 否 | `NULL` | （库无注释） |
| `process_name` | `varchar(160)` | 否 | `NULL` | （库无注释） |
| `process_start_at` | `datetime(6)` | 否 | `NULL` | （库无注释） |
| `process_end_at` | `datetime(6)` | 否 | `NULL` | （库无注释） |
| `process_status` | `varchar(20)` | 否 | `PLANNED` | （库无注释） |
| `data_nature` | `varchar(20)` | 否 | `NULL` | （库无注释） |
| `is_demo` | `tinyint(1)` | 否 | `0` | （库无注释） |
| `created_at` | `timestamp(6)` | 否 | `CURRENT_TIMESTAMP(6)` | （库无注释） |
| `updated_at` | `timestamp(6)` | 否 | `CURRENT_TIMESTAMP(6)` | （库无注释） |

### `esg_demo_indicator_detail` — Demo 指标对象明细

| 字段名 | 类型 | 是否为空 | 默认值 | 说明 |
|---|---|---|---|---|
| `id` | `bigint unsigned` | 否 | `NULL` | （库无注释） |
| `result_id` | `bigint unsigned` | 否 | `NULL` | （库无注释） |
| `project_id` | `bigint unsigned` | 否 | `NULL` | （库无注释） |
| `kpi_key` | `varchar(16)` | 否 | `NULL` | （库无注释） |
| `object_type` | `varchar(64)` | 否 | `NULL` | （库无注释） |
| `object_id` | `bigint unsigned` | 否 | `NULL` | （库无注释） |
| `object_name` | `varchar(255)` | 否 | `NULL` | （库无注释） |
| `metric_label` | `varchar(100)` | 否 | `NULL` | （库无注释） |
| `metric_value` | `varchar(255)` | 是 | `NULL` | （库无注释） |
| `metric_unit` | `varchar(32)` | 是 | `NULL` | （库无注释） |
| `status` | `varchar(32)` | 是 | `NULL` | （库无注释） |
| `risk_level` | `varchar(16)` | 是 | `NULL` | （库无注释） |
| `detail_json` | `json` | 是 | `NULL` | （库无注释） |

### `esg_demo_indicator_result` — Demo 指标结果适配层

| 字段名 | 类型 | 是否为空 | 默认值 | 说明 |
|---|---|---|---|---|
| `id` | `bigint unsigned` | 否 | `NULL` | （库无注释） |
| `project_id` | `bigint unsigned` | 否 | `NULL` | （库无注释） |
| `period_end` | `date` | 否 | `NULL` | （库无注释） |
| `kpi_key` | `varchar(16)` | 否 | `NULL` | （库无注释） |
| `kpi_name` | `varchar(200)` | 否 | `NULL` | （库无注释） |
| `domain_code` | `varchar(8)` | 否 | `NULL` | （库无注释） |
| `value_decimal` | `decimal(24,8)` | 是 | `NULL` | （库无注释） |
| `value_text` | `varchar(500)` | 是 | `NULL` | （库无注释） |
| `unit` | `varchar(32)` | 否 | `NULL` | （库无注释） |
| `hint` | `varchar(500)` | 是 | `NULL` | （库无注释） |
| `risk_level` | `varchar(16)` | 否 | `NULL` | （库无注释） |
| `source_summary` | `varchar(1000)` | 是 | `NULL` | （库无注释） |
| `rule_version` | `varchar(32)` | 否 | `NULL` | （库无注释） |
| `result_status` | `varchar(32)` | 否 | `PUBLISHED` | （库无注释） |
| `calculated_at` | `datetime` | 否 | `NULL` | （库无注释） |
| `published_at` | `datetime` | 是 | `NULL` | （库无注释） |

### `esg_schema_migration_history` — ESG 项目 Schema 迁移历史记录表（V1.1 引导）

| 字段名 | 类型 | 是否为空 | 默认值 | 说明 |
|---|---|---|---|---|
| `id` | `bigint` | 否 | `NULL` | （库无注释） |
| `version_key` | `varchar(64)` | 否 | `NULL` | 迁移脚本版本标识，如 V1_1_010 |
| `description` | `varchar(255)` | 否 | `NULL` | 脚本用途简述 |
| `file_name` | `varchar(255)` | 否 | `NULL` | SQL 文件名 |
| `checksum_sha256` | `char(64)` | 否 | `NULL` | 文件内容 SHA-256 校验和 |
| `execution_id` | `varchar(64)` | 否 | `NULL` | 本次执行的唯一标识 |
| `executed_at` | `datetime(6)` | 否 | `CURRENT_TIMESTAMP(6)` | 执行开始时间 |
| `finished_at` | `datetime(6)` | 是 | `NULL` | 执行结束时间 |
| `status` | `varchar(30)` | 否 | `NULL` | SUCCESS / FAILED / SKIPPED |
| `error_message` | `text` | 是 | `NULL` | 失败时的错误信息 |
| `executed_by` | `varchar(128)` | 是 | `NULL` | 执行者标识 |

### `gis_feature_business_summary` — GIS要素业务摘要

| 字段名 | 类型 | 是否为空 | 默认值 | 说明 |
|---|---|---|---|---|
| `feature_id` | `varchar(96)` | 否 | `NULL` | （库无注释） |
| `project_id` | `varchar(64)` | 否 | `LUOYI-ESG` | （库无注释） |
| `object_type` | `varchar(64)` | 否 | `NULL` | （库无注释） |
| `status_code` | `varchar(32)` | 是 | `NULL` | （库无注释） |
| `status_label` | `varchar(32)` | 是 | `NULL` | （库无注释） |
| `dashboard_title` | `varchar(120)` | 是 | `NULL` | （库无注释） |
| `dashboard_summary_json` | `json` | 否 | `NULL` | （库无注释） |
| `dashboard_note` | `text` | 是 | `NULL` | （库无注释） |
| `preview_detail_json` | `json` | 是 | `NULL` | （库无注释） |
| `target_module` | `varchar(64)` | 是 | `NULL` | （库无注释） |
| `target_route` | `varchar(255)` | 是 | `NULL` | （库无注释） |
| `updated_at` | `datetime` | 否 | `CURRENT_TIMESTAMP` | （库无注释） |

### `gis_layer` — GIS图层

| 字段名 | 类型 | 是否为空 | 默认值 | 说明 |
|---|---|---|---|---|
| `id` | `varchar(64)` | 否 | `NULL` | （库无注释） |
| `project_id` | `varchar(64)` | 否 | `LUOYI-ESG` | （库无注释） |
| `name` | `varchar(120)` | 否 | `NULL` | （库无注释） |
| `category` | `varchar(64)` | 是 | `NULL` | （库无注释） |
| `geometry_type` | `varchar(20)` | 否 | `NULL` | （库无注释） |
| `enabled` | `tinyint(1)` | 否 | `1` | （库无注释） |
| `object_type` | `varchar(64)` | 是 | `NULL` | （库无注释） |
| `source_type` | `varchar(32)` | 否 | `api` | （库无注释） |
| `source_url` | `varchar(255)` | 是 | `NULL` | （库无注释） |
| `style_json` | `json` | 否 | `NULL` | （库无注释） |
| `fields_json` | `json` | 是 | `NULL` | （库无注释） |
| `feature_count` | `int` | 否 | `0` | （库无注释） |
| `display_order` | `int` | 否 | `0` | （库无注释） |
| `created_at` | `datetime` | 否 | `CURRENT_TIMESTAMP` | （库无注释） |
| `updated_at` | `datetime` | 否 | `CURRENT_TIMESTAMP` | （库无注释） |

### `indicator_calculation_job` — 指标计算任务表

| 字段名 | 类型 | 是否为空 | 默认值 | 说明 |
|---|---|---|---|---|
| `id` | `bigint` | 否 | `NULL` | （库无注释） |
| `indicator_code` | `varchar(20)` | 否 | `NULL` | （库无注释） |
| `calculation_type` | `varchar(30)` | 否 | `NULL` | EVENT_TRIGGER/SCHEDULED/MANUAL |
| `trigger_source` | `varchar(100)` | 是 | `NULL` | 触发来源，如 permit_record 更新、每日定时等 |
| `trigger_record_id` | `varchar(100)` | 是 | `NULL` | （库无注释） |
| `job_status` | `varchar(30)` | 否 | `NULL` | PENDING/RUNNING/SUCCESS/FAILED |
| `calculation_period` | `varchar(50)` | 是 | `NULL` | 计算周期，如 2026-07 |
| `started_at` | `datetime` | 是 | `NULL` | （库无注释） |
| `finished_at` | `datetime` | 是 | `NULL` | （库无注释） |
| `result_value` | `decimal(18,4)` | 是 | `NULL` | （库无注释） |
| `result_payload` | `json` | 是 | `NULL` | 指标详情或弹窗聚合结果 |
| `error_message` | `text` | 是 | `NULL` | （库无注释） |
| `created_at` | `datetime` | 否 | `CURRENT_TIMESTAMP` | （库无注释） |

### `indicator_history` — 指标历史结果表

| 字段名 | 类型 | 是否为空 | 默认值 | 说明 |
|---|---|---|---|---|
| `id` | `bigint` | 否 | `NULL` | （库无注释） |
| `indicator_code` | `varchar(20)` | 否 | `NULL` | （库无注释） |
| `result_date` | `date` | 否 | `NULL` | （库无注释） |
| `result_value` | `decimal(18,4)` | 否 | `NULL` | （库无注释） |
| `result_text` | `varchar(100)` | 是 | `NULL` | （库无注释） |
| `unit` | `varchar(30)` | 是 | `NULL` | （库无注释） |
| `calculation_job_id` | `bigint` | 是 | `NULL` | （库无注释） |
| `detail_payload` | `json` | 是 | `NULL` | 当日指标详情快照 |
| `created_at` | `datetime` | 否 | `CURRENT_TIMESTAMP` | （库无注释） |

### `indicator_snapshot` — 指标/页面快照

| 字段名 | 类型 | 是否为空 | 默认值 | 说明 |
|---|---|---|---|---|
| `snapshot_type` | `varchar(50)` | 否 | `NULL` | （库无注释） |
| `snapshot_date` | `date` | 否 | `NULL` | （库无注释） |
| `payload_json` | `json` | 否 | `NULL` | （库无注释） |
| `published_at` | `datetime` | 否 | `NULL` | （库无注释） |

### `indicator_source_dependency` — 指标数据源依赖表

| 字段名 | 类型 | 是否为空 | 默认值 | 说明 |
|---|---|---|---|---|
| `id` | `bigint` | 否 | `NULL` | （库无注释） |
| `indicator_code` | `varchar(20)` | 否 | `NULL` | （库无注释） |
| `source_table` | `varchar(100)` | 否 | `NULL` | （库无注释） |
| `dependency_type` | `varchar(30)` | 否 | `NULL` | PRIMARY/SECONDARY/REFERENCE |
| `calculation_desc` | `varchar(500)` | 是 | `NULL` | （库无注释） |
| `enabled` | `tinyint` | 否 | `1` | （库无注释） |
| `created_at` | `datetime` | 否 | `CURRENT_TIMESTAMP` | （库无注释） |

### `manual_confirmation_log` — 人工确认记录

| 字段名 | 类型 | 是否为空 | 默认值 | 说明 |
|---|---|---|---|---|
| `id` | `bigint` | 否 | `NULL` | （库无注释） |
| `target_type` | `varchar(50)` | 否 | `NULL` | （库无注释） |
| `target_id` | `bigint` | 否 | `NULL` | （库无注释） |
| `action_type` | `varchar(50)` | 否 | `NULL` | （库无注释） |
| `before_json` | `json` | 是 | `NULL` | （库无注释） |
| `after_json` | `json` | 是 | `NULL` | （库无注释） |
| `comment` | `varchar(500)` | 是 | `NULL` | （库无注释） |
| `operator_id` | `bigint` | 是 | `NULL` | （库无注释） |
| `operator_name` | `varchar(100)` | 是 | `NULL` | （库无注释） |
| `operated_at` | `datetime` | 否 | `NULL` | （库无注释） |

### `monitor_frequency_rule` — 监测频次规则

| 字段名 | 类型 | 是否为空 | 默认值 | 说明 |
|---|---|---|---|---|
| `id` | `bigint` | 否 | `NULL` | （库无注释） |
| `rule_code` | `varchar(100)` | 否 | `NULL` | （库无注释） |
| `plan_item_id` | `bigint` | 否 | `NULL` | （库无注释） |
| `frequency_code` | `varchar(30)` | 否 | `NULL` | （库无注释） |
| `interval_value` | `int` | 是 | `NULL` | （库无注释） |
| `interval_unit` | `varchar(20)` | 是 | `NULL` | （库无注释） |
| `schedule_expression` | `varchar(160)` | 是 | `NULL` | （库无注释） |
| `aggregation_granularity` | `varchar(30)` | 是 | `NULL` | （库无注释） |
| `trigger_event` | `varchar(160)` | 是 | `NULL` | （库无注释） |
| `effective_from` | `datetime(6)` | 否 | `NULL` | （库无注释） |
| `effective_to` | `datetime(6)` | 是 | `NULL` | （库无注释） |
| `active_status` | `varchar(20)` | 否 | `ACTIVE` | （库无注释） |
| `data_nature` | `varchar(20)` | 否 | `NULL` | （库无注释） |
| `is_demo` | `tinyint(1)` | 否 | `0` | （库无注释） |
| `created_at` | `timestamp(6)` | 否 | `CURRENT_TIMESTAMP(6)` | （库无注释） |
| `updated_at` | `timestamp(6)` | 否 | `CURRENT_TIMESTAMP(6)` | （库无注释） |

### `monitor_point_object_relation` — 监测点与对象关联

| 字段名 | 类型 | 是否为空 | 默认值 | 说明 |
|---|---|---|---|---|
| `id` | `bigint` | 否 | `NULL` | （库无注释） |
| `relation_code` | `varchar(100)` | 否 | `NULL` | （库无注释） |
| `point_id` | `bigint` | 否 | `NULL` | （库无注释） |
| `section_id` | `bigint` | 否 | `NULL` | （库无注释） |
| `object_id` | `bigint` | 否 | `NULL` | （库无注释） |
| `phase_id` | `bigint` | 是 | `NULL` | （库无注释） |
| `object_phase_id` | `bigint` | 是 | `NULL` | （库无注释） |
| `relation_role` | `varchar(30)` | 否 | `PRIMARY` | （库无注释） |
| `valid_from` | `datetime(6)` | 否 | `NULL` | （库无注释） |
| `valid_to` | `datetime(6)` | 是 | `NULL` | （库无注释） |
| `data_nature` | `varchar(20)` | 否 | `NULL` | （库无注释） |
| `is_demo` | `tinyint(1)` | 否 | `0` | （库无注释） |
| `created_at` | `timestamp(6)` | 否 | `CURRENT_TIMESTAMP(6)` | （库无注释） |
| `updated_at` | `timestamp(6)` | 否 | `CURRENT_TIMESTAMP(6)` | （库无注释） |

### `monthly_report_chapter` — 月报章节清单

| 字段名 | 类型 | 是否为空 | 默认值 | 说明 |
|---|---|---|---|---|
| `id` | `bigint` | 否 | `NULL` | （库无注释） |
| `cycle_id` | `bigint` | 否 | `NULL` | （库无注释） |
| `chapter_index` | `int` | 否 | `NULL` | （库无注释） |
| `chapter_name` | `varchar(255)` | 否 | `NULL` | （库无注释） |
| `material_type` | `varchar(100)` | 是 | `NULL` | （库无注释） |
| `group_name` | `varchar(30)` | 是 | `NULL` | （库无注释） |
| `owner` | `varchar(100)` | 是 | `NULL` | （库无注释） |
| `responsible_person` | `varchar(100)` | 是 | `NULL` | （库无注释） |
| `status` | `varchar(50)` | 是 | `NULL` | （库无注释） |
| `deadline` | `varchar(50)` | 是 | `NULL` | （库无注释） |
| `created_at` | `datetime` | 否 | `CURRENT_TIMESTAMP` | （库无注释） |

### `monthly_report_cycle` — 月报周期主表

| 字段名 | 类型 | 是否为空 | 默认值 | 说明 |
|---|---|---|---|---|
| `id` | `bigint` | 否 | `NULL` | （库无注释） |
| `report_period` | `varchar(50)` | 否 | `NULL` | （库无注释） |
| `report_name` | `varchar(255)` | 否 | `NULL` | （库无注释） |
| `completion_rate` | `decimal(10,2)` | 否 | `0.00` | （库无注释） |
| `expected_complete_date` | `varchar(50)` | 是 | `NULL` | （库无注释） |
| `current_stage` | `varchar(50)` | 是 | `NULL` | （库无注释） |
| `update_time` | `datetime` | 是 | `NULL` | （库无注释） |
| `created_at` | `datetime` | 否 | `CURRENT_TIMESTAMP` | （库无注释） |

### `monthly_report_gap` — 月报缺项清单

| 字段名 | 类型 | 是否为空 | 默认值 | 说明 |
|---|---|---|---|---|
| `id` | `bigint` | 否 | `NULL` | （库无注释） |
| `cycle_id` | `bigint` | 否 | `NULL` | （库无注释） |
| `material_name` | `varchar(255)` | 否 | `NULL` | （库无注释） |
| `group_name` | `varchar(30)` | 是 | `NULL` | （库无注释） |
| `owner` | `varchar(100)` | 是 | `NULL` | （库无注释） |
| `deadline` | `varchar(50)` | 是 | `NULL` | （库无注释） |
| `status` | `varchar(50)` | 是 | `NULL` | （库无注释） |
| `note` | `varchar(500)` | 是 | `NULL` | （库无注释） |
| `created_at` | `datetime` | 否 | `CURRENT_TIMESTAMP` | （库无注释） |

### `monthly_report_group_progress` — 月报分组完成进度

| 字段名 | 类型 | 是否为空 | 默认值 | 说明 |
|---|---|---|---|---|
| `id` | `bigint` | 否 | `NULL` | （库无注释） |
| `cycle_id` | `bigint` | 否 | `NULL` | （库无注释） |
| `group_code` | `varchar(10)` | 否 | `NULL` | （库无注释） |
| `group_label` | `varchar(30)` | 否 | `NULL` | （库无注释） |
| `completion_rate` | `decimal(10,2)` | 否 | `0.00` | （库无注释） |
| `color` | `varchar(30)` | 是 | `NULL` | （库无注释） |
| `created_at` | `datetime` | 否 | `CURRENT_TIMESTAMP` | （库无注释） |

### `monthly_report_status_chain` — 月报状态链

| 字段名 | 类型 | 是否为空 | 默认值 | 说明 |
|---|---|---|---|---|
| `id` | `bigint` | 否 | `NULL` | （库无注释） |
| `cycle_id` | `bigint` | 否 | `NULL` | （库无注释） |
| `chain_key` | `varchar(50)` | 否 | `NULL` | （库无注释） |
| `label` | `varchar(100)` | 否 | `NULL` | （库无注释） |
| `status` | `varchar(30)` | 否 | `NULL` | （库无注释） |
| `display_order` | `int` | 否 | `NULL` | （库无注释） |
| `created_at` | `datetime` | 否 | `CURRENT_TIMESTAMP` | （库无注释） |

### `monthly_report_task_instance` — 月报资料任务实例统计扩展表

| 字段名 | 类型 | 是否为空 | 默认值 | 说明 |
|---|---|---|---|---|
| `id` | `bigint` | 否 | `NULL` | （库无注释） |
| `report_cycle_id` | `bigint` | 否 | `NULL` | （库无注释） |
| `upload_task_id` | `varchar(64)` | 是 | `NULL` | （库无注释） |
| `task_code` | `varchar(64)` | 否 | `NULL` | （库无注释） |
| `task_name` | `varchar(255)` | 否 | `NULL` | （库无注释） |
| `group_code` | `varchar(20)` | 否 | `NULL` | （库无注释） |
| `task_mechanism` | `varchar(30)` | 否 | `NULL` | （库无注释） |
| `scope_type` | `varchar(30)` | 否 | `NULL` | （库无注释） |
| `scope_key` | `varchar(100)` | 否 | `NULL` | （库无注释） |
| `monthly_status` | `varchar(30)` | 否 | `NULL` | （库无注释） |
| `triggered_flag` | `tinyint` | 否 | `1` | （库无注释） |
| `confirmation_required` | `tinyint` | 否 | `0` | （库无注释） |
| `include_in_denominator` | `tinyint` | 否 | `0` | （库无注释） |
| `responsible_unit` | `varchar(255)` | 否 | `NULL` | （库无注释） |
| `deadline` | `date` | 否 | `NULL` | （库无注释） |
| `dedup_key` | `varchar(255)` | 否 | `NULL` | （库无注释） |
| `validation_passed_at` | `datetime` | 是 | `NULL` | （库无注释） |
| `not_applicable_reason` | `varchar(500)` | 是 | `NULL` | （库无注释） |
| `not_applicable_confirmed_by` | `varchar(100)` | 是 | `NULL` | （库无注释） |
| `not_applicable_confirmed_at` | `datetime` | 是 | `NULL` | （库无注释） |
| `source_tag` | `varchar(50)` | 是 | `NULL` | （库无注释） |
| `created_at` | `datetime` | 否 | `CURRENT_TIMESTAMP` | （库无注释） |
| `updated_at` | `datetime` | 否 | `CURRENT_TIMESTAMP` | （库无注释） |
| `responsible_department` | `varchar(255)` | 是 | `NULL` | 责任部门/单位标准字段 |
| `responsible_role` | `varchar(100)` | 是 | `NULL` | 无人员主数据时使用的责任角色 |
| `responsible_user_id` | `bigint` | 是 | `NULL` | 正式责任用户ID |
| `responsible_user_name` | `varchar(100)` | 是 | `NULL` | 正式责任用户姓名 |
| `data_nature` | `varchar(30)` | 是 | `NULL` | 数据性质：formal/demo |
| `is_demo` | `tinyint(1)` | 否 | `0` | 演示记录标志 |

### `monthly_report_task_material_link` — 月报任务所需资料及资料关联

| 字段名 | 类型 | 是否为空 | 默认值 | 说明 |
|---|---|---|---|---|
| `id` | `bigint` | 否 | `NULL` | （库无注释） |
| `link_code` | `varchar(100)` | 否 | `NULL` | （库无注释） |
| `task_instance_id` | `bigint` | 否 | `NULL` | （库无注释） |
| `required_material_code` | `varchar(100)` | 否 | `NULL` | （库无注释） |
| `required_material_name` | `varchar(255)` | 否 | `NULL` | （库无注释） |
| `document_id` | `bigint` | 是 | `NULL` | （库无注释） |
| `source_task_id` | `varchar(64)` | 是 | `NULL` | （库无注释） |
| `relation_status` | `varchar(30)` | 否 | `NULL` | （库无注释） |
| `data_nature` | `varchar(30)` | 否 | `NULL` | （库无注释） |
| `is_demo` | `tinyint(1)` | 否 | `0` | （库无注释） |
| `created_at` | `datetime` | 否 | `CURRENT_TIMESTAMP` | （库无注释） |
| `updated_at` | `datetime` | 否 | `CURRENT_TIMESTAMP` | （库无注释） |

### `monthly_report_task_validation` — 月报任务完整性校验与补正记录

| 字段名 | 类型 | 是否为空 | 默认值 | 说明 |
|---|---|---|---|---|
| `id` | `bigint` | 否 | `NULL` | （库无注释） |
| `validation_code` | `varchar(100)` | 否 | `NULL` | （库无注释） |
| `task_instance_id` | `bigint` | 否 | `NULL` | （库无注释） |
| `validation_result` | `varchar(30)` | 否 | `NULL` | （库无注释） |
| `issue_description` | `varchar(500)` | 是 | `NULL` | （库无注释） |
| `correction_requirement` | `varchar(500)` | 是 | `NULL` | （库无注释） |
| `next_action_type` | `varchar(50)` | 否 | `NULL` | （库无注释） |
| `validated_at` | `datetime` | 是 | `NULL` | （库无注释） |
| `data_nature` | `varchar(30)` | 否 | `NULL` | （库无注释） |
| `is_demo` | `tinyint(1)` | 否 | `0` | （库无注释） |
| `created_at` | `datetime` | 否 | `CURRENT_TIMESTAMP` | （库无注释） |
| `updated_at` | `datetime` | 否 | `CURRENT_TIMESTAMP` | （库无注释） |

### `project_engineering_object` — 工程对象

| 字段名 | 类型 | 是否为空 | 默认值 | 说明 |
|---|---|---|---|---|
| `id` | `bigint` | 否 | `NULL` | （库无注释） |
| `project_id` | `varchar(64)` | 否 | `LUOYI-ESG` | （库无注释） |
| `section_id` | `bigint` | 否 | `NULL` | （库无注释） |
| `object_code` | `varchar(80)` | 否 | `NULL` | （库无注释） |
| `object_name` | `varchar(200)` | 否 | `NULL` | （库无注释） |
| `object_type` | `varchar(60)` | 否 | `NULL` | （库无注释） |
| `chainage_start` | `varchar(40)` | 是 | `NULL` | （库无注释） |
| `chainage_end` | `varchar(40)` | 是 | `NULL` | （库无注释） |
| `longitude` | `decimal(11,8)` | 是 | `NULL` | （库无注释） |
| `latitude` | `decimal(10,8)` | 是 | `NULL` | （库无注释） |
| `gis_feature_id` | `varchar(96)` | 是 | `NULL` | （库无注释） |
| `active_status` | `varchar(20)` | 否 | `ACTIVE` | （库无注释） |
| `data_nature` | `varchar(20)` | 否 | `NULL` | （库无注释） |
| `is_demo` | `tinyint(1)` | 否 | `0` | （库无注释） |
| `created_at` | `timestamp(6)` | 否 | `CURRENT_TIMESTAMP(6)` | （库无注释） |
| `updated_at` | `timestamp(6)` | 否 | `CURRENT_TIMESTAMP(6)` | （库无注释） |

### `project_phase_period` — 项目阶段周期

| 字段名 | 类型 | 是否为空 | 默认值 | 说明 |
|---|---|---|---|---|
| `id` | `bigint` | 否 | `NULL` | （库无注释） |
| `project_id` | `varchar(64)` | 否 | `LUOYI-ESG` | （库无注释） |
| `phase_code` | `varchar(60)` | 否 | `NULL` | （库无注释） |
| `phase_name` | `varchar(160)` | 否 | `NULL` | （库无注释） |
| `phase_type` | `varchar(50)` | 否 | `NULL` | （库无注释） |
| `start_at` | `datetime(6)` | 否 | `NULL` | （库无注释） |
| `end_at` | `datetime(6)` | 否 | `NULL` | （库无注释） |
| `phase_status` | `varchar(20)` | 否 | `PLANNED` | （库无注释） |
| `data_nature` | `varchar(20)` | 否 | `NULL` | （库无注释） |
| `is_demo` | `tinyint(1)` | 否 | `0` | （库无注释） |
| `created_at` | `timestamp(6)` | 否 | `CURRENT_TIMESTAMP(6)` | （库无注释） |
| `updated_at` | `timestamp(6)` | 否 | `CURRENT_TIMESTAMP(6)` | （库无注释） |

### `review_record` — 审核记录

| 字段名 | 类型 | 是否为空 | 默认值 | 说明 |
|---|---|---|---|---|
| `id` | `varchar(64)` | 否 | `NULL` | （库无注释） |
| `task_id` | `varchar(64)` | 是 | `NULL` | （库无注释） |
| `task_name` | `varchar(255)` | 否 | `NULL` | （库无注释） |
| `module_code` | `varchar(10)` | 否 | `NULL` | （库无注释） |
| `module_name` | `varchar(50)` | 否 | `NULL` | （库无注释） |
| `submit_time` | `datetime` | 否 | `NULL` | （库无注释） |
| `status` | `varchar(30)` | 否 | `NULL` | （库无注释） |
| `reviewer_id` | `bigint` | 是 | `NULL` | （库无注释） |
| `reviewer` | `varchar(100)` | 是 | `NULL` | （库无注释） |
| `comment_summary` | `varchar(500)` | 是 | `NULL` | （库无注释） |
| `next_step` | `varchar(100)` | 否 | `NULL` | （库无注释） |
| `created_at` | `datetime` | 否 | `CURRENT_TIMESTAMP` | （库无注释） |
| `updated_at` | `datetime` | 否 | `CURRENT_TIMESTAMP` | （库无注释） |

### `review_requirement` — 审核补正要求

| 字段名 | 类型 | 是否为空 | 默认值 | 说明 |
|---|---|---|---|---|
| `id` | `bigint` | 否 | `NULL` | （库无注释） |
| `review_id` | `varchar(64)` | 否 | `NULL` | （库无注释） |
| `requirement_text` | `varchar(500)` | 否 | `NULL` | （库无注释） |
| `requirement_status` | `varchar(30)` | 否 | `待补正` | （库无注释） |
| `sequence_no` | `int` | 否 | `0` | （库无注释） |
| `created_at` | `datetime` | 否 | `CURRENT_TIMESTAMP` | （库无注释） |

### `review_timeline` — 审核轨迹

| 字段名 | 类型 | 是否为空 | 默认值 | 说明 |
|---|---|---|---|---|
| `id` | `bigint` | 否 | `NULL` | （库无注释） |
| `review_id` | `varchar(64)` | 否 | `NULL` | （库无注释） |
| `event_time` | `datetime` | 否 | `NULL` | （库无注释） |
| `action_text` | `varchar(500)` | 否 | `NULL` | （库无注释） |
| `event_type` | `varchar(50)` | 是 | `NULL` | （库无注释） |
| `operator_name` | `varchar(100)` | 是 | `NULL` | （库无注释） |
| `sequence_no` | `int` | 否 | `0` | （库无注释） |
| `created_at` | `datetime` | 否 | `CURRENT_TIMESTAMP` | （库无注释） |

### `source_record_trace` — 业务记录来源追溯表

| 字段名 | 类型 | 是否为空 | 默认值 | 说明 |
|---|---|---|---|---|
| `id` | `bigint` | 否 | `NULL` | （库无注释） |
| `ingestion_job_id` | `bigint` | 否 | `NULL` | （库无注释） |
| `source_id` | `bigint` | 否 | `NULL` | （库无注释） |
| `source_type` | `varchar(30)` | 否 | `NULL` | UPLOAD/API/MANUAL/BATCH/GIS/SCHEDULE |
| `source_record_key` | `varchar(100)` | 是 | `NULL` | 来源记录ID、文件ID、解析字段ID等 |
| `document_id` | `bigint` | 是 | `NULL` | 如来自资料上传，关联 document_record |
| `file_id` | `bigint` | 是 | `NULL` | 如来自文件，关联 file_asset |
| `target_table` | `varchar(100)` | 否 | `NULL` | （库无注释） |
| `target_record_id` | `varchar(100)` | 否 | `NULL` | （库无注释） |
| `operation_type` | `varchar(30)` | 否 | `NULL` | INSERT/UPDATE/UPSERT/DELETE |
| `trace_payload` | `json` | 是 | `NULL` | 来源关键字段快照 |
| `created_at` | `datetime` | 否 | `CURRENT_TIMESTAMP` | （库无注释） |

### `task_candidate_document` — 任务办理候选关联资料

| 字段名 | 类型 | 是否为空 | 默认值 | 说明 |
|---|---|---|---|---|
| `id` | `varchar(64)` | 否 | `NULL` | （库无注释） |
| `task_id` | `varchar(64)` | 否 | `NULL` | （库无注释） |
| `name` | `varchar(255)` | 否 | `NULL` | （库无注释） |
| `cycle` | `varchar(50)` | 否 | `NULL` | （库无注释） |
| `unit_name` | `varchar(100)` | 否 | `NULL` | （库无注释） |
| `link_count` | `int` | 否 | `0` | （库无注释） |
| `match_rate` | `int` | 否 | `0` | （库无注释） |
| `sequence_no` | `int` | 否 | `0` | （库无注释） |
| `created_at` | `datetime` | 否 | `CURRENT_TIMESTAMP` | （库无注释） |
| `updated_at` | `datetime` | 否 | `CURRENT_TIMESTAMP` | （库无注释） |

### `task_match_candidate` — AI候选任务匹配

| 字段名 | 类型 | 是否为空 | 默认值 | 说明 |
|---|---|---|---|---|
| `id` | `bigint` | 否 | `NULL` | （库无注释） |
| `parse_job_id` | `bigint` | 否 | `NULL` | （库无注释） |
| `file_id` | `bigint` | 否 | `NULL` | （库无注释） |
| `document_id` | `bigint` | 是 | `NULL` | （库无注释） |
| `task_id` | `varchar(64)` | 否 | `NULL` | （库无注释） |
| `task_name` | `varchar(255)` | 是 | `NULL` | （库无注释） |
| `module_code` | `varchar(10)` | 是 | `NULL` | （库无注释） |
| `match_score` | `decimal(5,2)` | 否 | `NULL` | （库无注释） |
| `match_reason` | `text` | 是 | `NULL` | （库无注释） |
| `reuse_count` | `int` | 否 | `0` | （库无注释） |
| `candidate_status` | `varchar(30)` | 否 | `PENDING` | （库无注释） |
| `confirmed_by` | `bigint` | 是 | `NULL` | （库无注释） |
| `confirmed_at` | `datetime` | 是 | `NULL` | （库无注释） |
| `created_at` | `datetime` | 否 | `CURRENT_TIMESTAMP` | （库无注释） |

### `task_review_timeline` — 任务办理审核时间线

| 字段名 | 类型 | 是否为空 | 默认值 | 说明 |
|---|---|---|---|---|
| `id` | `varchar(64)` | 否 | `NULL` | （库无注释） |
| `task_id` | `varchar(64)` | 否 | `NULL` | （库无注释） |
| `event_time` | `datetime` | 否 | `NULL` | （库无注释） |
| `action_text` | `varchar(500)` | 否 | `NULL` | （库无注释） |
| `sequence_no` | `int` | 否 | `0` | （库无注释） |
| `created_at` | `datetime` | 否 | `CURRENT_TIMESTAMP` | （库无注释） |

### `upload_task` — 上传任务

| 字段名 | 类型 | 是否为空 | 默认值 | 说明 |
|---|---|---|---|---|
| `id` | `varchar(64)` | 否 | `NULL` | （库无注释） |
| `name` | `varchar(255)` | 否 | `NULL` | （库无注释） |
| `module_code` | `varchar(10)` | 否 | `NULL` | （库无注释） |
| `module_name` | `varchar(50)` | 否 | `NULL` | （库无注释） |
| `cycle` | `varchar(50)` | 否 | `NULL` | （库无注释） |
| `cycle_type` | `varchar(30)` | 否 | `NULL` | （库无注释） |
| `deadline` | `datetime` | 否 | `NULL` | （库无注释） |
| `progress_current` | `int` | 否 | `0` | （库无注释） |
| `progress_total` | `int` | 否 | `0` | （库无注释） |
| `status` | `varchar(30)` | 否 | `NULL` | （库无注释） |
| `next_step` | `varchar(100)` | 否 | `NULL` | （库无注释） |
| `assignee_id` | `bigint` | 是 | `NULL` | （库无注释） |
| `assignee_name` | `varchar(100)` | 是 | `NULL` | （库无注释） |
| `assignee_dept` | `varchar(100)` | 是 | `NULL` | （库无注释） |
| `priority_code` | `varchar(30)` | 是 | `NULL` | （库无注释） |
| `created_at` | `datetime` | 否 | `CURRENT_TIMESTAMP` | （库无注释） |
| `updated_at` | `datetime` | 否 | `CURRENT_TIMESTAMP` | （库无注释） |

### `upload_task_requirement` — 上传任务资料要求

| 字段名 | 类型 | 是否为空 | 默认值 | 说明 |
|---|---|---|---|---|
| `id` | `varchar(64)` | 否 | `NULL` | （库无注释） |
| `task_id` | `varchar(64)` | 否 | `NULL` | （库无注释） |
| `name` | `varchar(255)` | 否 | `NULL` | （库无注释） |
| `required` | `tinyint` | 否 | `1` | （库无注释） |
| `format_rule` | `varchar(255)` | 否 | `NULL` | （库无注释） |
| `status` | `varchar(30)` | 否 | `NULL` | （库无注释） |
| `template_available` | `tinyint` | 否 | `0` | （库无注释） |
| `sequence_no` | `int` | 否 | `0` | （库无注释） |
| `created_at` | `datetime` | 否 | `CURRENT_TIMESTAMP` | （库无注释） |
| `updated_at` | `datetime` | 否 | `CURRENT_TIMESTAMP` | （库无注释） |

### `user_account` — 用户账号

| 字段名 | 类型 | 是否为空 | 默认值 | 说明 |
|---|---|---|---|---|
| `id` | `bigint` | 否 | `NULL` | （库无注释） |
| `username` | `varchar(80)` | 否 | `NULL` | （库无注释） |
| `display_name` | `varchar(100)` | 否 | `NULL` | （库无注释） |
| `org_id` | `bigint` | 是 | `NULL` | （库无注释） |
| `role_name` | `varchar(100)` | 是 | `NULL` | （库无注释） |
| `enabled` | `tinyint` | 否 | `1` | （库无注释） |
| `created_at` | `datetime` | 否 | `CURRENT_TIMESTAMP` | （库无注释） |
| `updated_at` | `datetime` | 否 | `CURRENT_TIMESTAMP` | （库无注释） |

### `workspace_summary` — 工作台摘要快照

| 字段名 | 类型 | 是否为空 | 默认值 | 说明 |
|---|---|---|---|---|
| `id` | `int` | 否 | `NULL` | （库无注释） |
| `current_todo` | `int` | 否 | `NULL` | （库无注释） |
| `pending_upload` | `int` | 否 | `NULL` | （库无注释） |
| `pending_correction` | `int` | 否 | `NULL` | （库无注释） |
| `pending_submit` | `int` | 否 | `NULL` | （库无注释） |
| `under_review` | `int` | 否 | `NULL` | （库无注释） |
| `due_soon` | `int` | 否 | `NULL` | （库无注释） |
| `completed` | `int` | 否 | `NULL` | （库无注释） |
| `updated_at` | `datetime` | 否 | `CURRENT_TIMESTAMP` | （库无注释） |

## 8. Excel 模板设计建议

1. **按业务主题拆分工作簿**，不要一张表塞进全部 129 张库表。推荐最少拆分：
   - E：监测点、监测结果、环保问题、水保对象、生态文物、碳数据；
   - S：风险点、安全生产确认、劳务纠纷、工资汇总、群众诉求；
   - G：合规手续、许可、专项方案审批、设计变更、内控问题；
   - 综合：闭环案件、整改任务完成填报、资料清单。
2. **主数据先于业务数据**：`org_unit`、`project_section`、监测点、风险点先建下拉字典。
3. **文件与业务分离**：Excel 填业务键和文件编号；文件本体走上传接口/`file_asset`，模板只留 `file_code`/`approval_file_id` 列。
4. **禁止录入 KPI 结果表**：首页 12 项指标由系统计算；模板最多做“核对清单”，不得作为正式写入源。
5. **整改完成日期**：`e_rectification_task.rectification_completed_date` 必须由甲方填写，不得用关闭时间或当天日期顶替。
6. **专项方案审批**：`special_plan_approval` 为合规证据链，模板提供新增/变更字段，**不提供删除列**。
7. **Demo 标识**：涉及演示数据时保留 `data_nature`/`is_demo` 列，避免与正式数据混淆。
8. **GIS**：业务表优先填业务主键，空间位置通过 `gis_feature` / `gis_feature_business_relation` 或监测点坐标字段关联，避免在 Excel 中手写复杂几何。
9. **必填规则**：库中 `IS_NULLABLE=NO` 且无默认值的字段，应作为模板必填；有默认值的技术字段可隐藏。
10. **每行一事实**：一对象一行、一监测结果一行、一许可一行，禁止合并单元格表达多条事实。

## 9. 数据来源说明

| 来源类型 | 说明 | 对应库对象示例 |
|---|---|---|
| 现场人工台账 | Excel/工作台录入 | 问题、风险点、许可、诉求、对象台账 |
| 检测机构报告 | 上传后解析或手工摘录 | E01 批次/样品/因子结果、`file_asset` |
| 建设单位确认 | 签字确认批次 | `s01_confirmation_batch` |
| 系统计算 | 规则/任务/视图 | 指标结果、预警、首页 KPI 视图 |
| AI 辅助抽取 | 解析后人工确认 | `ai_parse_field_result` → 业务表 |
| GIS 图层 | 空间数据与业务挂接 | `gis_layer`、`gis_feature*` |

## 10. 使用与维护说明

- 本文仅用于**采集模板设计与现场数据采集范围确认**。
- 若后续执行新的数据库迁移，需重新只读扫描后再更新本文。
- 开发接口、首页 KPI 口径变更不在本文范围。

---

*生成依据：MySQL `luoyi_esg` @ `127.0.0.1:3307`，版本 8.4.9；扫描账号 `luoyi_app`。*
