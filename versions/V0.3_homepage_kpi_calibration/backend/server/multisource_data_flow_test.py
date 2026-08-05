from __future__ import annotations

import sys

sys.path.insert(0, "server")
from mysql_api import query_one, query_all  # noqa: E402


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def count(table: str) -> int:
    return int(query_one(f"SELECT COUNT(*) AS c FROM {table}")["c"])


def main() -> int:
    expected_min_counts = {
        "data_source_registry": 11,
        "data_mapping_rule": 14,
        "indicator_source_dependency": 15,
        "data_ingestion_job": 3,
        "source_record_trace": 4,
        "data_quality_check_result": 4,
        "indicator_calculation_job": 2,
        "indicator_history": 2,
    }
    for table, expected in expected_min_counts.items():
        actual = count(table)
        assert_true(actual >= expected, f"{table} count mismatch: expected >= {expected}, actual {actual}")

    e01_deps = query_all(
        """
        SELECT source_table
        FROM indicator_source_dependency
        WHERE indicator_code = 'E01' AND enabled = 1
        """
    )
    assert_true(any(row["source_table"] == "env_monitoring_record" for row in e01_deps), "E01 dependency missing")

    g02_trace = query_one(
        """
        SELECT *
        FROM source_record_trace
        WHERE target_table = 'permit_record' AND target_record_id = '320005'
        """
    )
    assert_true(g02_trace is not None, "G02 permit trace missing")

    quality_warn = query_one(
        """
        SELECT COUNT(*) AS c
        FROM data_quality_check_result
        WHERE check_status = 'WARN'
        """
    )
    assert_true(int(quality_warn["c"]) >= 1, "quality warning sample missing")

    history = query_one(
        """
        SELECT *
        FROM indicator_history
        WHERE indicator_code = 'G02' AND result_date = '2026-07-13'
        """
    )
    assert_true(history is not None and int(history["result_value"]) == 5, "G02 indicator history mismatch")

    print("✅ 多源数据流 V1.0 治理表与最小闭环样例验收通过。")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"❌ 多源数据流 V1.0 验收失败：{exc}", file=sys.stderr)
        raise SystemExit(1)

