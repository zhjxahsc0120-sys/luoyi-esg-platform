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
    s03 = get_json("/api/dashboard/kpi/S03")
    assert_true("labor_dispute_record" in s03.get("dataSource", ""), "S03 should come from labor_dispute_record")
    assert_true(summary_value(s03, "未办结纠纷") == 4, "S03 open count mismatch")
    assert_true(summary_value(s03, "本月新增") == 2, "S03 monthly new mismatch")
    assert_true(summary_value(s03, "本月办结") == 1, "S03 monthly closed mismatch")
    assert_true(summary_value(s03, "涉及人数") == 18, "S03 people mismatch")
    assert_true(summary_value(s03, "涉及金额") == 68, "S03 amount mismatch")
    assert_true(len(s03.get("detailData", [])) == 4, "S03 detail row count mismatch")

    s04 = get_json("/api/dashboard/kpi/S04")
    assert_true("appeal_record" in s04.get("dataSource", ""), "S04 should come from appeal_record")
    assert_true(summary_value(s04, "未办结诉求") == 3, "S04 open count mismatch")
    assert_true(summary_value(s04, "本月新增") == 2, "S04 monthly new mismatch")
    assert_true(summary_value(s04, "本月办结") == 4, "S04 monthly closed mismatch")
    assert_true(summary_value(s04, "逾期未办") == 1, "S04 overdue mismatch")
    assert_true(summary_value(s04, "平均办理时长") == 7, "S04 duration mismatch")
    assert_true(len(s04.get("detailData", [])) == 3, "S04 detail row count mismatch")

    print("✅ S03/S04 社会责任 KPI MySQL 明细聚合验收通过。")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"❌ S03/S04 社会责任 KPI MySQL 明细聚合验收失败：{exc}", file=sys.stderr)
        raise SystemExit(1)

