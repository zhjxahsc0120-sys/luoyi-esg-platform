# 罗宜高速 ESG 页面-接口-数据表映射 V0.1

## 1. 领导层 ESG 看板

| 页面区域 | 当前接口 | 后续正式来源表 |
|---|---|---|
| 顶部 12 项 KPI | `/api/dashboard/kpis` | `indicator_result` |
| S01 弹窗 | `/api/dashboard/kpi/S01` | `safety_production_record` + `indicator_detail_snapshot` |
| 其他 KPI 弹窗 | 暂未接入 | E/S/G 业务明细表 + `indicator_detail_snapshot` |
| GIS 地图 | 暂未接入 | `project_route_point`, `risk_location`, `environment_location` |
| 碳足迹专题 | 暂未接入 | `carbon_emission_activity`, `low_carbon_measure` |
| 月报专题 | 暂未接入 | `monthly_report_chapter`, `monthly_report_missing_item` |

## 2. 数据填报与上传工作台

| 页面区域 | 当前接口 | 后续正式来源表 |
|---|---|---|
| P01 状态卡 | `/api/workspace/summary` | `workspace_summary` 或任务状态聚合 |
| P01 任务列表 | `/api/workspace/tasks` | `upload_task` |
| P02 我的上传任务 | `/api/workspace/tasks` | `upload_task` |
| S01 任务办理弹窗 | `/api/workspace/tasks/{id}/detail` | `upload_task`, `upload_task_requirement`, `document_task_relation` |
| P03 解析队列 | `/api/workspace/ai/parse-queue` | `ai_parse_job`, `file_asset` |
| P03 解析摘要 | 暂未接入 | `ai_parse_field_result` |
| P03 建议关联任务 | 暂未接入 | `task_match_candidate` |
| P04 审核结果 | `/api/workspace/reviews` | `review_record` |
| P05 资料列表 | `/api/workspace/documents` | `document_record` |
| P05 资料详情 | 暂未接入 | `document_record`, `document_version`, `document_task_relation` |

## 3. 智能入库关键字段入库映射

| AI 字段 | 先进入 | 确认后进入 |
|---|---|---|
| 资料名称 | `ai_parse_field_result` | `document_record.document_name` |
| 资料类型 | `ai_parse_field_result` | `document_record.document_type` |
| ESG 模块 | `ai_parse_field_result` | `document_record.module_code` |
| 资料周期 | `ai_parse_field_result` | `document_record.period_value` |
| 责任单位 | `ai_parse_field_result` | `document_record.responsible_unit` |
| 有效期 | `ai_parse_field_result` | `document_record.valid_start_date/end_date` |
| 业务指标字段 | `ai_parse_field_result` | E/S/G 业务明细表 |

## 4. 设计结论

当前页面中：

- P03、S01、P05、P04 是数据生产与确认链路；
- 领导首页是结果消费链路；
- 因此后续接口接入应优先工作台，再领导首页。

不建议当前立即接入剩余 11 个 KPI 弹窗，因为其正式数据来源尚未全部固化。
