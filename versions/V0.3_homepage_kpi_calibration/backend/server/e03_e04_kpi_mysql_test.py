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


def summary_value(detail: dict, label: str):
    for item in detail.get("summary", []):
        if item.get("label") == label:
            return item.get("value")
    raise AssertionError(f"summary label missing: {label}")


def kpi_value(kpis: dict, key: str):
    for group in kpis.get("groups", []):
        for item in group.get("items", []):
            if item.get("key") == key:
                return item
    raise AssertionError(f"kpi missing: {key}")


def main() -> int:
    kpis = get_json("/api/dashboard/kpis")
    e03_card = kpi_value(kpis, "E03")
    e04_card = kpi_value(kpis, "E04")
    assert_true(e03_card.get("value") == 7, f"E03 card value mismatch: {e03_card}")
    assert_true(e04_card.get("value") == 12856, f"E04 card value mismatch: {e04_card}")

    e03 = get_json("/api/dashboard/kpi/E03")
    assert_true("water_protection_issue" in e03.get("dataSource", ""), "E03 should come from water_protection_issue")
    assert_true(summary_value(e03, "当前未闭环") == 7, "E03 open count mismatch")
    assert_true(summary_value(e03, "本月新增") == 3, "E03 monthly new mismatch")
    assert_true(summary_value(e03, "本月闭环") == 2, "E03 monthly closed mismatch")
    assert_true(summary_value(e03, "逾期未闭环") == 2, "E03 overdue mismatch")
    assert_true(summary_value(e03, "涉及标段") == 3, "E03 segment count mismatch")
    assert_true(len(e03.get("detailData", [])) == 7, "E03 detail row count mismatch")

    e04 = get_json("/api/dashboard/kpi/E04")
    assert_true("carbon_emission_activity" in e04.get("dataSource", ""), "E04 should come from carbon_emission_activity")
    assert_true(summary_value(e04, "累计碳排放") == 12856, "E04 total emission mismatch")
    assert_true(summary_value(e04, "本月新增") == 1256, "E04 monthly emission mismatch")
    assert_true(summary_value(e04, "较基准下降") == 10.1, "E04 reduction rate mismatch")
    assert_true(summary_value(e04, "单位产值排放") == 0.128, "E04 intensity mismatch")
    assert_true(len(e04.get("detailData", [])) == 4, "E04 source detail row count mismatch")

    print("[PASS] E03/E04 水保与碳排 KPI MySQL 明细聚合验收通过。")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"[FAIL] E03/E04 水保与碳排 KPI MySQL 明细聚合验收失败：{exc}", file=sys.stderr)
        raise SystemExit(1)
