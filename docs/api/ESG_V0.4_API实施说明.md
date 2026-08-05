# ESG V0.4 API实施说明

**文档版本：** V1.0（API 开发边界确认）  
**基线：** ESG Demo V0.3：首页一级指标业务事实校正版  
**状态：** 设计确认稿，**尚未编码**  
**前提：** 当前数据库 DDL **尚未执行**；完成数据库迁移并通过核验后，方可开始 API 编码

---

## 1. 文档状态与开发边界

### 1.1 当前阶段

| 项 | 状态 |
|---|---|
| V0.4 业务/数据模型决策 | 已形成（见 `docs/database/`） |
| V0.4 数据库 DDL | **尚未执行** |
| V0.4 API 设计 | 本文件确认 |
| V0.4 API 编码 | **禁止开始**，等待迁移完成 |

### 1.2 本阶段严格禁止

| 禁止项 | 说明 |
|---|---|
| 修改首页 KPI | 不改 `/api/dashboard/kpis` 及 V0.3 首页契约 |
| 修改 E/S/G 指标口径 | 名称、数值、单位、计算口径、描述、风险等级均不动 |
| 新增数据库表 | API 阶段不得发明额外表；仅使用已批准的 V0.4 DDL |
| 新增数据库字段 | API 阶段不得发明额外字段；仅使用已批准的 V0.4 DDL |
| 修改文件上传接口 | 不改 `/api/workspace/files/upload` 及既有解析流程 |
| 物理删除审批记录 | 禁止 `DELETE /api/governance/special-plans/{id}` 及任何 `DELETE FROM special_plan_approval` |

### 1.3 业务对象定性（专项方案）

`special_plan_approval` 属于：

1. 风险管控专项方案；
2. 审批事实；
3. 合规证据链。

因此：**禁止物理删除审批记录**。撤销、作废等业务语义如需表达，只能通过修改 `approvalStatus`（及必要审批信息）实现，不得删除行。

### 1.4 后端落点（编码阶段参考，当前不改代码）

| 项 | 路径 |
|---|---|
| 路由入口 | `backend/app.py` |
| 数据访问 | `backend/mysql_api.py` |
| HTTP | 原生 `BaseHTTPRequestHandler`（现有 GET / POST / OPTIONS） |
| 本次需补充 | `PATCH`；对专项方案 **不注册 DELETE 业务路由** |

本次新增 API **不复用**首页 KPI 查询函数，避免影响 V0.3 首页契约。

---

## 2. API 列表

### 2.1 整改任务（`e_rectification_task`）

| 方法 | 路径 | 状态 | 用途 |
|---|---|---|---|
| GET | `/api/governance/rectification-tasks` | 保留 | 查询整改任务列表 |
| GET | `/api/governance/rectification-tasks/{id}` | 保留 | 查询整改任务详情 |
| PATCH | `/api/governance/rectification-tasks/{id}` | 保留 | **仅**修改整改完成日期与填报人 |

允许修改字段（仅此两项）：

- `rectificationCompletedDate`
- `rectificationCompletedBy`

严格禁止：

- 系统自动填充完成时间；
- 使用当前日期/上传时间/提交时间/状态切换时间替代甲方填报；
- `closed_at` → `rectification_completed_date` 的任何映射或回填；
- 本接口自动改写 `task_status`、案件关闭时间或复核状态。

### 2.2 专项方案审批（`special_plan_approval`）

| 方法 | 路径 | 状态 | 用途 |
|---|---|---|---|
| GET | `/api/governance/special-plans` | 保留 | 查询专项方案审批列表 |
| GET | `/api/governance/special-plans/{id}` | 保留 | 查询专项方案审批详情 |
| POST | `/api/governance/special-plans` | 保留 | 新增专项方案审批事实 |
| PATCH | `/api/governance/special-plans/{id}` | 保留 | 修改审批状态、审批信息、文件关联 |

| 方法 | 路径 | 状态 | 处理要求 |
|---|---|---|---|
| DELETE | `/api/governance/special-plans/{id}` | **禁止** | **不提供该业务接口**；不得注册为可删除能力；若请求到达服务端，返回 `405 Method Not Allowed`，且 **严禁** 访问数据库执行删除 |

PATCH 允许修改的业务范围：

- 审批状态（`approvalStatus`）；
- 审批信息（如 `planName`、`riskLevel`、`approvalDate`、`sourceDocRef`）；
- 文件关联（`approvalFileId`；`null` 仅表示解除关联，不删除 `file_asset`）。

---

## 3. 请求参数

### 3.1 `GET /api/governance/rectification-tasks`

| 参数 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `taskStatus` | string | 否 | 任务状态过滤 |
| `dataNature` | string | 否 | `demo` / 正式等数据范围 |
| `isDemo` | 0/1 | 否 | Demo 标识过滤 |
| `completed` | 0/1 | 否 | `1`=已有完成日期；`0`=完成日期为空 |

不自动注入项目 ID 或其他隐式业务过滤。

### 3.2 `GET /api/governance/rectification-tasks/{id}`

路径参数：`id`（`e_rectification_task.id`）。

### 3.3 `PATCH /api/governance/rectification-tasks/{id}`

请求体仅允许下列字段（至少一个）：

```json
{
  "rectificationCompletedDate": "2026-08-05",
  "rectificationCompletedBy": 10001
}
```

| 字段 | 类型 | 规则 |
|---|---|---|
| `rectificationCompletedDate` | string \| null | `YYYY-MM-DD`；允许显式 `null`（清空完成日期时） |
| `rectificationCompletedBy` | number \| null | 对应 `user_account.id`；允许显式 `null` |

校验与写入规则：

1. 只更新请求体中**明确出现**的字段；
2. `rectificationCompletedBy` 非空时必须存在于 `user_account`；
3. 成对规则（与批准版参数一致）：
   - 日期为 `null` → 完成人可为 `null`；
   - 日期非空 → 完成人必须非空（可同一次 PATCH 一并提交）；
4. **禁止**读取或依赖 `e_closure_case.closed_at` 写入完成日期；
5. **禁止**服务端用 `CURRENT_DATE` / `NOW()` 自动填日期；
6. SQL `UPDATE` 目标列仅限：`rectification_completed_date`、`rectification_completed_by`。

### 3.4 `GET /api/governance/special-plans`

| 参数 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `projectId` | bigint | 建议 | 项目归属过滤 |
| `riskPointId` | bigint | 否 | 风险源过滤 |
| `approvalStatus` | string | 否 | 审批状态过滤 |
| `riskLevel` | string | 否 | 沿用既有风险等级，不新增等级 |
| `dataNature` | string | 否 | 数据范围 |
| `isDemo` | 0/1 | 否 | Demo 标识 |

不转换审批状态语义，不模糊合并事实记录。

### 3.5 `GET /api/governance/special-plans/{id}`

路径参数：`id`（`special_plan_approval.id`）。

### 3.6 `POST /api/governance/special-plans`

必填：

```json
{
  "projectId": 1001,
  "riskPointId": 1,
  "planCode": "SP-001",
  "planName": "高边坡专项施工方案",
  "riskLevel": "重大",
  "approvalStatus": "已审批"
}
```

可选：

```json
{
  "approvalDate": "2026-08-05",
  "approvalFileId": 900001,
  "sourceDocRef": "DOC-2026-001",
  "dataNature": "demo",
  "isDemo": true
}
```

校验：

- 必填字段齐全；
- `riskPointId` → `safety_risk_point.id`；
- `approvalFileId` 如提供 → 未删除的 `file_asset.id`；
- `(projectId, planCode)` 满足唯一约束；
- **不**自动生成审批日期、**不**自动改审批状态；
- **不**在本接口上传文件（继续使用既有上传接口）。

### 3.7 `PATCH /api/governance/special-plans/{id}`

允许修改：

| API 字段 | 业务含义 |
|---|---|
| `approvalStatus` | 审批状态 |
| `planName` | 方案名称（审批信息） |
| `riskLevel` | 风险等级（审批信息，沿用既有字典） |
| `approvalDate` | 审批日期（审批信息） |
| `sourceDocRef` | 来源资料引用（审批信息） |
| `approvalFileId` | 文件关联；`null`=解除关联，不删文件 |

禁止通过 PATCH 修改：

- `id`、`projectId`、`riskPointId`、`planCode`
- `createdAt`、以及表中不存在的审计伪造字段

### 3.8 禁止的 DELETE

```http
DELETE /api/governance/special-plans/{id}
```

预期行为（编码阶段）：

- HTTP `405 Method Not Allowed`；
- 响应体明确说明：专项方案审批为合规证据链，禁止物理删除；
- 数据库行数不变；
- 代码中不得出现针对本表的 `DELETE FROM special_plan_approval`。

---

## 4. 返回结构

### 4.1 列表通用包装

```json
{
  "total": 1,
  "items": []
}
```

### 4.2 整改任务项

```json
{
  "id": 928001,
  "taskCode": "TASK-E01-NOISE-20260708",
  "title": "调整夜间运输时段并增设临时声屏障",
  "taskStatus": "IN_PROGRESS",
  "deadline": "2026-07-25 18:00:00",
  "rectificationCompletedDate": null,
  "rectificationCompletedBy": null,
  "dataNature": "demo",
  "isDemo": true
}
```

说明：`rectificationCompletedDate` 为 `null` 时，前端可展示“待甲方填报”；API **原样返回 null**，不改写为假日期。

### 4.3 专项方案审批项

```json
{
  "id": 1,
  "projectId": 1001,
  "riskPointId": 1,
  "planCode": "SP-001",
  "planName": "高边坡专项施工方案",
  "riskLevel": "重大",
  "approvalStatus": "已审批",
  "approvalDate": "2026-08-05",
  "approvalFileId": 900001,
  "approvalFile": {
    "id": 900001,
    "fileCode": "FILE-202607-0001",
    "originalName": "专项方案审批文件.pdf",
    "fileExt": "pdf",
    "mimeType": "application/pdf",
    "fileSize": 102400,
    "uploadTime": "2026-07-15 11:12:25",
    "parseStatus": "WAIT_CONFIRM"
  },
  "sourceDocRef": "DOC-2026-001",
  "dataNature": "demo",
  "isDemo": true,
  "createdAt": "2026-08-05 10:00:00",
  "updatedAt": "2026-08-05 10:00:00"
}
```

文件不存在或已删除时：审批记录仍返回，`approvalFile` 为 `null`。

### 4.4 错误响应（约定）

| HTTP | 场景 |
|---|---|
| 400 | 参数缺失、格式错误、成对校验失败、试图 PATCH 禁止字段 |
| 404 | 记录不存在 |
| 405 | 专项方案 DELETE（禁止物理删除） |
| 409 | `(projectId, planCode)` 唯一冲突 |
| 422 | 外键不存在（风险源/用户/文件） |

---

## 5. 数据库映射

> 映射对象以已批准的 V0.4 DDL（`database/migration/v0.4/V0.4_database_migration.sql`）为准。  
> **DDL 尚未执行前不得编码依赖这些字段/表的写入路径。**

### 5.1 `e_rectification_task`

| API 字段 | 数据库字段 | 类型 | 备注 |
|---|---|---|---|
| `id` | `id` | BIGINT | |
| `taskCode` | `task_code` | VARCHAR(80) | 只读 |
| `title` | `title` | VARCHAR(255) | 只读 |
| `taskStatus` | `task_status` | VARCHAR(30) | 本接口只读，不改 |
| `deadline` | `deadline` | DATETIME(6) | 只读 |
| `rectificationCompletedDate` | `rectification_completed_date` | DATE NULL | PATCH 可写；禁止自动填充 |
| `rectificationCompletedBy` | `rectification_completed_by` | BIGINT NULL | PATCH 可写；FK → `user_account.id` |
| `dataNature` | `data_nature` | VARCHAR(20) | 只读 |
| `isDemo` | `is_demo` | TINYINT(1) | 只读 |

明确无关映射：

| 禁止来源 | 禁止目标 |
|---|---|
| `e_closure_case.closed_at` | `rectification_completed_date` |
| 服务端当前时间 | `rectification_completed_date` |

### 5.2 `special_plan_approval`

| API 字段 | 数据库字段 | 类型 | 备注 |
|---|---|---|---|
| `id` | `id` | BIGINT | |
| `projectId` | `project_id` | BIGINT | POST 必填；PATCH 禁止改 |
| `riskPointId` | `risk_point_id` | BIGINT | FK → `safety_risk_point.id`；PATCH 禁止改 |
| `planCode` | `plan_code` | VARCHAR(80) | 与 project 唯一；PATCH 禁止改 |
| `planName` | `plan_name` | VARCHAR(255) | PATCH 可改 |
| `riskLevel` | `risk_level` | VARCHAR(50) | PATCH 可改 |
| `approvalStatus` | `approval_status` | VARCHAR(40) | PATCH 可改 |
| `approvalDate` | `approval_date` | DATE NULL | PATCH 可改；不自动生成 |
| `approvalFileId` | `approval_file_id` | BIGINT NULL | PATCH 可改；FK → `file_asset.id` |
| `sourceDocRef` | `source_doc_ref` | VARCHAR(255) NULL | PATCH 可改 |
| `dataNature` | `data_nature` | VARCHAR(20) | POST 可选 |
| `isDemo` | `is_demo` | TINYINT(1) | POST 可选 |
| `createdAt` | `created_at` | DATETIME | 只读 |
| `updatedAt` | `updated_at` | DATETIME | 只读（库侧 ON UPDATE） |

### 5.3 文件关联（只读 JOIN）

```sql
LEFT JOIN file_asset f
  ON f.id = spa.approval_file_id
 AND f.is_deleted = 0
```

只返回文件元数据；不修改上传、解析、归档流程。

---

## 6. 权限要求

| 操作 | 建议权限 | 备注 |
|---|---|---|
| 查询整改任务 | 项目查看 / ESG 业务查看 | 只读 |
| PATCH 整改完成字段 | 甲方填报人员、项目 ESG 管理人员 | 不得伪造填报人 |
| 查询专项方案 | 项目查看 / 治理合规查看 | 只读 |
| POST 专项方案 | 项目 ESG 管理员、治理合规录入 | 写入审批事实 |
| PATCH 专项方案 | 项目 ESG 管理员、治理合规审核 | 仅状态/信息/文件关联 |
| DELETE 专项方案 | **所有角色禁止** | 合规证据链，物理删除一律拒绝 |

当前 `app.py` 未见独立认证中间件。编码阶段：

- 不新增整套认证系统；
- 复用现有部署层或上游认证上下文；
- 无可用身份上下文时，写接口不得伪造用户放行。

---

## 7. 回归测试方案

> 以下测试在 **数据库迁移完成且结构核验通过之后**、API 编码落地时执行。  
> 当前阶段仅确认方案，不执行接口测试、不改代码。

### 7.1 静态检查

1. `python -m compileall -q backend`
2. 首页 KPI 路由与 `get_dashboard_kpis` 未被改动
3. `/api/workspace/files/upload` 未被改动
4. 仓库中无针对 `special_plan_approval` 的物理删除 SQL
5. API 实现未引入额外 DDL（无新表、无新字段脚本）

### 7.2 整改任务接口

| # | 用例 | 期望 |
|---|---|---|
| R1 | GET 列表/详情 | 返回 `rectificationCompletedDate` / `rectificationCompletedBy` |
| R2 | PATCH 仅日期 | 只更新日期列 |
| R3 | PATCH 仅完成人 | 只更新完成人列（日期已存在时） |
| R4 | PATCH 日期非空且完成人为空 | 拒绝（成对校验） |
| R5 | PATCH 不存在的用户 ID | 拒绝 |
| R6 | 代码/SQL 路径检查 | 不读取 `closed_at` 写入完成日期 |
| R7 | 空 body / 非法字段 | 拒绝；不改状态与关闭时间 |
| R8 | 确认无自动 `CURRENT_DATE`/`NOW()` 填充 | 通过 |

### 7.3 专项方案接口

| # | 用例 | 期望 |
|---|---|---|
| S1 | GET 列表、详情、过滤 | 正常 |
| S2 | POST 有效风险源 | 创建成功 |
| S3 | POST 无效 `riskPointId` | 拒绝 |
| S4 | POST 无效/已删 `approvalFileId` | 拒绝 |
| S5 | PATCH 审批状态/日期/文件关联 | 成功 |
| S6 | PATCH `projectId`/`riskPointId`/`planCode` | 拒绝 |
| S7 | 重复 `(projectId, planCode)` | 409 |
| S8 | DELETE | **405**，行数不变，无 DELETE SQL |

### 7.4 回归保护（V0.3 基线）

| # | 用例 | 期望 |
|---|---|---|
| P1 | `GET /api/dashboard/kpis` | 12 项结构与业务事实不变 |
| P2 | E04 / S01 / S03 / G 组首页表达 | 与 V0.3 冻结一致 |
| P3 | `POST /api/workspace/files/upload` | 行为不变 |
| P4 | 表/字段/视图数量 | 仅等于已批准 V0.4 迁移结果，无额外漂移 |
| P5 | 重点表数据量抽样 | 非本接口写入表无意外变更 |

---

## 8. 编码启动门禁

必须同时满足后，方可开始 API 编码：

1. [ ] 人工确认本文件（V0.4 API 开发边界）已批准；
2. [ ] V0.4 数据库 DDL 已在目标库执行成功；
3. [ ] 结构核验：`e_rectification_task` 两字段、`special_plan_approval` 表/索引/外键齐全；
4. [ ] 确认未改首页 KPI、未改上传接口、未追加未批准 DDL。

**门禁未通过前：只维护文档，不修改 `backend/` 业务代码。**

---

## 9. 未完成事项

- 数据库 DDL 尚未执行（本文件以该前提为准）；
- API 代码尚未修改；
- PATCH 方法尚未在 `app.py` 中实现；
- 认证/角色映射尚未接入；
- 专项方案 Demo/正式业务数据尚未录入；
- G04 CHECK 域约束扩展仍按数据库文档单独审批，不在本 API 文档范围。

---

*本文件仅更新 API 设计与边界说明；未修改业务代码、页面、样式、首页 KPI、指标口径、文件上传接口或数据库结构。*
