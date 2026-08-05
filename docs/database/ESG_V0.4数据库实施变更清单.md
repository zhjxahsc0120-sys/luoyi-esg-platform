# ESG Demo V0.4 数据库实施变更清单

**版本：** V0.4 业务确认版（实施前清单）  
**基线：** ESG Demo V0.3：首页一级指标业务事实校正版  
**当前状态：** 只做清单，不执行数据库变更

> 本文件是 V0.4 业务确认后的数据库实施准备清单。当前未执行 `CREATE TABLE`、`ALTER TABLE`、`DROP TABLE`、数据迁移或 Demo 数据修改。

## 一、实施边界

本清单只承接已经进入 V0.4 设计范围的数据库对象和接口影响。任何对象在执行前必须补齐：业务来源、字段确认、主外键关系、状态字典、迁移顺序和回滚方案。

必须遵守：

- 业务事实表与整改闭环表分离。
- `rectification_completed_date` 必须由甲方填报，系统不得自动推算。
- 风险等级沿用项目已有等级，不在迁移脚本中自行新增“一般/重大/超危大”之外的等级。
- 当前 V0.3 表、视图、API 和首页保持可回退，不删除已确认事实链。
- `cl_case` 尚未完成业务确认，本次不纳入可执行清单。

## 二、新增表

### A. 确认进入 V0.4 实施准备的表

| 表名 | 用途 | 关键字段 | 来源/关系 | 实施状态 |
|---|---|---|---|---|
| `biz_labor_payment_record` | S03 农民工工资按时发放率事实 | `project_id`、`period`、`total_workers`、`paid_on_time_rate`、`source_type`、`record_date`、`created_time` | 财务系统或甲方人工填报；不采集个人姓名和工资金额明细 | 待字段评审 |
| `biz_special_plan_approval` | 重大风险源专项方案审批事实 | `risk_point_id`、`plan_name`、`risk_level`、`approval_status`、`approval_date`、`approval_file` | 外键关联 `biz_safety_risk_point`；等级沿用项目既有字典 | 待字段评审 |
| `biz_governance_inspection` | G04 内控检查事实 | `inspection_type`、`inspection_source`、`inspection_date`、`inspection_unit`、`problem_count` | 上级检查、内部检查、审计、纪检等检查记录 | 待字段评审 |
| `biz_governance_rectification` | G04 检查问题整改闭环 | `inspection_id`、`problem_code`、`problem_description`、`rectification_deadline`、`rectification_completed_date`、`verification_date`、`closed_date`、`status` | 关联 `biz_governance_inspection`；后续可扩展到 E02/E03/G03/安全隐患 | 待字段评审 |

### B. 候选对象，不纳入本次可执行清单

| 候选表 | 当前处理 | 原因 |
|---|---|---|
| `cl_case` | 暂不创建 | 业务确认版尚未明确其与检查事实、整改事项、材料和状态历史的关系 |
| 通用 `biz_rectification_case` | 暂不创建 | 当前先以 `biz_governance_rectification` 验证闭环模型；是否抽象成跨域通用表需在 E02/E03/G03 评审后决定 |

`cl_case` 若后续确认，应另行补充：适用域、来源对象、状态历史、整改轮次、证据材料、权限和与现有闭环表的替代/兼容关系；未确认前禁止建表。

### C. 新增表的共同字段要求

除业务字段外，新增表原则上需要评审以下公共字段：

| 字段 | 用途 |
|---|---|
| `id` | 主键 |
| `project_id` | 项目隔离 |
| `source_type` / `source_doc_ref` | 数据来源和资料追溯 |
| `created_time` / `updated_time` | 记录维护时间 |
| `data_status` | 草稿、已审核、已发布等数据状态，沿用项目现有字典 |

公共字段的最终类型和是否必填，要以当前数据库实际表规范为准，不在本清单中直接生成 SQL。

## 三、修改表

### 1. `biz_project_approval`

保留现有审批事实，新增或确认以下字段：

| 字段 | 说明 |
|---|---|
| `approval_type` | 审批类型 |
| `approval_status` | 审批状态，沿用现有状态字典 |
| `approval_date` | 审批完成/批复日期 |

执行前必须先确认该表的真实来源。当前迁移目录中的 V0.3 SQL/种子资料存在对审批事实的引用，但未形成可直接执行的 `biz_project_approval` 建表脚本；因此不能直接执行 `ALTER TABLE`，应先完成表来源和线上结构核对。

### 2. `biz_governance_control_item`（待确认）

如果现场现有数据库已存在该表，建议评审增加或对齐：

- `inspection_id`；
- `problem_code`；
- `control_status`；
- `rectification_id`；
- `source_doc_ref`。

但当前 V0.4 设计稿的正式检查事实表名称是 `biz_governance_inspection`，整改表名称是 `biz_governance_rectification`。在确认两者是否为同一业务对象前，不得同时修改 `biz_governance_control_item` 并新增重复结构。

### 3. `biz_worker_payment_summary`（兼容评审）

V0.3 已存在工资统计事实表名称。V0.4 设计提出 `biz_labor_payment_record`，执行前必须二选一并形成决策：

- 新建 `biz_labor_payment_record`，保留旧表用于 V0.3 回退/历史数据；或
- 将旧表升级为 V0.4 事实表，并通过兼容视图/映射使用业务新名称。

本清单不擅自删除或重命名 `biz_worker_payment_summary`。

### 4. 保留但本次不修改的事实表

| 表 | 处理 |
|---|---|
| `biz_permit` | 保留；本次不删除、不重命名；后续纳入合规审批与施工管控分母规则评审 |
| `biz_safety_risk_point` | 保留；作为 `biz_special_plan_approval.risk_point_id` 的事实来源 |
| `biz_internal_control_issue` | 保留；与新的检查/整改模型做历史映射评审，不直接删除 |
| `esg_demo_indicator_result` | 保留 V0.3 发布结果；V0.4 KPI 视图和 Demo 数据须在指标 key/口径冻结后另行变更 |

## 四、删除项

**无。**

本次不删除、不重命名、不覆盖：

- V0.3 业务事实表；
- 已确认的 KPI 发布结果和视图；
- 既有审批、许可、风险和内控历史资料；
- 旧模板和历史 Demo 数据。

历史结构如需停用，应先迁移、核对、保留回退路径，再另行提交废弃申请；不得在 V0.4 首次实施中直接 `DROP TABLE`。

## 五、模板变化

### 1. 通用整改模板新增/对齐字段

| 模板列 | 数据字段 | 填写责任 | 规则 |
|---|---|---|---|
| 问题编号 | `problem_code` | 检查人员/甲方 | 项目内唯一或按来源唯一 |
| 问题描述 | `problem_description` | 检查人员 | 必填 |
| 整改要求 | `rectification_requirement` | 检查人员/甲方 | 必填 |
| 责任单位 | `responsible_unit` | 甲方确认 | 必填 |
| 发现时间 | `discovered_date` | 检查人员 | 必填 |
| 整改期限 | `rectification_deadline` | 甲方确认 | 必填 |
| **整改完成时间** | **`rectification_completed_date`** | **甲方填报** | **不得由系统自动生成** |
| 复核时间 | `verification_date` | 复核人员 | 复核通过前必填 |
| 关闭时间 | `closed_date` | 关闭确认人员 | 关闭前必填 |
| 当前状态 | `status` | 流程维护 | 只允许项目状态字典 |

导入规则：`整改完成时间`为空时可以保存为未完成，但不能进入“待复核”；系统不得使用导入时间、提交时间或当前日期填充该字段。

### 2. S03 工资支付统计模板

建议模板字段：`项目`、`统计周期`、`统计人数`、`工资按时发放率`、`数据来源`、`填报日期`、`来源资料编号`。

明确不增加：个人姓名、个人工资金额、银行卡号等个人明细字段。

### 3. 专项方案审批模板

建议字段：`风险源编号`、`专项方案名称`、`风险等级`、`审批状态`、`审批日期`、`审批资料编号`、`备注`。风险等级使用项目既有字典，不在模板中创建新的等级值。

## 六、视图、指标和数据迁移影响

以下内容属于后续实施项，本次只列出，不执行：

1. 更新 `v_esg_demo_dashboard_kpis`，承接 S03 新事实来源以及 G01/G02 合并后的分子分母。
2. 重新确认 G01/G02 合并后的正式 KPI key、名称、单位、分母和发布结果。
3. 设计 G04 连续内控合规天数的计算规则，特别是是否因未闭环问题重置。
4. 对现有 `biz_internal_control_issue` 和旧工资统计表进行历史数据映射方案评审。
5. 生成可回滚的迁移脚本、校验 SQL 和 V0.3/V0.4 对照报告。

在上述事项完成前，不得修改当前 MySQL 视图或 `esg_demo_indicator_result`，也不得用前端临时值模拟 V0.4。

## 七、API 影响清单（只设计，不新增）

### 1. 现有接口的未来调整

| 接口 | 未来影响 |
|---|---|
| `GET /api/dashboard/kpis` | S03 名称/来源变化；G01/G02 合并；G04 改为闭环或连续天数表达 |
| `GET /api/dashboard/kpi/{key}` | 详情需返回事实摘要、整改状态和时间链 |
| 现有上传/工作区接口 | 需要识别整改模板字段并保留甲方填报的 `rectification_completed_date` |

以上路径本阶段保持不变，直到 KPI key 和 API 契约单独确认。

### 2. V0.4 候选新增接口

以下是数据库实施后的接口建议，不在本阶段创建：

| 方法 | 路径 | 用途 |
|---|---|---|
| GET | `/api/governance/inspections` | 检查事实列表、按来源/日期筛选 |
| GET | `/api/governance/inspections/{id}` | 检查事实及问题摘要 |
| POST | `/api/governance/inspections` | 导入或登记检查事实 |
| GET | `/api/governance/rectifications` | 整改台账、状态和逾期查询 |
| GET | `/api/governance/rectifications/{id}` | 整改详情及状态轨迹 |
| POST | `/api/governance/rectifications` | 建立整改事项 |
| PATCH | `/api/governance/rectifications/{id}` | 甲方填写整改要求、期限和完成时间 |
| POST | `/api/governance/rectifications/{id}/verify` | 复核通过或退回 |
| POST | `/api/governance/rectifications/{id}/close` | 正式关闭 |
| GET | `/api/safety/special-plan-approvals` | 专项方案审批列表 |
| GET | `/api/social/labor-payment` | S03 工资支付统计 |
| POST | `/api/social/labor-payment/import` | 导入工资支付统计模板 |

接口实现必须原样返回甲方填报的 `rectification_completed_date`；该字段为空时返回空值和明确状态，不得返回系统生成日期。

## 八、实施顺序与闸门

```text
V0.4 设计确认
        ↓
数据库变更清单（本文）
        ↓
表来源/字段/字典/关系核对
        ↓
Codex 执行数据库变更
        ↓
API 调整与接口验收
        ↓
Cursor 页面和模板调整
```

数据库执行前必须完成：

- `cl_case` 是否纳入的明确结论；
- `biz_worker_payment_summary` 与 `biz_labor_payment_record` 的取舍；
- `biz_project_approval`、`biz_permit`、`biz_safety_risk_point` 的真实表结构核对；
- `biz_governance_control_item` 是否与新检查事实表重复；
- 状态字典、风险等级、主外键和数据来源字段确认；
- V0.3 回退方案和验证 SQL；
- 新增整改表的权限、审计和甲方填报责任确认。

## 九、当前结论

- **新增表：** 4 张进入实施准备；`cl_case` 和通用 `biz_rectification_case` 暂不纳入。
- **修改表：** `biz_project_approval`、可能的 `biz_governance_control_item`，以及工资统计表的兼容方案待核对。
- **删除项：** 无。
- **模板：** 新增“整改完成时间”，由甲方填报，系统不得自动推算。
- **API：** 现有接口暂不改；列出治理整改、专项方案和工资统计的候选新增接口。
- **实施状态：** 仅完成清单，未执行数据库、API 或页面变更。
