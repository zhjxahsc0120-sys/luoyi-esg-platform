# E01环保风险预警二级分析区域 Class A 实现报告

> 版本：V1.0  
> 日期：2026-08-07  
> 范围：仅右侧二级分析区域（红框），E01 环保风险预警

---

## 一、页面结构

### 1.1 系统边界（已遵守）

| 区域 | 是否修改 |
|---|---|
| 顶部 E/S/G 一级指标卡 | ❌ 未改 |
| 左侧 Cesium 地图 | ❌ 未改 |
| 底部建设阶段时间轴 | ❌ 未改 |
| 首页导航 / 布局 | ❌ 未改 |
| **右侧二级分析区（`dashboard-e01-slot`）** | ✅ 已升级 |

未使用全屏弹窗、未新增三栏大屏、未在右侧内嵌第二套地图。

### 1.2 右侧 Class A 布局（自上而下）

```
┌─────────────────────────────────┐
│ 环保风险预警 🟢    [正常|关注|异常] │ ×
├─────────────────────────────────┤
│ 当前风险  N项                      │
├─────────────────────────────────┤
│ [异常] [全部] [正常]               │
│ ── 监测点对象列表（可滚动）──      │
│  W01 地表水监测点    正常          │
│  W02 废水排放点      COD超标       │
├─────────────────────────────────┤
│ 详情：基础信息 + 监测结果表        │
│ （异常时展示异常指标块）           │
├─────────────────────────────────┤
│ 趋势分析  [趋势折线][统计柱状]     │
│ ECharts 折线 / 柱状               │
└─────────────────────────────────┘
```

### 1.3 组件职责

| 组件 | 路径 | 职责 |
|---|---|---|
| `ESGRiskPanel` | `components/esg-class-a/ESGRiskPanel.vue` | Class A 母版壳：加载数据、摘要、列表+详情+趋势编排 |
| `ESGRiskObjectList` | `components/esg-class-a/ESGRiskObjectList.vue` | 对象列表 + 异常/全部/正常筛选 |
| `ESGRiskDetail` | `components/esg-class-a/ESGRiskDetail.vue` | 基础信息、因子表、异常块 |
| `ESGTrendChart` | `components/esg-class-a/ESGTrendChart.vue` | 折线趋势 / 超标次数柱状 |
| `E01WorkspacePanel` | `components/e01/E01WorkspacePanel.vue` | E01 接入层，挂载 `ESGRiskPanel` |

---

## 二、修改文件

| 文件 | 变更 |
|---|---|
| `src/components/esg-class-a/ESGRiskPanel.vue` | 新增，Class A 母版 |
| `src/components/esg-class-a/ESGRiskObjectList.vue` | 新增 |
| `src/components/esg-class-a/ESGRiskDetail.vue` | 新增 |
| `src/components/esg-class-a/ESGTrendChart.vue` | 新增 |
| `src/types/esg-class-a.ts` | 新增，展示层类型 |
| `src/utils/esg-e01-presenter.ts` | 新增，E01 API → 展示模型 |
| `src/components/e01/E01WorkspacePanel.vue` | 改为挂载 `ESGRiskPanel` |
| `src/styles/layout.scss` | `.esg-risk-panel` 纳入右侧 slot 高度规则 |

**未修改**：`DashboardPage.vue` 布局、`GisOverviewCesiumPanel`、E02/E03/S/G 工作区。

---

## 三、数据字段映射

### 3.1 数据流

```
MySQL e01_* / biz_env_*
    ↓
GET /api/environment/e01/events
GET /api/environment/e01/events/{id}
GET /api/environment/e01/points/{id}/trend
    ↓
utils/esg-e01-presenter.ts
    ↓
types/esg-class-a.ts（EsgRiskObjectCard / EsgRiskObjectDetail）
    ↓
ESGRisk* 组件
```

### 3.2 字段转换（禁止 DB 直出）

| API / DB | 页面展示 |
|---|---|
| `point_code` | 监测点编号 |
| `point_name` | 监测点名称 |
| `monitor_category` | 施工废水/扬尘/噪声监测 |
| `discoveredAt` / `sampled_at` | 2026年6月24日 |
| `detected_value` + `unit` | 检测值、单位（分列） |
| `limit_value` | 标准限值 |
| `judgement` PASS | 正常 |
| `judgement` FAIL / EXCEEDED | 异常 |
| `judgement` NO_STANDARD | 未评价 |
| `case_status` NO_ISSUE | 正常 |
| `case_status` RECTIFYING | 整改中 |
| `longitude` / `latitude` | 保留在 `E01OpenPoint`，经 `selectPoint` 联动左侧 GIS |

### 3.3 业务对象模型

- **列表**：按监测点聚合（`openPoints`），不展示单行 pH/COD 记录
- **详情**：该点初检因子表 + 可选异常块 + 整改措施
- **筛选**：`isE01AbnormalPoint()` 判定异常（超标倍数、状态关键词、未闭环 case）

---

## 四、API 调用情况

| 时机 | 接口 | 用途 |
|---|---|---|
| 面板 `onMounted` | `GET /api/environment/e01/events` | 监测点列表、`overviewReady` → GIS 标点 |
| 选中对象 | `GET /api/environment/e01/events/{eventId}` | 详情区 |
| 选中对象 / 切换因子 | `GET /api/environment/e01/points/{pointId}/trend` | 趋势折线；`factorOptions.exceedCount` 用于柱状 |

GIS 联动：沿用 `DashboardPage` 既有 `selectPoint` → `gisPanelRef.focusPoint()`；无坐标时列表正常显示，地图不强制标点。

---

## 五、验收对照

| 项 | 状态 |
|---|---|
| 首页/地图/时间轴无变化 | ✅ |
| 仅右侧区域升级 | ✅ |
| 默认「异常」筛选 | ✅ |
| 异常/全部/正常切换 | ✅ |
| 对象详情（区域内，非新页面） | ✅ |
| 趋势折线 + 统计柱状 | ✅ |
| GIS 联动预留（emit selectPoint） | ✅ |
| 无 PASS/NO_ISSUE 等码直出 | ✅（presenter 转换） |
| 大屏字号（标题24、数字36、列表18） | ✅ |

---

## 六、未完成事项

1. **「异常」Tab 数据量依赖库内超标/未闭环记录**：若 MySQL 路径仅返回 open exceed 事件，「正常」Tab 可能偏少；Demo API 含全量监测点。
2. **趋势图**：部分监测点无历史序列时显示「暂无趋势数据」。
3. **闭环管理**：整改轮次仅在详情异常块展示摘要，未单独做时间轴模块（可二期）。
4. **E02/E03/S/G**：尚未接入 Class A，仍用原 `*WorkspacePanel`。

---

## 七、后续 E02/E03/S/G 扩展方式

1. 新增 `esg-e02-presenter.ts` 等，映射各自 API 载荷 → `EsgRiskObjectCard`。
2. `ESGRiskPanel` 增加 `moduleKey` 分支或注入 `loadObjects` / `loadDetail` 函数。
3. 对应 `E02WorkspacePanel.vue` 等改为薄封装，传入 `config.theme` 与标题。
4. **禁止**复制一套新页面；复用同一母版与 GIS `overviewReady` / `selectPoint` 契约。

---

## 八、验证方式

1. 首页点击「环保风险预警」→ 右侧出现 Class A 面板（非全屏）。
2. 默认「异常」Tab；切换「全部」「正常」。
3. 点击监测点 → 详情表 + 底部趋势图；左侧地图可联动（有坐标时）。
4. `npx vue-tsc --noEmit` 通过。
