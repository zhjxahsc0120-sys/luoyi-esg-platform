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
    add_column_if_missing("env_monitoring_record", "monitor_point", "VARCHAR(255) NULL COMMENT '监测点'")
    add_column_if_missing("env_monitoring_record", "factor_name", "VARCHAR(100) NULL COMMENT '监测因子'")
    add_column_if_missing("env_monitoring_record", "detected_value", "VARCHAR(50) NULL COMMENT '检测值'")
    add_column_if_missing("env_monitoring_record", "limit_value", "VARCHAR(50) NULL COMMENT '标准限值'")
    add_column_if_missing("env_monitoring_record", "exceed_multiple", "DECIMAL(10,2) NULL COMMENT '超标倍数'")
    add_column_if_missing("env_monitoring_record", "recheck_status", "VARCHAR(30) NULL COMMENT '复测状态'")

    add_column_if_missing("env_issue_record", "issue_name", "VARCHAR(255) NULL COMMENT '问题名称'")
    add_column_if_missing("env_issue_record", "issue_level", "VARCHAR(50) NULL COMMENT '问题等级'")
    add_column_if_missing("env_issue_record", "responsible_department", "VARCHAR(100) NULL COMMENT '责任部门'")
    add_column_if_missing("env_issue_record", "deadline", "DATE NULL COMMENT '整改截止'")
    add_column_if_missing("env_issue_record", "duration_days", "INT NULL COMMENT '处置时长'")

    add_column_if_missing("safety_risk_point", "risk_type", "VARCHAR(100) NULL COMMENT '风险类型'")
    add_column_if_missing("safety_risk_point", "control_start_date", "DATE NULL COMMENT '管控起始日期'")
    add_column_if_missing("safety_risk_point", "cancelled_date", "DATE NULL COMMENT '销号日期'")


def seed_rows() -> None:
    with mysql_connect() as conn:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM env_monitoring_record WHERE id BETWEEN 410001 AND 410099")
            cur.execute("DELETE FROM env_issue_record WHERE id BETWEEN 420001 AND 420099")
            cur.execute("DELETE FROM safety_risk_point WHERE id BETWEEN 430001 AND 430099")

            cur.executemany(
                """
                INSERT INTO env_monitoring_record
                (id, monitor_date, monitor_type, exceed_count, dust_exceed_count, noise_exceed_count,
                 monitor_point, factor_name, detected_value, limit_value, exceed_multiple, recheck_status,
                 module_code, created_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 'E', %s)
                """,
                [
                    (410001, "2026-07-05", "噪声", 1, 0, 1, "K12+000 路基监测点", "噪声/昼间等效声级", "68.2 dB(A)", "70 dB(A)", 0.97, "已复测", "2026-07-05 10:00:00"),
                    (410002, "2026-07-08", "扬尘", 1, 1, 0, "K18+500 弃渣场监测点", "扬尘/PM10", "185 μg/m³", "150 μg/m³", 1.23, "待复测", "2026-07-08 10:00:00"),
                    (410003, "2026-06-25", "噪声", 0, 0, 0, "K24+000 桥梁施工点", "噪声/夜间等效声级", "52 dB(A)", "55 dB(A)", 0.95, "正常", "2026-06-25 10:00:00"),
                ],
            )

            cur.executemany(
                """
                INSERT INTO env_issue_record
                (id, issue_type, issue_name, issue_count, issue_status, overdue, found_date, closed_date,
                 issue_level, responsible_department, deadline, duration_days, created_at)
                VALUES (%s, %s, %s, 1, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                [
                    (420001, "扬尘管控", "弃渣场扬尘控制不到位", "整改中", 0, "2026-07-02", None, "一般", "工程管理部", "2026-07-15", 13, "2026-07-02 09:00:00"),
                    (420002, "废水处理", "施工废水处理设施故障", "整改中", 1, "2026-07-05", None, "较大", "安全环保部", "2026-07-10", 18, "2026-07-05 09:00:00"),
                    (420003, "水土保持", "临时堆土场防护不足", "待复查", 0, "2026-06-28", None, "一般", "工程管理部", "2026-07-20", 15, "2026-06-28 09:00:00"),
                    (420004, "噪声扰民", "噪声超标投诉处理", "待复查", 0, "2026-06-26", None, "一般", "安全环保部", "2026-07-18", 14, "2026-06-26 09:00:00"),
                    (420005, "生态保护", "生态敏感区施工管控", "待销项", 0, "2026-06-25", None, "重大", "总工办", "2026-07-25", 15, "2026-06-25 09:00:00"),
                    (420006, "水保整改", "边坡临时排水沟修复", "已闭环", 0, "2026-06-20", "2026-07-04", "一般", "工程管理部", "2026-07-04", 14, "2026-06-20 09:00:00"),
                    (420007, "扬尘治理", "施工便道洒水频次不足", "已闭环", 0, "2026-06-22", "2026-07-07", "一般", "工程管理部", "2026-07-07", 15, "2026-06-22 09:00:00"),
                    (420008, "弃渣场管理", "弃渣场截排水沟清淤", "已闭环", 0, "2026-06-25", "2026-07-12", "一般", "安全环保部", "2026-07-12", 17, "2026-06-25 09:00:00"),
                ],
            )

            cur.executemany(
                """
                INSERT INTO safety_risk_point
                (id, risk_name, risk_level, control_status, control_measure, location,
                 risk_type, control_start_date, cancelled_date, created_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                [
                    (430001, "隧道施工塌方风险", "重大", "持续管控", "超前地质预报、监控量测、短进尺施工", "K25+300 隧道出口", "隧道施工", "2026-06-01", None, "2026-06-01 09:00:00"),
                    (430002, "高边坡坍塌风险", "重大", "持续管控", "分级开挖、边坡监测、临时支护", "K18+200 路基边坡", "路基施工", "2026-05-15", None, "2026-05-15 09:00:00"),
                    (430003, "桥梁吊装作业风险", "较大", "持续管控", "吊装方案审批、旁站监护", "K32+500 大桥", "桥梁施工", "2026-07-01", None, "2026-07-01 09:00:00"),
                    (430004, "深基坑坍塌风险", "较大", "持续管控", "基坑支护、排水降水、巡查监测", "K32+500 大桥", "基坑施工", "2026-06-25", None, "2026-06-25 09:00:00"),
                    (430005, "爆破作业风险", "较大", "持续管控", "爆破警戒、审批交底、专业作业", "K28+000 石方段", "爆破作业", "2026-06-10", None, "2026-06-10 09:00:00"),
                    (430006, "起重机械倾覆风险", "较大", "持续管控", "设备验收、地基承载检查、限载作业", "K28+000 石方段", "起重作业", "2026-06-20", None, "2026-06-20 09:00:00"),
                    (430007, "临边防护缺失风险", "较大", "已销号", "临边防护补强并复查", "K10+200 通道", "临边作业", "2026-06-15", "2026-07-03", "2026-06-15 09:00:00"),
                    (430008, "模板支架稳定风险", "较大", "已销号", "支架复核验算并加固", "K30+100 小桥", "模板支架", "2026-06-18", "2026-07-09", "2026-06-18 09:00:00"),
                ],
            )


def main() -> int:
    ensure_columns()
    seed_rows()
    print("✅ E01/E02/S02 环境与安全风险明细表 V0.4 已扩展并写入演示台账数据。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
