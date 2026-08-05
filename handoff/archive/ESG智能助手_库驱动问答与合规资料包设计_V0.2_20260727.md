# ESG 智能助手 · 库驱动问答与合规资料包设计

| 项 | 内容 |
|----|------|
| **版本** | **V0.2**（承接 V0.1；见 §0 口径修正） |
| **日期** | 2026-07-27 |
| **状态** | **已实现 · 库驱动问答 + 上级检查合规资料包（用户可见文案已去 DEMO 等禁用字样）** |
| **范围页** | `/#/assistant`（`AssistantPage`） |
| **前序** | `_handoff/ESG智能助手_数据库驱动问答实现方案_V0.1_20260726.md`（架构与口径铁律仍有效） |
| **被取代** | `_handoff/ESG智能助手_库驱动问答与合规资料包设计_V0.1_20260727.md` |
| **样例包** | `public/samples/assistant-compliance-packs/` |
| **原则** | 回答数字与清单来自 MySQL / 现有 API；禁止固定 FAQ 业务数；不破坏首页 KPI；用户可见文案与包名禁止 DEMO 等禁用字样 |

---

## 0. 口径修正（V0.1 → V0.2）

### 0.1 纠正什么

| ❌ 弃用（V0.1） | ✅ 采用（V0.2） |
|----------------|----------------|
| 「某部门迎检需要准备哪些资料」— **部门自查 / 自备清单** 口吻 | **应对上级部门检查** — 向上级监管/检查组汇报与备检 |
| 安环部迎检 / 合约部迎检 部门自助 checklist | **上级环保 / 安全 / 综合检查** 的合规性资料与口径 |
| 仅列部门必交项 | **同一回答内**：库驱动 **合规性资料 / 口径回答** **+** 可下载 **资料包** |

### 0.2 产品一句话

> 用户问「怎么应对上级××检查」时，助手用 **库内同源口径** 说明应备合规资料与缺口，并在 **同条回答** 中给出 **「下载资料包」**（静态样例 zip → 后续 Formal 打包 API）。

### 0.3 问法对照

| V0.1（废弃） | V0.2（推荐） |
|--------------|--------------|
| 安环部迎检需要准备哪些资料？ | **应对上级环保检查应准备哪些合规资料？** |
| （无独立安全问） | **上级安全检查常见核查项与现有台账缺口？** |
| 合约部迎检需要准备哪些资料？ | **请给出本轮上级检查可用的合规资料包** |
| （部门包命名）`安环部_迎检资料包_…` | `上级检查_环保合规资料包_202607` 等（无  前缀） |

### 0.4 不变

- 现有页面问题（Q01–Q17）仍走 **库驱动 / 现有 API**；P1 全映射，禁止固定 FAQ 业务数。
- 样例包仅静态示意，**不入**正式 KPI / 月报统计。
- **已实现** AssistantPage 调 `/api/assistant/ask`；禁止写死 FAQ 业务数。

---

## 1. 本轮交付边界

| 做 | 不做 |
|----|------|
| 完整盘点页面可见问题 / chip / 快捷能力 | **不重写** `AssistantPage.vue` 的 `handleSendMessage` |
| 问题 → intent → API/表 → 回答模板映射表 | 不把固定 FAQ 答案写死进前端 |
| 新增 **应对上级检查** 问法（3–5 条）设计 | `POST /api/assistant/ask` + `GET /api/assistant/qa`（已实现） |
| 合规口径回答 + 聊天内「下载资料包」UX | 不接语音真能力（P3 预留） |
| 样例目录 / zip（上级检查命名，无 DEMO） | 不改首页 / GIS / 正式 KPI 口径 |

**结论：** P1/P2 已落地：每问独立 API 答 + PackageCard；用户可见文案无 DEMO 等禁用字样。

---

## 2. 现状（确认）

| 现象 | 证据 |
|------|------|
| 任意提问 → 同一回答 | `AssistantPage.handleSendMessage` 一律 `createEnvIssuesAnswer()` |
| 业务数写死 | `assistant.mock.ts`：「12 项未闭环」等与库内/首页可能不一致 |
| 上级检查 / 合规包无入口 | 欢迎区与快捷能力无「应对上级检查」问句；无资料包卡片 |
| 语音假录 | `AssistantInput.toggleRecording` 填固定句「当前有哪些未闭环环保问题？」 |

架构建议仍沿用 2026-07-26 方案：`POST /api/assistant/ask` → Intent → 复用现有 fetcher → 模板组装。

---

## 3. 页面可见问题 / Chip / 快捷入口全集

### 3.1 盘点来源

| 来源 | 文件 | 是否可点击发问 |
|------|------|----------------|
| 欢迎区能力标签（chip） | `AssistantWelcome.vue` → `categories` | **否**（纯展示） |
| 推荐问题 | `assistant.mock.ts` → `welcomeQuestions` | 是 → `handleWelcomeClick` |
| 快捷能力 E/S/G/C/M | `quickCategories`；点击发 `cat.name` | 是 → `handleQuickCategory` |
| 最近会话标题 | `recentSessions` | 部分（验收模式 session `1` 加载 mock；其余当前几乎空操作） |
| 跟进追问 | `createEnvIssuesAnswer().followUps` | 是（消息内芯片） |
| 输入框占位 / 假语音句 | `AssistantInput.vue` | 发送后同上链路 |
| 侧栏页脚提示 | `AssistantSidebar` footer | 否 |

### 3.2 欢迎区 Chip（不可发问 · 仅分类暗示）

1. ESG指标  
2. 环保、安全、治理事项  
3. 碳排放及低碳措施  
4. 月报准备情况  
5. 平台资料档案  

P2 建议：增补可见文案 **「应对上级检查」**（第 6 个 chip，或替换为可点击推荐区标题），并挂 §3.4 新问句。

### 3.3 当前可发问文案（去重全集 · 保持库驱动）

| ID | 文案 | 出现位置 |
|----|------|----------|
| Q01 | 当前有哪些未闭环环保问题？ | 推荐 / 最近会话 / 假语音 |
| Q02 | 当前较大及以上安全风险点有多少？ | 推荐 |
| Q03 | 项目累计碳排放是多少？ | 推荐 / 最近会话 |
| Q04 | 本月还有哪些月报资料待处理？ | 推荐 |
| Q05 | 查看E/S/G三类指标总体情况 | 推荐 |
| Q06 | 本月月报资料待处理情况 | 最近会话（与 Q04 近义） |
| Q07 | 当前有哪些逾期整改事项？ | 最近会话 |
| Q08 | 三标段安全风险情况 | 最近会话 |
| Q09 | 环境 E | 快捷能力（发 `cat.name`） |
| Q10 | 社会 S | 快捷能力 |
| Q11 | 治理 G | 快捷能力 |
| Q12 | 碳专题 | 快捷能力 |
| Q13 | 月报专题 | 快捷能力 |
| Q14 | 查看逾期事项 | 跟进（E02 mock） |
| Q15 | 按责任部门统计 | 跟进 |
| Q16 | 查看三标段问题 | 跟进 |
| Q17 | 导出问题清单 | 跟进 |

**去重后有效意图数（现页）：约 13–15 个**（Q04≈Q06；Q07≈Q14 可合并路由）。**P1 全部映射现有 API，口径不变。**

### 3.4 新增 · 应对上级检查推荐问题（设计 · 建议挂欢迎区）

| ID | 建议文案 | 说明 |
|----|----------|------|
| C01 | 当前有哪些待补齐的关键合规资料？ | 对齐 G04（库驱动，可无包） |
| C02 | 未完成报批报建手续还有多少项？ | 对齐 G01（库驱动，可无包） |
| C03 | **应对上级环保检查应准备哪些合规资料？** | 库口径 + **环保合规资料包**卡 |
| C04 | **上级安全检查常见核查项与现有台账缺口？** | 库口径（S02 等）+ **安全合规资料包**卡 |
| C05 | **请给出本轮上级检查可用的合规资料包** | 综合包卡（可附 G01/G04 摘要数） |

欢迎区推荐问题建议从 5 条扩到 **6–7 条**：保留 3 条高频 ESG 问 + 插入 C03、C04（或 C03+C05）；完整 C 组可放「治理 G」快捷能力下的 followUps。

---

## 4. 映射表：问题 → Intent → API/表 → 回答模板

**口径铁律：** 数字必须与现有 KPI / 工作台 **同源同函数**；助手侧禁止另写近似 SQL。

| # | 触发文案（含近义） | intent_key | 优先数据源 | 回答模板要点 | 空态 |
|---|-------------------|------------|------------|--------------|------|
| 1 | Q01 | `e02.open_issues` | `GET /api/environment/e02/issues` → `get_e02_issues` | 结论句插值 open 计数；KPI：未闭环/整改中/待复查/待销项；表前 5 条 | 暂无未闭环环保问题 |
| 2 | Q02 | `s02.active_major_risks` | `GET /api/social/s02/risks` / `get_s02_risks`；KPI S02 | 较大及以上在管数；表风险点 | 暂无较大及以上在管风险 |
| 3 | Q03 | `e04.cumulative_carbon` | `GET /api/dashboard/kpi/E04` / carbon topic | 累计 tCO₂e + 可选构成卡 | 暂无可用碳排数据 |
| 4 | Q04 / Q06 | `monthly.pending` | `/api/monthly-report/readiness` 或 `get_monthly_report_overview` | 待处理任务数 + 清单摘要 | 本月无待处理月报资料 |
| 5 | Q05 | `kpi.esg_overview` | `GET /api/dashboard/kpis` | E/S/G 三组 KPI 摘要卡 | 分项空则该项显示 — |
| 6 | Q07 / Q14 | `cross.overdue_rectify` | P1：E02 逾期筛选；P2：E02+E03+G03 聚合 | 逾期项数 + 表 | 暂无逾期整改事项 |
| 7 | Q08 | `s02.segment_3` | S02 + 标段过滤 | 三标段风险摘要 | 该标段暂无 |
| 8 | Q09 | `kpi.group_E` | `get_dashboard_kpis` E 组 | E01–E04 卡片 | — |
| 9 | Q10 | `kpi.group_S` | 同上 S 组 | S01–S04 | — |
| 10 | Q11 | `kpi.group_G` | 同上 G 组 | G01–G04；followUps 挂 C01–C05 | — |
| 11 | Q12 | `carbon.topic` | `/api/dashboard/topics/carbon` 或 `/api/carbon/benefit-overview` | 碳专题摘要 | — |
| 12 | Q13 | `monthly.topic` | `/api/dashboard/topics/monthly-report` | 月报专题摘要 | — |
| 13 | Q15 | `e02.by_department` | E02 issues 按责任部门聚合 | 部门×件数表 | — |
| 14 | Q16 | `e02.segment_3` | E02 + 标段=三标段 | 问题清单 | — |
| 15 | Q17 | `e02.export_hint` | 无文件生成 | 引导至 E02 工作台导出 + deep-link | — |
| 16 | C01 | `g04.material_gaps` | `GET /api/dashboard/kpi/G04` → `get_g04_material_gap_detail` | 待补齐数 + 清单表 | 暂无待补齐合规资料 |
| 17 | C02 | `g01.open_procedures` | `GET /api/dashboard/kpi/G01` → `get_g01_compliance_procedure_detail` | 未完成报批报建数 + 表 | 暂无未完成项 |
| 18 | C03 | `pack.superior_env` | 注册表 + 拼 E02/G04（可选水保）摘要 | **合规口径结论 + 清单表 + PackageCard** | 暂无注册环保包 |
| 19 | C04 | `pack.superior_safety` | 注册表 + S02（可选逾期）摘要 | **核查项/缺口口径 + PackageCard** | 暂无注册安全包 |
| 20 | C05 | `pack.superior_comprehensive` | 注册表 + 可选 G01/G04 摘要 | **本轮可用包说明 + PackageCard** | 暂无注册综合包 |

### 4.1 回答统一结构（沿用 `ChatMessage`）

| 区块 | 字段 | 规则 |
|------|------|------|
| 结论 | `content` | 含查询数字与 as_of；禁止常量业务数；上级检查问须点明「应对上级××检查」 |
| KPI | `kpiCards[]` | value 来自 API |
| 表 | `tableData` | 前 N 条 + total（合规资料清单 / 核查项） |
| 依据 | `dataBasis` | 同源口径说明；勿展示「测试数据」铬条 |
| 追问 | `followUps[]` | 仅已实现 intent |
| **资料包（新）** | `packageCard?`（见 §5） | **C03 / C04 / C05 必出**（与口径同条） |

### 4.2 Intent 未命中

返回引导话术 + **已注册问题列表**（含应对上级检查 C 组）；不回落成 E02 mock。

---

## 5. 应对上级检查 · 聊天内资料包 UX

### 5.1 用户故事（同答双件）

> 用户问：「应对上级环保检查应准备哪些合规资料？」  
> 助手 **同一条消息**：  
> 1. **合规性资料 / 口径回答**（库内：未闭环环保、待补齐合规资料等同源数 + 应备清单表）  
> 2. **资料包卡片** + 主按钮 **「下载资料包」** → `/samples/assistant-compliance-packs/上级检查_环保合规资料包_202607.zip`

安全问 / 综合包问同理，换 intent 与 zip。

### 5.2 PackageCard（建议前端类型扩展 · 本轮仅设计）

```ts
// 建议追加至 src/types/assistant.ts（实施阶段）
export interface AssistantPackageFile {
  name: string          // 展示名
  path: string          // 包内相对路径
  kind: 'report' | 'ledger' | 'checklist' | 'other'
  sizeHint?: string
}

export interface AssistantPackageCard {
  packageId: string
  title: string                 // 如「上级环保检查 · 合规资料包」
  inspectionType: 'env' | 'safety' | 'comprehensive'
  nature: 'sample' | 'formal'     // UI 用中性副标题，避免「测试数据」红条
  files: AssistantPackageFile[]
  downloadUrl: string           // /samples/assistant-compliance-packs/上级检查_….zip
  requiredCount: number
  updatedAt: string
}
```

`ChatMessage` 增加可选 `packageCard?: AssistantPackageCard`。  
`AssistantMessage.vue` 在 table 与 dataBasis 之间渲染卡片：文件列表 + 主按钮「下载资料包」→ `<a href={downloadUrl} download>` 或 `window.open(downloadUrl)`。

### 5.3 卡片线框（文案级）

```text
┌─────────────────────────────────────────────┐
│ 上级环保检查 · 合规资料包              │
│ 应备 4 项 · 更新 2026-07-27                   │
├─────────────────────────────────────────────┤
│ 📄 01_清单_合规资料目录.md                    │
│ 📊 02_水保月报/…水保监测月报摘要.csv           │
│ 📋 03_环保问题摘要/未闭环环保问题摘要说明.txt   │
│ ✅ 04_核查表/上级环保检查核查项.md             │
├─────────────────────────────────────────────┤
│            [ 下载资料包 ]                     │
└─────────────────────────────────────────────┘
```

**下载 UX：** 按钮文案固定「下载资料包」；`href` 指向静态 zip（P2）或 Formal API（P3）。

### 5.4 应备清单示例（回答表 · 与包内文件对应）

**上级环保检查（C03）**

| 序号 | 资料名称 | 类型 | 包内路径 |
|------|----------|------|----------|
| 1 | 合规资料目录 | 清单 | `01_清单_合规资料目录.md` |
| 2 | 水土保持监测月报摘要 | 月报 | `02_水保月报/…` |
| 3 | 未闭环环保问题摘要 | 摘要 | `03_环保问题摘要/…` |
| 4 | 上级环保检查核查项 | 核查表 | `04_核查表/…` |

**上级安全检查（C04）**

| 序号 | 资料名称 | 类型 | 包内路径 |
|------|----------|------|----------|
| 1 | 合规资料目录 | 清单 | `01_清单_合规资料目录.md` |
| 2 | 在管安全风险台账 | 台账 | `02_风险台账/…` |
| 3 | 上级安全检查核查项与台账缺口说明 | 核查表 | `03_核查表/…` |

**本轮上级检查综合包（C05）**

| 序号 | 资料名称 | 类型 | 包内路径 |
|------|----------|------|----------|
| 1 | 合规资料目录 | 清单 | `01_清单_合规资料目录.md` |
| 2 | 合同与履约合规检查表 | 检查表 | `02_合同履约/…` |
| 3 | 待补齐关键合规资料摘录 | 台账 | `03_合规资料缺口/…` |
| 4 | 报批报建手续进度摘要 | 摘要 | `04_报批报建/…` |

实施时：清单行数 = `requiredCount`；下载始终打完整 zip（含 README）。

---

## 6. 资料包格式 · 样例 vs Formal · 命名

### 6.1 目录约定

```text
public/samples/assistant-compliance-packs/
  README.md
  上级检查_环保合规资料包_202607/
  上级检查_环保合规资料包_202607.zip
  上级检查_安全合规资料包_202607/
  上级检查_安全合规资料包_202607.zip
  上级检查_综合合规资料包_202607/
  上级检查_综合合规资料包_202607.zip
  manifests/
    pack_superior_env.json
    pack_superior_safety.json
    pack_superior_comprehensive.json
```

### 6.2 Zip 内部结构（环保示例）

```text
上级检查_环保合规资料包_202607/
  README.md
  01_清单_合规资料目录.md
  02_水保月报/
    罗宜高速_2026年7月水保监测月报摘要.csv
  03_环保问题摘要/
    未闭环环保问题摘要说明.txt
  04_核查表/
    上级环保检查核查项.md
```

### 6.3 命名规则

| 规则 | 样例 | Formal（后续） |
|------|------|----------------|
| 前缀 | 无 ；直接 `上级检查_` | `FORMAL_` 或业务前缀 `LYGS_` |
| 场景 | `_上级检查_` | 同左 |
| 主题 | `_环保合规资料包_` / `_安全合规资料包_` / `_综合合规资料包_` | 同左 |
| 账期 | `_YYYYMM` | 同左 |
| 隔离 | 仅静态样例；**不入**正式 KPI / 正式月报统计 | 若接档案库，须权限与审计 |

### 6.4 样例 vs Formal 行为

| 项 | 样例 | Formal |
|----|------|--------|
| 文件来源 | `public/samples/...` 占位 csv/md/txt | 后端按权限从档案/月报任务材料打包 |
| `nature` | `sample` | `formal` |
| UI 副标题 | 「合规资料包 · {账期}」 | 「正式归档包 · {账期}」 |
| 数字 | 包内清单条数固定；旁路 KPI 仍读库 | 清单可与库内缺口实时对齐 |
| 下载 API | P2 可先静态 URL | P2+/P3：`GET /api/assistant/packages/{id}/download` |

### 6.5 Manifest 示例（环保）

```json
{
  "packageId": "PACK-SUPERIOR-ENV-202607",
  "intentKey": "pack.superior_env",
  "inspectionType": "env",
  "nature": "sample",
  "title": "上级环保检查 · 合规资料包",
  "downloadUrl": "/samples/assistant-compliance-packs/上级检查_环保合规资料包_202607.zip",
  "folderUrl": "/samples/assistant-compliance-packs/上级检查_环保合规资料包_202607/",
  "requiredDocs": [ /* … */ ],
  "relatedIntents": ["e02.open_issues", "g04.material_gaps"],
  "triggerQuestions": ["应对上级环保检查应准备哪些合规资料？"]
}
```

---

## 7. 语音（可选 · 后期）

| 项 | 说明 |
|----|------|
| 优先级 | **P3**；本主题焦点为 Q&A + 资料包 |
| 行为 | Web Speech 转写 → 填入输入框 → 同一 `/api/assistant/ask` |
| P1 | 可不改假录音；或改为 toast「语音即将支持」以免误导 |

---

## 8. 分期

| 阶段 | 内容 | 验收 |
|------|------|------|
| **P1** | 现有 Q01–Q17 全映射到现有 API；前端 `handleSendMessage` 调 `ask`；去掉凡问皆 E02 | 点每一推荐问题/快捷能力 → 数字与工作台/首页 KPI **一致**；空态正确；**首页不动** |
| **P2** | 应对上级检查 C01–C05；PackageCard +「下载资料包」；静态 zip；欢迎区挂 C03/C04/C05 | C03–C05 **同答**出口径+下载；G04/G01/S02/E02 数字同源 |
| **P3** | Trae 任务单细化：会话持久化、Formal 打包 API、语音、可选 LLM 润色 | 另开单；默认关闭 LLM |

**建议顺序：** 映射表确认 → P1 任务单 → P2 上级检查合规包 → 禁止并行做固定 FAQ。

---

## 9. 红线

| 红线 | 说明 |
|------|------|
| 不破坏首页 | 不改 Dashboard KPI 布局/口径/GIS |
| LLM 可选 | 无 Key 必须可用；失败回落模板 |
| 从现有 API 起步 | 优先 `mysql_api` 已有函数；缺口再薄封装 |
| 禁止固定 FAQ 业务数 | 含 mock 常量「12 项」等不得作为真回答 |
| 样例隔离 | 样例包不进入正式统计 |
| 不做部门自查迎检 | 问法与包名均面向 **上级检查** |
| 用户可见文案 | 禁止 DEMO 等禁用字样 |

---

## 10. 相关文件（只读参考）

| 路径 | 用途 |
|------|------|
| `src/views/AssistantPage.vue` | 发问入口（现状单 mock） |
| `src/data/assistant.mock.ts` | 推荐 / 快捷 / 会话 / 唯一富回答 |
| `src/components/assistant/*` | 欢迎、侧栏、消息、输入 |
| `src/types/assistant.ts` | 待扩展 `packageCard` |
| `server/mysql_api.py` | E02/S02/G01/G04/KPI/carbon/monthly |
| `public/samples/assistant-compliance-packs/` | 本轮样例（上级检查命名） |
| 前序方案 2026-07-26 | Intent / 模板 / 空态通则 |

---

## 11. 待确认（产品）

1. 欢迎区是「插入 2 条上级检查问」还是「扩到 7 条全展示」？  
2. Formal 打包是否进 P2，还是 P2 仅静态 样例 zip？  
3. `packageCard` 是否要在 P1 就留类型空字段（推荐 P2 再加，避免半截 UI）？  
4. 最近会话：P1 点击 = 重新提问标题文案，是否足够？  
5. C05「本轮」是否需绑定账期选择器，还是先固定当前账期 202607？（当前固定 202607）

---

## 12. 交付速查（示例）

| 示例问 | 同答内容 | 下载链接 |
|--------|----------|----------|
| 应对上级环保检查应准备哪些合规资料？ | 库口径结论 + 应备表 + PackageCard | `/samples/assistant-compliance-packs/上级检查_环保合规资料包_202607.zip` |
| 上级安全检查常见核查项与现有台账缺口？ | S02 等口径 + PackageCard | `/samples/assistant-compliance-packs/上级检查_安全合规资料包_202607.zip` |
| 请给出本轮上级检查可用的合规资料包 | 综合说明 + PackageCard | `/samples/assistant-compliance-packs/上级检查_综合合规资料包_202607.zip` |

**文档状态：** V0.2 **已实现**（库驱动问答 + 上级检查合规资料包；用户可见文案已去 DEMO 等禁用字样）。

---

## 附录 · V0.3 环保包 11 类目录（2026-07-27）

**变更摘要：** 上级环保检查合规资料包由稀疏「应备 4 项」改为 **11 类标准目录 + 具体文件归集统计**；G04 的约 4 项缺口映射为目录内「待补齐」子集，不再作为整包主口径。

### 标准目录

```text
上级环保检查合规资料包
├─ 00_资料目录及缺失说明
├─ 01_审批文件与环评批复落实
├─ 02_环保组织机构与管理制度
├─ 03_施工环保方案及交底培训
├─ 04_日常巡查与污染防治设施运行
├─ 05_施工期环境监测
├─ 06_环保监理检查
├─ 07_环保问题整改与闭环
├─ 08_固废危废及应急管理
├─ 09_生态保护与水土保持
├─ 10_环保月报及阶段总结
└─ 11_上级检查、投诉及处罚整改
```

### 回答统计口径（C03 / `pack.superior_env`）

| 字段 | 含义 |
|------|------|
| categoryCount | 应备资料类别（固定 11） |
| requiredFileCount | 应备具体文件 N |
| collectedCount | 已归集 M |
| pendingCount | 待补齐 K（包内清单；含 G04 映射项） |
| openIssueCount | 当前未闭环问题（`_get_e02_issues_aligned`） |
| closureRate | 历史问题闭环率 `已闭环/（未闭环+已闭环）` |

**叙事：** 审批要求 → 现场实施 → 监测检查 → 问题整改 → 复查销项。

**PackageCard：** 标题仍为「上级环保检查 · 合规资料包」；`downloadUrl` 不变；meta 展示「类别 / 文件 / 已归集 / 待补齐 / 未闭环 / 闭环率」chips，不以「应备 4 项」为主。
