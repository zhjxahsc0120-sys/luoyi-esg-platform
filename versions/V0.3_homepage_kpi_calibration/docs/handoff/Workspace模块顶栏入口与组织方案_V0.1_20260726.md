# Workspace 模块顶栏入口与组织方案

| 项 | 内容 |
| --- | --- |
| 版本 | V0.1 |
| 日期 | 2026-07-26 |
| 范围 | 分析现有 Workspace IA；提议顶栏入口（置于「ESG智能助手」右侧）；模块内信息架构与分阶段落地 |
| 约束 | **本文件仅方案，不含代码改动**；保留现有 `/#/workspace` 路由体系 |

---

## 0. 结论摘要

1. Workspace 本质是 **「数据填报 / 上传 / 审核 / 档案」作业区**，与大屏「工作台首页」（KPI/GIS 总览）职责不同。
2. 顶栏应新增第三项，放在 **「ESG智能助手」右侧**；入口文案建议用 **「数据填报」**（备选见 §2），避免再叫「工作台首页」。
3. 模块内保留 4～5 条二级导航即可；首页侧栏「迷你助手」应降级或链到正式助手页，避免与顶栏「ESG智能助手」重复心智。
4. 交互：继续走 `/#/workspace`（可用 `?t=` 深链）；壳层统一用平台 `HeaderNav`（80px），替换 Workspace 自有绿系顶栏。

---

## 1. 当前 Workspace IA 盘点

### 1.1 路由与壳层

| 项 | 现状 |
| --- | --- |
| 路由 | `src/router/index.ts`：`/#/workspace` → `WorkspacePage.vue` |
| Tab 切换 | 页内 `activeNav`；挂载时读 `route.query.t`，合法值：`workspace` / `tasks` / `smart-upload` / `review` / `documents` |
| 自有顶栏 | `WorkspaceNav.vue`：独立标题「…｜数据填报与上传工作台」+ 通知铃 + 用户区 + 二级 Tab |
| 平台顶栏 | `HeaderNav` 目前仅用于大屏与助手：`工作台首页`、`ESG智能助手`（`dashboard.mock.ts` / `master.mock.ts`） |
| Workspace 与平台顶栏 | **未接入**：从大屏/助手无法点进 Workspace；Workspace 页也未使用 80px `HeaderNav` |

### 1.2 各 Tab：目的 / 主操作 / 成熟度

| Tab key | 标签 | 目的 | 主操作 | 成熟度（相对） |
| --- | --- | --- | --- | --- |
| `workspace` | 工作台首页 | 填报总览：状态卡、快捷入库入口、任务预览、今日关注；右侧有「迷你 ESG 智能助手」 | 点状态卡进任务筛选；上传/批量/资料复用；打开 `TaskModal`；快捷问答（偏 mock） | **中低**：UI 完整，任务/助手多为 mock；与大屏同名「工作台首页」易混 |
| `tasks` | 我的上传任务 | 全量上传任务列表与筛选 | 状态卡/高级筛选/搜索；打开任务办理弹窗 | **中**：列表偏 mock；`TaskModal` 已接任务详情/保存/关联/提交等 API |
| `smart-upload` | ESG智能入库 | 上传 → AI 解析 → 人工确认 → 入库关联 | 上传/解析队列/字段确认/匹配候选/确认入库 | **高**：已接 parse-queue、upload、parse-job、confirm 等 API，是模块核心能力 |
| `review` | 审核管理 | 审核员处理待审/退回/归档 | 列表筛选、详情时间线、通过/退回 | **中高**：审核列表与动作有 API；展示仍有 mock 拼装痕迹 |
| `documents` | 资料中心与档案 | 资料检索、分类、版本与关联查看 | 按 ESG/类型筛选、详情/版本/关联、复用导向入库 | **中低**：结构完整，数据以 mock 为主；适合作为「库」而非顶栏一级名 |

### 1.3 横切能力

- **TaskModal**：任务办理中枢（资料要求 / 关联 / 校验 / 提交），从首页、任务、审核均可打开。
- **API 面**（`src/services/api.ts`）：`/api/workspace/*` 覆盖 summary、tasks、documents、reviews、files/parse 等——后端能力已偏「填报作业台」，与大屏 KPI 域分离清晰。

---

## 2. 顶栏入口提案

### 2.1 位置与顺序

建议平台顶栏顺序：

```text
工作台首页  →  ESG智能助手  →  【数据填报】（新）
     /              /assistant         /workspace
```

- 「工作台首页」继续表示 **大屏总览**（现有 `/`）。
- 「ESG智能助手」保持问答入口（`/assistant`）。
- 新项放在助手 **右侧**，符合「看数 → 问数 → 填数」心智流。

### 2.2 入口文案选项

| 优先级 | 文案 | 优点 | 风险 |
| --- | --- | --- | --- |
| **推荐** | **数据填报** | 与 `WorkspaceNav` 副标题「数据填报与上传工作台」一致；和「工作台首页」不撞名；业务语义清楚 | 略偏「表单」，未强调 AI 入库 |
| 备选 A | **ESG智能入库** | 突出最成熟能力；营销感强 | 窄化模块（审核/档案也在内）；与页内 Tab 同名易混淆「入口=单页」 |
| 备选 B | **填报工作台** | 「工作台」暗示作业区 | 仍含「工作台」，与大屏「工作台首页」半撞车 |
| 不推荐 | **工作台** / **工作台首页** | — | **与现顶栏第一项严重冲突**，禁止作为第三项文案 |

**推荐默认：** 顶栏 label = `数据填报`，`key` = `workspace`，跳转 `/#/workspace`（可选默认 `?t=workspace` 或直达 `?t=smart-upload`，见 §6）。

### 2.3 命名对齐（避免三套「首页」）

| 层级 | 建议称呼 | 说明 |
| --- | --- | --- |
| 顶栏第 1 项 | 工作台首页（可远期改为「综合看板」） | 大屏；本次可不改，以免牵动验收话术 |
| 顶栏第 3 项 | 数据填报 | Workspace 模块入口 |
| 模块内首 Tab | **填报概览**（由「工作台首页」改名） | 避免与顶栏第 1 项同名 |

---

## 3. 模块内信息架构建议

### 3.1 推荐二级导航（P2 目标态）

| 顺序 | key | 建议标签 | 处置 |
| --- | --- | --- | --- |
| 1 | `workspace` | **填报概览** | **保留**：状态卡 + 今日关注 + 任务预览 + 入库快捷入口 |
| 2 | `tasks` | **我的任务**（或保留「我的上传任务」） | **保留**：列表主场；与概览分工清晰 |
| 3 | `smart-upload` | **智能入库** | **保留并置为核心路径** |
| 4 | `review` | **审核** | **保留**；权限不足时可隐藏或只读入口 |
| 5 | `documents` | **资料中心** | **保留**；名称可略缩短 |

### 3.2 Keep / Merge / Demote

| 内容 | 建议 | 理由 |
| --- | --- | --- |
| 智能入库全流程 | **Keep（强化）** | 成熟度最高，是模块差异化价值 |
| 任务列表 + TaskModal | **Keep** | 填报闭环必需 |
| 审核管理 | **Keep（角色化）** | 管理动作，不宜拆成顶栏独立项 |
| 资料中心 | **Keep（库）** | 复用/溯源入口；不适合顶栏一级名 |
| 首页「ESG 智能助手」侧栏 | **Demote** | 与顶栏正式助手重复；改为：快捷链到 `/assistant`、或「与任务相关的快捷问句」轻量条，避免第二套对话产品 |
| 首页状态卡 vs 任务页状态卡 | **Merge 心智** | 两套卡可并存，但文案/筛选项需同源，避免数字不一致 |
| Workspace 自有绿系 Header（铃铛/用户） | **Demote（壳层统一）** | 用户/通知若需要，并入平台壳；二级 Tab 下沉到 `HeaderNav` 下方或页内 sub-nav |
| 通知徽标「8」 | **Demote 至后续** | 无真实通知源前不进顶栏 |

### 3.3 用户路径（模块内）

```text
填报概览 ──快捷上传──► 智能入库 ──确认入库──► 任务/资料更新
    │
    ├──状态卡/列表──► 我的任务 ──► TaskModal（办理/提交）──► 审核（角色）
    │
    └──从资料复用──► 资料中心（复用/归档/溯源）
```

---

## 4. 不宜放进顶栏的内容

| 类型 | 示例 | 原因 |
| --- | --- | --- |
| 重管理 / 仅管理员 | 解析失败运维台、迁移对账、权限配置、种子数据工具 | 频次低、角色窄；应藏在模块内或系统设置 |
| 与大屏重复的「看板」 | KPI 卡片复刻、GIS 总览、E/S/G 工作台面板 | 已有「工作台首页」；Workspace 专注填报闭环 |
| 正式对话助手本体 | 完整会话、历史会话侧栏 | 已有「ESG智能助手」；Workspace 最多做任务向快捷入口 |
| 过细能力直接顶栏化 | 「审核管理」「资料中心」单独占顶栏 | 顶栏超过 3～4 项会挤占 240px Tab 布局；应留在模块二级 |
| 预览/实验页 | `/gis-preview`、`/ui-master/dashboard` | 非业务主航 |

---

## 5. 交互与壳层一致性

| 项 | 建议 |
| --- | --- |
| 路由 | **保持** `/#/workspace`；Tab 继续用 `?t=<key>`（实现顶栏时建议在切换 Tab 时 `router.replace` 同步 query，便于分享/返回） |
| 深链示例 | `/#/workspace?t=smart-upload`、`/#/workspace?t=review` |
| 顶栏跳转 | `DashboardPage` / `AssistantPage` / `WorkspacePage` 统一：`dashboard`→`/`，`assistant`→`/assistant`，`workspace`→`/workspace` |
| Header 高度 | Workspace 改用与助手页相同的壳：`HeaderNav` + `height: var(--dashboard-header-h)`（**80px**，见 `tokens.scss` / `HeaderNav` 注释 42+4+34） |
| 二级 Tab | 放在 80px 顶栏 **下方** 一条 sub-nav（现 `WorkspaceNav` 下半段可复用样式，但去掉重复平台标题） |
| 视觉 | 逐步对齐大屏/助手的 cyan 体系；绿系可保留为「填报成功/通过」语义色，避免整页另一套品牌感 |
| 活跃态 | 在 Workspace 时顶栏第三项 `active`；模块内 sub-nav 表示当前 Tab |

---

## 6. 可选分阶段落地

### P1 — 仅入口（低风险）

- `navItems` 增加 `{ key: 'workspace', label: '数据填报' }`，排在 `assistant` 后。
- 三页 `handleNavClick` 互通跳转。
- `WorkspacePage` 顶部换成平台 `HeaderNav`（80px）+ 保留现有五 Tab sub-nav（文案可暂不改）。
- 默认进入 `/#/workspace`（或 `?t=workspace`）。
- **验收**：大屏 → 助手 → 数据填报 可来回；URL 仍为 hash workspace。

### P2 — 简化与正名

- 模块内首 Tab 改名为「填报概览」；「ESG智能入库」可简称「智能入库」。
- 首页迷你助手 **降级**（链接正式助手或缩成快捷问句）。
- Tab 切换同步 `?t=`；审核 Tab 按角色显隐（若已有角色则接，无则仍全量展示）。
- 统一状态卡数据源（summary API），减少 mock/实数双轨观感。

### P3 — 体验与权限（可选）

- 资料中心接真实 documents API；通知中心真数据。
- 从 KPI/月报「去填报」深链到对应 task / smart-upload。
- 管理员运维类能力不进顶栏，放模块「更多」或独立后台。

---

## 7. 实施时注意（供后续 Issue）

1. **撞名**：顶栏「工作台首页」≠ Workspace 内「工作台首页」——P1 至少在方案/培训口径上区分，P2 改内页名。
2. **Tab 宽度**：`HeaderNav` 单项约 240px；第三项需确认 1920 壳下不换行、不挤压标题。
3. **勿改 main 业务范围外文件**：实现时以 `dashboard.mock` / store navs、`DashboardPage`、`AssistantPage`、`WorkspacePage`、`WorkspaceNav` 为主。
4. 本方案 **不要求** 本期改代码；落地时另开 Issue，分支遵循 `AGENTS.md`。

---

## 8. 参考文件

- `src/views/WorkspacePage.vue`
- `src/components/workspace/WorkspaceNav.vue` 及 Home / Tasks / SmartUpload / Review / Documents / TaskModal
- `src/components/layout/HeaderNav.vue`
- `src/router/index.ts`
- `src/data/dashboard.mock.ts`（当前顶栏两项）
- `src/views/AssistantPage.vue`（80px Header 壳参考）
- `src/styles/tokens.scss`（`--dashboard-header-h: 80px`）
