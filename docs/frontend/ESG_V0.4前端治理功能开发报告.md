# ESG V0.4 前端治理功能开发报告

| 项 | 内容 |
|---|---|
| 文档版本 | V1.0 |
| 日期 | 2026-08-05 |
| 范围 | 工作台治理整改 + 专项方案；消费既有 V0.4 API |
| 禁区遵守 | **未改**首页、KPI 口径、主题样式、dashboard/KPI API、文件上传接口契约 |

---

## 1. 修改文件

| 文件 | 变更 |
|---|---|
| `frontend/src/types/governance.ts` | **新增** V0.4 治理类型 |
| `frontend/src/services/api.ts` | **新增** `apiPatch` / `apiMutate`、整改与专项方案 API；**未改** dashboard/KPI 既有函数 |
| `frontend/src/components/workspace/WorkspaceGovernanceRectification.vue` | **新增** 治理整改页 |
| `frontend/src/components/workspace/WorkspaceSpecialPlans.vue` | **新增** 专项方案页 |
| `frontend/src/components/workspace/WorkspaceNav.vue` | 增加「治理整改」「专项方案」Tab |
| `frontend/src/views/WorkspacePage.vue` | 挂载两个新 Tab；二级导航始终可见以便切换 |
| `docs/frontend/ESG_V0.4前端治理功能开发报告.md` | 本报告 |

未修改：`DashboardPage.vue`、`kpi-catalog.ts`、`dashboard.store.ts`、首页样式、`/api/dashboard/*` 调用逻辑。

---

## 2. 页面说明

### 2.1 入口

- 路由仍为 `/#/workspace`
- 深链：
  - `/#/workspace?t=governance-rectification` → 治理整改
  - `/#/workspace?t=special-plans` → 专项方案
- 工作台二级导航新增两项，沿用现有深色 Tab 样式（未引入 UI 框架）

### 2.2 治理整改

| 能力 | 说明 |
|---|---|
| 列表 | 展示任务编号、标题、状态、完成日期 |
| 详情 | 右侧详情面板 |
| 填报 | 仅 PATCH `rectificationCompletedDate`、`rectificationCompletedBy` |
| 空值展示 | 完成日期为空时显示 **「待甲方填报」** |
| 禁止 | 不使用当前日期自动填充；日期非空时前端要求同时填写填报人 ID |

Demo 填报人：当前库可用 `user_account.id = 10001`。

### 2.3 专项方案审批

| 能力 | 说明 |
|---|---|
| 列表 | 方案编号、名称、风险等级、审批状态、文件 |
| 新增 | POST 必填字段；风险源下拉来自 `GET /api/social/s02/risks` |
| 编辑 | PATCH 审批状态/信息/文件关联；不可改 projectId/riskPointId/planCode |
| 文件关联 | 复用既有 `uploadWorkspaceBinaryFile` → 写入 `approvalFileId`；支持解除关联（null） |
| 禁止 | **无删除按钮**；不调用 DELETE |

联调中已成功创建 Demo 记录：`planCode=SP-FE-001`（id=950100）。

---

## 3. API 调用

| 前端方法 | HTTP | 路径 |
|---|---|---|
| `getRectificationTasks` | GET | `/api/governance/rectification-tasks` |
| `getRectificationTask` | GET | `/api/governance/rectification-tasks/{id}` |
| `patchRectificationTask` | PATCH | `/api/governance/rectification-tasks/{id}` |
| `getSpecialPlans` | GET | `/api/governance/special-plans` |
| `getSpecialPlan` | GET | `/api/governance/special-plans/{id}` |
| `createSpecialPlan` | POST | `/api/governance/special-plans` |
| `patchSpecialPlan` | PATCH | `/api/governance/special-plans/{id}` |
| `apiPatch` | PATCH | 通用封装（治理写操作用） |

文件上传仍走既有：

- `POST /api/workspace/files/upload`（`uploadWorkspaceBinaryFile`）

---

## 4. 测试结果

### 4.1 静态检查

```text
npm.cmd run check --prefix frontend
→ vue-tsc -b 通过
```

### 4.2 接口联调（对运行中 `127.0.0.1:8765`）

| 用例 | 结果 |
|---|---|
| GET 整改任务列表 | 200，total=3 |
| PATCH 完成日期 + 填报人 10001 | 200 |
| PATCH 清空完成日期/填报人 | 200，界面可回到「待甲方填报」 |
| POST 专项方案 SP-FE-001 / riskPointId=430001 | 201 |
| GET 专项方案详情 | 200 |
| GET `/api/dashboard/kpis` | 200，仍为 12 项 E01–G04 |

### 4.3 前端使用说明（人工点验建议）

1. 打开 `http://localhost:5173/#/workspace?t=governance-rectification`
2. 选择任务 → 填写日期与 `10001` → 保存 → 刷新确认
3. 打开 `?t=special-plans` → 新增/编辑/上传关联 → 确认无删除入口
4. 打开首页 `/#/` → 确认布局与 12 KPI 未变

---

## 5. 首页回归

| 检查项 | 结果 |
|---|---|
| 首页路由 `/` / `DashboardPage` | 未修改 |
| KPI catalog / store bootstrap | 未修改 |
| `getDashboardKpis` / `getDashboardKpiDetail` 等 | 未改动签名与路径 |
| 主题 / tokens / dashboard.scss | 未修改 |
| 运行时 KPI 接口 | 仍返回 12 项 |

---

## 6. 已知说明

1. 工作台默认仍可能停在「ESG智能入库」；二级导航已常显，可直接点「治理整改 / 专项方案」。
2. 专项方案列表初始可为 0；创建后依赖真实 `safety_risk_point` 与 `file_asset` 外键。
3. 填报人必须是真实 `user_account.id`；无效 ID 由后端 400 拒绝，前端展示错误信息。
4. 本轮未改 Codex/后端；仅前端消费已稳定 API。

---

## 7. 状态

| 项 | 状态 |
|---|---|
| 第一阶段前端治理能力 | ✅ 已完成 |
| 首页 / KPI / 主题 | ✅ 未改动 |
| 下一步 | 可按需做浏览器点验、Demo 数据补充或 S03 非首页只读页 |

*报告对应代码变更仅限上表文件；后端 API 由既有 V0.4 实现提供。*
