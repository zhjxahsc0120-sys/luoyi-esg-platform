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
    add_column_if_missing("compliance_procedure", "procedure_type", "VARCHAR(100) NULL COMMENT '审批类型'")
    add_column_if_missing("compliance_procedure", "deadline", "DATE NULL COMMENT '完成时限'")
    add_column_if_missing("compliance_procedure", "responsible_department", "VARCHAR(100) NULL COMMENT '责任部门'")
    add_column_if_missing("compliance_procedure", "progress_percent", "INT NULL COMMENT '办理进度百分比'")
    add_column_if_missing("compliance_procedure", "completed_date", "DATE NULL COMMENT '完成日期'")
    add_column_if_missing("compliance_procedure", "expected_complete_date", "DATE NULL COMMENT '预计完成日期'")

    add_column_if_missing("permit_record", "permit_type", "VARCHAR(100) NULL COMMENT '许可类型'")
    add_column_if_missing("permit_record", "responsible_department", "VARCHAR(100) NULL COMMENT '责任部门'")

    add_column_if_missing("rectification_record", "issue_level", "VARCHAR(50) NULL COMMENT '问题等级'")
    add_column_if_missing("rectification_record", "deadline", "DATE NULL COMMENT '整改时限'")
    add_column_if_missing("rectification_record", "responsible_department", "VARCHAR(100) NULL COMMENT '责任部门'")
    add_column_if_missing("rectification_record", "check_batch", "VARCHAR(100) NULL COMMENT '检查批次，用于统计涉及检查次数'")

    add_column_if_missing("compliance_material_gap", "module_code", "VARCHAR(10) NULL COMMENT '所属 ESG 模块'")
    add_column_if_missing("compliance_material_gap", "deadline", "DATE NULL COMMENT '提交时限'")
    add_column_if_missing("compliance_material_gap", "action_text", "VARCHAR(30) NULL COMMENT '页面操作文案'")


def seed_rows() -> None:
    with mysql_connect() as conn:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM compliance_procedure WHERE id BETWEEN 310001 AND 310099")
            cur.execute("DELETE FROM permit_record WHERE id BETWEEN 320001 AND 320099")
            cur.execute("DELETE FROM rectification_record WHERE id BETWEEN 330001 AND 330099")
            cur.execute("DELETE FROM compliance_material_gap WHERE id BETWEEN 340001 AND 340099")

            cur.executemany(
                """
                INSERT INTO compliance_procedure
                (id, procedure_name, procedure_type, status, impact_node, overdue, deadline,
                 responsible_department, progress_percent, created_at, completed_date, expected_complete_date)
                VALUES
                (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                [
                    (310001, "水土保持设施验收", "行政许可", "待评审", "水保验收", 0, "2026-07-20", "安全环保部", 70, "2026-06-20 09:00:00", None, "2026-07-20"),
                    (310002, "环评变更审批", "行政许可", "待批复", "环评批复", 0, "2026-07-25", "安全环保部", 85, "2026-06-25 09:00:00", None, "2026-07-25"),
                    (310003, "林地占用审批", "行政许可", "资料补正", "用地手续", 0, "2026-07-18", "工程管理部", 40, "2026-06-28 09:00:00", None, "2026-07-18"),
                    (310004, "规划许可变更", "行政许可", "逾期未办", "规划许可", 1, "2026-07-05", "总工办", 30, "2026-06-10 09:00:00", None, None),
                    (310005, "消防设计审查", "行政许可", "待审查", "消防审查", 0, "2026-08-05", "工程管理部", 60, "2026-07-13 09:00:00", None, "2026-07-31"),
                    (310006, "临建备案确认", "备案", "已完成", "临建备案", 0, "2026-07-08", "工程管理部", 100, "2026-06-01 09:00:00", "2026-07-08", None),
                    (310007, "专项施工许可备案", "备案", "已完成", "专项备案", 0, "2026-07-10", "安全环保部", 100, "2026-06-08 09:00:00", "2026-07-10", None),
                ],
            )

            cur.executemany(
                """
                INSERT INTO permit_record
                (id, permit_name, permit_no, permit_type, expire_date, status, responsible_department, created_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """,
                [
                    (320001, "安全生产许可证", "(鄂)JZ安许证字第XXXXX号", "安全生产", "2026-07-20", "临期", "安全环保部", "2026-06-01 09:00:00"),
                    (320002, "排污许可证", "鄂环排证字第XXXXX号", "环境保护", "2026-07-28", "临期", "安全环保部", "2026-06-01 09:00:00"),
                    (320003, "特种设备使用登记证", "鄂特登字第XXXXX号", "特种设备", "2026-08-05", "临期", "工程管理部", "2026-06-01 09:00:00"),
                    (320004, "道路运输经营许可证", "鄂交运管许可字第XXXXX号", "道路运输", "2026-08-10", "临期", "物资设备部", "2026-06-01 09:00:00"),
                    (320005, "临时占用林地审批", "鄂林资临字第XXXXX号", "林地占用", "2026-07-05", "逾期", "工程管理部", "2026-06-01 09:00:00"),
                ],
            )

            cur.executemany(
                """
                INSERT INTO rectification_record
                (id, item_name, status, source_type, issue_level, overdue, deadline,
                 responsible_department, check_batch, closed_date, created_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                [
                    (330001, "安全管理制度不完善", "整改中", "省交通厅检查", "一般", 0, "2026-07-15", "安全环保部", "2026省厅检查", None, "2026-07-01 09:00:00"),
                    (330002, "环保设施运行台账不全", "整改中", "生态环境局检查", "一般", 0, "2026-07-18", "安全环保部", "2026生态环境局检查", None, "2026-07-02 09:00:00"),
                    (330003, "工程资料归档不及时", "待整改", "业主专项检查", "一般", 0, "2026-07-20", "工程管理部", "2026业主专项检查", None, "2026-06-28 09:00:00"),
                    (330004, "应急预案未及时修订", "逾期", "省交通厅检查", "较大", 1, "2026-07-10", "安全环保部", "2026省厅检查", None, "2026-06-25 09:00:00"),
                    (330005, "监理履职不到位", "逾期", "业主专项检查", "一般", 1, "2026-07-08", "监理单位", "2026业主专项检查", None, "2026-06-20 09:00:00"),
                    (330006, "合同管理不规范", "待整改", "审计检查", "一般", 0, "2026-07-25", "合约法务部", "2026业主专项检查", None, "2026-06-28 09:00:00"),
                    (330007, "临时用地资料归档缺项", "已关闭", "业主专项检查", "一般", 0, "2026-07-05", "工程管理部", "2026业主专项检查", "2026-07-05", "2026-06-20 09:00:00"),
                    (330008, "风险告知牌更新滞后", "已关闭", "省交通厅检查", "一般", 0, "2026-07-06", "安全环保部", "2026省厅检查", "2026-07-06", "2026-06-22 09:00:00"),
                    (330009, "材料验收记录签章不全", "已关闭", "审计检查", "一般", 0, "2026-07-12", "物资设备部", "2026业主专项检查", "2026-07-12", "2026-06-25 09:00:00"),
                ],
            )

            cur.executemany(
                """
                INSERT INTO compliance_material_gap
                (id, task_id, material_name, module_code, deadline, responsible_unit, status, action_text, created_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                [
                    (340001, "t-safety-cost", "安全生产费用使用台账", "S", "2026-07-15", "安全环保部", "待提交", "上传", "2026-07-01 09:00:00"),
                    (340002, "t-env-quarter", "环境监测季报", "E", "2026-07-20", "安全环保部", "待提交", "上传", "2026-07-01 09:00:00"),
                    (340003, "t-compliance-eval", "合规性评价报告", "G", "2026-07-25", "合约法务部", "待提交", "上传", "2026-07-01 09:00:00"),
                    (340004, "t-emergency-drill", "应急预案演练记录", "S", "2026-07-10", "安全环保部", "逾期", "补交", "2026-06-25 09:00:00"),
                ],
            )


def main() -> int:
    ensure_columns()
    seed_rows()
    print("✅ G01-G04 合规类业务明细表 V0.3 已扩展并写入演示台账数据。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
