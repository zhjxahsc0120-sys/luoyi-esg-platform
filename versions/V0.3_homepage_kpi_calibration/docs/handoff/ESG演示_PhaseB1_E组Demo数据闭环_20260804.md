# ESG 演示 · Phase B.1 E 组 Demo 数据闭环（2026-08-04）

**范围：** Phase B.1 only — E01–E04 首页 KPI / 工作台列表 / 详情对象统一到 ESG Demo API  
**未做：** Phase C（S/G 弹窗深改）  
**布局：** 未改首页 66/34、主题、字体、组件体系、GIS 框架  
**碳足迹：** 未触碰 Carbon 模块

---

## 1. 页面对应 API 清单

| 页面 | 摘要/列表 | 详情 | Demo 数据源 |
|------|-----------|------|-------------|
| 首页 E01–E04 | `GET /api/dashboard/kpis`（`source=esg_demo`，E 值 live overlay） | `GET /api/dashboard/kpi/{E0x}` | `esg_demo_indicator_result` + `aggregate_e0x()` |
| E01 环保风险预警 | `GET /api/environment/e01/events` | `…/e01/events/{id}`；趋势 `…/e01/points/{id}/trend` | `biz_env_monitor_point` + `biz_env_monitor_result`（缺表时自动建表种子）+ `biz_risk_warning` |
| E02 水保风险预警 | `GET /api/environment/e02/objects` | `…/e02/objects/{id}` | `biz_soil_disposal_site` / `biz_temporary_land_use` / `biz_topsoil_stripping` / `biz_construction_slope` + risk |
| E03 生态保护管控 | `GET /api/environment/e03/eco-objects` | `…/e03/eco-objects/{id}` | `biz_ecological_sensitive_area` + `biz_ecological_protection_object` + risk |
| E04 文物保护管控 | `GET /api/environment/e04/cultural-objects` | `…/e04/cultural-objects/{id}` | `biz_cultural_relic_object`（**仅 project_id=1001**） |

共享聚合函数（首页与工作台同源）：`aggregate_e01` / `aggregate_e02` / `aggregate_e03` / `aggregate_e04`（`server/esg_demo_api.py`）。

Legacy 保留（非工作台主路径）：`/api/environment/e02/issues`、`/e03/issues`。

---

## 2. 当前 mock 使用情况

| 模块 | Mock 文件 | 使用策略 |
|------|-----------|----------|
| E01 | `src/data/e01-workspace.mock.ts` | **已停用** — `api.ts` 不再 import；失败返回 `null`，面板显示错误+重试 |
| E02 | `src/data/e02-objects.mock.ts` | **已停用** — 同上 |
| E03 | `src/data/e03-ecology.mock.ts` | **已停用** — 同上 |
| E04 | `src/data/e04-cultural.mock.ts` | 仍保留 **仅 HTTP 失败** 回退（零对象领导态）；成功走 Demo |

> 2026-08-04 用户优先更新：后端 E01/E02/E03 Demo API 已完成 → **禁止** silent mock 冒充 live，避免与首页 KPI 分叉。

---

## 3. 已切换 Demo API 列表

| Endpoint | 状态 |
|----------|------|
| `GET /api/dashboard/kpis` | E01–E04 **live overlay**（与 workspace 同聚合） |
| `GET /api/dashboard/kpi/E01`–`E04` | objects/summary 来自 Demo 表 |
| `GET /api/environment/e01/events` (+detail/trend) | **Demo only**（前端无 mock 回退） |
| `GET /api/environment/e02/objects` (+/{id}) | **Demo only**（前端无 mock 回退） |
| `GET /api/environment/e03/eco-objects` (+/{id}) | **Demo only**（前端无 mock 回退） |
| `GET /api/environment/e04/cultural-objects` (+/{id}) | **Demo 优先**（过滤 project 1001；失败可 mock） |

---

## 4. 修改文件列表

| 文件 | 说明 |
|------|------|
| `server/esg_demo_api.py` | E01 精简表 ensure/seed；`aggregate_e0x`；workspace payloads；KPI overlay；E01–E03 objects 装载 |
| `server/app.py` | E01 Demo 优先；新增 e02/objects、e03/eco-objects；E04 Demo 优先 |
| `server/migrations/esg_demo_v0_1/esg_demo_e01_env_monitor_slim.sql` | E01 Demo DDL 文档副本 |
| `src/services/api.ts` | E01–E03 **移除** mock import/回退；失败 `null`；E04 保持失败 mock |
| `src/components/e01/E01WorkspacePanel.vue` | Demo-only 错误文案 + 重试 |
| `src/components/e02/E02WorkspacePanel.vue` | Demo-only 错误文案 |
| `src/components/e03/E03WorkspacePanel.vue` | Demo-only 错误文案 |
| `src/data/e01-workspace.mock.ts` / `e02-objects.mock.ts` / `e03-ecology.mock.ts` | 标注 OFFLINE/DEV ONLY，主路径不再引用 |
| `_handoff/ESG演示_PhaseB1_E组Demo数据闭环_20260804.md` | 本文件 |
| `_handoff/NEXT_FOR_TRAE.md` | 指针 |
| `_handoff/handoff_status.json` | 状态 |

**未改：** 首页栅格、GIS 框架、Carbon、S/G 弹窗（Phase C）。

---

## 5. 页面验证情况

### 已执行
```text
python -m compileall -q server     # OK
npm run check                      # OK (vue-tsc -b)
```

### Live smoke（:8765，`source=esg_demo`）

| 检查 | 结果 |
|------|------|
| `/api/dashboard/kpis` E01–E04 | E01=2次, E02=81.2%, E03=100%, E04=1处 |
| `/api/environment/e01/events` | anomaly=2, points=3, list=3 |
| `/api/environment/e02/objects` | completion=81.2, objectCount=8, list=8 |
| `/api/environment/e03/eco-objects` | area=2, protected=2, list=4 |
| `/api/environment/e04/cultural-objects` | objectCount=1, list=1 |
| `api.ts` E01–E03 mock imports | **REMOVED**（断言通过） |

---

## 6. Consistency check results E01–E04

| KPI | Homepage value | Workspace summary | Detail/list set | Match |
|-----|----------------|-------------------|-----------------|-------|
| **E01** | 2（超标次数） | anomalyCount=2；monitorPointCount=3；openCount=1 | points {11001,11002,11003} | **PASS** |
| **E02** | 81.2% | completionRate=81.2；objectCount=8 | 8 对象 | **PASS** |
| **E03** | 100% | areaCount=2 + protectedCount=2 | 4 对象 | **PASS** |
| **E04** | 1 处 | objectCount=1 | {23001} | **PASS** |

---

## 7. 已知剩余 / 非本阶段

| 项 | 说明 |
|----|------|
| Phase C S/G | **未启动** |
| E02/E03 GIS 定位 | Demo 对象仍 `canLocate=false` |
| Legacy e02/e03 issues | 仍可用，工作台主 UI 不依赖 |
| E01–E03 mock 文件 | 保留磁盘文件供离线实验，**主路径已断开** |
| E04 失败 mock | 仍保留（领导零对象演示兜底） |

---

## 下一棒

- **Phase C**：S/G 弹窗深对齐（勿改首页栅格）  
- 可选：删除或移出仓库外的 E01–E03 mock 文件
