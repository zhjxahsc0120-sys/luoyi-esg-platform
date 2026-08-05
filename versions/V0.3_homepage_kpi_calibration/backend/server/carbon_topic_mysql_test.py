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
    topic = get_json("/api/dashboard/topics/carbon")
    assert_true("carbon_emission_activity" in topic.get("dataSource", ""), "carbon topic should come from carbon_emission_activity")
    assert_true(summary_value(topic.get("summary", []), "施工阶段累计碳足迹") == 12856, "carbon topic total mismatch")
    assert_true(summary_value(topic.get("summary", []), "较基准下降") == 10.1, "carbon topic reduction rate mismatch")

    cumulative = topic.get("topicData", {}).get("cumulative", {})
    benefit = topic.get("topicData", {}).get("benefit", {})
    source = topic.get("topicData", {}).get("source", {})
    assert_true(cumulative.get("months") == ["2026-02", "2026-03", "2026-04", "2026-05", "2026-06", "2026-07"], "cumulative months mismatch")
    assert_true(cumulative.get("monthlyData")[-1] == 1256, "cumulative monthly data mismatch")
    assert_true(cumulative.get("cumulativeData")[-1] == 12856, "cumulative total data mismatch")
    assert_true(benefit.get("totalReduction") == 1445, "benefit total reduction mismatch")
    assert_true(benefit.get("reductionRate") == 10.1, "benefit reduction rate mismatch")
    assert_true(len(source.get("detailData", [])) == 4, "source detail row count mismatch")

    print("[PASS] 碳足迹与低碳增益专题 MySQL 业务表聚合验收通过。")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"[FAIL] 碳足迹与低碳增益专题 MySQL 业务表聚合验收失败：{exc}", file=sys.stderr)
        raise SystemExit(1)
