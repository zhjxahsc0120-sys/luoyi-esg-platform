# ESG V0.4 API开发完成报告

## 1. 开发结论

- API开发状态：完成
- 数据库结构：未修改
- 数据库数据：本次验证未产生业务写入
- 首页 KPI：未修改
- 文件上传接口：未修改
- 专项方案物理删除：禁止
- 当前后端：`C:\ESG_Project\backend`
- API地址：`http://127.0.0.1:8765`

## 2. 修改文件

### 已修改

1. `C:\ESG_Project\backend\app.py`
   - 新增 V0.4 整改任务和专项方案路由；
   - 增加 PATCH 处理；
   - 明确专项方案 DELETE 返回 405；
   - 将 MySQL-first 模式下对缺失本地 SQLite 文件的阻断条件调整为：SQLite 和 MySQL 均不可用时才阻断。

2. `C:\ESG_Project\backend\mysql_api.py`
   - 新增整改任务查询、详情和字段更新函数；
   - 新增专项方案查询、详情、新增和修改函数；
   - 增加审批文件元数据关联查询；
   - 未调用首页 KPI 组装逻辑。

### 新增

3. `C:\ESG_Project\backend\v0_4_api_test.py`
   - 新增 V0.4 数据库结构、只读查询、字段校验和 KPI 形状测试；
   - 测试不执行业务数据 INSERT、UPDATE、DELETE。

## 3. API列表

| 方法 | 路径 | 结果 |
|---|---|---|
| GET | `/api/governance/rectification-tasks` | 已实现 |
| GET | `/api/governance/rectification-tasks/{id}` | 已实现 |
| PATCH | `/api/governance/rectification-tasks/{id}` | 已实现，仅允许两个整改完成字段 |
| GET | `/api/governance/special-plans` | 已实现，支持项目、风险源、状态、等级和 Demo 过滤 |
| GET | `/api/governance/special-plans/{id}` | 已实现，包含 `approvalFile` |
| POST | `/api/governance/special-plans` | 已实现，包含风险源和文件有效性校验 |
| PATCH | `/api/governance/special-plans/{id}` | 已实现，支持审批信息、状态和文件关联修改 |
| DELETE | `/api/governance/special-plans/{id}` | 明确禁止，返回 HTTP 405 |

### 整改任务字段边界

PATCH 只允许：

- `rectificationCompletedDate`
- `rectificationCompletedBy`

没有自动生成完成时间的逻辑，也没有读取 `closed_at` 的逻辑。

### 专项方案字段边界

PATCH 允许修改：

- `planName`
- `riskLevel`
- `approvalStatus`
- `approvalDate`
- `approvalFileId`
- `sourceDocRef`

项目、风险源、方案编码和数据性质不可修改。传入 `approvalFileId: null` 只解除关联，不删除文件。

## 4. 数据库映射与关联

- `rectificationCompletedDate` → `e_rectification_task.rectification_completed_date`
- `rectificationCompletedBy` → `e_rectification_task.rectification_completed_by`
- 专项方案数据 → `special_plan_approval`
- `approvalFileId` → `special_plan_approval.approval_file_id`
- 文件元数据 → `file_asset`
- 风险源校验 → `safety_risk_point.id`
- 完成人校验 → `user_account.id`

文件查询使用 `file_asset.is_deleted = 0`。已删除文件不会被物理恢复，专项方案记录仍保留。

## 5. 测试结果

### 5.1 编译和单元测试

- `app.py`、`mysql_api.py`、`v0_4_api_test.py` Python 编译：通过；
- V0.4 测试：6 项通过；
- 数据库结构字段检查：通过；
- 整改任务只读查询：通过；
- 专项方案只读查询和文件结构检查：通过；
- 非法新增和非法更新参数校验：通过。

### 5.2 HTTP验证

| 请求 | 结果 |
|---|---|
| GET 整改任务列表 | HTTP 200，返回 3 条 |
| GET 专项方案列表 | HTTP 200，当前 0 条 |
| GET 不存在专项方案 | HTTP 404 |
| PATCH 整改任务传入禁止字段 | HTTP 400 |
| POST 专项方案缺少必填字段 | HTTP 400 |
| POST 专项方案使用不存在风险源 | HTTP 400，数据库记录数保持 0 |
| PATCH 专项方案修改不可变项目字段 | HTTP 400 |
| DELETE 专项方案 | HTTP 405，禁止物理删除 |

本次没有执行成功路径的 POST/PATCH 写入测试，避免向当前 Demo 数据库增加测试业务记录。

## 6. 首页 KPI回归

`GET /api/dashboard/kpis` 与 V0.3 快照逐项比对一致：

- KPI 数量：12 项；
- E04：`0处`；
- S03：`100%`；
- G04：`正常`；
- 其余 KPI 名称、数值、单位、描述和风险等级未变化。

## 7. 数据库和接口保护检查

- 未执行 CREATE TABLE、ALTER TABLE、DROP TABLE；
- 未执行历史数据 UPDATE；
- 未执行业务数据 INSERT；
- 未执行物理 DELETE；
- 未修改 `/api/dashboard/kpis`；
- 未修改 `/api/workspace/files/upload`；
- 未新增字段或表。

## 8. 待确认事项

1. 当前认证中间件和角色上下文仍未在 `app.py` 中发现；正式部署前需接入既有认证网关或权限上下文，不能由 API 伪造用户身份。
2. 成功路径 POST/PATCH 需要在隔离数据库或人工批准的 Demo 批次中验证，当前环境未写入测试记录。
3. `rectification_completed_date` 在“提交复核前必须填写”的流程校验尚未接入，本次仅提供字段读写，不自动改变任务状态。
4. G04 CHECK 域约束扩展仍是独立事项，本次 API 未处理。

## 9. 当前运行状态

- MySQL：`127.0.0.1:3307`，正常；
- Python API：`127.0.0.1:8765`，健康检查正常；
- 当前代码入口：`C:\ESG_Project\backend\app.py`；
- 当前首页 KPI 回归：通过。
