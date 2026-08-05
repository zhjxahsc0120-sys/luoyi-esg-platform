-- ============================================================================
-- V1_1_012__e01_factor_result.sql
-- E组公共闭环 & E01 V1.1 增量迁移 — 因子检测结果表
-- ============================================================================
-- 本表为 V1.1 新增表，存储监测因子检测结果及判定信息。
-- V1.1 设计草案将其定义为新增表，供超标事件、KPI 视图等引用。
-- ============================================================================

CREATE TABLE IF NOT EXISTS e01_factor_result (
    id              BIGINT          NOT NULL AUTO_INCREMENT,
    result_code     VARCHAR(255)    NOT NULL,
    sample_id       BIGINT          NOT NULL,
    factor_id       BIGINT          NOT NULL,
    standard_version_id BIGINT      NOT NULL,
    test_stage      VARCHAR(30)     NOT NULL,
    judgement       VARCHAR(30)     NULL,
    result_validity VARCHAR(20)     NULL,
    detected_value_raw  VARCHAR(100) NULL,
    limit_value_raw    VARCHAR(100) NULL,
    standard_name_snapshot VARCHAR(255) NULL,
    reported_factor_name  VARCHAR(160) NULL,
    reported_unit          VARCHAR(60)  NULL,
    judgement_source  VARCHAR(30)  NULL,
    effective_status VARCHAR(30)     NOT NULL DEFAULT 'DRAFT',
    data_nature     VARCHAR(20)     NOT NULL,
    is_demo         TINYINT(1)      NOT NULL DEFAULT 0,
    created_at      TIMESTAMP(6)    NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    updated_at      TIMESTAMP(6)    NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
    PRIMARY KEY (id),
    UNIQUE KEY uk_e01_factor_result_code (result_code),
    KEY idx_e01_factor_result_sample (sample_id, test_stage, data_nature, is_demo),
    KEY idx_e01_factor_result_kpi (
        test_stage, judgement, result_validity,
        effective_status, data_nature, is_demo
    ),
    KEY idx_e01_factor_result_factor (factor_id, standard_version_id),
    CONSTRAINT fk_e01_factor_result_sample
        FOREIGN KEY (sample_id) REFERENCES e01_monitor_sample(id)
        ON DELETE RESTRICT ON UPDATE RESTRICT,
    CONSTRAINT fk_e01_factor_result_factor
        FOREIGN KEY (factor_id) REFERENCES e01_factor_definition(id)
        ON DELETE RESTRICT ON UPDATE RESTRICT,
    CONSTRAINT fk_e01_factor_result_standard
        FOREIGN KEY (standard_version_id) REFERENCES e01_standard_version(id)
        ON DELETE RESTRICT ON UPDATE RESTRICT,
    CONSTRAINT ck_e01_factor_result_stage
        CHECK (test_stage IN ('INITIAL','RETEST','SUPPLEMENTARY')),
    CONSTRAINT ck_e01_factor_result_judgement
        CHECK (judgement IS NULL OR judgement IN ('EXCEEDED','COMPLIANT','NO_JUDGEMENT')),
    CONSTRAINT ck_e01_factor_result_validity
        CHECK (result_validity IS NULL OR result_validity IN ('VALID','VOID','PENDING')),
    CONSTRAINT ck_e01_factor_result_effective
        CHECK (effective_status IN ('DRAFT','PENDING_REVIEW','EFFECTIVE','INVALID')),
    CONSTRAINT ck_e01_factor_result_nature
        CHECK ((data_nature='demo' AND is_demo=1)
               OR (data_nature IN ('formal','platform_calc') AND is_demo=0)),
    CONSTRAINT ck_e01_factor_result_sample_required
        CHECK (sample_id IS NOT NULL),
    CONSTRAINT ck_e01_factor_result_factor_required
        CHECK (factor_id IS NOT NULL),
    CONSTRAINT ck_e01_factor_result_standard_required
        CHECK (standard_version_id IS NOT NULL),
    CONSTRAINT ck_e01_factor_result_stage_required
        CHECK (test_stage IS NOT NULL),
    CONSTRAINT ck_e01_factor_result_nature_required
        CHECK (data_nature IS NOT NULL),
    CONSTRAINT ck_e01_factor_result_demo_default
        CHECK (is_demo IS NOT NULL),
    CONSTRAINT ck_e01_factor_result_judgement_source
        CHECK (judgement_source IS NULL
               OR judgement_source IN ('AUTO_LIMIT','MANUAL','IMPORTED'))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
