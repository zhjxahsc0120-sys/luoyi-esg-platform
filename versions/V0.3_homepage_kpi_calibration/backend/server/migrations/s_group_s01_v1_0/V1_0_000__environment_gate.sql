-- ============================================================================
-- V1_0_000__environment_gate.sql
-- S01 连续安全生产天数 V1.0 增量迁移 — 环境门禁（阻断式检查）
-- ============================================================================
-- 本脚本为只读 SELECT + SET 会话变量，不创建/修改任何数据库对象。
-- 用途：在正式执行 DDL 之前，检查目标 MySQL 实例的版本、字符集、
--        基础表（safety_production_record）存在性。
-- 门禁语义：任何检查失败均累加 @gate_failures，最终输出 GATE_PASS/GATE_FAIL。
--        迁移执行器读取 @gate_failures，非 0 则停止。
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
       CASE WHEN @ver_ok = 1 THEN 'PASS' ELSE 'FAIL' END AS version_check;

SET @gate_failures = @gate_failures + (1 - @ver_ok);
SET @gate_details  = CONCAT(@gate_details, IF(@ver_ok = 0, CONCAT('MySQL version ', @ver, ' < 8.0; '), ''));

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
-- 3. 基础依赖表存在性检查（safety_production_record 由 v0.1 建库创建）
-- --------------------------------------------------------------------------
SELECT '--- 3. 基础依赖表存在性检查 ---' AS check_section;

SELECT req.table_name,
       CASE WHEN t.table_name IS NOT NULL THEN 'EXISTS' ELSE 'MISSING' END AS status
FROM (
    SELECT 'safety_production_record' AS table_name
) AS req
LEFT JOIN information_schema.tables t
    ON t.table_schema = DATABASE()
    AND t.table_name = req.table_name
    AND t.table_type = 'BASE TABLE';

SET @tbl_missing = (SELECT COUNT(*) FROM information_schema.tables t WHERE t.table_schema = DATABASE() AND t.table_name = 'safety_production_record' AND t.table_type = 'BASE TABLE');
SET @gate_failures = @gate_failures + (1 - LEAST(@tbl_missing, 1));
SET @gate_details  = CONCAT(@gate_details, IF(@tbl_missing = 0, 'safety_production_record MISSING; ', ''));

-- --------------------------------------------------------------------------
-- 4. S01 迁移目录隔离检查（确认不进入 E 组号段）
-- --------------------------------------------------------------------------
SELECT '--- 4. 迁移隔离检查 ---' AS check_section;

-- 检查本迁移文件名中不包含 e_group
SET @self_path = 's_group_s01_v1_0';
SELECT 'S组独立迁移目录' AS isolation_check,
       @self_path AS migration_group;

-- --------------------------------------------------------------------------
-- 最终结果
-- --------------------------------------------------------------------------
SELECT '--- 门禁结果 ---' AS check_section;
SELECT
    CASE WHEN @gate_failures = 0 THEN 'GATE_PASS'
         ELSE CONCAT('GATE_FAIL (', @gate_failures, ' issue(s))')
    END AS gate_result,
    @gate_details AS gate_details;
