from __future__ import annotations

from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))

from mysql_db import mysql_connect  # noqa: E402


def execute(sql: str, params: tuple = ()) -> None:
    with mysql_connect() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, params)


def executemany(sql: str, rows: list[tuple]) -> None:
    with mysql_connect() as conn:
        with conn.cursor() as cur:
            cur.executemany(sql, rows)


def ensure_tables() -> None:
    execute(
        """
        CREATE TABLE IF NOT EXISTS monthly_report_cycle (
          id BIGINT PRIMARY KEY,
          report_period VARCHAR(50) NOT NULL,
          report_name VARCHAR(255) NOT NULL,
          completion_rate DECIMAL(10,2) NOT NULL DEFAULT 0,
          expected_complete_date VARCHAR(50) NULL,
          current_stage VARCHAR(50) NULL,
          update_time DATETIME NULL,
          created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='月报周期主表'
        """
    )
    execute(
        """
        CREATE TABLE IF NOT EXISTS monthly_report_group_progress (
          id BIGINT PRIMARY KEY,
          cycle_id BIGINT NOT NULL,
          group_code VARCHAR(10) NOT NULL,
          group_label VARCHAR(30) NOT NULL,
          completion_rate DECIMAL(10,2) NOT NULL DEFAULT 0,
          color VARCHAR(30) NULL,
          created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
          INDEX idx_monthly_progress_cycle (cycle_id)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='月报分组完成进度'
        """
    )
    execute(
        """
        CREATE TABLE IF NOT EXISTS monthly_report_chapter (
          id BIGINT PRIMARY KEY,
          cycle_id BIGINT NOT NULL,
          chapter_index INT NOT NULL,
          chapter_name VARCHAR(255) NOT NULL,
          material_type VARCHAR(100) NULL,
          group_name VARCHAR(30) NULL,
          owner VARCHAR(100) NULL,
          responsible_person VARCHAR(100) NULL,
          status VARCHAR(50) NULL,
          deadline VARCHAR(50) NULL,
          created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
          INDEX idx_monthly_chapter_cycle (cycle_id)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='月报章节清单'
        """
    )
    execute(
        """
        CREATE TABLE IF NOT EXISTS monthly_report_gap (
          id BIGINT PRIMARY KEY,
          cycle_id BIGINT NOT NULL,
          material_name VARCHAR(255) NOT NULL,
          group_name VARCHAR(30) NULL,
          owner VARCHAR(100) NULL,
          deadline VARCHAR(50) NULL,
          status VARCHAR(50) NULL,
          note VARCHAR(500) NULL,
          created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
          INDEX idx_monthly_gap_cycle (cycle_id)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='月报缺项清单'
        """
    )
    execute(
        """
        CREATE TABLE IF NOT EXISTS monthly_report_status_chain (
          id BIGINT PRIMARY KEY,
          cycle_id BIGINT NOT NULL,
          chain_key VARCHAR(50) NOT NULL,
          label VARCHAR(100) NOT NULL,
          status VARCHAR(30) NOT NULL,
          display_order INT NOT NULL,
          created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
          INDEX idx_monthly_chain_cycle (cycle_id)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='月报状态链'
        """
    )


def seed_rows() -> None:
    execute("DELETE FROM monthly_report_status_chain WHERE cycle_id = 810001")
    execute("DELETE FROM monthly_report_gap WHERE cycle_id = 810001")
    execute("DELETE FROM monthly_report_chapter WHERE cycle_id = 810001")
    execute("DELETE FROM monthly_report_group_progress WHERE cycle_id = 810001")
    execute("DELETE FROM monthly_report_cycle WHERE id = 810001")

    execute(
        """
        INSERT INTO monthly_report_cycle
        (id, report_period, report_name, completion_rate, expected_complete_date, current_stage, update_time)
        VALUES (810001, '2026-07', '2026年7月ESG月报', 82, '7月12日', '报告编制', '2026-07-13 10:00:00')
        """
    )
    executemany(
        """
        INSERT INTO monthly_report_group_progress
        (id, cycle_id, group_code, group_label, completion_rate, color)
        VALUES (%s, 810001, %s, %s, %s, %s)
        """,
        [
            (810101, "E", "E组", 85, "#69e36f"),
            (810102, "S", "S组", 78, "#2f9cff"),
            (810103, "G", "G组", 83, "#a66cff"),
        ],
    )
    executemany(
        """
        INSERT INTO monthly_report_chapter
        (id, cycle_id, chapter_index, chapter_name, material_type, group_name, owner, responsible_person, status, deadline)
        VALUES (%s, 810001, %s, %s, %s, %s, %s, %s, %s, %s)
        """,
        [
            (810201, 1, "环境保护执行情况", "月度报告", "E组", "安全环保部", "张三", "已完成", "7月10日"),
            (810202, 2, "水土保持监测月报", "监测报告", "E组", "安全环保部", "李四", "已完成", "7月10日"),
            (810203, 3, "安全生产月报", "月度报告", "S组", "安全环保部", "王五", "编制中", "7月12日"),
            (810204, 4, "劳务用工情况统计", "统计报表", "S组", "人力资源部", "赵六", "待确认", "7月12日"),
            (810205, 5, "合规性检查报告", "检查报告", "G组", "合约法务部", "钱七", "待补充", "7月15日"),
            (810206, 6, "报批报建进度表", "进度报表", "G组", "工程管理部", "孙八", "编制中", "7月15日"),
        ],
    )
    executemany(
        """
        INSERT INTO monthly_report_gap
        (id, cycle_id, material_name, group_name, owner, deadline, status, note)
        VALUES (%s, 810001, %s, %s, %s, %s, %s, %s)
        """,
        [
            (810301, "噪声监测原始记录", "E组", "安全环保部", "7月15日", "待补齐", "7月上半月数据"),
            (810302, "碳排放因子确认", "E组", "技术管理部", "7月14日", "待确认", "7月因子更新"),
            (810303, "安全检查记录归档", "S组", "安全环保部", "7月16日", "待补齐", "6月检查记录"),
            (810304, "安全数据核验", "S组", "工程管理部", "7月16日", "待确认", "数据一致性核对"),
            (810305, "临时用地批复复印件", "G组", "工程管理部", "7月15日", "待补齐", "最新批复文件"),
            (810306, "监理通知单回执", "G组", "监理部", "7月17日", "待确认", "上月通知单"),
        ],
    )
    executemany(
        """
        INSERT INTO monthly_report_status_chain
        (id, cycle_id, chain_key, label, status, display_order)
        VALUES (%s, 810001, %s, %s, %s, %s)
        """,
        [
            (810401, "draft", "资料收集", "completed", 1),
            (810402, "verify", "数据核验", "completed", 2),
            (810403, "compile", "报告编制", "active", 3),
            (810404, "review", "内部审核", "pending", 4),
            (810405, "submit", "提交上报", "pending", 5),
        ],
    )


def main() -> int:
    ensure_tables()
    seed_rows()
    print("[PASS] 月报准备与输出专题 V0.7 业务表已创建并写入首页衍生测试数据。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
