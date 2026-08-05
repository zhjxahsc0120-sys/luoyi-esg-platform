# S01 任务提交审核闭环说明 V0.6

## 1. 本轮目标

在已有“任务办理中央弹窗 S01”和“审核结果 P04”的基础上，补齐后端提交审核闭环：

- 资料完整且校验通过的任务可以提交审核；
- 提交后任务状态进入“审核中”；
- P04 审核结果列表可以看到新增审核记录；
- P04 右侧审核轨迹可以展示提交与系统校验节点；
- 重复提交同一审核中任务时不重复创建审核记录，而是复用现有待审核记录；
- 资料缺失或格式异常时，接口返回 `ok:false`，前端展示轻量提示。

## 2. 关键接口

### POST /api/workspace/tasks/{taskId}/submit

用途：提交资料任务进入审核流程。

主要逻辑：

1. 读取任务资料要求完整性；
2. 存在“缺失”或“格式异常”时，返回 `ok:false`；
3. 任务已经处于“审核中”且已有待审核记录时，返回既有 `reviewId`，避免重复建单；
4. 校验通过后：
   - 新增 `review_record`；
   - 更新 `upload_task.status = 审核中`；
   - 更新 `upload_task.next_action = 查看进度`；
   - 写入 `task_timeline`；
   - 写入 `review_timeline`。

## 3. 审核轨迹默认节点

成功提交后，系统默认生成两类轨迹：

| 节点 | 含义 |
| --- | --- |
| 提交审核 | 上传用户完成资料提交，任务进入审核流程 |
| 完整性校验 | 系统对资料完整性和格式进行校验 |

后续如扩展“审核通过 / 审核退回 / 补正确认”，可继续追加 `review_timeline` 节点。

## 4. P04 联动效果

P04 仍使用以下接口：

- `GET /api/workspace/reviews`
- `GET /api/workspace/reviews/{reviewId}`
- `GET /api/workspace/reviews/{reviewId}/timeline`
- `GET /api/workspace/reviews/{reviewId}/requirements`

提交审核成功后：

- 审核记录列表新增或展示对应任务；
- 状态为“待审核”；
- 审核人为“待分配”；
- 右侧轨迹展示“提交审核 / 完整性校验”。

## 5. 数据量测试口径调整

由于当前后端已经进入可写联调阶段，智能入库和提交审核会新增任务、资料、审核记录。

因此冒烟测试不再断言固定总数，而是断言不少于初始化基线：

- 上传任务数量不少于 12；
- 审核记录数量不少于 7；
- 资料中心资料数量不少于 368；
- AI 解析任务数量不少于 3。

这样既能保证初始化数据完整，又不会因为正常业务写入导致测试误报。

## 6. 验证脚本

本轮重点脚本：

- `server/submit_review_flow_test.py`
- `server/confirm_updates_task_test.py`
- `server/smoke_test.py`
- `server/mysql_smoke_test.py`

完整验证命令示例：

```powershell
$env:PYTHONIOENCODING='utf-8'
python server\smoke_test.py
python server\mysql_smoke_test.py
python server\submit_review_flow_test.py
python server\confirm_updates_task_test.py
python server\parse_rule_dedup_test.py
python server\multipart_upload_test.py
python server\ingestion_api_test.py
npm run check
npm run build
```

## 7. 下一步建议

下一阶段可推进“审核处理闭环”：

1. P04 新增审核通过 / 审核退回后端接口；
2. 审核通过后任务进入“已完成”，资料归档状态更新；
3. 审核退回后任务回到“待补正”，生成补正要求；
4. P02 / P01 / P04 状态卡同步刷新；
5. 审核轨迹补齐“审核通过 / 审核退回 / 补正提交 / 复核完成”节点。

