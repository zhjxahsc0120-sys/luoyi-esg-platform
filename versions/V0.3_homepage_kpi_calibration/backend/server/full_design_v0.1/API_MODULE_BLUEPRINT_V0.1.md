# 罗宜高速 ESG 接口模块设计蓝图 V0.1

## 1. 接口分组

建议接口按业务域划分，而不是按页面硬拆。

| 接口域 | 说明 |
|---|---|
| Dashboard | 领导首页 KPI 与专题展示 |
| KPI Detail | 12 项 KPI 详情弹窗 |
| Workspace | 上传工作台、任务列表、任务办理 |
| Ingestion | 智能入库、AI 解析、字段确认 |
| Documents | 资料中心、版本、复用 |
| Review | 审核结果、退回、补正 |
| Report | 月报准备、章节、缺项清单 |
| Admin/Dict | 字典、配置、字段映射 |

## 2. Dashboard 接口

当前已接：

```http
GET /api/dashboard/kpis
GET /api/dashboard/kpi/S01
```

后续建议：

```http
GET /api/dashboard/overview
GET /api/dashboard/kpis
GET /api/dashboard/kpi/{kpiCode}
GET /api/dashboard/topics/carbon
GET /api/dashboard/topics/monthly-report
GET /api/dashboard/gis
```

## 3. Workspace 接口

当前已接：

```http
GET /api/workspace/summary
GET /api/workspace/tasks
GET /api/workspace/tasks/{id}/detail
```

后续建议：

```http
POST /api/workspace/tasks/{id}/link-document
POST /api/workspace/tasks/{id}/upload-document
POST /api/workspace/tasks/{id}/save-draft
POST /api/workspace/tasks/{id}/submit-review
GET  /api/workspace/tasks/{id}/validation
```

## 4. Ingestion 智能入库接口

建议：

```http
POST /api/workspace/files/upload
POST /api/workspace/files/{fileId}/parse
GET  /api/workspace/parse-jobs/{jobId}
GET  /api/workspace/parse-jobs/{jobId}/fields
GET  /api/workspace/parse-jobs/{jobId}/match-candidates
POST /api/workspace/parse-jobs/{jobId}/confirm
POST /api/workspace/match-candidates/{candidateId}/accept
POST /api/workspace/match-candidates/{candidateId}/reject
```

## 5. Documents 资料中心接口

当前已接：

```http
GET /api/workspace/documents/summary
GET /api/workspace/documents
```

后续建议：

```http
GET /api/workspace/documents/{id}
GET /api/workspace/documents/{id}/versions
GET /api/workspace/documents/{id}/relations
POST /api/workspace/documents/{id}/reuse
POST /api/workspace/documents/{id}/archive
```

## 6. Review 审核接口

当前已接：

```http
GET /api/workspace/reviews
```

后续建议：

```http
GET  /api/workspace/reviews/{id}
POST /api/workspace/reviews/{id}/approve
POST /api/workspace/reviews/{id}/reject
POST /api/workspace/reviews/{id}/correction-request
GET  /api/workspace/reviews/{id}/timeline
```

## 7. Report 月报接口

后续建议：

```http
GET /api/reports/monthly/summary
GET /api/reports/monthly/chapters
GET /api/reports/monthly/missing-items
GET /api/reports/monthly/status-chain
POST /api/reports/monthly/generate-draft
```

## 8. Dict / Config 接口

字段映射需要配置化。

```http
GET  /api/admin/field-mapping-rules
POST /api/admin/field-mapping-rules
PUT  /api/admin/field-mapping-rules/{id}
GET  /api/admin/document-types
GET  /api/admin/indicator-definitions
```

## 9. 接口接入顺序建议

优先级：

```text
1. Ingestion 智能入库接口
2. Workspace 任务办理写操作接口
3. Documents 资料详情与版本接口
4. Review 审核流转接口
5. KPI Detail 详情弹窗接口
6. Dashboard 专题接口
```

原因：

```text
先有数据产生和确认
再有资料沉淀
再有业务汇总
最后才是领导展示
```
