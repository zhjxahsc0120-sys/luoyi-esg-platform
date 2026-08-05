# S01 Trae 实施任务单 · P2（门禁 105 · V1.0 冻结稿配套）

**日期：** 2026-07-24  
**版本：** P2 / V1.0（**开工令**）  
**门禁：** 105（设计已通过并冻结）  
**状态：** **可开工**  
**权威设计：** `_handoff/S01_连续安全生产天数设计说明_B方案_V1.0冻结稿_20260724.md`  
**前置：** **P1 PASS**（Cursor 直接修复 · 二轮）  
- Schema/测数：`server/migrations/s_group_s01_v1_0/`（`V1_0_010`～`V1_0_030`）  
- 证据：`server/_tmp_s01_p1_round2_verify.txt`  
- 交付参考：`交付_S01_P1_Schema与数据登记包/`  
- 任务单：`_handoff/S01_Trae实施任务单_P1_V1.0_20260724.md`  
- 返修（已闭环）：`_handoff/S01_Trae返修任务单_P1_V1.0_20260724.md`  

**对标参考：** `_handoff/E04_Trae实施任务单_P2_V1.0_20260724.md`、`_handoff/E03_Trae实施任务单_P2_V1.0_20260724.md`（闸门/同源/类型齐备风格；**业务域为 S01，勿抄碳排或水保域**）  
**实施方：** Trae  
**本单范围：** **仅 P2**（读 API、重置/待认定谓词、正式·演示闸、首页 KPI 与详情同源、类型与契约）。**不做 UI（P3）**、**不做 P4 全量回归**、**不新增 Schema 迁移**（除非发现 P1 缺口且须先设计变更）。

> **重要：** 本文件是实现依据，**不得**把设计冻结稿直接当作 GitHub Issue 或替代本单。若需调整天数算法、重置硬条件、正式缺数策略、迁移归属 → **停工 → 设计变更**，不得在实现中自行改口径。

---

## 0. 角色与硬禁令

| 角色 | 职责 |
|------|------|
| Trae | 按本单完成 P2，提交可读 API + 自验报告 |
| Cursor | 对照冻结稿复核（仅在发现偏离时） |
| Codex | P2 完成后参与验收 |

**禁止：**

- 将迁移写入 **`e_group` / `e_group_e01_v1_1` / E 组号段**；一切增量仍只许 `server/migrations/s_group_s01_v1_0/`（本单原则上**不新增迁移**）
- 修改历史建库脚本；删除用户正式记录；为凑 **77** 覆盖正式历史
- 用演示数据冒充正式 KPI；正式无确认快照时用 **`0`** 代替缺失（必须 **`null` / 前端 `--`**）
- 仅靠前端 query 在正式部署读出 demo（须服务端闸）
- 继续依赖旧逻辑：`ORDER BY update_time DESC LIMIT 1` + 仅按 `interrupt_counting=1` 重算 368 天
- 让 `ensure_s01_business_tables()` 静默把 CSR 打回「主体工程施工」或与 P1 测数 dual-current
- 本单内做 **P3 UI**（含改首页 KPI 卡 DOM/版式）；不改无关 KPI（E/G/S02–S04）
- 不做地图闭环工作台；不写入 `e_closure_case`

---

## 1. P2 目标（可独立验收）

服务端按冻结稿主源读出 S01，使首页 KPI 与详情同源，演示基线 **77**：

| 验收项 | 期望（demo allow 时） |
|--------|------------------------|
| 天数 | `continuousDays = 77`（来自确认快照，算法口径 §2.1） |
| 周期 | `cycleStartDate = 2026-05-08`；`statisticsAsOf = 2026-07-24` |
| 开工 | `statisticsStart = 2026-05-08`（来自主数据/快照，非前端硬编码） |
| 计数状态 | `countingStatus = CONTINUOUS`（或兼容映射；无待认定） |
| 重置 | 无生效重置 → `latestInterruptDate/Reason` 为空或等价「未发生」字段语义 |
| 阶段 | `currentConstructionStage`（或既有 `currentStage`）= **路基桥涵施工** |
| 数据性质 | `dataNature=demo`，批次关联 `DEMO-S01-20260724` |
| 正式缺数 | formal 无有效确认快照 → `continuousDays=null`，**禁止**回退 77/368/Mock |
| 同源 | `GET /api/dashboard/kpis` 的 S01.value ≡ `GET /api/dashboard/kpi/S01` 的 `continuousDays` |
| 旧基线 | 不得再因 `ensure_s01_*` / 旧行重算冒出 **368** |

---

## 2. 动手前必读

| 位置 | 说明 |
|------|------|
| 冻结稿 §2 | 天数算法与 77 天样例；禁止前端用「今天」重算 |
| 冻结稿 §3 | 重置硬条件、待认定、追溯、最近一次重置文案 |
| 冻结稿 §4 | 正式/演示谓词与缺数 `--`；首页与详情同源 |
| 冻结稿 §5 | 表字段；CSR 只读展示 |
| 冻结稿 §7 | API 契约字段清单 |
| 冻结稿 §9 | 验收场景 A/F/G/H/I（本单至少覆盖 A、F、G、H、I） |
| 冻结稿 §10 | P2=API；P3=UI |
| P1 实态 | SPR current 77；旧 368 `is_current=0`；批次 `DEMO-S01-20260724`；CSR 路基桥涵施工 |

---

## 3. 执行步骤

### P2.1 Demo / Formal 闸

- 配置：`S01_ALLOW_DEMO`（对标 `E02_ALLOW_DEMO` / `E04_ALLOW_DEMO`；默认演示部署 `1`，正式部署 `0`）
- 查询参数可选：`scope=formal|demo`（受闸约束）；拒绝时 HTTP **403** 或空正式载荷 + 明确 `code`，打日志
- **禁止**仅靠前端参数在正式环境读出 demo
- 首页 KPI 与详情共用同一闸与同一解析函数

### P2.2 重写 `get_s01_detail()`（核心）

**现网问题（须消灭）：**

```4163:4182:server/mysql_api.py
def get_s01_detail() -> dict:
    ensure_s01_business_tables()
    row = query_one("SELECT * FROM safety_production_record ORDER BY update_time DESC LIMIT 1")
    ...
    continuous_days = (current_date - (latest_interrupt_date or project_start_date)).days
```

旧路径按 `interrupt_counting` 与旧日期重算，易回到 **368**，且忽略 P1 的 `is_current` / `data_nature` / 确认批次。

**改造要求：**

1. **主源** = `safety_production_record` 当前有效确认快照（冻结 §4.1 / §4.2 / §4.4）  
2. **演示谓词（allow 时）：**

```text
data_nature = 'demo'
is_demo = 1
effective_status = 'EFFECTIVE'
is_current = 1
demo_batch_code / confirmation_batch → DEMO-S01-20260724（或 batch 关联等价）
```

3. **正式谓词：**

```text
data_nature = 'formal'
is_demo = 0
effective_status = 'EFFECTIVE'
verification_status = 'VERIFIED'
confirmation_status = 'CONFIRMED'
is_current = 1
confirmation_batch_id = 当前正式确认批次
statistics_as_of <= 平台业务统计日
```

4. **主值：** 优先使用快照列 `continuous_days`；若需校验，仅用  
   `(statistics_as_of − cycle_start_date).days`（自然日，Asia/Shanghai 日期归一；起点当天为 0）  
5. **多条 current：** 不得静默 `LIMIT 1`；记录门禁异常（日志 / 响应 `gateError` 或等价），不得混正式·演示  
6. **正式无快照：** `continuousDays: null`（或省略数值字段但带明确缺数状态）；文案键/状态：「待建设单位确认」；**禁止** `0`、禁止回退 demo/Mock/SQLite `MODAL_S01`

### P2.3 重置与待认定（读路径）

事故主源：`safety_incident_record`（及认定字段，P1 已增强）。

**仅当同时满足才算生效重置（冻结 §3.1）：**

1. 项目边界内  
2. 责任认定 = 安全生产责任事故（`responsibility_determination_status = RESPONSIBLE` 或冻结等价）  
3. `fatality_count >= 1`  
4. 认定已生效且记录为当前有效版本  
5. 正式 KPI 只用正式非演示事故  

**明确不重置：** 隐患 / 未遂 / 无死亡轻微伤害 / 设备故障 / 待认定 / 撤销·无效·演示事故。

**状态机（读出）：**

| 条件 | `countingStatus` |
|------|------------------|
| 无待认定 | `CONTINUOUS` |
| 存在可能触发重置但尚未认定 | `PENDING_DETERMINATION`（**不改** `cycleStartDate`；返回 `pendingDeterminationCount`） |
| 已生效重置 | 周期自事故发生日；可 `RESET_CYCLE` 或 CONTINUOUS+有 `latestInterrupt*` |

`interrupt_counting` **仅审计结果**，不得单独作为重置开关。

`latestInterruptDate` / `latestInterruptReason` 必须来自**同一**当前有效认定记录；无重置时原因语义对齐 §3.4（「自开工令 2026-05-08 起未发生…」可由详情字段或结论句提供）。

### P2.4 工期阶段

- 只读 `construction_stage_record` 当前有效阶段（`stage_status='current'` / `is_current=1`）  
- 验收名：**路基桥涵施工**  
- 无有效记录 → 「资料待补齐」，**禁止**硬编码「主体工程施工」  
- 阶段**不参与**天数计算  

### P2.5 中和 `ensure_s01_business_tables()` 冲突

`ensure_s01_business_tables()`（约 `mysql_api.py:4090+`）仍会：

- `CREATE TABLE IF NOT EXISTS` 旧形态表  
- **UPSERT CSR** 把「主体工程施工」写成 `current`（与 P1 seed 冲突）

**P2 必须处理（择一或组合，交付说明写清）：**

1. `get_s01_detail` / KPI **不再依赖**该函数做演示种子；或  
2. 改造该函数：**禁止**在已有 V1.0 迁移字段/批次时回写旧 stage / 旧 368 逻辑；或  
3. 调用前检测 P1 迁移已应用则 **no-op** 业务种子  

目标：反复打 API 后，库内仍保持 P1 验收实态（77 current / 368 retired / 路基桥涵施工）。

### P2.6 首页 KPI 同源

改造 `get_dashboard_kpis`（约 `mysql_api.py:187` / `dynamic_values["S01"]`）：

- **必须**调用与详情相同的解析结果（同一函数或共享 `_resolve_s01_snapshot(scope)`）  
- `S01.value` = 详情 `continuousDays`（可为 `null`）  
- 附带：`dataNature` / `isDemo` / `scope` / `statisticsAsOf` / `confirmationStatus`（对标 E02/E03 扩展字段合并循环）  
- **不改**卡片布局；本单只保证 API 数值与元数据正确  

### P2.7 路由与 Mock 回退

| 层 | 路径 | 要求 |
|----|------|------|
| 路由 | `server/app.py` → `GET /api/dashboard/kpi/S01` → `get_s01_detail()` | 已存在；MySQL 优先 |
| MySQL | `server/mysql_api.py` → `get_s01_detail` | 本单主改 |
| Fallback | `app.py` 内 SQLite / `MODAL_S01` 快照 | **正式缺数时禁止**用旧 368 Mock 充数；无 MySQL 时须明确空/错误，不得冒充正式 77 |

### P2.8 类型与前端契约（本单齐备，可不绑 UI）

- `src/services/api.ts`：扩展 `S01Data` / `getDashboardKpiS01` 类型，对齐冻结 §7  
- 建议新增 `src/types/s01.ts`（若项目惯例与 E01/E02 一致）  
- **本单可不改** `S01SafetyProductionModal.vue` / `DashboardPage.vue` 展示逻辑（留给 P3）

---

## 4. API 契约（可测）

保持：

`GET /api/dashboard/kpi/S01`  
（可选）`?scope=demo|formal`、`?acceptance=1`（验收模式固定 `statisticsAsOf=2026-07-24`，冻结 §2.3）

响应**至少**包含（冻结 §7；camelCase）：

```text
continuousDays          // number | null；demo=77；formal 缺数=null
statisticsStart         // "2026-05-08"
cycleStartDate
statisticsAsOf
countingStatus          // CONTINUOUS | PENDING_DETERMINATION | RESET_CYCLE（可兼容映射旧枚举）
latestInterruptDate     // string | null
latestInterruptReason   // string | null
pendingDeterminationCount
confirmationStatus
confirmationBatchId     // 或 demoBatchCode
currentConstructionStage  // 建议；可与 currentStage 同值双写过渡
dataNature              // formal | demo
isDemo                  // boolean
scope                   // formal | demo
```

兼容过渡（可保留，但不得与上表矛盾）：

```text
projectStartDate ≈ statisticsStart
currentDate ≈ statisticsAsOf
currentStage ≈ currentConstructionStage
conclusion                  // 服务端可生成演示结论句（P3 展示）
```

约束：

- `continuousDays`、`cycleStartDate`、`statisticsAsOf` 同源自**同一**确认快照  
- `latestInterrupt*` 同源自**同一**认定记录  
- 无数据：明确空值 + 状态，**不拼装**旧 Mock 368  

首页：

`GET /api/dashboard/kpis` → groups.S.items[S01].value === 详情.continuousDays（含同为 null）

---

## 5. 必改 / 相关文件清单

**必改**

| 文件 | 动作 |
|------|------|
| `server/mysql_api.py` | 重写 `get_s01_detail`；中和 `ensure_s01_business_tables`；`get_dashboard_kpis` 的 S01 同源 + 闸 |
| `server/app.py` | 确认路由；收紧 SQLite/`MODAL_S01` 回退，避免正式缺数冒充 |

**建议改**

| 文件 | 动作 |
|------|------|
| `src/services/api.ts` | `S01Data` 契约字段 |
| `src/types/s01.ts` | 新建类型（可选） |

**不要改（本单）**

- `src/components/modal/S01SafetyProductionModal.vue`（P3）  
- `src/components/kpi/KpiCard.vue` / 首页卡 DOM（P3 仅绑值时再动）  
- `src/data/dashboard.mock.ts` 作为正式主源（P3 须禁止回退；本单后端先断）  
- `server/migrations/e_group_*`  
- 无关 KPI / E01–E04 工作台  

**已知冲突点（须在交付说明交代处理）：**

- `ensure_s01_business_tables()` CSR UPSERT「主体工程施工」  
- `server/smoke_test.py` / `dashboard_acceptance_test.py` 仍断言 368（本单可更新断言为 77/null，或注明留给 P4；**不得**为过旧测试改回 368 口径）

---

## 6. 验证命令

```bash
python -m compileall -q server
```

建议手工 / 脚本（服务已启动、P1 迁移已应用）：

```bash
# 演示闸开启（默认或显式）
# Windows PowerShell 示例：
$env:S01_ALLOW_DEMO="1"
curl -s http://127.0.0.1:8765/api/dashboard/kpi/S01
curl -s http://127.0.0.1:8765/api/dashboard/kpis
```

自验清单：

1. allow demo：`continuousDays===77`，`cycleStartDate===2026-05-08`，`statisticsAsOf===2026-07-24`，阶段「路基桥涵施工」  
2. `S01_ALLOW_DEMO=0`：不得返回 demo 77；formal 无快照时 `continuousDays` 为 null / 缺数字段，且**不是** 368  
3. 首页 `kpis` 与详情同源（场景 H）  
4. 连续调用详情后 CSR 仍为「路基桥涵施工」，旧 368 行仍非 current  
5. 不得仅靠 `interrupt_counting=1` 无死亡记录触发重置  

可选 SQL 对账（与 P1 一致）：

```sql
SELECT continuous_days, cycle_start_date, statistics_as_of, data_nature, is_current
FROM safety_production_record WHERE is_current = 1;
```

---

## 7. 交付物

建议目录：`交付_S01_P2_读数API包/`

1. 变更文件列表  
2. `P2交付报告.md`：闸默认值、契约字段、自验 curl/结果、与冻结稿偏差（口径偏差禁止）  
3. `ensure_s01_business_tables` 冲突处理说明  
4. 分支建议：`trae/105-s01-p2-read-api`（以实际 Issue 号为准）

---

## 8. P2 完成定义（DoD）

- [ ] `S01_ALLOW_DEMO` 闸生效；正式环境无法仅靠 URL 拉 demo  
- [ ] demo allow 时详情与首页均为 **77**，阶段「路基桥涵施工」，批次可追溯 `DEMO-S01-20260724`  
- [ ] formal 缺数 → `continuousDays=null`，不回退 77/368/Mock，不用 `0`  
- [ ] 重置只认死亡+责任+认定生效；待认定不改周期起点  
- [ ] `ensure_s01_*` 不再冲掉 P1 测数  
- [ ] `compileall` 通过；`api.ts` 类型已对齐 §7  
- [ ] 未做 P3 UI；未改首页卡结构；未写入 E 组迁移  

---

## 9. 下游

P2 DoD 通过后启用：`_handoff/S01_Trae实施任务单_P3_V1.0_20260724.md`
