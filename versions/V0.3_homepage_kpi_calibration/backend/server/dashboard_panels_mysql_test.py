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


def metric_value(items: list[dict], label: str):
    for item in items:
        if item.get("label") == label:
            return item.get("value")
    raise AssertionError(f"metric label missing: {label}")


def main() -> int:
    panels = get_json("/api/dashboard/panels")
    compliance = panels.get("compliance") or {}
    carbon = panels.get("carbon") or {}
    monthly = panels.get("monthly") or {}

    assert_true(metric_value(compliance.get("metrics", []), "合规点位") == 12, "compliance point count mismatch")
    assert_true(metric_value(compliance.get("metrics", []), "碳排点位") == 6, "carbon point count mismatch")
    assert_true(metric_value(compliance.get("metrics", []), "敏感区") == 3, "sensitive area count mismatch")
    assert_true(metric_value(compliance.get("metrics", []), "风险点") == 6, "risk point count mismatch")
    assert_true(metric_value(compliance.get("effectiveness", []), "已化解重大风险") == 12, "solved risk count mismatch")
    assert_true(metric_value(compliance.get("effectiveness", []), "保障关键施工节点") == 8, "safeguarded node count mismatch")
    assert_true(len(compliance.get("safeguards", [])) >= 3, "safeguards list too short")

    assert_true(metric_value(carbon.get("metrics", []), "施工阶段累计碳足迹") == 12856, "carbon total mismatch")
    assert_true(metric_value(carbon.get("metrics", []), "累计核算减排量") == 1445, "carbon reduction mismatch")
    assert_true(len(carbon.get("sources", [])) == 3, "carbon source count mismatch")
    assert_true(len(carbon.get("reductions", [])) >= 4, "carbon reductions count mismatch")

    assert_true(monthly.get("month") == "2026年7月", "monthly period mismatch")
    assert_true(monthly.get("progress") == 82, "monthly progress mismatch")
    assert_true(monthly.get("pendingCount") == 6, "monthly pending count mismatch")
    assert_true(monthly.get("confirmCount") == 4, "monthly confirm count mismatch")
    assert_true(len(monthly.get("materials", [])) == 6, "monthly materials count mismatch")

    print("[PASS] 首页右侧三块面板 MySQL 业务表聚合验收通过。")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"[FAIL] 首页右侧三块面板 MySQL 业务表聚合验收失败：{exc}", file=sys.stderr)
        raise SystemExit(1)
