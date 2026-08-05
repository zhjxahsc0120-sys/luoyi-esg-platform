-- ============================================================================
-- V1_1_043__e02_env_issue_fields.sql
-- E02 环保问题台账表字段补齐（MySQL 8 / pymysql 可执行，无 DELIMITER）
-- ============================================================================

SET @db := DATABASE();

-- is_demo
SET @exists := (
  SELECT COUNT(*) FROM information_schema.COLUMNS
  WHERE TABLE_SCHEMA=@db AND TABLE_NAME='env_issue_record' AND COLUMN_NAME='is_demo'
);
SET @sql := IF(@exists=0,
  'ALTER TABLE env_issue_record ADD COLUMN is_demo TINYINT(1) NOT NULL DEFAULT 0 COMMENT ''是否演示数据''',
  'SELECT 1');
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

-- data_nature
SET @exists := (
  SELECT COUNT(*) FROM information_schema.COLUMNS
  WHERE TABLE_SCHEMA=@db AND TABLE_NAME='env_issue_record' AND COLUMN_NAME='data_nature'
);
SET @sql := IF(@exists=0,
  'ALTER TABLE env_issue_record ADD COLUMN data_nature VARCHAR(20) NOT NULL DEFAULT ''formal'' COMMENT ''数据性质''',
  'SELECT 1');
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

-- business_code
SET @exists := (
  SELECT COUNT(*) FROM information_schema.COLUMNS
  WHERE TABLE_SCHEMA=@db AND TABLE_NAME='env_issue_record' AND COLUMN_NAME='business_code'
);
SET @sql := IF(@exists=0,
  'ALTER TABLE env_issue_record ADD COLUMN business_code VARCHAR(80) NULL COMMENT ''业务编号''',
  'SELECT 1');
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

-- issue_name
SET @exists := (
  SELECT COUNT(*) FROM information_schema.COLUMNS
  WHERE TABLE_SCHEMA=@db AND TABLE_NAME='env_issue_record' AND COLUMN_NAME='issue_name'
);
SET @sql := IF(@exists=0,
  'ALTER TABLE env_issue_record ADD COLUMN issue_name VARCHAR(255) NULL COMMENT ''问题名称''',
  'SELECT 1');
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

-- deadline
SET @exists := (
  SELECT COUNT(*) FROM information_schema.COLUMNS
  WHERE TABLE_SCHEMA=@db AND TABLE_NAME='env_issue_record' AND COLUMN_NAME='deadline'
);
SET @sql := IF(@exists=0,
  'ALTER TABLE env_issue_record ADD COLUMN deadline DATE NULL COMMENT ''整改期限''',
  'SELECT 1');
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

-- responsible_org_name
SET @exists := (
  SELECT COUNT(*) FROM information_schema.COLUMNS
  WHERE TABLE_SCHEMA=@db AND TABLE_NAME='env_issue_record' AND COLUMN_NAME='responsible_org_name'
);
SET @sql := IF(@exists=0,
  'ALTER TABLE env_issue_record ADD COLUMN responsible_org_name VARCHAR(100) NULL COMMENT ''责任单位名称''',
  'SELECT 1');
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

-- location_text
SET @exists := (
  SELECT COUNT(*) FROM information_schema.COLUMNS
  WHERE TABLE_SCHEMA=@db AND TABLE_NAME='env_issue_record' AND COLUMN_NAME='location_text'
);
SET @sql := IF(@exists=0,
  'ALTER TABLE env_issue_record ADD COLUMN location_text VARCHAR(255) NULL COMMENT ''位置描述''',
  'SELECT 1');
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

-- indexes
SET @exists := (
  SELECT COUNT(*) FROM information_schema.STATISTICS
  WHERE TABLE_SCHEMA=@db AND TABLE_NAME='env_issue_record' AND INDEX_NAME='idx_env_issue_scope'
);
SET @sql := IF(@exists=0,
  'CREATE INDEX idx_env_issue_scope ON env_issue_record(is_demo, data_nature, issue_status)',
  'SELECT 1');
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

SET @exists := (
  SELECT COUNT(*) FROM information_schema.STATISTICS
  WHERE TABLE_SCHEMA=@db AND TABLE_NAME='env_issue_record' AND INDEX_NAME='idx_env_issue_biz_code'
);
SET @sql := IF(@exists=0,
  'CREATE INDEX idx_env_issue_biz_code ON env_issue_record(business_code)',
  'SELECT 1');
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

UPDATE env_issue_record
   SET is_demo = 1,
       data_nature = 'demo',
       business_code = CASE id
           WHEN 420001 THEN 'E02-D03'
           WHEN 420002 THEN 'E02-D01'
           WHEN 420003 THEN 'E02-D02'
           WHEN 420004 THEN 'E02-D04'
           WHEN 420005 THEN 'E02-D05'
           ELSE business_code
       END
 WHERE id BETWEEN 420001 AND 420005;
