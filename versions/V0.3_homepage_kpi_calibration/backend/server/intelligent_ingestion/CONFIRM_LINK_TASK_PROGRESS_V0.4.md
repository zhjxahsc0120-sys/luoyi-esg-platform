# 罗宜高速 ESG 智能入库确认后任务进度回写说明 V0.4

本说明补充 P03 “确认入库并关联”后的任务回写行为。

## 1. 触发接口

```http
POST /api/workspace/parse-jobs/{jobId}/confirm
```

当 `acceptedCandidateIds` 不为空时，后端会对每个候选任务执行：

1. 创建 `document_record`；
2. 创建 `document_version`；
3. 创建 `document_task_relation`；
4. 将 `task_match_candidate.candidate_status` 更新为 `ACCEPTED`；
5. 匹配并更新 `upload_task_requirement.status = 已关联`；
6. 重算 `upload_task.progress_current / progress_total`；
7. 追加 `task_review_timeline` 记录。

## 2. 资料要求匹配规则

优先级：

1. 显式传入 `requirementId`；
2. 用资料名称、候选任务名称、资料类型匹配任务要求项名称；
3. 若没有精确匹配，选择当前任务第一个未完成要求项；
4. 匹配成功后标记为 `已关联`。

这样可以避免“资料已关联但任务完整度不变化”的问题。

## 3. 返回结构补充

确认入库响应增加：

```json
{
  "linkedTasks": [
    {
      "taskId": "t1",
      "taskName": "2026年7月水保监测月报",
      "requirementId": "td7",
      "requirementName": "审核确认单",
      "progress": {
        "completed": 7,
        "missing": 0,
        "abnormal": 0,
        "total": 7,
        "canSubmit": true
      }
    }
  ]
}
```

## 4. 自动化验证

新增测试：

```powershell
python server/confirm_updates_task_test.py
```

覆盖：

- 确认入库后生成任务关联；
- 匹配资料要求项；
- 要求项状态更新为 `已关联`；
- 任务进度同步重算。
