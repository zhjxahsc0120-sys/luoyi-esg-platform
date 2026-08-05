# Trae 实施任务单 · 碳核算与月报独立页 V1.0

> ## SUPERSEDED · 2026-07-26（用户修订）
>
> **本开工令已作废，禁止按本单实施。**
>
> - **错误方向：** 单页 `/#/carbon-report`「碳核算与月报」+ 四 Tab  
> - **正确方向：** 两个独立开工令 / 两页  
>   - `_handoff/碳核算与月报独立页/Trae实施任务单_碳核算独立页_V1.0_20260726.md` → `/#/carbon`  
>   - `_handoff/碳核算与月报独立页/Trae实施任务单_月报独立页_V1.0_20260726.md` → `/#/monthly-report`  
> - **继任设计：** `_handoff/碳核算与月报独立页/碳核算独立页设计_V0.1_20260726.md`、`_handoff/碳核算与月报独立页/月报独立页设计_V0.1_20260726.md`  
>
> 若已按本单开工：**停止并丢弃**合并页半成品，改按上述两单分别实施。

| 项 | 内容 |
| --- | --- |
| **日期** | 2026-07-26 |
| **版本** | V1.0 · **SUPERSEDED** |
| **状态** | **SUPERSEDED** |
| **实施方** | Trae |
| **本单性质** | ~~合并顶层页「碳核算与月报」~~ → 已废止 |
| **设计依据** | ~~`_handoff/碳核算与月报独立页/作废/碳与月报独立页设计_V0.1_20260726.md`~~ → 同批 **SUPERSEDED** |
| **开工基线 Tag** | **`baseline/workspace-ui-20260726`**（继任单仍用） |
| **首页保护 Tag** | **`baseline/l1-l2-gis-20260726`**（勿删） |
| **基线说明** | `_handoff/BASELINE_Workspace_UI_20260726.md` |

> 下文仅作历史对照，**不得**作为 Trae 实施依据。

---

## 0. 背景

1. 用户修订：碳与月报能力应是 **顶层独立页**，不是 Workspace 填报概览右栏，也不是以 E04 / MonthlyReportModal 为主路径的下钻。
2. 产品位阶与「数据填报」「ESG智能助手」相同：同一 `HeaderNav` + `screen-canvas` 壳 + 页内二级 Tab。
3. 数据与首页同源（panels / readiness / overview），口径遵循甲方 7.14（油+电+材料；累计 ~6174.99；运输暂不纳入）；UI **禁止**硬编码 6175、禁止演示 chrome。

---

## 0.1 基线与回退（MUST）

| 动作 | 命令 / 要求 |
|------|-------------|
| 开工前对齐 | 从含 `baseline/workspace-ui-20260726` 的分支创建实施分支；若该 tag 不可用则用当前 tip，并 **仍**以 `baseline/l1-l2-gis-20260726` 保护首页 |
| 本页破损回退 | `git switch --detach baseline/workspace-ui-20260726` |
| 首页回退对照 | `git switch --detach baseline/l1-l2-gis-20260726`；**禁止删除或覆盖该 tag** |
| 格式 | Workspace `.ws-*` / screen-canvas / HeaderNav 80px；**禁止新视觉语言** |

---

## 1. 硬禁令（红线 · MUST）

### 1.1 FORBIDDEN — 首页 / GIS / L1–L2 / 专题工作台

| # | 禁止 |
|---|------|
| R1 | **禁止改动** `DashboardPage.vue` **主体**（L1/L2、右栏、GIS 布局业务）；仅允许 `handleNav*` **最小**增加 `carbon-report` 跳转 |
| R2 | **禁止改动** GIS / `src/modules/traffic-gis-overview/**` |
| R3 | **禁止改动** E01–E03 / S02 工作台与相关文案 |
| R4 | **禁止改动** 首页右栏面板源码：`CarbonBenefitPanel` / `MonthlyReportPanel`（及 Master 对应物） |
| R5 | **禁止改动** S01–G04、E04 **模态内部业务**（可只读 import 作本页**可选**补充，不得改内部） |
| R6 | **禁止回归破坏** `baseline/l1-l2-gis-20260726` |

### 1.2 FORBIDDEN — Assistant / Workspace 业务

| # | 禁止 |
|---|------|
| R7 | **禁止改动** `AssistantPage` 内容与 `components/assistant/**`（`handleNav*` 最小跳转除外） |
| R8 | **禁止**推进助手 DB 驱动问答 |
| R9 | **禁止改动** `components/workspace/**` 业务页与 Workspace 五 Tab（**不要**做右栏碳/月报） |
| R10 | **禁止**继续或合入已 SUPERSEDED 的右栏实现 |

### 1.3 FORBIDDEN — 全局样式 / 数据 / 流程

| # | 禁止 |
|---|------|
| R11 | **禁止改动** `layout.scss` / `tokens.scss` 全局壳层（本页用局部 scss + 既有 ws token） |
| R12 | **禁止**新视觉语言；UI **禁止**「演示 / 测试 / 未确认」chrome |
| R13 | **禁止**硬编码累计排放 **6175** / **6174.99** 为展示主值（须走 API；口径说明可引用文档数字为静态说明，主 KPI 必须 API） |
| R14 | **禁止**新后端 schema / 碳主值迁移；默认不改 `server/**` |
| R15 | **禁止**改 HeaderNav **结构与样式**；仅允许 `navItems` + 各页 navigate 接线 |
| R16 | 不向 `main` 直推；分支遵循 `AGENTS.md` |

### 1.4 ALLOWED — 白名单

| 路径 | 允许动作 |
|------|----------|
| `src/views/CarbonReportPage.vue` | **新建**页壳 |
| `src/components/carbon-report/**` | **新建** Nav + 各 Tab 组件 |
| `src/styles/carbon-report.scss` | 可选；复用 `.ws-*` |
| `src/router/index.ts` | 注册 `/carbon-report` |
| `src/data/dashboard.mock.ts` | `navItems` 增加 `{ key: 'carbon-report', label: '碳核算与月报' }`（插在 `workspace` 后） |
| `src/data/master.mock.ts`（若有对称 nav） | 最小同步一项 |
| `DashboardPage` / `WorkspacePage` / `AssistantPage` | **仅** navigate 分支 → `/carbon-report` |
| `src/services/api.ts` | 薄复用已有 GET；无新 schema |
| 可选类型 | `src/types/` 仅本页 props 需要时 |

**只读复用（可 import，不改文件）：**  
`E04CarbonEmissionModal`、`MonthlyReportModal`、dashboard/monthly 类型与既有 client。

---

## 2. 与旧单关系

| 文档 | 处置 |
|------|------|
| `_handoff/碳核算与月报独立页/作废/Trae实施任务单_Workspace右侧碳与月报_V1.0_20260726.md` | **SUPERSEDED** |
| `_handoff/碳核算与月报独立页/作废/Workspace右侧_碳与月报模块设计_V0.1_20260726.md` | **SUPERSEDED** |
| `_handoff/Trae实施任务单_数据填报页续作_仅Workspace_V1.0_20260726.md` | 并行收尾可继续；冲突以本单红线为准 |
| `_handoff/Trae实施任务单_Workspace入口与S02S03小改_V1.0_20260726.md` | SUPERSEDED（仍有效） |
| Header 视觉统一 / 助手 DB 问答 | HOLD / OUT |

---

## 3. 范围内实施项（In Scope）

### 3.1 路由与顶栏（必做）

| ID | 动作 | 完成标准 |
|----|------|----------|
| N-1 | `navItems` 增加「碳核算与月报」，位于「数据填报」右侧 | Header 可见且 active 正确 |
| N-2 | 路由 `/#/carbon-report`（`name: 'carbon-report'`） | 直达可开 |
| N-3 | Dashboard / Workspace / Assistant / 本页 `handleNav*` 互通 | 四页可互跳 |

### 3.2 页壳（必做）

| ID | 动作 | 完成标准 |
|----|------|----------|
| S-1 | `CarbonReportPage`：screen-canvas 1920×1080 + HeaderNav 80px | 与 Workspace 同壳 |
| S-2 | 二级 `CarbonReportNav` + `?t=` 深链 | 四 Tab 可切可刷新保持 |
| S-3 | 版式 ws 语言；无演示 chrome | 视觉统一 |

### 3.3 碳模块（必做）

| ID | 动作 | 完成标准 |
|----|------|----------|
| C-1 | Tab **碳概览**：累计主值 + 构成 + 口径说明 | 数据自 `getDashboardPanels`；无硬编码主值 |
| C-2 | Tab **碳明细**：边界/来源列表化 | 只读；不以 E04 模态为主路径 |
| C-3 | （可选）按钮懒开 E04 模态 | 不改模态内部 |

### 3.4 月报模块（必做）

| ID | 动作 | 完成标准 |
|----|------|----------|
| M-1 | Tab **月报准备**：进度、计数、待办清单 | `getMonthlyReportReadiness` |
| M-2 | Tab **月报输出**：overview 或空态 | `getMonthlyReportOverview` |
| M-3 | （可选）懒开 MonthlyReportModal | 不改模态内部 |

### 3.5 Out of Scope

- Workspace 右栏摘要  
- 克隆首页右栏环图大板  
- 助手内容、Dashboard GIS/L1L2、E01–E03/S02  
- 新 schema / 碳主值迁移  

---

## 4. 验收清单

### 4.1 红线抽检

| # | 查 | 期望 |
|---|-----|------|
| H1 | `git diff` | 无 GIS / e01–e03/s02 / assistant 内容 / workspace 业务 / 首页右栏源码 / HeaderNav 样式 / layout·tokens 全局 / E04·月报模态内部 |
| H2 | 允许出现 | 新 `CarbonReportPage` + `carbon-report/**`；router；navItems；各页 navigate 一行；api 薄读 |
| H3 | 基线 | 未破坏 `baseline/l1-l2-gis-20260726`；优先自 `baseline/workspace-ui-20260726` 开工 |

### 4.2 功能

| # | 查 | 期望 |
|---|-----|------|
| W1 | 顶栏 | 「碳核算与月报」在「数据填报」右侧 |
| W2 | `/#/carbon-report` | 四 Tab 可用；`?t=` 有效 |
| W3 | 碳数据 | 与 panels 一致；无手工 6175 主值 |
| W4 | 月报 | readiness + overview/空态 |
| W5 | 口径 | 油+电+材料；运输暂不纳入；起点 2026-05-08 有说明 |
| W6 | 文案 | 无演示/测试/未确认 chrome |

### 4.3 编译

见 §5。

---

## 5. 验证命令

```bash
npm ci
npm run check
npm run build
```

若例外改动 Python（默认不应）：

```bash
python -m compileall -q server
```

**点击验收（最低）：**

1. 顶栏进入「碳核算与月报」→ `/#/carbon-report`  
2. 四 Tab 切换；刷新深链保持  
3. 碳概览有 API 数；明细有边界列表  
4. 月报准备有进度/待办；输出有数据或空态  
5. 回首页：GIS/L1/L2 **未改坏**（对照 `baseline/l1-l2-gis-20260726`）  
6. Workspace / Assistant **业务内容未改**

---

## 6. 交付包约定

建议目录：`交付_碳核算与月报独立页/`

1. 变更文件列表（对照白名单）  
2. 交付说明：完成项；API vs mock；验证结果；声明未改 Dashboard GIS/L1L2 主体、Assistant 内容、Workspace 业务、右栏方案未合入  
3. 可选截图（1920 / 1366）  
4. 已知未做项  

**分支建议：** `trae/<issue>-carbon-report-page`  
**PR：** 引用 Issue；按 `AGENTS.md`；不向 `main` 直推。

---

## 7. 完成定义（DoD）

- [ ] §1 红线未破  
- [ ] §3 必做项全部完成  
- [ ] §4 验收通过；§5 命令通过（或例外已记录）  
- [ ] 交付包完整  
- [ ] 无右栏半成品残留  

---

## 8. 给 Trae 的一句话

> **从 `baseline/workspace-ui-20260726` 开工**：新建 `/#/carbon-report` 顶层页「碳核算与月报」（HeaderNav 第四项 + 四 Tab + ws/screen-canvas）；只读 panels/readiness/overview；**禁止** Workspace 右栏与首页 GIS/L1L2/Assistant 内容改动；破损回退该 tag，首页对照 `baseline/l1-l2-gis-20260726`。
