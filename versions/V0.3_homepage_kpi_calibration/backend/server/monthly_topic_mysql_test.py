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


def summary_value(items: list[dict], label: str):
    for item in items:
        if item.get("label") == label:
            return item.get("value")
    raise AssertionError(f"summary label missing: {label}")


def main() -> int:
    topic = get_json("/api/dashboard/topics/monthly-report")
    assert_true("monthly_report_cycle" in topic.get("dataSource", ""), "monthly topic should come from monthly report tables")
    assert_true(summary_value(topic.get("summary", []), "月报完成度") == 82, "monthly completion mismatch")
    assert_true(summary_value(topic.get("summary", []), "待补资料") == 6, "monthly gap count mismatch")
    assert_true(summary_value(topic.get("summary", []), "待确认") == 4, "monthly pending confirm mismatch")
    assert_true(summary_value(topic.get("summary", []), "预计完成") == "7月12日", "monthly expected date mismatch")

    topic_data = topic.get("topicData", {})
    progress = topic_data.get("progress", {})
    chapters = topic_data.get("chapters", {})
    chain = topic_data.get("statusChain", [])

    groups = {item.get("key"): item.get("value") for item in progress.get("groups", [])}
    assert_true(groups == {"E": 85, "S": 78, "G": 83}, f"monthly progress groups mismatch: {groups}")
    assert_true(len(chapters.get("list", [])) == 6, "monthly chapter row count mismatch")
    assert_true(len(topic.get("detailData", [])) == 6, "monthly gap detail row count mismatch")
    assert_true([item.get("status") for item in chain] == ["completed", "completed", "active", "pending", "pending"], "monthly status chain mismatch")
    assert_true(topic.get("completeness") == "82%", "monthly completeness text mismatch")

    print("[PASS] 月报准备与输出专题 MySQL 业务表聚合验收通过。")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"[FAIL] 月报准备与输出专题 MySQL 业务表聚合验收失败：{exc}", file=sys.stderr)
        raise SystemExit(1)
