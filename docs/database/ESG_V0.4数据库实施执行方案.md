# ESG V0.4 数据库实施执行方案

**版本：** V1.0 实施前方案  
**工作区：** `C:\ESG_Project`  
**数据库：** MySQL 8.4.9，`127.0.0.1:3307/luoyi_esg`  
**基线：** ESG Demo V0.3：首页一级指标业务事实校正版  
**当前状态：** 只编制方案，不执行数据库修改

> 本文件中的 DDL、验证 SQL、备份命令均为待人工审核的执行材料。本次没有执行 `CREATE TABLE`、`ALTER TABLE`、`INSERT`、`UPDATE`、`DELETE`、视图修改、API 修改或前端修改。

## 一、实施决策基线

本方案依据以下已确认文件编制：

- `docs/business/ESG_V0.4业务调整与数据模型设计方案.md`
- `docs/database/ESG_V0.4数据库实施变更清单.md`
- `docs/database/ESG_V0.4数据库实施前结构核查报告.md`
- `docs/database/ESG_V0.4最终数据模型决策报告.md`

### 1. 最终采用的模型

```text
通用闭环：
e_closure_case
  ├── e_rectification_task
  ├── e_case_status_history
  ├── e_case_evidence
  └── e_case_rectification_link

S03：biz_worker_payment_summary
G01/G02：compliance_procedure + permit_record
风险专项方案：special_plan_approval（唯一新增业务表）
```

### 2. 明确不实施的重复对象

本次不新建：

- `biz_labor_payment_record`；
- `biz_project_approval`；
- `biz_permit`；
- `biz_governance_rectification`；
- `cl_case`。

本次不删除任何 V0.3 表、视图、历史数据或既有闭环表。

## 二、实施范围

### 1. 结构变更对象

| 对象 | 计划动作 | 目的 |
|---|---|---|
| `e_rectification_task` | 增加 `rectification_completed_date` | 保存甲方填报的实际整改完成日期 |
| `e_closure_case` | 扩展域值；评估增加 `project_id` | 接入 G04 并支持项目级查询 |
| `biz_worker_payment_summary` | 增加来源/记录时间字段 | 复用 S03 事实表且不破坏 `payment_rate` |
| `compliance_procedure` | 增加项目归属或完成可信映射 | 支持 G01/G02 项目级统计 |
| `permit_record` | 增加项目归属或完成可信映射 | 支持 G01/G02 项目级统计 |
| `safety_risk_point` | 只建立关联前置核查，不默认改表 | 作为专项方案的风险源目标 |
| `special_plan_approval` | 新增表 | 保存风险专项方案审批事实 |

### 2. 业务域

V0.4 首期启用：`E01_EXCEED`、`E02_ENV`、`E03_WATER`、`G04_GOVERNANCE`。  
同一闭环模型预留：`S02_SAFETY`、`G03_DESIGN_CHANGE`，本次不导入对应新业务数据。

## 三、阶段 1：数据库备份与基线快照

### 1. 备份范围

实施前必须同时保存：

- 全库表结构；
- 全库数据；
- 所有视图定义；
- 重点表结构和行数；
- `v_esg_demo_dashboard_kpis` 当前 KPI 结果；
- 当前 API `/api/dashboard/kpis` 返回快照；
- 当前 `esg_schema_migration_history` 内容。

建议目录：

```text
C:\ESG_Project\database\archive\v0.4_pre_migration\YYYYMMDD_HHMMSS\
├── schema.sql
├── data.sql
├── views.sql
├── key_table_counts.csv
├── v0.3_dashboard_kpis.json
└── migration_history.csv
```

### 2. 待审核备份命令

以下命令只作为执行模板，必须由数据库负责人确认账号、路径和窗口后执行；本次未执行：

```powershell
mysqldump.exe `
  --host=127.0.0.1 --port=3307 `
  --user=<DB_USER> --password `
  --single-transaction --routines --triggers `
  --no-data luoyi_esg `
  > C:\ESG_Project\database\archive\v0.4_pre_migration\schema.sql

mysqldump.exe `
  --host=127.0.0.1 --port=3307 `
  --user=<DB_USER> --password `
  --single-transaction --routines --triggers `
  --no-create-info luoyi_esg `
  > C:\ESG_Project\database\archive\v0.4_pre_migration\data.sql
```

密码不得写入脚本、Git、工作区文档或命令历史。

### 3. 实施前只读快照 SQL

```sql
SELECT VERSION() AS mysql_version, DATABASE() AS database_name;

SELECT TABLE_NAME, TABLE_TYPE
FROM information_schema.tables
WHERE TABLE_SCHEMA = 'luoyi_esg'
ORDER BY TABLE_TYPE, TABLE_NAME;

SELECT TABLE_NAME, TABLE_ROWS
FROM information_schema.tables
WHERE TABLE_SCHEMA = 'luoyi_esg'
  AND TABLE_NAME IN (
    'e_closure_case', 'e_rectification_task', 'e_case_status_history',
    'e_case_evidence', 'e_case_rectification_link',
    'biz_internal_control_issue', 'rectification_record',
    'biz_worker_payment_summary', 'compliance_procedure',
    'permit_record', 'safety_risk_point', 'esg_demo_indicator_result'
  )
ORDER BY TABLE_NAME;

SELECT project_id, period_end, kpi_key, kpi_name,
       value_decimal, value_text, unit, risk_level, result_status
FROM esg_demo_indicator_result
WHERE project_id = 1001
ORDER BY period_end, kpi_key;
```

快照结果必须导出保存，作为后续迁移前后对照基线。

## 四、阶段 2：结构变更设计

执行顺序固定为：

```text
增加字段
    ↓
新增 special_plan_approval
    ↓
增加域约束/必要外键
    ↓
建立索引
    ↓
结构验证
```

每一步执行前后都要记录 DDL、执行时间、执行人和影响行数。

### 1. `e_rectification_task` 增加整改完成时间

#### 字段决策

| 项目 | 决策 |
|---|---|
| 字段 | `rectification_completed_date` |
| 类型 | `DATE` |
| NULL | 允许 NULL |
| 填写责任 | 甲方填报 |
| 必填时点 | 提交复核/进入 `PENDING_REVIEW` 前 |
| 自动生成 | 禁止 |
| 复核退回 | 新整改轮次单独记录，不覆盖旧值 |
| API | 原样返回；NULL 返回空值和“待甲方填报”状态 |

#### 待审核 DDL

```sql
ALTER TABLE e_rectification_task
  ADD COLUMN rectification_completed_date DATE NULL
  COMMENT '甲方填报的实际整改完成日期，系统不得自动生成';
```

这条 SQL 仅为执行草案。执行前必须先查询字段不存在，并确认当前版本支持该列定义；不能重复执行。

### 2. `e_closure_case` 增加 G04 域和项目归属

#### G04 域

现有 `ck_e_case_domain` 只允许 E01/E02/E03。计划将以下值纳入域约束：

```text
E01_EXCEED
E02_ENV
E03_WATER
G04_GOVERNANCE
S02_SAFETY       -- 预留
G03_DESIGN_CHANGE -- 预留
```

V0.4 首期只启用 `G04_GOVERNANCE`；预留域不导入业务数据。

#### 项目归属

建议增加：

```sql
ALTER TABLE e_closure_case
  ADD COLUMN project_id BIGINT NULL
  COMMENT '项目归属；历史案件回填完成后，新案件必须填写';
```

原因：当前闭环模型依赖 `source_table + source_record_id`，但跨域统计和 G04 KPI 需要稳定的项目过滤字段。历史记录先允许 NULL，完成映射后再评估是否收紧为 NOT NULL。

#### 域约束执行草案

```sql
ALTER TABLE e_closure_case
  DROP CHECK ck_e_case_domain,
  ADD CONSTRAINT ck_e_case_domain CHECK (
    case_domain IN (
      'E01_EXCEED', 'E02_ENV', 'E03_WATER',
      'G04_GOVERNANCE', 'S02_SAFETY', 'G03_DESIGN_CHANGE'
    )
  );
```

执行前必须核对 MySQL 实际约束名称，并先确认现有数据无超出新约束的值。若线上约束管理方式不是直接 `CHECK`，应改为项目状态字典方案，不得盲目执行。

### 3. `biz_worker_payment_summary` 增加来源和记录时间

#### 字段决策

保留现有字段，尤其是：

```text
payment_rate
```

不重命名、不删除、不改变 V0.3 语义。新增字段建议：

| 字段 | 类型 | NULL | 用途 |
|---|---|---:|---|
| `source_type` | `VARCHAR(32)` | 是 | `FINANCE_SYSTEM`/`MANUAL` 等来源 |
| `record_date` | `DATE` | 是 | 实际填报/记录日期，不等于更新时间 |
| `created_at` | `DATETIME` | 是 | 技术创建时间 |

#### 待审核 DDL

```sql
ALTER TABLE biz_worker_payment_summary
  ADD COLUMN source_type VARCHAR(32) NULL COMMENT '数据来源类型',
  ADD COLUMN record_date DATE NULL COMMENT '实际填报/记录日期',
  ADD COLUMN created_at DATETIME NULL COMMENT '技术创建时间';
```

注意：现有 `updated_at` 不得直接冒充业务 `record_date`。如果历史数据没有真实填报日期，`record_date` 保持 NULL，待甲方补填；不能由系统推算。

### 4. `compliance_procedure` 和 `permit_record` 项目归属

#### 最终推荐

优先在两张事实表增加 `project_id`，不新建临时关联表。原因：当前两表没有可靠的项目字段，而 G01/G02 合并统计必须先按项目过滤；依赖 `document_id` 的间接映射无法保证所有 Demo/正式记录完整关联。

#### 待审核 DDL

```sql
ALTER TABLE compliance_procedure
  ADD COLUMN project_id BIGINT NULL COMMENT '项目归属，历史数据回填后使用';

ALTER TABLE permit_record
  ADD COLUMN project_id BIGINT NULL COMMENT '项目归属，历史数据回填后使用';
```

历史数据回填原则：

- 有明确项目资料关系时回填 1001；
- 无可信关系时保持 NULL，并从项目 KPI 分母排除；
- 不根据表名、责任部门或时间范围猜测项目归属。

### 5. `safety_risk_point` 与专项方案关系

本次不直接修改 `safety_risk_point`。现有 `safety_risk_point.id` 作为专项方案关系目标，专项方案表保存 `risk_point_id`。由于风险表当前没有明确 `project_id`，正式执行前必须完成风险源与项目的归属核对。

如果核对确认风险表的 `id` 可作为稳定主键，再建立外键；否则先只建立逻辑关联并延后物理外键，禁止建立错误外键。

## 五、阶段 2：新增 `special_plan_approval`

### 1. 建表设计

唯一新增表名最终确定为：

```text
special_plan_approval
```

### 2. 待审核建表 SQL

```sql
CREATE TABLE special_plan_approval (
  id BIGINT NOT NULL AUTO_INCREMENT,
  project_id BIGINT NULL COMMENT '项目归属，正式多项目数据必填',
  risk_point_id BIGINT NOT NULL COMMENT '关联 safety_risk_point.id',
  plan_code VARCHAR(80) NOT NULL COMMENT '专项方案编号',
  plan_name VARCHAR(255) NOT NULL COMMENT '专项方案名称',
  risk_level VARCHAR(50) NOT NULL COMMENT '沿用项目已有风险等级',
  approval_status VARCHAR(40) NOT NULL COMMENT '沿用项目审批状态字典',
  approval_date DATE NULL COMMENT '审批完成日期',
  approval_file_id BIGINT NULL COMMENT '关联 file_asset.id，可空',
  source_doc_ref VARCHAR(255) NULL COMMENT '来源资料编号',
  data_nature VARCHAR(20) NOT NULL DEFAULT 'demo' COMMENT 'demo/formal/platform_calc',
  is_demo TINYINT(1) NOT NULL DEFAULT 1,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  UNIQUE KEY uk_special_plan_project_code (project_id, plan_code),
  KEY idx_special_plan_risk_point (risk_point_id),
  KEY idx_special_plan_status (project_id, approval_status),
  KEY idx_special_plan_date (project_id, approval_date),
  KEY idx_special_plan_level (project_id, risk_level)
) ENGINE=InnoDB
  DEFAULT CHARSET=utf8mb4
  COLLATE=utf8mb4_0900_ai_ci
  COMMENT='ESG 风险专项方案审批事实';
```

### 3. 外键关系建议

建议关系：

```sql
ALTER TABLE special_plan_approval
  ADD CONSTRAINT fk_special_plan_risk_point
  FOREIGN KEY (risk_point_id)
  REFERENCES safety_risk_point (id)
  ON UPDATE RESTRICT
  ON DELETE RESTRICT;
```

`approval_file_id → file_asset.id` 是否建立物理外键，须先核对两列类型和文件生命周期；若文件可归档/替换，第一期可保留逻辑引用，避免误删文件导致事实记录不可用。

`project_id` 暂不设置外键，因为当前真实库未确认统一项目主表；项目主数据确定后再补齐。

## 六、通用整改闭环实施设计

### 1. G04 接入流程

```text
biz_internal_control_issue
        ↓ 只读映射/保留来源
e_closure_case(case_domain=G04_GOVERNANCE)
        ↓
e_rectification_task
        ↓ 甲方填写 rectification_completed_date
e_case_evidence（通知/整改材料/复核意见/关闭资料）
        ↓
e_case_status_history
        ↓
PENDING_RECTIFICATION → RECTIFYING → PENDING_REVIEW
        ↓ 复核通过
PENDING_CLOSURE → CLOSED
```

### 2. G04 旧数据映射

#### `biz_internal_control_issue`

| 旧字段 | 新对象/字段 | 规则 |
|---|---|---|
| `id` | `e_closure_case.source_record_id` | 原值保留 |
| 表名 | `source_table` | 固定为 `biz_internal_control_issue` |
| `issue_code` | `case_code`/`source_business_key` | 保留原问题编号 |
| `issue_description` | `e_closure_case.title` | 不改写业务事实 |
| `found_at` | `opened_at` | 原始发现时间 |
| `deadline` | `deadline` | 原始期限 |
| `responsible_org_id` | `responsible_org_id` | 原责任组织 |
| `current_status=CLOSED` | `current_status=CLOSED` | 保留历史关闭状态 |
| `current_status=OPEN` | `current_status=PENDING_RECTIFICATION` | 不推断已开始整改 |
| `closed_at` | `closed_at` | 仅有原关闭日期时保留 |
| `issue_level` | `severity` | 沿用现有等级 |

旧表没有 `rectification_completed_date`，历史 CLOSED 记录不得用 `closed_at` 冒充完成时间。迁移后的历史任务允许该字段 NULL，并标记为历史数据；新任务必须遵守 V0.4 规则。

#### `rectification_record`

该表没有稳定的 `inspection_id`/`case_id`，不能全量自动转换。仅在存在明确的 `source_doc_ref`、`check_batch`、问题编号或人工确认关系时映射；无法可靠关联的记录保留原表，列入待治理清单，不做模糊匹配。

### 3. 状态和证据迁移

- 新案件的状态变化全部写入 `e_case_status_history`；
- 甲方整改材料使用 `e_case_evidence.evidence_role=RECTIFICATION_MATERIAL`；
- 复核资料使用 `REVIEW_OPINION`；
- 关闭资料使用 `CLOSURE_DOCUMENT`；
- 案件与多轮整改任务通过 `e_case_rectification_link` 关联；
- 不复制源文件内容，只建立 `document_id`/`file_id` 引用。

## 七、阶段 3：数据映射方案

### 1. G04 映射

执行前先导出 `biz_internal_control_issue`、`rectification_record` 和既有 E 闭环数据。迁移采用“先案件、后任务、再状态和证据”的顺序：

```text
旧问题事实
  → e_closure_case
  → e_rectification_task
  → e_case_rectification_link
  → e_case_status_history
  → e_case_evidence
```

映射约束：

- 同一 `source_table + source_record_id` 只能对应一个主案件；
- 历史记录不补造甲方完成时间；
- 无法确认的整改完成日期保持 NULL；
- 迁移前后旧表行数必须一致；
- 新案件的 `data_nature`/`is_demo` 必须与来源一致。

### 2. S03 映射

继续使用 `biz_worker_payment_summary`，不复制到新表：

```text
worker_count  → total_workers
payment_rate  → paid_on_time_rate
period_start + period_end → period
source_doc_ref → source reference
```

`source_type`、`record_date`、`created_at`：

- 有真实来源时按来源填充；
- 无真实记录日期时保持 NULL；
- 不使用 `updated_at` 自动伪造业务记录日期；
- 不修改 `payment_rate` 当前值和 V0.3 读取逻辑。

### 3. G01/G02 映射

在项目归属确认后，分别给 `compliance_procedure`、`permit_record` 关联项目；不按全库总数直接计算。

统一控制事项：

```text
来源类型 + 来源表 + 来源记录ID
```

同一审批/许可证重复出现时，以业务编号、许可证号、方案编号或人工确认的关联关系去重。未能确认项目归属的记录不进入项目 KPI 分母，但保留原事实。

## 八、阶段 4：验证方案

### 1. 结构验证 SQL

以下 SQL 用于迁移后只读验收，不在本阶段执行：

```sql
-- 1. 表存在
SELECT TABLE_NAME, TABLE_TYPE
FROM information_schema.tables
WHERE TABLE_SCHEMA = 'luoyi_esg'
  AND TABLE_NAME IN (
    'special_plan_approval',
    'e_closure_case',
    'e_rectification_task',
    'biz_worker_payment_summary',
    'compliance_procedure',
    'permit_record'
  );

-- 2. 字段存在
SELECT TABLE_NAME, COLUMN_NAME, COLUMN_TYPE, IS_NULLABLE, COLUMN_DEFAULT
FROM information_schema.columns
WHERE TABLE_SCHEMA = 'luoyi_esg'
  AND (
    (TABLE_NAME = 'e_rectification_task' AND COLUMN_NAME = 'rectification_completed_date')
    OR (TABLE_NAME = 'e_closure_case' AND COLUMN_NAME IN ('project_id', 'case_domain'))
    OR (TABLE_NAME = 'biz_worker_payment_summary' AND COLUMN_NAME IN ('payment_rate', 'source_type', 'record_date', 'created_at'))
    OR (TABLE_NAME IN ('compliance_procedure', 'permit_record') AND COLUMN_NAME = 'project_id')
  )
ORDER BY TABLE_NAME, ORDINAL_POSITION;

-- 3. 索引存在
SELECT TABLE_NAME, INDEX_NAME, COLUMN_NAME, NON_UNIQUE, SEQ_IN_INDEX
FROM information_schema.statistics
WHERE TABLE_SCHEMA = 'luoyi_esg'
  AND TABLE_NAME IN ('special_plan_approval', 'e_rectification_task')
ORDER BY TABLE_NAME, INDEX_NAME, SEQ_IN_INDEX;

-- 4. 外键存在
SELECT TABLE_NAME, CONSTRAINT_NAME, COLUMN_NAME,
       REFERENCED_TABLE_NAME, REFERENCED_COLUMN_NAME
FROM information_schema.key_column_usage
WHERE CONSTRAINT_SCHEMA = 'luoyi_esg'
  AND TABLE_NAME = 'special_plan_approval'
  AND REFERENCED_TABLE_NAME IS NOT NULL;

-- 5. G04 域约束核对
SELECT CONSTRAINT_NAME, CHECK_CLAUSE
FROM information_schema.check_constraints
WHERE CONSTRAINT_SCHEMA = 'luoyi_esg'
  AND CONSTRAINT_NAME = 'ck_e_case_domain';
```

### 2. 数据数量验证 SQL

迁移前、迁移后分别执行并导出结果，不能只看迁移后数量：

```sql
SELECT 'biz_internal_control_issue' AS table_name, COUNT(*) AS row_count
FROM biz_internal_control_issue
UNION ALL
SELECT 'rectification_record', COUNT(*) FROM rectification_record
UNION ALL
SELECT 'e_closure_case', COUNT(*) FROM e_closure_case
UNION ALL
SELECT 'e_rectification_task', COUNT(*) FROM e_rectification_task
UNION ALL
SELECT 'e_case_status_history', COUNT(*) FROM e_case_status_history
UNION ALL
SELECT 'e_case_evidence', COUNT(*) FROM e_case_evidence
UNION ALL
SELECT 'biz_worker_payment_summary', COUNT(*) FROM biz_worker_payment_summary
UNION ALL
SELECT 'special_plan_approval', COUNT(*) FROM special_plan_approval;
```

### 3. S03 数据验证 SQL

```sql
SELECT project_id, period_start, period_end,
       SUM(worker_count) AS total_workers,
       SUM(worker_count * payment_rate) / NULLIF(SUM(worker_count), 0) AS weighted_rate,
       COUNT(*) AS source_rows
FROM biz_worker_payment_summary
WHERE is_deleted = 0
GROUP BY project_id, period_start, period_end
ORDER BY project_id, period_start, period_end;

SELECT project_id, period_end, kpi_key, kpi_name,
       value_decimal, value_text, unit, result_status
FROM esg_demo_indicator_result
WHERE project_id = 1001
ORDER BY period_end, kpi_key;
```

重点：`payment_rate` 必须仍然存在；V0.3 快照与新结果不一致时先停止切换，不直接修改 Demo 值。

### 4. G04 状态验证 SQL

```sql
SELECT current_status, COUNT(*) AS case_count
FROM e_closure_case
WHERE case_domain = 'G04_GOVERNANCE'
GROUP BY current_status
ORDER BY current_status;

SELECT task_status,
       COUNT(*) AS task_count,
       SUM(rectification_completed_date IS NULL) AS completed_date_null_count
FROM e_rectification_task
GROUP BY task_status
ORDER BY task_status;

SELECT c.case_code, c.current_status, t.task_status,
       t.rectification_completed_date, c.closed_at
FROM e_closure_case c
LEFT JOIN e_case_rectification_link l ON l.case_id = c.id
LEFT JOIN e_rectification_task t ON t.id = l.task_id
WHERE c.case_domain = 'G04_GOVERNANCE'
ORDER BY c.id, t.id;
```

### 5. 业务验证

#### 整改完成时间

验证规则：

- 新任务创建时允许 `rectification_completed_date IS NULL`；
- 未填写时不能提交为待复核；
- 甲方填写后能够保存真实日期；
- 状态历史记录提交复核动作；
- API 返回该日期原值；
- 系统日志能识别填报人和时间；
- 不出现当前日期自动写入。

建议使用一条隔离 Demo 测试任务进行人工验收，测试完成后按测试数据清理审批流程处理，不得直接在正式事实表中随意插入测试数据。

#### API 只读验证

数据库迁移和后端调整完成后，才执行：

```powershell
Invoke-RestMethod 'http://127.0.0.1:8765/api/dashboard/kpis'
Invoke-RestMethod 'http://127.0.0.1:8765/api/dashboard/kpi/G04'
```

本方案阶段不执行 API 验证切换，也不修改 API。

## 九、回滚方案

### 1. 字段回滚

- 新增字段先保留，不立即执行 `DROP COLUMN`；
- 停止 API 和视图读取新增字段即可恢复 V0.3；
- 只有确认无 API、视图、任务和数据依赖后，才另行审批删除字段；
- `payment_rate` 永不重命名或删除；
- `closed_at` 不改作完成日期。

### 2. 约束和索引回滚

- G04 域约束回滚前先确认没有 G04 案件；
- 新增索引回滚前检查执行计划和依赖，必要时保留索引；
- 外键回滚前确认没有孤儿记录，优先停用写入而不是强行删除约束。

### 3. 数据回滚

- 恢复实施前的表结构、数据、视图和 KPI 快照；
- 新增专项方案数据保留迁移批次标识，必要时标记无效，不直接物理删除；
- 映射失败的 G04 记录不覆盖旧表，保留在原表并从新 KPI 中排除；
- 恢复前后核对关键表行数、主键、外键和状态数量。

### 4. API 回滚

- 恢复 V0.3 `/api/dashboard/kpis` 和 `/api/dashboard/kpi/{key}` 契约；
- G04 详情恢复旧数据源或返回明确不可用状态，不返回伪造的完成时间；
- S03 恢复读取 `biz_worker_payment_summary.payment_rate`；
- 首页不保留前端临时计算值。

## 十、实施风险清单

| 风险 | 影响 | 控制措施 |
|---|---|---|
| `e_closure_case` 历史数据迁移 | 可能丢失状态/证据链 | 只映射有明确来源的记录，保留旧表和历史快照 |
| G04 域扩展 | Check 约束或状态映射失败 | 先核对约束名和值域，只启用 G04 |
| 项目归属字段 | 全库统计导致 KPI 错误 | 无可信项目归属的记录不进项目分母 |
| G01/G02 重复统计 | 审批与许可证同一事项重复计数 | 统一 `control_item_key`，先对账再计算 |
| S03 计算口径 | 98.5%/100% 被错误取第一条 | 按人数加权，明确标段与项目展示口径 |
| 专项方案关联 | 风险源不存在项目归属或主键关系 | 先验证 `risk_point_id`，必要时只做逻辑关联 |
| 完成时间伪造 | 产生合规风险 | NULL 允许，甲方填报，禁止系统时间补写 |
| Demo/正式混用 | 影响真实项目数据 | 保留 `data_nature`/`is_demo`，迁移前后隔离 |
| 旧接口依赖 | 页面回归或 KPI 变化 | 先保留 V0.3 视图/API，最后切换 |

## 十一、审批闸门与执行顺序

```text
本实施方案审核
        ↓
备份和 V0.3 快照
        ↓
字段/约束变更审核
        ↓
新增 special_plan_approval
        ↓
结构验证
        ↓
G04/S03/G01/G02 数据映射
        ↓
数据验证和业务验收
        ↓
API 调整
        ↓
Cursor 页面调整
```

数据库修改前必须由人工确认：

- 备份目录和恢复演练结果；
- DDL 逐条审核；
- `project_id` 的回填来源；
- G04 历史数据是否允许完成时间为空；
- S03 项目级加权口径；
- G01/G02 纳入范围、去重键和状态字典；
- `special_plan_approval` 最终命名及外键策略；
- 执行窗口、负责人和回滚负责人。

**最终状态：** V0.4 数据库实施执行方案已编制；数据库修改、API 调整和 Cursor 页面调整均未开始，等待数据库变更审批。
