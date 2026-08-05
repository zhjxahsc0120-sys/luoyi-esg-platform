"""E组V1.1 迁移文件结构与迁移器单元测试。

本文件不连接数据库，真实读取 SQL 迁移文件并检查：
- SQL 文件发现顺序（migrate_v1_1.py 的正则与排序）
- CREATE TABLE 语句数量和对象名称
- CREATE VIEW 语句数量和视图名称
- CONSTRAINT（命名约束）数量
- UNIQUE KEY / KEY（索引）数量
- 门禁查询结构（V1_1_000 关键检查节）
"""

import os
import re
import unittest
from pathlib import Path


# 迁移目录的绝对路径
MIGRATION_DIR = Path(__file__).resolve().parent.parent / 'migrations' / 'e_group_e01_v1_1'

# --- SQL 解析辅助 ---

_RE_CREATE_TABLE = re.compile(
    r'CREATE\s+TABLE\s+IF\s+NOT\s+EXISTS\s+(\w+)',
    re.IGNORECASE
)
_RE_CREATE_VIEW = re.compile(
    r'CREATE\s+OR\s+REPLACE\s+VIEW\s+(\w+)',
    re.IGNORECASE
)
_RE_CONSTRAINT = re.compile(
    r'CONSTRAINT\s+(\w+)\s+',
    re.IGNORECASE
)
_RE_UNIQUE_KEY = re.compile(
    r'UNIQUE\s+KEY\s+(\w+)',
    re.IGNORECASE
)
_RE_KEY = re.compile(
    r'^\s+KEY\s+(\w+)',
    re.IGNORECASE | re.MULTILINE
)
_RE_CHECK_SECTION = re.compile(
    r"SELECT\s+'---\s*(.+?)\s*---'",
    re.IGNORECASE
)


def _read_sql(path: Path) -> str:
    return path.read_text(encoding='utf-8')


def _extract_create_tables(sql: str) -> list[str]:
    return _RE_CREATE_TABLE.findall(sql)


def _extract_create_views(sql: str) -> list[str]:
    return _RE_CREATE_VIEW.findall(sql)


def _extract_constraints(sql: str) -> list[str]:
    return _RE_CONSTRAINT.findall(sql)


def _extract_unique_keys(sql: str) -> list[str]:
    return _RE_UNIQUE_KEY.findall(sql)


def _extract_keys(sql: str) -> list[str]:
    return _RE_KEY.findall(sql)


def _extract_gate_sections(sql: str) -> list[str]:
    return _RE_CHECK_SECTION.findall(sql)


def _discover_sql_files(directory: Path) -> list[Path]:
    """简单发现 .sql 文件，按文件名排序。"""
    files = sorted(p for p in directory.iterdir()
                  if p.is_file() and p.suffix.lower() == '.sql')
    return files


class TestMigratorRegexAndDiscovery(unittest.TestCase):
    """R1: 测试 migrate_v1_1.py 的正则能正确发现并排序 SQL 文件。"""

    def _import_and_test(self):
        """动态导入迁移器并测试文件发现。"""
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            'migrate_v1_1', MIGRATION_DIR / 'migrate_v1_1.py')
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return mod

    def test_discover_all_sql_files(self):
        """_discover_sql_files 应发现全部 SQL 文件。"""
        mod = self._import_and_test()
        files = mod._discover_sql_files(MIGRATION_DIR)
        self.assertGreaterEqual(len(files), 12)

    def test_discover_order_starts_with_gate(self):
        """第一个文件应为 V1_1_000__environment_gate.sql。"""
        mod = self._import_and_test()
        files = mod._discover_sql_files(MIGRATION_DIR)
        self.assertEqual(files[0].name, 'V1_1_000__environment_gate.sql')

    def test_discover_order_ends_with_verification(self):
        """最后一个文件应为 V1_1_090__post_migration_verification.sql。"""
        mod = self._import_and_test()
        files = mod._discover_sql_files(MIGRATION_DIR)
        self.assertEqual(files[-1].name, 'V1_1_090__post_migration_verification.sql')

    def test_full_order_is_correct(self):
        """完整文件发现顺序应与版本号一致。"""
        mod = self._import_and_test()
        files = mod._discover_sql_files(MIGRATION_DIR)
        expected_order = [
            'V1_1_000__environment_gate.sql',
            'V1_1_001__migration_history_bootstrap.sql',
            'V1_1_010__e01_config_and_monitor_tables.sql',
            'V1_1_012__e01_factor_result.sql',
            'V1_1_015__project_context_and_frequency.sql',
            'V1_1_020__closure_case_tables.sql',
            'V1_1_030__e01_event_retest_tables.sql',
            'V1_1_035__professional_demo_seed.sql',
            'V1_1_036__gis_link_seed.sql',
            'V1_1_037__construction_time_consistency.sql',
            'V1_1_038__e01_demo_coordinate_alignment.sql',
            'V1_1_039__e01_open_overview_demo_enrichment.sql',
            'V1_1_040__external_fk_and_circular_fk_guarded.sql',
            'V1_1_041__e01_demo_trend_series.sql',
            'V1_1_042__e01_water_point_near_source_zone.sql',
            'V1_1_043__e02_env_issue_fields.sql',
            'V1_1_044__e02_demo_seed.sql',
            'V1_1_045__e02_gis_body_relink.sql',
            'V1_1_046__e03_schema_fields.sql',
            'V1_1_047__e03_demo_seed.sql',
            'V1_1_048__e04_schema_boundary.sql',
            'V1_1_049__e04_demo_seed.sql',
            'V1_1_050__history_and_kpi_views.sql',
            'V1_1_051__e04_may_jul_boundary_rebuild.sql',
            'V1_1_052__e04_cultural_relic_demo.sql',
            'V1_1_060__consistency_views.sql',
            'V1_1_070__privilege_and_append_only_guard.sql',
            'V1_1_080__shadow_reconciliation_views.sql',
            'V1_1_090__post_migration_verification.sql',
        ]
        actual_names = [f.name for f in files]
        self.assertEqual(actual_names, expected_order)

    def test_parse_version_key(self):
        """_parse_version_key 应正确解析文件名。"""
        mod = self._import_and_test()
        self.assertEqual(mod._parse_version_key('V1_1_000__gate.sql'), (1, 1, 0))
        self.assertEqual(mod._parse_version_key('V1_1_010__e01_config.sql'), (1, 1, 10))
        self.assertEqual(mod._parse_version_key('V1_1_090__verify.sql'), (1, 1, 90))

    def test_parse_version_key_rejects_non_matching(self):
        """不匹配的文件名应返回 None。"""
        mod = self._import_and_test()
        self.assertIsNone(mod._parse_version_key('readme.txt'))
        self.assertIsNone(mod._parse_version_key('V1_1__no_patch.sql'))
        self.assertIsNone(mod._parse_version_key('migrate_v1_1.py'))

    def test_extract_version_key(self):
        """_extract_version_key 应返回 V1_1_XXX 格式。"""
        mod = self._import_and_test()
        self.assertEqual(
            mod._extract_version_key('V1_1_010__e01_config.sql'),
            'V1_1_010')
        self.assertEqual(
            mod._extract_version_key('V1_1_000__environment_gate.sql'),
            'V1_1_000')

    def test_extract_version_key_raises_on_bad_name(self):
        """不匹配的文件名应抛 ValueError。"""
        mod = self._import_and_test()
        with self.assertRaises(ValueError):
            mod._extract_version_key('readme.txt')


class TestSQLTableCount(unittest.TestCase):
    """R4: 检查 DDL 文件中的 CREATE TABLE 数量和名称。"""

    def setUp(self):
        self.all_sql_files = _discover_sql_files(MIGRATION_DIR)
        self.all_sql = '\n'.join(_read_sql(f) for f in self.all_sql_files)

    def test_total_create_table_count(self):
        """全部 SQL 文件中应有 32 个 CREATE TABLE（含 E04 边界/批次/因子快照 + 文物保护演示表）。"""
        tables = _extract_create_tables(self.all_sql)
        # 去重
        unique_tables = list(dict.fromkeys(tables))
        self.assertEqual(len(unique_tables), 32,
                         f'Expected 32 CREATE TABLE, got {len(unique_tables)}: {unique_tables}')

    def test_all_31_table_names_present(self):
        """确认全部建表名称存在（含 biz_cultural_relic_object）。"""
        tables = set(_extract_create_tables(self.all_sql))
        expected = {
            'esg_schema_migration_history',
            'e01_monitor_point', 'e01_monitor_plan', 'e01_monitor_plan_item',
            'e01_monitor_batch', 'e01_monitor_sample',
            'e01_factor_definition', 'e01_standard_version', 'e01_standard_limit',
            'e01_factor_result',
            'project_section', 'project_phase_period', 'project_engineering_object',
            'engineering_object_phase', 'monitor_point_object_relation',
            'monitor_frequency_rule',
            'e_closure_case', 'e_case_status_history',
            'e_case_party', 'e_case_evidence', 'e_case_relation',
            'e_rectification_task', 'e_case_rectification_link',
            'e01_exceed_event', 'e01_rectification_round',
            'e01_retest_round', 'e01_retest_result_link',
            'e01_legacy_record_mapping',
            'carbon_accounting_boundary', 'carbon_accounting_batch',
            'carbon_emission_factor_snapshot',
            'biz_cultural_relic_object',
        }
        self.assertEqual(tables, expected,
                         f'Missing: {expected - tables}, Extra: {tables - expected}')

    def test_e01_factor_result_has_ddl(self):
        """e01_factor_result 必须有 CREATE TABLE DDL（不再是外部依赖表）。"""
        tables = _extract_create_tables(self.all_sql)
        self.assertIn('e01_factor_result', tables)


class TestSQLViewCount(unittest.TestCase):
    """R4: 检查 CREATE VIEW 数量和名称。"""

    def setUp(self):
        self.all_sql_files = _discover_sql_files(MIGRATION_DIR)
        self.all_sql = '\n'.join(_read_sql(f) for f in self.all_sql_files)

    def test_total_view_count(self):
        """应有 13 个 CREATE VIEW。"""
        views = _extract_create_views(self.all_sql)
        unique_views = list(dict.fromkeys(views))
        self.assertEqual(len(unique_views), 13,
                         f'Expected 13 views, got {len(unique_views)}: {unique_views}')

    def test_view_names_set(self):
        """确认 13 个视图名称。"""
        views = set(_extract_create_views(self.all_sql))
        # 6 KPI/history + 7 consistency
        expected = {
            'v_e_case_effective_history_leaf',
            'v_e_case_current_history',
            'v_e01_monthly_exceed_item',
            'v_e01_monthly_exceed_count',
            'v_e01_open_exceed_event',
            'v_e01_open_exceed_count',
            'v_e_case_status_inconsistency',
            'v_e01_event_result_inconsistency',
            'v_e01_retest_chain_inconsistency',
            'v_e01_core_data_nature_inconsistency',
            'v_e01_configuration_data_nature_inconsistency',
            'v_e01_time_quarter_inconsistency',
            'v_e01_cross_month_retest_trace',
        }
        self.assertEqual(views, expected,
                         f'Missing: {expected - views}, Extra: {views - expected}')


class TestSQLConstraintCount(unittest.TestCase):
    """R4: 检查命名约束数量。"""

    def setUp(self):
        self.all_sql_files = _discover_sql_files(MIGRATION_DIR)
        self.all_sql = '\n'.join(_read_sql(f) for f in self.all_sql_files)

    def test_total_named_constraints(self):
        """应有超过 100 个命名约束（FK + CK）。"""
        constraints = _extract_constraints(self.all_sql)
        # 排除 PRIMARY KEY（它也被 CONSTRAINT 匹配到，但不是命名约束）
        named = [c for c in constraints if not c.upper().startswith('PRIMARY')]
        self.assertGreater(len(named), 100,
                           f'Expected >100 named constraints, got {len(named)}')

    def test_fk_constraints_exist(self):
        """应有外键约束（fk_ 前缀）。"""
        constraints = _extract_constraints(self.all_sql)
        fk_constraints = [c for c in constraints if c.lower().startswith('fk_')]
        self.assertGreater(len(fk_constraints), 20,
                           f'Expected >20 FK constraints, got {len(fk_constraints)}')

    def test_ck_constraints_exist(self):
        """应有 CHECK 约束（ck_ 前缀）。"""
        constraints = _extract_constraints(self.all_sql)
        ck_constraints = [c for c in constraints if c.lower().startswith('ck_')]
        self.assertGreater(len(ck_constraints), 60,
                           f'Expected >60 CHECK constraints, got {len(ck_constraints)}')


class TestSQLIndexCount(unittest.TestCase):
    """R4: 检查索引数量。"""

    def setUp(self):
        self.all_sql_files = _discover_sql_files(MIGRATION_DIR)
        self.all_sql = '\n'.join(_read_sql(f) for f in self.all_sql_files)

    def test_unique_keys_exist(self):
        """应有 UNIQUE KEY 索引。"""
        ukeys = _extract_unique_keys(self.all_sql)
        self.assertGreater(len(ukeys), 15,
                           f'Expected >15 UNIQUE KEY, got {len(ukeys)}')

    def test_non_unique_keys_exist(self):
        """应有普通 KEY 索引。"""
        keys = _extract_keys(self.all_sql)
        self.assertGreater(len(keys), 5,
                           f'Expected >5 KEY indexes, got {len(keys)}')


class TestSQLFileDiscoveryOrder(unittest.TestCase):
    """R4: 检查 SQL 文件本身的发现和顺序。"""

    def test_sql_files_exist_on_disk(self):
        """确认 16 个 SQL 文件存在于磁盘。"""
        expected = [
            'V1_1_000__environment_gate.sql',
            'V1_1_001__migration_history_bootstrap.sql',
            'V1_1_010__e01_config_and_monitor_tables.sql',
            'V1_1_012__e01_factor_result.sql',
            'V1_1_015__project_context_and_frequency.sql',
            'V1_1_020__closure_case_tables.sql',
            'V1_1_030__e01_event_retest_tables.sql',
            'V1_1_035__professional_demo_seed.sql',
            'V1_1_036__gis_link_seed.sql',
            'V1_1_037__construction_time_consistency.sql',
            'V1_1_038__e01_demo_coordinate_alignment.sql',
            'V1_1_039__e01_open_overview_demo_enrichment.sql',
            'V1_1_040__external_fk_and_circular_fk_guarded.sql',
            'V1_1_041__e01_demo_trend_series.sql',
            'V1_1_042__e01_water_point_near_source_zone.sql',
            'V1_1_043__e02_env_issue_fields.sql',
            'V1_1_044__e02_demo_seed.sql',
            'V1_1_045__e02_gis_body_relink.sql',
            'V1_1_046__e03_schema_fields.sql',
            'V1_1_047__e03_demo_seed.sql',
            'V1_1_048__e04_schema_boundary.sql',
            'V1_1_049__e04_demo_seed.sql',
            'V1_1_050__history_and_kpi_views.sql',
            'V1_1_051__e04_may_jul_boundary_rebuild.sql',
            'V1_1_052__e04_cultural_relic_demo.sql',
            'V1_1_060__consistency_views.sql',
            'V1_1_070__privilege_and_append_only_guard.sql',
            'V1_1_080__shadow_reconciliation_views.sql',
            'V1_1_090__post_migration_verification.sql',
        ]
        for name in expected:
            path = MIGRATION_DIR / name
            self.assertTrue(path.is_file(), f'SQL file missing: {name}')

    def test_no_extra_sql_files(self):
        """不应有超出预期的 SQL 文件。"""
        all_sql = [p.name for p in _discover_sql_files(MIGRATION_DIR)]
        expected = [
            'V1_1_000__environment_gate.sql',
            'V1_1_001__migration_history_bootstrap.sql',
            'V1_1_010__e01_config_and_monitor_tables.sql',
            'V1_1_012__e01_factor_result.sql',
            'V1_1_015__project_context_and_frequency.sql',
            'V1_1_020__closure_case_tables.sql',
            'V1_1_030__e01_event_retest_tables.sql',
            'V1_1_035__professional_demo_seed.sql',
            'V1_1_036__gis_link_seed.sql',
            'V1_1_037__construction_time_consistency.sql',
            'V1_1_038__e01_demo_coordinate_alignment.sql',
            'V1_1_039__e01_open_overview_demo_enrichment.sql',
            'V1_1_040__external_fk_and_circular_fk_guarded.sql',
            'V1_1_041__e01_demo_trend_series.sql',
            'V1_1_042__e01_water_point_near_source_zone.sql',
            'V1_1_043__e02_env_issue_fields.sql',
            'V1_1_044__e02_demo_seed.sql',
            'V1_1_045__e02_gis_body_relink.sql',
            'V1_1_046__e03_schema_fields.sql',
            'V1_1_047__e03_demo_seed.sql',
            'V1_1_048__e04_schema_boundary.sql',
            'V1_1_049__e04_demo_seed.sql',
            'V1_1_050__history_and_kpi_views.sql',
            'V1_1_051__e04_may_jul_boundary_rebuild.sql',
            'V1_1_052__e04_cultural_relic_demo.sql',
            'V1_1_060__consistency_views.sql',
            'V1_1_070__privilege_and_append_only_guard.sql',
            'V1_1_080__shadow_reconciliation_views.sql',
            'V1_1_090__post_migration_verification.sql',
        ]
        self.assertEqual(sorted(all_sql), sorted(expected),
                         f'Extra files: {set(all_sql) - set(expected)}')


class TestGateQueryStructure(unittest.TestCase):
    """R4: 检查 V1_1_000 门禁查询的关键结构。"""

    def setUp(self):
        gate_sql = _read_sql(MIGRATION_DIR / 'V1_1_000__environment_gate.sql')
        self.sections = _extract_gate_sections(gate_sql)
        self.full_sql = gate_sql

    def test_gate_has_version_check(self):
        """门禁应有版本检查节。"""
        self.assertTrue(any('MySQL 版本' in s for s in self.sections))

    def test_gate_has_charset_check(self):
        """门禁应有字符集检查节。"""
        self.assertTrue(any('字符集' in s for s in self.sections))

    def test_gate_has_external_table_check(self):
        """门禁应有外部依赖表检查节。"""
        self.assertTrue(any('外部依赖表' in s for s in self.sections))

    def test_gate_has_same_name_object_check(self):
        """门禁应有同名对象定义差异比较节。"""
        self.assertTrue(any('同名对象' in s for s in self.sections))

    def test_gate_has_column_check(self):
        """门禁应有列存在性检查节。"""
        self.assertTrue(any('列' in s for s in self.sections))

    def test_gate_has_collation_check(self):
        """门禁应有字符集与排序规则检查节。"""
        self.assertTrue(any('排序规则' in s for s in self.sections))

    def test_gate_has_pk_type_check(self):
        """门禁应有主键列类型检查节。"""
        self.assertTrue(any('主键' in s and '类型' in s for s in self.sections))

    def test_gate_has_engine_check(self):
        """门禁应有引擎检查节。"""
        self.assertTrue(any('引擎' in s for s in self.sections))

    def test_gate_no_duplicate_alias_c(self):
        """门禁不应有别名 c 冲突（修复验证）。"""
        # 确保没有将 c 同时用于 information_schema.columns 和子查询
        # 原始 bug: LEFT JOIN (SELECT COUNT(*) AS cnt ...) c ON TRUE
        self.assertNotIn(') c ON TRUE', self.full_sql)

    def test_gate_does_not_list_e01_factor_result_as_external(self):
        """e01_factor_result 应在新表预检中（V1.1 新建），不在外部依赖表中。"""
        # e01_factor_result 在新表列表中
        self.assertIn('e01_factor_result', self.full_sql)
        # 外部依赖表只有 5 个
        external_tables = [
            'document_record', 'gis_feature', 'org_unit',
            'file_asset', 'data_ingestion_job',
        ]
        for t in external_tables:
            self.assertIn(t, self.full_sql)
        # e01_factor_result 不应出现在外部依赖表的 UNION 中
        # 找到外部依赖表的 UNION 块
        external_block_match = re.search(
            r"SELECT '--- 3\. 外部依赖表存在性检查.*?\) req\b",
            self.full_sql, re.DOTALL
        )
        self.assertIsNotNone(external_block_match)
        external_block = external_block_match.group(0)
        self.assertNotIn('e01_factor_result', external_block)

    def test_gate_external_list_has_exactly_5_tables(self):
        """外部依赖表应恰好 5 个。"""
        external_block_match = re.search(
            r"SELECT '--- 3\. 外部依赖表存在性检查.*?\) req\b",
            self.full_sql, re.DOTALL
        )
        self.assertIsNotNone(external_block_match)
        external_block = external_block_match.group(0)
        count = external_block.count("AS table_name")
        self.assertEqual(count, 5)


if __name__ == '__main__':
    unittest.main()
