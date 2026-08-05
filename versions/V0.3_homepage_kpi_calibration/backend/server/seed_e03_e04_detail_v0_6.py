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
    add_column_if_missing("water_protection_issue", "issue_name", "VARCHAR(255) NULL COMMENT '水保问题名称'")
    add_column_if_missing("water_protection_issue", "issue_type", "VARCHAR(100) NULL COMMENT '问题类型'")
    add_column_if_missing("water_protection_issue", "segment_name", "VARCHAR(100) NULL COMMENT '所属标段'")
    add_column_if_missing("water_protection_issue", "deadline", "DATE NULL COMMENT '整改时限'")
    add_column_if_missing("water_protection_issue", "overdue", "TINYINT NOT NULL DEFAULT 0 COMMENT '是否逾期'")
    add_column_if_missing("water_protection_issue", "responsible_department", "VARCHAR(100) NULL COMMENT '责任部门'")

    add_column_if_missing("carbon_emission_activity", "output_value_wan", "DECIMAL(18,4) NULL COMMENT '完成产值，万元'")
    add_column_if_missing("carbon_emission_activity", "baseline_emission", "DECIMAL(18,4) NULL COMMENT '基准情景排放量'")
    add_column_if_missing("carbon_emission_activity", "diesel_emission", "DECIMAL(18,4) NULL COMMENT '施工用油排放量'")
    add_column_if_missing("carbon_emission_activity", "electricity_emission", "DECIMAL(18,4) NULL COMMENT '施工用电排放量'")
    add_column_if_missing("carbon_emission_activity", "material_emission", "DECIMAL(18,4) NULL COMMENT '主要材料排放量'")
    add_column_if_missing("carbon_emission_activity", "other_emission", "DECIMAL(18,4) NULL COMMENT '其他排放量'")


def seed_rows() -> None:
    with mysql_connect() as conn:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM water_protection_issue WHERE id BETWEEN 710001 AND 710099")
            cur.execute("DELETE FROM carbon_material_usage WHERE id BETWEEN 720501 AND 720599")
            cur.execute("DELETE FROM carbon_emission_activity WHERE id BETWEEN 720001 AND 720099")

            cur.executemany(
                """
                INSERT INTO water_protection_issue
                (id, document_id, issue_name, issue_type, segment_name, issue_status,
                 found_date, deadline, overdue, responsible_department, closed_date, created_at)
                VALUES (%s, NULL, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                [
                    (710001, "弃渣场挡墙未按设计施工", "弃渣场", "标段一", "逾期未闭环", "2026-06-28", "2026-07-10", 1, "工程管理部", None, "2026-06-28 09:00:00"),
                    (710002, "临时排水系统不完善", "排水", "标段二", "整改中", "2026-07-01", "2026-07-15", 0, "安全环保部", None, "2026-07-01 09:00:00"),
                    (710003, "边坡防护措施不到位", "边坡", "标段一", "待整改", "2026-07-03", "2026-07-18", 0, "工程管理部", None, "2026-07-03 09:00:00"),
                    (710004, "复绿面积不足", "复绿", "标段三", "待整改", "2026-06-30", "2026-07-22", 0, "工程管理部", None, "2026-06-30 09:00:00"),
                    (710005, "水土保持监测频次不足", "监测", "标段二", "整改中", "2026-06-26", "2026-07-20", 0, "安全环保部", None, "2026-06-26 09:00:00"),
                    (710006, "取土场恢复滞后", "取土场", "标段三", "待整改", "2026-07-10", "2026-07-25", 0, "工程管理部", None, "2026-07-10 09:00:00"),
                    (710007, "施工便道水土流失", "便道", "标段一", "逾期未闭环", "2026-06-25", "2026-07-05", 1, "安全环保部", None, "2026-06-25 09:00:00"),
                    (710008, "临时沉淀池清淤完成", "排水", "标段二", "已闭环", "2026-06-20", "2026-07-04", 0, "工程管理部", "2026-07-04", "2026-06-20 09:00:00"),
                    (710009, "弃渣场截排水沟修复完成", "弃渣场", "标段一", "已闭环", "2026-06-22", "2026-07-07", 0, "安全环保部", "2026-07-07", "2026-06-22 09:00:00"),
                ],
            )

            # 6 个完整核算月，累计排放量为 12,856 tCO₂e，2026-07 当月新增 1,256 tCO₂e。
            carbon_rows = [
                # id, period, carbon_emission, output_value_wan, baseline_emission,
                # diesel_emission, electricity_emission, material_emission, other_emission
                (720001, "2026-02", 1860, 14531.0, 2069, 810, 560, 360, 130),
                (720002, "2026-03", 2240, 12308.0, 2492, 980, 672, 425, 163),
                (720003, "2026-04", 2140, 12738.0, 2380, 935, 642, 414, 149),
                (720004, "2026-05", 2680, 18873.0, 2981, 1173, 804, 518, 185),
                (720005, "2026-06", 2680, 20303.0, 2981, 1174, 804, 518, 184),
                (720006, "2026-07", 1256, 21684.5, 1398, 556, 375, 251, 74),
            ]
            cur.executemany(
                """
                INSERT INTO carbon_emission_activity
                (id, document_id, period_value, diesel_usage, electricity_usage, material_usage,
                 carbon_emission, output_value_wan, baseline_emission,
                 diesel_emission, electricity_emission, material_emission, other_emission)
                VALUES (%s, NULL, %s, 0, 0, 0, %s, %s, %s, %s, %s, %s, %s)
                """,
                carbon_rows,
            )
            cur.executemany(
                """
                INSERT INTO carbon_material_usage
                (id, document_id, period_value, material_name, material_usage, material_unit)
                VALUES (%s, NULL, %s, %s, %s, 't')
                """,
                [
                    (720501, "2026-07", "水泥", 1150),
                    (720502, "2026-07", "钢材", 680),
                    (720503, "2026-07", "沥青", 420),
                ],
            )


def main() -> int:
    ensure_columns()
    seed_rows()
    print("[PASS] E03/E04 水保与碳排业务表 V0.6 已扩展并写入首页衍生测试数据。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
