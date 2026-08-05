# Workspace 智能入库 · 真解析演示说明（2026-07-26）

## 做了什么

- 新增可下载样例：`public/samples/罗宜高速_2026年7月水保监测月报摘要.csv`
- 后端确定性内容解析（无 LLM Key）：`server/intelligent_ingestion/content_parser.py`
- `start_parse_job` 读取上传落盘文件内容 → 字段入库 → 任务匹配
- 前端去掉上传后仍显示固定 mock 摘要的问题；展示文件内业务字段

## 点击步骤

1. 启动前后端。
2. 打开 `http://localhost:5174/#/workspace?t=smart-upload`
3. 点「下载样例文件」→ 再点「选择本地文件」上传该 CSV  
   （或直接选 `public/samples/罗宜高速_2026年7月水保监测月报摘要.csv`）
4. 看右侧「AI解析摘要」出现「已识别」；业务字段应为：扬尘 **3**、噪声 **2**、水保问题 **7**、监测日 **2026-07-18**
5. 「AI智能推荐」出现含水保相关任务；勾选后点「确认入库并关联」

## 自证

| 字段 | 文件内 | 旧文件名默认 |
|------|--------|--------------|
| 扬尘超标 | 3 | 1 |
| 噪声超标 | 2 | 1 |
| 水保问题 | 7 | 5 |

离线：`python server/content_parser_demo_test.py`

打磨任务单：`_handoff/Trae实施任务单_Workspace智能入库真解析演示_V1.0_20260726.md`
