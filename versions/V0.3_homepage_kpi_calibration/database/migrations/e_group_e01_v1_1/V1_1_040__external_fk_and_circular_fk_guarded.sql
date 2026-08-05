-- ============================================================================
-- V1_1_040__external_fk_and_circular_fk_guarded.sql
-- E组公共闭环 & E01 V1.1 增量迁移 — 循环外键受控添加
-- ============================================================================
-- 本脚本在 e_closure_case 上添加 fk_e_case_current_history 外键。
-- 该外键引用 e_case_status_history(id)，形成循环引用：
--   e_case_status_history.case_id -> e_closure_case.id
--   e_closure_case.current_status_history_id -> e_case_status_history.id
-- 循环外键必须在两张表都创建后才能添加。
-- 使用 information_schema 检查表和外键是否存在后条件执行。
-- ============================================================================

-- 步骤 1：检查前置条件
SELECT '--- 循环外键前置检查 ---' AS check_section;

SELECT CASE
         WHEN (SELECT COUNT(*) FROM information_schema.tables
               WHERE table_schema = DATABASE()
                 AND table_name  = 'e_closure_case'
                 AND table_type  = 'BASE TABLE') > 0
         THEN 'e_closure_case EXISTS'
         ELSE 'e_closure_case MISSING — 无法添加循环外键'
       END AS check_result;

SELECT CASE
         WHEN (SELECT COUNT(*) FROM information_schema.tables
               WHERE table_schema = DATABASE()
                 AND table_name  = 'e_case_status_history'
                 AND table_type  = 'BASE TABLE') > 0
         THEN 'e_case_status_history EXISTS'
         ELSE 'e_case_status_history MISSING — 无法添加循环外键'
       END AS check_result;

-- 步骤 2：检查是否已存在该外键（幂等保护）
SELECT CASE
         WHEN (SELECT COUNT(*) FROM information_schema.table_constraints
               WHERE constraint_schema = DATABASE()
                 AND table_name  = 'e_closure_case'
                 AND constraint_name = 'fk_e_case_current_history') > 0
         THEN 'ALREADY EXISTS — 跳过'
         ELSE 'NOT FOUND — 可以添加'
       END AS fk_check;

-- 步骤 3：受控添加循环外键
-- 仅在两张表都存在且外键尚未添加时执行
SET @tbl_case_exists    = (SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = DATABASE() AND table_name = 'e_closure_case'    AND table_type = 'BASE TABLE');
SET @tbl_history_exists  = (SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = DATABASE() AND table_name = 'e_case_status_history' AND table_type = 'BASE TABLE');
SET @fk_already_exists   = (SELECT COUNT(*) FROM information_schema.table_constraints WHERE constraint_schema = DATABASE() AND table_name = 'e_closure_case' AND constraint_name = 'fk_e_case_current_history');

SET @exec_sql = IF(
    @tbl_case_exists > 0
    AND @tbl_history_exists > 0
    AND @fk_already_exists = 0,
    'ALTER TABLE e_closure_case ADD CONSTRAINT fk_e_case_current_history FOREIGN KEY (current_status_history_id) REFERENCES e_case_status_history(id) ON DELETE RESTRICT ON UPDATE RESTRICT',
    'SELECT ''循环外键跳过：前置条件不满足或外键已存在'' AS message'
);

PREPARE stmt FROM @exec_sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- 步骤 4：验证结果
SELECT '--- 循环外键添加结果验证 ---' AS check_section;

SELECT constraint_name, constraint_type
FROM information_schema.table_constraints
WHERE constraint_schema = DATABASE()
  AND table_name = 'e_closure_case'
  AND constraint_name = 'fk_e_case_current_history';
