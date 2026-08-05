-- ============================================================================
-- V1_1_090__post_migration_verification.sql
-- E组公共闭环 & E01 V1.1 增量迁移 — 迁移后验证
-- ============================================================================
-- 本脚本为只读验证查询，不创建、修改或删除任何对象。
-- 验证内容：
--   1. 22 张新表是否存在
--   2. 13 个视图是否可查询（无报错）
--   3. esg_schema_migration_history 表是否存在
--   4. 关键外键是否存在
--   5. 循环外键 fk_e_case_current_history 是否存在
-- ============================================================================

SELECT '=== E组公共闭环 & E01 V1.1 迁移后验证 ===' AS verification_section;

-- 1. 表存在性验证
SELECT '--- 1. 新表存在性验证 ---' AS verification_section;

SELECT t.table_name,
       CASE WHEN t.table_name IS NOT NULL THEN 'OK' ELSE 'MISSING' END AS status,
       t.engine, t.table_collation
FROM (
    SELECT 'e01_monitor_point'            AS table_name UNION ALL
    SELECT 'e01_monitor_plan'             AS table_name UNION ALL
    SELECT 'e01_monitor_plan_item'        AS table_name UNION ALL
    SELECT 'e01_monitor_batch'            AS table_name UNION ALL
    SELECT 'e01_monitor_sample'           AS table_name UNION ALL
    SELECT 'e01_factor_definition'        AS table_name UNION ALL
    SELECT 'e01_standard_version'         AS table_name UNION ALL
    SELECT 'e01_standard_limit'           AS table_name UNION ALL
    SELECT 'e_closure_case'               AS table_name UNION ALL
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
    SELECT 'e01_legacy_record_mapping'    AS table_name UNION ALL
    SELECT 'esg_schema_migration_history' AS table_name
) expected
LEFT JOIN information_schema.tables t
  ON t.table_schema = DATABASE()
 AND t.table_name  = expected.table_name
 AND t.table_type  = 'BASE TABLE';

-- 2. 视图存在性验证
SELECT '--- 2. 视图存在性验证 ---' AS verification_section;

SELECT expected.view_name,
       CASE WHEN v.table_name IS NOT NULL THEN 'OK' ELSE 'MISSING' END AS status
FROM (
    SELECT 'v_e_case_effective_history_leaf'             AS view_name UNION ALL
    SELECT 'v_e_case_current_history'                    AS view_name UNION ALL
    SELECT 'v_e01_monthly_exceed_item'                   AS view_name UNION ALL
    SELECT 'v_e01_monthly_exceed_count'                  AS view_name UNION ALL
    SELECT 'v_e01_open_exceed_event'                      AS view_name UNION ALL
    SELECT 'v_e01_open_exceed_count'                      AS view_name UNION ALL
    SELECT 'v_e_case_status_inconsistency'                AS view_name UNION ALL
    SELECT 'v_e01_event_result_inconsistency'             AS view_name UNION ALL
    SELECT 'v_e01_retest_chain_inconsistency'             AS view_name UNION ALL
    SELECT 'v_e01_core_data_nature_inconsistency'       AS view_name UNION ALL
    SELECT 'v_e01_configuration_data_nature_inconsistency' AS view_name UNION ALL
    SELECT 'v_e01_time_quarter_inconsistency'             AS view_name UNION ALL
    SELECT 'v_e01_cross_month_retest_trace'               AS view_name
) expected
LEFT JOIN information_schema.views v
  ON v.table_schema = DATABASE()
 AND v.table_name  = expected.view_name;

-- 3. 视图可查询验证（带异常捕获）
SELECT '--- 3. 视图可查询验证 ---' AS verification_section;

-- 尝试查询各视图（仅检查不报错，不关注数据量）
SELECT 'v_e_case_effective_history_leaf' AS view_name, COUNT(*) AS row_count FROM v_e_case_effective_history_leaf;
SELECT 'v_e_case_current_history' AS view_name, COUNT(*) AS row_count FROM v_e_case_current_history;
SELECT 'v_e01_monthly_exceed_item' AS view_name, COUNT(*) AS row_count FROM v_e01_monthly_exceed_item;
SELECT 'v_e01_monthly_exceed_count' AS view_name, COUNT(*) AS row_count FROM v_e01_monthly_exceed_count;
SELECT 'v_e01_open_exceed_event' AS view_name, COUNT(*) AS row_count FROM v_e01_open_exceed_event;
SELECT 'v_e01_open_exceed_count' AS view_name, COUNT(*) AS row_count FROM v_e01_open_exceed_count;
SELECT 'v_e_case_status_inconsistency' AS view_name, COUNT(*) AS row_count FROM v_e_case_status_inconsistency;
SELECT 'v_e01_event_result_inconsistency' AS view_name, COUNT(*) AS row_count FROM v_e01_event_result_inconsistency;
SELECT 'v_e01_retest_chain_inconsistency' AS view_name, COUNT(*) AS row_count FROM v_e01_retest_chain_inconsistency;
SELECT 'v_e01_core_data_nature_inconsistency' AS view_name, COUNT(*) AS row_count FROM v_e01_core_data_nature_inconsistency;
SELECT 'v_e01_configuration_data_nature_inconsistency' AS view_name, COUNT(*) AS row_count FROM v_e01_configuration_data_nature_inconsistency;
SELECT 'v_e01_time_quarter_inconsistency' AS view_name, COUNT(*) AS row_count FROM v_e01_time_quarter_inconsistency;
SELECT 'v_e01_cross_month_retest_trace' AS view_name, COUNT(*) AS row_count FROM v_e01_cross_month_retest_trace;

-- 4. 关键外键验证
SELECT '--- 4. 关键外键验证 ---' AS verification_section;

SELECT expected.constraint_name, expected.table_name, expected.referenced_table_name,
       CASE WHEN rc.constraint_name IS NOT NULL THEN 'OK' ELSE 'MISSING' END AS status
FROM (
    SELECT 'fk_e_case_current_history' AS constraint_name, 'e_closure_case' AS table_name, 'e_case_status_history' AS referenced_table_name UNION ALL
    SELECT 'fk_e01_event_case', 'e01_exceed_event', 'e_closure_case' UNION ALL
    SELECT 'fk_e01_event_original', 'e01_exceed_event', 'e01_factor_result' UNION ALL
    SELECT 'fk_e01_plan_item_plan', 'e01_monitor_plan_item', 'e01_monitor_plan' UNION ALL
    SELECT 'fk_e01_sample_batch', 'e01_monitor_sample', 'e01_monitor_batch' UNION ALL
    SELECT 'fk_e01_retest_link_round', 'e01_retest_result_link', 'e01_retest_round' UNION ALL
    SELECT 'fk_e_case_rect_case', 'e_case_rectification_link', 'e_closure_case' UNION ALL
    SELECT 'fk_e_case_history_correction', 'e_case_status_history', 'e_case_status_history'
) expected
LEFT JOIN information_schema.referential_constraints rc
  ON rc.constraint_schema = DATABASE()
 AND rc.constraint_name = expected.constraint_name;

-- 5. CHECK 约束验证（MySQL 8.0.16+ 支持）
SELECT '--- 5. CHECK 约束抽样验证 ---' AS verification_section;

SELECT cc.constraint_name, tc.table_name, cc.check_clause
FROM information_schema.check_constraints cc
JOIN information_schema.table_constraints tc
  ON tc.constraint_schema = cc.constraint_schema
 AND tc.constraint_name = cc.constraint_name
 AND tc.constraint_type = 'CHECK'
WHERE cc.constraint_schema = DATABASE()
  AND tc.table_name IN (
      'e01_monitor_point', 'e_closure_case', 'e_case_status_history',
      'e01_exceed_event', 'e01_retest_round', 'e01_retest_result_link'
  )
ORDER BY tc.table_name, cc.constraint_name;

SELECT '=== 迁移后验证完毕。请确认所有状态为 OK。===' AS summary;
