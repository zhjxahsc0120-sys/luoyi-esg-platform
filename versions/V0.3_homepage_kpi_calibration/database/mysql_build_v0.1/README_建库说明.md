# 罗宜高速 ESG MySQL 建库包 V0.1

本目录是“罗宜高速 ESG 数据库与接口完整设计 V0.1”的 MySQL 可建库脚本包。

当前定位：

- 面向 MySQL 8.0；
- 支撑当前已完成前端页面联调；
- 支撑智能体资料自动解析入库主链路；
- 支撑首页 12 项 KPI 的结果表与后续业务明细来源；
- 暂不替代未来正式生产级权限、流程引擎和运维审计体系。

## 文件清单

| 文件 | 用途 |
|---|---|
| `01_schema_mysql.sql` | 创建数据库、核心表、索引 |
| `02_seed_dictionary.sql` | 初始化字典、指标定义、组织样例 |
| `03_seed_field_mapping.sql` | 初始化 AI 字段映射规则 |
| `04_seed_demo_data.sql` | 初始化页面联调样例数据 |
| `05_views.sql` | 初始化汇总视图 |
| `06_validation_queries.sql` | 建库后校验 SQL |

## 推荐执行顺序

```sql
SOURCE 01_schema_mysql.sql;
SOURCE 02_seed_dictionary.sql;
SOURCE 03_seed_field_mapping.sql;
SOURCE 04_seed_demo_data.sql;
SOURCE 05_views.sql;
SOURCE 06_validation_queries.sql;
```

如果使用命令行：

```powershell
mysql -uroot -p < 01_schema_mysql.sql
mysql -uroot -p luoyi_esg < 02_seed_dictionary.sql
mysql -uroot -p luoyi_esg < 03_seed_field_mapping.sql
mysql -uroot -p luoyi_esg < 04_seed_demo_data.sql
mysql -uroot -p luoyi_esg < 05_views.sql
mysql -uroot -p luoyi_esg < 06_validation_queries.sql
```

## 当前核心链路

```text
file_asset
→ ai_parse_job
→ ai_parse_field_result
→ ai_field_mapping_rule
→ task_match_candidate
→ manual_confirmation_log
→ document_record
→ document_version
→ document_task_relation
→ indicator_result / indicator_snapshot
```

## 当前建库包验收口径

建库后应满足：

```text
首页 KPI = 12 条
S01 = 368 天
上传任务 = 12 条
资料中心样例 = 10 条
审核记录 = 7 条
AI 字段映射规则 >= 27 条
智能入库样例解析任务 = 3 条
候选匹配任务 >= 1 条
```

## 后续建议

等 MySQL 实例准备好后，可由 Codex 执行：

1. 建库；
2. 导入脚本；
3. 执行校验 SQL；
4. 将当前 Python SQLite 原型服务改为读取 MySQL；
5. 再让 Trae 接智能入库页面接口。
