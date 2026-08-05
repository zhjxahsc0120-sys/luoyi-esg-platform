# E03 Trae 实施任务单 · P1（门禁 103 · V1.0 冻结稿配套）

**日期：** 2026-07-24  
**版本：** P1 / V1.0（**开工令**）  
**门禁：** 103（设计已通过并冻结）  
**权威设计：** `_handoff/E03_工作台设计说明_B方案_V1.0冻结稿_20260724.md`  
**对标参考：** `_handoff/E02_Trae实施任务单_V1.0_20260723.md`（壳与双写流程，勿抄业务域）  
**实施方：** Trae  
**本单范围：** **仅 P1**（测数 / Schema / 双写种子 / GIS 关系 / 自验）。P2 API、P3 UI 另开任务单，勿混入本单。  

> **重要：** 本文件是实现依据；**不得**把设计冻结稿直接当作 GitHub Issue 或替代本单。若需调整 KPI 主源、状态映射、双写、材料完整度、GIS 关系类型 → **停工 → 设计变更**，不得在实现中自行改口径。

---

## 0. 角色与硬禁令

| 角色 | 职责 |
|------|------|
| Trae | 按本单完成 P1，提交可重复执行的增量迁移 + 自验 SQL 报告 |
| Cursor | 对照冻结稿二轮修正（仅在发现偏离时） |
| Codex | 设计已冻结；实现完成后参与验收 |

**禁止：**

- 修改历史建库脚本  
- 台账 KPI 与案卷 KPI 相加  
- 用 `e_closure_case.current_status` 计切换前一级统计 / KPI 分项  
- 为凑正式 KPI=0 批量把来源不明记录改成 demo  
- 删除或擅自「迁出」历史记录  
- 修改正式 GIS 要素坐标 / 几何  
- 复用 E02 的 `environment_problem` 作为 E03 关系类型  
- 用普通 CLOSED 轨迹冒充销项材料  
- 启动切主源到案卷（仍处**切换前**）  
- 本单内做 P2/P3（工作台 UI / 新 API 可另单）

---

## 1. P1 目标（可独立验收）

在库内形成可演示的 E03 双写测数，使后续 P2/P3 能读出台账主源数字：

| 验收项 | 期望 |
|--------|------|
| 正式有效未闭环 | **由数据事实决定**（目标常为 0；不得用批量改性质凑数） |
| 演示未闭环 | **5**（D01+D02+D03+D04+D07） |
| 演示·整改中 | **3**（D01、D02、D07） |
| 演示·待复查 | **1**（D03） |
| 演示·待销项 | **1**（D04） |
| 演示·其中逾期 | **1**（仅 D02，叠加） |
| D05 / D06 | 各 1 条，**不计**未闭环 |
| D07 材料完整度 | **3/4**（本轮整改待补） |
| 双写 | 每条演示台账 ↔ 一条 `e_closure_case(E03_WATER)` |
| GIS | `relation_type='E03_WATER_ISSUE'`，仅关系、未改几何 |

等式：`5 = 3 + 1 + 1`（全部来自台账 `issue_status` 映射）。

---

## 2. 动手前必读

| 位置 | 说明 |
|------|------|
| 冻结稿 §2.3 / §2.4 / §2.5 / §2.6 | 主源、SQL、双写、存量核实 |
| 冻结稿 §5.3.1 / §5.3.2 / §8 / §9 | D01～D07、材料轮次、GIS |
| `water_protection_issue` | 现网台账；核查 `is_demo` / `data_nature` / `effective_status` |
| `e_closure_case` 等 | `case_domain` 已有 `E03_WATER`（见 `server/e_group/enums.py`） |
| 现网种子 | `710001–710007` 等 → 按 §2.6 **逐条核实** |
| E02 P1 任务单 | 双写步骤模板；域改为水保 |

---

## 3. 执行步骤（严格按序）

### P1.1 Schema 闸（增量、幂等）

1. 检查 `water_protection_issue` 是否具备：`is_demo`、`data_nature`；以及 `effective_status`（或写明等价有效性谓词并记入本单附录）。  
2. 检查 `e_case_evidence` 是否具备 `rectification_round_id`（D07 必需）。  
3. **若缺字段：** 新增独立迁移（建议  
   `server/migrations/e_group_e01_v1_1/V1_1_0xx__e03_water_issue_demo_fields.sql`  
   或独立目录，与现有 `migrate_v1_1.py` 约定一致）。  
4. Check 约束建议：`(data_nature='demo' AND is_demo=1) OR (data_nature IN ('formal','platform_calc') AND is_demo=0)`。  
5. **不得**改写 `V1_1_000`～既有历史脚本。

**`effective_status` 缺省时的等价谓词（须二选一写死）：**

- 方案 A：增量补列，默认历史 formal 有效行为 `EFFECTIVE`，待核实清单除外；或  
- 方案 B：服务端/SQL 等价：`IFNULL(effective_status,'EFFECTIVE')='EFFECTIVE'`（仅当表无列时；有列后切回正式谓词）。  

选定方案后写入 PR 说明，P2 不得另起炉灶。

### P1.2 存量 `710001–710007` 逐条核实

| 核实结果 | 动作 |
|----------|------|
| 能证明历史演示种子 | 原位补标 `is_demo=1`、`data_nature='demo'` |
| 能证明真实业务 | 保留 formal |
| 来源不明 | **待核实清单**（附件进 PR），暂不纳入正式有效统计 |

输出表：`id | 原状态 | 判定 | 处理 | 证据简述`。

### P1.3 双写种子 E03-D01～D07

对冻结稿 §5.3.1 每一条：

| 步骤 | 表 | 要求 |
|------|-----|------|
| A | `water_protection_issue` | `is_demo=1`、`data_nature='demo'`；`issue_status` 按逐项表；D02 `overdue`；水保类型；业务键与 `E03-D0x` 对齐；有效性满足 §2.4 |
| B | `e_closure_case` | `case_domain='E03_WATER'`；`source_table='water_protection_issue'`；`source_record_id`=A.id；状态英文字段与台账映射**一致**；`is_demo=1`、`data_nature='demo'` |
| C | `e_case_party` | 发现 / 整改 / 复查（销项）角色 |
| D | `e_case_status_history` | ≥2 条；**D07 含复查退回**轨迹与原因 |
| E | `e_case_evidence` | 按材料要点挂角色；`rectification_round_id` 区分上轮/本轮；D07 本轮整改**缺**；**不得**用 status_history 冒充 `CLOSURE_DOCUMENT` |
| F | GIS | `gis_feature_business_relation.relation_type='E03_WATER_ISSUE'`；挂**已有**弃渣/边坡/水源等本体要素；**禁止 UPDATE 几何** |
| G | 可选 | `document_record` 占位 |

**D05：** 销项材料或满足 E02 V1.0 §8.4 的等价销项确认写入 evidence。  
**D06：** `issue_status=已合并` / 案卷 `MERGED`，不计 KPI。  
**D07：** 完整度验收 **3/4**（通知+上轮整改+退回意见有；本轮整改无）。

建议台账 id 段避开 `710001–710007`（如 `711001+`），迁移**幂等**（按 `business_code`/`source_business_key` 先清 demo 再插，或存在则 skip）。

### P1.4 自验 SQL（必须写入交付报告）

```sql
-- 正式有效未闭环（事实结果；不得为凑 0 批量改性质）
SELECT COUNT(*) AS formal_open
FROM water_protection_issue
WHERE issue_status NOT IN ('已闭环','已撤销','已合并')
  AND is_demo = 0
  AND data_nature = 'formal'
  AND IFNULL(effective_status,'EFFECTIVE') = 'EFFECTIVE';

-- 演示未闭环 = 5
SELECT COUNT(*) AS demo_open
FROM water_protection_issue
WHERE issue_status NOT IN ('已闭环','已撤销','已合并')
  AND is_demo = 1
  AND data_nature = 'demo'
  AND IFNULL(effective_status,'EFFECTIVE') = 'EFFECTIVE';

-- 状态分项（仅台账映射；禁止用案卷计）
SELECT
  SUM(issue_status IN ('已发现','待整改','整改中')) AS rectifying,  -- 期望 3
  SUM(issue_status = '待复查') AS pending_review,                 -- 期望 1
  SUM(issue_status = '待销项') AS pending_closure,                -- 期望 1
  SUM(IFNULL(overdue,0)=1 AND issue_status NOT IN ('已闭环','已撤销','已合并')) AS overdue -- 期望 1
FROM water_protection_issue
WHERE is_demo=1 AND data_nature='demo'
  AND IFNULL(effective_status,'EFFECTIVE')='EFFECTIVE';

-- 一对一双写
SELECT c.case_code, c.source_record_id, w.id, w.issue_status, c.current_status
FROM e_closure_case c
JOIN water_protection_issue w ON w.id = c.source_record_id
WHERE c.case_domain='E03_WATER' AND c.is_demo=1;

-- GIS 关系类型
SELECT relation_type, COUNT(*) 
FROM gis_feature_business_relation
WHERE relation_type='E03_WATER_ISSUE'
GROUP BY relation_type;
```

台账↔案卷状态映射不一致的行 → 列入**对账异常清单**（不得前端二选一）；P1 种子应避免故意制造不一致。

### P1.5 交付物

1. 增量迁移 SQL（+ migrator 登记，若需要）  
2. 存量核实表 + 待核实清单  
3. 自验 SQL 结果截图或文本（含 `5=3+1+1`、D07=3/4 说明）  
4. 简短 PR/交接说明：未改历史脚本、未改正式几何、未切主源  

**验证命令（本仓约定）：**

```bash
python -m compileall -q server
```

（P1 以库侧为主；前端 `npm run check/build` 留到 P3。）

---

## 4. P1 完成定义（DoD）

- [ ] Schema 增量已上库且幂等  
- [ ] 存量逐条核实完成，无「为凑 0 批量改 demo」  
- [ ] D01～D07 双写齐全，GIS=`E03_WATER_ISSUE`  
- [ ] 演示：未闭环 5；整改中 3；待复查 1；待销项 1；逾期 1  
- [ ] D07 材料完整度可证明为 3/4  
- [ ] 切换前计数自验全部基于 `water_protection_issue`，未用案卷分项  
- [ ] 报告齐备；未启动切主源；未改代码业务口径以外的设计冻结项  

---

## 5. 下游任务单（已另编）

| 阶段 | 任务单 |
|------|--------|
| P2 | `_handoff/E03_Trae实施任务单_P2_V1.0_20260724.md` |
| P3 | `_handoff/E03_Trae实施任务单_P3_V1.0_20260724.md` |

---

## 6. 当前状态

**P1 已交付**（见 `交付_E03_P1双写测数包/`）。后续按 P2 → P3 任务单执行。
