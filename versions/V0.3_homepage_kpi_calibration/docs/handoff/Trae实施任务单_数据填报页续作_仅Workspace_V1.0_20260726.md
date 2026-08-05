# Trae 实施任务单 · 数据填报页续作（仅 Workspace）V1.0

| 项 | 内容 |
| --- | --- |
| **日期** | 2026-07-26 |
| **版本** | V1.0 · **开工令** |
| **状态** | **READY_for_trae** |
| **实施方** | Trae |
| **本单性质** | **仅** Workspace「数据填报」页内续作；上一轮混合任务被叫停后的 **收窄重开** |
| **对照基线** | `baseline/l1-l2-gis-20260726`（**首页受保护，禁止回归**） |

**权威依据（只读）：**

| 文档 | 用途 |
|------|------|
| `_handoff/Workspace数据填报页_基线自检_20260726.md` | P1 清单（仅 Workspace 内项） |
| `_handoff/Trae实施任务单_Workspace智能入库真解析演示_V1.0_20260726.md` | 真解析演示已落地能力 + 可选打磨 |
| `_handoff/Workspace智能入库真解析_演示说明_20260726.md` | 点击演示步骤 |
| `_handoff/BASELINE_L1L2_GIS_20260726.md` | 首页基线保护说明 |

> **重要：** 本文件是本 sprint **唯一实现依据**。口径变更或想改首页/助手 → **停工 → 设计变更**，不得自行扩 scope。

---

## 0. 背景（叫停后续作）

1. 先前混合单 `_handoff/Trae实施任务单_Workspace入口与S02S03小改_V1.0_20260726.md` 将 **Workspace 入口** 与 **S02/S03 首页小改** 绑在同一 sprint；执行中途 **用户叫停**。
2. 顶栏「数据填报」三入口与 Workspace 壳层 **已基本落地**（见自检）；首页 GIS / L1 / L2 已打标签保护，**不得再借本单动首页**。
3. 本单 **只续作数据填报（Workspace）**：自检 P1 文案/栅格/撞名/验收口径 + 智能入库真解析演示打磨。  
   **S02 / S03 / GIS / 助手 / Header 视觉统一 → 本 sprint 一律 CANCELLED / 另开单。**

---

## 1. 硬禁令（红线 · MUST）

以下条款为本单最高优先级；违反即视为未完成。

<span style="color:red">

### 1.1 禁止改动 — 工作台首页 / GIS / L1–L2

| # | 禁止 |
|---|------|
| R1 | **禁止改动** `src/views/DashboardPage.vue` |
| R2 | **禁止改动** GIS / `src/modules/traffic-gis-overview/**`（含预览页行为） |
| R3 | **禁止改动** E01–E04 / S01–S02 的 L1 / L2 工作台、弹窗、地图摘要卡及相关面板业务文案 |
| R4 | **禁止改动** 右栏面板（碳排/合规/月报等首页右栏） |
| R5 | **禁止改动** `HeaderNav.vue` 的样式与结构。平台顶栏 **已有三项**（工作台首页 → ESG智能助手 → 数据填报）时 **完全不要改 HeaderNav**；亦勿改 `dashboard.mock.ts` / `master.mock.ts` 中的 `navItems` 仅为「统一视觉」 |
| R6 | **禁止回归** 基线标签 `baseline/l1-l2-gis-20260726` 所保护的首页完整态 |

### 1.2 禁止改动 — ESG 智能助手

| # | 禁止 |
|---|------|
| R7 | **禁止改动** `src/views/AssistantPage.vue` |
| R8 | **禁止改动** `src/components/assistant/**` |
| R9 | **禁止**在本单推进助手「数据库驱动问答」或任何助手产品能力 |

### 1.3 禁止改动 — 全局样式 / Token

| # | 禁止 |
|---|------|
| R10 | **禁止改动** `src/styles/layout.scss`、`src/styles/tokens.scss` 中影响大屏顶栏 / 全局壳层的 token 与规则 |
| R11 | Workspace 样式仅允许 **组件内 scoped / Workspace 局部样式**；不得为对齐 Workspace 去改大屏全局 token |

### 1.4 其它硬禁

| # | 禁止 |
|---|------|
| R12 | **不要**把 Workspace 五个二级 Tab 挂进平台顶栏 |
| R13 | **不要**重设计平台 HeaderNav 标题 / Tab 视觉（跨页顶栏统一 **OUT**） |
| R14 | **不要**改首页 KPI 数据结构 / SQL / seed 枚举 |
| R15 | UI **禁止**出现「演示 / 测试 / 未确认」类 chrome（验收说明可写 mock/API，界面不写） |
| R16 | 不向 `main` 直推；分支遵循 `AGENTS.md` |

</span>

---

## 2. 与旧单关系（本 sprint 裁定）

| 旧单 | 本 sprint |
|------|-----------|
| `_handoff/Trae实施任务单_Workspace入口与S02S03小改_V1.0_20260726.md` | **SUPERSEDED**。其中 **WS-\*** 已落地部分不再重做；**S03-A / S02-A\* / MAP-1 及一切首页项 → CANCELLED（本 sprint）** |
| `_handoff/Trae实施任务单_Workspace智能入库真解析演示_V1.0_20260726.md` | **CONTINUED**：主路径已可演示；本单吸收其「可选打磨」中 **不阻塞、且仅触及 Workspace/解析 API** 的项 |
| 顶栏三入口 / 80px 壳 / 填报概览 / 迷你助手降级 | **视为已完成**；本单 **不要求**再改 HeaderNav / Dashboard / Assistant |

**从混合单提取、仍属本单的 Workspace 原则（非新需求）：**

- 模块内 **保留 5 个二级 Tab**；首 Tab 文案保持 **「填报概览」**
- 路由保持 `/#/workspace` + `?t=`；不新建平行路由
- 不把五项挂进平台顶栏

---

## 3. 允许改动文件清单（白名单）

**原则：未列出则不要改。** 若确需白名单外文件，先停工问设计方，不得自行扩。

### 3.1 前端（优先）

| 路径 | 允许动作 |
|------|----------|
| `src/views/WorkspacePage.vue` | 页内布局/Tab 宿主；**勿**改平台 Header 结构 |
| `src/components/workspace/**` | 全部 Workspace 子组件（Home / Nav / Tasks / SmartUpload / Review / Documents / TaskModal 等） |
| `src/data/workspace.mock.ts` | 仅当修复 Workspace 展示/回落逻辑需要 |
| `src/types/workspace.ts` | 仅当 Workspace 类型对齐需要 |
| `src/services/api.ts`（或现有 workspace API client 片段） | **仅** `/api/workspace/...` 相关调用修补；禁止顺手改 dashboard/GIS API |
| `src/utils/workspaceRefresh.ts` | 若续作任务刷新需要 |

### 3.2 后端（仅当真解析 / 任务需要）

| 路径 | 允许动作 |
|------|----------|
| `server/**` 中 **已有** workspace / `intelligent_ingestion` / parse-job 相关模块 | 打磨真解析、队列、失败态；**禁止**改 dashboard KPI / GIS / S02–S03 seed |
| `public/samples/**` | 保留并改进样例与 README（真解析演示） |

### 3.3 明确不在白名单（再次强调）

`DashboardPage.vue`、`HeaderNav.vue`、`AssistantPage.vue`、`src/components/assistant/**`、`traffic-gis-overview/**`、E01–E04/S01–S02 L1/L2 组件、右栏首页面板、`layout.scss`、`tokens.scss`（全局）、`dashboard.mock.ts` 的 `navItems`（无必要勿动）。

---

## 4. 范围内实施项（In Scope）

### 4.1 自检 P1（Workspace 内部 · 必做）

| ID | 来源 | 动作 | 完成标准 |
|----|------|------|----------|
| WS-P1-1 | 自检 N4/T2 | 统一审核文案：`WorkspaceNav`「审核结果」与 `WorkspaceReview`「审核管理」→ **统一为「审核管理」**（或两端同改为「审核」，须写死一种） | Tab 与页标题一致 |
| WS-P1-2 | 自检 L1 | `WorkspaceHome` 状态卡栅格：`repeat(5)` → **`repeat(6)`**（与 Tasks 对齐），消除第 6 卡折行不对称 | 6 卡同行（常规宽度） |
| WS-P1-3 | 自检 N6 | `WorkspaceTasks` 筛选区标题「ESG智能助手」→ 改为 **「智能筛选」** 或 **「任务问答筛选」**（勿与顶栏正式助手同名） | 界面无「ESG智能助手」作任务筛标题 |
| WS-P1-4 | 自检 D1 | **验收口径**：后端通时用真 API summary/tasks 验收；**不得**把 mock 回落数（如 45/12/7/5/21/36）当作基线验收数。UI 仍不标「演示」chrome；交付说明写清数据源 | 交付说明有「mock vs API」节 |

### 4.2 五 Tab 保持（必守 · 非重设计）

| 顺序 | key | 标签（本单） |
|------|-----|--------------|
| 1 | `workspace` | 填报概览 |
| 2 | `tasks` | 我的上传任务 |
| 3 | `smart-upload` | ESG智能入库（可简称「智能入库」） |
| 4 | `review` | 审核管理（或「审核」，与 WS-P1-1 一致） |
| 5 | `documents` | 资料中心（可略缩） |

深链 `?t=` 保持可用。

### 4.3 智能入库真解析（续作 / 打磨）

**已可演示（勿回退）：** 样例 CSV、`content_parser`、前端展示文件字段、推荐任务含水保相关项。自证：扬尘 3 / 噪声 2 / 水保问题 7 / 监测日 2026-07-18。

**本单建议打磨（按优先级，可不阻塞 P1）：**

| ID | 项 | 说明 |
|----|-----|------|
| SU-1 | 解析队列 | 展示上传时间；API 空时 **不要**回落假队列 |
| SU-2 | 关联入库 | 「复用并关联」走勾选候选 + 确认入库，避免纯提示 |
| SU-3 | 失败态 | 解析失败态与重解析接真实 API（若已有端点） |
| SU-X | xlsx / PDF OCR / 外部 LLM | **OUT**（另开 Issue；勿混进演示文案） |

文案：可用「已识别」「样例文件识别器」；勿暗示已接外部大模型商用能力。

### 4.4 明确不做（Out of Scope · 本 sprint）

- Header / 跨页顶栏视觉统一  
- ESG 智能助手 DB 驱动问答  
- S02 / S03 首页弹窗用语、进度轨、地图摘要卡（混合单模块 B/C/D → **CANCELLED**）  
- 任何 Dashboard / GIS 工作  
- Workspace 整页换肤、P2 token 大收敛（可另开小单）  
- 资料中心真 API 全量替换（非本单阻塞项）

---

## 5. 验收清单

### 5.1 红线抽检（必须全过）

| # | 项 | 期望 |
|---|-----|------|
| H1 | `git diff` 相对开工点 | **无** Dashboard / GIS / assistant / HeaderNav / layout&tokens 全局 的业务或样式改动 |
| H2 | 大屏顶栏 | 三项仍在；**未**被本单重设计标题/Tab 样式 |
| H3 | 基线 | 未故意改动受 `baseline/l1-l2-gis-20260726` 保护的首页行为 |

### 5.2 Workspace 功能

| # | 项 | 期望 |
|---|-----|------|
| W1 | 五 Tab | 填报概览 / 我的上传任务 / ESG智能入库 / 审核\* / 资料中心 均在 |
| W2 | 审核文案 | Nav 与审核页标题一致（「审核管理」或「审核」） |
| W3 | 状态卡 | Home 6 列栅格，无第 6 卡异常折行不对称 |
| W4 | 任务筛选标题 | 不再使用「ESG智能助手」撞名 |
| W5 | 真解析 | 按演示说明上传样例 CSV → 字段与自证一致；推荐含水保任务 |
| W6 | 数据源说明 | 交付包写明 summary/tasks 走 API 时的验收方式与 mock 回落条件 |

### 5.3 编译

见 §6。

---

## 6. 验证命令

前端（必跑）：

```bash
npm ci
npm run check
npm run build
```

若改动任何 Python：

```bash
python -m compileall -q server
```

真解析离线（若动解析器）：

```bash
python server/content_parser_demo_test.py
```

**点击验收（最低）：**

1. `/#/workspace` → 五 Tab 可见；审核 Tab 与页标题文案一致。  
2. 填报概览：6 张状态卡栅格整齐。  
3. 我的上传任务：筛选区标题无「ESG智能助手」。  
4. `/#/workspace?t=smart-upload`：样例 CSV 真解析字段与自证一致。  
5. 快速扫一眼大屏首页与助手页：确认 **未被本分支改坏**（对照基线，不要求本单改它们）。

环境限制须在交付说明写明，不得谎报通过。

---

## 7. 交付包约定

建议目录：`交付_数据填报页续作_仅Workspace包/`

须包含：

1. **变更文件列表**（路径级；对照白名单自检）  
2. **交付说明.md**：  
   - 本单完成的 P1 / SU 项勾选  
   - **mock vs API** 验收口径  
   - 验证命令结果摘要  
   - 明确声明：**未改** Dashboard / GIS / Assistant / HeaderNav / 全局 tokens  
3. 可选截图：审核文案、Home 6 卡、任务筛标题、智能入库真解析  
4. 已知未做项（P2 / xlsx / 资料中心真 API 等）

**分支建议：** `trae/<issue>-workspace-data-entry-continue`（以实际 Issue 号为准）  
**PR：** 引用 Issue；按 `AGENTS.md` 填完成报告；不向 `main` 直推。

---

## 8. 完成定义（DoD）

- [ ] 状态仍为「仅 Workspace」；§1 红线未破  
- [ ] §4.1 P1 四项全部完成  
- [ ] 五 Tab 保留；真解析主路径未回退  
- [ ] §5 验收通过；§6 命令通过（或例外已记录）  
- [ ] 交付包声明未触碰首页基线与助手  
- [ ] 未实施任何 S02/S03/GIS/助手/Header 视觉统一项  

---

## 9. 给 Trae 的一句话

> **只改 `WorkspacePage` + `components/workspace/**`（及必要的 workspace/解析 API 与 samples）**；做完自检 P1（审核文案、6 列卡、任务筛改名、mock/API 验收说明）并保住智能入库真解析演示——**HeaderNav / Dashboard / GIS / 助手 / layout&tokens 全局一律不许碰。**
