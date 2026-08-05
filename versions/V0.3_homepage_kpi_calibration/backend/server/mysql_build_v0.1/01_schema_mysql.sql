-- 罗宜高速 ESG MySQL 建库脚本 V0.1
-- Target: MySQL 8.0+

CREATE DATABASE IF NOT EXISTS luoyi_esg
  DEFAULT CHARACTER SET utf8mb4
  DEFAULT COLLATE utf8mb4_0900_ai_ci;

USE luoyi_esg;

SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

-- 1. 基础字典
CREATE TABLE IF NOT EXISTS dict_esg_module (
  module_code VARCHAR(10) PRIMARY KEY COMMENT 'E/S/G',
  module_name VARCHAR(50) NOT NULL COMMENT '模块名称',
  display_order INT NOT NULL,
  enabled TINYINT NOT NULL DEFAULT 1,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB COMMENT='ESG模块字典';

CREATE TABLE IF NOT EXISTS dict_document_type (
  id BIGINT PRIMARY KEY,
  type_code VARCHAR(64) NOT NULL UNIQUE,
  type_name VARCHAR(100) NOT NULL,
  module_code VARCHAR(10),
  enabled TINYINT NOT NULL DEFAULT 1,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  INDEX idx_doc_type_module(module_code)
) ENGINE=InnoDB COMMENT='资料类型字典';

CREATE TABLE IF NOT EXISTS org_unit (
  id BIGINT PRIMARY KEY,
  org_code VARCHAR(64) NOT NULL UNIQUE,
  org_name VARCHAR(100) NOT NULL,
  parent_id BIGINT,
  org_type VARCHAR(50),
  enabled TINYINT NOT NULL DEFAULT 1,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB COMMENT='组织机构';

CREATE TABLE IF NOT EXISTS user_account (
  id BIGINT PRIMARY KEY,
  username VARCHAR(80) NOT NULL UNIQUE,
  display_name VARCHAR(100) NOT NULL,
  org_id BIGINT,
  role_name VARCHAR(100),
  enabled TINYINT NOT NULL DEFAULT 1,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  INDEX idx_user_org(org_id)
) ENGINE=InnoDB COMMENT='用户账号';

-- 2. 上传任务
CREATE TABLE IF NOT EXISTS upload_task (
  id VARCHAR(64) PRIMARY KEY,
  name VARCHAR(255) NOT NULL,
  module_code VARCHAR(10) NOT NULL,
  module_name VARCHAR(50) NOT NULL,
  cycle VARCHAR(50) NOT NULL,
  cycle_type VARCHAR(30) NOT NULL,
  deadline DATETIME NOT NULL,
  progress_current INT NOT NULL DEFAULT 0,
  progress_total INT NOT NULL DEFAULT 0,
  status VARCHAR(30) NOT NULL,
  next_step VARCHAR(100) NOT NULL,
  assignee_id BIGINT,
  assignee_name VARCHAR(100),
  assignee_dept VARCHAR(100),
  priority_code VARCHAR(30),
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  INDEX idx_upload_task_module(module_code),
  INDEX idx_upload_task_status(status),
  INDEX idx_upload_task_deadline(deadline)
) ENGINE=InnoDB COMMENT='上传任务';

CREATE TABLE IF NOT EXISTS upload_task_requirement (
  id VARCHAR(64) PRIMARY KEY,
  task_id VARCHAR(64) NOT NULL,
  name VARCHAR(255) NOT NULL,
  required TINYINT NOT NULL DEFAULT 1,
  format_rule VARCHAR(255) NOT NULL,
  status VARCHAR(30) NOT NULL,
  template_available TINYINT NOT NULL DEFAULT 0,
  sequence_no INT NOT NULL DEFAULT 0,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  INDEX idx_requirement_task(task_id),
  INDEX idx_requirement_status(status)
) ENGINE=InnoDB COMMENT='上传任务资料要求';

CREATE TABLE IF NOT EXISTS task_candidate_document (
  id VARCHAR(64) PRIMARY KEY,
  task_id VARCHAR(64) NOT NULL,
  name VARCHAR(255) NOT NULL,
  cycle VARCHAR(50) NOT NULL,
  unit_name VARCHAR(100) NOT NULL,
  link_count INT NOT NULL DEFAULT 0,
  match_rate INT NOT NULL DEFAULT 0,
  sequence_no INT NOT NULL DEFAULT 0,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  INDEX idx_candidate_document_task(task_id)
) ENGINE=InnoDB COMMENT='任务办理候选关联资料';

CREATE TABLE IF NOT EXISTS task_review_timeline (
  id VARCHAR(64) PRIMARY KEY,
  task_id VARCHAR(64) NOT NULL,
  event_time DATETIME NOT NULL,
  action_text VARCHAR(500) NOT NULL,
  sequence_no INT NOT NULL DEFAULT 0,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  INDEX idx_task_review_timeline_task(task_id)
) ENGINE=InnoDB COMMENT='任务办理审核时间线';

CREATE TABLE IF NOT EXISTS workspace_summary (
  id INT PRIMARY KEY,
  current_todo INT NOT NULL,
  pending_upload INT NOT NULL,
  pending_correction INT NOT NULL,
  pending_submit INT NOT NULL,
  under_review INT NOT NULL,
  due_soon INT NOT NULL,
  completed INT NOT NULL,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB COMMENT='工作台摘要快照';

-- 3. 智能入库
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
  duplicate_status VARCHAR(30) NOT NULL DEFAULT 'UNKNOWN',
  duplicate_of_file_id BIGINT,
  parse_status VARCHAR(30) NOT NULL DEFAULT 'PENDING',
  is_deleted TINYINT NOT NULL DEFAULT 0,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  INDEX idx_file_hash(sha256_hash),
  INDEX idx_file_parse_status(parse_status),
  INDEX idx_file_upload_time(upload_time)
) ENGINE=InnoDB COMMENT='文件资产';

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
  retry_count INT NOT NULL DEFAULT 0,
  raw_result_json JSON,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  INDEX idx_parse_job_file(file_id),
  INDEX idx_parse_job_status(job_status)
) ENGINE=InnoDB COMMENT='AI解析任务';

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
  confirm_status VARCHAR(30) NOT NULL DEFAULT 'PENDING',
  confirmed_value TEXT,
  confirmed_by BIGINT,
  confirmed_at DATETIME,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  INDEX idx_parse_field_job(parse_job_id),
  INDEX idx_parse_field_key(field_key),
  INDEX idx_parse_field_confirm(confirm_status)
) ENGINE=InnoDB COMMENT='AI字段抽取结果';

CREATE TABLE IF NOT EXISTS ai_field_mapping_rule (
  id BIGINT PRIMARY KEY,
  document_type VARCHAR(100) NOT NULL,
  field_key VARCHAR(100) NOT NULL,
  field_name VARCHAR(100) NOT NULL,
  target_table VARCHAR(100) NOT NULL,
  target_column VARCHAR(100) NOT NULL,
  value_type VARCHAR(30),
  required TINYINT NOT NULL DEFAULT 0,
  normalize_rule VARCHAR(255),
  enabled TINYINT NOT NULL DEFAULT 1,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  UNIQUE KEY uk_mapping_doc_field(document_type, field_key, target_table, target_column),
  INDEX idx_mapping_doc_field(document_type, field_key, enabled)
) ENGINE=InnoDB COMMENT='AI字段入库映射规则';

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
  reuse_count INT NOT NULL DEFAULT 0,
  candidate_status VARCHAR(30) NOT NULL DEFAULT 'PENDING',
  confirmed_by BIGINT,
  confirmed_at DATETIME,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  INDEX idx_candidate_job(parse_job_id),
  INDEX idx_candidate_task(task_id),
  INDEX idx_candidate_status(candidate_status)
) ENGINE=InnoDB COMMENT='AI候选任务匹配';

CREATE TABLE IF NOT EXISTS deduplication_record (
  id BIGINT PRIMARY KEY,
  file_id BIGINT NOT NULL,
  matched_file_id BIGINT,
  matched_document_id BIGINT,
  match_type VARCHAR(30) NOT NULL,
  match_score DECIMAL(5,2),
  hash_equal TINYINT NOT NULL DEFAULT 0,
  name_similar TINYINT NOT NULL DEFAULT 0,
  content_similar TINYINT NOT NULL DEFAULT 0,
  decision_status VARCHAR(30) NOT NULL DEFAULT 'PENDING',
  decision_by BIGINT,
  decision_at DATETIME,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  INDEX idx_dedup_file(file_id),
  INDEX idx_dedup_status(decision_status)
) ENGINE=InnoDB COMMENT='文件去重记录';

-- 4. 资料中心
CREATE TABLE IF NOT EXISTS document_record (
  id BIGINT PRIMARY KEY,
  document_code VARCHAR(64) NOT NULL UNIQUE,
  document_name VARCHAR(255) NOT NULL,
  document_type VARCHAR(100) NOT NULL,
  module_code VARCHAR(10) NOT NULL,
  period_value VARCHAR(50),
  version_no VARCHAR(20) NOT NULL DEFAULT 'V1',
  source_name VARCHAR(100),
  relation_count INT NOT NULL DEFAULT 0,
  validity_status VARCHAR(30) NOT NULL DEFAULT '有效',
  document_status VARCHAR(30) NOT NULL DEFAULT 'ACTIVE',
  confirm_status VARCHAR(30) NOT NULL DEFAULT 'CONFIRMED',
  file_id BIGINT,
  parse_job_id BIGINT,
  responsible_unit VARCHAR(100),
  valid_start_date DATE,
  valid_end_date DATE,
  uploaded_at DATETIME,
  created_by BIGINT,
  updated_by BIGINT,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  INDEX idx_document_module(module_code),
  INDEX idx_document_type(document_type),
  INDEX idx_document_period(period_value),
  INDEX idx_document_status(document_status, validity_status)
) ENGINE=InnoDB COMMENT='资料主档';

CREATE TABLE IF NOT EXISTS document_version (
  id BIGINT PRIMARY KEY,
  document_id BIGINT NOT NULL,
  file_id BIGINT NOT NULL,
  version_no VARCHAR(20) NOT NULL,
  version_desc VARCHAR(500),
  change_type VARCHAR(50),
  uploaded_by BIGINT,
  uploaded_at DATETIME NOT NULL,
  is_current TINYINT NOT NULL DEFAULT 0,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  INDEX idx_doc_version_doc(document_id),
  INDEX idx_doc_version_current(document_id, is_current)
) ENGINE=InnoDB COMMENT='资料版本';

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
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  UNIQUE KEY uk_doc_task(document_id, task_id),
  INDEX idx_relation_task(task_id),
  INDEX idx_relation_status(relation_status)
) ENGINE=InnoDB COMMENT='资料任务关联';

-- 5. 审核流转
CREATE TABLE IF NOT EXISTS review_record (
  id VARCHAR(64) PRIMARY KEY,
  task_id VARCHAR(64),
  task_name VARCHAR(255) NOT NULL,
  module_code VARCHAR(10) NOT NULL,
  module_name VARCHAR(50) NOT NULL,
  submit_time DATETIME NOT NULL,
  status VARCHAR(30) NOT NULL,
  reviewer_id BIGINT,
  reviewer VARCHAR(100),
  comment_summary VARCHAR(500),
  next_step VARCHAR(100) NOT NULL,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  INDEX idx_review_status(status),
  INDEX idx_review_task(task_id)
) ENGINE=InnoDB COMMENT='审核记录';

CREATE TABLE IF NOT EXISTS review_timeline (
  id BIGINT PRIMARY KEY,
  review_id VARCHAR(64) NOT NULL,
  event_time DATETIME NOT NULL,
  action_text VARCHAR(500) NOT NULL,
  event_type VARCHAR(50),
  operator_name VARCHAR(100),
  sequence_no INT NOT NULL DEFAULT 0,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  INDEX idx_review_timeline_review(review_id)
) ENGINE=InnoDB COMMENT='审核轨迹';

CREATE TABLE IF NOT EXISTS review_requirement (
  id BIGINT PRIMARY KEY,
  review_id VARCHAR(64) NOT NULL,
  requirement_text VARCHAR(500) NOT NULL,
  requirement_status VARCHAR(30) NOT NULL DEFAULT '待补正',
  sequence_no INT NOT NULL DEFAULT 0,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  INDEX idx_review_requirement_review(review_id)
) ENGINE=InnoDB COMMENT='审核补正要求';

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
  operated_at DATETIME NOT NULL,
  INDEX idx_confirm_target(target_type, target_id),
  INDEX idx_confirm_operator(operator_id, operated_at)
) ENGINE=InnoDB COMMENT='人工确认记录';

-- 6. E/S/G 业务明细核心表
CREATE TABLE IF NOT EXISTS env_monitoring_record (
  id BIGINT PRIMARY KEY,
  document_id BIGINT,
  monitor_date DATE,
  monitor_type VARCHAR(50),
  exceed_count INT NOT NULL DEFAULT 0,
  dust_exceed_count INT NOT NULL DEFAULT 0,
  noise_exceed_count INT NOT NULL DEFAULT 0,
  module_code VARCHAR(10) NOT NULL DEFAULT 'E',
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  INDEX idx_env_monitor_date(monitor_date)
) ENGINE=InnoDB COMMENT='环境监测记录';

CREATE TABLE IF NOT EXISTS env_issue_record (
  id BIGINT PRIMARY KEY,
  document_id BIGINT,
  issue_type VARCHAR(100),
  issue_count INT NOT NULL DEFAULT 1,
  issue_status VARCHAR(30),
  overdue TINYINT NOT NULL DEFAULT 0,
  found_date DATE,
  closed_date DATE,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  INDEX idx_env_issue_status(issue_status)
) ENGINE=InnoDB COMMENT='环保问题记录';

CREATE TABLE IF NOT EXISTS water_protection_issue (
  id BIGINT PRIMARY KEY,
  document_id BIGINT,
  issue_status VARCHAR(30),
  found_date DATE,
  closed_date DATE,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  INDEX idx_water_issue_status(issue_status)
) ENGINE=InnoDB COMMENT='水保问题记录';

CREATE TABLE IF NOT EXISTS carbon_emission_activity (
  id BIGINT PRIMARY KEY,
  document_id BIGINT,
  period_value VARCHAR(50),
  diesel_usage DECIMAL(18,4),
  electricity_usage DECIMAL(18,4),
  material_usage DECIMAL(18,4),
  carbon_emission DECIMAL(18,4),
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  INDEX idx_carbon_period(period_value)
) ENGINE=InnoDB COMMENT='碳排放活动数据';

CREATE TABLE IF NOT EXISTS carbon_material_usage (
  id BIGINT PRIMARY KEY,
  document_id BIGINT,
  period_value VARCHAR(50),
  material_name VARCHAR(100),
  material_usage DECIMAL(18,4),
  material_unit VARCHAR(30),
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  INDEX idx_carbon_material_period(period_value)
) ENGINE=InnoDB COMMENT='碳排放材料用量';

CREATE TABLE IF NOT EXISTS safety_production_record (
  id BIGINT PRIMARY KEY,
  project_start_date DATE NOT NULL,
  `current_date` DATE NOT NULL,
  continuous_days INT NOT NULL,
  current_stage VARCHAR(100),
  current_stage_detail VARCHAR(255),
  counting_status VARCHAR(30) NOT NULL,
  update_time DATETIME NOT NULL,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB COMMENT='连续安全生产记录';

CREATE TABLE IF NOT EXISTS safety_risk_point (
  id BIGINT PRIMARY KEY,
  document_id BIGINT,
  risk_name VARCHAR(255),
  risk_level VARCHAR(50),
  control_status VARCHAR(50),
  control_measure TEXT,
  location VARCHAR(255),
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  INDEX idx_safety_risk_level(risk_level),
  INDEX idx_safety_risk_status(control_status)
) ENGINE=InnoDB COMMENT='安全风险点';

CREATE TABLE IF NOT EXISTS labor_dispute_record (
  id BIGINT PRIMARY KEY,
  document_id BIGINT,
  dispute_type VARCHAR(100),
  status VARCHAR(50),
  involved_people INT,
  overdue TINYINT NOT NULL DEFAULT 0,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  INDEX idx_labor_status(status)
) ENGINE=InnoDB COMMENT='劳务纠纷记录';

CREATE TABLE IF NOT EXISTS salary_payment_record (
  id BIGINT PRIMARY KEY,
  document_id BIGINT,
  payment_month VARCHAR(50),
  worker_count INT,
  payment_amount DECIMAL(18,2),
  payment_status VARCHAR(50),
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  INDEX idx_salary_payment_month(payment_month)
) ENGINE=InnoDB COMMENT='工资支付记录';

CREATE TABLE IF NOT EXISTS appeal_record (
  id BIGINT PRIMARY KEY,
  document_id BIGINT,
  appeal_type VARCHAR(100),
  status VARCHAR(50),
  source_channel VARCHAR(100),
  overdue TINYINT NOT NULL DEFAULT 0,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  INDEX idx_appeal_status(status)
) ENGINE=InnoDB COMMENT='群众诉求记录';

CREATE TABLE IF NOT EXISTS compliance_procedure (
  id BIGINT PRIMARY KEY,
  document_id BIGINT,
  procedure_name VARCHAR(255),
  status VARCHAR(50),
  impact_node VARCHAR(100),
  overdue TINYINT NOT NULL DEFAULT 0,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  INDEX idx_compliance_status(status)
) ENGINE=InnoDB COMMENT='合规手续';

CREATE TABLE IF NOT EXISTS permit_record (
  id BIGINT PRIMARY KEY,
  document_id BIGINT,
  permit_name VARCHAR(255),
  permit_no VARCHAR(100),
  expire_date DATE,
  status VARCHAR(50),
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  INDEX idx_permit_expire(expire_date),
  INDEX idx_permit_status(status)
) ENGINE=InnoDB COMMENT='许可事项';

CREATE TABLE IF NOT EXISTS rectification_record (
  id BIGINT PRIMARY KEY,
  document_id BIGINT,
  item_name VARCHAR(255),
  status VARCHAR(50),
  source_type VARCHAR(100),
  overdue TINYINT NOT NULL DEFAULT 0,
  closed_date DATE,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  INDEX idx_rectification_status(status)
) ENGINE=InnoDB COMMENT='整改事项';

CREATE TABLE IF NOT EXISTS compliance_material_gap (
  id BIGINT PRIMARY KEY,
  task_id VARCHAR(64),
  material_name VARCHAR(255),
  status VARCHAR(50),
  responsible_unit VARCHAR(100),
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  INDEX idx_material_gap_status(status)
) ENGINE=InnoDB COMMENT='待补齐合规资料';

-- 7. 指标计算
CREATE TABLE IF NOT EXISTS indicator_definition (
  indicator_code VARCHAR(20) PRIMARY KEY,
  group_code VARCHAR(10) NOT NULL,
  indicator_name VARCHAR(100) NOT NULL,
  unit VARCHAR(30) NOT NULL,
  source_table VARCHAR(100),
  calculation_desc VARCHAR(500),
  display_order INT NOT NULL,
  enabled TINYINT NOT NULL DEFAULT 1,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB COMMENT='指标定义';

CREATE TABLE IF NOT EXISTS indicator_result (
  indicator_code VARCHAR(20) PRIMARY KEY,
  group_code VARCHAR(10) NOT NULL,
  label VARCHAR(100) NOT NULL,
  full_name VARCHAR(100) NOT NULL,
  value DECIMAL(18,4) NOT NULL,
  value_text VARCHAR(100),
  unit VARCHAR(30) NOT NULL,
  display_order INT NOT NULL,
  calculated_at DATETIME NOT NULL,
  published_at DATETIME NOT NULL,
  INDEX idx_indicator_group(group_code, display_order)
) ENGINE=InnoDB COMMENT='指标当前结果';

CREATE TABLE IF NOT EXISTS indicator_snapshot (
  snapshot_type VARCHAR(50) NOT NULL,
  snapshot_date DATE NOT NULL,
  payload_json JSON NOT NULL,
  published_at DATETIME NOT NULL,
  PRIMARY KEY(snapshot_type, snapshot_date)
) ENGINE=InnoDB COMMENT='指标/页面快照';

-- 8. 审计
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
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  INDEX idx_audit_entity(entity_type, entity_id),
  INDEX idx_audit_operator(operator_id, created_at)
) ENGINE=InnoDB COMMENT='操作审计日志';

SET FOREIGN_KEY_CHECKS = 1;
