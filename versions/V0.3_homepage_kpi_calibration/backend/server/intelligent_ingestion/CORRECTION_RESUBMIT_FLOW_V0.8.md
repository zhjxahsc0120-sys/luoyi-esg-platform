# 审核退回补正再提交闭环说明 V0.8

## 1. 本轮目标

在 V0.7 “审核通过 / 审核退回”基础上，补齐退回后的补正再提交闭环：

- 审核退回后，任务进入“待补正”；
- 退回审核记录生成补正要求；
- 上传用户在 S01 任务办理弹窗中补正后可再次提交；
- 再次提交时，上一轮退回审核记录的补正要求自动标记为“已补正”；
- 上一轮退回审核轨迹追加“补正提交”；
- 系统生成新一轮“待审核”审核记录；
- 工作台摘要状态卡按当前数据库状态刷新。

## 2. 后端逻辑变化

### 2.1 submit_task_review 增强

接口：

```http
POST /api/workspace/tasks/{taskId}/submit
```

当任务状态为“待补正”，且资料校验通过时：

1. 查找该任务最近一条 `已退回` 审核记录；
2. 将该审核记录下的 `review_requirement.requirement_status` 更新为 `已补正`；
3. 向该审核记录的 `review_timeline` 追加：

```text
补正提交（任务资料已重新提交审核）
```

4. 创建新一轮 `review_record`，状态为 `待审核`；
5. 将任务状态更新为 `审核中`；
6. 刷新工作台摘要。

### 2.2 补正要求字段兼容

`GET /api/workspace/reviews/{reviewId}/requirements` 现在同时返回：

```json
{
  "requirement": "请补充资料签章页。",
  "requirementText": "请补充资料签章页。",
  "status": "待补正"
}
```

其中：

- `requirement` 兼容后端测试脚本；
- `requirementText` 兼容 P04 前端展示；
- `status` 用于区分 `待补正 / 已补正`。

## 3. 工作台摘要刷新口径修正

之前摘要刷新使用“历史当前值”和数据库状态取最大值，可能导致 `underReview` 只增不降。

现已修正为：

- 待上传：`max(12, 当前待上传任务数)`
- 待补正：`max(3, 当前待补正任务数)`
- 待提交：`max(5, 当前待提交任务数)`
- 审核中：`max(3, 当前审核中任务数)`
- 已完成：`max(36, 当前已完成 + 已归档任务数)`
- 当前待办：`max(27, 待上传 + 待补正 + 待提交 + 审核中)`

这样既保留原型基线，又允许真实业务状态流转后回落。

## 4. 验证脚本

已扩展：

- `server/review_action_flow_test.py`

覆盖：

1. 审核通过；
2. 审核退回；
3. 生成补正要求；
4. 退回任务再次提交；
5. 旧补正要求标记为“已补正”；
6. 旧审核轨迹追加“补正提交”；
7. 新审核记录进入“待审核”；
8. P04 审核列表可见新旧记录。

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

## 5. 下一步建议

后端退回补正再提交链路已经具备。

下一步可以推进：

1. P01 / P02 / P04 在操作成功后做跨页面局部刷新；
2. S01 任务弹窗中展示“上一轮补正要求状态”；
3. P04 右侧补正要求增加状态标签：待补正 / 已补正；
4. 若要进入更真实业务，可增加审核人、审核意见、补正截止时间的可编辑输入。

