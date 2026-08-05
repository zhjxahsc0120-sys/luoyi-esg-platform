-- ============================================================================
-- V1_0_010__s01_new_tables.sql
-- S01 V1.0 增量迁移 — 仅新建 s01_confirmation_batch
-- ============================================================================
-- safety_incident_record 和 construction_stage_record 已由旧代码
-- (ensure_s01_business_tables) 创建，不在此文件重复 CREATE。
-- 对它们的字段增强见 V1_0_015。
-- ============================================================================

-- --------------------------------------------------------------------------
-- 1. s01_confirmation_batch  确认批次表（全新表，无旧版本）
-- --------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS s01_confirmation_batch (
    id                      BIGINT       NOT NULL AUTO_INCREMENT,
    batch_code              VARCHAR(60)  NOT NULL COMMENT '批次编码，如 DEMO-S01-20260724',
    project_id              VARCHAR(50)  NOT NULL DEFAULT 'LUOYI-ESG' COMMENT '项目标识',
    confirmation_month      VARCHAR(7)   NOT NULL COMMENT '确认月份，如 2026-07',
    statistics_as_of        DATE         NOT NULL COMMENT '统计期末业务日期',
    cycle_start_date        DATE         NOT NULL COMMENT '当前安全生产周期起点',
    continuous_days         INT          NOT NULL COMMENT '后端按冻结算法生成的快照值',
    counting_status         VARCHAR(30)  NOT NULL COMMENT 'CONTINUOUS / PENDING_DETERMINATION / RESET_CYCLE',
    confirmation_unit       VARCHAR(200) NULL     COMMENT '确认单位名称',
    confirmed_by            VARCHAR(100) NULL     COMMENT '确认人',
    confirmed_at            DATETIME(6)  NULL     COMMENT '确认时间',
    confirmation_status     VARCHAR(30)  NOT NULL DEFAULT 'PENDING' COMMENT 'PENDING / CONFIRMED',
    verification_status     VARCHAR(30)  NOT NULL DEFAULT 'PENDING_REVIEW' COMMENT 'PENDING_REVIEW / VERIFIED / REJECTED',
    effective_status        VARCHAR(30)  NOT NULL DEFAULT 'DRAFT' COMMENT 'DRAFT / EFFECTIVE / INEFFECTIVE',
    effective_at            DATETIME(6)  NULL     COMMENT '生效时间',
    data_nature             VARCHAR(20)  NOT NULL COMMENT 'demo / formal',
    is_demo                 TINYINT(1)   NOT NULL DEFAULT 0 COMMENT '是否演示数据',
    version_no              INT          NOT NULL DEFAULT 1 COMMENT '批次版本号',
    remark                  VARCHAR(500) NULL     COMMENT '备注',
    created_at              TIMESTAMP(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    updated_at              TIMESTAMP(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
    PRIMARY KEY (id),
    UNIQUE KEY uk_batch_code (batch_code),
    UNIQUE KEY uk_project_nature_current (project_id, data_nature, is_demo, effective_status),
    KEY idx_confirmation_month (confirmation_month),
    KEY idx_data_nature (data_nature),
    KEY idx_is_demo (is_demo),
    CONSTRAINT ck_s01_cb_confirmation_status CHECK (confirmation_status IN ('PENDING','CONFIRMED')),
    CONSTRAINT ck_s01_cb_verification_status CHECK (verification_status IN ('PENDING_REVIEW','VERIFIED','REJECTED')),
    CONSTRAINT ck_s01_cb_effective_status CHECK (effective_status IN ('DRAFT','EFFECTIVE','INEFFECTIVE')),
    CONSTRAINT ck_s01_cb_counting_status CHECK (counting_status IN ('CONTINUOUS','PENDING_DETERMINATION','RESET_CYCLE')),
    CONSTRAINT ck_s01_cb_data_nature CHECK (data_nature IN ('demo','formal')),
    CONSTRAINT ck_s01_cb_nature_demo CHECK (
        (data_nature = 'demo' AND is_demo = 1) OR
        (data_nature = 'formal' AND is_demo = 0)
    )
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci
  COMMENT='S01 建设单位确认批次';
