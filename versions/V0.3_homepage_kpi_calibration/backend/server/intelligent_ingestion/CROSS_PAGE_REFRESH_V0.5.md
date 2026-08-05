# 罗宜高速 ESG 智能入库跨页面联动说明 V0.5

本说明补充 P03 “确认入库并关联”后，工作台其他页面的数据联动口径。

## 1. P03 ESG 智能入库

确认入库成功后，页面提示会展示：

- 生成的 `DocumentID`；
- 关联任务数量；
- 每个被关联任务名称；
- 匹配到的资料要求项；
- 最新资料完整度，例如 `6/7`。

示例：

```text
资料已入库并关联 1 个任务。DocumentID：930120。
2026年7月水保监测月报：审核确认单（完整度 6/7）
```

## 2. P01 工作台首页

P01 任务列表来自：

```http
GET /api/workspace/tasks
```

确认入库后，后端会更新 `upload_task.progress_current / progress_total`。用户返回工作台首页时，任务列表展示最新资料进度。

## 3. P02 我的上传任务

P02 与 P01 使用同一任务接口：

```http
GET /api/workspace/tasks
GET /api/workspace/tasks/{taskId}/detail
```

确认入库后：

- 任务列表资料进度同步变化；
- 任务弹窗资料要求项显示为 `已关联`；
- 校验问题随完整性重算减少。

## 4. P05 资料中心与档案

P05 资料列表来自：

```http
GET /api/workspace/documents
GET /api/workspace/documents/summary
```

确认入库后：

- 新资料出现在资料列表顶部；
- 资料总数在演示基准 `368` 基础上随新增资料增加；
- 本月新增在演示基准 `24` 基础上随新增资料增加；
- 资料详情可读取 `file_asset`、`document_record`、`document_version` 和 `document_task_relation`。

## 5. P04 审核结果

确认入库不会自动进入审核流。

只有调用：

```http
POST /api/workspace/tasks/{taskId}/submit
```

且完整性校验通过后，才创建 `review_record`。因此 P03 入库只解决资料准备，不替代提交审核。

## 6. 自动化验证

相关测试：

```powershell
python server/confirm_updates_task_test.py
python server/smoke_test.py
```

覆盖：

- 确认入库回写任务要求项；
- P02 任务详情可见更新；
- P05 资料列表可见新增资料；
- P04 审核流不被误触发。
