# 罗宜高速 ESG 前后端接口契约 V0.2

后端基址：

```text
http://127.0.0.1:8765
```

## V0.5 增量：最终联调口径修正

### P02 cycleType 兼容口径

`GET /api/workspace/tasks` 的 `cycleType` 同时兼容中文值和前端枚举值：

```text
月度 / MONTHLY / MONTH
季度 / QUARTERLY / QUARTER
年度 / ANNUAL / YEARLY
一次性 / ONCE / ONE_TIME
```

### S01 候选资料字段增强

`GET /api/workspace/tasks/{taskId}/detail` 的 `candidateDocuments` 新增：

```json
{
  "id": "c1",
  "documentId": "930001",
  "requirementId": "td5",
  "name": "弃渣场巡查记录_2026-07.pdf",
  "cycle": "2026-07",
  "unit": "水保监测单位",
  "linkCount": 2,
  "matchRate": 96
}
```

`POST /api/workspace/tasks/{taskId}/link-document` 支持：

- 前端传真实 `documentId`
- 前端传候选项 `id`，例如 `c1`
- 前端传 `requirementId` 时直接更新对应资料要求状态
- 未传 `requirementId` 时，后端按资料名称自动匹配资料要求并更新状态

关联成功后，任务完整性校验会重新计算；例如 t1 关联 `td5` 后可从 `5/7、格式异常1` 变为 `6/7、格式异常0、缺失1`。

## V0.4 增量：P01/P02/S01 任务办理链路

### 任务列表筛选

```http
GET /api/workspace/tasks?module=S&status=待补正&keyword=审批&cycle=2026-07&cycleType=月度&deadlineStart=2026-08-01&deadlineEnd=2026-08-31&assignee=工程管理部
```

新增可选参数：

- `cycle`：按资料周期模糊匹配，例如 `2026-07`
- `cycleType` / `cycle_type`：周期类型，例如 `月度`、`季度`、`年度`、`一次性`
- `deadlineStart` / `deadline_start`：截止时间起
- `deadlineEnd` / `deadline_end`：截止时间止
- `assignee`：责任人或责任部门精确匹配

### 任务办理详情

```http
GET /api/workspace/tasks/{taskId}/detail
```

在原有 `task / documents / validation / candidateDocuments / reviewTimeline` 基础上，新增：

```json
{
  "linkedDocuments": [
    {
      "relationId": 950001,
      "documentId": "930001",
      "documentName": "弃渣场巡查记录_2026-07.pdf",
      "documentType": "监测报告",
      "period": "2026-07",
      "version": "V2",
      "validityStatus": "有效",
      "source": "ESG智能入库",
      "relationStatus": "LINKED",
      "matchScore": 96,
      "linkedAt": "2026-08-10 18:05:00"
    }
  ],
  "validationIssues": [
    {
      "id": "format-td5",
      "documentRequirementId": "td5",
      "documentName": "弃渣场巡查记录",
      "issueType": "格式异常",
      "severity": "medium",
      "message": "弃渣场巡查记录存在格式异常，请重新上传或从资料中心关联有效版本。",
      "canSubmit": false
    }
  ],
  "reviewRecords": [
    {
      "id": "r4",
      "taskId": "t1",
      "taskName": "水保监测月报（2026年7月）",
      "submitTime": "2026-08-06 09:30:00",
      "status": "待审核",
      "reviewer": "-",
      "commentSummary": "",
      "nextStep": "查看进度"
    }
  ]
}
```

### 任务办理动作

```http
POST /api/workspace/tasks/{taskId}/save
POST /api/workspace/tasks/{taskId}/link-document
POST /api/workspace/tasks/{taskId}/submit
```

暂存请求：

```json
{
  "comment": "暂存本次办理进度"
}
```

关联资料请求：

```json
{
  "documentId": 930001,
  "requirementId": "td5",
  "source": "MANUAL",
  "operatorId": 10001
}
```

提交审核响应示例：

```json
{
  "ok": false,
  "taskId": "t1",
  "message": "所选任务存在资料缺失或格式异常，暂不可提交",
  "validation": {
    "completed": 5,
    "missing": 1,
    "abnormal": 1,
    "canSubmit": false,
    "total": 7
  }
}
```

## V0.3 增量：P04 审核结果详情/轨迹/补正要求

```http
GET /api/workspace/reviews/{reviewId}
GET /api/workspace/reviews/{reviewId}/timeline
GET /api/workspace/reviews/{reviewId}/requirements
```

详情响应：

```json
{
  "id": "r1",
  "taskId": "t2",
  "taskName": "高风险作业审批资料",
  "module": "S",
  "moduleName": "社会责任",
  "submitTime": "2026-08-07 09:15:00",
  "status": "已退回",
  "reviewer": "李安全",
  "commentSummary": "审批签章页缺失，附件日期与资料周期不一致",
  "nextStep": "查看意见并补正",
  "correctionDeadline": "2026-08-10 09:15:00",
  "requirementCount": 2
}
```

审核轨迹响应：

```json
{
  "items": [
    {
      "id": 970001,
      "reviewId": "r1",
      "time": "2026-08-05 18:00:00",
      "action": "提交上传",
      "eventType": "SUBMIT",
      "operatorName": "张建国"
    }
  ]
}
```

补正要求响应：

```json
{
  "items": [
    {
      "id": 980001,
      "reviewId": "r1",
      "requirement": "审批签章页缺失，请补充完整并加盖单位公章。",
      "status": "待补正"
    }
  ]
}
```

当前目标：支撑已完成前端页面从 mock 数据逐步切到 API。  
约束：前端接入时保留 mock fallback；后端不可用时页面不得空白。

当前联调基线、关键数据口径与回归命令详见：

```text
server/FRONTEND_BACKEND_BASELINE.md
```

## 1. 健康检查

```http
GET /health
```

响应：

```json
{
  "ok": true,
  "service": "luoyi-esg-api",
  "db": "server/data/luoyi_esg_dev.db"
}
```

## 2. 领导首页 KPI

```http
GET /api/dashboard/kpis
```

响应：

```json
{
  "groups": [
    {
      "key": "E",
      "title": "环境环保组",
      "theme": "green",
      "status": "总体可控",
      "items": [
        {
          "key": "E01",
          "label": "环境监测超标",
          "fullName": "环境监测超标项",
          "value": 2,
          "unit": "项"
        }
      ]
    }
  ]
}
```

当前已对齐的 12 项值：

```text
E01=2, E02=5, E03=7, E04=12856
S01=368, S02=6, S03=4, S04=3
G01=5, G02=5, G03=6, G04=4
```

## 3. 页面快照

```http
GET /api/dashboard/snapshot?type=LEADER_HOME
```

可用 type：

```text
LEADER_HOME
MODAL_S01
UPLOAD_WORKBENCH
```

响应：

```json
{
  "snapshotType": "LEADER_HOME",
  "snapshotDate": "2026-07-13",
  "publishedAt": "2026-07-13 10:30:00",
  "payload": {
    "E01": 2,
    "E02": 5
  }
}
```

## 4. S01 连续安全生产天数弹窗

```http
GET /api/dashboard/kpi/S01
```

响应：

```json
{
  "projectStartDate": "2025-07-10",
  "currentDate": "2026-07-13",
  "continuousDays": 368,
  "currentStage": "主体工程施工",
  "currentStageDetail": "路基｜桥梁｜隧道并行施工",
  "countingStatus": "continuous",
  "updateTime": "2026-07-13 10:30",
  "timeline": {
    "startLabel": "开工日期",
    "startDate": "2025-07-10",
    "message": "本轮连续周期内无事故中断",
    "endLabel": "当前",
    "endDate": "2026-07-13",
    "months": ["2025-07", "2025-08", "2026-07"]
  },
  "constructionStages": [
    {
      "id": "preparation",
      "name": "施工准备",
      "status": "completed"
    },
    {
      "id": "main-construction",
      "name": "主体工程施工",
      "status": "current",
      "detail": "路基｜桥梁｜隧道并行施工"
    }
  ],
  "conclusion": "项目开工以来，未发生导致连续安全生产记录中断的事故，当前已连续安全生产368天。"
}
```

## 5. 上传工作台汇总

```http
GET /api/workspace/summary
```

响应：

```json
{
  "currentTodo": 27,
  "pendingUpload": 12,
  "pendingCorrection": 3,
  "pendingSubmit": 5,
  "underReview": 3,
  "dueSoon": 4,
  "completed": 36
}
```

## 6. 上传任务列表

```http
GET /api/workspace/tasks
GET /api/workspace/tasks?module=E
GET /api/workspace/tasks?status=待上传
GET /api/workspace/tasks?keyword=水保
```

响应：

```json
{
  "total": 12,
  "items": [
    {
      "id": "t1",
      "name": "2026年7月水保监测月报",
      "module": "E",
      "moduleName": "环境环保",
      "cycle": "2026-07（月度）",
      "cycleType": "月度",
      "deadline": "2026-08-10 18:00",
      "deadlineDisplay": "2026-08-10 18:00",
      "progressCurrent": 5,
      "progressTotal": 7,
      "status": "待上传",
      "nextStep": "开始办理",
      "assignee": "张建国",
      "assigneeDept": "安全环保部",
      "priorityCode": "HIGH"
    }
  ]
}
```

## 7. 任务办理弹窗

```http
GET /api/workspace/tasks/{id}/detail
```

示例：

```http
GET /api/workspace/tasks/t1/detail
```

响应核心字段：

```json
{
  "task": {
    "id": "t1",
    "name": "2026年7月水保监测月报",
    "module": "E",
    "moduleName": "环境环保",
    "cycle": "2026-07（月度）",
    "deadline": "2026-08-10 18:00",
    "progressCurrent": 5,
    "progressTotal": 7,
    "status": "待上传"
  },
  "tabs": ["资料要求", "已关联资料", "校验问题", "审核记录"],
  "documents": [
    {
      "id": "td1",
      "name": "水保监测实施方案",
      "required": true,
      "format": "PDF，≤50MB",
      "status": "已关联",
      "templateAvailable": true
    }
  ],
  "validation": {
    "completed": 5,
    "missing": 1,
    "abnormal": 1,
    "canSubmit": false
  },
  "candidateDocuments": [
    {
      "id": "c1",
      "name": "弃渣场巡查记录_2026-07.pdf",
      "cycle": "2026-07",
      "unit": "水保监测单位",
      "linkCount": 2,
      "matchRate": 96
    }
  ],
  "aiRecommendation": {
    "fileName": "弃渣场巡查记录_2026-07.pdf",
    "matchRate": 96,
    "text": "该资料已用于其他流程，无需重复上传"
  },
  "aiTip": "还缺少“审核确认单”，建议下载模板后补充签章。",
  "reviewTimeline": [
    {
      "time": "2026-08-05 18:00",
      "action": "提交上传（张建国 提交任务）"
    }
  ]
}
```

## 8. 资料中心汇总

```http
GET /api/workspace/documents/summary
```

响应：

```json
{
  "documentTotal": 368,
  "monthNew": 24,
  "pendingArchive": 6,
  "expiringSoon": 4
}
```

## 9. 资料中心列表

```http
GET /api/workspace/documents
```

响应：

```json
{
  "total": 368,
  "items": [
    {
      "id": "d1",
      "documentName": "弃渣场巡查记录_2026-07.pdf",
      "documentType": "监测报告",
      "module": "E",
      "period": "2026-07",
      "version": "V2",
      "source": "ESG智能入库",
      "relationCount": 3,
      "validityStatus": "有效",
      "uploadedAt": "2026-08-10 18:00"
    }
  ]
}
```

## 10. 资料详情 / 版本 / 关联任务

```http
GET /api/workspace/documents/{documentId}
GET /api/workspace/documents/{documentId}/versions
GET /api/workspace/documents/{documentId}/relations
```

资料详情响应核心字段：

```json
{
  "id": "930017",
  "documentCode": "DOC-202607-930017",
  "documentName": "2026年7月水保监测月报_智能入库测试.pdf",
  "documentType": "水保监测月报",
  "module": "E",
  "period": "2026-07",
  "version": "V1",
  "source": "ESG智能入库",
  "relationCount": 1,
  "validityStatus": "有效",
  "documentStatus": "ACTIVE",
  "confirmStatus": "CONFIRMED",
  "responsibleUnit": "安全环保部",
  "uploadedAt": "2026-07-15 13:50:42",
  "file": {
    "fileId": 900011,
    "originalName": "2026年7月水保监测月报_智能入库测试.pdf",
    "fileExt": "pdf",
    "fileSizeText": "1.95MB",
    "sha256Hash": "..."
  },
  "tags": ["水保监测月报", "E", "ESG智能入库", "2026-07"],
  "isUnique": true
}
```

版本响应：

```json
{
  "items": [
    {
      "id": 940002,
      "documentId": "930017",
      "versionNo": "V1",
      "versionDesc": "智能入库确认生成首版资料",
      "changeType": "CREATE",
      "uploadedByName": "项目管理员",
      "uploadedAt": "2026-07-15 13:50:42",
      "isCurrent": true
    }
  ]
}
```

关联任务响应：

```json
{
  "items": [
    {
      "id": 950008,
      "documentId": "930017",
      "taskId": "t1",
      "taskName": "2026年7月水保监测月报",
      "module": "E",
      "moduleName": "环境环保",
      "cycle": "2026-07（月度）",
      "status": "待上传",
      "relationStatus": "LINKED",
      "matchScore": 88,
      "source": "AI_MATCH",
      "referenceCount": 1,
      "lastReference": "2026-07-15 13:50:43"
    }
  ]
}
```

## 11. 审核结果

```http
GET /api/workspace/reviews
```

响应：

```json
{
  "statusCards": [
    {"label": "待审核", "value": 3, "unit": "项", "color": "#2f9cff"}
  ],
  "items": [
    {
      "id": "r1",
      "taskName": "高风险作业审批资料",
      "module": "S",
      "moduleName": "社会责任",
      "submitTime": "2026-08-07 09:15",
      "status": "已退回",
      "reviewer": "李安全",
      "commentSummary": "审批签章页缺失，附件日期与资料周期不一致",
      "nextStep": "查看意见并补正"
    }
  ]
}
```

## 12. AI 解析队列

```http
GET /api/workspace/ai/parse-queue
```

响应：

```json
{
  "items": [
    {
      "id": "p1",
      "fileName": "水保监测记录_2026-07.xlsx",
      "size": "1.25MB",
      "progress": 100,
      "status": "解析完成"
    }
  ]
}
```
