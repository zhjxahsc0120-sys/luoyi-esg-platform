# S01 Trae 实施任务单 · P1（门禁 105 · V1.0 冻结稿配套）

**日期：** 2026-07-24  
**版本：** P1 / V1.0 · **开工令**  
**门禁：** 105（设计已通过并冻结）  
**权威设计：** `_handoff/S01_连续安全生产天数设计说明_B方案_V1.0冻结稿_20260724.md`  
**对标参考：** `_handoff/E04_Trae实施任务单_P1_V1.0_20260724.md`（分阶段迁移动作风格；业务域为 S01，勿抄 E04 碳排域）  
**实施方：** Trae  
**本单范围：** **仅 P1**（Schema / 确认批次与快照 / 正式·演示隔离 / 测数重建 / 自验）。**不含 P2 API 状态机**、**不含 P3 UI**、**不含 P4 全量回归**。另开任务单，勿混入本单。

> **重要：** 本文件是实现依据，**不得**把设计冻结稿直接当作 GitHub Issue 或替代本单。若需调整天数算法、重置硬条件、正式缺数策略、迁移归属 → **停工 → 设计变更**，不得在实现中自行改口径。

---

## 0. 角色与硬禁令

| 角色 | 职责 |
|------|------|
| Trae | 按本单完成 P1，提交可重复执行的增量迁移 + 自验 SQL/报告 |
| Cursor | 对照冻结稿复核（仅在发现偏离时） |
| Codex | 设计已冻结；P1 完成后参与验收 |

**禁止：**

- 将迁移写入 **`e_group` / `e_group_e01_v1_1` / E 组号段**；必须使用 **`server/migrations/s_group_s01_v1_0/`**（或冻结稿允许的 S01 独立目录）
- 修改历史建库脚本；删除用户正式记录
- 用演示数据冒充正式 KPI；正式无确认快照时用 `0` 代替缺失（正式读数属 P2，但 P1 测数不得制造「正式=0 天」假象行充当 CONFIRMED）
- 为凑 **77** 天覆盖或改写正式历史
- 把 `interrupt_counting` 做成可脱离硬条件的人工开关字段语义（可保留列，值须由规则可推导/审计）
- 本单内做 **P2/P3/P4**；不改首页 KPI 卡片 DOM 结构
- 不做地图工作台；不写入 `e_closure_case`

---

## 1. P1 目标（可独立验收）

在库内形成 S01 **数据模型与登记层**，使后续 P2/P3 能按冻结稿主源/谓词读数：

| 验收项 | 期望 |
|--------|------|
| 迁移目录 | `server/migrations/s_group_s01_v1_0/` + 可重复执行的 migrator（幂等） |
| 确认批次表 | `s01_confirmation_batch`（或冻结稿等价名）已建 |
| 快照字段 | `safety_production_record` 补齐冻结稿 §5.1 关键字段（含 `cycle_start_date`、`statistics_as_of`、`continuous_days`、`confirmation_*`、`effective_status`、`is_current`、`data_nature`/`is_demo` 等） |
| 事故字段 | `safety_incident_record` 补齐 §5.2（含 `fatality_count`、`responsibility_determination_status`、`occurred_date` 等） |
| 演示批次 | `demo_batch_code=DEMO-S01-20260724`（或等价），`is_current=1`，`data_nature=demo` |
| 演示勾稽 | 开工令 **2026-05-08**；`statistics_as_of=2026-07-24`；无生效重置；快照 **`continuous_days=77`**；`cycle_start_date=2026-05-08` |
| 工期阶段 | 当前有效阶段名称与验收一致：**路基桥涵施工**（只读展示用；日期对齐开工后） |
| 正式通道 | 可不造正式 CONFIRMED 快照；但不得把演示行标成 formal+CONFIRMED |
| 旧基线 | 原 `2025-07-10` / 368 演示行须 **退出当前有效集**（`is_current=0` 或等价），不得与 77 天 dual-current |

---

## 2. 动手前必读

| 位置 | 说明 |
|------|------|
| 冻结稿 §2 | 天数算法与 77 天样例 |
| 冻结稿 §3 | 重置硬条件、待认定、追溯 |
| 冻结稿 §4 | 正式/演示谓词与缺数策略 |
| 冻结稿 §5 | 表字段与确认批次 |
| 冻结稿 §10–11 | 分期与门禁 |

---

## 3. 建议交付物

1. `server/migrations/s_group_s01_v1_0/` 下增量 SQL（及 migrator，若项目惯例需要）  
2. 演示测数 seed（幂等）  
3. `P1交付报告.md`：自验 SQL 结果（当前 demo 快照 77、旧 368 非 current、阶段名、批次码）  
4. 简短说明：如何执行迁移  

**分支建议：** `trae/105-s01-p1-schema-seed`（以实际 Issue 号为准）

---

## 4. 自验 SQL（最低集）

```sql
-- 当前演示快照应为 77
SELECT continuous_days, cycle_start_date, statistics_as_of, data_nature, is_current
FROM safety_production_record
WHERE is_demo = 1 AND is_current = 1;

-- 不得存在 formal+CONFIRMED+is_current 的「假正式」凑数（若本环境未建正式包，结果集为空即可）
SELECT COUNT(*) AS bad
FROM safety_production_record
WHERE data_nature = 'formal' AND confirmation_status = 'CONFIRMED' AND is_current = 1
  AND continuous_days = 77 AND is_demo = 1;

-- 阶段名
SELECT stage_name, stage_status FROM construction_stage_record
WHERE stage_status = 'current';
```

期望：`continuous_days=77`；`cycle_start_date=2026-05-08`；`statistics_as_of=2026-07-24`；当前阶段 **路基桥涵施工**。

---

## 5. 完成定义（P1）

- [ ] 迁移幂等可重复执行  
- [ ] 演示当前快照 77 天勾稽成立  
- [ ] 旧 368/2025-07-10 退出 current  
- [ ] 未改首页卡结构；未做 P2/P3  
- [ ] 未写入 `e_group` 迁移链  
- [ ] 交付报告含自验证据  

P1 签收通过后，另开 **P2**（API）任务单。
