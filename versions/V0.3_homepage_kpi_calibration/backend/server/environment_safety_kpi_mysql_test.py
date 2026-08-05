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
    e01 = get_json("/api/dashboard/kpi/E01")
    assert_true("env_monitoring_record" in e01.get("dataSource", ""), "E01 should come from env_monitoring_record")
    assert_true(summary_value(e01, "当前超标项") == 2, "E01 current exceed mismatch")
    assert_true(summary_value(e01, "已复测") == 1, "E01 rechecked mismatch")
    assert_true(summary_value(e01, "待复测") == 1, "E01 pending recheck mismatch")
    category = {item["name"]: item["value"] for item in e01.get("categoryData", [])}
    assert_true(category == {"扬尘": 1, "噪声": 1, "合计": 2}, f"E01 category mismatch: {category}")
    assert_true(len(e01.get("detailData", [])) == 2, "E01 detail row count mismatch")

    e02 = get_json("/api/dashboard/kpi/E02")
    assert_true("env_issue_record" in e02.get("dataSource", ""), "E02 should come from env_issue_record")
    assert_true(summary_value(e02, "当前未闭环") == 5, "E02 open count mismatch")
    assert_true(summary_value(e02, "本月新增") == 2, "E02 monthly new mismatch")
    assert_true(summary_value(e02, "本月闭环") == 3, "E02 monthly closed mismatch")
    assert_true(summary_value(e02, "逾期未闭环") == 1, "E02 overdue mismatch")
    status_data = {item["name"]: item["value"] for item in e02.get("statusData", [])}
    assert_true(status_data == {"整改中": 2, "待复查": 2, "待销项": 1}, f"E02 statusData mismatch: {status_data}")
    assert_true("逾期" not in status_data, "E02 statusData must not include overdue as primary status")
    assert_true(any(item.get("overdue") is True and item.get("mainStatus") == "整改中" for item in e02.get("detailData", [])), "E02 overdue flag/mainStatus mismatch")

    s02 = get_json("/api/dashboard/kpi/S02")
    assert_true("safety_risk_point" in s02.get("dataSource", ""), "S02 should come from safety_risk_point")
    assert_true(summary_value(s02, "较大风险点") == 4, "S02 larger risk mismatch")
    assert_true(summary_value(s02, "重大风险点") == 2, "S02 major risk mismatch")
    assert_true(summary_value(s02, "本月新增") == 1, "S02 monthly new mismatch")
    assert_true(summary_value(s02, "本月销号") == 2, "S02 monthly cancelled mismatch")
    assert_true(summary_value(s02, "涉及工点") == 4, "S02 location count mismatch")
    statuses = {item.get("status") for item in s02.get("detailData", [])}
    assert_true(statuses <= {"持续管控", "正常管控"}, f"S02 status wording mismatch: {statuses}")

    print("✅ E01/E02/S02 环境与安全 KPI MySQL 明细聚合验收通过。")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"❌ E01/E02/S02 环境与安全 KPI MySQL 明细聚合验收失败：{exc}", file=sys.stderr)
        raise SystemExit(1)

