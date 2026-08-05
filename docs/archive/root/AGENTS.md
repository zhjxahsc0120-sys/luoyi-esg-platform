# ESG-project 智能代理协作规则

本文件是 Codex、TRAE 及其他编码代理在本仓库工作的统一规则。

## 项目基线

- 前端：Vue 3、Vite 5、TypeScript、Pinia、SCSS、ECharts、Cesium。
- Node.js：使用 22.x；依赖安装使用 `npm ci`。
- 默认分支：`main`。
- 禁止代理直接向 `main` 提交或推送业务修改。
- 内部资料、环境变量、用户上传文件及凭据不得提交到仓库。

## 角色分工

### Codex

- 把需求整理成 GitHub Issue，写清目标、范围、验收标准与验证命令。
- 审查 Pull Request 的正确性、安全性、回归风险和测试证据。
- 审查不通过时，在 PR 中给出可执行的修改意见。
- 不以“完成报告”代替代码、测试和差异检查。

### TRAE

- 只实现 Issue 明确列出的范围。
- 从最新 `main` 创建独立分支，完成代码、验证和 Pull Request。
- 在 PR 正文中填写完成报告，不通过聊天消息单独交付。
- 收到 Codex 审查意见后，在同一分支修复并继续推送。

## 标准工作流

1. Codex 创建 Issue，状态为待 TRAE 实现。
2. TRAE 同步主分支：
   ```bash
   git fetch origin
   git switch main
   git pull --ff-only origin main
   ```
3. TRAE 创建分支：
   ```bash
   git switch -c trae/<issue-number>-<short-name>
   ```
4. TRAE 实现 Issue，并运行规定的验证。
5. TRAE 提交并推送分支，创建以 `main` 为目标的 Pull Request。
6. PR 正文必须引用 Issue，例如 `Closes #12`，并完整填写模板。
7. CI 通过后触发 Codex Review；未开启自动评审时，在 PR 评论中使用精确指令 `@codex review`。
8. TRAE 根据审查意见修复；Codex 再次核验。
9. 只有 CI 通过且 Codex 无阻塞意见时才能合并。

## 分支和提交

- TRAE：`trae/<issue-number>-<short-name>`
- Codex：`codex/<issue-number>-<short-name>`
- 修复：`fix/<issue-number>-<short-name>`
- 每个分支只处理一个 Issue。
- 提交信息使用清晰的动词前缀，例如 `feat:`、`fix:`、`refactor:`、`test:`、`docs:`、`chore:`。
- 禁止强制推送共享分支，除非用户明确批准。

## 必须执行的验证

前端相关修改至少执行：

```bash
npm ci
npm run check
npm run build
```

后端 Python 修改至少执行：

```bash
python -m compileall -q server
```

如某项命令无法运行，PR 必须写明原因、错误信息和替代验证，不能标记为已通过。

## 审查标准

Codex Review 按以下优先级检查：

1. 数据泄露、密钥、越权、注入、文件上传与路径处理风险。
2. 功能是否满足 Issue 的验收标准。
3. 空值、异常、加载失败、网络失败和边界输入。
4. 类型错误、构建失败、破坏现有路由或大屏布局。
5. 不必要的大范围改动、重复代码和缺少验证证据。

## 安全与数据

- 不提交 `.env`、Token、API Key、密码、数据库连接串或真实用户数据。
- 不提交 `server/storage/uploads/`、缓存、构建产物或依赖目录。
- 不得为了让 CI 通过而删除测试、降低类型检查或吞掉错误。
- 数据库迁移、依赖大版本升级、权限模型变化和破坏性操作必须在 Issue 与 PR 中单独说明。
- 发现疑似凭据时立即停止，不复制其内容，并通知用户。

## 完成定义

任务只有同时满足以下条件才算完成：

- Issue 验收标准全部满足。
- PR 模板填写完整并关联 Issue。
- 必需验证通过，或明确记录经用户接受的例外。
- CI 通过。
- Codex Review 无未解决的阻塞意见。
- 工作区无意外文件，改动范围与任务一致。
