# 罗宜高速 ESG 本地后端联调服务

本目录由 Codex 维护，Trae 可继续只处理前端页面。

## 一、定位

这是当前前端原型的本地后端联调底座：

- 使用 Python 标准库提供 HTTP API；
- 使用 SQLite 作为本地开发镜像库；
- 数据口径对齐当前前端页面与 `luoyi_esg_page_test_data_v1.1_patch.sql`；
- 不替代正式 MySQL 数据库成果包，后续可平滑迁移到 MySQL/NestJS/FastAPI。

## 二、启动

在项目根目录执行：

```powershell
python server/init_db.py
python server/app.py
```

当前后端支持 MySQL-first 模式：

```text
MySQL: 127.0.0.1:3307 / luoyi_esg
用户: luoyi_app
```

MySQL 可用时接口优先读取 MySQL；MySQL 不可用时回退 SQLite 联调库。

如更换 Python 环境，请先安装依赖：

```powershell
python -m pip install -r server/requirements.txt
```

如果系统 `python` 不在 PATH，可使用 Codex bundled Python：

```powershell
C:\Users\TB\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe server/init_db.py
C:\Users\TB\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe server/app.py
```

服务地址：

```text
http://127.0.0.1:8765
```

数据库文件：

```text
server/data/luoyi_esg_dev.db
```

## 三、已提供接口

```text
GET /health
GET /api/dashboard/kpis
GET /api/dashboard/snapshot?type=LEADER_HOME
GET /api/dashboard/kpi/S01
GET /api/workspace/summary
GET /api/workspace/tasks
GET /api/workspace/tasks/{id}/detail
GET /api/workspace/documents/summary
GET /api/workspace/documents
GET /api/workspace/reviews
GET /api/workspace/ai/parse-queue
POST /api/esg/document/analyze
GET /api/esg/document/{analysis_id}/result
```

工程资料 AI 解析接口、独立数据表和测试数据说明见：

```text
server/AI_DOCUMENT_ANALYSIS_API.md
```

## 四、基线回归

启动后端后，可执行：

```powershell
python server/smoke_test.py
```

通过后会输出：

```text
✅ 后端 API 冒烟测试通过：当前接口与前端联调基线一致。
```

当前前后端联调基线详见：

```text
server/FRONTEND_BACKEND_BASELINE.md
```

## 五、当前口径

领导首页 KPI：

```text
E01=2
E02=5
E03=7
E04=12856 tCO₂e
S01=368
S02=6
S03=4
S04=3
G01=5
G02=5
G03=6
G04=4
```

上传工作台：

```text
当前待办=27
待上传=12
待补正=3
待提交=5
审核中=3
即将到期=4
已完成=36
```

资料中心：

```text
资料总数=368
本月新增=24
待归档=6
即将失效=4
```

## 六、前端对接建议

前端先不要删除 mock 数据，可新增 API service：

```text
src/services/api.ts
```

将 `dashboard.mock.ts` 和 `workspace.mock.ts` 的数据读取逐步切到接口；若接口不可用，则回退到 mock。这样 Trae 修页面时不会被后端状态卡住。
