# ESG V0.4 最终数据模型决策报告

**版本：** V1.0 业务确认版  
**基线：** ESG Demo V0.3：首页一级指标业务事实校正版  
**真实数据库：** MySQL 8.4.9，`127.0.0.1:3307/luoyi_esg`  
**决策状态：** 已形成实施决策，等待数据库变更审批  
**本次操作：** 只读分析和文档输出，未修改数据库

## 一、最终决策摘要

| 决策项 | 最终决定 |
|---|---|
| ESG 通用整改底座 | 采用 `e_closure_case` + `e_rectification_task` + `e_case_status_history` + `e_case_evidence`，并继续使用 `e_case_rectification_link` |
| 首期业务域 | E01、E02、E03、G04；S02、G03 预留同一底座，待事实来源映射后启用 |
| G04 | 纳入 `e_closure_case` 的通用闭环域，增加 G04 域值 |
| 整改完成时间 | 放在 `e_rectification_task.rectification_completed_date`，由甲方填报，系统不得自动生成 |
| S03 工资支付 | 复用 `biz_worker_payment_summary`，不新建 `biz_labor_payment_record` |
| G01/G02 | 复用 `compliance_procedure` + `permit_record`；不新建 `biz_project_approval`、`biz_permit` |
| 风险专项方案 | 当前无现成专项方案表；新增 `special_plan_approval`，不使用 `biz_special_plan_approval` 重复命名 |
| `cl_case` | 不新建；已有 `e_closure_case` 承担同类职责 |
| 删除项 | 无；V0.3 旧表和历史事实全部保留 |

## 二、通用整改闭环最终模型

### 1. 采用的表组

正式采用以下表组作为 ESG 通用闭环基础：

```text
e_closure_case
    ├── e_case_status_history
    ├── e_case_evidence
    ├── e_case_rectification_link
    └── e_rectification_task
```

职责划分：

| 表 | 最终职责 |
|---|---|
| `e_closure_case` | 一个可追溯的业务问题/闭环案件，保存来源、责任、期限、当前状态和关闭信息 |
| `e_rectification_task` | 某一轮具体整改任务，保存责任单位、整改期限和甲方填报的完成日期 |
| `e_case_status_history` | 所有状态转移和操作轨迹，作为流程审计事实 |
| `e_case_evidence` | 通知单、原始记录、整改材料、复核意见、关闭资料等证据 |
| `e_case_rectification_link` | 案件与整改任务的关联，支持多轮整改 |

`biz_internal_control_issue` 和 `rectification_record` 不再作为 V0.4 新闭环主表；它们保留为 V0.3/历史事实和兼容映射来源。

### 2. 支持的业务域

#### V0.4 首期启用

| 域代码 | 业务域 | 事实来源/关联 |
|---|---|---|
| `E01_EXCEED` | 环境监测异常/超标 | 现有 E01 事实和 E01 闭环表 |
| `E02_ENV` | 环保问题 | `env_issue_record` 或现有 E02 来源 |
| `E03_WATER` | 水保问题 | `water_protection_issue` 或现有 E03 来源 |
| `G04_GOVERNANCE` | 内控检查与整改闭环 | `biz_internal_control_issue` 映射为检查/案件来源 |

#### 同一模型预留

| 域代码 | 业务域 | 状态 |
|---|---|---|
| `S02_SAFETY` | 安全风险/安全隐患整改 | 复用同一模型，待事实源和责任流程确认后启用 |
| `G03_DESIGN_CHANGE` | 设计变更问题整改 | 复用同一模型，待设计变更闭环规则确认后启用 |

S03 工资支付是周期性业务事实，不默认进入整改闭环；只有出现工资支付争议或专项整改时，才通过独立案件来源进入同一闭环底座。

### 3. `rectification_completed_date` 最终放置位置

最终字段位置：

```text
e_rectification_task.rectification_completed_date
```

原因：整改完成是某一轮具体整改任务的事实，不是案件本身的固定属性。一个 `e_closure_case` 可能因复核退回产生多轮 `e_rectification_task`，每轮必须独立保存甲方填报的完成日期。

字段规则：

- 类型建议：`DATE NULL`；
- 来源：甲方填报；
- `task_status` 进入 `SUBMITTED` 或案件进入 `PENDING_REVIEW` 前必须有值；
- 允许复核退回后产生新的整改轮次，不覆盖上一轮完成日期；
- 系统不得用上传时间、提交时间、状态切换时间或当前日期自动填充；
- API 必须原样返回该字段，空值显示为“待甲方填报”。

复核时间使用 `e_case_status_history.action_at` 记录进入复核通过/待关闭阶段的时间；正式关闭时间继续使用 `e_closure_case.closed_at`，避免重复保存同一过程事实。

### 4. G04 域需要的结构扩展

现有 `e_closure_case.case_domain` 检查约束只允许 E01/E02/E03。实施时需将 `G04_GOVERNANCE` 纳入域值；S02/G03 是否同时加入约束，建议在同一迁移中加入预留值，但未启用前不导入业务数据。

不新增 `biz_governance_rectification`，不新增 `cl_case`。

### 5. 状态统一规则

以 `e_closure_case.current_status` 为案件主状态，以 `e_case_status_history` 为审计依据；`e_rectification_task.task_status` 只表示当前整改任务状态，不与案件状态并列竞争。

| 业务状态 | 案件状态 | 整改任务状态建议 |
|---|---|---|
| 待整改 | `PENDING_RECTIFICATION` | `PENDING` |
| 整改中 | `RECTIFYING` | `IN_PROGRESS` |
| 待复核 | `PENDING_REVIEW` | `SUBMITTED` |
| 复核通过/待关闭 | `PENDING_CLOSURE` | `REVIEWED` |
| 已关闭 | `CLOSED` | `COMPLETED` |

复核不通过时回到 `RECTIFYING`，新增状态历史记录，不删除或覆盖上一轮证据。

## 三、S03 工资支付最终决策

### 1. 复用结论

复用真实存在的 `biz_worker_payment_summary`，不新建 `biz_labor_payment_record`。

当前表有 2 条 Demo 记录，包含 `worker_count`、`payment_rate`、统计周期、支付状态和来源资料，已经能够支撑 V0.3/V0.4 的 Demo 展示。

### 2. 字段映射

| V0.4 业务字段 | 现有字段 | 决策 |
|---|---|---|
| `project_id` | `project_id` | 直接复用 |
| `period` | `period_start` + `period_end` | 保留日期范围，不改成单一字符串 |
| `total_workers` | `worker_count` | 直接映射 |
| `paid_on_time_rate` | `payment_rate` | 语义映射，不重命名，避免破坏 V0.3 |
| `source_type` | 当前无独立字段 | 增加字段，或通过 `source_doc_ref` 关联来源注册表；最终实施优先增加明确来源类型 |
| `record_date` | 当前无独立字段 | 增加填报/记录日期字段 |
| `created_time` | 当前无独立字段 | 可用新增 `created_at`；不能把 `updated_at` 当创建时间 |
| 来源资料 | `source_doc_ref` | 直接复用 |
| 统计有效性 | `is_deleted` | 直接复用 |

现有 `payable_amount`、`paid_amount`、`overdue_amount` 等字段保留，用于历史和权限受控的事实追溯；S03 首页和普通 API 不返回工资金额明细。

### 3. 指标计算逻辑

以项目和统计周期为粒度：

```text
工资按时发放率
= SUM(worker_count × payment_rate) / SUM(worker_count)
```

规则：

- 只统计 `is_deleted = 0` 且已审核/发布的记录；
- `worker_count <= 0` 的记录不进入分母；
- 无有效人数时返回空值和“待填报”，不返回 0%；
- 百分比保留两位计算精度，首页按业务展示规则显示；
- 不采集、不展示个人姓名、个人工资金额明细。

当前两条 Demo 记录是 100.00% 和 98.50%，因此 V0.4 必须先确认页面展示是按标段分别展示还是按人数加权形成项目总率，不能由前端自行取第一条记录。

## 四、G01/G02 合规审批与施工管控最终决策

### 1. 事实来源

采用：

```text
compliance_procedure
permit_record
```

不新建：

```text
biz_project_approval
biz_permit
```

当前真实数据量为 `compliance_procedure` 7 条、`permit_record` 5 条。

### 2. 事实角色

| 来源表 | 事实角色 |
|---|---|
| `compliance_procedure` | 报批报建、专项审批、手续办理过程 |
| `permit_record` | 许可证、许可类型、证号、有效期和责任部门 |
| `special_plan_approval` | 风险专项方案审批，作为新增的第三类审批事实 |

### 3. 合并指标计算逻辑

指标名称：**合规审批与施工管控完成率**。

逻辑对象不是三张表行数的简单相加，而是先构造统一控制事项集合：

```text
control_item_key
= 来源类型 + 来源表 + 来源记录ID
```

计算：

```text
合规审批与施工管控完成率
= 已完成/有效控制事项数 ÷ 纳入管理的控制事项总数 × 100%
```

纳入规则：

1. `compliance_procedure` 中属于当前项目、当前统计周期且需要管理的审批/手续事项进入分母。
2. `permit_record` 中属于当前项目、处于有效管理范围的许可证进入分母；临期/过期不等于不存在，而是未完成或风险状态。
3. `special_plan_approval` 中与已纳入风险源关联且要求审批的专项方案进入分母。
4. 同一业务事项跨表出现时，使用业务编号、许可证号、方案编号或已确认的来源关系去重。
5. 项目归属必须明确。当前 `compliance_procedure`、`permit_record`、`safety_risk_point` 的结构未直接显示 `project_id`，正式多项目实施前必须补齐项目归属或通过可信文档关系解析，不能按全库行数计算。

完成判定：

- 审批事项：状态为已批准/已完成且具备完成日期或审批日期；
- 许可证：状态有效且统计日不超过有效期；
- 专项方案：审批状态完成且存在审批日期；
- 具体状态值必须建立数据字典映射，不能凭中文显示文本临时判断。

## 五、风险专项方案最终决策

### 1. 现状

只读核查未发现专项方案审批相关表。现有 `safety_risk_point` 有 10 条风险源，具备 `risk_level`、`control_status`、`location` 等字段，但没有专项方案名称、审批状态或审批日期。

### 2. 新增表决策

新增一张：

```text
special_plan_approval
```

最终采用该名称而不是 `biz_special_plan_approval`，原因是其事实来源同族表实际使用 `compliance_procedure`、`permit_record`、`safety_risk_point` 等名称；避免继续扩展一个与现有实际命名不一致的 `biz_*` 重复层。

建议字段：

| 字段 | 说明 |
|---|---|
| `id` | 主键 |
| `project_id` | 项目归属，正式多项目必填 |
| `risk_point_id` | 关联 `safety_risk_point.id` |
| `plan_code` | 专项方案编号 |
| `plan_name` | 专项方案名称 |
| `risk_level` | 沿用 `safety_risk_point.risk_level` 或项目设计等级 |
| `approval_status` | 审批状态，使用项目已有状态字典 |
| `approval_date` | 审批日期 |
| `approval_file_id` | 关联资料/文件，不在表内保存大文件 |
| `source_doc_ref` | 来源资料引用 |
| `created_at` / `updated_at` | 维护时间 |
| `data_nature` / `is_demo` | Demo/正式边界 |

该表是唯一决定新增的 V0.4 业务事实表。它不替代风险源表，也不承担整改状态；专项方案未通过或资料缺失时，再通过通用闭环模型建立整改案件。

## 六、最终表清单

### 1. 复用表

| 表 | 最终用途 |
|---|---|
| `e_closure_case` | 通用案件/问题闭环 |
| `e_rectification_task` | 多轮整改任务 |
| `e_case_status_history` | 状态审计 |
| `e_case_evidence` | 整改和复核证据 |
| `e_case_rectification_link` | 案件与整改任务关系 |
| `biz_worker_payment_summary` | S03 工资支付事实 |
| `compliance_procedure` | G01/G02 审批事实 |
| `permit_record` | G01/G02 许可事实 |
| `safety_risk_point` | 风险事实及专项方案关联目标 |
| `biz_internal_control_issue` | G04 历史/当前内控问题来源 |
| `rectification_record` | 历史整改兼容来源，不作为新主模型 |

### 2. 新增表

| 表 | 是否新增 | 用途 |
|---|---:|---|
| `special_plan_approval` | 是 | 风险专项方案审批事实 |

### 3. 不新增的重复表

| 设计名称 | 最终处理 |
|---|---|
| `biz_labor_payment_record` | 不新增，复用 `biz_worker_payment_summary` |
| `biz_project_approval` | 不新增，复用 `compliance_procedure` |
| `biz_permit` | 不新增，复用 `permit_record` |
| `biz_governance_rectification` | 不新增，复用通用 E 闭环模型 |
| `cl_case` | 不新增，复用 `e_closure_case` |

### 4. 删除项

无。旧表、旧视图、旧 Demo 数据和历史闭环模型均保留。

## 七、需要修改的字段/约束

本节是未来实施清单，不是本次执行记录。

### 必要修改

1. `e_rectification_task` 增加 `rectification_completed_date DATE NULL`。
2. `e_closure_case.case_domain` 允许 `G04_GOVERNANCE`；同时评估预留 S02/G03 域值。
3. `e_closure_case` 增加 `project_id`（新数据必填；历史数据先回填后收紧约束），或提交等价的可信项目归属方案。
4. `biz_worker_payment_summary` 增加 `source_type`、`record_date`，并补齐创建时间字段；不重命名 `payment_rate`。
5. 审批/许可事实必须补齐项目归属：优先在 `compliance_procedure`、`permit_record` 增加 `project_id`，否则必须建立可靠的文档-项目关系映射。

### 不修改/不删除

- 不删除 `payable_amount`、`paid_amount` 等历史字段；
- 不把 `closed_at` 改名为 `rectification_completed_date`；
- 不用系统时间填充甲方完成时间；
- 不改变 V0.3 `esg_demo_indicator_result` 和 `v_esg_demo_dashboard_kpis`，直到 V0.4 KPI key 和首页口径单独确认。

## 八、数据迁移方案

### 阶段 1：备份和基线锁定

1. 保存当前库 DDL、视图定义、行数快照和 V0.3 KPI 返回快照。
2. 标记迁移批次和 `data_nature`，保持 Demo/正式数据隔离。
3. 暂停 V0.4 写入，保证迁移期间事实不漂移。

### 阶段 2：先扩展闭环底座

1. 增加 `e_rectification_task.rectification_completed_date`。
2. 扩展 `e_closure_case` 域值和项目归属。
3. 建立 G04 旧内控问题到 `e_closure_case` 的映射规则。
4. 为每条案件创建对应的整改任务和状态历史映射；证据通过 `e_case_evidence` 关联，不复制文件内容。
5. 不删除 `biz_internal_control_issue`、`rectification_record` 或 E 组旧数据。

### 阶段 3：接入 S03

1. 保留 `biz_worker_payment_summary` 现有字段和 V0.3 数据。
2. 补齐来源类型、记录日期和创建时间。
3. 以项目+统计周期+标段建立唯一性检查。
4. 建立 V0.4 语义映射：`payment_rate` → `paid_on_time_rate`。
5. API/视图先完成对照验证，再切换首页或详情使用新语义。

### 阶段 4：接入 G01/G02

1. 为 `compliance_procedure`、`permit_record` 补齐项目归属或完成文档关系映射。
2. 建立审批、许可证、专项方案的统一控制事项键。
3. 新增 `special_plan_approval` 并关联风险源。
4. 对重复审批/许可记录进行只读对账，确认分母。
5. 形成 G01/G02 合并指标的 SQL 和 API 变更单后再实施。

### 阶段 5：指标与接口切换

数据库事实验证通过后，才允许：

1. 更新 KPI 计算视图；
2. 更新 API 详情和整改接口；
3. 更新模板导入；
4. 最后由 Cursor 调整页面展示。

## 九、回滚方案

### 回滚原则

- 不删除 V0.3 表和字段；
- 新增字段保留但停止读取，不采用破坏性 `DROP COLUMN` 回滚；
- 新增表只在没有业务引用和数据写入时才允许删除，否则标记停用；
- V0.3 KPI 视图和 API 响应必须可恢复。

### 回滚步骤

1. 停止 V0.4 新接口和新写入。
2. 将首页 KPI 读取恢复到 V0.3 `v_esg_demo_dashboard_kpis` 和原 API 契约。
3. 停止读取 G04 新案件映射，保留已写入的历史映射数据。
4. 停止使用 `special_plan_approval`，保留表和数据以便追溯。
5. S03 恢复使用 V0.3 `biz_worker_payment_summary.payment_rate` 读取路径。
6. 通过迁移前快照核对 KPI、行数、状态和关键外键。

## 十、最终实施闸门

数据库变更开始前必须再次确认：

- `rectification_completed_date` 的甲方填报权限和空值规则；
- G04 域值是否加入当前迁移，S02/G03 是否只预留；
- `e_closure_case.project_id` 的历史回填来源；
- S03 是按标段展示还是按人数加权展示项目总率；
- G01/G02 的项目归属、去重键和完成状态字典；
- `special_plan_approval` 的最终字段和风险等级来源；
- V0.3 回退快照和验证 SQL；
- 数据库变更审批人和执行窗口。

**最终结论：** V0.4 不再按初稿直接造 `biz_project_approval`、`cl_case`、`biz_governance_rectification` 等重复表。正式实施路线是：以现有 E 闭环模型为 ESG 通用底座，扩展 G04；复用现有 S03、审批、许可和风险事实表；仅新增专项方案审批事实表；完成必要字段和项目归属补齐后，再进入数据库变更阶段。
