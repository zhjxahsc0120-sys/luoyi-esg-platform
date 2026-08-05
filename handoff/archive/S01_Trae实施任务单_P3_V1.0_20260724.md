# S01 Trae 实施任务单 · P3（门禁 105 · V1.0 冻结稿配套）

**日期：** 2026-07-24  
**版本：** P3 / V1.0（**开工令**；须 **P2 DoD 通过后**执行）  
**门禁：** 105（设计已通过并冻结）  
**状态：** **已发单 · 阻塞于 P2 PASS**（P2 通过前勿开工改 UI）  
**权威设计：** `_handoff/S01_连续安全生产天数设计说明_B方案_V1.0冻结稿_20260724.md`  
**前置：**  
- P1 PASS：`server/migrations/s_group_s01_v1_0/` + `交付_S01_P1_Schema与数据登记包/`  
- P2 PASS：`_handoff/S01_Trae实施任务单_P2_V1.0_20260724.md`（读 API 已返回 77 / 正式 `--` 契约）  

**对标参考：** `_handoff/E04_Trae实施任务单_P3_V1.0_20260724.md`（专属模态升级、异常态、不改无关 KPI）；视觉可参考既有 S 组蓝主题与 E01–E03 字体/间距习惯，**路线为 B′ 模态，不做 E01–E03 地图工作台**  
**实施方：** Trae  
**本单范围：** **仅 P3** — 绑定 P2 API；收敛 `S01SafetyProductionModal` 至 B′；首页 KPI **仅切换同源数值/缺数展示，不改卡片结构**。不重做测数、不改冻结口径、不新增 Schema。

> 不得把冻结稿直接当 Issue。口径变更走设计变更。

---

## 0. 硬禁令

- **不改**首页 S01 KPI 卡片 DOM/版式/chrome（冻结 §8.4 / §1.3）；只改数据绑定与 `null→--` 展示  
- **不做** E01–E03 式 GIS 闭环工作台；无引导线；无「发起督办」伪入口  
- **禁止**前端用浏览器「今天」或开工日**重算**主值（冻结 §2.1）；主值只信 API `continuousDays`  
- **禁止**正式缺数时回退 `dashboard.mock.ts` / 组件内默认 368 / 本地推算  
- 演示全程「演示数据」角标（全局或模态内，与 E 组演示标识习惯一致）  
- 不改正式 GIS；不写 `e_group` 迁移；不改无关 KPI  
- 不恢复冻结稿 §8.3 已删除交互（见下）

---

## 1. P3 目标

点击首页 **S01「连续安全生产天数」** → 打开既有专属 **`S01SafetyProductionModal`（B′）** → 摘要/时间轴/辅区/结论与 P2 API 一致；演示主值 **77**；正式无确认时主值 **`--`** +「待建设单位确认」。

入口现状（保持，勿改成工作台）：

- `DashboardPage.vue` → `handleKpiSelect('S01')` → `KpiDetailModal` → `S01SafetyProductionModal`  
- 数据：`getDashboardKpiS01()` → `GET /api/dashboard/kpi/S01`

---

## 2. 动手前必读

| 位置 | 说明 |
|------|------|
| 冻结稿 §2.3 | `?acceptance=1` 固定统计日；正式显示「截至 YYYY-MM-DD」 |
| 冻结稿 §3.4 | 最近一次重置文案 |
| 冻结稿 §4.3 / §4.4 | `--` 与演示隔离 |
| 冻结稿 §7 | 字段名与同源 |
| 冻结稿 §8 | B′ 信息结构与删除项 |
| 冻结稿 §9 | 场景 A/F/G/H/I 前端可感知 |
| P2 任务单 | 契约字段与闸；P3 不得回改后端口径 |

---

## 3. 执行步骤

### P3.1 首页 KPI 绑值（不改结构）

| 文件 | 要求 |
|------|------|
| `src/stores/dashboard.store.ts` | 继续吃 `/api/dashboard/kpis`；S01 用 API 值 |
| `src/components/kpi/KpiCard.vue` | `value === null` / 缺数时显示 **`--`**（可仅对 S01 或通用空值）；**不改**卡布局 class 结构 |
| `src/data/dashboard.mock.ts` / `master.mock.ts` | 离线兜底可保留，但**在线正式路径不得**在 API 返回 null 时用 368 覆盖 |

首页仍只显示主值「连续安全生产天数」；最近重置 / 统计日 / 确认状态放在模态顶部（§8.4）。

演示部署：若 API 带 `isDemo`/`dataNature=demo`，卡片或顶栏可见演示标识（不新增第二套卡结构）。

### P3.2 收敛 `S01SafetyProductionModal` → B′（§8.2）

**保留壳：** 1920×1080 画布；模态约 1436×880；深色壳；S 组蓝 `#2f9cff`；1366 等比缩放；无模态内纵向滚动；保留 `?acceptance=1`。

**信息结构（必须）：**

1. **顶部摘要：** 连续天数、统计起点（`cycleStartDate` / `statisticsStart`）、统计期末（`statisticsAsOf`）、计数状态（`countingStatus`）  
2. **主区：** 连续计数**时间轴** — 节点：开工令、月度确认、待认定事故（如有）、最近重置（如有）、统计期末  
3. **辅区：** 当前工期阶段、最近一次重置、确认状态  
4. **底部：** 一句业务结论 + 资料来源说明  

无重置演示结论（对齐 API `conclusion` 或本地按字段组装，语义须一致）：

> 项目开工以来，截至 2026-07-24 已连续安全生产 77 天，未发生触发重置的人员死亡安全生产责任事故。

**明确删除或不恢复（§8.3）：**

- 6 个摘要卡堆叠（现网 `summaryCards` 过多时须收敛到 §8.2 四项摘要）  
- 30/60/90 天节点  
- 12 个月状态宫格  
- 大段计数规则说教（现网「连续安全生产计数规则」大块须去掉或极度压缩为脚注级）  
- 独立证据表格  
- 用 ECharts 月度累计曲线**冒充**主时间轴（可改为线性时间轴节点；若保留图，不得作为主值来源）

### P3.3 字段绑定与空态

| API 字段 | UI |
|----------|-----|
| `continuousDays` | 数字；`null` → **`--`** |
| `statisticsStart` / `cycleStartDate` | 摘要「统计起点」 |
| `statisticsAsOf` | 摘要「统计期末」；若早于业务日，展示「截至 YYYY-MM-DD」 |
| `countingStatus` | CONTINUOUS / PENDING_DETERMINATION / … 中文映射（待认定须可感知） |
| `latestInterruptDate/Reason` | 辅区「最近一次重置」；无则 §3.4 文案 |
| `pendingDeterminationCount` | >0 时提示「存在待认定事故」 |
| `confirmationStatus` / batch | 辅区确认状态 |
| `currentConstructionStage` / `currentStage` | 辅区阶段；无则「资料待补齐」 |
| `dataNature` / `isDemo` | 演示角标 |

异常态：加载中、失败+重试、正式缺数、无权 demo（403）、门禁异常提示。无哑「预览」按钮。

**删除前端重算：**

```75:82:src/components/modal/S01SafetyProductionModal.vue
const continuousDays = computed(() => {
  if (typeof data.value.continuousDays === 'number') return data.value.continuousDays
  const cycleStartDate = data.value.latestInterruptDate ?? data.value.projectStartDate
  ...
})
```

无数值时必须显示 `--`，**禁止**用日期差回算。

**删除硬编码阶段覆盖：**

```209:209:src/components/modal/S01SafetyProductionModal.vue
    currentStage: '路基桥涵施工',
```

阶段名只信 API。

### P3.4 Dashboard / Modal 接线

| 文件 | 动作 |
|------|------|
| `src/views/DashboardPage.vue` | 保持 S01 → 专属模态路径；勿改成 E0x workspace |
| `src/components/modal/KpiDetailModal.vue` | 继续 `v-if detail.key==='S01'` 挂载专属模态；清理无用的旧 S01 内嵌大段（若仍残留 12 月宫格等且不可达，可删死代码） |
| `src/services/api.ts` | 使用 P2 已齐类型；按需补 UI 用字段 |
| `src/types/s01.ts` | 若 P2 已建则复用 |

### P3.5 视觉语言

- 保持既有 dashboard 深色壳、S 组蓝、数字字体习惯  
- 不对齐 E01 地图面板宽度体系；模态居中 overlay 即可  
- 1920 与 1366 下无内部滚动条、无内容溢出遮挡关闭钮  

### P3.6 不做范围

- Schema / 迁移 / 重置写路径  
- P4 自动化全量回归（可自测 §9 场景）  
- 改其他 11 个 KPI 卡结构  
- 地图选点联动 S01  

---

## 4. 预期文件

**修改（主）**

- `src/components/modal/S01SafetyProductionModal.vue`  
- `src/components/kpi/KpiCard.vue`（`--` 展示，最小改动）  
- `src/services/api.ts`（若 P2 未齐字段）  
- 必要时：`src/stores/dashboard.store.ts`、`src/types/dashboard.ts`、`KpiDetailModal.vue`

**不要改**

- `server/migrations/**`（含 s_group，除非 P2 遗留阻断且已另开设计变更）  
- E01/E02/E03 工作台与 E04 碳模态业务边界  
- 首页 KPI 卡 HTML 结构（除绑值/`--`）

---

## 5. 验收清单（可测）

| # | 项 | 期望 |
|---|-----|------|
| 1 | 入口 | S01 → `S01SafetyProductionModal`，非 E0x 工作台 |
| 2 | 演示主值 | 首页与模态均为 **77**（同源） |
| 3 | 阶段 | 模态显示 **路基桥涵施工**（来自 API） |
| 4 | 正式缺数 | 主值 **`--`** +「待建设单位确认」；不出现 0/368/77 回退 |
| 5 | 模式隔离 | 正式模式不因本地 Mock 显示演示 77（场景 G） |
| 6 | B′ 结构 | 摘要四项 + 时间轴 + 辅区 + 结论；无 12 月宫格/规则说教堆叠 |
| 7 | 禁止重算 | 断网或字段缺失时不出现前端自算天数 |
| 8 | 待认定 | API 返回 PENDING 时可感知提示 |
| 9 | acceptance | `?acceptance=1` 下统计日稳定 |
| 10 | 编译 | 见下 |

---

## 6. 验证命令

```bash
npm ci
npm run check
npm run build
```

后端若本单有极小配合改动：`python -m compileall -q server`  
（环境限制须在交付说明写明原因与替代验证。）

手工：演示闸开 → 首页 S01=77 → 开模态核对摘要/结论；闸关或 formal 空 → `--`。

---

## 7. 交付物

建议目录：`交付_S01_P3_UI实施包/`

1. 变更文件列表  
2. `P3交付报告.md`：启动方式、`S01_ALLOW_DEMO`、自测要点（77 / `--` / B′ 结构截图或条目）  
3. 已知未做项（交 P4）  
4. 分支建议：`trae/105-s01-p3-b-prime-modal`

---

## 8. P3 完成定义（DoD）

- [ ] B′ 模态信息结构符合冻结 §8.2；§8.3 删除项已移除  
- [ ] 首页卡结构未改；主值与详情同源；缺数 `--`  
- [ ] 无前端主值重算；无正式回退 Mock 368  
- [ ] `npm run check` / `npm run build` 通过（或书面例外）  
- [ ] 未改 Schema；未做地图工作台；未动无关 KPI  

---

## 9. 给 Trae 的一句话

> 先确认 **P2 PASS** 且 API 已出 77/`--`，再只改 UI：收敛 `S01SafetyProductionModal` 到 B′，首页卡只绑同源数；不要回改 P1 测数或 P2 口径。
