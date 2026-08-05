# 《ESG工作区迁移报告》

迁移日期：2026-08-04  
目标工作区：`C:\ESG_Project`  
基线版本：ESG Demo V0.3：首页一级指标业务事实校正版

## 一、迁移结论

迁移已完成。新工作区按迁移清单建立，没有对旧工作区做全量复制、删除或移动。

- 新工作区已创建：`C:\ESG_Project`
- 当前 V0.3 已归档：`versions/V0.3_homepage_kpi_calibration/`
- 迁移清单：`migration_manifest.md`
- SHA256 明细：`migration_manifest_sha256.csv`
- 迁移文件数：1,395
- SHA256 匹配：1,395
- SHA256 不匹配：0
- 未迁移旧目录内容未被删除，仍保留在原工作区

## 二、新工作区结构

```text
C:\ESG_Project
├── frontend
├── backend
├── database
│   ├── current
│   └── archive
├── gis
│   ├── current
│   └── archive
├── docs
│   ├── current
│   └── archive
├── demo_data
│   ├── current
│   └── archive
├── handoff
│   ├── current
│   └── archive
├── scripts
├── versions
├── README.md
├── PROJECT_RULES.md
├── .env.example
├── frontend/.env.example
├── migration_manifest.md
└── migration_manifest_sha256.csv
```

## 三、当前主链路

### 前端

- 框架：Vue 3、Vite 5、TypeScript、Pinia、SCSS、ECharts、Cesium
- 目录：`frontend/`
- 安装：`npm.cmd ci --prefix frontend`
- 启动：`powershell -ExecutionPolicy Bypass -File .\scripts\start-frontend.ps1`
- 入口：<http://localhost:5173/#/>

### 后端

- 框架：Python `http.server` / `ThreadingHTTPServer`
- 目录：`backend/`
- 入口：`backend/app.py`
- 启动：`powershell -ExecutionPolicy Bypass -File .\scripts\start-backend.ps1`
- API：`http://127.0.0.1:8765`
- 健康检查：`http://127.0.0.1:8765/health`

### 数据库

- 类型：MySQL 8.4.9
- 地址：`127.0.0.1:3307`
- 数据库：`luoyi_esg`
- 主链路：`database/current/`
- V0.3 首页 KPI 视图：`v_esg_demo_dashboard_kpis`
- 本地凭据：未迁移；使用根目录 `.env.example` 创建本地 `.env`

### GIS

- 当前有效模块：`frontend/src/modules/traffic-gis-overview/`
- GIS 归属副本：`gis/current/traffic-gis-overview/`
- 地图资源：`frontend/public/gis/` 与 `gis/current/public-gis/`
- 历史 GIS 配置和测试资料：`gis/archive/`
- 本次未替换地图、未接入新数据源、未修改 GIS 业务逻辑

## 四、当前 / 历史资料边界

- `database/current/`：V0.3 主链路所需 schema、Dashboard build、Demo 基础和 V0.3 校正。
- `database/archive/`：旧 build、历史 migration 和历史数据库资料，不作为默认执行入口。
- `docs/current/`：当前 README、API 契约、前后端基线和迁移资料。
- `docs/archive/`：历史设计说明和旧根目录文档。
- `handoff/current/`：当前有效交接资料，主要为基线、V0.3、2026-08-04 联调和 GIS 交接内容。
- `handoff/archive/`：历史交接资料，保留用于追溯，不进入当前上下文默认入口。
- `demo_data/current/`：当前 Demo 数据和 V0.3 数据脚本。
- `demo_data/archive/`：历史 seed 脚本和旧 Demo 资料。

## 五、未迁移内容

按已确认的 `migration_manifest.md` 第三节执行，以下内容未迁移：

- `node_modules/`
- 构建产物 `dist/` 和历史构建备份
- Python 缓存、日志、PID
- `_tmp*`、`_sec*` 临时文件
- `.git`、`.trae`、`.uploads` 和工具缓存目录
- 历史备份包、历史交付包和历史截图进入归档或留在旧工作区
- `.env` 及任何数据库密码、Token、连接凭据

迁移验证期间为运行 `npm ci` 和 `vite build` 产生的依赖/构建目录不属于迁移清单，也不纳入 SHA256 迁移记录。

## 六、验证结果

已通过：

```text
npm.cmd ci --prefix frontend       通过
npm.cmd run check --prefix frontend 通过
npm.cmd run build --prefix frontend 通过
python -m compileall -q backend    通过
新工作区 backend → MySQL 3307     连接成功，MySQL 8.4.9
新工作区临时 Vite 5174 首页       HTTP 200
新工作区临时 Vite 5174 KPI API    HTTP 200，响应长度 3343
迁移 SHA256                      1395/1395 匹配
```

当前旧工作区运行状态保持不变：MySQL 3307、Vite 5173、Python API 8765 继续运行。新工作区未启动 5173/8765 常驻服务，避免与旧工作区端口冲突。

## 七、AI 接入入口

Cursor/Codex 后续只打开：`C:\ESG_Project`。

首次接入必须按顺序读取：

1. `PROJECT_RULES.md`
2. `README.md`
3. `versions/V0.3_homepage_kpi_calibration/README.md`
4. `migration_manifest.md`

迁移验收前不得继续开发 S 组、G 组、E 组、GIS 或数据库，也不得自动优化首页。

## 八、剩余风险项

- 新工作区没有迁移真实 `.env`，首次启动前必须由使用者在本地配置。
- `npm ci` 验证报告 8 个依赖审计项（5 moderate、3 high）；本次未自动升级依赖，避免改变 V0.3 基线。
- `gis/current/` 与前端运行目录存在同源副本，后续修改前必须明确权威路径，避免双写漂移。
- 当前数据库历史脚本虽已归档，但正式执行顺序仍需下一阶段单独确认。
- 旧工作区仍在运行；Cursor 切换后必须关闭旧项目，避免在错误目录继续开发。
