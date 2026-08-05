from __future__ import annotations

import sys
import unittest
from pathlib import Path

SERVER_DIR = Path(__file__).resolve().parent
if str(SERVER_DIR) not in sys.path:
    sys.path.insert(0, str(SERVER_DIR))

from ai_document_analysis.service import (  # noqa: E402
    MemoryAnalysisRepository,
    analyze_document,
    build_analysis_result,
    get_analysis_result,
)
from migrations.migration_001_ai_document_analysis import (  # noqa: E402
    CREATE_STATEMENTS,
    DROP_STATEMENTS,
    TABLE_NAMES,
)


class MigrationStructureTest(unittest.TestCase):
    def test_only_six_independent_ai_tables_are_created(self) -> None:
        self.assertEqual(
            TABLE_NAMES,
            (
                "ai_document_analysis",
                "ai_extracted_project_info",
                "ai_extracted_progress",
                "ai_extracted_safety",
                "ai_extracted_environment",
                "ai_extracted_resource",
            ),
        )
        self.assertEqual(len(CREATE_STATEMENTS), 6)
        self.assertEqual(len(DROP_STATEMENTS), 6)
        ddl = "\n".join(CREATE_STATEMENTS).lower()
        for table_name in TABLE_NAMES:
            self.assertIn(f"create table if not exists {table_name}", ddl)
        self.assertIn("excluded_from_dashboard", ddl)
        self.assertIn("on delete cascade", ddl)

    def test_migration_does_not_target_existing_business_tables(self) -> None:
        ddl = "\n".join(CREATE_STATEMENTS).lower()
        for existing_table in (
            "indicator_result",
            "e01_monitor_point",
            "water_protection_issue",
            "carbon_emission_result",
            "gis_feature",
        ):
            self.assertNotIn(f"create table if not exists {existing_table}", ddl)
            self.assertNotIn(f"alter table {existing_table}", ddl)


class AnalysisContractTest(unittest.TestCase):
    def test_may_engineering_report_contains_required_dimensions(self) -> None:
        file_name, result = build_analysis_result(985)
        payload = result.to_dict()
        self.assertEqual(file_name, "罗宜高速2026年5月工程监理月报.pdf")
        self.assertEqual(payload["document"]["type"], "工程监理月报")
        self.assertEqual(payload["document"]["period"], "2026-05")
        self.assertEqual(payload["data"]["project_info"]["route_length"], 78.6)
        self.assertEqual(payload["data"]["project_info"]["section_count"], 5)
        self.assertEqual(len(payload["data"]["progress"]), 4)
        self.assertEqual(
            [item["work_content"] for item in payload["data"]["progress"]],
            ["路基填筑、边坡防护", "桥梁下部结构施工", "隧道初期支护", "互通区土石方及结构物施工"],
        )
        self.assertIn("environment", payload["data"])
        self.assertIn("resource", payload["data"])
        self.assertIn("review", payload)

    def test_june_safety_report_contains_acceptance_values(self) -> None:
        _, result = build_analysis_result(987)
        payload = result.to_dict()
        safety = payload["data"]["safety"]
        self.assertEqual(payload["document"]["type"], "安全监理月报")
        self.assertEqual(safety["safe_days"], 355)
        self.assertEqual(safety["risk_point_count"], 2)
        self.assertEqual(safety["unfinished_issue_count"], 4)

    def test_memory_repository_round_trip_and_dashboard_gate(self) -> None:
        repository = MemoryAnalysisRepository()
        created = analyze_document({"fileId": 985}, repository=repository)
        fetched = get_analysis_result(created["analysis_id"], repository=repository)
        self.assertIsNotNone(fetched)
        assert fetched is not None
        self.assertEqual(fetched["analysis_id"], created["analysis_id"])
        self.assertEqual(fetched["ingestion_status"], "stored")
        self.assertTrue(fetched["excluded_from_dashboard"])
        self.assertEqual(fetched["data"]["project_info"]["project_name"], "罗宜高速公路项目")

    def test_one_file_is_sufficient_and_bad_id_is_rejected(self) -> None:
        repository = MemoryAnalysisRepository()
        payload = analyze_document({"fileId": 987}, repository=repository)
        self.assertEqual(payload["source_file_id"], 987)
        with self.assertRaisesRegex(ValueError, "正整数"):
            analyze_document({"fileId": 0}, repository=repository)


if __name__ == "__main__":
    unittest.main()
