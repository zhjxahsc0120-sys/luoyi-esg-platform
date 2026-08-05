-- 罗宜高速 ESG 数字化管理平台
-- Demo 数据库结构 V0.1
-- 用途：今日演示验证；不是生产库 DDL，不得直接在生产库执行。
-- 设计原则：引用现有 mdm_* 主数据；本脚本不创建、复制项目/组织/标段/工点主表。
-- 前置依赖：mdm_project、mdm_org、mdm_contract_section、mdm_work_point，以及现有环境/安全/审批/许可事实表。
-- 兼容：MySQL 8.0+；所有 project_id/section_id/work_point_id/responsible_org_id 均为逻辑引用，Demo 不加跨表外键。

SET NAMES utf8mb4;
SET time_zone = '+08:00';

-- ==================== E02 水土保持对象 ====================
CREATE TABLE IF NOT EXISTS biz_soil_disposal_site (
  id BIGINT UNSIGNED NOT NULL,
  project_id BIGINT UNSIGNED NOT NULL,
  section_id BIGINT UNSIGNED NULL,
  work_point_id BIGINT UNSIGNED NULL,
  object_code VARCHAR(64) NOT NULL,
  object_name VARCHAR(200) NOT NULL,
  location_desc VARCHAR(500) NULL,
  longitude DECIMAL(10,7) NULL,
  latitude DECIMAL(10,7) NULL,
  approved_flag TINYINT UNSIGNED NOT NULL DEFAULT 0,
  capacity_m3 DECIMAL(18,2) NULL,
  disposal_status VARCHAR(32) NOT NULL,
  control_measure VARCHAR(500) NULL,
  measure_rate DECIMAL(5,2) NULL,
  risk_status VARCHAR(16) NOT NULL DEFAULT 'NORMAL',
  responsible_org_id BIGINT UNSIGNED NULL,
  source_doc_ref VARCHAR(255) NULL,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  is_deleted TINYINT UNSIGNED NOT NULL DEFAULT 0,
  PRIMARY KEY (id), UNIQUE KEY uk_demo_soil_site (project_id, object_code),
  KEY idx_demo_soil_site_status (project_id, disposal_status, risk_status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='Demo E02 弃土弃渣场对象';

CREATE TABLE IF NOT EXISTS biz_temporary_land_use (
  id BIGINT UNSIGNED NOT NULL,
  project_id BIGINT UNSIGNED NOT NULL,
  section_id BIGINT UNSIGNED NULL,
  work_point_id BIGINT UNSIGNED NULL,
  object_code VARCHAR(64) NOT NULL,
  object_name VARCHAR(200) NOT NULL,
  land_type VARCHAR(64) NOT NULL,
  area_mu DECIMAL(18,2) NULL,
  approval_status VARCHAR(32) NOT NULL,
  restore_status VARCHAR(32) NOT NULL,
  measure_rate DECIMAL(5,2) NULL,
  risk_status VARCHAR(16) NOT NULL DEFAULT 'NORMAL',
  responsible_org_id BIGINT UNSIGNED NULL,
  source_doc_ref VARCHAR(255) NULL,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  is_deleted TINYINT UNSIGNED NOT NULL DEFAULT 0,
  PRIMARY KEY (id), UNIQUE KEY uk_demo_temp_land (project_id, object_code),
  KEY idx_demo_temp_land_status (project_id, approval_status, restore_status, risk_status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='Demo E02 临时用地对象';

CREATE TABLE IF NOT EXISTS biz_topsoil_stripping (
  id BIGINT UNSIGNED NOT NULL,
  project_id BIGINT UNSIGNED NOT NULL,
  section_id BIGINT UNSIGNED NULL,
  work_point_id BIGINT UNSIGNED NULL,
  object_code VARCHAR(64) NOT NULL,
  object_name VARCHAR(200) NOT NULL,
  planned_area_mu DECIMAL(18,2) NULL,
  completed_area_mu DECIMAL(18,2) NULL,
  completion_rate DECIMAL(5,2) NULL,
  storage_measure VARCHAR(500) NULL,
  current_status VARCHAR(32) NOT NULL,
  risk_status VARCHAR(16) NOT NULL DEFAULT 'NORMAL',
  responsible_org_id BIGINT UNSIGNED NULL,
  source_doc_ref VARCHAR(255) NULL,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  is_deleted TINYINT UNSIGNED NOT NULL DEFAULT 0,
  PRIMARY KEY (id), UNIQUE KEY uk_demo_topsoil (project_id, object_code),
  KEY idx_demo_topsoil_status (project_id, current_status, risk_status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='Demo E02 表土剥离对象';

CREATE TABLE IF NOT EXISTS biz_construction_slope (
  id BIGINT UNSIGNED NOT NULL,
  project_id BIGINT UNSIGNED NOT NULL,
  section_id BIGINT UNSIGNED NULL,
  work_point_id BIGINT UNSIGNED NULL,
  object_code VARCHAR(64) NOT NULL,
  object_name VARCHAR(200) NOT NULL,
  slope_type VARCHAR(64) NOT NULL,
  chainage VARCHAR(64) NULL,
  greening_rate DECIMAL(5,2) NULL,
  stability_status VARCHAR(32) NOT NULL,
  protection_measure VARCHAR(500) NULL,
  risk_status VARCHAR(16) NOT NULL DEFAULT 'NORMAL',
  responsible_org_id BIGINT UNSIGNED NULL,
  source_doc_ref VARCHAR(255) NULL,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  is_deleted TINYINT UNSIGNED NOT NULL DEFAULT 0,
  PRIMARY KEY (id), UNIQUE KEY uk_demo_slope (project_id, object_code),
  KEY idx_demo_slope_status (project_id, stability_status, risk_status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='Demo E02 施工边坡对象';

-- ==================== E03 生态对象 ====================
CREATE TABLE IF NOT EXISTS biz_ecological_sensitive_area (
  id BIGINT UNSIGNED NOT NULL,
  project_id BIGINT UNSIGNED NOT NULL,
  section_id BIGINT UNSIGNED NULL,
  object_code VARCHAR(64) NOT NULL,
  object_name VARCHAR(200) NOT NULL,
  sensitive_type VARCHAR(64) NOT NULL,
  location_desc VARCHAR(500) NULL,
  area_mu DECIMAL(18,2) NULL,
  protection_level VARCHAR(32) NULL,
  identification_status VARCHAR(32) NOT NULL,
  monitoring_status VARCHAR(32) NOT NULL,
  protection_measure VARCHAR(500) NULL,
  risk_status VARCHAR(16) NOT NULL DEFAULT 'NORMAL',
  responsible_org_id BIGINT UNSIGNED NULL,
  source_doc_ref VARCHAR(255) NULL,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  is_deleted TINYINT UNSIGNED NOT NULL DEFAULT 0,
  PRIMARY KEY (id), UNIQUE KEY uk_demo_sensitive_area (project_id, object_code),
  KEY idx_demo_sensitive_status (project_id, monitoring_status, risk_status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='Demo E03 生态敏感区';

CREATE TABLE IF NOT EXISTS biz_ecological_protection_object (
  id BIGINT UNSIGNED NOT NULL,
  project_id BIGINT UNSIGNED NOT NULL,
  section_id BIGINT UNSIGNED NULL,
  object_code VARCHAR(64) NOT NULL,
  object_name VARCHAR(200) NOT NULL,
  object_type VARCHAR(64) NOT NULL,
  importance_level VARCHAR(32) NULL,
  location_desc VARCHAR(500) NULL,
  identification_status VARCHAR(32) NOT NULL,
  inspection_status VARCHAR(32) NOT NULL,
  protection_measure VARCHAR(500) NULL,
  risk_status VARCHAR(16) NOT NULL DEFAULT 'NORMAL',
  responsible_org_id BIGINT UNSIGNED NULL,
  source_doc_ref VARCHAR(255) NULL,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  is_deleted TINYINT UNSIGNED NOT NULL DEFAULT 0,
  PRIMARY KEY (id), UNIQUE KEY uk_demo_eco_object (project_id, object_code),
  KEY idx_demo_eco_object_status (project_id, inspection_status, risk_status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='Demo E03 生态保护对象';

-- ==================== E04 文物保护 ====================
CREATE TABLE IF NOT EXISTS biz_cultural_relic_object (
  id BIGINT UNSIGNED NOT NULL,
  project_id BIGINT UNSIGNED NOT NULL,
  section_id BIGINT UNSIGNED NULL,
  relic_code VARCHAR(64) NOT NULL,
  relic_name VARCHAR(200) NOT NULL,
  relic_type VARCHAR(64) NULL,
  protection_level VARCHAR(32) NULL,
  location_desc VARCHAR(500) NULL,
  longitude DECIMAL(10,7) NULL,
  latitude DECIMAL(10,7) NULL,
  protection_scope VARCHAR(500) NULL,
  impact_analysis VARCHAR(1000) NULL,
  protection_measure VARCHAR(1000) NULL,
  survey_status VARCHAR(32) NOT NULL,
  measure_rate DECIMAL(5,2) NULL,
  responsible_org_id BIGINT UNSIGNED NULL,
  risk_status VARCHAR(16) NOT NULL DEFAULT 'NORMAL',
  source_doc_ref VARCHAR(255) NULL,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  is_deleted TINYINT UNSIGNED NOT NULL DEFAULT 0,
  PRIMARY KEY (id), UNIQUE KEY uk_demo_relic (project_id, relic_code),
  KEY idx_demo_relic_status (project_id, survey_status, risk_status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='Demo E04 文物保护对象';

-- ==================== S03 工资支付 ====================
CREATE TABLE IF NOT EXISTS biz_worker_payment_summary (
  id BIGINT UNSIGNED NOT NULL,
  project_id BIGINT UNSIGNED NOT NULL,
  section_id BIGINT UNSIGNED NULL,
  period_start DATE NOT NULL,
  period_end DATE NOT NULL,
  responsible_org_id BIGINT UNSIGNED NULL,
  worker_count INT UNSIGNED NOT NULL DEFAULT 0,
  payable_amount DECIMAL(18,2) NOT NULL DEFAULT 0,
  paid_amount DECIMAL(18,2) NOT NULL DEFAULT 0,
  payment_rate DECIMAL(5,2) NOT NULL DEFAULT 0,
  payment_status VARCHAR(32) NOT NULL,
  overdue_amount DECIMAL(18,2) NOT NULL DEFAULT 0,
  dispute_count INT UNSIGNED NOT NULL DEFAULT 0,
  risk_status VARCHAR(16) NOT NULL DEFAULT 'NORMAL',
  source_doc_ref VARCHAR(255) NULL,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  is_deleted TINYINT UNSIGNED NOT NULL DEFAULT 0,
  PRIMARY KEY (id), UNIQUE KEY uk_demo_payment_period (project_id, section_id, period_start, period_end),
  KEY idx_demo_payment_status (project_id, payment_status, risk_status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='Demo S03 工资支付周期汇总';

-- ==================== G02 夜间施工 ====================
CREATE TABLE IF NOT EXISTS biz_night_construction_record (
  id BIGINT UNSIGNED NOT NULL,
  project_id BIGINT UNSIGNED NOT NULL,
  section_id BIGINT UNSIGNED NULL,
  work_point_id BIGINT UNSIGNED NULL,
  record_code VARCHAR(64) NOT NULL,
  construction_date DATE NOT NULL,
  start_time DATETIME NOT NULL,
  end_time DATETIME NOT NULL,
  permit_id BIGINT UNSIGNED NULL,
  permit_status VARCHAR(32) NOT NULL,
  approval_status VARCHAR(32) NOT NULL,
  noise_measure VARCHAR(500) NULL,
  responsible_org_id BIGINT UNSIGNED NULL,
  risk_status VARCHAR(16) NOT NULL DEFAULT 'NORMAL',
  source_doc_ref VARCHAR(255) NULL,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  is_deleted TINYINT UNSIGNED NOT NULL DEFAULT 0,
  PRIMARY KEY (id), UNIQUE KEY uk_demo_night_record (project_id, record_code),
  KEY idx_demo_night_status (project_id, construction_date, permit_status, risk_status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='Demo G02 夜间施工记录';

-- ==================== G03 设计变更 ====================
CREATE TABLE IF NOT EXISTS biz_design_change (
  id BIGINT UNSIGNED NOT NULL,
  project_id BIGINT UNSIGNED NOT NULL,
  section_id BIGINT UNSIGNED NULL,
  work_point_id BIGINT UNSIGNED NULL,
  change_code VARCHAR(64) NOT NULL,
  change_type VARCHAR(64) NOT NULL,
  change_name VARCHAR(255) NOT NULL,
  location_desc VARCHAR(500) NULL,
  change_reason VARCHAR(1000) NULL,
  apply_date DATE NOT NULL,
  approve_status VARCHAR(32) NOT NULL,
  approve_date DATE NULL,
  implementation_status VARCHAR(32) NOT NULL,
  attachment_status VARCHAR(32) NOT NULL,
  responsible_org_id BIGINT UNSIGNED NULL,
  risk_status VARCHAR(16) NOT NULL DEFAULT 'NORMAL',
  source_doc_ref VARCHAR(255) NULL,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  is_deleted TINYINT UNSIGNED NOT NULL DEFAULT 0,
  PRIMARY KEY (id), UNIQUE KEY uk_demo_design_change (project_id, change_code),
  KEY idx_demo_design_change_status (project_id, approve_status, implementation_status, risk_status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='Demo G03 设计变更';

-- ==================== G04 内控廉洁 ====================
CREATE TABLE IF NOT EXISTS biz_internal_control_issue (
  id BIGINT UNSIGNED NOT NULL,
  project_id BIGINT UNSIGNED NOT NULL,
  section_id BIGINT UNSIGNED NULL,
  issue_code VARCHAR(64) NOT NULL,
  issue_type VARCHAR(64) NOT NULL,
  issue_level VARCHAR(16) NOT NULL,
  issue_description VARCHAR(1000) NOT NULL,
  found_at DATETIME NOT NULL,
  responsible_org_id BIGINT UNSIGNED NULL,
  current_status VARCHAR(32) NOT NULL,
  deadline DATE NULL,
  closed_at DATE NULL,
  recurrence_flag TINYINT UNSIGNED NOT NULL DEFAULT 0,
  evidence_status VARCHAR(32) NOT NULL,
  risk_status VARCHAR(16) NOT NULL DEFAULT 'NORMAL',
  source_doc_ref VARCHAR(255) NULL,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  is_deleted TINYINT UNSIGNED NOT NULL DEFAULT 0,
  PRIMARY KEY (id), UNIQUE KEY uk_demo_control_issue (project_id, issue_code),
  KEY idx_demo_control_issue_status (project_id, current_status, issue_level, risk_status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='Demo G04 内控廉洁问题';

-- ==================== 风险预警层 ====================
CREATE TABLE IF NOT EXISTS cfg_warning_rule (
  id BIGINT UNSIGNED NOT NULL,
  rule_code VARCHAR(64) NOT NULL,
  kpi_key VARCHAR(16) NOT NULL,
  domain_code VARCHAR(8) NOT NULL,
  rule_name VARCHAR(255) NOT NULL,
  trigger_condition_json JSON NOT NULL,
  warning_level VARCHAR(16) NOT NULL,
  version_no VARCHAR(32) NOT NULL,
  enabled TINYINT UNSIGNED NOT NULL DEFAULT 1,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (id), UNIQUE KEY uk_demo_warning_rule (rule_code, version_no),
  KEY idx_demo_warning_rule_kpi (kpi_key, enabled)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='Demo 风险规则';

CREATE TABLE IF NOT EXISTS biz_risk_warning (
  id BIGINT UNSIGNED NOT NULL,
  warning_code VARCHAR(64) NOT NULL,
  project_id BIGINT UNSIGNED NOT NULL,
  domain_code VARCHAR(8) NOT NULL,
  kpi_key VARCHAR(16) NOT NULL,
  object_type VARCHAR(64) NOT NULL,
  object_id BIGINT UNSIGNED NOT NULL,
  object_name_snapshot VARCHAR(255) NOT NULL,
  warning_level VARCHAR(16) NOT NULL,
  warning_reason VARCHAR(1000) NOT NULL,
  trigger_time DATETIME NOT NULL,
  responsible_org_id BIGINT UNSIGNED NULL,
  responsible_unit VARCHAR(255) NULL,
  status VARCHAR(32) NOT NULL,
  source_rule_id BIGINT UNSIGNED NULL,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (id), UNIQUE KEY uk_demo_warning_code (warning_code),
  KEY idx_demo_warning_list (project_id, status, warning_level, kpi_key),
  KEY idx_demo_warning_object (object_type, object_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='Demo ESG 风险预警';

CREATE TABLE IF NOT EXISTS biz_risk_disposal (
  id BIGINT UNSIGNED NOT NULL,
  warning_id BIGINT UNSIGNED NOT NULL,
  project_id BIGINT UNSIGNED NOT NULL,
  responsible_unit VARCHAR(255) NOT NULL,
  action_content VARCHAR(1000) NULL,
  handler VARCHAR(100) NULL,
  disposal_status VARCHAR(32) NOT NULL,
  disposal_time DATETIME NULL,
  close_time DATETIME NULL,
  close_evidence VARCHAR(255) NULL,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (id), KEY idx_demo_disposal_warning (warning_id, disposal_status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='Demo ESG 风险处置';

-- ==================== Demo 结果适配层 ====================
-- 生产方案应映射到 fact_indicator_result/fact_indicator_detail_ref；Demo 为避免改动现有结果表，使用 demo 前缀适配。
CREATE TABLE IF NOT EXISTS esg_demo_indicator_result (
  id BIGINT UNSIGNED NOT NULL,
  project_id BIGINT UNSIGNED NOT NULL,
  period_end DATE NOT NULL,
  kpi_key VARCHAR(16) NOT NULL,
  kpi_name VARCHAR(200) NOT NULL,
  domain_code VARCHAR(8) NOT NULL,
  value_decimal DECIMAL(24,8) NULL,
  value_text VARCHAR(500) NULL,
  unit VARCHAR(32) NOT NULL,
  hint VARCHAR(500) NULL,
  risk_level VARCHAR(16) NOT NULL,
  source_summary VARCHAR(1000) NULL,
  rule_version VARCHAR(32) NOT NULL,
  result_status VARCHAR(32) NOT NULL DEFAULT 'PUBLISHED',
  calculated_at DATETIME NOT NULL,
  published_at DATETIME NULL,
  PRIMARY KEY (id), UNIQUE KEY uk_demo_result (project_id, period_end, kpi_key),
  KEY idx_demo_result_latest (project_id, period_end, kpi_key, result_status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='Demo 指标结果适配层';

CREATE TABLE IF NOT EXISTS esg_demo_indicator_detail (
  id BIGINT UNSIGNED NOT NULL,
  result_id BIGINT UNSIGNED NOT NULL,
  project_id BIGINT UNSIGNED NOT NULL,
  kpi_key VARCHAR(16) NOT NULL,
  object_type VARCHAR(64) NOT NULL,
  object_id BIGINT UNSIGNED NOT NULL,
  object_name VARCHAR(255) NOT NULL,
  metric_label VARCHAR(100) NOT NULL,
  metric_value VARCHAR(255) NULL,
  metric_unit VARCHAR(32) NULL,
  status VARCHAR(32) NULL,
  risk_level VARCHAR(16) NULL,
  detail_json JSON NULL,
  PRIMARY KEY (id), KEY idx_demo_detail_kpi (project_id, kpi_key, object_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='Demo 指标对象明细';

-- ==================== Demo 查询视图 ====================
CREATE OR REPLACE VIEW v_esg_demo_dashboard_kpis AS
SELECT project_id, kpi_key AS `key`, kpi_name AS `name`,
       COALESCE(value_decimal, value_text) AS `value`, unit, hint, risk_level AS riskLevel,
       period_end
  FROM esg_demo_indicator_result
 WHERE result_status = 'PUBLISHED';

CREATE OR REPLACE VIEW v_esg_demo_risk_list AS
SELECT id, warning_code, project_id, warning_level AS level, domain_code AS domain,
       kpi_key AS kpiKey, object_id AS objectId, object_name_snapshot AS objectName,
       responsible_unit AS responsibleUnit, status, warning_reason AS reason, trigger_time AS triggerTime
  FROM biz_risk_warning;

CREATE OR REPLACE VIEW v_esg_demo_kpi_detail AS
SELECT result_id, project_id, kpi_key, object_type AS objectType, object_id AS objectId,
       object_name AS objectName, metric_label AS metricLabel, metric_value AS metricValue,
       metric_unit AS metricUnit, status, risk_level AS riskLevel, detail_json AS detailJson
  FROM esg_demo_indicator_detail;
