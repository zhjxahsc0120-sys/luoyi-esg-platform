### 5.2 边界与活动事实分离（冻结）

| 对象 | 职责 |
|------|------|
| 活动/结果记录 | 保存活动事实、`source_code`、量、因子快照引用等；**不把 boundary_version 当作可批量改写的权威计入开关** |
| `carbon_accounting_boundary` | `boundary_version` + `source_code` + `in_boundary` + 生效说明 |
| 核算批次 / 结果快照 | `accounting_batch_id`、采用的 `boundary_version`、`statistics_as_of`、期间、性质、核验态、`is_current` |
| 切换边界 | **新批次 + 新快照**；禁止批量 UPDATE 历史活动以「切换版本」 |

允许活动行上冗余缓存「写入时边界」仅作审计，**权威过滤以批次所选边界配置为准**。