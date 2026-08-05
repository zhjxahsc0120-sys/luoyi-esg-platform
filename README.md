# 罗宜高速 ESG 数字化管理平台

唯一开发工作区：`C:\ESG_Project`

当前开发基线：ESG Demo V0.3：首页一级指标业务事实校正版。

## 当前状态

- 首页 12 项 E/S/G 一级 KPI 已冻结。
- E04 无文物对象时显示 0 处。
- S01 按 2026-05-08 起算日期计算。
- S03 工资支付达标率显示百分比。
- G 组首页使用合规率、完成率、受控率和合规状态表达。
- 当前调用链：Vite 5173 → Python API 8765 → MySQL 3307 `luoyi_esg`。
- 旧工作区未删除，仅作为历史来源和追溯材料保留。

## 目录

```text
C:\ESG_Project
├── frontend       当前 Vue/Vite 前端
├── backend        当前 Python API 与运行模块
├── database       当前数据库主链路与历史资料归档
├── gis            当前有效 GIS 模块与历史 GIS 资料归档
├── docs           当前文档与历史设计资料归档
├── demo_data      当前 Demo 数据与历史种子资料归档
├── handoff        当前交接资料与历史交接资料归档
├── scripts        新工作区启动/停止脚本
├── versions       V0.3 基线归档
├── migration_manifest.md
└── migration_manifest_sha256.csv
```

## 启动

首次使用前，在根目录创建本地 `.env`，内容参考 `.env.example`。`.env` 不纳入版本库和迁移清单。

```powershell
cd C:\ESG_Project
npm.cmd ci --prefix frontend
powershell -ExecutionPolicy Bypass -File .\scripts\start-backend.ps1
powershell -ExecutionPolicy Bypass -File .\scripts\start-frontend.ps1
```

入口：<http://localhost:5173/#/>

后端健康检查：<http://127.0.0.1:8765/health>

## 迁移说明

- 主工作区只包含当前有效内容。
- 历史设计、旧 build/migration、旧交接资料和历史 GIS 配置进入对应 `archive/`。
- `node_modules`、构建产物、缓存、日志、PID、临时文件、工具目录和 `.env` 未迁移。
- 迁移文件的源/目标 SHA256 见 `migration_manifest_sha256.csv`。
- V0.3 冻结归档见 `versions/V0.3_homepage_kpi_calibration/`。

开始任何开发前，必须先读取 `PROJECT_RULES.md`。
