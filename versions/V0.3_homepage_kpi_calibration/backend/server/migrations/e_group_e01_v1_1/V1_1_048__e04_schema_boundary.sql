-- ============================================================================
-- V1_1_048__e04_schema_boundary.sql
-- E04 P1 Schema 闸：边界配置 / 核算批次 / 因子快照 / 显式有效性 / 证据
-- 权威依据：E04_Trae实施任务单_P1_V1.0 + E04_累计碳排放工作台设计说明_B方案_V1.0冻结稿
-- 增量、幂等；不修改历史建库脚本
-- ============================================================================

SET @db := DATABASE();

-- --------------------------------------------------------------------------
-- 1. carbon_accounting_boundary — 边界配置表（按来源维度）
--    生命周期：DRAFT → CANDIDATE → ACTIVE → RETIRED（§5.2.1）
-- --------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS carbon_accounting_boundary (
  id BIGINT AUTO_INCREMENT PRIMARY KEY,
  boundary_version VARCHAR(80) NOT NULL COMMENT '边界版本标识，如 DEMO-BOUND-E04-20260718',
  boundary_label VARCHAR(200) NOT NULL COMMENT '边界版本名称',
  boundary_status VARCHAR(30) NOT NULL DEFAULT 'DRAFT' COMMENT 'DRAFT | CANDIDATE | ACTIVE | RETIRED',
  source_code VARCHAR(30) NOT NULL COMMENT '来源代码：diesel/electricity/material/transport/equipment',
  source_label VARCHAR(100) NULL COMMENT '来源名称',
  in_boundary TINYINT(1) NOT NULL DEFAULT 1 COMMENT '是否计入当前边界',
  sort_order INT NOT NULL DEFAULT 0 COMMENT '展示排序',
  description TEXT NULL COMMENT '生效说明',
  is_demo TINYINT(1) NOT NULL DEFAULT 0 COMMENT '演示数据标识',
  data_nature VARCHAR(30) NOT NULL DEFAULT 'formal' COMMENT 'formal | demo | platform_calc',
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  UNIQUE KEY uk_boundary_version_source(boundary_version, source_code),
  INDEX idx_boundary_status(boundary_status),
  INDEX idx_boundary_version(boundary_version),
  INDEX idx_boundary_nature(data_nature),
  CONSTRAINT ck_boundary_status CHECK (boundary_status IN ('DRAFT','CANDIDATE','ACTIVE','RETIRED'))
) ENGINE=InnoDB COMMENT='碳排放核算边界配置（按来源维度，§5.2）';

-- --------------------------------------------------------------------------
-- 2. carbon_accounting_batch — 核算批次 + current 指针
-- --------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS carbon_accounting_batch (
  id BIGINT AUTO_INCREMENT PRIMARY KEY,
  batch_code VARCHAR(80) NOT NULL UNIQUE COMMENT '批次代码',
  batch_label VARCHAR(200) NOT NULL COMMENT '批次名称',
  boundary_version VARCHAR(80) NOT NULL COMMENT '采用的边界版本（须 ACTIVE）',
  statistics_as_of DATE NOT NULL COMMENT '统计截止日期',
  period_start VARCHAR(7) NULL COMMENT '核算起始月份 YYYY-MM',
  period_end VARCHAR(7) NULL COMMENT '核算结束月份 YYYY-MM',
  data_nature VARCHAR(30) NOT NULL DEFAULT 'demo' COMMENT 'formal | demo',
  is_current TINYINT(1) NOT NULL DEFAULT 0 COMMENT '当前生效批次指针',
  is_demo TINYINT(1) NOT NULL DEFAULT 0,
  verification_status VARCHAR(40) NOT NULL DEFAULT 'PENDING' COMMENT 'PENDING | VERIFIED',
  boundary_snapshot_note TEXT NULL COMMENT '批次创建时边界快照说明',
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  INDEX idx_batch_current(is_current, data_nature),
  INDEX idx_batch_boundary(boundary_version),
  INDEX idx_batch_nature(data_nature)
  -- FK 等价约束说明：boundary_version 引用 carbon_accounting_boundary.boundary_version
  -- 因 boundary_version 在 carbon_accounting_boundary 中为复合唯一键
  -- (uk_boundary_version_source) 的一部分，非独立唯一键，MySQL 不支持直接
  -- 创建 FOREIGN KEY；应用层 / API 层负责校验引用完整性（§5.2）
) ENGINE=InnoDB COMMENT='碳排放核算批次（§5.3）';

-- --------------------------------------------------------------------------
-- 3. carbon_emission_factor_snapshot — 因子不可变快照（§5.4）
-- --------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS carbon_emission_factor_snapshot (
  id BIGINT AUTO_INCREMENT PRIMARY KEY,
  snapshot_code VARCHAR(80) NOT NULL UNIQUE COMMENT '快照代码',
  factor_id BIGINT NOT NULL COMMENT '关联 carbon_emission_factor.id',
  factor_code VARCHAR(60) NOT NULL COMMENT '因子代码',
  factor_name VARCHAR(160) NOT NULL COMMENT '因子名称',
  factor_value DECIMAL(24,12) NOT NULL COMMENT '因子数值',
  factor_unit VARCHAR(80) NOT NULL COMMENT '因子单位',
  numerator_unit VARCHAR(30) NULL COMMENT '分子单位',
  denominator_unit VARCHAR(30) NULL COMMENT '分母单位',
  activity_unit VARCHAR(30) NULL COMMENT '活动单位',
  conversion_factor DECIMAL(24,12) NULL COMMENT '单位换算系数',
  conversion_path VARCHAR(255) NULL COMMENT '换算路径',
  factor_version VARCHAR(80) NOT NULL COMMENT '因子版本',
  factor_source VARCHAR(255) NOT NULL COMMENT '因子来源文件/机构',
  gwp_version VARCHAR(80) NULL COMMENT 'GWP 或折算依据版本',
  precision_rule VARCHAR(100) NULL COMMENT '计算精度与舍入规则引用',
  effective_from DATE NULL COMMENT '因子生效起始',
  effective_until DATE NULL COMMENT '因子生效截止',
  snapshot_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '快照时间',
  data_nature VARCHAR(30) NOT NULL COMMENT 'formal | demo',
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  INDEX idx_factor_snapshot_factor(factor_id),
  INDEX idx_factor_snapshot_code(snapshot_code),
  CONSTRAINT fk_factor_snapshot_factor FOREIGN KEY (factor_id)
    REFERENCES carbon_emission_factor(id)
    ON UPDATE CASCADE
) ENGINE=InnoDB COMMENT='碳排放因子不可变快照（行级，§5.4）';

-- --------------------------------------------------------------------------
-- 4. carbon_emission_activity 扩展字段
--    is_demo / effective_status / evidence_status / boundary_version /
--    accounting_batch_id / is_current / factor_snapshot_id(s)
-- --------------------------------------------------------------------------

-- 4a. is_demo
SET @exists := (
  SELECT COUNT(*) FROM information_schema.COLUMNS
  WHERE TABLE_SCHEMA=@db AND TABLE_NAME='carbon_emission_activity' AND COLUMN_NAME='is_demo'
);
SET @sql := IF(@exists=0,
  'ALTER TABLE carbon_emission_activity ADD COLUMN is_demo TINYINT(1) NOT NULL DEFAULT 0 COMMENT ''demo data flag''',
  'SELECT 1');
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

-- 4b. effective_status（禁止 IFNULL 默认；NULL=待核实）
SET @exists := (
  SELECT COUNT(*) FROM information_schema.COLUMNS
  WHERE TABLE_SCHEMA=@db AND TABLE_NAME='carbon_emission_activity' AND COLUMN_NAME='effective_status'
);
SET @sql := IF(@exists=0,
  'ALTER TABLE carbon_emission_activity ADD COLUMN effective_status VARCHAR(30) NULL COMMENT ''EFFECTIVE | INEFFECTIVE | NULL=待核实；正式KPI禁止IFNULL默认''',
  'SELECT 1');
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

-- 4c. evidence_status
SET @exists := (
  SELECT COUNT(*) FROM information_schema.COLUMNS
  WHERE TABLE_SCHEMA=@db AND TABLE_NAME='carbon_emission_activity' AND COLUMN_NAME='evidence_status'
);
SET @sql := IF(@exists=0,
  'ALTER TABLE carbon_emission_activity ADD COLUMN evidence_status VARCHAR(40) NOT NULL DEFAULT ''MISSING'' COMMENT ''MISSING | PENDING | VERIFIED；禁止占位文件冒充''',
  'SELECT 1');
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

-- 4d. boundary_version（审计冗余，权威过滤以批次边界为准）
SET @exists := (
  SELECT COUNT(*) FROM information_schema.COLUMNS
  WHERE TABLE_SCHEMA=@db AND TABLE_NAME='carbon_emission_activity' AND COLUMN_NAME='boundary_version'
);
SET @sql := IF(@exists=0,
  'ALTER TABLE carbon_emission_activity ADD COLUMN boundary_version VARCHAR(80) NULL COMMENT ''写入时边界版本（审计冗余）''',
  'SELECT 1');
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

-- 4e. accounting_batch_id
SET @exists := (
  SELECT COUNT(*) FROM information_schema.COLUMNS
  WHERE TABLE_SCHEMA=@db AND TABLE_NAME='carbon_emission_activity' AND COLUMN_NAME='accounting_batch_id'
);
SET @sql := IF(@exists=0,
  'ALTER TABLE carbon_emission_activity ADD COLUMN accounting_batch_id BIGINT NULL COMMENT ''核算批次ID''',
  'SELECT 1');
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

-- 4f. is_current（版本控制：1=当前有效，0=被替代/作废）
SET @exists := (
  SELECT COUNT(*) FROM information_schema.COLUMNS
  WHERE TABLE_SCHEMA=@db AND TABLE_NAME='carbon_emission_activity' AND COLUMN_NAME='is_current'
);
SET @sql := IF(@exists=0,
  'ALTER TABLE carbon_emission_activity ADD COLUMN is_current TINYINT(1) NOT NULL DEFAULT 1 COMMENT ''当前有效标志；0=被替代/作废''',
  'SELECT 1');
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

-- 4g. factor_snapshot_id（按来源维度，每行四个来源各一个快照）
SET @exists := (
  SELECT COUNT(*) FROM information_schema.COLUMNS
  WHERE TABLE_SCHEMA=@db AND TABLE_NAME='carbon_emission_activity' AND COLUMN_NAME='diesel_factor_snapshot_id'
);
SET @sql := IF(@exists=0,
  'ALTER TABLE carbon_emission_activity ADD COLUMN diesel_factor_snapshot_id BIGINT NULL COMMENT ''施工用油因子快照ID''',
  'SELECT 1');
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

SET @exists := (
  SELECT COUNT(*) FROM information_schema.COLUMNS
  WHERE TABLE_SCHEMA=@db AND TABLE_NAME='carbon_emission_activity' AND COLUMN_NAME='electricity_factor_snapshot_id'
);
SET @sql := IF(@exists=0,
  'ALTER TABLE carbon_emission_activity ADD COLUMN electricity_factor_snapshot_id BIGINT NULL COMMENT ''施工用电因子快照ID''',
  'SELECT 1');
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

SET @exists := (
  SELECT COUNT(*) FROM information_schema.COLUMNS
  WHERE TABLE_SCHEMA=@db AND TABLE_NAME='carbon_emission_activity' AND COLUMN_NAME='material_factor_snapshot_id'
);
SET @sql := IF(@exists=0,
  'ALTER TABLE carbon_emission_activity ADD COLUMN material_factor_snapshot_id BIGINT NULL COMMENT ''主要材料因子快照ID（汇总引用）''',
  'SELECT 1');
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

SET @exists := (
  SELECT COUNT(*) FROM information_schema.COLUMNS
  WHERE TABLE_SCHEMA=@db AND TABLE_NAME='carbon_emission_activity' AND COLUMN_NAME='transport_factor_snapshot_id'
);
SET @sql := IF(@exists=0,
  'ALTER TABLE carbon_emission_activity ADD COLUMN transport_factor_snapshot_id BIGINT NULL COMMENT ''施工运输因子快照ID''',
  'SELECT 1');
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

-- --------------------------------------------------------------------------
-- 5. carbon_material_usage 扩展字段
-- --------------------------------------------------------------------------

-- 5a. is_demo
SET @exists := (
  SELECT COUNT(*) FROM information_schema.COLUMNS
  WHERE TABLE_SCHEMA=@db AND TABLE_NAME='carbon_material_usage' AND COLUMN_NAME='is_demo'
);
SET @sql := IF(@exists=0,
  'ALTER TABLE carbon_material_usage ADD COLUMN is_demo TINYINT(1) NOT NULL DEFAULT 0 COMMENT ''demo data flag''',
  'SELECT 1');
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

-- 5b. effective_status
SET @exists := (
  SELECT COUNT(*) FROM information_schema.COLUMNS
  WHERE TABLE_SCHEMA=@db AND TABLE_NAME='carbon_material_usage' AND COLUMN_NAME='effective_status'
);
SET @sql := IF(@exists=0,
  'ALTER TABLE carbon_material_usage ADD COLUMN effective_status VARCHAR(30) NULL COMMENT ''EFFECTIVE | INEFFECTIVE | NULL=待核实''',
  'SELECT 1');
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

-- 5c. evidence_status
SET @exists := (
  SELECT COUNT(*) FROM information_schema.COLUMNS
  WHERE TABLE_SCHEMA=@db AND TABLE_NAME='carbon_material_usage' AND COLUMN_NAME='evidence_status'
);
SET @sql := IF(@exists=0,
  'ALTER TABLE carbon_material_usage ADD COLUMN evidence_status VARCHAR(40) NOT NULL DEFAULT ''MISSING'' COMMENT ''MISSING | PENDING | VERIFIED''',
  'SELECT 1');
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

-- 5d. factor_snapshot_id
SET @exists := (
  SELECT COUNT(*) FROM information_schema.COLUMNS
  WHERE TABLE_SCHEMA=@db AND TABLE_NAME='carbon_material_usage' AND COLUMN_NAME='factor_snapshot_id'
);
SET @sql := IF(@exists=0,
  'ALTER TABLE carbon_material_usage ADD COLUMN factor_snapshot_id BIGINT NULL COMMENT ''材料因子快照ID''',
  'SELECT 1');
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

-- 5e. accounting_batch_id
SET @exists := (
  SELECT COUNT(*) FROM information_schema.COLUMNS
  WHERE TABLE_SCHEMA=@db AND TABLE_NAME='carbon_material_usage' AND COLUMN_NAME='accounting_batch_id'
);
SET @sql := IF(@exists=0,
  'ALTER TABLE carbon_material_usage ADD COLUMN accounting_batch_id BIGINT NULL COMMENT ''核算批次ID''',
  'SELECT 1');
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

-- 5f. is_current
SET @exists := (
  SELECT COUNT(*) FROM information_schema.COLUMNS
  WHERE TABLE_SCHEMA=@db AND TABLE_NAME='carbon_material_usage' AND COLUMN_NAME='is_current'
);
SET @sql := IF(@exists=0,
  'ALTER TABLE carbon_material_usage ADD COLUMN is_current TINYINT(1) NOT NULL DEFAULT 1 COMMENT ''当前有效标志''',
  'SELECT 1');
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

-- --------------------------------------------------------------------------
-- 5g. 数据修复：同步现有 is_demo 与 data_nature（在 CHECK 约束前）
--     现有演示数据 data_nature='demo' 但 is_demo 默认为 0，需先同步再添加 CHECK
-- --------------------------------------------------------------------------
UPDATE carbon_emission_activity
SET is_demo = 1
WHERE data_nature = 'demo' AND is_demo = 0;

UPDATE carbon_emission_activity
SET is_demo = 0
WHERE data_nature IN ('formal', 'platform_calc') AND is_demo = 1;

UPDATE carbon_material_usage
SET is_demo = 1
WHERE data_nature = 'demo' AND is_demo = 0;

UPDATE carbon_material_usage
SET is_demo = 0
WHERE data_nature IN ('formal', 'platform_calc') AND is_demo = 1;

-- --------------------------------------------------------------------------
-- 6. CHECK 约束：is_demo 与 data_nature 一致性
-- --------------------------------------------------------------------------

-- carbon_emission_activity
SET @exists := (
  SELECT COUNT(*) FROM information_schema.TABLE_CONSTRAINTS
  WHERE TABLE_SCHEMA=@db AND TABLE_NAME='carbon_emission_activity'
    AND CONSTRAINT_NAME='ck_cea_demo_nature'
);
SET @sql := IF(@exists=0,
  'ALTER TABLE carbon_emission_activity ADD CONSTRAINT ck_cea_demo_nature CHECK ((data_nature IS NULL) OR (data_nature=''demo'' AND is_demo=1) OR (data_nature IN (''formal'',''platform_calc'') AND is_demo=0))',
  'SELECT 1');
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;

-- carbon_material_usage
SET @exists := (
  SELECT COUNT(*) FROM information_schema.TABLE_CONSTRAINTS
  WHERE TABLE_SCHEMA=@db AND TABLE_NAME='carbon_material_usage'
    AND CONSTRAINT_NAME='ck_cmu_demo_nature'
);
SET @sql := IF(@exists=0,
  'ALTER TABLE carbon_material_usage ADD CONSTRAINT ck_cmu_demo_nature CHECK ((data_nature IS NULL) OR (data_nature=''demo'' AND is_demo=1) OR (data_nature IN (''formal'',''platform_calc'') AND is_demo=0))',
  'SELECT 1');
PREPARE stmt FROM @sql; EXECUTE stmt; DEALLOCATE PREPARE stmt;