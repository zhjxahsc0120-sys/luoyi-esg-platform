# Trae 实施任务单 · 月报独立页 V1.0

| 项 | 内容 |
| --- | --- |
| **日期** | 2026-07-26 |
| **版本** | V1.0 · **开工令** |
| **状态** | **READY_for_trae** |
| **实施方** | Trae |
| **本单性质** | 新建顶层页「月报」（与数据填报 / ESG智能助手 / 碳核算同级）；**仅月报，不含碳** |
| **设计依据** | `_handoff/碳核算与月报独立页/月报独立页设计_V0.1_20260726.md` |
| **姊妹开工令** | `_handoff/碳核算与月报独立页/Trae实施任务单_碳核算独立页_V1.0_20260726.md`（并行；互不实现对方页） |
| **开工基线 Tag** | **`baseline/workspace-ui-20260726`** |
| **首页保护 Tag** | **`baseline/l1-l2-gis-20260726`**（勿删） |
| **基线说明** | `_handoff/BASELINE_Workspace_UI_20260726.md` |

> **重要：** 本文件是 **月报页** 的实现依据。口径或 IA 变更 → **停工 → 改设计**。  
> **已作废：**  
> - `_handoff/碳核算与月报独立页/作废/Trae实施任务单_碳与月报独立页_V1.0_20260726.md`（合并四 Tab）  
> - `_handoff/碳核算与月报独立页/作废/碳与月报独立页设计_V0.1_20260726.md`  
> - `_handoff/碳核算与月报独立页/作废/Trae实施任务单_Workspace右侧碳与月报_V1.0_20260726.md` + 右栏设计  
> 若有右栏或合并页半成品：**停止并丢弃**，勿合入。

---

## 0. 背景

1. 用户修订：**月报**与**碳相关**是 **两个独立顶层页**，禁止合并为「碳核算与月报」四 Tab，也禁止 Workspace 右栏方案。
2. 本单只做 **月报**：路由 `/#/monthly-report`，页内三 Tab（准备进度 / 待办 / 输出归档）。
3. 数据：monthly readiness + overview；版式 Workspace `.ws-*`；**禁止演示 chrome**。
4. **MonthlyReportModal 不是整页主路径**（可选懒挂补充）。

---

## 0.1 基线与回退（MUST）

| 动作 | 命令 / 要求 |
|------|-------------|
| 开工前对齐 | 从含 `baseline/workspace-ui-20260726` 的分支创建实施分支 |
| 本页破损回退 | `git switch --detach baseline/workspace-ui-20260726` |
| 首页对照 | `git switch --detach baseline/l1-l2-gis-20260726`；**禁止删 tag** |
| 格式 | Workspace `.ws-*` / screen-canvas / HeaderNav 80px；**禁止新视觉语言** |

---

## 1. 硬禁令（红线 · MUST）

### 1.1 FORBIDDEN — 首页 / GIS / L1–L2

| # | 禁止 |
|---|------|
| R1 | **禁止改动** `DashboardPage.vue` **主体**；仅允许 `handleNav*` **最小**增加 `monthly-report` / `carbon` 跳转 |
| R2 | **禁止改动** GIS / `src/modules/traffic-gis-overview/**` |
| R3 | **禁止改动** E01–E03 / S02 工作台 |
| R4 | **禁止改动** 首页右栏 `CarbonBenefitPanel` / `MonthlyReportPanel` 源码 |
| R5 | **禁止改动** S01–G04、`MonthlyReportModal` **内部业务**（可只读 import 可选补充） |
| R6 | **禁止回归破坏** `baseline/l1-l2-gis-20260726` |

### 1.2 FORBIDDEN — Assistant / Workspace / 姊妹页

| # | 禁止 |
|---|------|
| R7 | **禁止改动** `AssistantPage` 内容与 `components/assistant/**`（`handleNav*` 除外） |
| R8 | **禁止**推进助手 DB 驱动问答 |
| R9 | **禁止改动** `components/workspace/**` 业务与 Workspace 五 Tab |
| R10 | **禁止实现** 碳核算独立页内容、`CarbonPage`、碳三 Tab、panels/benefit-overview 作为本页主内容 |
| R11 | **禁止**继续或合入右栏 / 合并四 Tab 半成品 |

### 1.3 FORBIDDEN — 全局 / 数据

| # | 禁止 |
|---|------|
| R12 | **禁止改动** `layout.scss` / `tokens.scss` 全局壳层 |
| R13 | **禁止**新视觉语言；UI **禁止**演示/测试/未确认 chrome |
| R14 | **禁止**新后端 schema；默认不改 `server/**` |
| R15 | **禁止**改 HeaderNav **结构与样式**；仅 `navItems` + navigate 接线 |
| R16 | 不向 `main` 直推；遵循 `AGENTS.md` |

### 1.4 ALLOWED — 白名单

| 路径 | 允许动作 |
|------|----------|
| `src/views/MonthlyReportPage.vue` | **新建**页壳 |
| `src/components/monthly-report/**` | **新建** Nav + 三 Tab（页级组件；勿改首页 modal 内部） |
| `src/styles/monthly-report-page.scss` | 可选；复用 `.ws-*` |
| `src/router/index.ts` | 注册 `/monthly-report`（**勿**在本单实现 `/carbon` 页组件） |
| `src/data/dashboard.mock.ts` | `navItems` 增加「月报」；**允许**一并增加「碳核算」nav 项（最小） |
| `src/data/master.mock.ts`（若有对称 nav） | 最小同步 |
| Dashboard / Workspace / Assistant / MonthlyReportPage（+ CarbonPage 若已存在） | **仅** navigate 分支 |
| `src/services/api.ts` | 薄复用 readiness / overview GET |
| 可选类型 | `src/types/` 仅本页 props 需要时 |

**只读复用（可 import，不改）：** `MonthlyReportModal`、monthly 类型与既有 client。

---

## 2. 与旧单 / 姊妹单关系

| 文档 | 处置 |
|------|------|
| `_handoff/碳核算与月报独立页/作废/Trae实施任务单_碳与月报独立页_V1.0_20260726.md` | **SUPERSEDED** |
| `_handoff/碳核算与月报独立页/作废/碳与月报独立页设计_V0.1_20260726.md` | **SUPERSEDED** |
| `_handoff/碳核算与月报独立页/作废/Trae实施任务单_Workspace右侧碳与月报_V1.0_20260726.md` | **SUPERSEDED** |
| `_handoff/碳核算与月报独立页/Trae实施任务单_碳核算独立页_V1.0_20260726.md` | **并行姊妹单**；勿互相吞并 scope |
| `_handoff/Trae实施任务单_数据填报页续作_仅Workspace_V1.0_20260726.md` | 并行收尾可继续 |
| Header 视觉统一 / 助手 DB 问答 | HOLD / OUT |

---

## 3. 范围内实施项（In Scope）

### 3.1 路由与顶栏（必做）

| ID | 动作 | 完成标准 |
|----|------|----------|
| N-1 | `navItems`：`月报`（key `monthly-report`）；位于「碳核算」右侧 | Header 可见且 active 正确 |
| N-2 | （允许）`navItems` 同步挂上「碳核算」项；**不**实现碳页 | 顶栏顺序完整或注明姊妹单承接 |
| N-3 | 路由 `/#/monthly-report`（`name: 'monthly-report'`） | 直达可开 |
| N-4 | 各页 `handleNav*` 互通 `monthly-report`（及已挂的 `carbon` 跳转） | 可互跳 |

### 3.2 页壳（必做）

| ID | 动作 | 完成标准 |
|----|------|----------|
| S-1 | `MonthlyReportPage`：screen-canvas + HeaderNav 80px | 与 Workspace 同壳 |
| S-2 | 二级 Nav + `?t=`：`prep` / `todos` / `archive` | 三 Tab 可切可深链 |
| S-3 | 版式 ws 语言；无演示 chrome | 视觉统一 |

### 3.3 月报内容（必做）

| ID | 动作 | 完成标准 |
|----|------|----------|
| M-1 | Tab **准备进度**：期次、归集率、状态计数 | `getMonthlyReportReadiness` |
| M-2 | Tab **待办**：exceptionTasks 清单或空态 | readiness |
| M-3 | Tab **输出归档**：overview 或空态 | `getMonthlyReportOverview` |
| M-4 | （可选）按钮懒开 MonthlyReportModal | 不改模态内部 |

### 3.4 Out of Scope

- 碳核算页 / 碳三 Tab / panels 主内容  
- 合并四 Tab 页、Workspace 右栏  
- 克隆首页月报大板 / 整页只挂 Modal  
- 助手、Dashboard GIS/L1L2、新 schema  

---

## 4. 验收清单

### 4.1 红线抽检

| # | 查 | 期望 |
|---|-----|------|
| H1 | `git diff` | 无 GIS / e01–e03/s02 / assistant 内容 / workspace 业务 / 首页右栏源码 / HeaderNav 样式 / layout·tokens / 月报模态内部 / **碳核算页实现** |
| H2 | 允许 | `MonthlyReportPage` + `monthly-report/**`（页级）；router `/monthly-report`；navItems；navigate；api 薄读 |
| H3 | 基线 | 未破坏 `baseline/l1-l2-gis-20260726` |

### 4.2 功能

| # | 查 | 期望 |
|---|-----|------|
| W1 | 顶栏 | 「月报」在「碳核算」右侧（推荐顺序） |
| W2 | `/#/monthly-report` | 三 Tab；`?t=` 有效；**无碳核算 Tab** |
| W3 | 数据 | readiness + overview/空态 |
| W4 | 文案 | 无演示/测试 chrome |

### 4.3 编译

见 §5。

---

## 5. 验证命令

```bash
npm ci
npm run check
npm run build
```

**点击验收（最低）：**

1. 顶栏进入「月报」→ `/#/monthly-report`  
2. 三 Tab 切换；刷新深链保持  
3. 准备进度有归集率/计数；待办有列表或空态；输出有数据或空态  
4. 回首页：GIS/L1/L2 **未改坏**  
5. Workspace / Assistant **业务未改**；本 PR **无**碳核算页主体（除非注明姊妹单同分支且已隔离文件）

---

## 6. 交付包约定

建议目录：`交付_月报独立页/`

1. 变更文件列表（对照白名单）  
2. 交付说明：完成项；API vs mock；验证结果；声明未改 Dashboard GIS/L1L2、Assistant、Workspace 业务、未实现碳核算页  
3. 可选截图（1920 / 1366）  
4. 已知未做项  

**分支建议：** `trae/<issue>-monthly-report-page`  
**PR：** 引用 Issue；按 `AGENTS.md`；不向 `main` 直推。

---

## 7. 完成定义（DoD）

- [ ] §1 红线未破  
- [ ] §3 必做项全部完成  
- [ ] §4 / §5 通过（或例外已记录）  
- [ ] 交付包完整  
- [ ] 无右栏 / 合并页半成品残留  

---

## 8. 给 Trae 的一句话

> **从 `baseline/workspace-ui-20260726` 开工**：新建 `/#/monthly-report` 顶层页「月报」（HeaderNav + 三 Tab + ws/screen-canvas）；只读 readiness/overview；**禁止**做碳核算页、合并四 Tab、Workspace 右栏与首页 GIS/L1L2/Assistant 内容改动。
