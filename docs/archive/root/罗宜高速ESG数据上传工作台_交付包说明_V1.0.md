# 罗宜高速 ESG 数据上传工作台交付包说明 V1.0

## 1. 交付包定位

本交付包用于支撑当前“罗宜高速 ESG 数字化管理平台”的本地演示、前后端联调和阶段验收。

当前交付范围包括：

- 领导层 ESG 看板首页基础 API；
- 数据填报与上传工作台 P01-P05；
- S01 任务办理中央弹窗；
- 智能入库上传、解析、入库、关联任务闭环；
- 审核通过、审核退回、补正再提交闭环；
- 资料中心列表、详情、版本、关联任务接口；
- MySQL-first 后端服务；
- SQLite fallback 本地镜像库；
- 自动化联调与验收脚本；
- 前端样式同事对接说明。

本交付包适合：

- 阶段成果演示；
- 前端样式优化；
- 后端接口联调；
- 数据库设计验证；
- 业务闭环验收。

暂不等同于生产上线版本。

---

## 2. 项目目录说明

项目根目录：

```text
C:\Users\TB\AppData\Roaming\TRAE SOLO CN\ModularData\ai-agent\work-mode-projects\6a53a1b3d0f497e311ecc95f
```

核心目录：

| 路径 | 说明 |
| --- | --- |
| `src/` | Vue 前端源码 |
| `src/components/workspace/` | 数据上传工作台 P01-P05、S01 弹窗组件 |
| `src/services/api.ts` | 前端 API 封装 |
| `src/utils/workspaceRefresh.ts` | 工作台跨页面刷新事件 |
| `src/data/workspace.mock.ts` | 前端 mock fallback 数据 |
| `server/` | 本地后端、数据库脚本、测试脚本 |
| `server/mysql_api.py` | MySQL 业务接口实现 |
| `server/app.py` | Python 本地 HTTP API 服务 |
| `server/intelligent_ingestion/` | 智能入库、审核闭环、验收说明文档 |
| `dist/` | 前端构建产物 |
| `release-pack/` | 阶段打包目录，如有需要可继续用于输出交付包 |

---

## 3. 数据库说明

### 3.1 当前数据库模式

后端当前采用：

```text
MySQL-first + SQLite fallback
```

含义：

- MySQL 可用时，接口优先读取和写入 MySQL；
- MySQL 不可用时，部分接口可回退到 SQLite/mock，用于前端原型兜底；
- 当前业务闭环测试以 MySQL 为主。

### 3.2 MySQL 开发实例

当前本地 MySQL 信息：

| 项目 | 值 |
| --- | --- |
| MySQL 安装目录 | `E:\mysql\mysql-8.4.9-winx64` |
| MySQL 数据目录 | `E:\mysql\data-8.4-luoyi` |
| 配置文件 | `E:\mysql\my-luoyi.cnf` |
| 端口 | `3307` |
| 数据库 | `luoyi_esg` |
| 应用用户 | `luoyi_app` |

> 说明：数据库账号密码属于本地联调配置，对外正式交付时建议单独通过安全渠道提供，不建议写入公开文档或代码仓库。

### 3.3 SQLite fallback

SQLite 本地镜像库：

```text
server/data/luoyi_esg_dev.db
```

初始化命令：

```powershell
python server/init_db.py
```

---

## 4. 后端启动说明

### 4.1 推荐启动方式

在项目根目录执行：

```powershell
powershell -ExecutionPolicy Bypass -File server/start_backend.ps1
```

启动后访问健康检查：

```text
http://127.0.0.1:8765/health
```

预期返回：

```json
{
  "ok": true,
  "service": "luoyi-esg-local-api"
}
```

### 4.2 手动启动方式

如果不使用启动脚本，可执行：

```powershell
python server/init_db.py
python server/app.py
```

如果系统 Python 环境不可用，可使用 Codex bundled Python：

```powershell
C:\Users\TB\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe server/init_db.py
C:\Users\TB\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe server/app.py
```

### 4.3 后端停止

```powershell
powershell -ExecutionPolicy Bypass -File server/stop_backend.ps1
```

### 4.4 后端日志

| 文件 | 说明 |
| --- | --- |
| `server/server.log` | 后端标准输出日志 |
| `server/server.err.log` | 后端错误日志 |
| `server/server.pid` | 后端进程 ID |
| `api-start.log` | Codex 启动后端时的输出日志 |
| `api-start.err.log` | Codex 启动后端时的错误日志 |

---

## 5. 前端启动与访问

### 5.1 安装依赖

如已存在 `node_modules` 可跳过。

```powershell
npm install
```

### 5.2 启动前端开发服务

```powershell
npm run dev -- --host 127.0.0.1 --port 5174
```

如使用已有启动脚本或 Trae 启动的实例，保持当前 `5174` 端口即可。

### 5.3 页面访问地址

| 页面 | 地址 | 说明 |
| --- | --- | --- |
| 领导层 ESG 看板首页 | `http://localhost:5174/#/` | 领导驾驶舱，12 项 KPI、GIS、专题模块 |
| 数据填报与上传工作台 | `http://localhost:5174/#/workspace` | 上传用户工作台首页 |

### 5.4 前端 API 地址

默认 API 地址：

```text
http://127.0.0.1:8765
```

配置位置：

```text
src/services/api.ts
```

默认逻辑：

```ts
const API_BASE = import.meta.env.VITE_API_BASE || 'http://127.0.0.1:8765'
```

如需切换后端地址，可通过环境变量 `VITE_API_BASE` 配置。

---

## 6. 自动化测试命令

### 6.1 最小只读验收

用于快速确认当前接口能支撑前端页面：

```powershell
$env:PYTHONIOENCODING='utf-8'
python server/workspace_acceptance_test.py
```

预期输出：

```text
✅ 工作台最终验收只读校核通过：P01-P05、S01、领导 S01、资料中心、审核结果与解析队列接口均可支撑当前前端。
```

### 6.2 后端 API 冒烟测试

```powershell
$env:PYTHONIOENCODING='utf-8'
python server/smoke_test.py
```

### 6.3 MySQL 数据库冒烟测试

```powershell
$env:PYTHONIOENCODING='utf-8'
python server/mysql_smoke_test.py
```

### 6.4 业务闭环测试

```powershell
$env:PYTHONIOENCODING='utf-8'
python server/submit_review_flow_test.py
python server/review_action_flow_test.py
python server/confirm_updates_task_test.py
python server/parse_rule_dedup_test.py
python server/multipart_upload_test.py
python server/ingestion_api_test.py
```

### 6.5 前端检查与构建

```powershell
npm run check
npm run build
```

### 6.6 完整回归建议顺序

```powershell
$env:PYTHONIOENCODING='utf-8'
python server/workspace_acceptance_test.py
python server/smoke_test.py
python server/mysql_smoke_test.py
python server/submit_review_flow_test.py
python server/review_action_flow_test.py
python server/confirm_updates_task_test.py
python server/parse_rule_dedup_test.py
python server/multipart_upload_test.py
python server/ingestion_api_test.py
npm run check
npm run build
```

---

## 7. 已完成能力边界

### 7.1 领导层 ESG 看板

已完成：

- 首页 12 项 KPI API；
- S01 连续安全生产天数弹窗 API；
- 当前领导首页可访问；
- S01 弹窗按最新设计展示。

仍为原型/mock：

- 除 S01 外的部分 KPI 详情弹窗仍以 mock 数据为主；
- GIS 地图、专题模块仍偏原型展示。

### 7.2 P01 工作台首页

已完成：

- 状态卡 API；
- 任务列表 API；
- 快捷入口；
- 今日重点关注；
- 跨页面刷新。

仍为原型/mock：

- ESG 智能助手真实问答能力未接入。

### 7.3 P02 我的上传任务

已完成：

- 状态卡；
- 任务列表；
- E/S/G、状态、周期、截止时间、责任人筛选；
- 打开 S01 任务弹窗；
- 操作后刷新。

仍为原型/mock：

- 批量提交、批量关联资料仍为预留交互。

### 7.4 P03 ESG 智能入库

已完成：

- 真实文件上传；
- 文件落盘；
- SHA256 哈希；
- 重复检测；
- 创建解析任务；
- 规则字段抽取；
- 候选任务匹配；
- 确认入库；
- 回写资料中心；
- 回写任务资料要求和任务进度。

仍需后续建设：

- 真实 OCR；
- 大模型语义解析；
- 字段在线编辑确认器；
- 文件预览。

### 7.5 P04 审核结果

已完成：

- 审核列表；
- 审核详情；
- 审核轨迹；
- 补正要求；
- 审核通过；
- 审核退回；
- 补正再提交；
- 补正要求状态：待补正 / 已补正；
- 操作后跨页面刷新。

仍可优化：

- 审核意见输入框；
- 审核人选择；
- 补正截止时间编辑；
- 更细的审核权限控制。

### 7.6 P05 资料中心与档案

已完成：

- 状态卡；
- 资料列表；
- 分类筛选；
- 资料详情；
- 版本记录；
- 关联任务；
- 智能入库后刷新。

仍需后续建设：

- 文件下载；
- 文件在线预览；
- 版本回滚；
- 版本对比；
- 文件权限。

### 7.7 S01 任务办理中央弹窗

已完成：

- 资料要求；
- 已关联资料；
- 校验问题；
- 审核记录；
- 从资料中心关联资料；
- 暂存；
- 提交审核；
- 待补正任务重新提交审核；
- API 优先加载真实任务详情；
- 操作后跨页面刷新。

仍需后续建设：

- 真实上传新资料；
- 更完整的资料选择器；
- 附件预览；
- 操作审计。

---

## 8. 关键文档索引

| 文档 | 说明 |
| --- | --- |
| `server/intelligent_ingestion/WORKSPACE_FINAL_ACCEPTANCE_V1.0.md` | 最终联调验收清单 |
| `server/intelligent_ingestion/FRONTEND_STYLE_HANDOFF_V1.0.md` | 前端样式同事对接说明 |
| `server/intelligent_ingestion/TRAE_STYLE_TASK_BRIEF.md` | 可直接发给样式同事的简版任务 |
| `server/intelligent_ingestion/WORKSPACE_REFRESH_FLOW_V0.9.md` | 跨页面刷新机制说明 |
| `server/intelligent_ingestion/CORRECTION_RESUBMIT_FLOW_V0.8.md` | 审核退回补正再提交说明 |
| `server/intelligent_ingestion/REVIEW_ACTION_FLOW_V0.7.md` | 审核通过/退回闭环说明 |
| `server/intelligent_ingestion/SUBMIT_REVIEW_FLOW_V0.6.md` | 提交审核闭环说明 |
| `server/intelligent_ingestion/PARSE_RULE_AND_DEDUP_V0.3.md` | 解析规则和去重说明 |
| `server/intelligent_ingestion/REAL_FILE_UPLOAD_V0.2.md` | 真实文件上传说明 |

---

## 9. 样式同事协作注意事项

前端样式同事可优先修改：

```text
src/components/workspace/*.vue
src/views/WorkspacePage.vue
```

建议主要修改：

- `<template>` 中的 class 结构；
- `<style scoped>` 中的字体、间距、颜色、布局；
- 状态标签样式；
- 表格密度；
- 弹窗尺寸。

不建议修改：

```text
src/services/api.ts
src/utils/workspaceRefresh.ts
server/
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

这些文案参与筛选、接口映射和业务状态判断。

---

## 10. 当前交付状态判断

当前状态：

```text
可演示：是
可联调：是
可阶段验收：是
可直接生产上线：否
```

原因：

- 核心业务闭环已经打通；
- 数据库和接口能支撑当前前端；
- 测试脚本已覆盖主要链路；
- 但真实 OCR/AI、鉴权、文件预览下载、生产部署、安全审计仍需后续建设。

---

## 11. 建议下一阶段工作

按优先级建议：

1. 前端样式统一与截图级验收；
2. 文件预览 / 下载 / 上传新资料能力；
3. 真实 OCR 或大模型解析服务接入；
4. 登录、角色、权限；
5. 生产化后端框架与部署；
6. Playwright 浏览器端到端测试；
7. 正式环境数据库迁移脚本与备份策略。

