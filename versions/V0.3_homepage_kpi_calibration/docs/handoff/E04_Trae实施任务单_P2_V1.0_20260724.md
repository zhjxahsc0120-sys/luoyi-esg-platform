# E04 Trae 实施任务单 · P2（门禁 104 · V1.0 冻结稿配套）

**日期：** 2026-07-24  
**版本：** P2 / V1.0（**开工令**）  
**门禁：** 104（设计已冻结）  
**权威设计：** `_handoff/E04_累计碳排放工作台设计说明_B方案_V1.0冻结稿_20260724.md`  
**前置：** P1 已交付 — `交付_E04_P1_Schema与数据登记包/`（`V1_1_048` / `V1_1_049`）  
**实施方：** Trae  
**本单范围：** **仅 P2**（demo 闸、KPI/详情 API、专题同源、对照试算字段、精度落地）。**不做 UI（P3）**。  

> 不得把冻结稿直接当 Issue。口径变更走设计变更。

---

## 0. 硬禁令

- **禁止**改写或重算 **12,856.00** 及月度/来源/材料/成本锚定  
- **禁止**把 **11,970.96** 或 `BOUND-E04-V1-CANDIDATE` 当作正式/演示 KPI 主值  
- 正式 current 批次 **只能**引用 `boundary_status=ACTIVE`  
- `CANDIDATE` **仅**对照试算字段  
- 正式 KPI：**显式** `effective_status='EFFECTIVE'` + `verification_status='VERIFIED'` + 行级因子快照齐全 + 勾稽通过；**禁止** `IFNULL(...,'EFFECTIVE')`  
- `PENDING` / 月度暂算 **不进**正式 KPI  
- `platform_calc` 不得冒充 formal  
- 材料明细 **不得**与活动表再求和；运输在演示边界计入、候选对照剔除  
- 汇总：**先 SUM 未舍入中间量，再 `ROUND_HALF_UP` 至 2 位**；前端禁止重算累计  
- 不进 `e_closure_case`；本单不做 P3 UI  

---

## 1. P2 目标

| 项 | 期望 |
|----|------|
| 演示 KPI / 详情主值 | **12,856.00**（`DEMO-BOUND-E04-20260718` + 演示 current 批次） |
| 四来源 | 油 5,627.84 / 电 3,857.39 / 材料 2,485.73 / 运输 885.04 |
| 材料分项合计 | **2,485.73** |
| 候选对照 | 约 **11,970.96** 只读字段；不进任何正式 KPI |
| E04 ≡ C01 | 完整 scope 键一致（冻结稿 §6.2） |
| 正式 KPI | 无正式已核验批次时为 0/空，**不得**混入 demo |

---

## 2. 执行步骤

### P2.1 Demo 闸

- `E04_ALLOW_DEMO`（或共用碳模块闸；交付说明写清默认值）  
- 正式部署默认拒绝 `scope=demo` → 403 或空 + 明确 code；打日志  
- **禁止**仅靠前端参数在正式环境读出 demo  

### P2.2 KPI `GET /api/dashboard/kpi/E04`（或现路径等价改造）

- 主值来自 **current 演示批次**（demo scope）或 **current 正式批次**（formal）  
- 返回：`value`、`boundaryVersion`、`accountingBatchId`、`dataNature`、`isDemo`、`scope`、`statisticsAsOf`、差异提示文案键  
- 正式谓词按冻结稿 §5.5；演示路径保持 12,856 勾稽  

### P2.3 Detail（E04 详情载荷）

- 摘要 + 月度趋势 + **in_boundary 来源表**（演示含运输）  
- 材料下钻（主从：明细合计＝材料来源）  
- 数据质量：性质、因子版本/快照、核验、`evidence_status`  
- 可选：`candidateBoundaryContrast`（只读，约 11,970.96 + 说明）  
- **禁止**前端把对照值加进合计  

### P2.4 碳专题 `GET /api/carbon/benefit-overview`

- 同 scope 下 **C01 ＝ E04**  
- C02/C03/C05：强化演示/平台测算标识；C03 支持默认折叠所需字段  
- 标段分析可保留，标注非首页 E04 口径  
- 不得改变已冻结成本/减排演示锚定数字（若展示则标演示）  

### P2.5 精度

- 接口权威值已按批次舍入规则落地  
- 详情可两位小数展示；**展示值不回灌**  

### P2.6 类型与路由

- `src/types` / `api.ts` 补齐 E04 scope 字段（若缺）  
- `compileall`  

---

## 3. 验证

```bash
python -m compileall -q server
```

自验：

1. demo allow 时 KPI=12856；来源四分项与材料勾稽  
2. allow=0 时 scope=demo 拒绝  
3. contrast≈11970.96 仅只读，不进 KPI  
4. C01 与 E04 同 scope 一致  
5. 无 IFNULL EFFECTIVE 进正式 KPI  

---

## 4. DoD

- [ ] 闸 + KPI + detail + benefit-overview 按上款  
- [ ] 12,856 锚定未改；CANDIDATE 未进主值  
- [ ] 精度与 scope 勾稽自验写入报告  
- [ ] 未做 P3 UI  

## 5. 下游

P2 DoD 后：`_handoff/E04_Trae实施任务单_P3_V1.0_20260724.md`
