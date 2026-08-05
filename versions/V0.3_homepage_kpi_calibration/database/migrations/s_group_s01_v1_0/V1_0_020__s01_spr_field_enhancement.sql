-- ============================================================================
-- V1_0_020__s01_spr_field_enhancement.sql
-- S01 V1.0 增量迁移 — safety_production_record 字段补齐
-- ============================================================================
-- safety_production_record 由 v0.1 建库创建，原结构缺少 V1.0 冻结稿 §5.1
-- 要求的确认批次、计数状态、数据治理等关键字段。
-- 使用 SET @sql + PREPARE/EXECUTE 模式保证幂等（避免 DELIMITER）。
-- ============================================================================

-- --------------------------------------------------------------------------
-- 辅助：如果列不存在则添加列（幂等 ALTER TABLE）
-- --------------------------------------------------------------------------
-- 注意：以下每段均为独立的 SET + PREPARE + EXECUTE + DEALLOCATE 块。
-- 每个 ALTER TABLE 只添加一列，利用 information_schema 做存在性检测。

-- 1. project_id
SET @col = 'project_id';
SET @tbl = 'safety_production_record';
SET @ddl = CONCAT('ALTER TABLE ', @tbl, ' ADD COLUMN project_id VARCHAR(50) NOT NULL DEFAULT \'LUOYI-ESG\' COMMENT \'项目标识\' AFTER id');
SET @cnt = (SELECT COUNT(*) FROM information_schema.columns WHERE table_schema = DATABASE() AND table_name = @tbl AND column_name = @col);
SET @sql = IF(@cnt = 0, @ddl, 'SELECT 1');
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

-- 2. cycle_start_date
SET @col = 'cycle_start_date';
SET @ddl = CONCAT('ALTER TABLE ', @tbl, ' ADD COLUMN cycle_start_date DATE NULL COMMENT \'当前安全生产周期起点\' AFTER `current_date`');
SET @cnt = (SELECT COUNT(*) FROM information_schema.columns WHERE table_schema = DATABASE() AND table_name = @tbl AND column_name = @col);
SET @sql = IF(@cnt = 0, @ddl, 'SELECT 1');
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

-- 3. statistics_as_of
SET @col = 'statistics_as_of';
SET @ddl = CONCAT('ALTER TABLE ', @tbl, ' ADD COLUMN statistics_as_of DATE NULL COMMENT \'统计期末\' AFTER `current_date`');
SET @cnt = (SELECT COUNT(*) FROM information_schema.columns WHERE table_schema = DATABASE() AND table_name = @tbl AND column_name = @col);
SET @sql = IF(@cnt = 0, @ddl, 'SELECT 1');
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

-- 4. confirmation_batch_id
SET @col = 'confirmation_batch_id';
SET @ddl = CONCAT('ALTER TABLE ', @tbl, ' ADD COLUMN confirmation_batch_id BIGINT NULL COMMENT \'关联确认批次ID\' AFTER continuous_days');
SET @cnt = (SELECT COUNT(*) FROM information_schema.columns WHERE table_schema = DATABASE() AND table_name = @tbl AND column_name = @col);
SET @sql = IF(@cnt = 0, @ddl, 'SELECT 1');
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

-- 5. confirmation_status
SET @col = 'confirmation_status';
SET @ddl = CONCAT('ALTER TABLE ', @tbl, ' ADD COLUMN confirmation_status VARCHAR(30) NOT NULL DEFAULT \'PENDING\' COMMENT \'PENDING / CONFIRMED\' AFTER confirmation_batch_id');
SET @cnt = (SELECT COUNT(*) FROM information_schema.columns WHERE table_schema = DATABASE() AND table_name = @tbl AND column_name = @col);
SET @sql = IF(@cnt = 0, @ddl, 'SELECT 1');
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

-- 6. verification_status
SET @col = 'verification_status';
SET @ddl = CONCAT('ALTER TABLE ', @tbl, ' ADD COLUMN verification_status VARCHAR(30) NOT NULL DEFAULT \'PENDING_REVIEW\' COMMENT \'PENDING_REVIEW / VERIFIED / REJECTED\' AFTER confirmation_status');
SET @cnt = (SELECT COUNT(*) FROM information_schema.columns WHERE table_schema = DATABASE() AND table_name = @tbl AND column_name = @col);
SET @sql = IF(@cnt = 0, @ddl, 'SELECT 1');
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

-- 7. effective_status
SET @col = 'effective_status';
SET @ddl = CONCAT('ALTER TABLE ', @tbl, ' ADD COLUMN effective_status VARCHAR(30) NOT NULL DEFAULT \'DRAFT\' COMMENT \'DRAFT / EFFECTIVE / INEFFECTIVE\' AFTER verification_status');
SET @cnt = (SELECT COUNT(*) FROM information_schema.columns WHERE table_schema = DATABASE() AND table_name = @tbl AND column_name = @col);
SET @sql = IF(@cnt = 0, @ddl, 'SELECT 1');
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

-- 8. is_current
SET @col = 'is_current';
SET @ddl = CONCAT('ALTER TABLE ', @tbl, ' ADD COLUMN is_current TINYINT(1) NOT NULL DEFAULT 1 COMMENT \'当前有效快照\' AFTER effective_status');
SET @cnt = (SELECT COUNT(*) FROM information_schema.columns WHERE table_schema = DATABASE() AND table_name = @tbl AND column_name = @col);
SET @sql = IF(@cnt = 0, @ddl, 'SELECT 1');
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

-- 9. data_nature
SET @col = 'data_nature';
SET @ddl = CONCAT('ALTER TABLE ', @tbl, ' ADD COLUMN data_nature VARCHAR(20) NOT NULL DEFAULT \'demo\' COMMENT \'demo / formal\' AFTER is_current');
SET @cnt = (SELECT COUNT(*) FROM information_schema.columns WHERE table_schema = DATABASE() AND table_name = @tbl AND column_name = @col);
SET @sql = IF(@cnt = 0, @ddl, 'SELECT 1');
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

-- 10. is_demo
SET @col = 'is_demo';
SET @ddl = CONCAT('ALTER TABLE ', @tbl, ' ADD COLUMN is_demo TINYINT(1) NOT NULL DEFAULT 0 COMMENT \'是否演示数据\' AFTER data_nature');
SET @cnt = (SELECT COUNT(*) FROM information_schema.columns WHERE table_schema = DATABASE() AND table_name = @tbl AND column_name = @col);
SET @sql = IF(@cnt = 0, @ddl, 'SELECT 1');
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

-- 11. confirmed_at
SET @col = 'confirmed_at';
SET @ddl = CONCAT('ALTER TABLE ', @tbl, ' ADD COLUMN confirmed_at DATETIME(6) NULL COMMENT \'确认时间\' AFTER is_demo');
SET @cnt = (SELECT COUNT(*) FROM information_schema.columns WHERE table_schema = DATABASE() AND table_name = @tbl AND column_name = @col);
SET @sql = IF(@cnt = 0, @ddl, 'SELECT 1');
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

-- 12. confirmed_by
SET @col = 'confirmed_by';
SET @ddl = CONCAT('ALTER TABLE ', @tbl, ' ADD COLUMN confirmed_by VARCHAR(100) NULL COMMENT \'确认人\' AFTER confirmed_at');
SET @cnt = (SELECT COUNT(*) FROM information_schema.columns WHERE table_schema = DATABASE() AND table_name = @tbl AND column_name = @col);
SET @sql = IF(@cnt = 0, @ddl, 'SELECT 1');
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

-- 13. updated_at
SET @col = 'updated_at';
SET @ddl = CONCAT('ALTER TABLE ', @tbl, ' ADD COLUMN updated_at TIMESTAMP(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6) COMMENT \'更新时间\' AFTER created_at');
SET @cnt = (SELECT COUNT(*) FROM information_schema.columns WHERE table_schema = DATABASE() AND table_name = @tbl AND column_name = @col);
SET @sql = IF(@cnt = 0, @ddl, 'SELECT 1');
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

-- --------------------------------------------------------------------------
-- 索引补充（幂等：存在则跳过）
-- --------------------------------------------------------------------------

-- 索引：project_id
SET @idx_name = 'idx_spr_project_id';
SET @idx_ddl = CONCAT('ALTER TABLE ', @tbl, ' ADD INDEX idx_spr_project_id (project_id)');
SET @idx_exists = (SELECT COUNT(*) FROM information_schema.statistics WHERE table_schema = DATABASE() AND table_name = @tbl AND index_name = @idx_name);
SET @sql = IF(@idx_exists = 0, @idx_ddl, 'SELECT 1');
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

-- 索引：data_nature + is_demo + is_current
SET @idx_name = 'idx_spr_nature_current';
SET @idx_ddl = CONCAT('ALTER TABLE ', @tbl, ' ADD INDEX idx_spr_nature_current (data_nature, is_demo, is_current)');
SET @idx_exists = (SELECT COUNT(*) FROM information_schema.statistics WHERE table_schema = DATABASE() AND table_name = @tbl AND index_name = @idx_name);
SET @sql = IF(@idx_exists = 0, @idx_ddl, 'SELECT 1');
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

-- 索引：confirmation_status
SET @idx_name = 'idx_spr_confirmation_status';
SET @idx_ddl = CONCAT('ALTER TABLE ', @tbl, ' ADD INDEX idx_spr_confirmation_status (confirmation_status)');
SET @idx_exists = (SELECT COUNT(*) FROM information_schema.statistics WHERE table_schema = DATABASE() AND table_name = @tbl AND index_name = @idx_name);
SET @sql = IF(@idx_exists = 0, @idx_ddl, 'SELECT 1');
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;
