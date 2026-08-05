# ESG 演示 Phase B — E 组工作台（2026-08-04）

**范围：** Phase B only（E04 → E01 → E02 → E03）  
**未做：** Phase C（S/G 弹窗深改）、Phase D（风险下钻）  
**布局：** 未改 66/34、卡片尺寸、主题、字体、导航  
**碳足迹：** 未触碰 `CarbonBenefitPanel` / `CarbonBenefitModal` / E04 碳 Modal 主路径

---

## 完成项（按优先级）

### E04 文物保护管控（领导演示优先）

- 摘要四格：**文物调查状态 / 保护对象 / 措施落实率 / 风险状态**
- **零对象友好态**：`文物调查已完成` · `保护对象 0` · `风险状态 正常`（禁止「暂无数据」）
- Mock：`src/data/e04-cultural.mock.ts`；`getE04CulturalObjects` API 优先，失败回退 mock（默认零对象）
- 面板：`E04CulturalRelicWorkspacePanel` 巩固，未重设计 chrome

### E01 环保风险预警

- 标题与 catalog：**环保风险预警**
- 顶部：监测点数量、异常数量、未闭环数量、风险等级
- 列表：监测点 / 检测值 / 状态 / 风险；类型筛选条保留
- 详情：基础信息、检测值、整改记录（趋势仍可走地图 `E01MapSummaryCard`）
- Mock：`src/data/e01-workspace.mock.ts` + API normalize/fallback

### E02 水保风险预警

- **主设计改为对象域**（弃土场 / 临时用地 / 表土剥离 / 边坡复绿），不再以「未闭环环境问题」为主叙事
- 摘要：对象分类计数 + 风险/完成率/恢复提示
- 列表 + 内嵌详情（对象信息 / 空间位置 / 措施要求 / 整改恢复）
- Mock：`getE02Objects` / `getE02ObjectDetail` → `/api/environment/e02/objects` 规划路径 + mock
- 旧 `getE02Issues` 仍保留（legacy）；地图侧旧问题闭环弹窗暂不挂载，避免对象 ID 冲突

### E03 生态保护管控

- 标题与 catalog：**生态保护管控**
- 对象：生态敏感区域 + 生态保护对象；展示对象 / 位置 / 风险
- Mock：`getE03EcoObjects` → `/api/environment/e03/eco-objects` + mock
- 旧 `getE03Issues` 保留

### 首页接线

- E01–E04 仍打开各自 workspace；E04 仍为文物工作台（非碳）
- `kpi-catalog` / `dashboard.mock` / `esg-home.mock` / `master.mock` E 组标签对齐演示名

---

## 修改文件

| 文件 | 说明 |
|------|------|
| `src/components/e04/E04CulturalRelicWorkspacePanel.vue` | 调查状态 + 零对象三句空态 |
| `src/components/e01/E01WorkspacePanel.vue` | 环保风险预警统计/列表/详情 |
| `src/components/e02/E02WorkspacePanel.vue` | 水保对象域工作台 |
| `src/components/e03/E03WorkspacePanel.vue` | 生态敏感区/保护对象工作台 |
| `src/components/gis/GisOverviewCesiumPanel.vue` | GIS 类型放宽；E02/E03 旧闭环弹窗暂卸 |
| `src/views/DashboardPage.vue` | E02/E03 对象类型与筛选 |
| `src/types/e01.ts` / `e02.ts` / `e03.ts` / `e04-cultural.ts` | Phase B 字段与对象契约 |
| `src/data/e01-workspace.mock.ts` | **新增** |
| `src/data/e02-objects.mock.ts` | **新增** |
| `src/data/e03-ecology.mock.ts` | **新增** |
| `src/data/e04-cultural.mock.ts` | **新增** |
| `src/services/api.ts` | E 组 mock fallback + E02/E03 objects API |
| `src/data/kpi-catalog.ts` | E01–E04 演示名 |
| `src/data/dashboard.mock.ts` | E 组首页 mock 标签/E04 hint |
| `src/data/esg-home.mock.ts` | E 组数值与 E04 零对象 hint |
| `src/data/master.mock.ts` | E 组标签对齐 |
| `_handoff/NEXT_FOR_TRAE.md` | 指针更新 |
| `_handoff/handoff_status.json` | 状态更新 |
| `_handoff/ESG演示_PhaseB_E组工作台_20260804.md` | 本文件 |

---

## 验收核对

- [x] E04 零对象文案：调查已完成 / 对象 0 / 风险正常（无「暂无数据」）
- [x] E01 顶部三量 + 风险；列表含检测值/状态
- [x] E02 四类水保对象为主，非「未闭环环境问题」主壳
- [x] E03 敏感区 + 保护对象
- [x] 首页 KPI 名：环保风险预警 / 水保风险预警 / 生态保护管控 / 文物保护管控
- [x] 碳模块未改；布局未改
- [x] `npm run check`（`vue-tsc -b`）通过
- [ ] 截图：见下方

---

## 验证说明

```bash
npm run check
# 可选：npm run build
# 手工：npm run dev → http://127.0.0.1:5173/
# 点击 E04 → 确认零对象三句（API 若返回有对象则展示列表；mock 默认 0）
# 点击 E01/E02/E03 → 确认标题与对象域
```

**截图：** 本环境浏览器 MCP 未稳定起页抓图。请本地 `npm run dev` 后对 E04 零对象态、E01 列表、E02 四类对象、E03 生态对象各截一帧归档。

**E04 mock 策略：** API 不可用时默认 **零对象领导演示态**。若需 mock 三条对象，设 `VITE_E04_MOCK_OBJECTS=1`。

---

## 已知问题 / 交 Phase C

| 项 | 说明 | 阶段 |
|----|------|------|
| E02/E03 GIS 本体高亮 | mock 对象 `canLocate=false`、无 spatialLinks；真库对象需 Demo API 补 feature | 后端/GIS |
| E02/E03 地图侧旧闭环弹窗 | Phase B 暂卸，详情在工作台内 | 可选恢复 |
| 后端 `/e02/objects` `/e03/eco-objects` | 前端已规划；现 mock | Demo API |
| G03 设计变更 Modal | 未动 | **Phase C** |
| 风险清单下钻 | 未动 | **Phase D** |
| API 可用时 E04 若仍返回 3 对象 | 走 API 列表，不强制零对象（零对象以 mock/空表演示） | 产品/数据 |

---

## 下一棒

**Phase C**：S/G 弹窗对齐（含 G03 设计变更许可 Modal）。勿改首页栅格。
