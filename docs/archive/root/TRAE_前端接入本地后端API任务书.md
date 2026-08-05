# TRAE 前端接入本地后端 API 任务书

## 一、任务目标

当前数据库和后端联调服务由 Codex 维护，Trae 只负责前端接入。

本轮目标不是重构页面，也不是重新设计 UI，而是将当前前端 mock 数据逐步切换为本地 API 数据，同时保留 mock fallback，确保后端未启动时页面仍能正常展示。

后端服务地址：

```text
http://127.0.0.1:8765
```

接口契约文件：

```text
server/API_CONTRACT.md
```

## 二、禁止事项

1. 不要修改数据库脚本；
2. 不要修改 `server/` 目录；
3. 不要重构领导首页布局；
4. 不要重构数据上传工作台布局；
5. 不要删除现有 mock 文件；
6. 不要因为 API 接口未启动导致页面空白；
7. 不要改动 S01 弹窗视觉结构，只允许替换数据来源。

## 三、建议实现方式

新增 API 客户端：

```text
src/services/api.ts
```

建议结构：

```ts
const API_BASE = import.meta.env.VITE_API_BASE || 'http://127.0.0.1:8765'

export async function apiGet<T>(path: string): Promise<T | null> {
  try {
    const res = await fetch(`${API_BASE}${path}`)
    if (!res.ok) return null
    return await res.json() as T
  } catch {
    return null
  }
}
```

后续所有页面调用 API 时必须允许返回 `null`，并回退到现有 mock 数据。

## 四、环境变量

新增或支持：

```text
VITE_API_BASE=http://127.0.0.1:8765
```

如果不新增 `.env`，也可以在 `api.ts` 中写默认值。

## 五、第一批接入范围

### 5.1 领导首页 KPI 卡片

接口：

```text
GET /api/dashboard/kpis
```

前端目标：

- 替换 `src/data/dashboard.mock.ts` 中 `kpiGroups` 的运行时数据来源；
- 仍保留 `dashboard.mock.ts` 作为 fallback；
- 页面显示应保持：
  - E01=2
  - E02=5
  - E03=7
  - E04=12856 tCO₂e
  - S01=368
  - S02=6
  - S03=4
  - S04=3
  - G01=5
  - G02=5
  - G03=6
  - G04=4

建议改动位置：

```text
src/stores/dashboard.store.ts
```

不要改 `KpiCard.vue` 和首页布局。

### 5.2 S01 弹窗数据

接口：

```text
GET /api/dashboard/kpi/S01
```

前端目标：

- S01 弹窗从 API 获取：
  - `projectStartDate`
  - `currentDate`
  - `continuousDays`
  - `currentStage`
  - `currentStageDetail`
  - `countingStatus`
  - `updateTime`
  - `timeline`
  - `constructionStages`
  - `conclusion`
- API 失败时使用当前组件内已有示例数据；
- 不改变 S01 弹窗结构、尺寸和样式。

建议改动位置：

```text
src/components/modal/S01SafetyProductionModal.vue
```

### 5.3 数据上传工作台状态卡

接口：

```text
GET /api/workspace/summary
```

前端目标：

- P01/P02 状态卡从 API 获取；
- 当前前端 P02 有“当前待办 / 待上传 / 待补正 / 待提交 / 审核中 / 已完成”；
- API 字段映射：

| API 字段 | 页面字段 |
|---|---|
| `currentTodo` | 当前待办 |
| `pendingUpload` | 待上传 |
| `pendingCorrection` | 待补正 |
| `pendingSubmit` | 待提交 |
| `underReview` | 审核中 |
| `dueSoon` | 即将到期 |
| `completed` | 已完成 |

建议改动位置：

```text
src/data/workspace.mock.ts
src/components/workspace/WorkspaceHome.vue
src/components/workspace/WorkspaceTasks.vue
```

优先在页面组件层加载 API 数据，不要大规模改 mock 类型。

### 5.4 上传任务列表

接口：

```text
GET /api/workspace/tasks
```

支持参数：

```text
module=E/S/G
status=待上传/待补正/待提交/审核中/已完成
keyword=水保
```

前端目标：

- 替换 P01 简化任务列表；
- 替换 P02 我的上传任务列表；
- 保留前端现有筛选逻辑，如果接口暂未覆盖全部筛选，可以先 API 获取全量后在前端筛选。

### 5.5 资料中心

接口：

```text
GET /api/workspace/documents/summary
GET /api/workspace/documents
```

前端目标：

- P05 顶部卡片接入 summary；
- 资料列表接入 documents；
- 右侧详情面板可继续使用当前 mock 逻辑，后续再接详情接口。

### 5.6 审核结果

接口：

```text
GET /api/workspace/reviews
```

前端目标：

- P04 状态卡和审核记录列表接入 API；
- 右侧审核轨迹如接口暂未提供，可继续使用前端现有按记录 ID 映射的 mock。

### 5.7 ESG 智能入库解析队列

接口：

```text
GET /api/workspace/ai/parse-queue
```

前端目标：

- P03 解析队列接入 API；
- AI摘要、建议关联任务暂可继续使用当前 mock，后续由 Codex 补接口。

## 六、建议接入顺序

1. 新增 `src/services/api.ts`；
2. 接入 `/api/dashboard/kpis`；
3. 接入 `/api/dashboard/kpi/S01`；
4. 接入 `/api/workspace/summary`；
5. 接入 `/api/workspace/tasks`；
6. 接入资料中心、审核结果、AI解析队列。

每完成一步都需要确认：

- API 开启时显示 API 数据；
- API 关闭时回退 mock；
- 页面不空白；
- 控制台没有未捕获异常。

## 七、验收标准

后端启动：

```powershell
.\server\start_backend.ps1
```

前端启动：

```powershell
npm run dev
```

验收：

1. 访问 `http://localhost:5174/#/`；
2. 首页 12 项 KPI 与 API 口径一致；
3. 点击 S01，弹窗显示：
   - 368天；
   - 2025-07-10；
   - 2026-07-13；
   - 主体工程施工；
   - 路基｜桥梁｜隧道并行施工；
4. 访问 `http://localhost:5174/#/workspace`；
5. 工作台状态卡显示：
   - 当前待办 27；
   - 待上传 12；
   - 待补正 3；
   - 待提交 5；
   - 审核中 3；
   - 已完成 36；
6. 资料中心显示：
   - 资料总数 368；
   - 本月新增 24；
   - 待归档 6；
   - 即将失效 4；
7. 停止后端后刷新页面，仍回退显示 mock 数据。

停止后端：

```powershell
.\server\stop_backend.ps1
```

## 八、完成后回报

Trae 完成后请回报：

1. 修改文件清单；
2. 每个接口的接入位置；
3. API 开启/关闭两种状态的验证结果；
4. `npm run check` 结果；
5. `npm run build` 结果；
6. 是否存在仍使用 mock 的页面区域。
