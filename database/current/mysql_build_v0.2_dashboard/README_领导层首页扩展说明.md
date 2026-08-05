# 罗宜高速 ESG 领导层首页 MySQL 扩展 V0.2

本扩展用于把当前领导层首页剩余弹窗和专题模块，从 `dashboard_payload.json` 原型数据推进到 MySQL 可管理数据。

## 覆盖范围

- E01-E04、S02-S04、G01-G04 共 11 个 KPI 通用弹窗；
- 碳足迹与低碳增益专题；
- 月报准备与输出专题；
- 合规保障与风险防控成效首页面板；
- 首页碳足迹面板、月报面板、GIS 点位、建设时间线。

S01「连续安全生产天数」已有专属表 `safety_production_record`，不纳入本快照表。

## 表设计思路

V0.2 采用“快照扩展层”：

| 表 | 用途 |
| --- | --- |
| `dashboard_kpi_detail_snapshot` | 存 KPI 弹窗完整结构 |
| `dashboard_topic_snapshot` | 存专题弹窗完整结构 |
| `dashboard_panel_snapshot` | 存首页专题面板/GIS/时间线组合结构 |

这样做的好处：

- 前端接口结构不变；
- 后端优先读 MySQL，MySQL 不可用时仍可 fallback 到 JSON；
- 后续可以逐项把 JSON 快照替换成 `env_monitoring_record`、`permit_record`、`carbon_emission_activity` 等业务表实时聚合。

## 执行顺序

```powershell
$env:PYTHONIOENCODING='utf-8'
$py='C:\Users\TB\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'
& $py server\seed_dashboard_snapshots_v0_2.py
```

执行后可运行：

```powershell
& $py server\dashboard_acceptance_test.py
```

