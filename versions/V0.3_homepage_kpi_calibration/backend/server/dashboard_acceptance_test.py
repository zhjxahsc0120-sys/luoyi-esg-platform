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


def assert_detail_shape(detail: dict, key: str) -> None:
    required = [
        "key",
        "fullName",
        "theme",
        "summary",
        "chartTitle",
        "detailTitle",
        "detailColumns",
        "detailData",
        "dataSource",
        "updateTime",
    ]
    missing = [name for name in required if name not in detail]
    assert_true(not missing, f"{key} detail missing fields: {missing}")
    assert_true(detail["key"] == key, f"{key} detail key mismatch")
    assert_true(len(detail.get("summary", [])) >= 4, f"{key} summary should have cards")
    assert_true(len(detail.get("detailColumns", [])) >= 4, f"{key} detail columns should exist")
    assert_true(len(detail.get("detailData", [])) >= 1, f"{key} detail data should exist")


def main() -> int:
    kpis = get_json("/api/dashboard/kpis")
    groups = kpis.get("groups", [])
    assert_true(len(groups) == 3, "dashboard kpi groups should include E/S/G")
    kpi_keys = [item["key"] for group in groups for item in group.get("items", [])]
    assert_true(len(kpi_keys) == 12, "dashboard should expose 12 KPI cards")

    s01 = get_json("/api/dashboard/kpi/S01")
    assert_true(s01.get("continuousDays") == 368, "S01 safety detail should keep continuous days")

    for key in [k for k in kpi_keys if k != "S01"]:
      detail = get_json(f"/api/dashboard/kpi/{key}")
      assert_detail_shape(detail, key)
      assert_true(detail.get("isMock") is False, f"{key} should be API payload, not frontend-only mock")

    carbon = get_json("/api/dashboard/topics/carbon")
    assert_detail_shape(carbon, "CARBON")
    assert_true(carbon.get("isTopic") is True, "carbon topic should be marked as topic")
    assert_true("topicData" in carbon and "cumulative" in carbon["topicData"], "carbon topic should include tab data")

    monthly = get_json("/api/dashboard/topics/monthly-report")
    assert_detail_shape(monthly, "MONTHLY")
    assert_true(monthly.get("isTopic") is True, "monthly topic should be marked as topic")
    assert_true("topicData" in monthly and "progress" in monthly["topicData"], "monthly topic should include tab data")

    panels = get_json("/api/dashboard/panels")
    assert_true(len(panels.get("compliance", {}).get("metrics", [])) >= 4, "compliance panel metrics should exist")
    assert_true(len(panels.get("compliance", {}).get("effectiveness", [])) >= 4, "compliance effectiveness should exist")
    assert_true(len(panels.get("carbon", {}).get("metrics", [])) >= 3, "carbon panel metrics should exist")
    assert_true(len(panels.get("carbon", {}).get("sources", [])) >= 3, "carbon sources should exist")
    assert_true(panels.get("monthly", {}).get("progress", 0) >= 1, "monthly panel should expose progress")
    assert_true(len(panels.get("timeline", [])) >= 1, "construction timeline should exist")
    assert_true(len(panels.get("gis", {}).get("routePoints", [])) >= 1, "GIS route points should exist")

    print("✅ 领导层首页接入验收通过：12项KPI、11个通用弹窗、S01专属弹窗、合规/碳/月报专题与右侧面板接口均可用。")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"❌ 领导层首页接入验收失败：{exc}", file=sys.stderr)
        raise SystemExit(1)
