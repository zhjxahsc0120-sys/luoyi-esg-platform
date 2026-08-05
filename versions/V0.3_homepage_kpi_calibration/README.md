# ESG Demo V0.3 首页一级指标业务事实校正版

冻结时间：2026-08-04  
冻结来源：当前唯一运行项目工作树  
来源路径：`C:\Users\TB\AppData\Roaming\TRAE SOLO CN\ModularData\ai-agent\work-mode-projects\6a53a1b3d0f497e311ecc95f`

## 版本定位

本目录是 ESG Demo V0.3 的当前工作树归档快照，作为后续开发基线。归档动作只做复制、整理和记录，没有回退、清理或改写业务代码、API、数据库结构和 Demo 数据。

当前 Git HEAD：见 `docs/freeze_git_head.txt`。  
冻结时工作树状态：见 `docs/freeze_git_status.txt`。  
冻结时间记录：见 `docs/freeze_created_at.txt`。

## 已完成范围

- 首页驾驶舱可运行。
- 首页 12 项 E/S/G 一级 KPI 的业务展示方向已确认。
- E04 文物保护对象：无对象时显示 0 处。
- S01 连续安全生产：从 2026-05-08 起按统计截止日计算。
- S03 工资支付达标率：显示百分比。
- G 组首页使用合规率、完成率、受控率和合规状态表达。
- MySQL Demo 数据源、`v_esg_demo_dashboard_kpis`、Python API 和前端首页链路已验证。
- 当前 S03 首页单位修正为 `%`，浏览器验收显示 `100 %`。

## 运行链路

```text
浏览器 http://localhost:5173/#/
  → Vite /api 代理或 VITE_API_BASE
  → Python API 127.0.0.1:8765
  → server/app.py / server/mysql_api.py / server/esg_demo_api.py
  → MySQL 127.0.0.1:3307 / luoyi_esg
  → v_esg_demo_dashboard_kpis
```

## 归档目录

| 目录 | 内容 |
|---|---|
| `frontend/` | Vue/Vite/TypeScript 前端源码、静态资源和构建配置 |
| `backend/` | Python API、服务、测试和后端配置 |
| `database/` | Schema、迁移脚本、MySQL 构建脚本和数据库初始化脚本 |
| `demo_data/` | ESG Demo V0.1/V0.3 数据脚本、Dashboard Demo 数据和前端测试数据 |
| `docs/` | 项目文档、交接资料、部署脚本及冻结状态记录 |

## 当前未完成

- S 组详细页面与二级下钻逻辑的业务事实审计。
- G 组深化页面与二级下钻逻辑的业务事实审计。
- GIS 模块向统一工作区迁移和独立验收。
- 正式数据库及正式业务数据迁移。
- 新工作区 `C:\ESG_Project` 的建立与环境复核。
- `PROJECT_RULES.md` 和统一 AI 上下文接入。

## 归档边界

为避免把凭据、缓存和生成物带入版本基线，归档未复制：`.env`、数据库密码、`node_modules/`、构建产物、Python 缓存、运行日志、PID 文件和临时 `_tmp*` 文件。原工作树中的这些文件没有被删除或修改。

后续 Cursor/Codex 接入统一工作区后，必须先读取新工作区的 `PROJECT_RULES.md`、根目录 `README.md` 和本文件，再开始下一阶段任务。
