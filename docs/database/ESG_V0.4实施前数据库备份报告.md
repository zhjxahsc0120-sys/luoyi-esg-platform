# ESG V0.4 实施前数据库备份报告

**备份时间：** 2026-08-04 21:13:01（Asia/Shanghai）  
**工作区：** `C:\ESG_Project`  
**数据库实例：** `127.0.0.1:3307`  
**数据库：** `luoyi_esg`  
**当前基线：** ESG Demo V0.3：首页一级指标业务事实校正版

## 一、执行结论

本阶段已完成 MySQL 环境检查、全库结构备份、重点表结构和数据备份、视图定义导出以及 V0.3 KPI 快照。

本阶段未执行 `CREATE TABLE`、`ALTER TABLE`、`DROP TABLE`、`INSERT`、`UPDATE`、`DELETE`、数据迁移、API 修改或前端修改。

当前状态：备份和环境检查完成，等待下一步“执行数据库变更”指令。

## 二、数据库环境检查

| 检查项 | 实际结果 | 状态 |
|---|---|---|
| MySQL 版本 | 8.4.9 | ✅ |
| 连接地址 | `127.0.0.1:3307` | ✅ |
| 数据库 | `luoyi_esg` | ✅ |
| 当前用户 | `luoyi_app@127.0.0.1` | ✅ |
| 当前权限 | `ALL PRIVILEGES ON luoyi_esg.* WITH GRANT OPTION` | ✅ |
| 服务端/数据库/连接字符集 | `utf8mb4` | ✅ |
| 排序规则 | `utf8mb4_0900_ai_ci` | ✅ |
| 全局/会话时区 | `SYSTEM` / `SYSTEM` | ✅ |
| 数据库本地时间 | `2026-08-04 21:11:43` | ✅ |
| UTC 时间 | `2026-08-04 13:11:43` | ✅ |
| BASE TABLE | 128 | ✅ |
| VIEW | 21 | ✅ |

当前数据库 `SYSTEM` 时区与项目 Asia/Shanghai 环境一致；后续迁移仍需明确日期口径，避免将数据库时间误当 UTC。

## 三、备份位置

```text
C:\ESG_Project\database\archive\v0.4_pre_migration\20260804_211301\
```

## 四、备份文件与校验值

### 1. 结构备份

| 文件 | 内容 | 大小 | SHA256 |
|---|---|---:|---|
| `schema_all.sql` | 全库表结构、索引、约束、触发器、例程及视图相关定义；128 张表 | 522034 | `D2EF82BA1F377984BFF2FAC0F8E15EFBDE995EF3A207BA31206CC45196AC654E` |
| `重点表结构.sql` | 7 张重点表的结构、索引和约束 | 28410 | `7C5AA20B548515574BFCC0C01EBF41423610BAD6B9F7B32EFD88509896593F21` |
| `views_definition.tsv` | `information_schema.views` 导出的 21 个视图定义 | 77774 | `30FEEDF3232C12B549D3EDF3219B3765C785E08BD5759DC40CBC029342AE9E02` |

### 2. 重点表数据备份

| 文件 | 内容 | 大小 | SHA256 |
|---|---|---:|---|
| `重点表数据.sql` | 重点表数据，仅包含数据 INSERT | 27550 | `DA64F7BD609471E07A38127BC0AA9D4D532E27ACC4D284BBB4794573D74DE556` |

包含：`e_closure_case`、`e_rectification_task`、`biz_worker_payment_summary`、`compliance_procedure`、`permit_record`、`safety_risk_point`、`biz_internal_control_issue`。

### 3. KPI 快照

| 文件 | 内容 | 大小 | SHA256 |
|---|---|---:|---|
| `v0.3_dashboard_kpi_view.tsv` | 直接读取 `v_esg_demo_dashboard_kpis`，12 行 | 1862 | `0F239635AFF30FDDB73C39D0BD825E5ED38CB9C27EE8D8A5915A103C31BF2090` |
| `v0.3_dashboard_kpi_api.json` | `GET /api/dashboard/kpis`，HTTP 200 | 4625 | `2A992C9E5C4DFB9E628A2C0E6FE615598EF14EE4002B6892F5A6E6D82BFB8340` |
| `backup_manifest_sha256.csv` | 上述主要文件的大小与 SHA256 清单 | — | 以文件内容为准 |

备份目录中的 `.stderr.log` 仅记录 MySQL 客户端“命令行传入密码”的安全警告；最终备份命令均成功，未发现数据库错误。

## 五、重点表数据量

| 表 | 备份前数据量 |
|---|---:|
| `e_closure_case` | 17 |
| `e_rectification_task` | 2 |
| `biz_worker_payment_summary` | 2 |
| `compliance_procedure` | 7 |
| `permit_record` | 5 |
| `safety_risk_point` | 10 |
| `biz_internal_control_issue` | 2 |

## 六、V0.3 KPI 快照确认

API 快照确认：`HTTP 200`、`source=esg_demo`、`projectId=1001`、`periodEnd=2026-08-04`、12 个 KPI。

| KPI | 变更前快照 |
|---|---:|
| E04 文物保护对象 | 0 处 |
| S01 连续安全生产 | 89 天 |
| S03 工资支付达标率 | 100% |
| G01 审批合规率 | 12/12，100% |
| G02 许可管控完成率 | 2/2，100% |
| G03 设计变更受控率 | 4/4，100% |
| G04 内控合规状态 | 正常 |

后续变更前后对比必须使用本目录快照，不使用页面截图或前端临时值替代。

## 七、验证结果

- `schema_all.sql` 非空，包含 128 个 `CREATE TABLE` 定义；
- `重点表结构.sql` 非空，包含 7 张重点表结构；
- `重点表数据.sql` 非空，包含 7 张重点表数据段；
- `views_definition.tsv` 非空，包含 `v_esg_demo_dashboard_kpis`；
- 数据库 KPI 快照 12 行，API KPI 快照 12 项；
- 关键 KPI 已核对：E04=0、S01=89、S03=100%、G04=正常；
- 主要备份文件已生成 SHA256；
- 未执行数据库写操作。

本次未执行恢复演练。恢复演练必须在隔离数据库中进行，不能直接对当前 `luoyi_esg` 恢复。

## 八、恢复方式

仅允许在隔离目标库恢复，不得直接指向当前 `luoyi_esg`：

```powershell
mysql.exe --host=127.0.0.1 --port=3307 --user=<DB_USER> --password <target_database> < C:\ESG_Project\database\archive\v0.4_pre_migration\20260804_211301\schema_all.sql
mysql.exe --host=127.0.0.1 --port=3307 --user=<DB_USER> --password <target_database> < C:\ESG_Project\database\archive\v0.4_pre_migration\20260804_211301\重点表数据.sql
```

恢复后依次检查表数量、重点表行数、视图定义和 KPI 快照；密码不得写入脚本、文档或 Git。

## 九、下一步闸门

```text
数据库环境检查 ✅
结构备份 ✅
重点表数据备份 ✅
V0.3 KPI 快照 ✅
DDL 执行 ⏸ 未开始
```

**最终状态：** V0.4 实施前备份和环境检查完成，数据库保持原状，等待下一步指令。
