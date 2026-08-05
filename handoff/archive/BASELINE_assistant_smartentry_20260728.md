# BASELINE · ESG助手 + 智能填报 · 2026-07-28

| 项 | 内容 |
| --- | --- |
| **日期** | 2026-07-28 |
| **分支** | `trae/carbon-page` |
| **Tag** | `baseline/assistant-smartentry-20260728` |
| **Commit** | `fc06c2e8d8874591f71471e91c98ba27f2231e33` |
| **用途** | 记录当前产品态：智能助手业务化问答、上级检查资料包、ESG智能数据填报 AI 解析报告、首页大标题「宜罗高速 ESG 数字化看板」 |

## 与既有基线共存

| Tag | 保护范围 | 用途 |
| --- | --- | --- |
| `baseline/l1-l2-gis-20260726` | 首页 Dashboard L1/L2、GIS | **首页受保护**；勿覆盖/删除 |
| `baseline/workspace-ui-20260726` | Workspace UI 打磨快照 | 早期 Workspace 回退点 |
| `baseline/assistant-smartentry-20260728` | 助手问答 + 智能填报解析报告 + 顶栏标题 | **本快照**；后续改助手/填报前对照 |

三个 tag **同时保留**。回退本轮助手/填报产品态时用本文件；回退首页 GIS/L1L2 时仍用 `baseline/l1-l2-gis-20260726`。

## 恢复命令（只读检视 / 回退对照）

```bash
git fetch origin --tags
git switch --detach baseline/assistant-smartentry-20260728
```

恢复到可继续开发的分支 tip：

```bash
git switch trae/carbon-page
# 若需把工作区对齐到本 tag（危险：会丢弃未备份改动，须先确认）
# git reset --hard baseline/assistant-smartentry-20260728
```

## 本快照包含（产品相关）

### ESG 智能助手
- `src/views/AssistantPage.vue`
- `src/components/assistant/**`
- `src/utils/assistant-business-answer.ts`
- `src/types/assistant.ts` · `src/data/assistant.mock.ts` · `src/services/api.ts`（助手相关）
- `server/assistant_qa.py` · `server/app.py`（`/api/assistant/*`）· `server/start_backend.ps1`
- `public/samples/assistant-compliance-packs/`（上级检查 00–11 环保包等）
- 相关 `_handoff/ESG智能助手_*` 设计与实施说明

### ESG 智能数据填报
- `src/components/workspace/WorkspaceSmartEntry.vue`
- `src/data/esg-smart-entry-analysis.mock.json`
- `src/services/esgSmartEntryDemo.ts`
- `src/views/WorkspacePage.vue`（默认 smart-upload → SmartEntry）
- `_handoff/ESG智能数据填报_AI解析结果*`

### 顶栏 / 壳层
- `src/components/layout/HeaderNav.vue` — 大标题：**宜罗高速 ESG 数字化看板**
- `index.html` 页签标题同步
- `src/data/dashboard.mock.ts`（顶栏导航项）

## 明确未纳入 / 仍暂停
- 碳核算独立页组件（未接线，保持未跟踪或不纳入本基线强制范围）
- `_tmp_*`、`__pycache__`、日志、`dist-backup*`、巨型 `交付_*` 包、截图杂物
- 智能入库 V0.2 真 DB 回写 / DEMO 资料包 A–D 门禁仍为 PARTIAL

## 产品要点（验收对照）
1. 助手：业务卡片（状态→KPI→风险→依据→建议）；上级检查保留 11 类统计 + 资料包下载  
2. 智能填报：分阶段不等间隔处理；AI 解析报告（文档理解→摘要→重点→结构化→入库建议待确认）  
3. 首页标题：宜罗高速 ESG 数字化看板  
