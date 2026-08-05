# 罗宜高速 ESG 智能体资料自动解析入库接口建议 V0.1

本文件是接口设计建议，当前尚未纳入 `server/app.py` 运行基线。

## 1. 上传文件

```http
POST /api/workspace/files/upload
```

返回：

```json
{
  "fileId": 900001,
  "fileCode": "FILE-202607-0001",
  "originalName": "水保监测记录_2026-07.xlsx",
  "sha256Hash": "8B2F...",
  "duplicateStatus": "UNIQUE",
  "parseStatus": "PENDING"
}
```

## 2. 发起解析

```http
POST /api/workspace/files/{fileId}/parse
```

返回：

```json
{
  "jobId": 910001,
  "jobCode": "PARSE-202607-0001",
  "jobStatus": "RUNNING"
}
```

## 3. 查询解析任务

```http
GET /api/workspace/parse-jobs/{jobId}
```

返回：

```json
{
  "jobId": 910001,
  "fileId": 900001,
  "jobStatus": "WAIT_CONFIRM",
  "confidence": 96.5,
  "startedAt": "2026-07-13 10:10:00",
  "finishedAt": "2026-07-13 10:10:08"
}
```

## 4. 查询抽取字段

```http
GET /api/workspace/parse-jobs/{jobId}/fields
```

返回：

```json
{
  "items": [
    {
      "fieldKey": "document_type",
      "fieldName": "资料类型",
      "fieldValue": "水保监测月报",
      "normalizedValue": "水保监测月报",
      "confidence": 98.2,
      "confirmStatus": "PENDING"
    }
  ]
}
```

## 5. 查询候选任务

```http
GET /api/workspace/parse-jobs/{jobId}/match-candidates
```

返回：

```json
{
  "items": [
    {
      "candidateId": 920001,
      "taskId": "t1",
      "taskName": "2026年7月水保监测月报",
      "module": "E",
      "matchScore": 96,
      "matchReason": "资料类型、周期和模块均匹配",
      "candidateStatus": "PENDING"
    }
  ]
}
```

## 6. 确认解析结果并入库

```http
POST /api/workspace/parse-jobs/{jobId}/confirm
```

请求：

```json
{
  "confirmedFields": [
    {
      "fieldKey": "document_type",
      "confirmedValue": "水保监测月报"
    }
  ],
  "acceptedCandidateIds": [920001],
  "operatorId": 10001,
  "operatorName": "项目管理员"
}
```

返回：

```json
{
  "documentId": 930001,
  "documentCode": "DOC-202607-0001",
  "documentStatus": "ACTIVE",
  "linkedTaskCount": 1
}
```

## 7. 采纳候选任务

```http
POST /api/workspace/match-candidates/{candidateId}/accept
```

## 8. 拒绝候选任务

```http
POST /api/workspace/match-candidates/{candidateId}/reject
```

## 9. 查询资料版本

```http
GET /api/workspace/documents/{documentId}/versions
```

## 10. 查询资料关联任务

```http
GET /api/workspace/documents/{documentId}/relations
```
