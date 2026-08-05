# 工作台跨页面状态刷新说明 V0.9

## 1. 本轮目标

补齐数据上传工作台各页面之间的轻量状态联动，避免用户完成审核、补正、入库后必须手动刷新页面。

覆盖范围：

- P01 工作台首页；
- P02 我的上传任务；
- P03 ESG 智能入库；
- P04 审核结果；
- P05 资料中心与档案；
- S01 任务办理中央弹窗。

## 2. 新增前端刷新事件

新增文件：

```text
src/utils/workspaceRefresh.ts
```

提供：

- `emitWorkspaceRefresh(payload)`
- `onWorkspaceRefresh(handler)`

事件名称：

```text
workspace:data-refresh
```

刷新范围：

```ts
type WorkspaceRefreshScope =
  | 'summary'
  | 'tasks'
  | 'reviews'
  | 'documents'
  | 'parse-queue'
```

## 3. 页面监听逻辑

### P01 工作台首页

监听：

- `summary`
- `tasks`

触发后重新加载：

- `getWorkspaceSummary()`
- `getWorkspaceTasks()`

### P02 我的上传任务

监听：

- `summary`
- `tasks`

触发后：

- 若当前存在筛选条件，保留筛选条件重新查询；
- 否则重新加载默认任务列表。

### P03 ESG 智能入库

监听：

- `parse-queue`

触发后重新加载解析队列。

确认入库并关联成功后广播：

- `summary`
- `tasks`
- `documents`
- `parse-queue`

### P04 审核结果

监听：

- `reviews`

触发后重新加载审核列表和当前右侧详情。

审核通过 / 审核退回成功后广播：

- `summary`
- `tasks`
- `reviews`

### P05 资料中心与档案

监听：

- `documents`

触发后重新加载资料中心状态卡和资料列表。

### S01 任务办理中央弹窗

关联资料成功后广播：

- `summary`
- `tasks`

提交审核 / 重新提交审核成功后广播：

- `summary`
- `tasks`
- `reviews`

## 4. 动态任务 ID 打开修复

原问题：

`WorkspacePage.vue` 打开 S01 弹窗时，只能从本地 mock `uploadTasks` 中查找任务。

后端新增的任务、自动化测试生成的任务、或智能入库/审核流转产生的新任务 ID，可能无法打开 S01 弹窗。

修复方式：

- 如果本地 mock 找不到任务，仍使用该 `taskId` 构造一个最小占位任务；
- S01 弹窗打开后调用 `getTaskDetail(taskId)`；
- 弹窗标题、状态、周期、进度等优先使用 API 返回的真实任务详情。

## 5. P04 进入补正 taskId 修复

后端 `GET /api/workspace/reviews` 已增加：

```json
{
  "taskId": "xxx"
}
```

P04 “进入补正”优先使用审核记录中的真实 `taskId`，不再只依赖 mock 映射。

## 6. 验证结果

完整回归已通过：

- `server/smoke_test.py`
- `server/mysql_smoke_test.py`
- `server/submit_review_flow_test.py`
- `server/review_action_flow_test.py`
- `server/confirm_updates_task_test.py`
- `server/parse_rule_dedup_test.py`
- `server/multipart_upload_test.py`
- `server/ingestion_api_test.py`
- `vue-tsc -b`
- `vite build`

## 7. 当前仍可优化

当前跨页面刷新使用轻量事件机制，适合原型联调阶段。

后续如果项目进入正式前端工程化阶段，可考虑升级为：

- Pinia 全局 store；
- 请求缓存与失效机制；
- 页面级 loading 状态；
- 操作后局部 optimistic update。

