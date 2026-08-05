-- Demo slim E01 env monitor tables (Phase B.1)
-- Created at runtime by esg_demo_api.ensure_e01_demo_tables() when absent.
-- Not full V2 DDL; Demo-only for homepage/workspace closed loop.

CREATE TABLE IF NOT EXISTS biz_env_monitor_point (
  id BIGINT UNSIGNED NOT NULL,
  project_id BIGINT UNSIGNED NOT NULL,
  section_id BIGINT UNSIGNED NULL,
  point_code VARCHAR(64) NOT NULL,
  point_name VARCHAR(200) NOT NULL,
  monitor_category VARCHAR(32) NOT NULL,
  location_desc VARCHAR(500) NULL,
  longitude DECIMAL(10,7) NULL,
  latitude DECIMAL(10,7) NULL,
  active_status VARCHAR(16) NOT NULL DEFAULT 'ACTIVE',
  risk_status VARCHAR(16) NOT NULL DEFAULT 'NORMAL',
  case_status VARCHAR(32) NULL,
  responsible_unit VARCHAR(200) NULL,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  is_deleted TINYINT UNSIGNED NOT NULL DEFAULT 0,
  PRIMARY KEY (id),
  UNIQUE KEY uk_demo_env_point (project_id, point_code)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='Demo E01 环境监测点（精简）';

CREATE TABLE IF NOT EXISTS biz_env_monitor_result (
  id BIGINT UNSIGNED NOT NULL,
  project_id BIGINT UNSIGNED NOT NULL,
  point_id BIGINT UNSIGNED NOT NULL,
  factor_code VARCHAR(64) NOT NULL,
  factor_name VARCHAR(128) NOT NULL,
  detected_value DECIMAL(18,4) NULL,
  limit_value DECIMAL(18,4) NULL,
  unit VARCHAR(32) NULL,
  judgement VARCHAR(20) NOT NULL,
  exceed_multiple DECIMAL(12,4) NULL,
  sampled_at DATETIME NULL,
  case_status VARCHAR(32) NULL,
  is_closed TINYINT UNSIGNED NOT NULL DEFAULT 0,
  rectification_note VARCHAR(500) NULL,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  is_deleted TINYINT UNSIGNED NOT NULL DEFAULT 0,
  PRIMARY KEY (id),
  KEY idx_demo_env_result_point (project_id, point_id, judgement)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='Demo E01 监测结果（精简）';
