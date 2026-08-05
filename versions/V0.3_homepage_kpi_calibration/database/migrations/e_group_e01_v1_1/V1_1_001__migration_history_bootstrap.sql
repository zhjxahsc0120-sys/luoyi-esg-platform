-- ============================================================================
-- V1_1_001__migration_history_bootstrap.sql
-- E组公共闭环 & E01 V1.1 增量迁移 — 迁移历史引导表
-- ============================================================================
-- 创建 esg_schema_migration_history 表，用于追踪各迁移脚本的执行状态。
-- 本表为幂等建表（IF NOT EXISTS），不插入任何数据。
-- ============================================================================

CREATE TABLE IF NOT EXISTS esg_schema_migration_history (
    id              BIGINT        NOT NULL AUTO_INCREMENT,
    version_key     VARCHAR(64)   NOT NULL COMMENT '迁移脚本版本标识，如 V1_1_010',
    description     VARCHAR(255)  NOT NULL COMMENT '脚本用途简述',
    file_name       VARCHAR(255)  NOT NULL COMMENT 'SQL 文件名',
    checksum_sha256 CHAR(64)      NOT NULL COMMENT '文件内容 SHA-256 校验和',
    execution_id    VARCHAR(64)   NOT NULL COMMENT '本次执行的唯一标识',
    executed_at     DATETIME(6)   NOT NULL DEFAULT CURRENT_TIMESTAMP(6) COMMENT '执行开始时间',
    finished_at     DATETIME(6)   NULL     COMMENT '执行结束时间',
    status          VARCHAR(30)   NOT NULL COMMENT 'SUCCESS / FAILED / SKIPPED',
    error_message   TEXT          NULL     COMMENT '失败时的错误信息',
    executed_by     VARCHAR(128)  NULL     COMMENT '执行者标识',
    PRIMARY KEY (id),
    UNIQUE KEY uk_migration_version_execution (version_key, execution_id),
    KEY idx_migration_version_status (version_key, status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci
  COMMENT='ESG 项目 Schema 迁移历史记录表（V1.1 引导）';
