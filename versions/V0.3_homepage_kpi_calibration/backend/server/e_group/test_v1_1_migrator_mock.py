"""E组V1.1 执行器模拟测试（不连接数据库）。

覆盖：
- 门禁失败停止后续迁移
- 首次执行时 bootstrap 顺序（history表不存在 → 先建表 → 再记录）
- 同名对象冲突检测
"""

import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch, call

MIGRATION_DIR = Path(__file__).resolve().parent.parent / 'migrations' / 'e_group_e01_v1_1'


class _FakeConn:
    """Minimal fake connection with a shared sequential row queue.

    All cursors created by this connection share the same row queue.
    Rows are consumed in order across all cursors, which matches the
    behavior of a real MySQL connection where each query returns its
    own result set independently.
    """
    def __init__(self, cursor_rows=None):
        self._cursor_rows = cursor_rows or []
        self._global_idx = 0
        self.commit_count = 0
        self.rollback_count = 0

    def cursor(self):
        return _FakeCursor(self)

    def _next_row(self):
        if self._global_idx < len(self._cursor_rows):
            row = self._cursor_rows[self._global_idx]
            self._global_idx += 1
            return row
        return None

    def commit(self):
        self.commit_count += 1

    def rollback(self):
        self.rollback_count += 1


class _FakeCursor:
    """Minimal fake cursor that delegates row fetching to the parent _FakeConn."""

    def __init__(self, conn):
        self._conn = conn
        self.executed = []

    def execute(self, sql, params=None, multi=False):
        self.executed.append((sql, params, multi))
        if multi:
            return [None]
        return self

    def fetchone(self):
        return self._conn._next_row()

    def fetchall(self):
        remaining = []
        while True:
            row = self._conn._next_row()
            if row is None:
                break
            remaining.append(row)
        return remaining

    def close(self):
        pass


def _import_migrator():
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        'migrate_v1_1', MIGRATION_DIR / 'migrate_v1_1.py')
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class TestGateFailureBlocksMigration(unittest.TestCase):
    """门禁失败时应停止后续迁移。"""

    @patch('builtins.print')
    def test_gate_fail_stops_migration(self, mock_print):
        mod = _import_migrator()
        fake_conn = _FakeConn(cursor_rows=[
            (1,),  # table exists check (bootstrap)
            (5,),  # gate_failures = 5
        ])
        with patch.object(mod, '_get_connection', return_value=fake_conn):
            with patch.object(mod, '_execute_sql_file'):
                result = mod.run_migration(dry_run=False)
        self.assertEqual(result, 1)
        # Verify GATE_BLOCKED was printed
        printed = ' '.join(str(c) for c in mock_print.call_args_list)
        self.assertIn('GATE', printed)

    @patch('builtins.print')
    def test_gate_pass_allows_migration(self, mock_print):
        mod = _import_migrator()
        fake_conn = _FakeConn(cursor_rows=[
            (1,),  # table exists
            (0,),  # gate_failures = 0
        ])
        with patch.object(mod, '_get_connection', return_value=fake_conn):
            with patch.object(mod, '_execute_sql_file'):
                with patch.object(mod, '_get_last_successful_checksum', return_value=None):
                    with patch.object(mod, '_record_migration'):
                        result = mod.run_migration(dry_run=False)
        self.assertEqual(result, 0)
        printed = ' '.join(str(c) for c in mock_print.call_args_list)
        self.assertIn('PASSED', printed)


class TestBootstrapOrder(unittest.TestCase):
    """首次执行时必须先 bootstrap migration_history 表。"""

    def test_bootstrap_when_table_missing(self):
        mod = _import_migrator()
        fake_conn = _FakeConn(cursor_rows=[
            None,  # table does NOT exist
            (0,),   # gate pass
        ])
        with patch.object(mod, '_get_connection', return_value=fake_conn):
            with patch.object(mod, '_execute_sql_file') as mock_exec:
                with patch.object(mod, '_extract_gate_result', return_value='GATE_PASS'):
                    with patch.object(mod, '_record_migration'):
                        with patch.object(mod, '_get_last_successful_checksum', return_value=None):
                            mod.run_migration(dry_run=False)
        # _execute_sql_file should have been called at least once for bootstrap.
        # (gate SQL is executed via _extract_gate_result, not _execute_sql_file)
        # Additional calls are for the actual migration files (V1_1_005..V1_1_090).
        self.assertGreaterEqual(mock_exec.call_count, 1)
        # Verify the FIRST call was for the bootstrap file V1_1_001
        first_call = str(mock_exec.call_args_list[0])
        self.assertIn('V1_1_001', first_call)

    def test_skip_bootstrap_when_table_exists(self):
        mod = _import_migrator()
        fake_conn = _FakeConn(cursor_rows=[
            (1,),  # table exists
            (0,),  # gate pass
        ])
        with patch.object(mod, '_get_connection', return_value=fake_conn):
            with patch.object(mod, '_execute_sql_file') as mock_exec:
                with patch.object(mod, '_extract_gate_result', return_value='GATE_PASS'):
                    with patch.object(mod, '_record_migration'):
                        with patch.object(mod, '_get_last_successful_checksum', return_value=None):
                            mod.run_migration(dry_run=False)
        # Should NOT have called _execute_sql_file for bootstrap
        bootstrap_calls = [c for c in mock_exec.call_args_list
                          if 'V1_1_001' in str(c)]
        self.assertEqual(len(bootstrap_calls), 0)


class TestConflictingObjectDetection(unittest.TestCase):
    """同名对象冲突检测。"""

    def test_gate_sql_has_conflict_check_section(self):
        """门禁SQL应包含同名对象检查节。"""
        gate = (MIGRATION_DIR / 'V1_1_000__environment_gate.sql').read_text('utf-8')
        self.assertIn('同名对象定义差异', gate)
        self.assertIn('conflict_tables', gate)

    def test_gate_sql_accumulates_failures(self):
        """门禁SQL应使用 @gate_failures 累加器。"""
        gate = (MIGRATION_DIR / 'V1_1_000__environment_gate.sql').read_text('utf-8')
        self.assertIn('@gate_failures', gate)
        self.assertIn('GATE_PASS', gate)
        self.assertIn('GATE_FAIL', gate)

    def test_gate_sql_has_key_column_usage_join(self):
        """门禁主键查询必须使用 key_column_usage。"""
        gate = (MIGRATION_DIR / 'V1_1_000__environment_gate.sql').read_text('utf-8')
        self.assertIn('key_column_usage', gate)
        self.assertIn('table_constraints', gate)

    def test_migrator_has_bootstrap_function(self):
        """迁移器必须有 _bootstrap_migration_history_if_needed 函数。"""
        mod = _import_migrator()
        self.assertTrue(hasattr(mod, '_bootstrap_migration_history_if_needed'))

    def test_migrator_has_extract_gate_result(self):
        """迁移器必须有 _extract_gate_result 函数。"""
        mod = _import_migrator()
        self.assertTrue(hasattr(mod, '_extract_gate_result'))


if __name__ == '__main__':
    unittest.main()
