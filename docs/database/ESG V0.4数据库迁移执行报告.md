# ESG V0.4数据库迁移执行报告

## 1. 执行结论

- 执行状态：成功
- 执行日期：2026-08-05
- 数据库：MySQL 8.4.9
- 实例：`127.0.0.1:3307`
- 数据库：`luoyi_esg`
- 执行用户：`luoyi_app@127.0.0.1`
- 执行脚本：`C:\ESG_Project\database\migration\v0.4\V0.4_database_migration.sql`
- 执行范围：批准版 10 个步骤
- G04 CHECK 约束扩展：未执行
- 数据迁移：未执行
- API/前端代码：未修改

执行前确认的备份目录：

`C:\ESG_Project\database\archive\v0.4_pre_migration\20260804_211301\`

备份清单中的 6 个文件 SHA256 全部匹配。

## 2. 执行步骤结果

| 步骤 | 内容 | 结果 |
|---|---|---|
| 1 | `e_rectification_task` 新增 `rectification_completed_date`、`rectification_completed_by` | 成功 |
| 2 | 新增 `rectification_completed_by → user_account.id` 外键 | 成功 |
| 3 | `e_closure_case` 新增 `project_id` | 成功 |
| 4 | `compliance_procedure` 新增 `project_id` | 成功 |
| 5 | `permit_record` 新增 `project_id` | 成功 |
| 6 | `biz_worker_payment_summary` 新增 `source_type`、`record_date`、`created_at` | 成功 |
| 7 | 新建 `special_plan_approval` | 成功 |
| 8 | 新增专项方案批准索引 | 成功 |
| 9 | 新增 `risk_point_id → safety_risk_point.id` 外键 | 成功 |
| 10 | 新增 `approval_file_id → file_asset.id` 外键 | 成功 |

失败步骤：无。执行过程中未发生中途停止或补偿性回滚。

## 3. 表结构验证

### 3.1 新增字段

| 表 | 字段 | 实际类型 | NULL | 验证结果 |
|---|---|---|---|---|
| `e_rectification_task` | `rectification_completed_date` | `date` | YES | 通过 |
| `e_rectification_task` | `rectification_completed_by` | `bigint` | YES | 通过 |
| `e_closure_case` | `project_id` | `bigint` | YES | 通过 |
| `compliance_procedure` | `project_id` | `bigint` | YES | 通过 |
| `permit_record` | `project_id` | `bigint` | YES | 通过 |
| `biz_worker_payment_summary` | `source_type` | `varchar(32)` | YES | 通过 |
| `biz_worker_payment_summary` | `record_date` | `date` | YES | 通过 |
| `biz_worker_payment_summary` | `created_at` | `datetime` | YES | 通过 |

### 3.2 新增表与索引

`special_plan_approval` 已创建，存储引擎为 InnoDB，字符集/排序规则为 `utf8mb4_0900_ai_ci`。

已验证索引：

- `PRIMARY (id)`
- `uk_special_plan_project_code (project_id, plan_code)`
- `idx_special_plan_risk_point (risk_point_id)`
- `idx_special_plan_status (project_id, approval_status)`
- `idx_special_plan_date (project_id, approval_date)`
- `idx_special_plan_level (project_id, risk_level)`

当前 `special_plan_approval` 数据量为 0；本次未插入业务数据。

## 4. 外键验证

| 外键 | 目标 | 更新规则 | 删除规则 | 结果 |
|---|---|---|---|---|
| `fk_e_rect_task_completed_by` | `user_account.id` | RESTRICT | RESTRICT | 通过 |
| `fk_special_plan_risk_point` | `safety_risk_point.id` | RESTRICT | RESTRICT | 通过 |
| `fk_special_plan_approval_file` | `file_asset.id` | RESTRICT | RESTRICT | 通过 |

类型核对通过：三个目标主键均为 `BIGINT`，与新增引用字段一致。

`project_id` 未增加物理外键，仍按批准参数由 API/业务层负责项目归属校验。

## 5. 数据量与业务数据保护验证

| 重点表 | 迁移前 | 迁移后 | 结果 |
|---|---:|---:|---|
| `e_closure_case` | 17 | 17 | 未变化 |
| `e_rectification_task` | 3 | 3 | 未变化 |
| `biz_worker_payment_summary` | 2 | 2 | 未变化 |
| `compliance_procedure` | 7 | 7 | 未变化 |
| `permit_record` | 5 | 5 | 未变化 |
| `safety_risk_point` | 10 | 10 | 未变化 |
| `biz_internal_control_issue` | 2 | 2 | 未变化 |

本次执行未包含 `INSERT`、`UPDATE`、`DELETE` 或历史数据回填。

## 6. KPI 回归验证

### 6.1 数据库视图

`v_esg_demo_dashboard_kpis` 查询成功，仍返回 12 项 KPI。

### 6.2 HTTP API

- 健康检查：`GET http://127.0.0.1:8765/health`，通过；
- KPI 接口：`GET http://127.0.0.1:8765/api/dashboard/kpis`，通过；
- 迁移前后 12 项 KPI 快照逐项比对：一致；
- API 数据源：`esg_demo`；
- 统计截止日：`2026-08-04`。

重点结果保持：

- E04 文物保护对象：`0处`；
- S01 连续安全生产：`89天`，自 `2026-05-08` 起动态计算；
- S03 工资支付达标率：`100%`；
- G01：`12/12`、`100%`；
- G02：`2/2`、`100%`；
- G03：`4/4`、`100%`；
- G04：内控合规状态“正常”。

## 7. 未执行与后续边界

1. `e_closure_case.ck_e_case_domain` 保持原状，G04 域值扩展未执行；该项需独立审批和单独约束迁移。
2. `project_id` 历史数据未回填，历史记录仍允许 `NULL`。
3. `rectification_completed_date` 尚未加入 API 写入/复核校验逻辑；本次仅完成数据库字段和外键。
4. `special_plan_approval` 尚无 Demo 业务数据。
5. API 和前端未修改，当前 V0.3 KPI 契约保持兼容。

## 8. 回滚状态

- 回滚：未执行，原因是 10 步全部成功且验证通过；
- 数据恢复：未执行；
- API 回滚：未执行；
- 执行前备份：保留；
- 新增字段和新表：保留并等待 V0.4 API/数据接入；
- 若后续发现问题，优先在隔离库使用执行前备份恢复验证，禁止未经审批直接删除新增字段或新表。

## 9. 当前服务状态

- MySQL：`127.0.0.1:3307` 正在监听；
- Python API：`127.0.0.1:8765` 健康检查通过；
- 前端：未修改；
- 页面 KPI：迁移后回归一致。

## 10. 最终结论

ESG V0.4 批准版数据库 DDL 已完成执行，10 个步骤全部成功。数据库结构变更已生效，历史业务数据和 V0.3 首页 KPI 未发生变化，G04 CHECK 约束扩展及后续 API/前端开发仍按原计划等待单独任务。
