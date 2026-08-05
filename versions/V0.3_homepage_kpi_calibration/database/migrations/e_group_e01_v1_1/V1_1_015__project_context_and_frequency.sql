-- E01 V1.1 增量：合同段、项目阶段、工程对象、点位上下文和监测频次。

CREATE TABLE IF NOT EXISTS project_section (
    id BIGINT NOT NULL AUTO_INCREMENT,
    project_id VARCHAR(64) NOT NULL DEFAULT 'LUOYI-ESG',
    section_code VARCHAR(40) NOT NULL,
    section_name VARCHAR(160) NOT NULL,
    chainage_start VARCHAR(40) NOT NULL,
    chainage_end VARCHAR(40) NOT NULL,
    start_km DECIMAL(10,3) NOT NULL,
    end_km DECIMAL(10,3) NOT NULL,
    section_type VARCHAR(40) NOT NULL DEFAULT 'CIVIL',
    active_status VARCHAR(20) NOT NULL DEFAULT 'ACTIVE',
    data_nature VARCHAR(20) NOT NULL,
    is_demo TINYINT(1) NOT NULL DEFAULT 0,
    created_at TIMESTAMP(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    updated_at TIMESTAMP(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
    PRIMARY KEY (id),
    UNIQUE KEY uk_project_section_code (project_id, section_code),
    KEY idx_project_section_range (project_id, start_km, end_km),
    CONSTRAINT ck_project_section_range CHECK (start_km < end_km),
    CONSTRAINT ck_project_section_status CHECK (active_status IN ('PLANNED','ACTIVE','COMPLETED','INACTIVE')),
    CONSTRAINT ck_project_section_nature CHECK ((data_nature='demo' AND is_demo=1) OR (data_nature IN ('formal','platform_calc') AND is_demo=0))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE IF NOT EXISTS project_phase_period (
    id BIGINT NOT NULL AUTO_INCREMENT,
    project_id VARCHAR(64) NOT NULL DEFAULT 'LUOYI-ESG',
    phase_code VARCHAR(60) NOT NULL,
    phase_name VARCHAR(160) NOT NULL,
    phase_type VARCHAR(50) NOT NULL,
    start_at DATETIME(6) NOT NULL,
    end_at DATETIME(6) NOT NULL,
    phase_status VARCHAR(20) NOT NULL DEFAULT 'PLANNED',
    data_nature VARCHAR(20) NOT NULL,
    is_demo TINYINT(1) NOT NULL DEFAULT 0,
    created_at TIMESTAMP(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    updated_at TIMESTAMP(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
    PRIMARY KEY (id),
    UNIQUE KEY uk_project_phase_code (project_id, phase_code),
    KEY idx_project_phase_time (project_id, start_at, end_at),
    CONSTRAINT ck_project_phase_time CHECK (start_at <= end_at),
    CONSTRAINT ck_project_phase_status CHECK (phase_status IN ('PLANNED','ACTIVE','COMPLETED','SUSPENDED')),
    CONSTRAINT ck_project_phase_nature CHECK ((data_nature='demo' AND is_demo=1) OR (data_nature IN ('formal','platform_calc') AND is_demo=0))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE IF NOT EXISTS project_engineering_object (
    id BIGINT NOT NULL AUTO_INCREMENT,
    project_id VARCHAR(64) NOT NULL DEFAULT 'LUOYI-ESG',
    section_id BIGINT NOT NULL,
    object_code VARCHAR(80) NOT NULL,
    object_name VARCHAR(200) NOT NULL,
    object_type VARCHAR(60) NOT NULL,
    chainage_start VARCHAR(40) NULL,
    chainage_end VARCHAR(40) NULL,
    longitude DECIMAL(11,8) NULL,
    latitude DECIMAL(10,8) NULL,
    gis_feature_id VARCHAR(96) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL,
    active_status VARCHAR(20) NOT NULL DEFAULT 'ACTIVE',
    data_nature VARCHAR(20) NOT NULL,
    is_demo TINYINT(1) NOT NULL DEFAULT 0,
    created_at TIMESTAMP(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    updated_at TIMESTAMP(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
    PRIMARY KEY (id),
    UNIQUE KEY uk_project_object_code (project_id, object_code),
    KEY idx_project_object_section (section_id, object_type, active_status),
    KEY idx_project_object_gis (gis_feature_id),
    CONSTRAINT fk_project_object_section FOREIGN KEY (section_id) REFERENCES project_section(id) ON DELETE RESTRICT ON UPDATE RESTRICT,
    CONSTRAINT fk_project_object_gis FOREIGN KEY (gis_feature_id) REFERENCES gis_feature(id) ON DELETE RESTRICT ON UPDATE RESTRICT,
    CONSTRAINT ck_project_object_coordinates CHECK ((longitude IS NULL AND latitude IS NULL) OR (longitude IS NOT NULL AND latitude IS NOT NULL)),
    CONSTRAINT ck_project_object_status CHECK (active_status IN ('PLANNED','ACTIVE','COMPLETED','INACTIVE')),
    CONSTRAINT ck_project_object_nature CHECK ((data_nature='demo' AND is_demo=1) OR (data_nature IN ('formal','platform_calc') AND is_demo=0))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE IF NOT EXISTS engineering_object_phase (
    id BIGINT NOT NULL AUTO_INCREMENT,
    object_id BIGINT NOT NULL,
    phase_id BIGINT NOT NULL,
    process_code VARCHAR(80) NOT NULL,
    process_name VARCHAR(160) NOT NULL,
    process_start_at DATETIME(6) NOT NULL,
    process_end_at DATETIME(6) NOT NULL,
    process_status VARCHAR(20) NOT NULL DEFAULT 'PLANNED',
    data_nature VARCHAR(20) NOT NULL,
    is_demo TINYINT(1) NOT NULL DEFAULT 0,
    created_at TIMESTAMP(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    updated_at TIMESTAMP(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
    PRIMARY KEY (id),
    UNIQUE KEY uk_object_phase_process (object_id, phase_id, process_code),
    KEY idx_object_phase_time (object_id, process_start_at, process_end_at),
    CONSTRAINT fk_object_phase_object FOREIGN KEY (object_id) REFERENCES project_engineering_object(id) ON DELETE RESTRICT ON UPDATE RESTRICT,
    CONSTRAINT fk_object_phase_phase FOREIGN KEY (phase_id) REFERENCES project_phase_period(id) ON DELETE RESTRICT ON UPDATE RESTRICT,
    CONSTRAINT ck_object_phase_time CHECK (process_start_at <= process_end_at),
    CONSTRAINT ck_object_phase_status CHECK (process_status IN ('PLANNED','ACTIVE','COMPLETED','SUSPENDED')),
    CONSTRAINT ck_object_phase_nature CHECK ((data_nature='demo' AND is_demo=1) OR (data_nature IN ('formal','platform_calc') AND is_demo=0))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE IF NOT EXISTS monitor_point_object_relation (
    id BIGINT NOT NULL AUTO_INCREMENT,
    relation_code VARCHAR(100) NOT NULL,
    point_id BIGINT NOT NULL,
    section_id BIGINT NOT NULL,
    object_id BIGINT NOT NULL,
    phase_id BIGINT NULL,
    object_phase_id BIGINT NULL,
    relation_role VARCHAR(30) NOT NULL DEFAULT 'PRIMARY',
    valid_from DATETIME(6) NOT NULL,
    valid_to DATETIME(6) NULL,
    data_nature VARCHAR(20) NOT NULL,
    is_demo TINYINT(1) NOT NULL DEFAULT 0,
    created_at TIMESTAMP(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    updated_at TIMESTAMP(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
    PRIMARY KEY (id),
    UNIQUE KEY uk_monitor_point_object_relation (relation_code),
    KEY idx_monitor_point_object_time (point_id, valid_from, valid_to),
    KEY idx_monitor_object_point (object_id, point_id),
    CONSTRAINT fk_monitor_relation_point FOREIGN KEY (point_id) REFERENCES e01_monitor_point(id) ON DELETE RESTRICT ON UPDATE RESTRICT,
    CONSTRAINT fk_monitor_relation_section FOREIGN KEY (section_id) REFERENCES project_section(id) ON DELETE RESTRICT ON UPDATE RESTRICT,
    CONSTRAINT fk_monitor_relation_object FOREIGN KEY (object_id) REFERENCES project_engineering_object(id) ON DELETE RESTRICT ON UPDATE RESTRICT,
    CONSTRAINT fk_monitor_relation_phase FOREIGN KEY (phase_id) REFERENCES project_phase_period(id) ON DELETE RESTRICT ON UPDATE RESTRICT,
    CONSTRAINT fk_monitor_relation_object_phase FOREIGN KEY (object_phase_id) REFERENCES engineering_object_phase(id) ON DELETE RESTRICT ON UPDATE RESTRICT,
    CONSTRAINT ck_monitor_relation_time CHECK (valid_to IS NULL OR valid_from <= valid_to),
    CONSTRAINT ck_monitor_relation_role CHECK (relation_role IN ('PRIMARY','IMPACT','BACKGROUND','CONTROL')),
    CONSTRAINT ck_monitor_relation_nature CHECK ((data_nature='demo' AND is_demo=1) OR (data_nature IN ('formal','platform_calc') AND is_demo=0))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE IF NOT EXISTS monitor_frequency_rule (
    id BIGINT NOT NULL AUTO_INCREMENT,
    rule_code VARCHAR(100) NOT NULL,
    plan_item_id BIGINT NOT NULL,
    frequency_code VARCHAR(30) NOT NULL,
    interval_value INT NULL,
    interval_unit VARCHAR(20) NULL,
    schedule_expression VARCHAR(160) NULL,
    aggregation_granularity VARCHAR(30) NULL,
    trigger_event VARCHAR(160) NULL,
    effective_from DATETIME(6) NOT NULL,
    effective_to DATETIME(6) NULL,
    active_status VARCHAR(20) NOT NULL DEFAULT 'ACTIVE',
    data_nature VARCHAR(20) NOT NULL,
    is_demo TINYINT(1) NOT NULL DEFAULT 0,
    created_at TIMESTAMP(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    updated_at TIMESTAMP(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
    PRIMARY KEY (id),
    UNIQUE KEY uk_monitor_frequency_rule (rule_code),
    KEY idx_monitor_frequency_plan_item (plan_item_id, active_status, effective_from),
    CONSTRAINT fk_monitor_frequency_plan_item FOREIGN KEY (plan_item_id) REFERENCES e01_monitor_plan_item(id) ON DELETE RESTRICT ON UPDATE RESTRICT,
    CONSTRAINT ck_monitor_frequency_code CHECK (frequency_code IN ('CONTINUOUS','DAILY','WEEKLY','MONTHLY','QUARTERLY','EVENT_TRIGGERED')),
    CONSTRAINT ck_monitor_frequency_interval CHECK ((frequency_code IN ('CONTINUOUS','EVENT_TRIGGERED')) OR (interval_value IS NOT NULL AND interval_value > 0)),
    CONSTRAINT ck_monitor_frequency_time CHECK (effective_to IS NULL OR effective_from <= effective_to),
    CONSTRAINT ck_monitor_frequency_status CHECK (active_status IN ('ACTIVE','INACTIVE')),
    CONSTRAINT ck_monitor_frequency_nature CHECK ((data_nature='demo' AND is_demo=1) OR (data_nature IN ('formal','platform_calc') AND is_demo=0))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- 放开计划频次的季度单值限制；历史 segment 快照列继续保留。
SET @drop_frequency_check = IF(
    EXISTS (
        SELECT 1 FROM information_schema.table_constraints
        WHERE constraint_schema=DATABASE() AND table_name='e01_monitor_plan'
          AND constraint_name='ck_e01_plan_frequency' AND constraint_type='CHECK'
    ),
    'ALTER TABLE e01_monitor_plan DROP CHECK ck_e01_plan_frequency',
    'SELECT 1'
);
PREPARE stmt FROM @drop_frequency_check;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

SET @add_frequency_check = IF(
    EXISTS (
        SELECT 1 FROM information_schema.table_constraints
        WHERE constraint_schema=DATABASE() AND table_name='e01_monitor_plan'
          AND constraint_name='ck_e01_plan_frequency' AND constraint_type='CHECK'
    ),
    'SELECT 1',
    'ALTER TABLE e01_monitor_plan ADD CONSTRAINT ck_e01_plan_frequency CHECK (frequency_code IN (''CONTINUOUS'',''DAILY'',''WEEKLY'',''MONTHLY'',''QUARTERLY'',''EVENT_TRIGGERED''))'
);
PREPARE stmt FROM @add_frequency_check;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;
