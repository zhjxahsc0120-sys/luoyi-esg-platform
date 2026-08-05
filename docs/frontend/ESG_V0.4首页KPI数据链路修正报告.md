# ESG V0.4 首页 KPI 数据链路修正报告

**日期**：2026-08-05  
**范围**：首页驾驶舱 G01 / G02 / S02 数据口径（API 聚合 → 详情 → 前端适配），不改库表、不改 E 组 / 地图 / 右栏 / KpiCard、不改 12 卡数量；G04 保持现有前端 Demo overlay（合规管理天数 / 89 天）。

---

## 1. 修正前（Before）

| 指标 | 问题 |
|------|------|
| **G01** | 首页展示名已改为「合规审批与许可」，但数值仍走 V0.3 发布层（常见为 `12/12`），**未合并** `compliance_procedure` + `permit_record`；存在「名称已换、数据未换」风险。禁止的拼接口径（如 `12/12 + 2/2`）与「只读一表」均不符合 V0.4。 |
| **G02** | 展示名「重大风险专项方案」，数据仍来自 **夜施/许可** 链路（`biz_night_construction_record` / 旧许可统计，常见 `2/2`），**未接入** `safety_risk_point → special_plan_approval`。 |
| **S02** | 名称「重大风险源」；需确认计数仅来自 `safety_risk_point`（风险对象），而非专项方案审批表。 |
| **G04** | 正式模型不变；首页继续用前端 Demo overlay，不在本次修改。 |

依据文档：`docs/frontend/G01_G02首页指标链路核查报告.md`、`docs/frontend/ESG首页V0.4指标口径调整报告.md`。

---

## 2. 修正后（After）

### 2.1 后端聚合（新建/沿用）

`backend/esg_v04_kpi_aggregate.py`：

| 函数 | 口径 |
|------|------|
| `aggregate_g01_compliance_and_permit` | 两表分别计数后相加：`done = proc_done + perm_done`，`due = proc_total + perm_total` → 展示 `已完成/应完成`（如 `2/12`）。审批完成 = `status==已完成`；许可完成 = 非临期/逾期等开放态。**禁止**字符串拼接两个 `X/X`。 |
| `aggregate_g02_special_plans` | 应完成 = 在管重大/较大 `safety_risk_point`；已完成 = 对应 `special_plan_approval` 审批通过且关联审批文件。**不再读** `biz_night_construction_record`。 |
| `aggregate_s02_risk_points` | 仅 `COUNT(safety_risk_point)`（重大/较大且未销号）。 |

### 2.2 API 接线（`backend/esg_demo_api.py`）

- `GET /api/dashboard/kpis`：对 G01 / G02 / S02 做 **live overlay**（覆盖 V0.3 发布值）。
- `GET /api/dashboard/kpi/{key}`：G01/G02 详情 `value` / `summary` / `objects` / `dataSource` 走同一聚合；G02 摘要回退逻辑由「许可临期/逾期」改为专项方案编制/审批/文件字段。
- 详情对象日期字段 JSON 序列化修复（`date` → ISO 字符串），避免详情接口因 `TypeError: date is not JSON serializable` 断连。

### 2.3 前端适配

- `kpi-catalog.ts`：G01/G02 展示名与口径注释（名称 overlay 不变）。
- `esg-demo.ts` / `esg-home.ts`：继续以 API `items[]` 数值为准，catalog 只覆盖 label；G04 仍前端 Demo 天数 overlay。
- Mock 对齐现网样例：`dashboard.mock.ts`、`master.mock.ts`、`esg-home.mock.ts`（G01=`2/12`，G02=`0/8`，S02=`8`；详情摘要改为合并/专项方案语义）。

---

## 3. 全量映射表

| 指标 | 展示名称 | API | 数据来源 | 状态 |
|------|----------|-----|----------|------|
| E01 | 环保风险预警 | `/api/dashboard/kpis` + E01 既有聚合 | E 组监测/异常（不变） | 保持 |
| E02 | 水保风险预警 | 同上 | E02 水保对象（不变） | 保持 |
| E03 | 生态保护管控 | 同上 | E03 生态对象（不变） | 保持 |
| E04 | 文物保护管控 | 同上 | `biz_cultural_relic_object`（不变） | 保持 |
| S01 | 安全生产天数 | `/api/dashboard/kpis` | S01 确认批次 / 连续安全生产天数（现网样例 **89 天**） | 已核对 |
| S02 | 重大风险源 | `/api/dashboard/kpis` live overlay | **`safety_risk_point` only**（现网 **8 项**） | 已修正/已核 |
| S03 | 工资按时发放率 | `/api/dashboard/kpis` | `biz_worker_payment_summary`（现网 **100%**） | 保持 |
| S04 | 群众诉求闭环 | `/api/dashboard/kpis` | 群众诉求台账（不变） | 保持 |
| G01 | 合规审批与许可 | `/api/dashboard/kpis` + `/api/dashboard/kpi/G01` | **`compliance_procedure` + `permit_record` 合并计数**（现网 **2/12**，hint：审批 2/7 · 许可 0/5） | 已修正 |
| G02 | 重大风险专项方案 | `/api/dashboard/kpis` + `/api/dashboard/kpi/G02` | **`safety_risk_point` → `special_plan_approval`**（现网 **0/8**，编制 1/8） | 已修正 |
| G03 | 设计变更管理 | `/api/dashboard/kpis` | `biz_design_change`（不变） | 保持 |
| G04 | 合规管理天数 | 首页前端 overlay（API 可仍为「正常」） | `G04_HOME_DEMO_DISPLAY` → **89 天** | 保持 Demo |

---

## 4. 现网核验记录（2026-08-05）

环境：MySQL `127.0.0.1:3307/luoyi_esg` + Backend `8765`（需从 legacy Trae `.env` 加载 `LUOYI_MYSQL_PASSWORD`；仓库根目录可无 `.env`）。

```
GET /api/dashboard/kpis  → items.length = 12
G01 = 2/12 (17%)   hint=审批 2/7 · 许可 0/5
G02 = 0/8  (0%)    hint=编制 1/8 · 审批通过 0/8 · 有审批文件 0/8
S02 = 8 项
S01 = 89 天
S03 = 100%
```

详情：

| 路径 | value | dataSource | objectType |
|------|-------|------------|------------|
| `/api/dashboard/kpi/G01` | `2/12` | `compliance_procedure + permit_record (V0.4 merge)` | `compliance_procedure`, `permit_record`（共 12） |
| `/api/dashboard/kpi/G02` | `0/8` | `safety_risk_point → special_plan_approval (V0.4)` | `safety_risk_point`, `special_plan_approval`（共 8） |
| S02 首页值 | `8` | `safety_risk_point` | 聚合仅风险点计数 |

对照：**已不是** V0.3 的 G01=`12/12`、G02 夜施许可=`2/2`。

---

## 5. 回归结论

| 检查项 | 结果 |
|--------|------|
| 仍为 **12** 张 KPI 卡 | 通过（`items.length=12`，`KPI_HOME_HIDDEN_KEYS` 为空） |
| E 组数值链路未改 | 通过（未改 E 聚合/地图/右栏/KpiCard） |
| S 组：S01/S03 保持；S02 仅风险点 | 通过 |
| G 组名称与数据一致 | 通过（G01/G02 名+合并/专项方案数据一致） |
| G04 Demo overlay | 通过（未改正式模型；首页仍天数展示） |
| API / 页面可核验 | 通过（本机重启带密码后 health.mysql.ok；kpis + G01/G02 detail OK） |

---

## 6. 代码变更清单

| 文件 | 变更要点 |
|------|----------|
| `backend/esg_v04_kpi_aggregate.py` | G01/G02/S02 聚合；日期 JSON 安全 |
| `backend/esg_demo_api.py` | kpis overlay、详情 overlay、G02 summary 回退、objects 加载 |
| `frontend/src/data/dashboard.mock.ts` | 首页/详情 mock 对齐 V0.4 数值与摘要 |
| `frontend/src/data/master.mock.ts` | G01/G02/S02 mock 对齐 |
| `frontend/src/data/esg-home.mock.ts` | G01/G02/S02 mock 对齐 |
| `frontend/src/data/kpi-catalog.ts` | 口径注释（既有） |

---

## 7. 重启说明（若 health 报 Access denied / password: NO）

1. 确认 MySQL 监听 `3307`（`mysqld --defaults-file=E:\Mysql\my-luoyi.cnf`）。  
2. 从 `C:\ESG_Project\.env` 或 legacy Trae `.env` 加载 `LUOYI_MYSQL_*`。  
3. 结束占用 `8765` 的进程后，在 `backend` 目录启动 `python app.py`（进程环境须带密码）。  
4. 校验：`GET http://127.0.0.1:8765/health` 中 `mysql.ok=true`，再查 `/api/dashboard/kpis`。  
5. 或执行：`powershell -File C:\ESG_Project\scripts\start-esg.ps1`。

---

## 8. 结论

V0.4 首页 KPI **数据链路**已落到业务表聚合：G01 为审批+许可合并的 `已完成/应完成`；G02 为风险源→专项方案；S02 为风险源计数。现网样例值为 **G01=2/12、G02=0/8、S02=8**，与旧版 **12/12 / 2/2** 已区分。G04 仍为约定 Demo overlay。
