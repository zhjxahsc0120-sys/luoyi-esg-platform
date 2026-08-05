# ESG 智能数据填报：工程资料 AI 解析接口 V1.0

任务编号：`ESG-AI-DATA-001`

## 边界

- 仅写入 `ai_document_analysis` 与五张 `ai_extracted_*` 新表。
- 新表与既有 ESG 业务表无外键、触发器、视图或统计查询关系。
- `excluded_from_dashboard=1` 固定标记解析数据不进入首页 KPI 口径。
- 当前使用确定性测试结果建立工程资料到 ESG 结构化数据的接口契约，不接入真实 OCR、LLM 或 RAG。
- 所有子表均通过 `analysis_id` 关联主表，并设置 `ON DELETE CASCADE`，删除主记录即可删除整份解析结果。

## 1. 发起文件解析

`POST /api/esg/document/analyze`

请求体：

```json
{
  "fileId": 985,
  "fileName": "罗宜高速2026年5月工程监理月报.pdf"
}
```

`fileName` 可省略；测试文件 ID：

| fileId | 文件 |
|---:|---|
| 985 | 罗宜高速2026年5月工程监理月报 |
| 986 | 罗宜高速2026年6月工程监理月报 |
| 987 | 罗宜高速2026年6月安全监理月报 |

成功返回 HTTP `201`：

```json
{
  "analysis_id": 1,
  "source_file_id": 985,
  "file_name": "罗宜高速2026年5月工程监理月报.pdf",
  "analysis_status": "completed",
  "ingestion_status": "stored",
  "excluded_from_dashboard": true,
  "document": {
    "type": "工程监理月报",
    "period": "2026-05",
    "confidence": 0.87
  },
  "summary": {
    "overview": "...",
    "key_work": ["路基填筑", "桥梁下部结构", "隧道初期支护", "互通施工"],
    "risk_focus": ["汛期排水", "高边坡稳定", "隧道围岩变化", "交叉作业交通组织"]
  },
  "data": {
    "project_info": {},
    "progress": [],
    "safety": {},
    "environment": {},
    "resource": {}
  },
  "review": {
    "need_confirm": [],
    "status": "completed"
  }
}
```

当前页面采用自动入库，因此 `review` 仅作为后续扩展字段，不构成前端操作门禁。

## 2. 查询解析结果

`GET /api/esg/document/{analysis_id}/result`

返回同一份摘要、结构化数据、解析状态和入库状态；记录不存在时返回 HTTP `404`。

## 3. 数据库迁移

```powershell
python server/migrations/migration_001_ai_document_analysis.py --dry-run
python server/migrations/migration_001_ai_document_analysis.py
```

仅删除本模块全部新表：

```powershell
python server/migrations/migration_001_ai_document_analysis.py --rollback
```

## 4. 生成测试数据

```powershell
python server/seed_ai_document_analysis_v1.py
```

## 5. 验证

```powershell
python -m unittest server/ai_document_analysis_test.py
python -m compileall -q server
```
