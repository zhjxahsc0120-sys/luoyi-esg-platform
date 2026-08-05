-- 罗宜高速 ESG 智能体资料自动解析入库数据库扩展 Schema V0.1
-- 说明：
-- 1. 本 SQL 是面向智能入库能力的扩展草案，不直接替代 server/schema.sql。
-- 2. SQLite 原型可将 BIGINT/JSON/DATETIME 视为兼容类型；正式 MySQL 落地时建议补充外键、索引、枚举字典和分区策略。

CREATE TABLE IF NOT EXISTS file_asset (
  id BIGINT PRIMARY KEY,
  file_code VARCHAR(64) NOT NULL UNIQUE,
  original_name VARCHAR(255) NOT NULL,
  file_ext VARCHAR(20),
  mime_type VARCHAR(100),
  file_size BIGINT,
  storage_path VARCHAR(500) NOT NULL,
  storage_bucket VARCHAR(100),
  sha256_hash VARCHAR(128) NOT NULL,
  upload_source VARCHAR(50) NOT NULL,
  uploader_id BIGINT,
  uploader_name VARCHAR(100),
  upload_time DATETIME NOT NULL,
  duplicate_status VARCHAR(30) DEFAULT 'UNKNOWN',
  duplicate_of_file_id BIGINT,
  parse_status VARCHAR(30) DEFAULT 'PENDING',
  is_deleted TINYINT DEFAULT 0,
  created_at DATETIME NOT NULL,
  updated_at DATETIME NOT NULL
);

CREATE TABLE IF NOT EXISTS ai_parse_job (
  id BIGINT PRIMARY KEY,
  job_code VARCHAR(64) NOT NULL UNIQUE,
  file_id BIGINT NOT NULL,
  job_status VARCHAR(30) NOT NULL,
  parse_engine VARCHAR(100),
  model_name VARCHAR(100),
  rule_version VARCHAR(50),
  started_at DATETIME,
  finished_at DATETIME,
  duration_ms INT,
  confidence DECIMAL(5,2),
  error_code VARCHAR(50),
  error_message TEXT,
  retry_count INT DEFAULT 0,
  raw_result_json JSON,
  created_at DATETIME NOT NULL,
  updated_at DATETIME NOT NULL
);

CREATE TABLE IF NOT EXISTS ai_parse_field_result (
  id BIGINT PRIMARY KEY,
  parse_job_id BIGINT NOT NULL,
  field_key VARCHAR(100) NOT NULL,
  field_name VARCHAR(100) NOT NULL,
  field_value TEXT,
  normalized_value TEXT,
  value_type VARCHAR(30),
  confidence DECIMAL(5,2),
  source_page INT,
  source_location VARCHAR(255),
  confirm_status VARCHAR(30) DEFAULT 'PENDING',
  confirmed_value TEXT,
  confirmed_by BIGINT,
  confirmed_at DATETIME,
  created_at DATETIME NOT NULL
);

CREATE TABLE IF NOT EXISTS ai_field_mapping_rule (
  id BIGINT PRIMARY KEY,
  document_type VARCHAR(100) NOT NULL,
  field_key VARCHAR(100) NOT NULL,
  field_name VARCHAR(100) NOT NULL,
  target_table VARCHAR(100) NOT NULL,
  target_column VARCHAR(100) NOT NULL,
  value_type VARCHAR(30),
  required TINYINT DEFAULT 0,
  normalize_rule VARCHAR(255),
  enabled TINYINT DEFAULT 1,
  created_at DATETIME NOT NULL,
  updated_at DATETIME NOT NULL
);

CREATE TABLE IF NOT EXISTS document_version (
  id BIGINT PRIMARY KEY,
  document_id BIGINT NOT NULL,
  file_id BIGINT NOT NULL,
  version_no VARCHAR(20) NOT NULL,
  version_desc VARCHAR(500),
  change_type VARCHAR(50),
  uploaded_by BIGINT,
  uploaded_at DATETIME NOT NULL,
  is_current TINYINT DEFAULT 0,
  created_at DATETIME NOT NULL
);

CREATE TABLE IF NOT EXISTS document_task_relation (
  id BIGINT PRIMARY KEY,
  document_id BIGINT NOT NULL,
  task_id VARCHAR(64) NOT NULL,
  relation_type VARCHAR(30) NOT NULL,
  relation_status VARCHAR(30) NOT NULL,
  match_score DECIMAL(5,2),
  linked_by BIGINT,
  linked_at DATETIME,
  source VARCHAR(50),
  created_at DATETIME NOT NULL
);

CREATE TABLE IF NOT EXISTS task_match_candidate (
  id BIGINT PRIMARY KEY,
  parse_job_id BIGINT NOT NULL,
  file_id BIGINT NOT NULL,
  document_id BIGINT,
  task_id VARCHAR(64) NOT NULL,
  task_name VARCHAR(255),
  module_code VARCHAR(10),
  match_score DECIMAL(5,2) NOT NULL,
  match_reason TEXT,
  reuse_count INT DEFAULT 0,
  candidate_status VARCHAR(30) DEFAULT 'PENDING',
  confirmed_by BIGINT,
  confirmed_at DATETIME,
  created_at DATETIME NOT NULL
);

CREATE TABLE IF NOT EXISTS manual_confirmation_log (
  id BIGINT PRIMARY KEY,
  target_type VARCHAR(50) NOT NULL,
  target_id BIGINT NOT NULL,
  action_type VARCHAR(50) NOT NULL,
  before_json JSON,
  after_json JSON,
  comment VARCHAR(500),
  operator_id BIGINT,
  operator_name VARCHAR(100),
  operated_at DATETIME NOT NULL
);

CREATE TABLE IF NOT EXISTS deduplication_record (
  id BIGINT PRIMARY KEY,
  file_id BIGINT NOT NULL,
  matched_file_id BIGINT,
  matched_document_id BIGINT,
  match_type VARCHAR(30) NOT NULL,
  match_score DECIMAL(5,2),
  hash_equal TINYINT DEFAULT 0,
  name_similar TINYINT DEFAULT 0,
  content_similar TINYINT DEFAULT 0,
  decision_status VARCHAR(30) DEFAULT 'PENDING',
  decision_by BIGINT,
  decision_at DATETIME,
  created_at DATETIME NOT NULL
);

CREATE TABLE IF NOT EXISTS audit_log (
  id BIGINT PRIMARY KEY,
  module_name VARCHAR(100) NOT NULL,
  entity_type VARCHAR(100) NOT NULL,
  entity_id VARCHAR(100) NOT NULL,
  action VARCHAR(100) NOT NULL,
  action_desc VARCHAR(500),
  operator_id BIGINT,
  operator_name VARCHAR(100),
  ip_address VARCHAR(50),
  user_agent VARCHAR(500),
  created_at DATETIME NOT NULL
);

-- 正式 MySQL 建议索引
-- CREATE INDEX idx_file_asset_hash ON file_asset(sha256_hash);
-- CREATE INDEX idx_ai_parse_job_file ON ai_parse_job(file_id, job_status);
-- CREATE INDEX idx_ai_parse_field_job ON ai_parse_field_result(parse_job_id, field_key);
-- CREATE INDEX idx_mapping_doc_field ON ai_field_mapping_rule(document_type, field_key, enabled);
-- CREATE INDEX idx_task_match_job ON task_match_candidate(parse_job_id, candidate_status);
-- CREATE INDEX idx_doc_task_relation_task ON document_task_relation(task_id, relation_status);
