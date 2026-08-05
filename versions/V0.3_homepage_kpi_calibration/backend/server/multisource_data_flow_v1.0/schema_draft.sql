-- 罗宜高速 ESG 多源数据接入与指标动态更新核心表草案 V1.0
-- 注意：本文件为设计草案，暂不自动执行。

CREATE TABLE IF NOT EXISTS data_source_registry (
  id BIGINT PRIMARY KEY,
  source_code VARCHAR(50) NOT NULL UNIQUE COMMENT '来源编码',
  source_name VARCHAR(100) NOT NULL COMMENT '来源名称',
  source_type VARCHAR(30) NOT NULL COMMENT 'UPLOAD/API/MANUAL/BATCH/GIS/SCHEDULE',
  owner_department VARCHAR(100) COMMENT '来源责任部门',
  provider_name VARCHAR(100) COMMENT '系统或供应商名称',
  endpoint_url VARCHAR(500) COMMENT '接口地址，仅接口类来源使用',
  enabled TINYINT NOT NULL DEFAULT 1,
  remark VARCHAR(500),
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='数据来源登记表';

CREATE TABLE IF NOT EXISTS data_ingestion_job (
  id BIGINT PRIMARY KEY,
  source_id BIGINT NOT NULL,
  job_type VARCHAR(30) NOT NULL COMMENT 'FILE_PARSE/API_SYNC/MANUAL_IMPORT/BATCH_IMPORT/SCHEDULE_SYNC',
  job_status VARCHAR(30) NOT NULL COMMENT 'PENDING/RUNNING/SUCCESS/FAILED/PARTIAL_SUCCESS',
  business_domain VARCHAR(50) COMMENT 'ENV/SAFETY/SOCIAL/GOVERNANCE/CARBON/MONTHLY/GIS',
  target_table VARCHAR(100) COMMENT '目标业务表',
  started_at DATETIME,
  finished_at DATETIME,
  total_count INT DEFAULT 0,
  success_count INT DEFAULT 0,
  failed_count INT DEFAULT 0,
  operator_id BIGINT,
  operator_name VARCHAR(100),
  error_message TEXT,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  INDEX idx_ingestion_source(source_id, created_at),
  INDEX idx_ingestion_status(job_status, created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='数据接入任务表';

CREATE TABLE IF NOT EXISTS data_mapping_rule (
  id BIGINT PRIMARY KEY,
  source_id BIGINT NOT NULL,
  source_object VARCHAR(100) COMMENT '来源对象，如接口资源、资料类型、sheet名称',
  source_field VARCHAR(100) NOT NULL COMMENT '来源字段',
  target_table VARCHAR(100) NOT NULL COMMENT '目标业务表',
  target_field VARCHAR(100) NOT NULL COMMENT '目标字段',
  target_data_type VARCHAR(30) COMMENT '目标数据类型',
  transform_rule VARCHAR(500) COMMENT '转换规则',
  required TINYINT NOT NULL DEFAULT 0,
  enabled TINYINT NOT NULL DEFAULT 1,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  INDEX idx_mapping_source(source_id, source_object),
  INDEX idx_mapping_target(target_table)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='多源字段映射规则表';

CREATE TABLE IF NOT EXISTS data_quality_check_result (
  id BIGINT PRIMARY KEY,
  ingestion_job_id BIGINT NOT NULL,
  source_record_key VARCHAR(100) COMMENT '来源记录主键或文件行号',
  target_table VARCHAR(100),
  target_record_id VARCHAR(100),
  check_type VARCHAR(50) NOT NULL COMMENT 'REQUIRED/FORMAT/RANGE/CONSISTENCY/DUPLICATE/BUSINESS_RULE',
  check_status VARCHAR(30) NOT NULL COMMENT 'PASS/WARN/FAIL',
  check_message VARCHAR(1000),
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  INDEX idx_quality_job(ingestion_job_id),
  INDEX idx_quality_target(target_table, target_record_id),
  INDEX idx_quality_status(check_status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='数据质量校验结果表';

CREATE TABLE IF NOT EXISTS source_record_trace (
  id BIGINT PRIMARY KEY,
  ingestion_job_id BIGINT NOT NULL,
  source_id BIGINT NOT NULL,
  source_type VARCHAR(30) NOT NULL COMMENT 'UPLOAD/API/MANUAL/BATCH/GIS/SCHEDULE',
  source_record_key VARCHAR(100) COMMENT '来源记录ID、文件ID、解析字段ID等',
  document_id BIGINT COMMENT '如来自资料上传，关联 document_record',
  file_id BIGINT COMMENT '如来自文件，关联 file_asset',
  target_table VARCHAR(100) NOT NULL,
  target_record_id VARCHAR(100) NOT NULL,
  operation_type VARCHAR(30) NOT NULL COMMENT 'INSERT/UPDATE/UPSERT/DELETE',
  trace_payload JSON COMMENT '来源关键字段快照',
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  INDEX idx_trace_source(source_id, source_record_key),
  INDEX idx_trace_target(target_table, target_record_id),
  INDEX idx_trace_job(ingestion_job_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='业务记录来源追溯表';

CREATE TABLE IF NOT EXISTS indicator_calculation_job (
  id BIGINT PRIMARY KEY,
  indicator_code VARCHAR(20) NOT NULL,
  calculation_type VARCHAR(30) NOT NULL COMMENT 'EVENT_TRIGGER/SCHEDULED/MANUAL',
  trigger_source VARCHAR(100) COMMENT '触发来源，如 permit_record 更新、每日定时等',
  trigger_record_id VARCHAR(100),
  job_status VARCHAR(30) NOT NULL COMMENT 'PENDING/RUNNING/SUCCESS/FAILED',
  calculation_period VARCHAR(50) COMMENT '计算周期，如 2026-07',
  started_at DATETIME,
  finished_at DATETIME,
  result_value DECIMAL(18,4),
  result_payload JSON COMMENT '指标详情或弹窗聚合结果',
  error_message TEXT,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  INDEX idx_indicator_job_code(indicator_code, created_at),
  INDEX idx_indicator_job_status(job_status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='指标计算任务表';

CREATE TABLE IF NOT EXISTS indicator_history (
  id BIGINT PRIMARY KEY,
  indicator_code VARCHAR(20) NOT NULL,
  result_date DATE NOT NULL,
  result_value DECIMAL(18,4) NOT NULL,
  result_text VARCHAR(100),
  unit VARCHAR(30),
  calculation_job_id BIGINT,
  detail_payload JSON COMMENT '当日指标详情快照',
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  UNIQUE KEY uk_indicator_history(indicator_code, result_date),
  INDEX idx_indicator_history_code(indicator_code, result_date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='指标历史结果表';

CREATE TABLE IF NOT EXISTS indicator_source_dependency (
  id BIGINT PRIMARY KEY,
  indicator_code VARCHAR(20) NOT NULL,
  source_table VARCHAR(100) NOT NULL,
  dependency_type VARCHAR(30) NOT NULL COMMENT 'PRIMARY/SECONDARY/REFERENCE',
  calculation_desc VARCHAR(500),
  enabled TINYINT NOT NULL DEFAULT 1,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  UNIQUE KEY uk_indicator_source(indicator_code, source_table)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='指标数据源依赖表';

