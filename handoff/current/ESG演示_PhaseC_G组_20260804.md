# ESG 演示 · Phase C G 组（2026-08-04）

**范围：** Phase C — **G 组 only**（G02/G03/G04 P0 → G01 P1）  
**不含：** S 组（S01–S04）— **NOT STARTED**  
**契约：** `server/migrations/esg_demo_v0_1/esg_demo_api_contract_v0.1.md`  
**红线：** 未改首页布局/主题/碳模块；禁止旧语义（G02≠整改、G03≠履约评价）

---

## 1. API 清单

| Endpoint | 状态 | G 组说明 |
|----------|------|----------|
| `GET /api/dashboard/kpis` | **wired** | Demo overlay；G01–G04 展示名覆盖为 Phase A 口径 |
| `GET /api/dashboard/kpi/G02` | **wired** | `biz_night_construction_record`（Demo 无 `biz_permit` 表时以此为准）；summary=总数/有效/临期/逾期/待审批；objects+detailData |
| `GET /api/dashboard/kpi/G03` | **wired** | `biz_design_change` only；禁止整改语义 |
| `GET /api/dashboard/kpi/G04` | **wired** | `biz_internal_control_issue`；内控字段（类型/等级/证据/关闭） |
| `GET /api/dashboard/kpi/G01` | **wired** | Demo detail 行 + summary 四象限（审批/已完成/未完成/异常） |
| `GET /api/dashboard/kpi/{G0x}/objects/{id}` | **wired** | 对象详情 + 关联 riskWarnings |
| `GET /api/dashboard/risk-warnings` | **wired** | 含 G02/G03/G04（objectId 可下钻）；本轮 seed 无 G01 OPEN 风险 |

### 语义隔离（强制）

| key | 正确语义 | 禁止 |
|-----|----------|------|
| G02 | 许可及施工管控（许可/夜间施工） | 整改闭环 |
| G03 | 设计变更管理 | 参建单位履约评价 / 整改 |
| G04 | 内控与廉洁 | 关键合规资料缺失统计 |
| G01 | 合规审批 / 报批报建 | — |

---

## 2. 页面完成情况

| 优先级 | 能力 | 状态 | 备注 |
|--------|------|------|------|
| **P0** | G02 → `G02LicenseModal` + Demo KPI/objects | **DONE** | 去掉硬编码分桶/预警；失败 error+重试；`focusObjectId` |
| **P0** | G03 → `G03DesignChangeModal`（首页唯一绑定） | **DONE** | `KpiDetailModal` 仅挂 DesignChange；legacy Contractor/Rectification 不解绑到首页 |
| **P0** | G04 → 内控字段对齐 | **DONE** | 列名改为问题描述/类型/等级/证据；去掉假「4 项资料」文案 |
| **P0** | 风险 `kpiKey+objectId` 下钻 G02/G03/G04 | **DONE** | `ComplianceRiskPanel` → `DashboardPage` focusContext → 各 Modal 选中行 |
| **P1** | G01 → Demo API 增强（不重设计） | **DONE** | objects/detailData + 派生图表；无 silent mock 数字 |
| — | S01–S04 Phase C | **NOT STARTED** | 本轮明确排除 |

---

## 3. Mock 情况

| 场景 | 行为 |
|------|------|
| Demo API 可用 | G01–G04 Modal **只吃** `/api/dashboard/kpi/G0x`；图表/摘要从 objects 派生 |
| Demo API 失败（null/网络） | `loadError` + 重试；**不**回填假许可/假整改/假履约列表 |
| 首页 KPI | `/api/dashboard/kpis` Demo overlay；catalog 兜底标签与 Phase A 一致 |
| 遗留文件 | `G03ContractorEvalModal.vue` / `G03RectificationModal.vue` **保留但不挂首页** |
| E 组 / 碳 | 未改 |

---

## 4. 风险下钻情况

| kpiKey | objectId（seed） | 前端行为 |
|--------|------------------|----------|
| G02 | 25002 | 打开 `G02LicenseModal`，选中夜间施工临期记录 |
| G03 | 26002 | 打开 `G03DesignChangeModal`，选中待审批设计变更 |
| G04 | 27002 | 打开 `G04ComplianceModal`，选中未关闭内控问题 |
| G01 | —（无 OPEN 风险） | KPI 点击可开 Modal；风险链就绪，待 seed 有 G01 预警即可 |

规则：只用 `kpiKey + objectId`，**不**按 objectName 反查。

---

## 5. 修改文件清单

### Backend
- `server/esg_demo_api.py` — G01 summary/cards/detail 行；G02 valid 计数；状态中文化；G 组展示名覆盖；kpis 首页名覆盖

### Frontend
- `src/utils/esg-demo.ts` — `demoBizStatusLabel` / `parseFocusObjectId`
- `src/components/modal/KpiDetailModal.vue` — G01–G04 传 `focusObjectId`；仍禁 legacy G03 绑定
- `src/components/modal/G02LicenseModal.vue` — Demo only + 派生图 + object 聚焦
- `src/components/modal/G03DesignChangeModal.vue` — focusObjectId + 状态中文
- `src/components/modal/G04ComplianceModal.vue` — 内控列语义 + Demo only
- `src/components/modal/G01ApprovalModal.vue` — Demo objects + 派生分布

### Handoff
- `_handoff/ESG演示_PhaseC_G组_20260804.md`（本文件）
- `_handoff/NEXT_FOR_TRAE.md`
- `_handoff/handoff_status.json`

---

## 6. 验证

```text
python -c "import esg_demo_api; …G01–G04 detail…"   # OK（模块直调）
python -m compileall -q server                       # OK
npm run check                                        # OK (vue-tsc -b)
```

Live `:8765`：改后端后需**重启** `server/app.py` 才加载新 summary/中文状态；前端 Vite HMR 即可。

手工建议：
1. 首页 G02/G03/G04/G01 名称与 Demo 值
2. 点开四 Modal，确认非整改/履约
3. 风险列表点 G02/G03/G04 → 对应 Modal 且选中 objectId

---

## 7. Gaps / 已知限制

| # | Gap | 影响 |
|---|-----|------|
| 1 | Demo 库无 `biz_permit` / `biz_project_approval` 物理表 | G02 以夜施记录为主；G01 以 `v_esg_demo_kpi_detail` 种子行为主 |
| 2 | G01 无 OPEN 风险样例 | 风险下钻需靠 KPI 点击验证 |
| 3 | S 组未做 | Phase C S 待下一棒 |
| 4 | 服务进程需重启加载后端改动 | 联调注意 |
| 5 | 未 commit | 按规则等待指示 |

---

## 下一棒

- Phase C **S 组**（S01/S03/S04 弹窗；S02 若需）按契约对齐  
- 可选：补 `biz_permit` Demo 表以完整表达 G02「许可+夜施」双源  
- 可选：补 G01 OPEN 风险 seed 便于下钻演示
