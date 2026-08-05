from __future__ import annotations

import json
import sys
from urllib.request import urlopen

sys.path.insert(0, "server")
from mysql_api import query_one  # noqa: E402


BASE_URL = "http://127.0.0.1:8765"


def get_json(path: str) -> dict:
    with urlopen(f"{BASE_URL}{path}", timeout=10) as response:
        return json.loads(response.read().decode("utf-8"))


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> int:
    health = get_json("/health")
    assert_true(health.get("mysql", {}).get("ok") is True, "MySQL must be online for snapshot test")

    kpi_count = query_one("SELECT COUNT(*) AS c FROM dashboard_kpi_detail_snapshot")["c"]
    topic_count = query_one("SELECT COUNT(*) AS c FROM dashboard_topic_snapshot")["c"]
    panel_count = query_one("SELECT COUNT(*) AS c FROM dashboard_panel_snapshot")["c"]
    assert_true(kpi_count == 11, f"KPI detail snapshot count mismatch: {kpi_count}")
    assert_true(topic_count == 2, f"topic snapshot count mismatch: {topic_count}")
    assert_true(panel_count == 1, f"panel snapshot count mismatch: {panel_count}")

    for code in ["E01", "E02", "S02", "S03", "S04", "G01", "G02", "G03", "G04"]:
        detail = get_json(f"/api/dashboard/kpi/{code}")
        assert_true(detail.get("key") == code, f"{code} endpoint key mismatch")
        assert_true(detail.get("isMock") is False, f"{code} should not be mock")
        assert_true(len(detail.get("detailData", [])) >= 1, f"{code} detail data missing")

    carbon = get_json("/api/dashboard/topics/carbon")
    assert_true(carbon.get("key") == "CARBON", "carbon topic key mismatch")
    assert_true("cumulative" in carbon.get("topicData", {}), "carbon topicData missing cumulative")

    monthly = get_json("/api/dashboard/topics/monthly-report")
    assert_true(monthly.get("key") == "MONTHLY", "monthly topic key mismatch")
    assert_true("chapters" in monthly.get("topicData", {}), "monthly topicData missing chapters")

    panels = get_json("/api/dashboard/panels")
    assert_true(len(panels.get("compliance", {}).get("metrics", [])) >= 4, "compliance panel missing")
    assert_true(len(panels.get("carbon", {}).get("measures", [])) >= 1, "carbon measures missing")
    assert_true(len(panels.get("gis", {}).get("routePoints", [])) >= 1, "GIS route points missing")

    print("✅ 领导层首页 MySQL 快照验收通过：11项KPI详情、2个专题、首页面板均可由 MySQL 支撑。")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"❌ 领导层首页 MySQL 快照验收失败：{exc}", file=sys.stderr)
        raise SystemExit(1)

