# ESG V0.4 数据库执行批准版参数清单

**版本：** V1.0  
**工作区：** `C:\ESG_Project`  
**数据库：** MySQL 8.4.9，`127.0.0.1:3307/luoyi_esg`  
**数据库：** `luoyi_esg`  
**当前基线：** ESG Demo V0.3：首页一级指标业务事实校正版  
**参数状态：** 已冻结，等待人工批准执行

> 本文件只冻结数据库执行参数，不执行 SQL，不修改数据库、API 或前端。实际执行必须以人工批准后的 DDL 和备份结果为准。

## 一、执行边界

本次批准版只允许实施以下范围：

1. 通用整改闭环字段和 G04 域扩展；
2. S03 工资统计表的兼容字段；
3. 审批/许可证项目归属字段；
4. 唯一新增表 `special_plan_approval`；
5. 必要索引和确认过的外键。

禁止：

- 新建 `biz_project_approval`、`biz_permit`、`biz_labor_payment_record`、`biz_governance_rectification`、`cl_case`；
- 删除或重命名 V0.3 表、字段、视图；
- 修改 `payment_rate` 的字段名或 V0.3 读取语义；
- 用系统时间生成整改完成时间；
- 在备份和执行审批完成前运行任何 DDL。

## 二、冻结参数总表

| 类别 | 冻结决定 |
|---|---|
| 唯一新增表 | `special_plan_approval` |
| 通用闭环 | `e_closure_case` + `e_rectification_task` + `e_case_status_history` + `e_case_evidence` + `e_case_rectification_link` |
| G04 | 接入通用闭环，域值为 `G04_GOVERNANCE` |
| 整改完成日期 | `e_rectification_task.rectification_completed_date DATE NULL` |
| 整改完成填报人 | 增加 `e_rectification_task.rectification_completed_by BIGINT NULL` |
| 项目归属 | 历史数据允许 NULL；新业务数据由 API 强制填写 |
| S03 | 复用 `biz_worker_payment_summary` |
| S03 业务映射 | `payment_rate` → 农民工工资按时发放率 |
| S03 计算 | 按 `worker_count` 人数加权 |
| G01/G02 事实来源 | `compliance_procedure` + `permit_record` + `special_plan_approval` |
| G01/G02 去重 | 有明确业务键才跨表去重；无明确关系不模糊合并 |
| G01/G02 完成 | 按统一状态字典分别判断审批完成、许可证有效、专项方案批准 |
| 执行状态 | 参数冻结，等待人工批准；尚未执行 |

## 三、`special_plan_approval` 冻结参数

### 1. 表名

唯一正式表名：

```text
special_plan_approval
```

不采用 `biz_special_plan_approval`，避免在现有 `compliance_procedure`、`permit_record`、`safety_risk_point` 事实层之外再形成重复命名层。

### 2. 字段参数

| 字段 | 类型 | NULL | 冻结说明 |
|---|---|---:|---|
| `id` | `BIGINT` | 否 | 自增主键 |
| `project_id` | `BIGINT` | 否 | 新增事实必须有项目归属；暂不绑定未知项目主表 |
| `risk_point_id` | `BIGINT` | 否 | 关联 `safety_risk_point.id` |
| `plan_code` | `VARCHAR(80)` | 否 | 项目内专项方案编号 |
| `plan_name` | `VARCHAR(255)` | 否 | 专项方案名称 |
| `risk_level` | `VARCHAR(50)` | 否 | 沿用项目已有风险等级，不新增等级 |
| `approval_status` | `VARCHAR(40)` | 否 | 沿用现有审批状态字典 |
| `approval_date` | `DATE` | 是 | 审批完成日期 |
| `approval_file_id` | `BIGINT` | 是 | 关联 `file_asset.id` |
| `source_doc_ref` | `VARCHAR(255)` | 是 | 来源资料编号 |
| `data_nature` | `VARCHAR(20)` | 否 | `demo/formal/platform_calc` |
| `is_demo` | `TINYINT(1)` | 否 | Demo 标识 |
| `created_at` | `DATETIME` | 否 | 技术创建时间 |
| `updated_at` | `DATETIME` | 否 | 技术更新时间 |

### 3. 外键策略

| 关系 | 决策 |
|---|---|
| `risk_point_id → safety_risk_point.id` | 建立物理外键，`ON DELETE RESTRICT`、`ON UPDATE RESTRICT` |
| `approval_file_id → file_asset.id` | 建立物理外键，`ON DELETE RESTRICT`、`ON UPDATE RESTRICT` |
| `project_id` | 暂不建立物理外键；当前未确认统一项目主表，由 API/数据校验保证 |

执行前必须再次核对三对字段类型和字符集；类型不一致时先修正关系方案，不强行建外键。

### 4. 索引策略

| 索引 | 字段 | 目的 |
|---|---|---|
| PRIMARY | `id` | 主键 |
| UNIQUE | `project_id, plan_code` | 项目内方案编号唯一 |
| `idx_special_plan_risk_point` | `risk_point_id` | 风险源关联查询 |
| `idx_special_plan_status` | `project_id, approval_status` | 项目审批状态统计 |
| `idx_special_plan_date` | `project_id, approval_date` | 项目审批日期查询 |
| `idx_special_plan_level` | `project_id, risk_level` | 项目风险等级筛选 |

## 四、整改闭环冻结参数

### 1. 最终模型

```text
e_closure_case
    ├── e_rectification_task
    ├── e_case_status_history
    ├── e_case_evidence
    └── e_case_rectification_link
```

职责冻结：

- `e_closure_case`：案件主状态、来源、项目、责任、期限和关闭信息；
- `e_rectification_task`：具体整改轮次和甲方完成填报；
- `e_case_status_history`：全部状态变化和操作审计；
- `e_case_evidence`：通知、整改材料、复核意见、关闭资料；
- `e_case_rectification_link`：案件与多轮整改任务关联。

不再新增 `cl_case` 或 `biz_governance_rectification`。

### 2. `rectification_completed_date`

| 参数 | 冻结值 |
|---|---|
| 存放表 | `e_rectification_task` |
| 字段 | `rectification_completed_date` |
| 类型 | `DATE` |
| NULL | 允许 |
| 数据来源 | 甲方填报 |
| 自动生成 | 禁止 |
| 关闭时间替代 | 禁止 |
| 提交复核前 | 必须填写 |
| API 返回 | 原样返回；NULL 返回“待甲方填报” |
| 历史无日期 | 保持 NULL，不补造 |

### 3. `rectification_completed_by`

最终决定：**增加。**

| 参数 | 冻结值 |
|---|---|
| 字段 | `rectification_completed_by` |
| 类型 | `BIGINT` |
| NULL | 允许；未填完成日期时可为空 |
| 来源 | 甲方登录用户 `user_account.id` |
| 填写规则 | 填写 `rectification_completed_date` 时同步保存 |
| 修改规则 | 变更完成日期必须产生审计记录 |
| 外键 | `→ user_account.id`，`ON DELETE RESTRICT`、`ON UPDATE RESTRICT` |

字段成对校验：

```text
rectification_completed_date IS NULL
    → rectification_completed_by 可以 NULL

rectification_completed_date IS NOT NULL
    → rectification_completed_by 必须非 NULL
```

现有 `updated_by` 不替代该字段；`updated_by` 记录最后修改人，`rectification_completed_by` 记录完成事实的责任人。

### 4. G04 域参数

首期启用：

```text
G04_GOVERNANCE
```

同一模型预留但本期不导入：

```text
S02_SAFETY
G03_DESIGN_CHANGE
```

G04 映射入口：

```text
biz_internal_control_issue
        ↓
e_closure_case(case_domain='G04_GOVERNANCE')
        ↓
e_rectification_task
        ↓
e_case_status_history / e_case_evidence
        ↓
CLOSED
```

历史 `CLOSED` 记录没有完成日期时，保留 `closed_at`，但 `rectification_completed_date` 仍为 NULL，不用关闭日期冒充完成日期。

## 五、项目归属冻结参数

### 1. `e_closure_case.project_id`

| 场景 | 规则 |
|---|---|
| 字段 | `project_id BIGINT` |
| 历史数据 | 允许 NULL |
| 历史回填 | 只有来源记录明确归属项目时才回填 |
| 无可信来源 | 保持 NULL，不猜测 |
| 新建案件 | API 强制非 NULL |
| KPI 统计 | `project_id` 不明确的案件不进入项目 KPI |
| 外键 | 暂不绑定未知项目主表 |

### 2. `compliance_procedure.project_id`

- 增加 `BIGINT NULL`；
- 历史记录允许 NULL；
- 有可信文档/项目关系时回填；
- 新增或编辑正式事实时 API 强制填写；
- NULL 记录保留，但不进入项目级 G01/G02 分母。

### 3. `permit_record.project_id`

- 增加 `BIGINT NULL`；
- 历史记录允许 NULL；
- 不以责任部门、许可证名称或日期范围猜测项目；
- 新增正式许可证时 API 强制填写；
- NULL 记录保留，但不进入项目级 G01/G02 分母。

### 4. `special_plan_approval.project_id`

新表不承载历史兼容数据，直接冻结为 `NOT NULL`。风险源 `risk_point_id` 必须经过项目归属一致性校验。

## 六、S03 冻结参数

### 1. 事实表

继续复用：

```text
biz_worker_payment_summary
```

不新建 `biz_labor_payment_record`。

### 2. 字段映射

| V0.4 语义 | 真实字段 | 冻结规则 |
|---|---|---|
| 统计周期 | `period_start` + `period_end` | 保留日期范围 |
| 统计人数 | `worker_count` | 作为加权分母 |
| 工资按时发放率 | `payment_rate` | 保留字段名和原值 |
| 数据来源 | `source_type` | 新增，财务系统/人工填报 |
| 记录日期 | `record_date` | 新增，甲方/来源系统填报 |
| 技术创建时间 | `created_at` | 新增，不能代替 `record_date` |
| 来源资料 | `source_doc_ref` | 保留 |

### 3. 指标计算

冻结为人数加权：

```text
农民工工资按时发放率
= SUM(worker_count × payment_rate)
  ÷ SUM(worker_count)
```

规则：

- `worker_count <= 0` 不进入分母；
- 无有效人数返回 NULL/待填报，不返回 0%；
- 不采集、不新增个人姓名和工资金额明细；
- 不重命名、不删除、不改变 `payment_rate`；
- V0.3 首页/API 迁移前保持原读取逻辑。

## 七、G01/G02 冻结参数

### 1. 三类事实来源

```text
compliance_procedure
permit_record
special_plan_approval
```

对应业务：

- `compliance_procedure`：审批/报批报建/手续过程；
- `permit_record`：许可证事实和有效期；
- `special_plan_approval`：风险专项方案审批。

### 2. 统一控制事项键

优先级冻结如下：

1. 有正式业务编号时使用业务编号：许可证号、专项方案编号、审批事项编号；
2. 无正式编号时使用：`project_id + source_type + source_table + source_record_id`；
3. 无项目归属的记录不得进入项目级控制事项集合；
4. 不以名称、责任部门、日期做模糊去重。

### 3. 去重规则

- 同一来源表同一记录只计一次；
- 跨表仅在存在相同正式业务编号或人工批准的明确映射时合并；
- 审批流程和许可证属于不同控制阶段时，默认分别计数；
- 专项方案审批不与风险源本身合并，风险源是事实，方案是审批事实；
- 无明确关系的跨表记录不自动合并，宁可保留两项并进入人工对账。

### 4. 完成状态

| 来源 | 完成条件 | 不完成条件 |
|---|---|---|
| `compliance_procedure` | 规范化状态为已批准/已完成，且有完成/审批日期 | 待办理、待审查、资料补正、逾期未办等 |
| `permit_record` | 规范化状态为有效，且统计日未超过有效期 | 临期、过期、失效、注销 |
| `special_plan_approval` | `approval_status` 为已批准/已完成，且 `approval_date` 非空 | 待审、退回、未提交、逾期 |

原始中文状态不在 API 或前端中硬编码判断，先通过状态字典规范化。

### 5. 指标表达

```text
合规审批与施工管控完成率
= 已完成/有效控制事项数
  ÷ 纳入管理的控制事项总数
  × 100%
```

首页不展示“事项数量”作为问题数量；使用完成率或 `X/X 100%` 状态表达。

## 八、执行顺序冻结

人工批准后，严格按以下顺序：

1. 数据库备份：表结构、数据、视图、V0.3 KPI 快照；
2. 新增字段；
3. 新增 `special_plan_approval`；
4. 结构验证；
5. Demo 数据验证；
6. 增加 G04 域约束和必要约束；
7. 建立索引和确认过的外键；
8. G04/S03/G01/G02 数据映射与业务验证；
9. API 调整；
10. Cursor 页面调整。

任何一步验证失败，停止后续步骤并进入回滚评估，不跳步继续。

## 九、执行前最后审批项

以下内容是唯一仍需人工批准的事项，不属于参数未决：

- [ ] 批准执行 `special_plan_approval` 建表 DDL；
- [ ] 批准整改日期和填报人字段 DDL；
- [ ] 批准 G04 域约束扩展；
- [ ] 批准历史项目归属 NULL 规则；
- [ ] 批准 S03 人数加权计算；
- [ ] 批准 G01/G02 三类事实来源、去重和完成状态；
- [ ] 批准备份、执行窗口和回滚负责人；
- [ ] 批准数据库变更开始。

**最终状态：** V0.4 数据库执行参数已冻结；当前不执行 SQL，等待人工批准后再进入“备份 → DDL → 验证”阶段。
