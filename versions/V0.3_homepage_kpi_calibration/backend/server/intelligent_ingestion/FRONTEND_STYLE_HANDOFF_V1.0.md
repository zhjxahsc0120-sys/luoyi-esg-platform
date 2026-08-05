# 前端样式同事对接说明 V1.0

## 1. 对接目标

当前数据填报与上传工作台已经完成主要业务闭环：

- P01 工作台首页；
- P02 我的上传任务；
- P03 ESG 智能入库；
- P04 审核结果；
- P05 资料中心与档案；
- S01 任务办理中央弹窗；
- 跨页面状态刷新；
- 后端 API 联调与 mock fallback。

下一位同事主要负责字体、间距、格式、视觉一致性优化时，请尽量只改样式层，不改接口、事件、状态和业务逻辑。

## 2. 页面访问地址

| 页面 | 地址 |
| --- | --- |
| 领导层 ESG 看板 | `http://localhost:5174/#/` |
| 数据填报与上传工作台 | `http://localhost:5174/#/workspace` |

## 3. 工作台组件地图

| 页面 / 模块 | 文件 | 可改内容 | 谨慎修改 |
| --- | --- | --- | --- |
| 工作台外壳 | `src/views/WorkspacePage.vue` | 页面背景、主区域尺寸、弹窗挂载层级样式 | `activeNav`、`selectedTaskId`、`currentTask` |
| 顶部导航 | `src/components/workspace/WorkspaceNav.vue` | 导航字体、图标间距、选中态、hover | 导航 key、`@navigate` 事件 |
| P01 工作台首页 | `src/components/workspace/WorkspaceHome.vue` | 状态卡、任务表、智能助手、重点关注区样式 | `loadData()`、`onWorkspaceRefresh()`、`emit('openTask')` |
| P02 我的上传任务 | `src/components/workspace/WorkspaceTasks.vue` | 筛选区、表格、分页、批量按钮样式 | 筛选参数、`loadDataWithParams()`、任务状态判断 |
| P03 ESG 智能入库 | `src/components/workspace/WorkspaceSmartUpload.vue` | 上传区、解析队列、AI 摘要、候选任务样式 | 上传/解析/确认入库 API、`emitWorkspaceRefresh()` |
| P04 审核结果 | `src/components/workspace/WorkspaceReview.vue` | 状态卡、审核列表、右侧轨迹、补正标签、按钮样式 | 审核通过/退回逻辑、`taskId`、`reloadAll()` |
| P05 资料中心 | `src/components/workspace/WorkspaceDocuments.vue` | 分类树、资料列表、右侧详情、标签样式 | 筛选逻辑、详情/版本/关联接口 |
| S01 任务办理弹窗 | `src/components/workspace/TaskModal.vue` | 弹窗宽度、高度、页签、表格、底部按钮样式 | 资料关联、提交审核、重新提交审核、API 优先任务详情 |

## 4. 样式文件现状

### 4.1 公共样式

当前公共样式主要在：

```text
src/styles/tokens.scss
src/styles/layout.scss
src/styles/dashboard.scss
```

其中：

- `tokens.scss`：颜色、字体、字号、面板 mixin；
- `layout.scss`：领导看板主布局；
- `dashboard.scss`：领导看板相关样式。

注意：这些文件目前更偏领导层首页，不建议直接大范围改动以影响工作台。

### 4.2 工作台样式

工作台样式主要写在各 Vue 文件的 `<style scoped>` 中。

建议样式同事优先在对应组件内调整：

- 字号；
- 行高；
- 间距；
- 表格高度；
- 卡片圆角；
- 按钮尺寸；
- 状态标签颜色；
- hover / active 态。

不建议第一轮就抽全局 CSS，因为目前工作台仍处在原型联调阶段，局部 scoped style 更安全。

## 5. 推荐统一视觉口径

### 5.1 字体

建议沿用：

```css
font-family: 'PingFang SC', 'Microsoft YaHei', 'Helvetica Neue', Arial, sans-serif;
```

数字类可以使用：

```css
font-family: 'DIN Alternate', 'Bahnschrift', 'Roboto Mono', 'Consolas', monospace;
```

### 5.2 字号建议

| 场景 | 建议字号 |
| --- | --- |
| 页面标题 | 24–28px |
| 模块标题 | 18–22px |
| 卡片主数字 | 28–36px |
| 表头 | 13–14px |
| 表格正文 | 13–15px |
| 弱说明文字 | 12–13px |
| 状态标签 | 11–13px |
| 按钮文字 | 14–16px |

### 5.3 间距建议

| 场景 | 建议 |
| --- | --- |
| 页面主区边距 | 14–20px |
| 卡片间距 | 12–16px |
| 表格行高 | 48–58px |
| 筛选项间距 | 10–14px |
| 弹窗内部模块间距 | 12–18px |
| 按钮高度 | 36–44px |

### 5.4 状态颜色建议

| 状态 | 颜色建议 |
| --- | --- |
| 待上传 / 待审核 | 蓝色 |
| 待补正 / 即将到期 | 橙色 |
| 待提交 / 治理合规强调 | 紫色 |
| 已完成 / 已通过 / 已补正 | 绿色 |
| 已退回 / 已逾期 / 异常 | 红色 |
| 普通弱信息 | 灰蓝色 |

## 6. 绝对不要改的逻辑点

以下内容请不要在样式优化中改动：

### 6.1 API 调用

```text
src/services/api.ts
```

除非明确接到接口变更任务，否则不要修改：

- API 路径；
- 请求参数；
- 返回类型；
- fallback 逻辑。

### 6.2 跨页面刷新事件

```text
src/utils/workspaceRefresh.ts
```

不要删除：

- `emitWorkspaceRefresh`
- `onWorkspaceRefresh`

这些用于 P01/P02/P03/P04/P05/S01 状态联动。

### 6.3 关键事件绑定

不要删除或改名：

- `@open-task`
- `@navigate`
- `handleSubmit`
- `handleApprove`
- `handleReturn`
- `handleConfirmAndLink`
- `loadData`
- `reloadAll`

### 6.4 关键状态字段

不要改这些业务状态文案：

- 待上传；
- 待补正；
- 待提交；
- 审核中；
- 已完成；
- 待审核；
- 已通过；
- 已退回；
- 待补正 / 已补正标签。

这些文案直接参与筛选、状态卡、接口映射。

## 7. 适合样式同事优先优化的问题

### 7.1 字体层级

当前不同页面的字号略有差异，建议优先统一：

- 页面标题；
- 卡片标题；
- 表头；
- 表格正文；
- 弱说明；
- 按钮文字。

### 7.2 表格密度

P02、P04、P05 表格较多，建议统一：

- 表格行高；
- 表头高度；
- 单元格左右 padding；
- 状态标签宽度；
- 操作按钮间距。

### 7.3 弹窗可读性

S01 任务办理弹窗内容较多，建议重点关注：

- 弹窗宽度和最大高度；
- 页签区高度；
- 表格区域高度；
- 底部操作栏是否遮挡内容；
- 资料要求表格中按钮是否拥挤。

### 7.4 状态标签一致性

建议统一以下标签样式：

- ESG 模块标签 E/S/G；
- 任务状态标签；
- 审核状态标签；
- 补正要求状态标签；
- 资料有效状态标签。

## 8. 每次样式修改后的最低验证

样式同事每次提交前至少执行：

```powershell
npm run check
npm run build
```

并人工打开：

```text
http://localhost:5174/#/workspace
```

至少点测：

1. P01 首页无错位；
2. P02 表格和筛选区无裁切；
3. P03 上传区和右侧 AI 摘要不溢出；
4. P04 右侧审核轨迹和补正要求标签可读；
5. P05 左中右三栏不挤压；
6. S01 弹窗无内部内容遮挡；
7. 弹窗关闭后页面正常。

## 9. 如果样式改动后出现问题，优先排查

| 现象 | 优先排查 |
| --- | --- |
| 任务弹窗打不开 | `WorkspacePage.vue` 的 `currentTask` / `selectedTaskId` 是否被误改 |
| P04 进入补正打不开任务 | `reviewRecord.taskId` 是否仍保留 |
| 状态卡不刷新 | `workspaceRefresh.ts` 事件监听是否被删 |
| 审核按钮消失 | `selectedRecord?.status === '待审核'` 判断是否被改 |
| 补正标签不显示 | `requirement.status` 是否仍保留 |
| P02 筛选失效 | `selectedStatus`、`hasSearch`、`handleAiSearch` 是否被改 |
| API 数据不显示 | `loadData()` 是否被误删或改为只读 mock |

## 10. 建议协作方式

为了避免冲突，建议：

1. 样式同事只改 `template` 的 class 结构和 `<style scoped>`；
2. 如果必须改 script，先说明原因；
3. 不要改 API 文件和后端文件；
4. 每次改完发：
   - 修改文件清单；
   - 样式影响范围；
   - `npm run check` 结果；
   - `npm run build` 结果；
   - 2–3 张关键截图。

