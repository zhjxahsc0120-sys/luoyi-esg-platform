# ESG 首页 V0.4 指标口径调整报告（V0.4.5）

**范围：** 仅首页展示名称与数据映射（“显示什么”）  
**禁止项遵守：** 未改数据库、API/KPI 计算、E 组、地图/Cesium、右侧风险模块；未新增 KPI 编码；未写死假统计。

---

## 1. 结论

首页恢复 **12 卡（E4+S4+G4）**：撤销 V0.4.4 隐藏 G02 的合并策略；G01 展示「合规审批与许可」，G02 槽位展示「重大风险专项方案」；S 组与 G04 名称对齐业务口径。数值仍透传既有 `/api/dashboard/kpis` 对应 key 字段。

---

## 2. 调整前后对比

### 2.1 S 社会责任组

| Key | 调整前（V0.3 / 旧展示残留） | V0.4.5 展示名 | 业务含义 |
| --- | --- | --- | --- |
| S01 | 连续安全生产天数（API 旧名） | **安全生产天数** | 连续安全生产天数 |
| S02 | 重大风险源管控 / 较大及以上风险源 | **重大风险源** | 风险对象数量（`safety_risk_point`，如 6 项） |
| S03 | 农民工权益保障 | **工资按时发放率** | 农民工工资支付指标 |
| S04 | 未闭环群众诉求 / 群众诉求闭环 | **群众诉求闭环** | 群众诉求处理情况 |

> 说明：V0.4.3/V0.4.4 已将 S 组短名对齐到接近目标；本版在 catalog 中固化口径说明，fullName 与 label 对齐首页短名。

### 2.2 G 治理合规组

| Key | V0.4.4 展示 | V0.4.5 展示 | 数值映射 |
| --- | --- | --- | --- |
| G01 | 合规审批与专项方案（单卡，含合并叙事） | **合规审批与许可** | 取 **G01** API `value`（现网 Demo 为 `12/12`） |
| G02 | **隐藏**（并入 G01） | **重大风险专项方案**（恢复出卡） | 取 **G02** API `value`（现网 Demo 为 `2/2`） |
| G03 | 设计变更管理 | **设计变更管理**（保持） | G03 API |
| G04 | 内控检查 / fullName 内控与廉洁 | **内控检查** | G04 API（如「正常」） |

**撤销的 V0.4.4 冲突点：**

- 不再将 G01 标为「合规审批与专项方案」；
- 不再把 G02 从首页隐藏；
- 专项方案改为独立 G02 展示槽，而非塞进 G01 标题。

---

## 3. 数据来源与 API 映射

### 3.1 主路径

| 首页卡片 | KPI key | 字段 | 现网示例（`GET /api/dashboard/kpis`，2026-08-05） |
| --- | --- | --- | --- |
| 安全生产天数 | S01 | `items[].value` / `unit` | `89` / `天` |
| 重大风险源 | S02 | `value` / `unit` | `6` / `项` |
| 工资按时发放率 | S03 | `value` / `unit` | `100` / `%` |
| 群众诉求闭环 | S04 | `value` / `unit` | `3` / `项` |
| 合规审批与许可 | G01 | `value`（X/X） | `12/12`（unit `100%`） |
| 重大风险专项方案 | G02 | `value`（透传） | `2/2`（unit `100%`） |
| 设计变更管理 | G03 | `value` | `4/4` |
| 内控检查 | G04 | `value` | `正常` |

展示名称一律由前端 `KPI_HOME_CATALOG` + `applyKpiHomeCatalogLabels` / `normalizeDashboardKpis` overlay，覆盖 API/DB 旧文案。

### 3.2 映射实现层

| 层 | 文件 | 作用 |
| --- | --- | --- |
| Catalog | `frontend/src/data/kpi-catalog.ts` | 首页 label/fullName/unit 策略；`KPI_HOME_HIDDEN_KEYS` 置空 |
| Overlay | `frontend/src/utils/esg-home.ts` | `applyKpiHomeCatalogLabels` |
| Demo 归一化 | `frontend/src/utils/esg-demo.ts` | items→groups 时套用 catalog，不跳过 G02 |
| Store | `frontend/src/stores/dashboard.store.ts` | 加载后 overlay（既有逻辑） |
| Mock 对齐 | `dashboard.mock.ts` / `master.mock.ts` | 离线 12 卡名称与 G 槽位一致 |

### 3.3 相关事实表（业务语义，非本次改库）

| 卡片 | 事实来源（业务） |
| --- | --- |
| S02 重大风险源 | `safety_risk_point` |
| G01 合规审批与许可 | `compliance_procedure` + `permit_record`（展示合并叙事） |
| G02 重大风险专项方案 | `special_plan_approval`（编制/审查/审批/文件关联） |
| G04 内控检查 | `biz_internal_control_issue` 等内控事实 |

专项方案读写 API（`/api/governance/special-plans`）已存在，但 **未进入** `/api/dashboard/kpis` 的 G02 字段；本次按禁令不改 API、不在前端另算假 X/X。

---

## 4. 首页回归说明

| 检查项 | 结果 |
| --- | --- |
| 首页指标数量 | **12**（E4+S4+G4）；G02 重新可见 |
| E 组 | **未改**名称/映射/计算 |
| 地图 / Cesium / traffic-gis-overview / public/gis | **未改** |
| 右侧风险模块 | **未改** |
| KPI 编码 | 仍为 E01–E04 / S01–S04 / G01–G04，无新 code |
| 弹窗深页 | 未改 G01–G04 Modal 业务实现（仅首页卡标题 overlay） |

动态列：`KpiGroupPanel` 仍按 `group.items.length` 设 `--kpi-item-cols`，G 组恢复 4 列。

---

## 5. 剩余缺口（诚实记录）

1. **G01 数值合并完整性**  
   现网 G01 已为 `X/X`（`12/12`），首页采用该字段作为「合规审批与许可」。许可分项在 KPI 列表中仍可能以旧语义留在 G02 数值里；**前端未把 G01+G02 算术合并**（避免假统计）。若业务要求分子分母含全部许可，需后续 API/发布层把合并结果写入 G01。

2. **G02「重大风险专项方案」数值口径**  
   `/api/dashboard/kpis` 的 G02 现网仍为许可类 `X/X`（`2/2`），**未暴露** `special_plan_approval` 的编制/审查/审批/文件关联统计。  
   - 本次：**标签正确**，数值 **透传 G02 API 字段**。  
   - `GET /api/governance/special-plans` 有台账数据，但不属于首页 KPI 载荷；按「不改 API、不硬编码假数」未接入首页卡。  
   - **后续建议（需另开任务）：** 在 KPI 发布/API 层将专项方案完成率写入 G02（或约定字段），前端再只做透传。

3. **G04 弹窗文案**  
   首页卡已为「内控检查」；`G04ComplianceModal` 等详情标题仍可能保留「内控与廉洁」（非本次范围）。

4. **后端 `KPI_HOME_LABELS`（mysql_api）**  
   仍为 V0.3 旧名；前端 overlay 覆盖首页，后端标签未改（禁止改 API）。

---

## 6. 修改文件清单

| 文件 | 变更 |
| --- | --- |
| `frontend/src/data/kpi-catalog.ts` | V0.4.5 catalog；清空 `KPI_HOME_HIDDEN_KEYS` |
| `frontend/src/data/dashboard.mock.ts` | G 组首页 mock 名称/hint |
| `frontend/src/data/master.mock.ts` | 同上 |
| `frontend/src/components/kpi/KpiCard.vue` | 长标题注释对齐新文案 |
| `docs/frontend/ESG首页V0.4指标口径调整报告.md` | 本报告 |

---

## 7. 验证

- [x] 12 项首页指标；S/G 展示名与任务表一致  
- [x] E 组、地图、右侧风险未改动  
- [x] `npm run check`（`vue-tsc -b`）通过

*报告版本：V0.4.5 | 日期：2026-08-05*
