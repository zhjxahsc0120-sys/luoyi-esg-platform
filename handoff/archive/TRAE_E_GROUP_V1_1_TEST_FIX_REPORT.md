# E组V1.1 迁移测试修复完成报告

## 一、修改文件清单

| 文件 | 操作 | 说明 |
|---|---|---|
| `server/e_group/test_v1_1_migrator_mock.py` | 修改 | 修复 `_FakeConn`/`_FakeCursor` 的行队列共享机制，补全缺失的 mock patch |

## 二、完成内容

### 根因分析

`test_v1_1_migrator_mock.py` 中存在两个缺陷：

1. **`_FakeConn` 行队列设计错误**：原实现中每个 `cursor()` 调用都创建独立的 `_FakeCursor`，各 cursor 从各自的行队列副本的起始位置开始消费。这导致 `_bootstrap_migration_history_if_needed` 消费第一行 `(1,)`（表存在）后，`_extract_gate_result` 的新 cursor 也从第一行开始，再次拿到 `(1,)`（误判为 `@gate_failures=1`），门禁被错误地判定为 FAIL。正确行为应该是：一个连接上的所有 cursor 共享行队列，按调用顺序依次消费。

2. **`test_bootstrap_when_table_missing` 缺少 `_get_last_successful_checksum` 的 mock**：该测试未 patch `_get_last_successful_checksum`，导致迁移循环中实际调用该函数时，fake cursor 返回整数值 `(0,)`，随后 `row[0] = 0`（整数），在 `run_migration` 第 258 行执行 `last_checksum[:16]` 时触发 `TypeError: 'int' object is not subscriptable`。

### 修复措施

1. **重构 `_FakeConn` 为全局共享行队列模式**：`_FakeConn` 维护 `_global_idx` 计数器，`_next_row()` 方法按顺序分配行给任何 cursor。`_FakeCursor` 不再持有自己的行队列，而是委托给父 `_FakeConn` 的 `_next_row()`。

2. **为 `test_bootstrap_when_table_missing` 补充 `_get_last_successful_checksum` mock**：添加 `patch.object(mod, '_get_last_successful_checksum', return_value=None)`，使迁移循环中的 checksum 检查正确跳过。

## 三、验证结果

| 验证项 | 结果 | 说明 |
|---|---|---|
| `python -m compileall -q server/e_group` | PASS | 无编译错误 |
| `python -m unittest server.e_group.test_v1_1_migrator_mock` | PASS | 9 tests OK |
| `python -m unittest server.e_group.test_v1_1_migration_structure` | PASS | 33 tests OK |
| `python -m unittest server.e_group.test_v1_1_structure` | PASS | 91 tests OK |
| `python -m unittest server.e_group.test_v1_1_db_integration` | PASS | 20 tests OK (22 skipped, 需隔离测试库) |
| **全部 153 测试** | **PASS** | **131 active + 22 skipped = 153 OK** |

## 四、未修改项确认

- [x] 未修改禁止范围文件
- [x] 未修改任何 SQL 迁移文件
- [x] 未修改 `migrate_v1_1.py` 迁移执行器
- [x] 未修改 `enums.py`、`models.py`、`service_skeleton.py`
- [x] 未修改其他测试文件
- [x] 保留原有测试断言和覆盖范围

## 五、遗留问题 / 需 Codex 校核点

- `test_v1_1_structure.py` 使用相对导入（`from .enums import ...`），通过 `python -m unittest server.e_group.test_v1_1_structure` 可正常运行，但 `unittest discover` 从 `server/e_group` 目录运行时会报 `ImportError: attempted relative import with no known parent package`。这不影响 CI（应使用模块路径运行），但如果 CI 配置使用 `discover` 则需要添加 `__init__.py` 或调整发现方式。
