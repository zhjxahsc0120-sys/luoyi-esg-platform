-- ============================================================================
-- V1_1_020__closure_case_tables.sql
-- E组公共闭环 & E01 V1.1 增量迁移 — 公共闭环案件表
-- ============================================================================
-- 包含 7 张表：
--   e_closure_case             闭环案件
--   e_case_status_history      案件状态变更历史（仅追加，禁止修改/删除）
--   e_case_party               案件参与方
--   e_case_evidence            案件证据
--   e_case_relation            案件关联关系
--   e_rectification_task       整改任务
--   e_case_rectification_link 案件-整改任务关联
-- ============================================================================

CREATE TABLE IF NOT EXISTS e_closure_case (
    id BIGINT NOT NULL AUTO_INCREMENT,
    case_code VARCHAR(80) NOT NULL,
    case_domain VARCHAR(30) NOT NULL,
    source_table VARCHAR(80) NOT NULL,
    source_record_id BIGINT NOT NULL,
    source_business_key VARCHAR(160) NULL,
    source_document_id BIGINT NULL,
    title VARCHAR(255) NOT NULL,
    location_text VARCHAR(255) NULL,
    gis_feature_id VARCHAR(96) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL,
    current_status VARCHAR(40) NOT NULL DEFAULT 'DISCOVERED',
    current_status_history_id BIGINT NULL,
    priority VARCHAR(30) NULL,
    severity VARCHAR(30) NULL,
    deadline DATETIME(6) NULL,
    discovery_org_id BIGINT NULL,
    responsible_org_id BIGINT NULL,
    review_org_id BIGINT NULL,
    close_org_id BIGINT NULL,
    opened_at DATETIME(6) NOT NULL,
    closed_at DATETIME(6) NULL,
    reopened_at DATETIME(6) NULL,
    closure_reason VARCHAR(500) NULL,
    merged_into_case_id BIGINT NULL,
    data_nature VARCHAR(20) NOT NULL,
    is_demo TINYINT(1) NOT NULL DEFAULT 0,
    verification_status VARCHAR(30) NOT NULL DEFAULT 'PENDING_REVIEW',
    effective_status VARCHAR(30) NOT NULL DEFAULT 'DRAFT',
    effective_at DATETIME(6) NULL,
    effective_by BIGINT NULL,
    row_version INT NOT NULL DEFAULT 0,
    created_by BIGINT NULL,
    updated_by BIGINT NULL,
    created_at TIMESTAMP(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    updated_at TIMESTAMP(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
    PRIMARY KEY (id),
    UNIQUE KEY uk_e_case_code (case_code),
    UNIQUE KEY uk_e_case_source_key (case_domain, source_business_key),
    KEY idx_e_case_open (case_domain, current_status, effective_status, data_nature, is_demo),
    CONSTRAINT fk_e_case_source_document FOREIGN KEY (source_document_id) REFERENCES document_record(id) ON DELETE RESTRICT ON UPDATE RESTRICT,
    CONSTRAINT fk_e_case_gis FOREIGN KEY (gis_feature_id) REFERENCES gis_feature(id) ON DELETE RESTRICT ON UPDATE RESTRICT,
    CONSTRAINT fk_e_case_discovery_org FOREIGN KEY (discovery_org_id) REFERENCES org_unit(id) ON DELETE RESTRICT ON UPDATE RESTRICT,
    CONSTRAINT fk_e_case_responsible_org FOREIGN KEY (responsible_org_id) REFERENCES org_unit(id) ON DELETE RESTRICT ON UPDATE RESTRICT,
    CONSTRAINT fk_e_case_review_org FOREIGN KEY (review_org_id) REFERENCES org_unit(id) ON DELETE RESTRICT ON UPDATE RESTRICT,
    CONSTRAINT fk_e_case_close_org FOREIGN KEY (close_org_id) REFERENCES org_unit(id) ON DELETE RESTRICT ON UPDATE RESTRICT,
    CONSTRAINT fk_e_case_merged_into FOREIGN KEY (merged_into_case_id) REFERENCES e_closure_case(id) ON DELETE RESTRICT ON UPDATE RESTRICT,
    CONSTRAINT ck_e_case_domain CHECK (case_domain IN ('E01_EXCEED','E02_ENV','E03_WATER')),
    CONSTRAINT ck_e_case_status CHECK (current_status IN ('DISCOVERED','PENDING_RECTIFICATION','RECTIFYING','PENDING_REVIEW','PENDING_CLOSURE','CLOSED','CANCELLED','MERGED','SUSPENDED')),
    CONSTRAINT ck_e_case_formal_source CHECK (data_nature<>'formal' OR source_business_key IS NOT NULL),
    CONSTRAINT ck_e_case_closed_fields CHECK (current_status<>'CLOSED' OR (closed_at IS NOT NULL AND closure_reason IS NOT NULL)),
    CONSTRAINT ck_e_case_merged_fields CHECK (current_status<>'MERGED' OR merged_into_case_id IS NOT NULL),
    CONSTRAINT ck_e_case_nature CHECK ((data_nature='demo' AND is_demo=1) OR (data_nature IN ('formal','platform_calc') AND is_demo=0)),
    CONSTRAINT ck_e_case_effective CHECK (effective_status IN ('DRAFT','PENDING_REVIEW','EFFECTIVE','INVALID'))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE IF NOT EXISTS e_case_status_history (
    id BIGINT NOT NULL AUTO_INCREMENT,
    case_id BIGINT NOT NULL,
    sequence_no INT NOT NULL,
    from_status VARCHAR(40) NULL,
    to_status VARCHAR(40) NOT NULL,
    action_code VARCHAR(60) NOT NULL,
    transition_result VARCHAR(30) NOT NULL DEFAULT 'SUCCESS',
    action_at DATETIME(6) NOT NULL,
    operator_id BIGINT NULL,
    operator_name VARCHAR(100) NULL,
    operator_org_id BIGINT NULL,
    operator_org_name VARCHAR(160) NULL,
    comment VARCHAR(1000) NULL,
    source_document_id BIGINT NULL,
    client_request_id VARCHAR(100) NOT NULL,
    correction_of_history_id BIGINT NULL,
    data_nature VARCHAR(20) NOT NULL,
    is_demo TINYINT(1) NOT NULL DEFAULT 0,
    created_at TIMESTAMP(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    PRIMARY KEY (id),
    UNIQUE KEY uk_e_case_history_sequence (case_id, sequence_no),
    UNIQUE KEY uk_e_case_history_request (case_id, client_request_id),
    KEY idx_e_case_history_correction (case_id, correction_of_history_id),
    CONSTRAINT fk_e_case_history_case FOREIGN KEY (case_id) REFERENCES e_closure_case(id) ON DELETE RESTRICT ON UPDATE RESTRICT,
    CONSTRAINT fk_e_case_history_document FOREIGN KEY (source_document_id) REFERENCES document_record(id) ON DELETE RESTRICT ON UPDATE RESTRICT,
    CONSTRAINT fk_e_case_history_correction FOREIGN KEY (correction_of_history_id) REFERENCES e_case_status_history(id) ON DELETE RESTRICT ON UPDATE RESTRICT,
    CONSTRAINT ck_e_case_history_from CHECK (from_status IS NULL OR from_status IN ('DISCOVERED','PENDING_RECTIFICATION','RECTIFYING','PENDING_REVIEW','PENDING_CLOSURE','CLOSED','CANCELLED','MERGED','SUSPENDED')),
    CONSTRAINT ck_e_case_history_to CHECK (to_status IN ('DISCOVERED','PENDING_RECTIFICATION','RECTIFYING','PENDING_REVIEW','PENDING_CLOSURE','CLOSED','CANCELLED','MERGED','SUSPENDED')),
    CONSTRAINT ck_e_case_history_result CHECK (transition_result IN ('SUCCESS','REJECTED','RETURNED','CORRECTION')),
    CONSTRAINT ck_e_case_history_correction CHECK ((action_code='CORRECT_HISTORY' AND correction_of_history_id IS NOT NULL AND transition_result='CORRECTION') OR (action_code<>'CORRECT_HISTORY' AND correction_of_history_id IS NULL)),
    CONSTRAINT ck_e_case_history_nature CHECK ((data_nature='demo' AND is_demo=1) OR (data_nature IN ('formal','platform_calc') AND is_demo=0))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE IF NOT EXISTS e_case_party (
    id BIGINT NOT NULL AUTO_INCREMENT,
    case_id BIGINT NOT NULL,
    party_role VARCHAR(30) NOT NULL,
    org_id BIGINT NULL,
    org_name VARCHAR(160) NULL,
    user_id BIGINT NULL,
    user_name VARCHAR(100) NULL,
    valid_from DATETIME(6) NOT NULL,
    valid_to DATETIME(6) NULL,
    is_current TINYINT(1) NOT NULL DEFAULT 1,
    data_nature VARCHAR(20) NOT NULL,
    is_demo TINYINT(1) NOT NULL DEFAULT 0,
    created_at TIMESTAMP(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    PRIMARY KEY (id),
    KEY idx_e_case_party_case (case_id, party_role, is_current),
    CONSTRAINT fk_e_case_party_case FOREIGN KEY (case_id) REFERENCES e_closure_case(id) ON DELETE RESTRICT ON UPDATE RESTRICT,
    CONSTRAINT fk_e_case_party_org FOREIGN KEY (org_id) REFERENCES org_unit(id) ON DELETE RESTRICT ON UPDATE RESTRICT,
    CONSTRAINT ck_e_case_party_role CHECK (party_role IN ('DISCOVERER','RESPONSIBLE','HANDLER','REVIEWER','CLOSER','TEST_PROVIDER')),
    CONSTRAINT ck_e_case_party_nature CHECK ((data_nature='demo' AND is_demo=1) OR (data_nature IN ('formal','platform_calc') AND is_demo=0))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE IF NOT EXISTS e_case_evidence (
    id BIGINT NOT NULL AUTO_INCREMENT,
    case_id BIGINT NOT NULL,
    status_history_id BIGINT NULL,
    document_id BIGINT NULL,
    file_id BIGINT NULL,
    evidence_role VARCHAR(40) NOT NULL,
    version_no INT NOT NULL DEFAULT 1,
    is_current TINYINT(1) NOT NULL DEFAULT 1,
    validity_status VARCHAR(20) NOT NULL DEFAULT 'VALID',
    verification_status VARCHAR(30) NOT NULL DEFAULT 'PENDING_REVIEW',
    data_nature VARCHAR(20) NOT NULL,
    is_demo TINYINT(1) NOT NULL DEFAULT 0,
    created_by BIGINT NULL,
    created_at TIMESTAMP(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    PRIMARY KEY (id),
    KEY idx_e_case_evidence_case (case_id, evidence_role, is_current),
    CONSTRAINT fk_e_case_evidence_case FOREIGN KEY (case_id) REFERENCES e_closure_case(id) ON DELETE RESTRICT ON UPDATE RESTRICT,
    CONSTRAINT fk_e_case_evidence_history FOREIGN KEY (status_history_id) REFERENCES e_case_status_history(id) ON DELETE RESTRICT ON UPDATE RESTRICT,
    CONSTRAINT fk_e_case_evidence_document FOREIGN KEY (document_id) REFERENCES document_record(id) ON DELETE RESTRICT ON UPDATE RESTRICT,
    CONSTRAINT fk_e_case_evidence_file FOREIGN KEY (file_id) REFERENCES file_asset(id) ON DELETE RESTRICT ON UPDATE RESTRICT,
    CONSTRAINT ck_e_case_evidence_source CHECK (document_id IS NOT NULL OR file_id IS NOT NULL),
    CONSTRAINT ck_e_case_evidence_role CHECK (evidence_role IN ('FORMAL_NOTICE','INITIAL_REPORT','RAW_RECORD','RECTIFICATION_MATERIAL','RETEST_REPORT','REVIEW_OPINION','CLOSURE_DOCUMENT','CANCELLATION_DOCUMENT')),
    CONSTRAINT ck_e_case_evidence_validity CHECK (validity_status IN ('VALID','SUPERSEDED','INVALID')),
    CONSTRAINT ck_e_case_evidence_nature CHECK ((data_nature='demo' AND is_demo=1) OR (data_nature IN ('formal','platform_calc') AND is_demo=0))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE IF NOT EXISTS e_case_relation (
    id BIGINT NOT NULL AUTO_INCREMENT,
    from_case_id BIGINT NOT NULL,
    to_case_id BIGINT NOT NULL,
    relation_type VARCHAR(30) NOT NULL,
    reason VARCHAR(500) NULL,
    data_nature VARCHAR(20) NOT NULL,
    is_demo TINYINT(1) NOT NULL DEFAULT 0,
    created_at TIMESTAMP(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    PRIMARY KEY (id),
    UNIQUE KEY uk_e_case_relation (from_case_id, to_case_id, relation_type),
    CONSTRAINT fk_e_case_relation_from FOREIGN KEY (from_case_id) REFERENCES e_closure_case(id) ON DELETE RESTRICT ON UPDATE RESTRICT,
    CONSTRAINT fk_e_case_relation_to FOREIGN KEY (to_case_id) REFERENCES e_closure_case(id) ON DELETE RESTRICT ON UPDATE RESTRICT,
    CONSTRAINT ck_e_case_relation_self CHECK (from_case_id<>to_case_id),
    CONSTRAINT ck_e_case_relation_type CHECK (relation_type IN ('RELATED','DUPLICATE_OF','MERGED_INTO','SAME_TASK')),
    CONSTRAINT ck_e_case_relation_nature CHECK ((data_nature='demo' AND is_demo=1) OR (data_nature IN ('formal','platform_calc') AND is_demo=0))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE IF NOT EXISTS e_rectification_task (
    id BIGINT NOT NULL AUTO_INCREMENT,
    task_code VARCHAR(80) NOT NULL,
    title VARCHAR(255) NOT NULL,
    responsible_org_id BIGINT NULL,
    deadline DATETIME(6) NULL,
    task_status VARCHAR(30) NOT NULL DEFAULT 'PENDING',
    data_nature VARCHAR(20) NOT NULL,
    is_demo TINYINT(1) NOT NULL DEFAULT 0,
    effective_status VARCHAR(30) NOT NULL DEFAULT 'DRAFT',
    effective_at DATETIME(6) NULL,
    effective_by BIGINT NULL,
    created_at TIMESTAMP(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    updated_at TIMESTAMP(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
    PRIMARY KEY (id),
    UNIQUE KEY uk_e_rect_task_code (task_code),
    CONSTRAINT fk_e_rect_task_org FOREIGN KEY (responsible_org_id) REFERENCES org_unit(id) ON DELETE RESTRICT ON UPDATE RESTRICT,
    CONSTRAINT ck_e_rect_task_status CHECK (task_status IN ('PENDING','IN_PROGRESS','SUBMITTED','REVIEWED','COMPLETED','CANCELLED')),
    CONSTRAINT ck_e_rect_task_nature CHECK ((data_nature='demo' AND is_demo=1) OR (data_nature IN ('formal','platform_calc') AND is_demo=0)),
    CONSTRAINT ck_e_rect_task_effective CHECK (effective_status IN ('DRAFT','PENDING_REVIEW','EFFECTIVE','INVALID'))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE IF NOT EXISTS e_case_rectification_link (
    id BIGINT NOT NULL AUTO_INCREMENT,
    case_id BIGINT NOT NULL,
    task_id BIGINT NOT NULL,
    link_role VARCHAR(30) NOT NULL DEFAULT 'PRIMARY',
    data_nature VARCHAR(20) NOT NULL,
    is_demo TINYINT(1) NOT NULL DEFAULT 0,
    effective_status VARCHAR(30) NOT NULL DEFAULT 'EFFECTIVE',
    created_at TIMESTAMP(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    PRIMARY KEY (id),
    UNIQUE KEY uk_e_case_rect_link (case_id, task_id),
    CONSTRAINT fk_e_case_rect_case FOREIGN KEY (case_id) REFERENCES e_closure_case(id) ON DELETE RESTRICT ON UPDATE RESTRICT,
    CONSTRAINT fk_e_case_rect_task FOREIGN KEY (task_id) REFERENCES e_rectification_task(id) ON DELETE RESTRICT ON UPDATE RESTRICT,
    CONSTRAINT ck_e_case_rect_link_nature CHECK ((data_nature='demo' AND is_demo=1) OR (data_nature IN ('formal','platform_calc') AND is_demo=0)),
    CONSTRAINT ck_e_case_rect_link_effective CHECK (effective_status IN ('DRAFT','PENDING_REVIEW','EFFECTIVE','INVALID'))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
