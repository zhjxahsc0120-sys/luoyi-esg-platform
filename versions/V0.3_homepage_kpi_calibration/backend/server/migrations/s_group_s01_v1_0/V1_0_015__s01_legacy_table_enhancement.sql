-- ============================================================================
-- V1_0_015__s01_legacy_table_enhancement.sql
-- S01 V1.0 增量迁移 — 对旧表做幂等字段增强
-- ============================================================================
-- safety_incident_record 和 construction_stage_record 已由旧代码
-- (ensure_s01_business_tables in mysql_api.py) 创建，结构与冻结稿不一致。
-- 本文件通过 ALTER TABLE ADD COLUMN 补齐冻结稿要求字段，
-- 使用 SET @sql + PREPARE/EXECUTE 模式保证幂等。
--
-- Round-2 修复：
--   - CSR/SIR.id 幂等补 AUTO_INCREMENT（旧表 BIGINT PK 无 AI）
--   - skip 路径全部使用 CONCAT（禁止 MySQL + 字符串拼接）
--
-- 旧 safety_incident_record 列：
--   id, document_id, incident_date, incident_name, incident_type, incident_level,
--   interrupt_counting, responsible_department, handling_status, interrupt_reason, created_at
--
-- 旧 construction_stage_record 列：
--   id, stage_key, stage_name, stage_status, stage_detail, sequence_no, start_date, end_date, created_at
-- ============================================================================

-- ============================================================================
-- Part A: safety_incident_record 字段增强
-- ============================================================================

SET @tbl = 'safety_incident_record';

-- A0. id AUTO_INCREMENT（旧表 BIGINT PK 无 AI；为后续 SIR seed 预留）
SET @col = 'id';
SET @extra = (
    SELECT EXTRA FROM information_schema.columns
    WHERE table_schema = DATABASE() AND table_name = @tbl AND column_name = @col
);
SET @ddl = CONCAT('ALTER TABLE ', @tbl, ' MODIFY COLUMN id BIGINT NOT NULL AUTO_INCREMENT');
SET @sql = IF(IFNULL(@extra, '') NOT LIKE '%auto_increment%', @ddl, 'SELECT CONCAT(\'skip: \', @col, \' already AUTO_INCREMENT\')');
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

-- A1. project_id
SET @col = 'project_id';
SET @ddl = CONCAT('ALTER TABLE ', @tbl, ' ADD COLUMN project_id VARCHAR(50) NOT NULL DEFAULT \'LUOYI-ESG\' COMMENT \'项目标识\' AFTER id');
SET @cnt = (SELECT COUNT(*) FROM information_schema.columns WHERE table_schema = DATABASE() AND table_name = @tbl AND column_name = @col);
SET @sql = IF(@cnt = 0, @ddl, 'SELECT CONCAT(\'skip: \', @col, \' already exists\')');
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

-- A2. incident_code
SET @col = 'incident_code';
SET @ddl = CONCAT('ALTER TABLE ', @tbl, ' ADD COLUMN incident_code VARCHAR(60) NULL COMMENT \'事故编码\' AFTER project_id');
SET @cnt = (SELECT COUNT(*) FROM information_schema.columns WHERE table_schema = DATABASE() AND table_name = @tbl AND column_name = @col);
SET @sql = IF(@cnt = 0, @ddl, 'SELECT CONCAT(\'skip: \', @col, \' already exists\')');
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

-- A3. occurred_date（冻结稿 §5.2 要求；与旧 incident_date 语义重叠，新增后由应用层对齐）
SET @col = 'occurred_date';
SET @ddl = CONCAT('ALTER TABLE ', @tbl, ' ADD COLUMN occurred_date DATE NULL COMMENT \'事故发生日期（冻结稿口径）\' AFTER incident_code');
SET @cnt = (SELECT COUNT(*) FROM information_schema.columns WHERE table_schema = DATABASE() AND table_name = @tbl AND column_name = @col);
SET @sql = IF(@cnt = 0, @ddl, 'SELECT CONCAT(\'skip: \', @col, \' already exists\')');
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

-- A4. incident_category
SET @col = 'incident_category';
SET @ddl = CONCAT('ALTER TABLE ', @tbl, ' ADD COLUMN incident_category VARCHAR(50) NULL COMMENT \'事故分类\' AFTER incident_type');
SET @cnt = (SELECT COUNT(*) FROM information_schema.columns WHERE table_schema = DATABASE() AND table_name = @tbl AND column_name = @col);
SET @sql = IF(@cnt = 0, @ddl, 'SELECT CONCAT(\'skip: \', @col, \' already exists\')');
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

-- A5. description
SET @col = 'description';
SET @ddl = CONCAT('ALTER TABLE ', @tbl, ' ADD COLUMN description TEXT NULL COMMENT \'事故描述\' AFTER incident_category');
SET @cnt = (SELECT COUNT(*) FROM information_schema.columns WHERE table_schema = DATABASE() AND table_name = @tbl AND column_name = @col);
SET @sql = IF(@cnt = 0, @ddl, 'SELECT CONCAT(\'skip: \', @col, \' already exists\')');
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

-- A6. segment_name
SET @col = 'segment_name';
SET @ddl = CONCAT('ALTER TABLE ', @tbl, ' ADD COLUMN segment_name VARCHAR(100) NULL COMMENT \'标段名称\' AFTER description');
SET @cnt = (SELECT COUNT(*) FROM information_schema.columns WHERE table_schema = DATABASE() AND table_name = @tbl AND column_name = @col);
SET @sql = IF(@cnt = 0, @ddl, 'SELECT CONCAT(\'skip: \', @col, \' already exists\')');
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

-- A7. responsible_unit
SET @col = 'responsible_unit';
SET @ddl = CONCAT('ALTER TABLE ', @tbl, ' ADD COLUMN responsible_unit VARCHAR(200) NULL COMMENT \'责任单位\' AFTER segment_name');
SET @cnt = (SELECT COUNT(*) FROM information_schema.columns WHERE table_schema = DATABASE() AND table_name = @tbl AND column_name = @col);
SET @sql = IF(@cnt = 0, @ddl, 'SELECT CONCAT(\'skip: \', @col, \' already exists\')');
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

-- A8. fatality_count
SET @col = 'fatality_count';
SET @ddl = CONCAT('ALTER TABLE ', @tbl, ' ADD COLUMN fatality_count INT NOT NULL DEFAULT 0 COMMENT \'死亡人数\' AFTER responsible_unit');
SET @cnt = (SELECT COUNT(*) FROM information_schema.columns WHERE table_schema = DATABASE() AND table_name = @tbl AND column_name = @col);
SET @sql = IF(@cnt = 0, @ddl, 'SELECT CONCAT(\'skip: \', @col, \' already exists\')');
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

-- A9. injury_count
SET @col = 'injury_count';
SET @ddl = CONCAT('ALTER TABLE ', @tbl, ' ADD COLUMN injury_count INT NOT NULL DEFAULT 0 COMMENT \'受伤人数\' AFTER fatality_count');
SET @cnt = (SELECT COUNT(*) FROM information_schema.columns WHERE table_schema = DATABASE() AND table_name = @tbl AND column_name = @col);
SET @sql = IF(@cnt = 0, @ddl, 'SELECT CONCAT(\'skip: \', @col, \' already exists\')');
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

-- A10. responsibility_determination_status
SET @col = 'responsibility_determination_status';
SET @ddl = CONCAT('ALTER TABLE ', @tbl, ' ADD COLUMN responsibility_determination_status VARCHAR(30) NOT NULL DEFAULT \'PENDING\' COMMENT \'PENDING / RESPONSIBLE / NON_RESPONSIBLE\' AFTER injury_count');
SET @cnt = (SELECT COUNT(*) FROM information_schema.columns WHERE table_schema = DATABASE() AND table_name = @tbl AND column_name = @col);
SET @sql = IF(@cnt = 0, @ddl, 'SELECT CONCAT(\'skip: \', @col, \' already exists\')');
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

-- A11. determination_effective_date
SET @col = 'determination_effective_date';
SET @ddl = CONCAT('ALTER TABLE ', @tbl, ' ADD COLUMN determination_effective_date DATE NULL COMMENT \'认定生效日期\' AFTER responsibility_determination_status');
SET @cnt = (SELECT COUNT(*) FROM information_schema.columns WHERE table_schema = DATABASE() AND table_name = @tbl AND column_name = @col);
SET @sql = IF(@cnt = 0, @ddl, 'SELECT CONCAT(\'skip: \', @col, \' already exists\')');
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

-- A12. determination_summary
SET @col = 'determination_summary';
SET @ddl = CONCAT('ALTER TABLE ', @tbl, ' ADD COLUMN determination_summary VARCHAR(500) NULL COMMENT \'认定摘要\' AFTER determination_effective_date');
SET @cnt = (SELECT COUNT(*) FROM information_schema.columns WHERE table_schema = DATABASE() AND table_name = @tbl AND column_name = @col);
SET @sql = IF(@cnt = 0, @ddl, 'SELECT CONCAT(\'skip: \', @col, \' already exists\')');
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

-- A13. effective_status
SET @col = 'effective_status';
SET @ddl = CONCAT('ALTER TABLE ', @tbl, ' ADD COLUMN effective_status VARCHAR(30) NOT NULL DEFAULT \'DRAFT\' COMMENT \'DRAFT / EFFECTIVE / INEFFECTIVE\' AFTER interrupt_reason');
SET @cnt = (SELECT COUNT(*) FROM information_schema.columns WHERE table_schema = DATABASE() AND table_name = @tbl AND column_name = @col);
SET @sql = IF(@cnt = 0, @ddl, 'SELECT CONCAT(\'skip: \', @col, \' already exists\')');
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

-- A14. is_current
SET @col = 'is_current';
SET @ddl = CONCAT('ALTER TABLE ', @tbl, ' ADD COLUMN is_current TINYINT(1) NOT NULL DEFAULT 1 COMMENT \'当前有效版本\' AFTER effective_status');
SET @cnt = (SELECT COUNT(*) FROM information_schema.columns WHERE table_schema = DATABASE() AND table_name = @tbl AND column_name = @col);
SET @sql = IF(@cnt = 0, @ddl, 'SELECT CONCAT(\'skip: \', @col, \' already exists\')');
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

-- A15. effective_at
SET @col = 'effective_at';
SET @ddl = CONCAT('ALTER TABLE ', @tbl, ' ADD COLUMN effective_at DATETIME(6) NULL COMMENT \'生效时间\' AFTER is_current');
SET @cnt = (SELECT COUNT(*) FROM information_schema.columns WHERE table_schema = DATABASE() AND table_name = @tbl AND column_name = @col);
SET @sql = IF(@cnt = 0, @ddl, 'SELECT CONCAT(\'skip: \', @col, \' already exists\')');
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

-- A16. effective_by
SET @col = 'effective_by';
SET @ddl = CONCAT('ALTER TABLE ', @tbl, ' ADD COLUMN effective_by BIGINT NULL COMMENT \'生效操作人\' AFTER effective_at');
SET @cnt = (SELECT COUNT(*) FROM information_schema.columns WHERE table_schema = DATABASE() AND table_name = @tbl AND column_name = @col);
SET @sql = IF(@cnt = 0, @ddl, 'SELECT CONCAT(\'skip: \', @col, \' already exists\')');
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

-- A17. data_nature
SET @col = 'data_nature';
SET @ddl = CONCAT('ALTER TABLE ', @tbl, ' ADD COLUMN data_nature VARCHAR(20) NOT NULL DEFAULT \'demo\' COMMENT \'demo / formal\' AFTER effective_by');
SET @cnt = (SELECT COUNT(*) FROM information_schema.columns WHERE table_schema = DATABASE() AND table_name = @tbl AND column_name = @col);
SET @sql = IF(@cnt = 0, @ddl, 'SELECT CONCAT(\'skip: \', @col, \' already exists\')');
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

-- A18. is_demo
SET @col = 'is_demo';
SET @ddl = CONCAT('ALTER TABLE ', @tbl, ' ADD COLUMN is_demo TINYINT(1) NOT NULL DEFAULT 1 COMMENT \'是否演示数据（旧行默认 demo）\' AFTER data_nature');
SET @cnt = (SELECT COUNT(*) FROM information_schema.columns WHERE table_schema = DATABASE() AND table_name = @tbl AND column_name = @col);
SET @sql = IF(@cnt = 0, @ddl, 'SELECT CONCAT(\'skip: \', @col, \' already exists\')');
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

-- A19. demo_batch_code
SET @col = 'demo_batch_code';
SET @ddl = CONCAT('ALTER TABLE ', @tbl, ' ADD COLUMN demo_batch_code VARCHAR(60) NULL COMMENT \'关联演示批次编码\' AFTER is_demo');
SET @cnt = (SELECT COUNT(*) FROM information_schema.columns WHERE table_schema = DATABASE() AND table_name = @tbl AND column_name = @col);
SET @sql = IF(@cnt = 0, @ddl, 'SELECT CONCAT(\'skip: \', @col, \' already exists\')');
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

-- A20. source_document_id
SET @col = 'source_document_id';
SET @ddl = CONCAT('ALTER TABLE ', @tbl, ' ADD COLUMN source_document_id BIGINT NULL COMMENT \'来源资料ID\' AFTER demo_batch_code');
SET @cnt = (SELECT COUNT(*) FROM information_schema.columns WHERE table_schema = DATABASE() AND table_name = @tbl AND column_name = @col);
SET @sql = IF(@cnt = 0, @ddl, 'SELECT CONCAT(\'skip: \', @col, \' already exists\')');
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

-- A21. remark
SET @col = 'remark';
SET @ddl = CONCAT('ALTER TABLE ', @tbl, ' ADD COLUMN remark VARCHAR(500) NULL COMMENT \'备注\' AFTER source_document_id');
SET @cnt = (SELECT COUNT(*) FROM information_schema.columns WHERE table_schema = DATABASE() AND table_name = @tbl AND column_name = @col);
SET @sql = IF(@cnt = 0, @ddl, 'SELECT CONCAT(\'skip: \', @col, \' already exists\')');
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

-- A22. updated_at
SET @col = 'updated_at';
SET @ddl = CONCAT('ALTER TABLE ', @tbl, ' ADD COLUMN updated_at TIMESTAMP(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6) COMMENT \'更新时间\' AFTER created_at');
SET @cnt = (SELECT COUNT(*) FROM information_schema.columns WHERE table_schema = DATABASE() AND table_name = @tbl AND column_name = @col);
SET @sql = IF(@cnt = 0, @ddl, 'SELECT CONCAT(\'skip: \', @col, \' already exists\')');
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

-- A23. 回填 occurred_date from incident_date（旧行有 incident_date 无 occurred_date）
UPDATE safety_incident_record SET occurred_date = incident_date WHERE occurred_date IS NULL AND incident_date IS NOT NULL;

-- A24. 回填 incident_code（旧行无 incident_code，用 SIR-LEGACY-{id} 生成）
UPDATE safety_incident_record SET incident_code = CONCAT('SIR-LEGACY-', id) WHERE incident_code IS NULL;

-- A25. 标记旧行为 demo
UPDATE safety_incident_record SET data_nature = 'demo', is_demo = 1 WHERE data_nature = 'demo' AND is_demo = 1;

-- 索引补充（幂等）
SET @idx_name = 'idx_sir_project_occurred';
SET @idx_ddl = CONCAT('ALTER TABLE ', @tbl, ' ADD INDEX idx_sir_project_occurred (project_id, occurred_date)');
SET @idx_exists = (SELECT COUNT(*) FROM information_schema.statistics WHERE table_schema = DATABASE() AND table_name = @tbl AND index_name = @idx_name);
SET @sql = IF(@idx_exists = 0, @idx_ddl, 'SELECT 1');
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

SET @idx_name = 'idx_sir_determination_status';
SET @idx_ddl = CONCAT('ALTER TABLE ', @tbl, ' ADD INDEX idx_sir_determination_status (responsibility_determination_status)');
SET @idx_exists = (SELECT COUNT(*) FROM information_schema.statistics WHERE table_schema = DATABASE() AND table_name = @tbl AND index_name = @idx_name);
SET @sql = IF(@idx_exists = 0, @idx_ddl, 'SELECT 1');
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

SET @idx_name = 'idx_sir_effective_current';
SET @idx_ddl = CONCAT('ALTER TABLE ', @tbl, ' ADD INDEX idx_sir_effective_current (effective_status, is_current)');
SET @idx_exists = (SELECT COUNT(*) FROM information_schema.statistics WHERE table_schema = DATABASE() AND table_name = @tbl AND index_name = @idx_name);
SET @sql = IF(@idx_exists = 0, @idx_ddl, 'SELECT 1');
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

SET @idx_name = 'idx_sir_data_nature';
SET @idx_ddl = CONCAT('ALTER TABLE ', @tbl, ' ADD INDEX idx_sir_data_nature (data_nature)');
SET @idx_exists = (SELECT COUNT(*) FROM information_schema.statistics WHERE table_schema = DATABASE() AND table_name = @tbl AND index_name = @idx_name);
SET @sql = IF(@idx_exists = 0, @idx_ddl, 'SELECT 1');
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

SET @idx_name = 'idx_sir_is_demo';
SET @idx_ddl = CONCAT('ALTER TABLE ', @tbl, ' ADD INDEX idx_sir_is_demo (is_demo)');
SET @idx_exists = (SELECT COUNT(*) FROM information_schema.statistics WHERE table_schema = DATABASE() AND table_name = @tbl AND index_name = @idx_name);
SET @sql = IF(@idx_exists = 0, @idx_ddl, 'SELECT 1');
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

SET @idx_name = 'idx_sir_occurred_date';
SET @idx_ddl = CONCAT('ALTER TABLE ', @tbl, ' ADD INDEX idx_sir_occurred_date (occurred_date)');
SET @idx_exists = (SELECT COUNT(*) FROM information_schema.statistics WHERE table_schema = DATABASE() AND table_name = @tbl AND index_name = @idx_name);
SET @sql = IF(@idx_exists = 0, @idx_ddl, 'SELECT 1');
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;


-- ============================================================================
-- Part B: construction_stage_record 字段增强
-- ============================================================================

SET @tbl = 'construction_stage_record';

-- B0. id AUTO_INCREMENT（旧表由 ensure_s01_business_tables 创建为 BIGINT PK 无 AI）
SET @col = 'id';
SET @extra = (
    SELECT EXTRA FROM information_schema.columns
    WHERE table_schema = DATABASE() AND table_name = @tbl AND column_name = @col
);
SET @ddl = CONCAT('ALTER TABLE ', @tbl, ' MODIFY COLUMN id BIGINT NOT NULL AUTO_INCREMENT');
SET @sql = IF(IFNULL(@extra, '') NOT LIKE '%auto_increment%', @ddl, 'SELECT CONCAT(\'skip: \', @col, \' already AUTO_INCREMENT\')');
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

-- B1. project_id
SET @col = 'project_id';
SET @ddl = CONCAT('ALTER TABLE ', @tbl, ' ADD COLUMN project_id VARCHAR(50) NOT NULL DEFAULT \'LUOYI-ESG\' COMMENT \'项目标识\' AFTER id');
SET @cnt = (SELECT COUNT(*) FROM information_schema.columns WHERE table_schema = DATABASE() AND table_name = @tbl AND column_name = @col);
SET @sql = IF(@cnt = 0, @ddl, 'SELECT CONCAT(\'skip: \', @col, \' already exists\')');
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

-- B2. detail（旧表有 stage_detail，新增 detail 对齐冻结稿）
SET @col = 'detail';
SET @ddl = CONCAT('ALTER TABLE ', @tbl, ' ADD COLUMN detail VARCHAR(500) NULL COMMENT \'阶段详情\' AFTER end_date');
SET @cnt = (SELECT COUNT(*) FROM information_schema.columns WHERE table_schema = DATABASE() AND table_name = @tbl AND column_name = @col);
SET @sql = IF(@cnt = 0, @ddl, 'SELECT CONCAT(\'skip: \', @col, \' already exists\')');
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

-- B3. effective_status
SET @col = 'effective_status';
SET @ddl = CONCAT('ALTER TABLE ', @tbl, ' ADD COLUMN effective_status VARCHAR(30) NOT NULL DEFAULT \'DRAFT\' COMMENT \'DRAFT / EFFECTIVE / INEFFECTIVE\' AFTER detail');
SET @cnt = (SELECT COUNT(*) FROM information_schema.columns WHERE table_schema = DATABASE() AND table_name = @tbl AND column_name = @col);
SET @sql = IF(@cnt = 0, @ddl, 'SELECT CONCAT(\'skip: \', @col, \' already exists\')');
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

-- B4. is_current
SET @col = 'is_current';
SET @ddl = CONCAT('ALTER TABLE ', @tbl, ' ADD COLUMN is_current TINYINT(1) NOT NULL DEFAULT 1 COMMENT \'当前有效\' AFTER effective_status');
SET @cnt = (SELECT COUNT(*) FROM information_schema.columns WHERE table_schema = DATABASE() AND table_name = @tbl AND column_name = @col);
SET @sql = IF(@cnt = 0, @ddl, 'SELECT CONCAT(\'skip: \', @col, \' already exists\')');
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

-- B5. data_nature
SET @col = 'data_nature';
SET @ddl = CONCAT('ALTER TABLE ', @tbl, ' ADD COLUMN data_nature VARCHAR(20) NOT NULL DEFAULT \'demo\' COMMENT \'demo / formal\' AFTER is_current');
SET @cnt = (SELECT COUNT(*) FROM information_schema.columns WHERE table_schema = DATABASE() AND table_name = @tbl AND column_name = @col);
SET @sql = IF(@cnt = 0, @ddl, 'SELECT CONCAT(\'skip: \', @col, \' already exists\')');
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

-- B6. is_demo
SET @col = 'is_demo';
SET @ddl = CONCAT('ALTER TABLE ', @tbl, ' ADD COLUMN is_demo TINYINT(1) NOT NULL DEFAULT 1 COMMENT \'是否演示数据（旧行默认 demo）\' AFTER data_nature');
SET @cnt = (SELECT COUNT(*) FROM information_schema.columns WHERE table_schema = DATABASE() AND table_name = @tbl AND column_name = @col);
SET @sql = IF(@cnt = 0, @ddl, 'SELECT CONCAT(\'skip: \', @col, \' already exists\')');
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

-- B7. updated_at
SET @col = 'updated_at';
SET @ddl = CONCAT('ALTER TABLE ', @tbl, ' ADD COLUMN updated_at TIMESTAMP(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6) COMMENT \'更新时间\' AFTER created_at');
SET @cnt = (SELECT COUNT(*) FROM information_schema.columns WHERE table_schema = DATABASE() AND table_name = @tbl AND column_name = @col);
SET @sql = IF(@cnt = 0, @ddl, 'SELECT CONCAT(\'skip: \', @col, \' already exists\')');
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

-- B8. 标记旧行为 demo
UPDATE construction_stage_record SET data_nature = 'demo', is_demo = 1 WHERE data_nature = 'demo' AND is_demo = 1;

-- B9. 回填 detail from stage_detail（旧表有 stage_detail）
UPDATE construction_stage_record SET detail = stage_detail WHERE detail IS NULL AND stage_detail IS NOT NULL;

-- B10. 旧「主体工程施工」current 行退出现役（改为 completed，is_current=0）
UPDATE construction_stage_record
SET stage_status = 'completed', is_current = 0
WHERE stage_name = '主体工程施工' AND stage_status = 'current' AND is_current = 1;

-- 索引补充（幂等）
SET @idx_name = 'idx_csr_project_current';
SET @idx_ddl = CONCAT('ALTER TABLE ', @tbl, ' ADD INDEX idx_csr_project_current (project_id, stage_status, is_current)');
SET @idx_exists = (SELECT COUNT(*) FROM information_schema.statistics WHERE table_schema = DATABASE() AND table_name = @tbl AND index_name = @idx_name);
SET @sql = IF(@idx_exists = 0, @idx_ddl, 'SELECT 1');
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

SET @idx_name = 'idx_csr_stage_status';
SET @idx_ddl = CONCAT('ALTER TABLE ', @tbl, ' ADD INDEX idx_csr_stage_status (stage_status)');
SET @idx_exists = (SELECT COUNT(*) FROM information_schema.statistics WHERE table_schema = DATABASE() AND table_name = @tbl AND index_name = @idx_name);
SET @sql = IF(@idx_exists = 0, @idx_ddl, 'SELECT 1');
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

SET @idx_name = 'idx_csr_sequence';
SET @idx_ddl = CONCAT('ALTER TABLE ', @tbl, ' ADD INDEX idx_csr_sequence (sequence_no)');
SET @idx_exists = (SELECT COUNT(*) FROM information_schema.statistics WHERE table_schema = DATABASE() AND table_name = @tbl AND index_name = @idx_name);
SET @sql = IF(@idx_exists = 0, @idx_ddl, 'SELECT 1');
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;
