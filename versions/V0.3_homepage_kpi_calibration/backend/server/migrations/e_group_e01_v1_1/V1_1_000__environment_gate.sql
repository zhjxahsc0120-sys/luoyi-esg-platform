-- ============================================================================
-- V1_1_000__environment_gate.sql
-- E组公共闭环 & E01 V1.1 增量迁移 — 环境门禁（阻断式检查）
-- ============================================================================
-- 本脚本为只读 SELECT + SET 会话变量，不创建/修改任何数据库对象。
-- 用途：在正式执行 DDL 之前，检查目标 MySQL 实例的版本、字符集、
--        外部表/字段/类型/排序规则/引擎，同名对象定义差异。
-- 门禁语义：任何检查失败均累加 @gate_failures，最终输出 GATE_PASS/GATE_FAIL。
--        迁移执行器读取最后一行 gate_result 列，非 GATE_PASS 则停止。
-- 运行方式：由 migrate_v1_1.py 或任意 SQL 客户端执行。
-- ============================================================================

SET @gate_failures = 0;
SET @gate_details  = '';

-- --------------------------------------------------------------------------
-- 1. MySQL 版本检查
-- --------------------------------------------------------------------------
SELECT '--- 1. MySQL 版本检查 ---' AS check_section;

SET @ver = VERSION();
SET @ver_ok = CASE
  WHEN @ver REGEXP '^8\\.' OR @ver REGEXP '^9\\.' OR @ver REGEXP '^1[0-9]\\.'
  THEN 1 ELSE 0 END;

SELECT @ver AS mysql_version,
       @@sql_mode AS sql_mode,
       CASE WHEN @ver_ok = 1 THEN 'PASS' ELSE 'FAIL' END AS version_check;

SET @gate_failures = @gate_failures + (1 - @ver_ok);
SET @gate_details  = CONCAT(@gate_details, IF(@ver_ok = 0, CONCAT('MySQL version ', @ver, ' < 8.0.18; '), ''));

-- --------------------------------------------------------------------------
-- 2. 字符集与排序规则检查
-- --------------------------------------------------------------------------
SELECT '--- 2. 字符集检查 ---' AS check_section;

SET @cs_ok = CASE
  WHEN @@character_set_server = 'utf8mb4' AND @@collation_server = 'utf8mb4_0900_ai_ci'
  THEN 1 ELSE 0 END;

SELECT @@character_set_server AS server_charset,
       @@collation_server   AS server_collation,
       CASE WHEN @cs_ok = 1 THEN 'PASS'
            ELSE CONCAT('DIFFERENT: charset=', @@character_set_server,
                        ' collation=', @@collation_server)
       END AS charset_check;

SET @gate_failures = @gate_failures + (1 - @cs_ok);
SET @gate_details  = CONCAT(@gate_details, IF(@cs_ok = 0, CONCAT('charset=', @@character_set_server, '; '), ''));

-- --------------------------------------------------------------------------
-- 3. 外部依赖表存在性检查（5张，V1.1 不创建）
-- --------------------------------------------------------------------------
SELECT '--- 3. 外部依赖表存在性检查 ---' AS check_section;

SELECT req.table_name,
       CASE WHEN t.table_name IS NOT NULL THEN 'EXISTS' ELSE 'MISSING' END AS status
FROM (
    SELECT 'document_record'    AS table_name UNION ALL
    SELECT 'gis_feature'        AS table_name UNION ALL
    SELECT 'org_unit'           AS table_name UNION ALL
    SELECT 'file_asset'         AS table_name UNION ALL
    SELECT 'data_ingestion_job' AS table_name
) req
LEFT JOIN information_schema.tables t
  ON t.table_schema = DATABASE()
 AND t.table_name  = req.table_name
 AND t.table_type  = 'BASE TABLE';

SET @missing_ext = (SELECT COUNT(*)
    FROM (SELECT 'document_record' AS tbl UNION ALL SELECT 'gis_feature' UNION ALL
          SELECT 'org_unit' UNION ALL SELECT 'file_asset' UNION ALL
          SELECT 'data_ingestion_job') req
    LEFT JOIN information_schema.tables t
      ON t.table_schema = DATABASE() AND t.table_name = req.tbl AND t.table_type = 'BASE TABLE'
    WHERE t.table_name IS NULL);

SET @gate_failures = @gate_failures + @missing_ext;

-- --------------------------------------------------------------------------
-- 4. 外部表关键列存在性检查
-- --------------------------------------------------------------------------
SELECT '--- 4. 外部表关键列存在性检查 ---' AS check_section;

SELECT expected.tbl AS table_name,
       expected.col AS column_name,
       CASE WHEN actual.column_name IS NOT NULL THEN 'EXISTS' ELSE 'MISSING' END AS status
FROM (
    SELECT 'document_record' AS tbl, 'id' AS col UNION ALL
    SELECT 'gis_feature', 'id' UNION ALL
    SELECT 'org_unit', 'id' UNION ALL
    SELECT 'file_asset', 'id' UNION ALL
    SELECT 'data_ingestion_job', 'id'
) expected
LEFT JOIN information_schema.columns actual
  ON actual.table_schema = DATABASE()
 AND actual.table_name = expected.tbl
 AND actual.column_name = expected.col
ORDER BY expected.tbl, expected.col;

SET @missing_cols = (SELECT COUNT(*)
    FROM (SELECT 'document_record' AS tbl, 'id' AS col UNION ALL
          SELECT 'gis_feature', 'id' UNION ALL SELECT 'org_unit', 'id' UNION ALL
          SELECT 'file_asset', 'id' UNION ALL SELECT 'data_ingestion_job', 'id') e
    LEFT JOIN information_schema.columns a
      ON a.table_schema = DATABASE() AND a.table_name = e.tbl AND a.column_name = e.col
    WHERE a.column_name IS NULL);

SET @gate_failures = @gate_failures + @missing_cols;

-- --------------------------------------------------------------------------
-- 5. 外部表排序规则检查
-- --------------------------------------------------------------------------
SELECT '--- 5. 外部表排序规则检查 ---' AS check_section;

SELECT t.table_name,
       CASE
         WHEN t.table_name IS NULL THEN 'TABLE MISSING'
         WHEN t.table_collation = 'utf8mb4_0900_ai_ci' THEN 'PASS'
         ELSE CONCAT('DIFFERENT: ', t.table_collation)
       END AS collation_check
FROM (
    SELECT 'document_record'    AS table_name UNION ALL
    SELECT 'gis_feature'        AS table_name UNION ALL
    SELECT 'org_unit'           AS table_name UNION ALL
    SELECT 'file_asset'         AS table_name UNION ALL
    SELECT 'data_ingestion_job' AS table_name
) req
LEFT JOIN information_schema.tables t
  ON t.table_schema = DATABASE()
 AND t.table_name  = req.table_name
 AND t.table_type  = 'BASE TABLE';

SET @bad_coll = (SELECT COUNT(*)
    FROM (SELECT 'document_record' AS table_name UNION ALL
          SELECT 'gis_feature' UNION ALL SELECT 'org_unit' UNION ALL
          SELECT 'file_asset' UNION ALL SELECT 'data_ingestion_job') r
    LEFT JOIN information_schema.tables t
      ON t.table_schema = DATABASE() AND t.table_name = r.table_name
      AND t.table_type = 'BASE TABLE'
    WHERE t.table_name IS NOT NULL AND t.table_collation != 'utf8mb4_0900_ai_ci');

SET @gate_failures = @gate_failures + @bad_coll;

-- --------------------------------------------------------------------------
-- 6. 外部表主键列类型检查（正确关联 key_column_usage）
-- --------------------------------------------------------------------------
SELECT '--- 6. 外部表主键列类型检查 ---' AS check_section;

SELECT kcu.table_name,
       kcu.column_name,
       col.data_type,
       col.column_type,
       col.character_set_name,
       col.collation_name
FROM information_schema.table_constraints tc
JOIN information_schema.key_column_usage kcu
  ON kcu.constraint_schema = tc.constraint_schema
 AND kcu.table_name = tc.table_name
 AND kcu.constraint_name = tc.constraint_name
JOIN information_schema.columns col
  ON col.table_schema = kcu.table_schema
 AND col.table_name = kcu.table_name
 AND col.column_name = kcu.column_name
WHERE tc.table_schema = DATABASE()
  AND tc.constraint_type = 'PRIMARY KEY'
  AND tc.table_name IN ('document_record','gis_feature','org_unit','file_asset','data_ingestion_job')
ORDER BY tc.table_name;

-- --------------------------------------------------------------------------
-- 7. 外部表引擎检查
-- --------------------------------------------------------------------------
SELECT '--- 7. 外部表引擎检查 ---' AS check_section;

SELECT t.table_name,
       t.engine,
       CASE WHEN t.engine = 'InnoDB' THEN 'PASS'
            ELSE CONCAT('DIFFERENT: ', t.engine)
       END AS engine_check
FROM information_schema.tables t
WHERE t.table_schema = DATABASE()
  AND t.table_type = 'BASE TABLE'
  AND t.table_name IN ('document_record','gis_feature','org_unit','file_asset','data_ingestion_job')
ORDER BY t.table_name;

SET @bad_engine = (SELECT COUNT(*)
    FROM information_schema.tables t
    WHERE t.table_schema = DATABASE()
      AND t.table_type = 'BASE TABLE'
      AND t.table_name IN ('document_record','gis_feature','org_unit','file_asset','data_ingestion_job')
      AND t.engine != 'InnoDB');

SET @gate_failures = @gate_failures + @bad_engine;

-- --------------------------------------------------------------------------
-- 8. 同名对象定义差异比较
--    注意：esg_schema_migration_history 不在检查范围内，因为它由
--    bootstrap 流程（V1_1_001）在门禁之前创建，总是已存在的。
--    完整定义比较（字段、索引、外键、CHECK约束）未实现，仅检查
--    存在性和引擎/排序规则差异。
-- --------------------------------------------------------------------------
SELECT '--- 8. 同名对象定义差异比较 ---' AS check_section;

SELECT n.table_name AS new_table,
       CASE WHEN e.table_name IS NULL THEN 'CLEAN' ELSE 'EXISTS — CHECK BELOW' END AS status
FROM (
    SELECT 'e01_monitor_point'            AS table_name UNION ALL
    SELECT 'e01_monitor_plan'             AS table_name UNION ALL
    SELECT 'e01_monitor_plan_item'        AS table_name UNION ALL
    SELECT 'e01_monitor_batch'            AS table_name UNION ALL
    SELECT 'e01_monitor_sample'           AS table_name UNION ALL
    SELECT 'e01_factor_definition'        AS table_name UNION ALL
    SELECT 'e01_standard_version'          AS table_name UNION ALL
    SELECT 'e01_standard_limit'            AS table_name UNION ALL
    SELECT 'e01_factor_result'             AS table_name UNION ALL
    SELECT 'e_closure_case'                AS table_name UNION ALL
    SELECT 'e_case_status_history'        AS table_name UNION ALL
    SELECT 'e_case_party'                 AS table_name UNION ALL
    SELECT 'e_case_evidence'              AS table_name UNION ALL
    SELECT 'e_case_relation'              AS table_name UNION ALL
    SELECT 'e_rectification_task'         AS table_name UNION ALL
    SELECT 'e_case_rectification_link'    AS table_name UNION ALL
    SELECT 'e01_exceed_event'             AS table_name UNION ALL
    SELECT 'e01_rectification_round'       AS table_name UNION ALL
    SELECT 'e01_retest_round'             AS table_name UNION ALL
    SELECT 'e01_retest_result_link'       AS table_name UNION ALL
    SELECT 'e01_legacy_record_mapping'    AS table_name
) n
LEFT JOIN information_schema.tables e
  ON e.table_schema = DATABASE()
 AND e.table_name  = n.table_name
 AND e.table_type  = 'BASE TABLE'
ORDER BY n.table_name;

-- 已存在同名表的引擎和排序规则差异
SELECT t.table_name,
       t.engine AS existing_engine,
       CASE WHEN t.engine = 'InnoDB' THEN 'PASS' ELSE 'DIFFERENT' END AS engine_check,
       t.table_collation AS existing_collation,
       CASE WHEN t.table_collation = 'utf8mb4_0900_ai_ci' THEN 'PASS'
            ELSE 'DIFFERENT' END AS collation_check
FROM information_schema.tables t
WHERE t.table_schema = DATABASE()
  AND t.table_type = 'BASE TABLE'
  AND t.table_name IN (
    'e01_monitor_point','e01_monitor_plan','e01_monitor_plan_item',
    'e01_monitor_batch','e01_monitor_sample','e01_factor_definition',
    'e01_standard_version','e01_standard_limit','e01_factor_result',
    'e_closure_case','e_case_status_history','e_case_party',
    'e_case_evidence','e_case_relation','e_rectification_task',
    'e_case_rectification_link','e01_exceed_event','e01_rectification_round',
    'e01_retest_round','e01_retest_result_link','e01_legacy_record_mapping'
)
ORDER BY t.table_name;

SET @has_v11_success = (SELECT COUNT(*)
    FROM esg_schema_migration_history
    WHERE status = 'SUCCESS'
      AND version_key REGEXP '^V1_1_(005|010|012|015|020|030|035|040|050|060|070|080|090)$');

SET @conflict_tables = IF(@has_v11_success > 0, 0, (SELECT COUNT(*)
    FROM information_schema.tables t
    WHERE t.table_schema = DATABASE()
      AND t.table_type = 'BASE TABLE'
      AND t.table_name IN (
        'e01_monitor_point','e01_monitor_plan','e01_monitor_plan_item',
        'e01_monitor_batch','e01_monitor_sample','e01_factor_definition',
        'e01_standard_version','e01_standard_limit','e01_factor_result',
        'e_closure_case','e_case_status_history','e_case_party',
        'e_case_evidence','e_case_relation','e_rectification_task',
        'e_case_rectification_link','e01_exceed_event','e01_rectification_round',
        'e01_retest_round','e01_retest_result_link','e01_legacy_record_mapping'
      )));

SET @gate_failures = @gate_failures + @conflict_tables;

-- --------------------------------------------------------------------------
-- 门禁结论
-- --------------------------------------------------------------------------
SELECT '--- 门禁结论 ---' AS check_section;

SELECT
  CASE WHEN @gate_failures = 0
       THEN 'GATE_PASS'
       ELSE CONCAT('GATE_FAIL (', @gate_failures, ' issue(s))')
  END AS gate_result,
  CASE WHEN @gate_failures = 0
       THEN 'All checks passed. Safe to proceed with migration.'
       ELSE IFNULL(@gate_details, 'See details above.')
  END AS gate_details;
