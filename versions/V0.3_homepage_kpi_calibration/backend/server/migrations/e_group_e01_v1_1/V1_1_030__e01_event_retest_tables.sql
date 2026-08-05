-- ============================================================================
-- V1_1_030__e01_event_retest_tables.sql
-- E组公共闭环 & E01 V1.1 增量迁移 — E01 超标事件与复测表
-- ============================================================================
-- 包含 5 张表：
--   e01_exceed_event            超标事件
--   e01_rectification_round    整改轮次
--   e01_retest_round            复测轮次
--   e01_retest_result_link      复测结果关联
--   e01_legacy_record_mapping   历史记录映射（数据迁移对账用）
-- ============================================================================

CREATE TABLE IF NOT EXISTS e01_exceed_event (
    id BIGINT NOT NULL AUTO_INCREMENT,
    event_code VARCHAR(100) NOT NULL,
    case_id BIGINT NOT NULL,
    original_result_id BIGINT NOT NULL,
    first_exceeded_at DATETIME(6) NOT NULL,
    event_category VARCHAR(20) NOT NULL,
    current_retest_round INT NOT NULL DEFAULT 0,
    latest_retest_outcome VARCHAR(30) NOT NULL DEFAULT 'NOT_TESTED',
    closure_confirmed_at DATETIME(6) NULL,
    closure_confirmed_by BIGINT NULL,
    effective_status VARCHAR(30) NOT NULL DEFAULT 'DRAFT',
    effective_at DATETIME(6) NULL,
    effective_by BIGINT NULL,
    data_nature VARCHAR(20) NOT NULL,
    is_demo TINYINT(1) NOT NULL DEFAULT 0,
    active_original_result_id BIGINT GENERATED ALWAYS AS (CASE WHEN effective_status='EFFECTIVE' THEN original_result_id ELSE NULL END) STORED,
    created_at TIMESTAMP(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    updated_at TIMESTAMP(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
    PRIMARY KEY (id),
    UNIQUE KEY uk_e01_event_code (event_code),
    UNIQUE KEY uk_e01_event_case (case_id),
    UNIQUE KEY uk_e01_event_active_result (active_original_result_id),
    KEY idx_e01_event_open (effective_status, data_nature, is_demo, current_retest_round),
    CONSTRAINT fk_e01_event_case FOREIGN KEY (case_id) REFERENCES e_closure_case(id) ON DELETE RESTRICT ON UPDATE RESTRICT,
    CONSTRAINT fk_e01_event_original FOREIGN KEY (original_result_id) REFERENCES e01_factor_result(id) ON DELETE RESTRICT ON UPDATE RESTRICT,
    CONSTRAINT ck_e01_event_category CHECK (event_category IN ('WATER','AIR','NOISE')),
    CONSTRAINT ck_e01_event_retest_round CHECK (current_retest_round>=0),
    CONSTRAINT ck_e01_event_retest_outcome CHECK (latest_retest_outcome IN ('NOT_TESTED','COMPLIANT','STILL_EXCEEDED','NO_JUDGEMENT')),
    CONSTRAINT ck_e01_event_nature CHECK ((data_nature='demo' AND is_demo=1) OR (data_nature IN ('formal','platform_calc') AND is_demo=0)),
    CONSTRAINT ck_e01_event_effective CHECK (effective_status IN ('DRAFT','PENDING_REVIEW','EFFECTIVE','INVALID'))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE IF NOT EXISTS e01_rectification_round (
    id BIGINT NOT NULL AUTO_INCREMENT,
    event_id BIGINT NOT NULL,
    round_no INT NOT NULL,
    task_id BIGINT NULL,
    started_at DATETIME(6) NULL,
    submitted_at DATETIME(6) NULL,
    rectification_summary VARCHAR(1000) NULL,
    review_status VARCHAR(30) NOT NULL DEFAULT 'PENDING_REVIEW',
    data_nature VARCHAR(20) NOT NULL,
    is_demo TINYINT(1) NOT NULL DEFAULT 0,
    effective_status VARCHAR(30) NOT NULL DEFAULT 'DRAFT',
    effective_at DATETIME(6) NULL,
    effective_by BIGINT NULL,
    created_at TIMESTAMP(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    PRIMARY KEY (id),
    UNIQUE KEY uk_e01_rect_round (event_id, round_no),
    CONSTRAINT fk_e01_rect_round_event FOREIGN KEY (event_id) REFERENCES e01_exceed_event(id) ON DELETE RESTRICT ON UPDATE RESTRICT,
    CONSTRAINT fk_e01_rect_round_task FOREIGN KEY (task_id) REFERENCES e_rectification_task(id) ON DELETE RESTRICT ON UPDATE RESTRICT,
    CONSTRAINT ck_e01_rect_round_no CHECK (round_no>0),
    CONSTRAINT ck_e01_rect_round_time CHECK (submitted_at IS NULL OR started_at IS NULL OR started_at<=submitted_at),
    CONSTRAINT ck_e01_rect_round_nature CHECK ((data_nature='demo' AND is_demo=1) OR (data_nature IN ('formal','platform_calc') AND is_demo=0)),
    CONSTRAINT ck_e01_rect_round_effective CHECK (effective_status IN ('DRAFT','PENDING_REVIEW','EFFECTIVE','INVALID'))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE IF NOT EXISTS e01_retest_round (
    id BIGINT NOT NULL AUTO_INCREMENT,
    event_id BIGINT NOT NULL,
    round_no INT NOT NULL,
    retest_batch_id BIGINT NOT NULL,
    requested_at DATETIME(6) NULL,
    planned_sample_at DATETIME(6) NULL,
    actual_sample_at DATETIME(6) NULL,
    report_document_id BIGINT NULL,
    outcome VARCHAR(30) NOT NULL,
    review_status VARCHAR(30) NOT NULL DEFAULT 'PENDING_REVIEW',
    reviewed_at DATETIME(6) NULL,
    reviewed_by BIGINT NULL,
    data_nature VARCHAR(20) NOT NULL,
    is_demo TINYINT(1) NOT NULL DEFAULT 0,
    effective_status VARCHAR(30) NOT NULL DEFAULT 'DRAFT',
    effective_at DATETIME(6) NULL,
    effective_by BIGINT NULL,
    created_at TIMESTAMP(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    PRIMARY KEY (id),
    UNIQUE KEY uk_e01_retest_round (event_id, round_no),
    CONSTRAINT fk_e01_retest_round_event FOREIGN KEY (event_id) REFERENCES e01_exceed_event(id) ON DELETE RESTRICT ON UPDATE RESTRICT,
    CONSTRAINT fk_e01_retest_round_batch FOREIGN KEY (retest_batch_id) REFERENCES e01_monitor_batch(id) ON DELETE RESTRICT ON UPDATE RESTRICT,
    CONSTRAINT fk_e01_retest_round_document FOREIGN KEY (report_document_id) REFERENCES document_record(id) ON DELETE RESTRICT ON UPDATE RESTRICT,
    CONSTRAINT ck_e01_retest_round_no CHECK (round_no>0),
    CONSTRAINT ck_e01_retest_outcome CHECK (outcome IN ('COMPLIANT','STILL_EXCEEDED','NO_JUDGEMENT')),
    CONSTRAINT ck_e01_retest_review CHECK (review_status IN ('PENDING_REVIEW','PASSED','REJECTED')),
    CONSTRAINT ck_e01_retest_round_nature CHECK ((data_nature='demo' AND is_demo=1) OR (data_nature IN ('formal','platform_calc') AND is_demo=0)),
    CONSTRAINT ck_e01_retest_round_effective CHECK (effective_status IN ('DRAFT','PENDING_REVIEW','EFFECTIVE','INVALID'))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE IF NOT EXISTS e01_retest_result_link (
    id BIGINT NOT NULL AUTO_INCREMENT,
    event_id BIGINT NOT NULL,
    retest_round_id BIGINT NOT NULL,
    factor_result_id BIGINT NOT NULL,
    original_result_id BIGINT NOT NULL,
    data_nature VARCHAR(20) NOT NULL,
    is_demo TINYINT(1) NOT NULL DEFAULT 0,
    effective_status VARCHAR(30) NOT NULL DEFAULT 'DRAFT',
    effective_at DATETIME(6) NULL,
    effective_by BIGINT NULL,
    created_at TIMESTAMP(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    PRIMARY KEY (id),
    UNIQUE KEY uk_e01_retest_link_round_result (retest_round_id, factor_result_id),
    UNIQUE KEY uk_e01_retest_link_result (factor_result_id),
    CONSTRAINT fk_e01_retest_link_event FOREIGN KEY (event_id) REFERENCES e01_exceed_event(id) ON DELETE RESTRICT ON UPDATE RESTRICT,
    CONSTRAINT fk_e01_retest_link_round FOREIGN KEY (retest_round_id) REFERENCES e01_retest_round(id) ON DELETE RESTRICT ON UPDATE RESTRICT,
    CONSTRAINT fk_e01_retest_link_result FOREIGN KEY (factor_result_id) REFERENCES e01_factor_result(id) ON DELETE RESTRICT ON UPDATE RESTRICT,
    CONSTRAINT fk_e01_retest_link_original FOREIGN KEY (original_result_id) REFERENCES e01_factor_result(id) ON DELETE RESTRICT ON UPDATE RESTRICT,
    CONSTRAINT ck_e01_retest_link_distinct CHECK (factor_result_id<>original_result_id),
    CONSTRAINT ck_e01_retest_link_nature CHECK ((data_nature='demo' AND is_demo=1) OR (data_nature IN ('formal','platform_calc') AND is_demo=0)),
    CONSTRAINT ck_e01_retest_link_effective CHECK (effective_status IN ('DRAFT','PENDING_REVIEW','EFFECTIVE','INVALID'))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE IF NOT EXISTS e01_legacy_record_mapping (
    id BIGINT NOT NULL AUTO_INCREMENT,
    legacy_table VARCHAR(80) NOT NULL,
    legacy_record_id BIGINT NOT NULL,
    target_table VARCHAR(80) NULL,
    target_record_id BIGINT NULL,
    mapping_status VARCHAR(40) NOT NULL,
    reconciliation_class VARCHAR(60) NOT NULL,
    difference_reason VARCHAR(1000) NULL,
    migration_version VARCHAR(64) NOT NULL,
    created_at TIMESTAMP(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    PRIMARY KEY (id),
    UNIQUE KEY uk_e01_legacy_mapping (legacy_table, legacy_record_id, target_table, target_record_id, migration_version),
    CONSTRAINT ck_e01_legacy_status CHECK (mapping_status IN ('MAPPED','AGGREGATE_ONLY','UNMAPPABLE','EXCLUDED')),
    CONSTRAINT ck_e01_legacy_class CHECK (reconciliation_class IN ('TOTAL_MATCH','ROW_MAPPABLE','AGGREGATE_MAPPABLE','UNMAPPABLE','EXPECTED_DIFFERENCE_DEMO_EXCLUDED','EXPECTED_DIFFERENCE_INVALID_EXCLUDED'))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
