# 可发给前端样式同事的任务说明

请基于当前项目，仅做数据填报与上传工作台的样式优化，不改业务逻辑和接口。

## 一、访问地址

```text
数据填报与上传工作台：
http://localhost:5174/#/workspace

领导层 ESG 看板：
http://localhost:5174/#/
```

## 二、本轮目标

优化工作台 P01-P05 和 S01 弹窗的字体、格式、间距、表格密度、按钮样式、状态标签一致性。

重点页面：

- P01 工作台首页；
- P02 我的上传任务；
- P03 ESG 智能入库；
- P04 审核结果；
- P05 资料中心与档案；
- S01 任务办理中央弹窗。

## 三、优先修改文件

```text
src/components/workspace/WorkspaceHome.vue
src/components/workspace/WorkspaceTasks.vue
src/components/workspace/WorkspaceSmartUpload.vue
src/components/workspace/WorkspaceReview.vue
src/components/workspace/WorkspaceDocuments.vue
src/components/workspace/TaskModal.vue
src/components/workspace/WorkspaceNav.vue
src/views/WorkspacePage.vue
```

建议优先改各文件底部 `<style scoped>`，不要大范围改 script。

## 四、不要修改

不要修改以下文件或逻辑：

```text
src/services/api.ts
src/utils/workspaceRefresh.ts
server/
```

不要改这些事件和函数名：

```text
loadData
reloadAll
handleSubmit
handleApprove
handleReturn
handleConfirmAndLink
emitWorkspaceRefresh
onWorkspaceRefresh
```

不要改这些状态文案：

```text
待上传
待补正
待提交
审核中
已完成
待审核
已通过
已退回
已补正
```

这些字段参与筛选、接口映射和跨页面刷新。

## 五、样式优化建议

1. 统一字体层级：
   - 页面标题 24–28px；
   - 模块标题 18–22px；
   - 表格正文 13–15px；
   - 状态标签 11–13px；
   - 按钮文字 14–16px。

2. 统一表格密度：
   - P02/P04/P05 表格行高建议 48–58px；
   - 表头和正文 padding 保持一致；
   - 操作按钮间距保持 8–12px。

3. 优化 S01 弹窗：
   - 避免底部按钮遮挡内容；
   - 页签、表格、右侧校验卡保持清晰；
   - 弹窗内部不要出现不必要的横向滚动。

4. 统一状态标签：
   - 待上传 / 待审核：蓝色；
   - 待补正 / 即将到期：橙色；
   - 已完成 / 已通过 / 已补正：绿色；
   - 已退回 / 异常：红色；
   - 普通弱信息：灰蓝色。

## 六、验收要求

完成后执行：

```powershell
npm run check
npm run build
```

人工点测：

1. P01 首页状态卡和任务列表无错位；
2. P02 筛选区、表格、分页无裁切；
3. P03 上传区、解析队列、右侧 AI 摘要不溢出；
4. P04 审核轨迹、补正要求标签清晰；
5. P05 左侧分类、中间列表、右侧详情三栏稳定；
6. S01 弹窗打开、切换页签、关闭均正常；
7. 审核通过/退回按钮仍可点击；
8. 待补正任务按钮仍显示“重新提交审核”。

回报时请提供：

- 修改文件清单；
- 主要样式调整说明；
- `npm run check` 结果；
- `npm run build` 结果；
- 关键页面截图。

