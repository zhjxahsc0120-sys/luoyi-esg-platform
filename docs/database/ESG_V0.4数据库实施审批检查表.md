# ESG V0.4 数据库实施审批检查表

**版本：** V1.0  
**工作区：** `C:\ESG_Project`  
**用途：** 数据库实施前人工审批记录  
**当前阶段：** 仅审批准备，不执行数据库修改

> 本检查表生成时未执行 `CREATE TABLE`、`ALTER TABLE`、`INSERT`、`UPDATE`、`DELETE`、数据迁移、API 修改或前端修改。

## 一、审批结论

### 是否建议执行数据库变更

- [ ] 可以执行
- [x] 需要补充确认
- [ ] 暂不执行

**当前建议：需要补充确认。** 主要原因是项目归属字段的历史回填、G01/G02 统计范围、`rectification_completed_by` 是否纳入、`special_plan_approval` 外键策略仍需人工确认。

### 人工审批记录

| 项目 | 内容 |
|---|---|
| 审批人 | 待填写 |
| 审批日期 | 待填写 |
| 审批结论 | 待填写 |
| 补充意见 | 待填写 |
| 允许执行窗口 | 待填写 |
| 回滚负责人 | 待填写 |

## 二、实施基线确认

| 项目 | 已确认值 | 状态 |
|---|---|---|
| 工作区 | `C:\ESG_Project` | ✅ 已确认 |
| 数据库类型 | MySQL 8.4.9 | ✅ 已只读核查 |
| 数据库实例 | `127.0.0.1:3307` | ✅ 已只读核查 |
| 数据库 | `luoyi_esg` | ✅ 已只读核查 |
| 当前基线 | ESG Demo V0.3 | ✅ 已冻结 |
| 当前 API | V0.3 现有 API 契约 | ✅ 保持不变 |
| 当前首页 | V0.3 首页一级指标业务事实校正版 | ✅ 保持不变 |

## 三、数据库变更确认

### 1. 唯一新增表：`special_plan_approval`

**当前真实状态：** 数据库中不存在，属于待实施新增对象。

**审批状态：**

- [ ] 已确认
- [x] 待确认

#### 用途确认

- [ ] 保存风险源对应的专项方案审批事实
- [ ] 不承担整改状态
- [ ] 不替代 `safety_risk_point`
- [ ] 作为 G01/G02 合规审批与施工管控的第三类事实来源

#### 字段确认

| 字段 | 设计用途 | 确认 |
|---|---|---|
| `id` | 主键 | [ ] |
| `project_id` | 项目归属 | [ ] |
| `risk_point_id` | 关联 `safety_risk_point.id` | [ ] |
| `plan_code` | 专项方案编号 | [ ] |
| `plan_name` | 专项方案名称 | [ ] |
| `risk_level` | 沿用项目已有等级 | [ ] |
| `approval_status` | 沿用项目审批状态字典 | [ ] |
| `approval_date` | 审批完成日期 | [ ] |
| `approval_file_id` | 关联资料，可空 | [ ] |
| `source_doc_ref` | 来源资料编号 | [ ] |
| `data_nature` / `is_demo` | Demo/正式边界 | [ ] |
| `created_at` / `updated_at` | 维护时间 | [ ] |

#### 关联和索引确认

- [ ] `risk_point_id → safety_risk_point.id` 建立物理外键
- [ ] `approval_file_id → file_asset.id` 建立物理外键
- [ ] 文件外键类型和文件生命周期已核对
- [ ] `(project_id, plan_code)` 唯一索引确认
- [ ] `risk_point_id` 索引确认
- [ ] `approval_status`、`approval_date` 查询索引确认
- [ ] `project_id` 暂不设置外键，待项目主数据确定

**人工决策记录：**

```text
最终表名：____________________
外键策略：____________________
审批人：______________________
日期：________________________
```

### 2. `e_rectification_task` 字段新增确认

#### `rectification_completed_date`

| 检查项 | 设计结论 | 状态 |
|---|---|---|
| 字段类型 | `DATE` | ✅ 已设计 |
| 是否允许 NULL | 允许 NULL；提交复核前必须有值 | ✅ 已设计 |
| 来源 | 甲方填报 | ✅ 已确认 |
| 系统自动生成 | 禁止 | ✅ 已确认 |
| 是否可用关闭时间代替 | 禁止 | ✅ 已确认 |
| API 返回 | 原样返回；空值显示“待甲方填报” | ✅ 已设计 |
| 复核退回 | 新轮次记录，不覆盖旧完成日期 | ✅ 已设计 |

审批确认：

- [ ] 同意增加 `rectification_completed_date DATE NULL`
- [ ] 同意提交 `PENDING_REVIEW` 前强制校验非空
- [ ] 同意历史迁移记录允许 NULL，不伪造历史完成日期

#### `rectification_completed_by` 评估

**建议：** V0.4 正式实施推荐增加 `rectification_completed_by BIGINT NULL`，用于记录完成日期的填报人；但如果现有 `updated_by` 加审计日志已经能够证明“谁修改了该字段”，可以暂不增加，避免重复审计字段。

- [ ] 增加 `rectification_completed_by`
- [ ] 不增加，使用现有 `updated_by + audit_log` 追踪
- [ ] 先验证现有审计能力后决定

**当前建议：先验证审计能力，再决定；不得因此延后 `rectification_completed_date`。**

### 3. `e_closure_case` 确认

#### G04 域

现有 `case_domain` 约束目前只允许：

```text
E01_EXCEED、E02_ENV、E03_WATER
```

V0.4 计划增加：

```text
G04_GOVERNANCE
```

预留但本期不导入数据：

```text
S02_SAFETY、G03_DESIGN_CHANGE
```

确认：

- [ ] 同意增加 `G04_GOVERNANCE`
- [ ] 同意预留 `S02_SAFETY`
- [ ] 同意预留 `G03_DESIGN_CHANGE`
- [ ] 同意 G04 首期接入，不新增 `biz_governance_rectification`

#### `project_id`

**用途：** 项目级统计、G04 KPI 过滤和跨域查询。

建议：

- 新增 `project_id BIGINT NULL`；
- 历史案件先允许 NULL；
- 只有来源关系明确时回填；
- 新建案件由 API 强制要求项目归属；
- 历史回填完成后，再评估是否收紧为 NOT NULL。

确认：

- [ ] 同意增加 `project_id`
- [ ] 同意历史数据允许 NULL
- [ ] 同意无可信来源的历史记录不强行回填
- [ ] 同意新案件必须有项目归属

### 4. `biz_worker_payment_summary` 确认

**最终决策：** 继续复用，不新建 `biz_labor_payment_record`。

#### V0.3 兼容确认

- [ ] 保留 `payment_rate`
- [ ] 不重命名 `payment_rate`
- [ ] 不删除 `payable_amount`、`paid_amount` 等历史字段
- [ ] 不改变 V0.3 KPI 读取逻辑
- [ ] 首页 S03 语义映射为“农民工工资按时发放率”

#### 新增字段确认

| 字段 | 建议类型 | 用途 | 状态 |
|---|---|---|---|
| `source_type` | `VARCHAR(32) NULL` | 财务系统/人工填报 | [ ] |
| `record_date` | `DATE NULL` | 实际填报/记录日期 | [ ] |
| `created_at` | `DATETIME NULL` | 技术创建时间 | [ ] |

特别确认：

- [ ] 不使用 `updated_at` 自动伪造 `record_date`
- [ ] 缺少真实填报日期时保持 NULL
- [ ] S03 不新增个人姓名和工资金额明细
- [ ] 项目级指标采用人数加权计算，或另行确认标段展示口径

### 5. `compliance_procedure` 项目归属

**当前真实状态：** 存在，7 条；没有直接的 `project_id`。

推荐方案：增加 `project_id BIGINT NULL`，通过可信来源回填；没有可信归属的记录不进入项目 KPI 分母。

- [ ] 同意增加 `project_id`
- [ ] 同意历史数据允许 NULL
- [ ] 同意不通过责任部门/时间范围猜测项目归属
- [ ] 同意使用状态字典判断审批完成

### 6. `permit_record` 项目归属

**当前真实状态：** 存在，5 条；没有直接的 `project_id`。

推荐方案：增加 `project_id BIGINT NULL`，不依赖 `document_id` 作为唯一项目关系；临期/逾期记录保留为事实，不从表中删除。

- [ ] 同意增加 `project_id`
- [ ] 同意历史数据允许 NULL
- [ ] 同意临期/逾期记录仍保留
- [ ] 同意 G01/G02 计算前建立审批/许可证去重键

## 四、业务模型确认

### 1. 最终整改闭环

```text
e_closure_case
    |
    ├── e_rectification_task
    ├── e_case_status_history
    ├── e_case_evidence
    └── e_case_rectification_link
```

确认：

- [ ] `e_closure_case` 是案件主状态来源
- [ ] `e_rectification_task` 是具体整改轮次来源
- [ ] `e_case_status_history` 是不可替代的状态审计来源
- [ ] `e_case_evidence` 保存通知、整改、复核和关闭材料引用
- [ ] `e_case_rectification_link` 支持多轮整改
- [ ] G04 从 `biz_internal_control_issue` 映射接入
- [ ] `rectification_record` 仅作为历史/兼容来源，不全量模糊迁移

### 2. 整改完成时间规则

必须同时满足：

- [ ] 字段为 `e_rectification_task.rectification_completed_date`
- [ ] 来源为甲方填报
- [ ] 允许 NULL
- [ ] 提交复核前必须非空
- [ ] 系统不得自动生成
- [ ] 不得使用 `closed_at`/`closed_date` 代替
- [ ] API 原样返回
- [ ] 空值显示“待甲方填报”
- [ ] 历史无来源日期时保持 NULL

## 五、G01/G02 合并确认

### 1. 事实来源

```text
compliance_procedure
        +
permit_record
        +
special_plan_approval
```

确认：

- [ ] 审批事实来源为 `compliance_procedure`
- [ ] 许可证事实来源为 `permit_record`
- [ ] 专项方案审批纳入第三类事实来源
- [ ] 不新建 `biz_project_approval`
- [ ] 不新建 `biz_permit`

### 2. 首页指标

```text
合规审批与施工管控
```

### 3. 统计范围确认

| 状态 | 是否进入分母 | 是否计入完成数 | 确认 |
|---|---:|---:|---|
| 已完成/已批准 | 是 | 是 | [ ] |
| 有效许可证 | 是 | 是 | [ ] |
| 临期 | 是 | 否 | [ ] |
| 逾期 | 是 | 否 | [ ] |
| 未完成/待办理 | 是 | 否 | [ ] |
| 无项目归属 | 否，保留事实 | 否 | [ ] |
| 重复事项 | 去重后计一次 | 按统一事实判断 | [ ] |

计算建议：

```text
合规审批与施工管控完成率
= 已完成/有效控制事项数 ÷ 纳入管理的控制事项总数 × 100%
```

确认：

- [ ] 同意按统一 `control_item_key` 去重
- [ ] 同意不按三张表行数直接相加
- [ ] 同意无项目归属记录不进入项目 KPI 分母
- [ ] 同意具体状态值由状态字典确认后实现

## 六、S03 确认

### 1. 事实来源

- [ ] 继续使用 `biz_worker_payment_summary`
- [ ] 不新建 `biz_labor_payment_record`
- [ ] 保留 `payment_rate`
- [ ] 指标名称为“农民工工资按时发放率”
- [ ] 首页表达为“工资按时发放率 100%”等百分比表达

### 2. 计算口径

```text
工资按时发放率
= SUM(worker_count × payment_rate) ÷ SUM(worker_count)
```

确认：

- [ ] 按人数加权
- [ ] `worker_count <= 0` 不进入分母
- [ ] 无有效人数时返回空值，不返回 0%
- [ ] 不新增个人工资明细
- [ ] 标段展示与项目总率展示方式已确认

## 七、实施顺序检查

以下顺序是数据库审批通过后的执行顺序，本阶段不执行：

1. [ ] 数据库备份：表结构、数据、视图、V0.3 KPI 快照
2. [ ] 新增字段：先执行字段存在性检查
3. [ ] 新增 `special_plan_approval`
4. [ ] 结构验证：表、字段、索引、外键
5. [ ] Demo 数据验证：数量、来源、KPI 对照
6. [ ] 增加约束：G04 域值和必要约束
7. [ ] 建立索引：按验证后的执行计划建立
8. [ ] G04/S03/G01/G02 数据映射和业务验收
9. [ ] API 调整
10. [ ] Cursor 页面调整

每一步必须记录：执行人、时间、SQL 版本、影响对象、验证结果和异常处理。

## 八、回滚检查

### 1. 字段回滚

- [ ] 新增字段默认保留，不立即删除
- [ ] 停止 API/视图读取即可恢复 V0.3
- [ ] 删除字段前确认无 API、视图、任务和数据依赖
- [ ] `payment_rate` 不回滚为其他名称
- [ ] 不将关闭时间改作整改完成时间

### 2. 数据回滚

- [ ] 恢复实施前的表结构快照
- [ ] 恢复实施前的数据备份
- [ ] 恢复 V0.3 KPI 结果快照
- [ ] 新增数据保留迁移批次标识
- [ ] 不直接删除无法确认的数据，优先停用/标记无效

### 3. API 回滚

- [ ] 恢复 `/api/dashboard/kpis` V0.3 契约
- [ ] 恢复 `/api/dashboard/kpi/{key}` V0.3 读取逻辑
- [ ] S03 恢复读取 `biz_worker_payment_summary.payment_rate`
- [ ] G04 不返回系统生成的整改完成时间
- [ ] 首页不保留前端临时计算值

## 九、审批前必须人工确认事项

1. `special_plan_approval` 最终表名、字段、风险源外键和文件外键。
2. `rectification_completed_by` 是否随本次 DDL 增加，或由现有审计能力承担。
3. `e_closure_case.project_id` 的历史回填来源和 NULL 处理范围。
4. G04 域扩展是否同时预留 S02/G03 值。
5. G04 历史 CLOSED 记录是否允许没有整改完成日期。
6. S03 是否按人数加权形成项目总率，还是按标段分别展示。
7. `compliance_procedure`、`permit_record` 的项目归属回填清单。
8. G01/G02 的状态字典、统计周期、去重键和分母范围。
9. `safety_risk_point.id` 是否允许建立专项方案物理外键。
10. 数据库备份路径、恢复演练、执行窗口和回滚负责人。

## 十、最终建议

### 当前建议

**需要补充确认，不建议立即执行数据库变更。**

### 满足以下条件后可进入执行

- [ ] 本审批表所有“必须确认”项完成勾选并签字
- [ ] DDL 经过人工审核
- [ ] 备份和恢复路径已验证
- [ ] G04 历史映射清单已确认
- [ ] S03 和 G01/G02 计算口径已确认
- [ ] 项目归属回填方案已确认
- [ ] 回滚负责人和执行窗口已确认

**当前阶段状态：** 审批检查表已生成；数据库备份、DDL 执行、数据迁移、API 调整和 Cursor 页面调整均未开始。
