# ESG智能数据填报 · AI解析结果 JSON Schema V1.0

> 日期：2026-07-27  
> 适用页面：`WorkspaceSmartEntry.vue`（ESG智能数据填报）  
> Mock 源文件：`src/data/esg-smart-entry-analysis.mock.json`

## 设计意图

解析结果以 **AI解析报告** 叙事呈现（先理解与摘要，再列重点），结构化字段降为辅助核对，入库状态为 **待业务确认**（非自动入库成功）。

## 顶层结构

```ts
interface AnalysisMockData {
  project: {
    name: string           // 短名，如「罗宜高速」
    fullName?: string      // 全称（可选）
    stage: string          // 建设阶段，如「主体施工」
  }
  documents: DocumentParseResult[]
  ingestionSuggestion: IngestionSuggestion
}
```

## DocumentParseResult

| 字段 | 类型 | 说明 |
|---|---|---|
| `id` | string | 文档 mock 标识 |
| `matchKeywords` | string[] | 文件名匹配关键词 |
| `documentType` | string | 文档类型（兼容字段） |
| `period` | string | 周期（兼容字段） |
| `confidence` | string | 识别置信度展示 |
| `coverage` | string[] | 覆盖标段/工作面（辅助） |
| `documentUnderstanding` | object | **文档理解**：文件类型 / 项目 / 周期 / 建设阶段 |
| `aiSummary` | string[] | **AI摘要**：2～5 段自然语言，合计宜 ≤300 字 |
| `highlightItems` | HighlightItem[] | **AI识别重点**：动态 3～8 条 |
| `structuredData` | object | **结构化数据（辅助）**：工程 / 安全 / 环境 |
| `recognitionNotes` | object | **AI识别说明**：章节/表格/关键事项计数 + 确认提示 |

### documentUnderstanding

```json
{
  "fileType": "监理月报",
  "project": "罗宜高速",
  "period": "2026年5月",
  "constructionStage": "主体施工"
}
```

### highlightItems[]

```json
{
  "name": "路基施工推进",
  "type": "工程",
  "content": "TJ-01、TJ-02 路基填筑及边坡防护持续推进，多工作面并行。",
  "focus": "关注边坡稳定与临时排水措施落实情况"
}
```

`type` 建议取值：`工程` | `安全` | `环境`（可扩展，UI 按类型着色）。

### structuredData

```json
{
  "engineering": [{ "label": "路线长度", "value": "78.6 km" }],
  "safety": [{ "label": "连续安全生产", "value": "355 天" }],
  "environment": [{ "label": "未闭环环保问题", "value": "7 项" }]
}
```

空数组或缺失字段时，前端展示「未识别」/「待确认」，不编造。

### recognitionNotes

```json
{
  "chapterCount": 8,
  "tableCount": 12,
  "keyItemCount": 36,
  "confirmHint": "以下内容建议业务人员确认后入库"
}
```

## IngestionSuggestion

```json
{
  "title": "入库建议",
  "parseStatus": "解析完成",
  "status": "pending_confirm",
  "statusLabel": "待业务确认",
  "objects": [
    "工程进展记录",
    "安全风险记录",
    "环境管理记录",
    "水保管理记录",
    "月报归档记录"
  ],
  "usage": "ESG 月报填报与项目资料管理"
}
```

- `statusLabel` 在解析完成且未点确认时显示为 **待业务确认**。
- 用户点击「确认入库」后，由前端本地状态切换为已确认；不表示后台已自动入库成功。

## 相对 V0.x 的变更

| 旧字段 | 处理 |
|---|---|
| `overview` / `keyWork` / `riskFocus` | 由 `aiSummary` + `highlightItems` 取代 |
| 顶层 `progress` 大表、`esg` 指标卡、`project.routeLength` 等英雄指标卡 | 迁入各文档 `structuredData`，降为辅助 |
| 入库「自动成功」语义 | 明确为 `pending_confirm` / 待业务确认 |

## 样例（节选：2026年5月监理月报）

见 `src/data/esg-smart-entry-analysis.mock.json` 中 `documents[0]`（`engineering-2026-05`）。
