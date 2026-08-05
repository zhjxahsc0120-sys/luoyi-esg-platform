# 罗宜高速 ESG 前后端联调基线 V0.2

本文件用于固定当前“领导层 ESG 看板 + 数据填报与上传工作台”的第一版 API 联调范围。Trae 后续继续修前端时，建议以本文件和 `smoke_test.py` 作为回归基线。

## 1. 服务地址

```text
http://127.0.0.1:8765
```

当前后端运行模式：

```text
mysql-first
```

即 MySQL 可用时优先读取 `127.0.0.1:3307/luoyi_esg`，不可用时回退 SQLite 联调库。

启动：

```powershell
powershell -ExecutionPolicy Bypass -File server\start_backend.ps1
```

停止：

```powershell
powershell -ExecutionPolicy Bypass -File server\stop_backend.ps1
```

重新初始化数据库：

```powershell
python server\init_db.py
```

Codex 环境可用 bundled Python：

```powershell
C:\Users\TB\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe server\init_db.py
```

## 2. 当前已接入接口

| 页面 | 接口 | 当前用途 |
|---|---|---|
| 领导层首页 | `GET /api/dashboard/kpis` | 首页顶部 E/S/G 12 项 KPI |
| S01 弹窗 | `GET /api/dashboard/kpi/S01` | 连续安全生产天数中央弹窗 |
| 工作台 P01/P02 | `GET /api/workspace/summary` | 工作台状态卡 |
| 工作台 P01/P02 | `GET /api/workspace/tasks` | 上传任务列表 |
| 工作台 S01 | `GET /api/workspace/tasks/{id}/detail` | 任务办理中央弹窗 |
| 资料中心 P05 | `GET /api/workspace/documents/summary` | 资料中心状态卡 |
| 资料中心 P05 | `GET /api/workspace/documents` | 资料列表与 E/S/G 分类筛选 |
| 审核结果 P04 | `GET /api/workspace/reviews` | 审核状态卡和审核记录 |
| ESG 智能入库 P03 | `GET /api/workspace/ai/parse-queue` | AI 解析队列 |

## 3. 必须保持稳定的关键数据

首页 KPI：

```text
E01=2, E02=5, E03=7, E04=12856
S01=368, S02=6, S03=4, S04=3
G01=5, G02=5, G03=6, G04=4
```

S01：

```text
projectStartDate=2025-07-10
currentDate=2026-07-13
continuousDays=368
currentStage=主体工程施工
currentStageDetail=路基｜桥梁｜隧道并行施工
constructionStages=4 个主阶段
```

工作台摘要：

```text
currentTodo=27
pendingUpload=12
pendingCorrection=3
pendingSubmit=5
underReview=3
dueSoon=4
completed=36
```

任务办理弹窗：

```text
documents=7
validation.completed=5
validation.missing=1
validation.abnormal=1
candidateDocuments=5
reviewTimeline=2
```

资料中心：

```text
documentTotal=368
monthNew=24
pendingArchive=6
expiringSoon=4
documents.items=10 条样例
documents.items.module 覆盖 E/S/G
```

审核结果：

```text
statusCards=4
reviews.items=7
```

AI 解析队列：

```text
parseQueue.items=3
```

## 4. 回归命令

后端 API 冒烟测试：

```powershell
python server\smoke_test.py
```

前端类型检查与构建：

```powershell
npm run check
npm run build
```

如果本机 `npm` 不在 PATH，可在 Codex 环境中临时补 PATH：

```powershell
$env:PATH='C:\Users\TB\.cache\codex-runtimes\codex-primary-runtime\dependencies\node\bin;' + $env:PATH
.\node_modules\.bin\vue-tsc.cmd -b
.\node_modules\.bin\vite.cmd build
```

## 5. 当前仍保留 mock 的范围

- 除 S01 外的 11 个 KPI 详情弹窗；
- 碳足迹专题、月报专题详情；
- 首页 GIS 路线图、合规保障、碳效益面板、建设时间线、月报面板；
- 资料中心右侧详情面板；
- 审核结果右侧审核轨迹与补正要求；
- AI 解析摘要、建议关联任务；
- 今日关注、快捷问题。

这些区域暂不纳入本轮后端接口基线，避免前端还在原型阶段时过早固化过多接口。
