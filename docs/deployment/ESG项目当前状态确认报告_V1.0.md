# ESG项目当前状态确认报告 V1.0

**确认日期：** 2026-08-04  
**唯一工作区：** `C:\ESG_Project`  
**当前基线：** ESG Demo V0.3：首页一级指标业务事实校正版

## 一、确认结论

项目已按迁移基线在 `C:\ESG_Project` 建立。当前工作区结构、基线归档、迁移清单和项目规则文件均存在。

本次确认未修改业务代码、数据库结构、页面、API路径、指标口径或 Demo 数据；仅生成本报告，并修正了迁移报告中一处 SHA256 文件数笔误（1399 改为 1395）。

## 二、当前技术架构

| 层级 | 当前确认结果 |
|---|---|
| 前端 | Vue 3 + TypeScript + Vite 5；Vue Router、Pinia、ECharts、Cesium |
| 后端 | Python 原生 `http.server`：`ThreadingHTTPServer`，入口为 `backend/app.py`，监听 8765 |
| 数据库 | MySQL 8.4.9；当前连接 `127.0.0.1:3307/luoyi_esg` |
| GIS | Cesium 3D 地图能力、GeoJSON/KML 图层、交通 GIS Overview 模块；前端运行模块仍位于 `frontend/src/modules/traffic-gis-overview/` |

## 三、当前目录结构

```text
C:\ESG_Project
├── frontend       # 当前前端源代码、配置和静态资源
├── backend        # 当前 Python API、MySQL 访问和服务模块
├── database       # current 当前版本 SQL；archive 历史 build/migration
├── gis            # current 当前 GIS 模块与资源；archive 历史配置/测试
├── docs           # current 当前文档；archive 历史设计资料
├── demo_data      # current 当前 Demo 数据；archive 历史种子脚本
├── handoff        # current 当前交接资料；archive 历史交接资料
├── scripts        # 启停和环境辅助脚本
└── versions       # V0.3 基线归档
```

关键文件确认存在：

- `README.md`
- `PROJECT_RULES.md`
- `migration_manifest.md`
- `ESG工作区迁移报告.md`
- `versions/V0.3_homepage_kpi_calibration/README.md`
- `versions/V0.3_homepage_kpi_calibration/frontend/`
- `versions/V0.3_homepage_kpi_calibration/backend/`
- `versions/V0.3_homepage_kpi_calibration/database/`
- `versions/V0.3_homepage_kpi_calibration/demo_data/`
- `versions/V0.3_homepage_kpi_calibration/docs/`

迁移清单共 1,395 条文件记录，最终 SHA256 校验结果为 1,395/1,395 匹配，0 条不匹配；未迁移 `.env`、缓存、构建产物和 `node_modules` 等内容。`npm ci` 和构建验证期间产生的 `frontend/node_modules`、`frontend/dist` 属于验证产物，不属于迁移清单。

## 四、当前运行链路

```text
MySQL 8.4.9
127.0.0.1:3307 / luoyi_esg
        ↓
Python API
backend/app.py : 8765
        ↓
Vite Dev Server
frontend/vite.config.ts : 5173
        ↓
ESG Dashboard
浏览器 http://localhost:5173/#/
```

首页 KPI 的实际代码路径为：

```text
frontend/src/services/api.ts
        ↓ GET /api/dashboard/kpis
vite.config.ts proxy → http://127.0.0.1:8765
        ↓
backend/app.py
        ↓
backend/mysql_api.py / backend/esg_demo_api.py
        ↓
MySQL v_esg_demo_dashboard_kpis
        ↓
esg_demo_indicator_result
```

前端配置确认：`/api` 代理目标为 `http://127.0.0.1:8765`；API 服务的 MySQL 默认配置为端口 3307、数据库 `luoyi_esg`。

当前机器端口检查结果：3307、5173、8765 均在监听。现有 5173/8765 进程的命令行仍指向旧工作区，用于保持当前页面运行；新工作区已完成独立的前端检查、构建、Python 编译和临时 5174 API 访问验证，未强行抢占现有端口。

## 五、V0.3 已完成模块

1. 首页驾驶舱及 E/S/G 三组一级指标展示。
2. 首页 12 项 ESG 一级 KPI 业务事实和展示口径确认。
3. MySQL Demo 数据 → KPI 视图 → Python API → 前端展示链路。
4. E04 文物保护对象无对象时显示 0 处。
5. S01 按 2026-05-08 起算日期动态计算连续安全生产天数。
6. S03 工资支付达标率以百分比展示。
7. G01/G02/G03 使用合规、完成、受控表达；G04 使用内控合规状态表达。
8. 当前有效 GIS 能力：Cesium/交通 GIS Overview、静态 GeoJSON/KML 图层和相关图层配置已迁移。

## 六、实际 KPI 返回确认

实际请求：`GET http://127.0.0.1:8765/api/dashboard/kpis`  
返回：HTTP 200；`projectId=1001`，`periodEnd=2026-08-04`，`source=esg_demo`。

| KPI | 当前返回 | 单位/状态 | 业务表达确认 |
|---|---:|---|---|
| E04 | 0 | 处 | 已完成文物调查，无涉文物影响 |
| S01 | 89 | 天 | 自 2026-05-08 起，按统计截止日动态计算 |
| S03 | 100 | % | 工资按期足额支付 |
| G01 | 12/12 | 100% | 审批合规率 |
| G02 | 2/2 | 100% | 许可管控完成率 |
| G03 | 4/4 | 100% | 设计变更受控率 |
| G04 | 正常 | 无数量单位 | 内控合规状态 |

## 七、当前冻结内容

以下内容按 V0.3 基线冻结，后续变更须先取得人工确认：

- **首页指标：** E01-E04、S01-S04、G01-G04 的名称、单位、展示值和描述口径。
- **数据库事实链：** `esg_demo_indicator_result` 已发布结果及 `v_esg_demo_dashboard_kpis` 视图；当前 V0.3 SQL 位于 `database/current/esg_demo_v0_3/`。
- **API 契约：** `GET /api/dashboard/kpis` 的现有路径及 `items`、`groups` 返回结构；不新增 API，不改变整体字段结构。
- **页面结构：** 首页驾驶舱布局、一级 KPI 卡片和现有路由结构。
- **迁移边界：** `current` 为当前工作内容，`archive` 为追溯资料，不作为默认开发入口。

## 八、当前待开发任务建议（仅列清单，不执行）

1. 对 E01/E02/G01/S01 等二级页面逐项进行业务事实审计。
2. 统一一级指标与二级下钻的事实来源、日期口径和状态表达。
3. 评审 GIS 当前模块的正式归属、图层数据来源和生产化接口边界。
4. 评审正式数据库迁移方案、凭据配置和部署方式。
5. 明确 S 组、G 组深化页面的业务范围后再进入开发。
6. 迁移完成验收后，再按 `PROJECT_RULES.md` 重新开启开发任务。

## 九、禁止操作确认

本次未执行：

- 修改业务代码、前端页面或页面布局；
- 修改数据库、数据库结构或 Demo 数据；
- 新增字段、调整指标口径或新增 API；
- 重构接口或开发 S/G/E/GIS 新功能。

**当前状态：** V0.3 首页一级指标基线已识别并保持冻结，等待下一步指令。
