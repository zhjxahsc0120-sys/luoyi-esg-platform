-- ============================================================================
-- V1_0_001__migration_history_bootstrap.sql
-- S01 V1.0 迁移 — migration_history 引导表
-- ============================================================================
-- 本文件仅在 esg_schema_migration_history 表不存在时执行（由执行器 bootstrap 阶段调用）。
-- DDL 使用 IF NOT EXISTS 保证幂等。
-- ============================================================================

CREATE TABLE IF NOT EXISTS esg_schema_migration_history (
    id BIGINT NOT NULL AUTO_INCREMENT,
    version_key        VARCHAR(30)  NOT NULL COMMENT '迁移版本号，如 V1_0_010',
    description        VARCHAR(200) NOT NULL COMMENT '迁移描述',
    file_name          VARCHAR(200) NOT NULL COMMENT 'SQL 文件名',
    checksum_sha256    CHAR(64)     NOT NULL COMMENT '文件 SHA-256 校验和',
    execution_id       VARCHAR(60)  NOT NULL COMMENT '本次执行唯一 ID',
    executed_at        DATETIME(6)  NOT NULL COMMENT '开始执行时间',
    finished_at        DATETIME(6)  NOT NULL COMMENT '完成执行时间',
    status             VARCHAR(20)  NOT NULL COMMENT 'SUCCESS / FAILED / GATE_BLOCKED',
    error_message      TEXT         NULL     COMMENT '失败原因',
    executed_by        VARCHAR(100) NULL     COMMENT '执行者标识',
    PRIMARY KEY (id),
    UNIQUE KEY uk_version_key (version_key),
    KEY idx_execution_id (execution_id),
    KEY idx_status (status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci
  COMMENT='ESG 项目 schema 迁移执行历史（跨组共享）';
