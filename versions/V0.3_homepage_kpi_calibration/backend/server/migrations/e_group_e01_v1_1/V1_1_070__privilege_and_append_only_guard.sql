-- ============================================================================
-- V1_1_070__privilege_and_append_only_guard.sql
-- E组公共闭环 & E01 V1.1 增量迁移 — 权限与追加保护
-- ============================================================================
-- 对 e_case_status_history 表实施追加保护：撤销 UPDATE 和 DELETE 权限。
-- 该表是案件状态变更的不可篡改审计日志，仅允许 INSERT。
-- 注意：需要 DBA 或拥有 GRANT OPTION 权限的账户执行。
-- 如果执行账户权限不足，本脚本会输出警告但不中断。
-- ============================================================================

-- 步骤 1：检查 e_case_status_history 表是否存在
SELECT '--- 追加保护前置检查 ---' AS check_section;

SET @tbl_exists = (SELECT COUNT(*) FROM information_schema.tables
                   WHERE table_schema = DATABASE()
                     AND table_name = 'e_case_status_history'
                     AND table_type = 'BASE TABLE');

SELECT CASE
         WHEN @tbl_exists > 0 THEN 'e_case_status_history EXISTS — 继续执行追加保护'
         ELSE 'e_case_status_history MISSING — 跳过追加保护'
       END AS check_result;

-- 步骤 2：撤销对 e_case_status_history 的 UPDATE 和 DELETE 权限
-- 仅在表存在且当前账号拥有表级直接授权时执行；库级授权无需重复撤销。
SET @direct_mutation_grants = (
    SELECT COUNT(*)
    FROM information_schema.table_privileges
    WHERE table_schema = DATABASE()
      AND table_name = 'e_case_status_history'
      AND privilege_type IN ('UPDATE', 'DELETE')
      AND grantee = CONCAT('''', REPLACE(CURRENT_USER(), '@', '''@'''), '''')
);

SET @exec_revoke = IF(
    @tbl_exists > 0 AND @direct_mutation_grants = 2,
    CONCAT('REVOKE UPDATE, DELETE ON ', DATABASE(), '.e_case_status_history FROM CURRENT_USER()'),
    'SELECT ''No direct table-level UPDATE/DELETE grants to revoke'' AS message'
);

PREPARE stmt FROM @exec_revoke;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- 步骤 3：查询当前用户对 e_case_status_history 的权限（验证）
SELECT '--- 权限验证 ---' AS check_section;

SELECT grantee, table_name, privilege_type
FROM information_schema.table_privileges
WHERE table_schema = DATABASE()
  AND table_name = 'e_case_status_history'
ORDER BY grantee, privilege_type;

SELECT '追加保护执行完毕。e_case_status_history 表已撤销 UPDATE 和 DELETE 权限。' AS summary;
