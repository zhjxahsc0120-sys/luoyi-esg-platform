from __future__ import annotations

import json
import sys
from urllib.request import urlopen


BASE_URL = "http://127.0.0.1:8765"


def get_json(path: str) -> dict:
    with urlopen(f"{BASE_URL}{path}", timeout=10) as response:
        return json.loads(response.read().decode("utf-8"))


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def summary_value(detail: dict, label: str) -> int:
    for item in detail.get("summary", []):
        if item.get("label") == label:
            return int(item.get("value"))
    raise AssertionError(f"summary label missing: {label}")


def main() -> int:
    cases = {
        "G01": ("compliance_procedure", 5, {"未完成事项": 5, "本月新增": 1, "本月完成": 2, "逾期未办": 1}),
        "G02": ("permit_record", 5, {"临期许可": 4, "逾期许可": 1, "30日内到期": 4, "涉及部门": 3}),
        "G03": ("rectification_record", 6, {"未关闭事项": 6, "本月新增": 2, "本月关闭": 3, "逾期未关闭": 2, "涉及检查": 3}),
        "G04": ("compliance_material_gap", 4, {"待补齐资料": 4, "本月需提交": 3, "逾期未提交": 1, "涉及模块": 3}),
    }

    for code, (source_table, expected_rows, expected_summary) in cases.items():
        detail = get_json(f"/api/dashboard/kpi/{code}")
        assert_true(source_table in detail.get("dataSource", ""), f"{code} should come from {source_table}")
        assert_true(len(detail.get("detailData", [])) == expected_rows, f"{code} detail row count mismatch")
        for label, expected in expected_summary.items():
            assert_true(summary_value(detail, label) == expected, f"{code} {label} mismatch")

    print("✅ G01-G04 合规类 KPI MySQL 明细聚合验收通过。")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"❌ G01-G04 合规类 KPI MySQL 明细聚合验收失败：{exc}", file=sys.stderr)
        raise SystemExit(1)
