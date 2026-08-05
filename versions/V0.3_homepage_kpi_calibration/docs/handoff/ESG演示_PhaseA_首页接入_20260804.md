# ESG 演示 Phase A — 首页接入（2026-08-04）

**范围：** Phase A only（首页 ESG 状态 / 指标入口 / G 命名 / Mock API）  
**未做：** Phase B（E 工作台）、C（S/G 弹窗深改）、D（风险清单下钻）  
**布局：** 未改 66/34、卡片尺寸、主题、字体、导航

---

## 完成项

1. **G 首页命名对齐任务书**
   - G02 → **许可及施工管控**
   - G03 → **设计变更许可**
   - 来源：`kpi-catalog.ts` + `dashboard.mock.ts` + store 强制 overlay（即使后端仍返回旧文案）

2. **ESG 首页状态服务层**
   - 契约：`src/types/esg-home.ts`
   - Mock：`src/data/esg-home.mock.ts`
   - API：`getEsgHomeStatus()` in `src/services/api.ts`
   - **真实 Demo API（规划）：** `GET /api/dashboard/esg-home-status`
   - **过渡：** 组合 `GET /api/dashboard/kpis` + `GET /api/dashboard/panels`；均失败则前端 mock
   - Store：`loadEsgHomeStatus()` 合并组状态（风险/红黄蓝计数文案）+ 指标 value/hint + ComplianceRiskPanel RYB

3. **指标入口**
   - E01–E04 / S02 仍走既有 workspace；其余 KPI 仍走 `KpiDetailModal`
   - **微小修复：** G02 改绑 `G02LicenseModal`（不再误开整改 Modal）

4. **ComplianceRiskPanel**
   - 继续消费 store 红黄蓝 metrics + 预警清单；数值由 `getEsgHomeStatus` / panels 注入，无硬编码在 Vue 模板

---

## 修改文件

| 文件 | 说明 |
|------|------|
| `src/data/kpi-catalog.ts` | G02/G03 正式口径 |
| `src/data/dashboard.mock.ts` | 首页 KPI + G02/G03 detail mock 对齐 |
| `src/types/esg-home.ts` | **新增** ESG home 契约 |
| `src/data/esg-home.mock.ts` | **新增** mock 载荷 |
| `src/utils/esg-home.ts` | **新增** catalog overlay + merge |
| `src/services/api.ts` | `getEsgHomeStatus()` |
| `src/stores/dashboard.store.ts` | bootstrap 调 ESG home；暴露 source/error |
| `src/components/modal/KpiDetailModal.vue` | G02 → G02LicenseModal |
| `src/components/modal/G02LicenseModal.vue` | 标题改为「许可及施工管控」 |
| `_handoff/NEXT_FOR_TRAE.md` | 指针更新 |
| `_handoff/handoff_status.json` | 状态更新 |
| `_handoff/ESG演示_PhaseA_首页接入_20260804.md` | 本文件 |

---

## 验收核对

- [x] 首页 G02/G03 文案与任务书一致（catalog + mock + overlay）
- [x] E/S/G 组头可显示风险/红黄蓝摘要（`group.status`）
- [x] ComplianceRiskPanel 红黄蓝 + 清单仍可用
- [x] 点击入口：E 组 workspace / S·G modal 路径保留；G02 打开许可 Modal
- [x] 无布局/主题/导航改动
- [ ] 截图：见下方「验证说明」（本机若未起 dev server 则手工点验）

---

## 已知问题 / 阻塞（交 Phase B/C）

| 项 | 说明 | 阶段 |
|----|------|------|
| G03 弹窗仍为履约评价空态壳 | 首页已改「设计变更许可」，Modal 未重建 | **Phase C** |
| 后端 `mysql_api.py` 首页 G02 仍可能按「整改」聚合 | 前端 catalog overlay 盖住标签；数值待 Demo API 正式对齐 | 后端 Demo |
| `/api/dashboard/esg-home-status` 未实现 | 前端已定义契约 + mock/compose | 后端 |
| 风险清单点击下钻 | 有意未做 | **Phase D** |
| E01–E04 工作台内容巩固 | 有意未做 | **Phase B** |

---

## 验证说明

```bash
npm run check
# 可选：npm run build
# 手工：npm run dev → 打开首页
# 核对：G02=许可及施工管控、G03=设计变更许可、组头风险文案、右栏红黄蓝
# 点击 G02 应打开许可 Modal（非整改）
```

截图：浏览器 MCP / Playwright 本环境未能成功抓图。请本地 `npm run dev`（已可起于 `http://127.0.0.1:5173/`）后对首页右栏 KPI + 综合风险面板截图归档。

---

## 下一棒（Phase B）

巩固 E01–E04 工作台字段/空态（E04 文物三句空态）；**不要**在 B 阶段改首页栅格或 G03 设计变更 Modal（那是 C）。
