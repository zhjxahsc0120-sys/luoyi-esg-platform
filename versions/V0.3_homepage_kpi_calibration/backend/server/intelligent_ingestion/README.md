# 罗宜高速 ESG 智能体资料自动解析入库扩展设计 V0.1

本目录用于承接“智能体资料自动解析入库”能力的数据库与接口扩展设计。

当前 `server/schema.sql` 是页面联调型 SQLite 基线，已经支撑领导首页、上传工作台、任务办理弹窗等页面。智能入库能力不直接改动该基线，而是以本目录为扩展包逐步落地。

## 设计边界

智能入库链路覆盖：

```text
文件上传/选择已有资料
→ 文件去重
→ AI 解析
→ 字段抽取
→ 字段标准化
→ 候选任务匹配
→ 人工确认
→ 资料正式入库
→ 资料任务关联
→ 操作留痕
```

## 文件说明

| 文件 | 说明 |
|---|---|
| `schema_extension_v0.1.sql` | 智能入库扩展表 SQL 草案 |
| `field_mapping_seed_v0.1.sql` | 抽取字段到数据库字段的映射规则样例 |
| `INGESTION_DB_DESIGN_V0.1.md` | 设计说明 |
| `INGESTION_API_CONTRACT_V0.1.md` | 后续接口建议 |

## 当前结论

AI 抽取字段可以对应进库，但不建议直接写业务主表。推荐流程为：

```text
ai_parse_field_result 保存原始抽取结果
→ ai_field_mapping_rule 判断目标表/字段
→ 人工确认
→ document_record / document_task_relation / 业务明细表
```

这样可以保留 AI 原始值、标准化值、置信度、人工修正值和审计记录。
