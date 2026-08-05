# P04 审核处理闭环说明 V0.7

## 1. 本轮目标

在已有“提交审核”链路基础上，补齐 P04 审核结果页的后端处理能力：

- 审核通过；
- 审核退回；
- 退回时生成补正要求；
- 审核轨迹自动追加；
- 任务状态同步回写；
- 工作台状态卡同步刷新。

本轮仅完成后端接口和 API 封装，不改 P04 页面视觉布局。

## 2. 新增接口

### POST /api/workspace/reviews/{reviewId}/approve

用途：审核通过。

示例请求：

```json
{
  "reviewer": "项目审核人",
  "comment": "资料完整，审核通过"
}
```

成功后：

- `review_record.status = 已通过`
- `review_record.next_step = 查看结果`
- `upload_task.status = 已完成`
- `upload_task.next_step = 查看结果`
- `review_timeline` 追加“审核通过”
- `task_review_timeline` 追加“审核通过”
- `workspace_summary` 同步刷新

示例响应：

```json
{
  "ok": true,
  "reviewId": "xxx",
  "taskId": "xxx",
  "status": "已通过",
  "taskStatus": "已完成",
  "message": "审核已通过，任务已完成"
}
```

### POST /api/workspace/reviews/{reviewId}/return

用途：审核退回并生成补正要求。

示例请求：

```json
{
  "reviewer": "项目审核人",
  "comment": "附件签章和日期信息需补正",
  "requirements": [
    "请补充工资支付凭证签章页。",
    "请重新上传附件日期清晰的扫描件。"
  ]
}
```

成功后：

- `review_record.status = 已退回`
- `review_record.next_step = 进入补正`
- `upload_task.status = 待补正`
- `upload_task.next_step = 继续补正`
- `review_requirement` 写入补正要求
- `review_timeline` 追加“审核退回”
- `task_review_timeline` 追加“审核退回”
- `workspace_summary` 同步刷新

示例响应：

```json
{
  "ok": true,
  "reviewId": "xxx",
  "taskId": "xxx",
  "status": "已退回",
  "taskStatus": "待补正",
  "message": "审核已退回，任务已转入待补正",
  "requirements": [
    "请补充工资支付凭证签章页。",
    "请重新上传附件日期清晰的扫描件。"
  ]
}
```

## 3. 状态保护

仅 `待审核` 状态允许执行审核通过或审核退回。

如果记录已经是 `已通过` 或 `已退回`，接口返回：

```json
{
  "ok": false,
  "message": "该审核记录当前状态不可重复审核"
}
```

或：

```json
{
  "ok": false,
  "message": "该审核记录当前状态不可退回"
}
```

前端应展示页面内轻量提示，不跳转、不强制刷新整页。

## 4. 前端 API 封装

已在 `src/services/api.ts` 新增：

- `approveReview(reviewId, payload)`
- `returnReview(reviewId, payload)`
- `ReviewActionResponse`

Trae 后续只需在 P04 审核结果右侧详情区绑定按钮。

## 5. 建议 Trae 绑定方式

P04 页面右侧当前选中审核记录：

- 当 `status === '待审核'` 时显示两个按钮：
  - 次要按钮：审核退回
  - 主要按钮：审核通过
- 当 `status !== '待审核'` 时不显示处理按钮，只保留查看轨迹和补正要求。

按钮逻辑：

1. 点击“审核通过”
   - 调用 `approveReview(selectedRecordId, { reviewer: '项目审核人', comment: '资料完整，审核通过' })`
   - 成功后重新加载：
     - `getReviews()`
     - `getReviewDetail(selectedRecordId)`
     - `getReviewTimeline(selectedRecordId)`
     - `getReviewRequirements(selectedRecordId)`
   - 页面内提示接口 `message`

2. 点击“审核退回”
   - 可先用固定原型补正要求：
     - `请补充资料签章页。`
     - `请重新上传日期清晰的扫描件。`
   - 调用 `returnReview(selectedRecordId, { reviewer, comment, requirements })`
   - 成功后同样刷新列表和右侧详情
   - 页面内提示接口 `message`

本阶段不建议新增复杂表单弹窗；先用轻量确认或页面内小面板即可。

## 6. 验证脚本

新增：

- `server/review_action_flow_test.py`

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

## 7. 当前停止点

后端能力已经具备，下一步需要 Trae 在 P04 页面上补审核处理按钮和页面内提示。

