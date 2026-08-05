from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal, ROUND_HALF_UP
from typing import Any

from mysql_db import mysql_connect


MONTHLY_STATUSES = (
    "待提交",
    "待确认",
    "待补正",
    "校验通过",
    "不适用（已确认）",
)


def _json_date(value: Any) -> str | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.date().isoformat()
    if isinstance(value, date):
        return value.isoformat()
    return str(value)


def get_monthly_report_readiness(report_period: str) -> dict | None:
    with mysql_connect() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT id, report_period
                FROM monthly_report_cycle
                WHERE report_period = %s
                ORDER BY id DESC
                LIMIT 1
                """,
                (report_period,),
            )
            cycle = cur.fetchone()
            if cycle is None:
                return None
            cycle_id = cycle["id"]

            cur.execute(
                """
                SELECT
                  SUM(CASE
                        WHEN include_in_denominator = 1
                         AND monthly_status <> '不适用（已确认）'
                        THEN 1 ELSE 0
                      END) AS denominator,
                  SUM(CASE
                        WHEN include_in_denominator = 1
                         AND monthly_status = '校验通过'
                        THEN 1 ELSE 0
                      END) AS numerator,
                  MIN(CASE
                        WHEN include_in_denominator = 1
                         AND monthly_status <> '不适用（已确认）'
                        THEN deadline
                      END) AS deadline_start,
                  MAX(CASE
                        WHEN include_in_denominator = 1
                         AND monthly_status <> '不适用（已确认）'
                        THEN deadline
                      END) AS deadline_end
                FROM monthly_report_task_instance
                WHERE report_cycle_id = %s
                """,
                (cycle_id,),
            )
            aggregate = cur.fetchone() or {}

            cur.execute(
                """
                SELECT monthly_status, COUNT(*) AS count
                FROM monthly_report_task_instance
                WHERE report_cycle_id = %s
                  AND (include_in_denominator = 1 OR monthly_status = '不适用（已确认）')
                GROUP BY monthly_status
                """,
                (cycle_id,),
            )
            status_rows = list(cur.fetchall())

            cur.execute(
                """
                SELECT task_code, task_name, responsible_unit, deadline, monthly_status
                FROM monthly_report_task_instance
                WHERE report_cycle_id = %s
                  AND include_in_denominator = 1
                  AND monthly_status NOT IN ('校验通过', '不适用（已确认）')
                ORDER BY FIELD(monthly_status, '待提交', '待确认', '待补正'), deadline, task_code
                """,
                (cycle_id,),
            )
            exception_rows = list(cur.fetchall())

    denominator = int(aggregate.get("denominator") or 0)
    numerator = int(aggregate.get("numerator") or 0)
    if denominator:
        exact_decimal = (Decimal(numerator) * Decimal(100) / Decimal(denominator)).quantize(
            Decimal("0.1"), rounding=ROUND_HALF_UP
        )
        progress = int(exact_decimal.quantize(Decimal("1"), rounding=ROUND_HALF_UP))
    else:
        exact_decimal = Decimal("0.0")
        progress = 0

    status_counts = {status: 0 for status in MONTHLY_STATUSES}
    for row in status_rows:
        status = row.get("monthly_status")
        if status in status_counts:
            status_counts[status] = int(row.get("count") or 0)

    return {
        "metricName": "月报资料归集率",
        "reportPeriod": cycle["report_period"],
        "numerator": numerator,
        "denominator": denominator,
        "exactProgress": float(exact_decimal),
        "progress": progress,
        "deadlineStart": _json_date(aggregate.get("deadline_start")),
        "deadlineEnd": _json_date(aggregate.get("deadline_end")),
        "statusCounts": status_counts,
        "exceptionTasks": [
            {
                "taskCode": row.get("task_code"),
                "taskName": row.get("task_name"),
                "responsibleUnit": row.get("responsible_unit"),
                "deadline": _json_date(row.get("deadline")),
                "monthlyStatus": row.get("monthly_status"),
            }
            for row in exception_rows
        ],
    }
