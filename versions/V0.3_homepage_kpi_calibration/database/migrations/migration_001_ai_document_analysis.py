"""ESG-AI-DATA-001：工程资料 AI 解析独立表迁移。

用法：
    python server/migrations/migration_001_ai_document_analysis.py --dry-run
    python server/migrations/migration_001_ai_document_analysis.py
    python server/migrations/migration_001_ai_document_analysis.py --rollback

迁移只创建六张 ai_* 新表。回滚按依赖顺序删除这些新表，不触碰任何已有业务表。
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

SERVER_DIR = Path(__file__).resolve().parents[1]
if str(SERVER_DIR) not in sys.path:
    sys.path.insert(0, str(SERVER_DIR))

from mysql_db import mysql_connect  # noqa: E402


TABLE_NAMES = (
    "ai_document_analysis",
    "ai_extracted_project_info",
    "ai_extracted_progress",
    "ai_extracted_safety",
    "ai_extracted_environment",
    "ai_extracted_resource",
)


CREATE_STATEMENTS = (
    """
    CREATE TABLE IF NOT EXISTS ai_document_analysis (
        id BIGINT NOT NULL AUTO_INCREMENT,
        source_file_id BIGINT NOT NULL,
        file_name VARCHAR(500) NOT NULL,
        file_type VARCHAR(80) NOT NULL,
        project_name VARCHAR(200) NOT NULL,
        report_period VARCHAR(20) NOT NULL,
        analysis_status VARCHAR(20) NOT NULL DEFAULT 'uploaded',
        summary_text TEXT NULL,
        confidence_score DECIMAL(5,4) NULL,
        ingestion_status VARCHAR(20) NOT NULL DEFAULT 'pending',
        excluded_from_dashboard TINYINT(1) NOT NULL DEFAULT 1,
        created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
        updated_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
        PRIMARY KEY (id),
        KEY idx_ai_document_source_file (source_file_id),
        KEY idx_ai_document_period_status (report_period, analysis_status),
        CONSTRAINT chk_ai_document_status CHECK (
            analysis_status IN ('uploaded', 'processing', 'completed', 'review', 'failed')
        )
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    """,
    """
    CREATE TABLE IF NOT EXISTS ai_extracted_project_info (
        id BIGINT NOT NULL AUTO_INCREMENT,
        analysis_id BIGINT NOT NULL,
        project_name VARCHAR(200) NOT NULL,
        construction_stage VARCHAR(100) NULL,
        route_length DECIMAL(10,2) NULL,
        section_count INT NULL,
        professional_type_count INT NULL,
        period VARCHAR(20) NOT NULL,
        PRIMARY KEY (id),
        UNIQUE KEY uk_ai_project_analysis (analysis_id),
        CONSTRAINT fk_ai_project_analysis FOREIGN KEY (analysis_id)
            REFERENCES ai_document_analysis (id) ON DELETE CASCADE
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    """,
    """
    CREATE TABLE IF NOT EXISTS ai_extracted_progress (
        id BIGINT NOT NULL AUTO_INCREMENT,
        analysis_id BIGINT NOT NULL,
        section_code VARCHAR(50) NOT NULL,
        work_type VARCHAR(100) NOT NULL,
        work_content VARCHAR(500) NOT NULL,
        supervision_focus VARCHAR(500) NULL,
        period VARCHAR(20) NOT NULL,
        PRIMARY KEY (id),
        KEY idx_ai_progress_analysis (analysis_id),
        KEY idx_ai_progress_period_section (period, section_code),
        CONSTRAINT fk_ai_progress_analysis FOREIGN KEY (analysis_id)
            REFERENCES ai_document_analysis (id) ON DELETE CASCADE
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    """,
    """
    CREATE TABLE IF NOT EXISTS ai_extracted_safety (
        id BIGINT NOT NULL AUTO_INCREMENT,
        analysis_id BIGINT NOT NULL,
        safe_days INT NOT NULL DEFAULT 0,
        risk_point_count INT NOT NULL DEFAULT 0,
        unfinished_issue_count INT NOT NULL DEFAULT 0,
        inspection_count INT NOT NULL DEFAULT 0,
        period VARCHAR(20) NOT NULL,
        PRIMARY KEY (id),
        UNIQUE KEY uk_ai_safety_analysis (analysis_id),
        CONSTRAINT fk_ai_safety_analysis FOREIGN KEY (analysis_id)
            REFERENCES ai_document_analysis (id) ON DELETE CASCADE
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    """,
    """
    CREATE TABLE IF NOT EXISTS ai_extracted_environment (
        id BIGINT NOT NULL AUTO_INCREMENT,
        analysis_id BIGINT NOT NULL,
        environment_issue_count INT NOT NULL DEFAULT 0,
        water_issue_count INT NOT NULL DEFAULT 0,
        rectification_status VARCHAR(80) NULL,
        monitoring_abnormal_count INT NOT NULL DEFAULT 0,
        period VARCHAR(20) NOT NULL,
        PRIMARY KEY (id),
        UNIQUE KEY uk_ai_environment_analysis (analysis_id),
        CONSTRAINT fk_ai_environment_analysis FOREIGN KEY (analysis_id)
            REFERENCES ai_document_analysis (id) ON DELETE CASCADE
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    """,
    """
    CREATE TABLE IF NOT EXISTS ai_extracted_resource (
        id BIGINT NOT NULL AUTO_INCREMENT,
        analysis_id BIGINT NOT NULL,
        person_count INT NOT NULL DEFAULT 0,
        equipment_count INT NOT NULL DEFAULT 0,
        equipment_type VARCHAR(500) NULL,
        period VARCHAR(20) NOT NULL,
        PRIMARY KEY (id),
        UNIQUE KEY uk_ai_resource_analysis (analysis_id),
        CONSTRAINT fk_ai_resource_analysis FOREIGN KEY (analysis_id)
            REFERENCES ai_document_analysis (id) ON DELETE CASCADE
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    """,
)

DROP_STATEMENTS = tuple(f"DROP TABLE IF EXISTS {name}" for name in reversed(TABLE_NAMES))


def run_migration(rollback: bool = False, dry_run: bool = False) -> None:
    statements = DROP_STATEMENTS if rollback else CREATE_STATEMENTS
    action = "ROLLBACK" if rollback else "CREATE"
    if dry_run:
        print(f"[DRY-RUN] {action}: {', '.join(TABLE_NAMES)}")
        for statement in statements:
            print(statement.strip() + ";")
        return

    with mysql_connect() as conn:
        with conn.cursor() as cursor:
            for statement in statements:
                cursor.execute(statement)
        conn.commit()
    print(f"[OK] {action}: {', '.join(TABLE_NAMES)}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--rollback", action="store_true", help="删除本迁移创建的六张新表")
    parser.add_argument("--dry-run", action="store_true", help="仅打印 SQL，不连接数据库")
    args = parser.parse_args()
    run_migration(rollback=args.rollback, dry_run=args.dry_run)


if __name__ == "__main__":
    main()
