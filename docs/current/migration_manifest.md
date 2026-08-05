# ESG 工作区迁移清单 V1.1

生成日期：2026-08-04  
当前基线：ESG Demo V0.3：首页一级指标业务事实校正版  
当前源工作区：`C:\Users\TB\AppData\Roaming\TRAE SOLO CN\ModularData\ai-agent\work-mode-projects\6a53a1b3d0f497e311ecc95f`  
目标工作区：`C:\ESG_Project`（本清单确认前不创建、不写入）

## 一、执行状态

- [x] 完成旧工作区扫描
- [x] 冻结 `versions/V0.3_homepage_kpi_calibration/`
- [ ] 用户确认本清单中的建议不迁移项
- [ ] 创建 `C:\ESG_Project`
- [ ] 迁移有效内容
- [ ] SHA256 完整性检查
- [ ] 新工作区前后端运行验证
- [ ] 输出最终《ESG工作区迁移报告》

## 二、必须迁移内容

以下内容属于当前运行链路或 V0.3 基线，建议迁移到新工作区：

### frontend

- `index.html`
- `package.json`
- `package-lock.json`
- `vite.config.ts`
- `tsconfig.json`
- `src/`
- `public/`

其中当前有效 GIS 前端入口包括：

- `src/views/GisPreviewPage.vue`
- `src/modules/traffic-gis-overview/`
- `src/components/gis/GisOverviewCesiumPanel.vue`
- `public/gis/`

### backend

- `server/app.py`
- `server/mysql_api.py`
- `server/mysql_db.py`
- `server/esg_demo_api.py`
- `server/requirements.txt`
- 当前 API 所需的后端模块、类型、服务和测试文件

运行链路：

```text
127.0.0.1:8765
→ server/app.py
→ server/mysql_api.py
→ server/esg_demo_api.py
→ MySQL 3307 / luoyi_esg
```

### database

- `server/schema.sql`
- `server/mysql_build_v0.1/`
- `server/mysql_build_v0.2_dashboard/`
- `server/migrations/`
- `server/init_db.py`
- 当前数据库初始化和迁移所需的 `seed_*.py`
- `server/migrations/esg_demo_v0_1/`
- `server/migrations/esg_demo_v0_3/`
- V0.3 首页 KPI 校正 SQL

### demo_data

- ESG Demo V0.1 种子和契约资料
- ESG Demo V0.3 首页 KPI 校正资料
- `server/dashboard_payload.json`
- `public/samples/`
- `public/test-data/`

所有 Demo 数据必须在新工作区文档中标明 `demo`，不得与正式业务数据混用。

### gis

- `src/modules/traffic-gis-overview/`
- `src/views/GisPreviewPage.vue`
- `src/components/gis/`
- `public/gis/`
- `server/seed_gis_map_v0_8.py`
- 当前 GIS API 相关后端读取逻辑和配置资料
- GIS 交接文档与当前有效地图配置

GIS 本次只迁移现有有效内容，不替换地图、不接入新数据源、不改 GIS 业务逻辑。

### docs / handoff / scripts

- 当前根目录 `README.md`
- `server/README.md`
- `server/API_CONTRACT.md`
- `server/FRONTEND_BACKEND_BASELINE.md`
- V0.3 首页一级指标业务事实校正报告
- 当前 `_handoff/` 中用于解释现有链路、数据模型、GIS 和页面交接的资料
- 当前启动、停止和验证脚本
- `versions/V0.3_homepage_kpi_calibration/`

## 三、建议不迁移列表（待用户确认）

以下项目建议不进入 `C:\ESG_Project` 主工作区，但只归档、不删除；如需追溯，可从旧工作区或 V0.3 归档查找。

| 建议不迁移项 | 原因 | 处理方式 |
|---|---|---|
| `node_modules/` | 依赖安装产物，体积大，可用 `npm ci` 重建 | 不迁移 |
| `dist/`、`dist-backup-*` | 构建产物或历史构建备份 | 不迁移 |
| `__pycache__/`、`*.pyc` | Python 缓存 | 不迁移 |
| `*.log`、`server.pid`、`vite-runtime*` | 运行时产物 | 不迁移 |
| `*_tmp*`、`_sec_*`、临时输出 txt/json | 临时诊断或中间产物 | 不迁移 |
| `screenshots/`、根目录历史截图 | 视觉验证产物，不是运行依赖 | 不迁移主工作区，可保留归档 |
| `backup-*`、`release-pack/`、历史 dist 备份 | 历史交付或备份包 | 不迁移主工作区，可保留归档 |
| `.git/`、`.trae/`、`.uploads/` | 旧工作区元数据、上传缓存或工具状态 | 不迁移 |
| 根目录历史交付包 `交付_*` | 已有阶段性交付资料，内容可能重复 | 不迁移主工作区，保留旧目录/归档 |
| 根目录 `_sec_*` 文件 | 文档抽取中间文件 | 不迁移 |
| 根目录 `_tmp_*` 文件 | 历史修复/验证临时文件 | 不迁移 |
| `.env` | 含本地连接配置和敏感凭据 | 绝不迁移；新工作区只生成脱敏模板 |

## 四、需要用户确认的边界项

以下内容存在追溯价值，暂不自动排除：

- `_handoff/` 中的旧任务单、设计说明和阶段性交接资料；
- `src/modules/traffic-gis-overview/` 中的历史配置、禁用数据和设计资料；
- `server/` 中的测试文件及旧版本 seed 文件；
- `docs/` 中的历史设计文档；
- 根目录的历史 Markdown 任务书；
- `backup-20260717/` 与 `release-pack/` 中可能包含的正式交付材料。

默认建议：有效代码进入主工作区，历史资料进入 `C:\ESG_Project\handoff\archive` 或 `C:\ESG_Project\versions`，不做删除。

## 五、禁止迁移/执行的事项

迁移验收前禁止：

- 修改首页、指标名称、单位和指标口径；
- 开发 S 组或 G 组；
- 调整 E 组业务逻辑；
- 修改数据库结构、Demo 数据或视图；
- 替换 GIS、接入新地图数据源；
- 重构接口或页面架构；
- 删除旧工作区文件。

## 六、确认后执行命令范围

用户确认后才执行：

1. 创建 `C:\ESG_Project` 目录结构；
2. 按本清单迁移有效文件；
3. 对迁移清单内文件生成源目录/目标目录 SHA256；
4. 写入 `PROJECT_RULES.md`、根 README、handoff 和 versions；
5. 在新工作区配置脱敏环境模板；
6. 用新工作区启动/验证前端、后端和数据库连接；
7. 输出最终迁移报告。

本清单生成本身未创建 `C:\ESG_Project`，未删除、移动或修改旧工作区业务文件。
