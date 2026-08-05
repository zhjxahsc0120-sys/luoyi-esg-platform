"""Offline test: sample CSV content parser (no MySQL / LLM required)."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from intelligent_ingestion.content_parser import parse_file_content

SAMPLE = ROOT.parent / "public" / "samples" / "罗宜高速_2026年7月水保监测月报摘要.csv"


def main() -> None:
    assert SAMPLE.is_file(), f"sample missing: {SAMPLE}"
    result = parse_file_content(SAMPLE)
    assert result["ok"], result
    fields = result["fields"]
    assert fields.get("document_type") == "水保监测月报", fields
    assert fields.get("dust_exceed_count") == "3", fields
    assert fields.get("noise_exceed_count") == "2", fields
    assert fields.get("water_protection_issue_count") == "7", fields
    assert fields.get("monitor_date") == "2026-07-18", fields
    assert fields.get("responsible_unit") == "罗宜高速项目安全环保部", fields
    assert fields.get("project_section") == "第二合同段", fields
    assert fields.get("suggested_kpi_code") == "E03", fields
    assert result["source"] == "content"
    print("PASS content_parser_demo_test")
    print("summary:", result["summary"])
    print("fields:", len(fields))


if __name__ == "__main__":
    main()
