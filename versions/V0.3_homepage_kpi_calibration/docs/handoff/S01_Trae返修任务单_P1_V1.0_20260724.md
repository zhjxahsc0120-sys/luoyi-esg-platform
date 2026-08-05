# S01 Trae 返修任务单 · P1（二轮 · 门禁 105 · 不签收）

**日期：** 2026-07-24  
**状态：** **P1 签收 PASS（二轮 / round 2 · Cursor 直接修复）**  
**权威设计：** `_handoff/S01_连续安全生产天数设计说明_B方案_V1.0冻结稿_20260724.md`  
**原开工令：** `_handoff/S01_Trae实施任务单_P1_V1.0_20260724.md`  
**交付包参考：** `交付_S01_P1_Schema与数据登记包/`（已同步 round-2 修复 SQL）  
**验证证据：** `server/_tmp_s01_p1_round2_verify.txt`  

> **本单二轮阻断已闭环。** Cursor 直接修复：CSR/SIR.`id` AUTO_INCREMENT + skip `CONCAT` + seed 显式 `stage_key`；migrator exit 0，验收 SQL 全绿。  
> **P2 任务单：等用户指示后再开（本轮未开）。**

---

## 0. 一轮 vs 二轮（对照）

| 项 | 一轮 FAIL（已处理方向） | 二轮 FAIL（当前） |
|----|-------------------------|-------------------|
| 现象 | `V1_0_030`：`Unknown column 'project_id'` | `V1_0_030`：`Field 'id' doesn't have a default value` (1364) |
| Trae 已做 | 新增 `V1_0_015` 对旧表 ALTER；SIR/CSR 补字段；旧「主体工程」退出现役 | — |
| 二轮复验 | `V1_0_010` / `015` / `020` **SUCCESS**；SIR 新增列存在；「主体工程」`is_current=0` | `V1_0_030` **FAILED**；seed **整段回滚** |
| 库内实态（seed 后） | （一轮时 seed 未成功） | SPR 仍 `continuous_days=368` / `is_current=1`；**无** `DEMO-S01-20260724`；**无**「路基桥涵施工」current |
| 残余 | — | `V1_0_015` skip 路径 MySQL `+` 拼接；`ensure_s01_business_tables()` 仍建非冻结结构 |

**结论：** 一轮根因（缺 `project_id` 等冻结字段）已由 `V1_0_015` 路径解决；**P1 仍 FAIL**，不得签收、不得开 P2。

---

## 1. 二轮阻断根因（Cursor 复现）

前置：已清除 `V1_0_%` history 后重跑（清除 OK）。

```bash
cd server
python -m migrations.s_group_s01_v1_0.migrate_v1_0
```

结果（exit 1）：

- `V1_0_010` / `V1_0_015` / `V1_0_020`：**SUCCESS**
- **`V1_0_030` FAIL**：

```text
OperationalError: (1364, "Field 'id' doesn't have a default value")
```

根因链：

1. 现网 `construction_stage_record` 由 `ensure_s01_business_tables()` 创建：  
   `id` = **`BIGINT PRIMARY KEY` 无 `AUTO_INCREMENT`**（证据：`CSR.id EXTRA=''`）
2. `V1_0_030` 的 CSR `INSERT` **省略 `id`** → 1364
3. **下一阻断（修完 id 后必现）：** `stage_key` **NOT NULL** 且无默认值，seed 亦省略 → 须一并处理
4. Seed 事务回滚 → SPR 仍 368/`is_current=1`；无 DEMO 批次；无「路基桥涵施工」

部分进度（`V1_0_015` 已落库、不因 030 回滚）：

- SIR 冻结相关列已存在
- 「主体工程施工」已为 `is_current=0`（其余旧阶段行仍有多条 `is_current=1`，须由成功 seed 收敛）

---

## 2. 返修要求（仍属 P1，不做 P2）

### 2.1 必须：CSR.`id` → AUTO_INCREMENT（优先改 `V1_0_015`）

在 `V1_0_015__s01_legacy_table_enhancement.sql`（幂等）：

- 若 `construction_stage_record.id` 尚无 `AUTO_INCREMENT`，则 `MODIFY` 为带 `AUTO_INCREMENT` 的主键（与现有 PK 兼容，勿盲目再建主键）
- 保证二次/跳过执行安全（信息_schema 探测后再 ALTER）

### 2.2 必须：对齐 `V1_0_030` CSR INSERT 与旧表 NOT NULL 列

至少覆盖：

| 列 | 要求 |
|----|------|
| `id` | 依赖 AUTO_INCREMENT，或 INSERT 显式给值（优先 AI） |
| `stage_key` | seed **显式写入**，或在 `V1_0_015` 给可工作默认 / 可空策略（须可重复跑） |

核对旧表其余 NOT NULL、无默认值列，避免修完 id/stage_key 后再踩下一列。

### 2.3 必须：修复 `V1_0_015` skip 路径字符串拼接

Skip 分支约 **29** 处使用 MySQL **`+` 字符串拼接**（如 `'skip: ' + @col + ...`）。  
**改为 `CONCAT(...)`**，否则幂等重跑走到 skip 路径会炸。  
（本轮主 FAIL 在 030；此项为重跑门禁，必须修。）

### 2.4 可选说明（勿扩 P1 范围除非阻塞）

`ensure_s01_business_tables()` 仍会创建**非冻结稿** CSR/SIR 结构，空库调用可能再种「主体工程」等旧测数。  
**P1 本单：** 以迁移链在**已有旧表**环境下全绿 + 验收 SQL 为准；不必本单内大改运行时建表，除非不改就无法通过复验。P2 再单独立项。

### 2.5 非目标

- 不改 API / UI（P2/P3）
- 不改首页 KPI 卡片结构
- 不写入 `e_group`

---

## 3. 重跑步骤（修复后 Trae / Cursor 共用）

```sql
DELETE FROM esg_schema_migration_history WHERE version_key LIKE 'V1_0_%';
```

```bash
cd server
python -m migrations.s_group_s01_v1_0.migrate_v1_0
```

期望：migrator **exit 0**，全部 `V1_0_*` = SUCCESS（含 `V1_0_030`）。

---

## 4. 验收标准（与冻结稿一致 · 未变）

| 检查 | 期望 |
|------|------|
| demo + `is_current` SPR | `continuous_days=77`，`cycle_start_date=2026-05-08`，`statistics_as_of=2026-07-24` |
| 旧 368 行 | `is_current=0`（退出现役） |
| 确认批次 | 存在 `DEMO-S01-20260724` |
| 当前施工阶段 | **路基桥涵施工** 为 current |
| 旧「主体工程施工」 | **非** current |
| migrator | 全绿，无 FAIL |

将**实际查询结果**写入返修交付说明（不得只贴 SQL 文本）。Cursor 复跑 migrator + 自验后再签收。

---

## 5. 完成定义与门禁

- [x] `V1_0_015`：CSR.`id` AUTO_INCREMENT（幂等）+ `stage_key` 可插入策略就绪（seed 显式写）
- [x] `V1_0_030`：CSR INSERT 与旧表 NOT NULL 列对齐
- [x] `V1_0_015` skip：全部改为 `CONCAT`，幂等重跑 skip 路径不炸
- [x] 按 §3 清 history 后 migrator 全绿（exit 0）
- [x] 库内实态满足 §4（见 `server/_tmp_s01_p1_round2_verify.txt`）
- [x] 交付说明含复现命令 + 查询结果粘贴

**Gate：P1 已 PASS；P2 仍须用户指示后再开。**

---

## 6. Cursor round-2 签收记录（2026-07-24）

```text
migrate exit_code=0
V1_0_010/015/020/030 = SUCCESS
SPR current: days=77, cycle_start=2026-05-08, as_of=2026-07-24, data_nature=demo
SPR id=1: days=368, is_current=0
batch DEMO-S01-20260724: continuous_days=77
CSR: 路基桥涵施工 current; 主体工程施工 is_current=0
CSR.id EXTRA=auto_increment
OVERALL: PASS
```
