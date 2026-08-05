# Trae 实施任务单 · Workspace 智能入库真解析演示 V1.0

**日期：** 2026-07-26  
**状态：** **CONTINUED** — 主路径已可演示；剩余打磨并入 `_handoff/Trae实施任务单_数据填报页续作_仅Workspace_V1.0_20260726.md`（仅 Workspace sprint）  
**勿动：** 首页 KPI 数据结构 / 口径；S01 UI 回退轨道；Dashboard / GIS / Assistant / HeaderNav

---

## 1. 背景

用户要求 Workspace「ESG智能入库」展示**真实读文件解析**能力，而非上传后仍显示固定 mock 摘要。

## 2. Cursor 已完成（可演示）

| 项 | 说明 |
|----|------|
| 样例文件 | `public/samples/罗宜高速_2026年7月水保监测月报摘要.csv` |
| 使用说明 | `public/samples/README.md` |
| 内容解析器 | `server/intelligent_ingestion/content_parser.py`（无外部 LLM Key） |
| 解析接入 | `mysql_api.start_parse_job` 读取上传落盘文件 → 字段写入 `ai_parse_field_result` → 任务候选写入 `task_match_candidate` |
| 前端 | `WorkspaceSmartUpload.vue`：下载样例、清空 mock 摘要、展示内容字段/置信度/任务推荐 |
| 离线校验 | `python server/content_parser_demo_test.py` |

**自证口径（文件值 ≠ 旧默认）：** 扬尘 3 / 噪声 2 / 水保问题 7 / 监测日 2026-07-18 / 责任单位「罗宜高速项目安全环保部」。

## 3. Trae 可选打磨（非阻塞演示）

1. 解析队列行展示上传时间、去掉过期 mock 队列依赖（API 空时不要回落假队列）。
2. 「复用并关联」按钮改为勾选候选 + 走确认入库，避免纯提示。
3. xlsx 真实解析（需评估 openpyxl 依赖；当前 CSV/TXT 已足够演示）。
4. PDF OCR / 外部 LLM：仅在有 Key 与产品确认后另开 Issue，勿混进本演示路径文案。
5. 解析失败态与重解析按钮接真实 API。

## 4. 验收（点击）

见下文「点击演示步骤」；通过标准：右侧摘要与「自文件识别的业务字段」数值与 CSV 一致，且推荐任务含「水保」相关上传任务。

## 5. 文案约束

- 可用：「已识别」「样例文件识别器」
- 避免 UI 写：「测试数据」「未确认假数据」「mock」
- 勿暗示已接入外部大模型商用能力（当前为确定性内容解析）
