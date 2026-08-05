from __future__ import annotations

from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))

from mysql_db import mysql_connect  # noqa: E402


def existing_columns(table: str) -> set[str]:
    with mysql_connect() as conn:
        with conn.cursor() as cur:
            cur.execute(f"SHOW COLUMNS FROM {table}")
            return {row["Field"] for row in cur.fetchall()}


def add_column_if_missing(table: str, column: str, ddl: str) -> None:
    if column in existing_columns(table):
        return
    with mysql_connect() as conn:
        with conn.cursor() as cur:
            cur.execute(f"ALTER TABLE {table} ADD COLUMN {column} {ddl}")


def ensure_columns() -> None:
    add_column_if_missing("labor_dispute_record", "dispute_name", "VARCHAR(255) NULL COMMENT '纠纷事项'")
    add_column_if_missing("labor_dispute_record", "occurred_date", "DATE NULL COMMENT '发生时间'")
    add_column_if_missing("labor_dispute_record", "amount_wan", "DECIMAL(18,2) NULL COMMENT '涉及金额，万元'")
    add_column_if_missing("labor_dispute_record", "responsible_department", "VARCHAR(100) NULL COMMENT '责任部门'")
    add_column_if_missing("labor_dispute_record", "closed_date", "DATE NULL COMMENT '办结日期'")
    add_column_if_missing(
        "labor_dispute_record",
        "data_nature",
        "VARCHAR(30) NOT NULL DEFAULT 'formal' COMMENT 'formal | demo'",
    )
    add_column_if_missing(
        "labor_dispute_record",
        "is_demo",
        "TINYINT NOT NULL DEFAULT 0 COMMENT '0=formal 1=demo'",
    )

    add_column_if_missing("appeal_record", "appeal_content", "VARCHAR(500) NULL COMMENT '诉求内容'")
    add_column_if_missing("appeal_record", "accepted_date", "DATE NULL COMMENT '受理时间'")
    add_column_if_missing("appeal_record", "location", "VARCHAR(255) NULL COMMENT '涉及地点'")
    add_column_if_missing("appeal_record", "deadline", "DATE NULL COMMENT '办结期限'")
    add_column_if_missing("appeal_record", "closed_date", "DATE NULL COMMENT '办结日期'")
    add_column_if_missing("appeal_record", "duration_days", "INT NULL COMMENT '办理时长'")


def seed_rows() -> None:
    """S03：仅农民工工资类；正式存量 0；demo 包 2 未办结+1 已办结。S04 保留既有构造台账。"""
    with mysql_connect() as conn:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM labor_dispute_record WHERE id BETWEEN 510001 AND 510099")
            cur.execute("DELETE FROM appeal_record WHERE id BETWEEN 520001 AND 520099")

            cur.executemany(
                """
                INSERT INTO labor_dispute_record
                (id, dispute_type, dispute_name, status, involved_people, amount_wan,
                 responsible_department, overdue, occurred_date, closed_date, created_at,
                 data_nature, is_demo)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                [
                    (510001, "工资支付", "班组农民工工资拖欠上访", "协调中", 8, 32, "合同部", 0, "2026-07-05", None, "2026-07-05 09:00:00", "demo", 1),
                    (510002, "工资支付", "加班工资支付争议上访", "调查中", 3, 3, "合同部", 0, "2026-06-28", None, "2026-06-28 09:00:00", "demo", 1),
                    (510003, "工资支付", "零星用工工资核算", "已办结", 2, 6, "合同部", 0, "2026-06-20", "2026-07-06", "2026-06-20 09:00:00", "demo", 1),
                ],
            )

            cur.executemany(
                """
                INSERT INTO appeal_record
                (id, appeal_type, appeal_content, status, source_channel, overdue,
                 accepted_date, location, deadline, closed_date, duration_days, created_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                [
                    (520001, "噪声扰民", "夜间施工噪声扰民投诉", "办理中", "12345热线", 0, "2026-07-08", "K15+000 附近村庄", "2026-07-13", None, 7, "2026-07-08 09:00:00"),
                    (520002, "扬尘投诉", "施工扬尘影响周边居民", "办理中", "信访", 0, "2026-07-10", "K18+500 弃渣场", "2026-07-15", None, 7, "2026-07-10 09:00:00"),
                    (520003, "补偿争议", "临时用地占用农田补偿", "逾期", "现场来访", 1, "2026-06-28", "K22+000 临时用地", "2026-07-08", None, 7, "2026-06-28 09:00:00"),
                    (520004, "道路通行", "施工便道影响村民通行", "已办结", "村委反馈", 0, "2026-06-20", "K10+000 便道", "2026-07-01", "2026-07-01", 8, "2026-06-20 09:00:00"),
                    (520005, "水系影响", "临时排水影响农田灌溉", "已办结", "现场来访", 0, "2026-06-21", "K16+000 排水沟", "2026-07-03", "2026-07-03", 7, "2026-06-21 09:00:00"),
                    (520006, "扬尘投诉", "运输车辆带泥上路", "已办结", "12345热线", 0, "2026-06-25", "K20+000 施工便道", "2026-07-05", "2026-07-05", 6, "2026-06-25 09:00:00"),
                    (520007, "噪声扰民", "拌合站夜间噪声投诉", "已办结", "信访", 0, "2026-06-26", "K30+000 拌合站", "2026-07-07", "2026-07-07", 7, "2026-06-26 09:00:00"),
                ],
            )


def main() -> int:
    ensure_columns()
    seed_rows()
    print("OK S03/S04 social detail seed: wage-only S03 demo (2 open) + S04 appeal ledger.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
