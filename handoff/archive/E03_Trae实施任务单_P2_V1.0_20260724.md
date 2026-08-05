# E03 Trae 实施任务单 · P2（门禁 103 · V1.0 冻结稿配套）

**日期：** 2026-07-24  
**版本：** P2 / V1.0（**开工令**）  
**门禁：** 103（设计已冻结）  
**权威设计：** `_handoff/E03_工作台设计说明_B方案_V1.0冻结稿_20260724.md`  
**前置：** P1 已交付 — `交付_E03_P1双写测数包/`（`V1_1_046` / `V1_1_047`）  
**对标参考：** E02 P2（`_handoff/E02_Trae实施任务单_V1.0_20260723.md` §P2）；壳与闸门可复用，**业务域不得混用**  
**实施方：** Trae  
**本单范围：** **仅 P2**（demo 闸、KPI、列表/详情 API、材料完整度服务端计算、类型与路由）。**不做 UI（P3）**。  

> 不得把冻结稿直接当 Issue。若需改 KPI 主源、状态映射、双写、材料完整度、GIS 类型 → **停工 → 设计变更**。

---

## 0. 硬禁令

- 切换前 KPI / 一级统计**唯一主源** = `water_protection_issue`  
- 状态分项严格按冻结稿 **§2.3 台账 `issue_status` 映射**  
- **`e_closure_case.current_status` 不参与**切换前 KPI 与 overview 分项计数（仅详情展示 / 对账）  
- 台账与案卷**不得相加**  
- 正式环境禁止仅靠前端参数读出 demo  
- **不切主源**到案卷  
- 不修改历史建库脚本、不改正式 GIS 几何  
- 不复用 E02 `environment_problem`；关系类型保持 `E03_WATER_ISSUE`  
- 普通 CLOSED 轨迹**不算**销项材料  
- 本单不做工作台 UI（归 P3）

---

## 1. P2 目标

服务端可读出与 P1 测数一致的正式/演示 KPI 与工作台数据：

| 项 | 期望（demo，allow 时） |
|----|------------------------|
| 未闭环 | **5** |
| 整改中 | **3** |
| 待复查 | **1** |
| 待销项 | **1** |
| 其中逾期 | **1**（叠加） |
| D07 完整度 | **3/4**，含「本轮整改材料待补」类 notes |
| formal 未闭环 | 按事实（通常 0；不得为凑数改数据） |

---

## 2. 执行步骤

### P2.1 服务端 demo 闸

- 配置：`E03_ALLOW_DEMO`（或共用 E 组 demo 闸，须在交付说明写清默认值与优先级）  
- 演示部署默认允许；正式部署默认拒绝 `scope=demo`  
- 拒绝：HTTP **403** 或空 formal 集 + 明确 `code`；打日志  
- **禁止**仅靠前端 query 在正式环境读出 demo  

### P2.2 KPI（首页 E03 卡）

改造 `get_dashboard_kpis`（或等价）中 E03：

```text
formal: COUNT water_protection_issue
        未闭环（issue_status NOT IN 已闭环/已撤销/已合并）
        AND is_demo=0 AND data_nature='formal'
        AND effective_status='EFFECTIVE'（或 P1 已写死的等价谓词）

demo:   仅当 allow_demo 时，同上但 is_demo=1 AND data_nature='demo'
```

- 响应带 `dataNature` / `isDemo` / `scope`，供卡片角标  
- **禁止** `issue_status <> '已闭环'` 单独作为条件  
- **禁止**台账 + 案卷 count 相加  

### P2.3 列表与详情 API

| Method | Path | 说明 |
|--------|------|------|
| GET | `/api/environment/e03/issues` | overview + issues + spatialLinks |
| GET | `/api/environment/e03/issues/{id}` | 二级详情 |

查询参数：`scope=formal|demo`（受闸门约束）。

**overview（全部来自台账映射，冻结 §5.2）：**

```text
total, rectifying, pendingReview, pendingClosure, suspended?(可选), overdueAmong
```

映射：

| 台账 `issue_status` | statusGroup |
|---------------------|-------------|
| 已发现、待整改、整改中 | 整改中 |
| 待复查 | 待复查 |
| 待销项 | 待销项 |
| 暂缓 | 暂缓 |
| 已闭环、已撤销、已合并 | 不入 overview 未闭环 |

等式：`total = rectifying + pendingReview + pendingClosure [+ suspended]`（同源台账）。

**列表项建议字段：**  
`id, businessCode, title, issueType, locationText, status, statusGroup, overdue, deadline, responsibleOrgName, canLocate, spatialLinks[]`

**spatialLinks：**  
`{ featureId, geometryType, role, isPrimary }`  
从 `gis_feature_business_relation`（`relation_type='E03_WATER_ISSUE'`）+ 案卷主关联组装；**不要**只返回虚构 lon/lat。

**详情：**  
- **先**水保「问题概况」六项（冻结 §6.2）：类型、关联对象、合同段/桩号/位置、描述、发现依据、整改要求或影响  
- 再：进度、当前进展、party、statusHistory、evidence、`materialCompleteness`、deadline/overdue、spatialLinks  
- 演示关联 GIS 时，详情须带免责文案字段（前端展示）：  
  `演示关联位置，仅用于验证地图联动，不代表该位置真实发生此问题。`  
- 案卷字段可进详情；**overview / KPI 仍只读台账**  
- 台账↔案卷状态不一致：打标进对账异常（响应可带 `reconcileWarning`），**计数仍以台账为准**

### P2.4 材料完整度（服务端算）

复用 E02 完整度逻辑，域改为 E03；轮次识别 = `e_case_evidence.rectification_round_id`（P1 已补列）。

输出示例：

```json
{
  "requiredRoles": ["FORMAL_NOTICE", "RECTIFICATION_MATERIAL", "REVIEW_OPINION", "…"],
  "coveredRoles": ["…"],
  "pendingRoles": ["RECTIFICATION_MATERIAL"],
  "ratio": "3/4",
  "notes": ["本轮整改材料待补"]
}
```

硬规则：

- D07：退回后**不得**塌成 1/1  
- `CLOSURE_DOCUMENT`：附件 **或** E02 V1.0 §8.4 等价确认；普通 CLOSED history 不算  

### P2.5 旧接口

- 既有 `get_e03_water_protection_detail`（或同类）：加 demo 过滤，避免正式弹窗混 demo；或标记 deprecated，P3 改走新 API  
- 硬编码 GIS map：改为读 `E03_WATER_ISSUE` 关系表  

### P2.6 注册与类型

- `server/app.py` 注册路由  
- `server/mysql_api.py` 实现  
- `src/services/api.ts`：`getE03Issues` / `getE03IssueDetail`  
- `src/types/e03.ts`：列表、详情、overview、spatialLinks、materialCompleteness  

**本单可不接 Dashboard UI**（留给 P3），但类型与 api.ts 须齐备。

---

## 3. 验证

```bash
python -m compileall -q server
```

建议手工/脚本核：

1. `E03_ALLOW_DEMO=0`（或正式配置）时 `scope=demo` → 403 / 空  
2. allow 时 overview：`5 / 3 / 1 / 1 / overdue=1`  
3. D07 detail：`materialCompleteness.ratio === '3/4'`  
4. KPI formal / demo 分计，无双表相加  

---

## 4. 交付物

1. 变更文件列表  
2. API 路径与闸门默认值说明  
3. 自验结果（overview / D07 完整度 / 闸门拒绝）  
4. 与冻结稿偏差（若有，须极短；口径偏差禁止）  

---

## 5. P2 完成定义（DoD）

- [ ] demo 闸生效，正式环境无法仅靠 URL 拉 demo  
- [ ] E03 KPI formal/demo 分计，主源=台账，无双表相加  
- [ ] `GET .../e03/issues` overview 与 P1 数字一致且分项来自台账映射  
- [ ] `GET .../e03/issues/{id}` 含水保概况 + 完整度；D07=3/4  
- [ ] spatialLinks 来自 `E03_WATER_ISSUE`  
- [ ] `compileall` 通过；类型与 api.ts 已加  
- [ ] 未做 P3 UI；未切主源  

---

## 6. 下游

P2 DoD 通过后启用：`_handoff/E03_Trae实施任务单_P3_V1.0_20260724.md`
