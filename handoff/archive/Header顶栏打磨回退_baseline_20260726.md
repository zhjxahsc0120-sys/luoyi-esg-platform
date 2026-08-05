# Header 顶栏打磨回退说明（2026-07-26）

## 决定

近期「标题 / 一级三 Tab 跨路由统一」实验（单行顶栏、固定 px 字号、Workspace 套 1920 scale 壳等）**效果不可接受**，已全部回退。

**在未获新的设计批准前，不要再改 HeaderNav / 顶栏壳统一方案。**

## 回退方式

从 git tag `baseline/l1-l2-gis-20260726` 检出下列文件到工作区（与该基线一致；相对当前 HEAD 无额外 diff，因实验均为未提交改动）：

- `src/components/layout/HeaderNav.vue`
- `src/components/workspace/WorkspaceNav.vue`
- `src/views/WorkspacePage.vue`
- `src/views/AssistantPage.vue`
- `src/styles/tokens.scss`
- `src/styles/layout.scss`

## 未回退

GIS / L1 / L2 正文相关文件**未**从基线覆盖；仅恢复顶栏/壳层相关文件。

## 验证

- `npm run check`：通过（回退后）
