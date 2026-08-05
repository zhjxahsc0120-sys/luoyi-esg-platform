# 罗宜高速 ESG 多源数据流与首页指标动态更新设计 V1.0

更新时间：2026-07-16

## 1. 设计结论

罗宜高速 ESG 平台后续不应只依赖“资料上传解析”驱动首页指标，也不应长期依赖 `dashboard_*_snapshot` 这类页面快照表作为主数据源。

正式方向应调整为：

```text
多源数据接入
  ↓
标准化 / 映射 / 质量校验
  ↓
业务闭环表
  ↓
指标计算 / SQL 聚合
  ↓
首页 KPI / 弹窗 / 专题
  ↓
快照缓存 / 发布留痕
```

其中：

- 资料上传只是数据来源之一；
- 外部系统接口、人工填报、定时采集、GIS/空间数据也应进入同一套接入与追溯机制；
- 首页指标应主要由业务闭环表和指标结果表计算得到；
- 快照表只做缓存、版本发布和历史留痕，不能作为长期主数据源。

## 2. 当前问题判断

当前项目已完成较多真实库态推进：

- S01、E01、E02、S02、S03、S04、G01-G04 已能从业务明细表聚合；
- E03、E04、碳足迹专题、月报专题仍主要依赖快照或原型数据；
- `dashboard_kpi_detail_snapshot`、`dashboard_topic_snapshot`、`dashboard_panel_snapshot` 当前承担了过渡支撑作用。

这套过渡方案适合原型联调，但不能作为最终数据治理逻辑。

如果长期依赖快照表，会出现：

1. 首页数字与业务事实脱节；
2. 上传资料或接口同步后无法自然驱动首页变化；
3. 难以追溯“某个 KPI 数字为什么是这个值”；
4. 同一个业务事实可能在资料表、快照表、弹窗表中多处重复；
5. 后期审计、校核、月报追溯成本很高。

## 3. 推荐总体分层

### 3.1 多源接入层

负责接收各种来源的数据。

来源包括：

- 数据上传工作台上传的文件；
- 外部业务系统接口；
- 人工填报；
- 批量导入；
- 定时采集；
- GIS/空间数据；
- 第三方监测机构数据。

建议核心表：

| 表 | 用途 |
| --- | --- |
| `data_source_registry` | 登记数据来源，例如资料上传、证照系统、监测机构接口 |
| `data_ingestion_job` | 记录每一次接入任务，例如文件解析、接口同步、人工导入 |
| `data_mapping_rule` | 定义来源字段到业务字段的映射 |
| `data_quality_check_result` | 记录接入数据质量校验结果 |
| `source_record_trace` | 记录业务表每条数据来自哪个文件、接口、任务 |

### 3.2 资料层

负责资料本身的管理。

当前已有：

- `file_asset`
- `document_record`
- `document_version`
- `document_task_relation`
- `ai_parse_job`
- `ai_parse_field_result`
- `manual_confirmation_log`

资料层职责：

- 存原始文件；
- 存 AI 解析结果；
- 存人工确认结果；
- 管理资料版本；
- 管理资料与任务/流程的复用关系。

资料层不应直接作为首页 KPI 的唯一来源。

### 3.3 业务闭环层

这是首页动态更新的核心。

每个闭环逻辑都应有自己的业务事实表。

| 业务闭环 | 当前/建议业务表 | 支撑指标 |
| --- | --- | --- |
| 环境监测超标 | `env_monitoring_record` | E01 |
| 环保问题闭环 | `env_issue_record` | E02 |
| 水保问题闭环 | `water_protection_issue` | E03 |
| 碳排放活动 | `carbon_emission_activity`、`carbon_material_usage` | E04、碳专题 |
| 连续安全生产 | `safety_production_record` | S01 |
| 安全风险点 | `safety_risk_point` | S02 |
| 劳务纠纷 | `labor_dispute_record` | S03 |
| 群众诉求 | `appeal_record` | S04 |
| 合规手续 | `compliance_procedure` | G01 |
| 许可事项 | `permit_record` | G02 |
| 整改事项 | `rectification_record` | G03 |
| 合规资料缺口 | `compliance_material_gap` | G04 |
| 低碳措施 | 建议新增 `low_carbon_measure` | 碳专题 |
| 月报章节 | 建议新增 `monthly_report_chapter` | 月报专题 |
| 月报缺项 | 建议新增 `monthly_report_missing_item` | 月报专题 |
| 月报状态链 | 建议新增 `monthly_report_status_chain` | 月报专题 |

### 3.4 指标计算层

负责把业务闭环表转换为首页 KPI。

建议职责：

- 定义指标；
- 定义计算规则；
- 记录计算任务；
- 记录当前结果；
- 记录历史结果；
- 支持手动重算和定时重算。

当前已有：

- `indicator_definition`
- `indicator_result`
- `indicator_snapshot`

建议补强：

- `indicator_calculation_job`
- `indicator_history`
- `indicator_source_dependency`

### 3.5 展示与快照层

负责页面展示缓存和留痕。

当前已有：

- `dashboard_kpi_detail_snapshot`
- `dashboard_topic_snapshot`
- `dashboard_panel_snapshot`

后续定位应调整为：

| 快照表 | 正式定位 |
| --- | --- |
| `dashboard_kpi_detail_snapshot` | KPI 弹窗结果缓存、发布版本留痕 |
| `dashboard_topic_snapshot` | 专题页结果缓存、发布版本留痕 |
| `dashboard_panel_snapshot` | 首页组合面板缓存、发布版本留痕 |

快照表不应直接手工维护业务事实。

## 4. 多源数据进入业务闭环表的规则

### 4.1 资料上传路径

```text
用户上传资料
  ↓
file_asset
  ↓
ai_parse_job / ai_parse_field_result
  ↓
manual_confirmation_log
  ↓
document_record / document_version
  ↓
业务闭环表
  ↓
source_record_trace
```

示例：

```text
上传《NCR整改关闭资料》
  ↓
AI 抽取整改事项、状态、关闭日期
  ↓
人工确认
  ↓
写入 rectification_record
  ↓
G03 自动更新
```

### 4.2 外部系统接口路径

```text
外部系统接口
  ↓
data_ingestion_job
  ↓
data_mapping_rule
  ↓
data_quality_check_result
  ↓
业务闭环表
  ↓
source_record_trace
```

示例：

```text
证照管理系统接口
  ↓
permit_record
  ↓
G02 SQL 聚合
  ↓
首页 G02 动态更新
```

### 4.3 人工填报路径

```text
人工填报
  ↓
data_ingestion_job(source_type='MANUAL')
  ↓
业务闭环表
  ↓
source_record_trace
```

人工填报不应绕过业务闭环表直接修改首页快照。

## 5. 首页 12 项 KPI 正式数据来源

| KPI | 正式业务源 | 当前状态 | 后续动作 |
| --- | --- | --- | --- |
| E01 环境监测超标项 | `env_monitoring_record` | 已聚合 | 保持 |
| E02 未闭环环保问题 | `env_issue_record` | 已聚合 | 保持 |
| E03 未闭环水保问题 | `water_protection_issue` | 待真实化 | 下一阶段实现 |
| E04 碳排放强度 | `carbon_emission_activity` + 投资/产值口径 | 待真实化 | 与碳专题一起实现 |
| S01 连续安全生产天数 | `safety_production_record` | 已聚合 | 保持 |
| S02 安全风险点 | `safety_risk_point` | 已聚合 | 保持 |
| S03 劳务纠纷 | `labor_dispute_record` | 已聚合 | 保持 |
| S04 群众诉求 | `appeal_record` | 已聚合 | 保持 |
| G01 合规手续 | `compliance_procedure` | 已聚合 | 保持 |
| G02 许可临期/逾期 | `permit_record` | 已聚合 | 保持 |
| G03 整改事项 | `rectification_record` | 已聚合 | 保持 |
| G04 合规资料缺口 | `compliance_material_gap` | 已聚合 | 保持 |

## 6. 专题模块正式数据来源

### 6.1 合规保障与风险防控成效

正式来源：

- `compliance_procedure`
- `permit_record`
- `rectification_record`
- `compliance_material_gap`
- 后续可增加 `legal_risk_record`、`compliance_safeguard_action`

当前策略：

- 首页右侧合规模块仍可使用快照缓存；
- 明细应逐步改为从上述业务表聚合。

### 6.2 碳足迹与低碳增益

正式来源：

- `carbon_emission_activity`
- `carbon_material_usage`
- 建议新增 `low_carbon_measure`
- 建议新增 `carbon_factor_library`
- 建议新增 `carbon_baseline_scenario`

当前策略：

- E04 和碳专题应一起推进；
- 不建议继续只维护 `dashboard_topic_snapshot`。

### 6.3 月报准备与输出

正式来源：

- `document_record`
- `document_task_relation`
- `upload_task`
- 建议新增 `monthly_report_chapter`
- 建议新增 `monthly_report_missing_item`
- 建议新增 `monthly_report_status_chain`

当前策略：

- 月报专题不应从单个 JSON 快照长期读取；
- 应由资料完成度、章节状态、缺项清单和审核状态聚合生成。

## 7. 指标动态更新机制

建议采用两种机制并存：

### 7.1 事件触发

当以下事件发生时，触发相关指标重算：

- 资料确认入库；
- 外部接口同步完成；
- 人工填报保存；
- 审核通过或退回；
- 整改关闭；
- 许可状态变化；
- 月报资料状态变化。

事件示例：

```text
permit_record 更新
  ↓
触发 G02 重算
  ↓
更新 indicator_result
  ↓
刷新 dashboard_kpi_detail_snapshot
```

### 7.2 定时重算

每天或每小时定时重算：

- 临期/逾期类指标；
- 连续天数类指标；
- 月报倒计时；
- 碳排放累计值；
- 资料完成率。

原因：

即使没有新数据写入，日期变化也会导致指标变化。

例如 G02：

```text
今天未逾期
明天可能逾期
```

所以必须支持定时任务。

## 8. 快照表使用规则

快照表可以存在，但要遵守以下规则：

1. 不能作为业务事实主表；
2. 不能由前端或人工直接维护；
3. 只能由指标计算或专题聚合任务生成；
4. 必须记录生成时间、数据版本、来源批次；
5. 必须能追溯到业务明细表或接入任务；
6. 可以用于页面性能优化；
7. 可以用于领导层某日展示结果留痕。

推荐定位：

```text
业务表是事实
指标表是结果
快照表是发布版本
```

## 9. 建议后续实施顺序

### 阶段一：补齐多源接入治理表

新增或完善：

- `data_source_registry`
- `data_ingestion_job`
- `data_mapping_rule`
- `data_quality_check_result`
- `source_record_trace`

目标：

让资料上传、接口同步、人工填报统一纳入接入任务管理。

### 阶段二：完成剩余 KPI 真实化

优先：

1. E03 未闭环水保问题；
2. E04 碳排放强度；
3. 碳足迹专题；
4. 月报专题。

### 阶段三：建设指标计算任务

新增：

- `indicator_calculation_job`
- `indicator_history`
- `indicator_source_dependency`

目标：

让首页 KPI 不再依赖接口即时拼装，而是有可追溯计算批次。

### 阶段四：快照表降级

将：

- `dashboard_kpi_detail_snapshot`
- `dashboard_topic_snapshot`
- `dashboard_panel_snapshot`

定位调整为：

- 页面缓存；
- 发布留痕；
- 历史版本回放。

## 10. 对当前开发协作的影响

### Codex 侧

继续负责：

- 数据库设计；
- 后端接口；
- 多源接入逻辑；
- 指标计算；
- 真实库态测试；
- 任务书输出。

### Trae 侧

继续负责：

- 前端点测；
- 样式适配；
- 文案统一；
- 弹窗布局优化。

Trae 不建议修改：

- 数据接入逻辑；
- API 字段结构；
- store 聚合逻辑；
- 后端接口。

## 11. 当前结论

后续系统应从“资料上传驱动首页”升级为：

```text
多源数据接入驱动业务闭环
业务闭环驱动指标计算
指标计算驱动首页展示
快照表只做缓存和留痕
```

这套逻辑更适合后期接入外部系统、自动更新首页、支撑月报生成和审计追溯。

## 12. V1.0 落库状态

本设计中的多源接入治理核心表已于 2026-07-16 落库，并写入基础种子与最小闭环样例。

已执行脚本：

- `server/multisource_data_flow_v1.0/01_multisource_schema.sql`
- `server/seed_multisource_data_flow_v1_0.py`

已新增表：

| 表名 | 当前用途 | 当前样例状态 |
| --- | --- | --- |
| `data_source_registry` | 登记上传、接口、人工、GIS、定时任务等数据源 | 已写入 11 个数据源 |
| `data_ingestion_job` | 记录文件解析、接口同步、人工导入等接入任务 | 已写入 3 条样例 |
| `data_mapping_rule` | 维护来源字段到业务字段的映射规则 | 已写入 14 条样例 |
| `data_quality_check_result` | 记录质量校验、业务规则校验结果 | 已写入 4 条样例 |
| `source_record_trace` | 追溯业务记录来源 | 已写入 4 条样例 |
| `indicator_calculation_job` | 记录指标计算任务和触发来源 | 已写入 2 条样例 |
| `indicator_history` | 记录指标历史结果 | 已写入 2 条样例 |
| `indicator_source_dependency` | 维护指标与正式业务源表的依赖关系 | 已写入 15 条依赖 |

已通过验收：

- `server/multisource_data_flow_test.py`
- 全部 dashboard / workspace / review / MySQL 回归测试
- `npm run check`
- `npm run build`

### 12.1 当前最小闭环样例

已写入三个典型接入任务：

```text
第三方环境监测机构接口
  → data_ingestion_job
  → env_monitoring_record
  → source_record_trace
  → E01 指标计算任务
  → indicator_history
```

```text
证照许可管理系统接口
  → data_ingestion_job
  → permit_record
  → source_record_trace
  → G02 指标计算任务
  → indicator_history
```

```text
数据上传工作台资料解析
  → data_ingestion_job
  → rectification_record
  → source_record_trace
  → G03 可追溯业务闭环
```

### 12.2 下一步建议

下一步不建议继续扩快照表，而应优先做：

1. E03 水保问题真实化；
2. E04 碳排放强度真实化；
3. 碳足迹专题从 `carbon_emission_activity`、`carbon_material_usage`、`low_carbon_measure` 聚合；
4. 月报专题从 `document_record`、`upload_task`、月报章节/缺项表聚合；
5. 将 P03 智能入库“确认入库”动作接入 `data_ingestion_job` 和 `source_record_trace`。

