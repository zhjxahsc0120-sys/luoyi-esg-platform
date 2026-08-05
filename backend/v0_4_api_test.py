"""Read-only smoke tests for the V0.4 governance API data layer.

These tests intentionally do not create, update, or delete business records.
Set the database connection environment variables before running the module.
"""

from __future__ import annotations

import unittest

import mysql_api
from mysql_db import mysql_connect, MYSQL_CONFIG


class V04ApiReadOnlyTests(unittest.TestCase):
    def test_v04_schema_contract(self) -> None:
        with mysql_connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT COUNT(*) AS n
                    FROM information_schema.COLUMNS
                    WHERE TABLE_SCHEMA = %s
                      AND TABLE_NAME = 'e_rectification_task'
                      AND COLUMN_NAME IN ('rectification_completed_date', 'rectification_completed_by')
                    """,
                    (MYSQL_CONFIG["database"],),
                )
                self.assertEqual(cur.fetchone()["n"], 2)
                cur.execute(
                    """
                    SELECT COUNT(*) AS n
                    FROM information_schema.TABLES
                    WHERE TABLE_SCHEMA = %s
                      AND TABLE_NAME = 'special_plan_approval'
                    """,
                    (MYSQL_CONFIG["database"],),
                )
                self.assertEqual(cur.fetchone()["n"], 1)
                cur.execute(
                    """
                    SELECT COUNT(*) AS n
                    FROM information_schema.COLUMNS
                    WHERE TABLE_SCHEMA = %s
                      AND TABLE_NAME = 'special_plan_approval'
                      AND COLUMN_NAME = 'approval_file_id'
                    """,
                    (MYSQL_CONFIG["database"],),
                )
                self.assertEqual(cur.fetchone()["n"], 1)

    def test_rectification_read_contract(self) -> None:
        payload = mysql_api.get_rectification_tasks()
        self.assertIn("total", payload)
        self.assertIn("items", payload)
        if payload["items"]:
            item = payload["items"][0]
            self.assertIn("rectificationCompletedDate", item)
            self.assertIn("rectificationCompletedBy", item)

    def test_special_plan_read_contract_and_file_shape(self) -> None:
        payload = mysql_api.get_special_plans()
        self.assertIn("total", payload)
        self.assertIn("items", payload)
        for item in payload["items"]:
            self.assertIn("approvalFileId", item)
            self.assertIn("approvalFile", item)
            if item["approvalFile"] is not None:
                self.assertIn("originalName", item["approvalFile"])

    def test_dashboard_kpi_regression_shape(self) -> None:
        payload = mysql_api.get_dashboard_kpis()
        keys = {item.get("key") for item in payload.get("items", [])}
        self.assertEqual(len(keys), 12)
        self.assertIn("E04", keys)
        self.assertIn("S03", keys)
        self.assertIn("G04", keys)

    def test_invalid_create_is_rejected_before_write(self) -> None:
        with self.assertRaises(ValueError):
            mysql_api.create_special_plan({})

    def test_invalid_rectification_patch_is_rejected_before_write(self) -> None:
        with self.assertRaises(ValueError):
            mysql_api.update_rectification_task(928001, {"taskStatus": "COMPLETED"})


if __name__ == "__main__":
    unittest.main(verbosity=2)
