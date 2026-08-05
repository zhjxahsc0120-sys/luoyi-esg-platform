-- ============================================================================
-- V1_1_046__e03_schema_fields.sql
-- E03 P1 schema fields, guarded for MySQL 8 / pymysql multi-statement execution.
-- ============================================================================

SET @db := DATABASE();

-- Add a column only when it is absent. MySQL 8.4 does not support
-- ALTER TABLE ... ADD COLUMN IF NOT EXISTS.

-- water_protection_issue.is_demo
SET @exists := (
  SELECT COUNT(*) FROM information_schema.COLUMNS
  WHERE TABLE_SCHEMA=@db AND TABLE_NAME='water_protection_issue' AND COLUMN_NAME='is_demo'
);
SET @sql := IF(@exists=0,
  'ALTER TABLE water_protection_issue ADD COLUMN is_demo TINYINT(1) NOT NULL DEFAULT 0 COMMENT ''demo data flag''',
  'SELECT 1');
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

-- water_protection_issue.data_nature
SET @exists := (
  SELECT COUNT(*) FROM information_schema.COLUMNS
  WHERE TABLE_SCHEMA=@db AND TABLE_NAME='water_protection_issue' AND COLUMN_NAME='data_nature'
);
SET @sql := IF(@exists=0,
  'ALTER TABLE water_protection_issue ADD COLUMN data_nature VARCHAR(20) NOT NULL DEFAULT ''formal'' COMMENT ''formal, demo, or platform_calc''',
  'SELECT 1');
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

-- water_protection_issue.effective_status
SET @exists := (
  SELECT COUNT(*) FROM information_schema.COLUMNS
  WHERE TABLE_SCHEMA=@db AND TABLE_NAME='water_protection_issue' AND COLUMN_NAME='effective_status'
);
SET @sql := IF(@exists=0,
  'ALTER TABLE water_protection_issue ADD COLUMN effective_status VARCHAR(30) NOT NULL DEFAULT ''EFFECTIVE'' COMMENT ''EFFECTIVE, INEFFECTIVE, or DRAFT''',
  'SELECT 1');
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

-- water_protection_issue.business_code
SET @exists := (
  SELECT COUNT(*) FROM information_schema.COLUMNS
  WHERE TABLE_SCHEMA=@db AND TABLE_NAME='water_protection_issue' AND COLUMN_NAME='business_code'
);
SET @sql := IF(@exists=0,
  'ALTER TABLE water_protection_issue ADD COLUMN business_code VARCHAR(80) NULL COMMENT ''business code, for example E03-D01''',
  'SELECT 1');
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

-- water_protection_issue.issue_name
SET @exists := (
  SELECT COUNT(*) FROM information_schema.COLUMNS
  WHERE TABLE_SCHEMA=@db AND TABLE_NAME='water_protection_issue' AND COLUMN_NAME='issue_name'
);
SET @sql := IF(@exists=0,
  'ALTER TABLE water_protection_issue ADD COLUMN issue_name VARCHAR(255) NULL COMMENT ''issue title''',
  'SELECT 1');
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

-- water_protection_issue.issue_type
SET @exists := (
  SELECT COUNT(*) FROM information_schema.COLUMNS
  WHERE TABLE_SCHEMA=@db AND TABLE_NAME='water_protection_issue' AND COLUMN_NAME='issue_type'
);
SET @sql := IF(@exists=0,
  'ALTER TABLE water_protection_issue ADD COLUMN issue_type VARCHAR(64) NULL COMMENT ''water protection issue type''',
  'SELECT 1');
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

-- water_protection_issue.overdue
SET @exists := (
  SELECT COUNT(*) FROM information_schema.COLUMNS
  WHERE TABLE_SCHEMA=@db AND TABLE_NAME='water_protection_issue' AND COLUMN_NAME='overdue'
);
SET @sql := IF(@exists=0,
  'ALTER TABLE water_protection_issue ADD COLUMN overdue TINYINT(1) NOT NULL DEFAULT 0 COMMENT ''overdue flag''',
  'SELECT 1');
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

-- water_protection_issue.deadline
SET @exists := (
  SELECT COUNT(*) FROM information_schema.COLUMNS
  WHERE TABLE_SCHEMA=@db AND TABLE_NAME='water_protection_issue' AND COLUMN_NAME='deadline'
);
SET @sql := IF(@exists=0,
  'ALTER TABLE water_protection_issue ADD COLUMN deadline DATE NULL COMMENT ''rectification deadline''',
  'SELECT 1');
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

-- water_protection_issue.responsible_org_name
SET @exists := (
  SELECT COUNT(*) FROM information_schema.COLUMNS
  WHERE TABLE_SCHEMA=@db AND TABLE_NAME='water_protection_issue' AND COLUMN_NAME='responsible_org_name'
);
SET @sql := IF(@exists=0,
  'ALTER TABLE water_protection_issue ADD COLUMN responsible_org_name VARCHAR(100) NULL COMMENT ''responsible organization''',
  'SELECT 1');
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

-- water_protection_issue.location_text
SET @exists := (
  SELECT COUNT(*) FROM information_schema.COLUMNS
  WHERE TABLE_SCHEMA=@db AND TABLE_NAME='water_protection_issue' AND COLUMN_NAME='location_text'
);
SET @sql := IF(@exists=0,
  'ALTER TABLE water_protection_issue ADD COLUMN location_text VARCHAR(255) NULL COMMENT ''location description''',
  'SELECT 1');
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

-- water_protection_issue.description
SET @exists := (
  SELECT COUNT(*) FROM information_schema.COLUMNS
  WHERE TABLE_SCHEMA=@db AND TABLE_NAME='water_protection_issue' AND COLUMN_NAME='description'
);
SET @sql := IF(@exists=0,
  'ALTER TABLE water_protection_issue ADD COLUMN description TEXT NULL COMMENT ''issue description''',
  'SELECT 1');
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

-- water_protection_issue.discovery_basis
SET @exists := (
  SELECT COUNT(*) FROM information_schema.COLUMNS
  WHERE TABLE_SCHEMA=@db AND TABLE_NAME='water_protection_issue' AND COLUMN_NAME='discovery_basis'
);
SET @sql := IF(@exists=0,
  'ALTER TABLE water_protection_issue ADD COLUMN discovery_basis VARCHAR(100) NULL COMMENT ''discovery basis''',
  'SELECT 1');
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

-- Keep data_nature and is_demo consistent.
SET @exists := (
  SELECT COUNT(*) FROM information_schema.TABLE_CONSTRAINTS
  WHERE TABLE_SCHEMA=@db AND TABLE_NAME='water_protection_issue'
    AND CONSTRAINT_NAME='ck_wpi_demo_nature'
);
SET @sql := IF(@exists=0,
  'ALTER TABLE water_protection_issue ADD CONSTRAINT ck_wpi_demo_nature CHECK ((data_nature=''demo'' AND is_demo=1) OR (data_nature IN (''formal'',''platform_calc'') AND is_demo=0))',
  'SELECT 1');
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

-- e_case_evidence.rectification_round_id
SET @exists := (
  SELECT COUNT(*) FROM information_schema.COLUMNS
  WHERE TABLE_SCHEMA=@db AND TABLE_NAME='e_case_evidence' AND COLUMN_NAME='rectification_round_id'
);
SET @sql := IF(@exists=0,
  'ALTER TABLE e_case_evidence ADD COLUMN rectification_round_id INT NULL COMMENT ''rectification round id''',
  'SELECT 1');
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;
