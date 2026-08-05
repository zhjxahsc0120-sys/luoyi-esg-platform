from __future__ import annotations

import json
import sys
from urllib.parse import urlencode
from urllib.request import urlopen
from urllib.error import URLError


BASE_URL = "http://127.0.0.1:8765"


def get_json(path: str, params: dict | None = None) -> dict:
    query = f"?{urlencode(params or {})}" if params else ""
    try:
        with urlopen(f"{BASE_URL}{path}{query}", timeout=5) as response:
            return json.loads(response.read().decode("utf-8"))
    except URLError as exc:
        raise AssertionError(f"接口不可访问：{path}{query}；请先启动 server/start_backend.ps1。原始错误：{exc}") from exc


def assert_equal(actual: object, expected: object, message: str) -> None:
    if actual != expected:
        raise AssertionError(f"{message}：期望 {expected!r}，实际 {actual!r}")


def assert_at_least(actual: int, expected_min: int, message: str) -> None:
    if actual < expected_min:
        raise AssertionError(f"{message}：期望至少 {expected_min!r}，实际 {actual!r}")


def main() -> int:
    layers_payload = get_json("/api/esg/gis/layers", {"projectId": "LUOYI-ESG"})
    assert_equal(layers_payload.get("code"), 0, "GIS 图层接口 code")
    layers = layers_payload.get("data") or []
    assert_at_least(len(layers), 10, "GIS 图层数量")

    layer_ids = {item["id"] for item in layers}
    for layer_id in {"section-1", "section-2", "section-3", "water-1", "slope-2"}:
        if layer_id not in layer_ids:
            raise AssertionError(f"缺少 GIS 图层：{layer_id}")

    first_layer = next(item for item in layers if item["id"] == "section-1")
    assert_equal(first_layer["geometryType"], "line", "section-1 图层类型")
    assert_equal(first_layer["source"]["type"], "api", "section-1 数据源类型")

    all_features_payload = get_json("/api/esg/gis/features", {"projectId": "LUOYI-ESG"})
    assert_equal(all_features_payload.get("code"), 0, "GIS 全量要素接口 code")
    all_features = all_features_payload.get("data") or []
    assert_at_least(len(all_features), 10, "GIS 全量要素数量")

    section_features_payload = get_json(
        "/api/esg/gis/features",
        {"projectId": "LUOYI-ESG", "layerId": "section-1"},
    )
    section_features = section_features_payload.get("data") or []
    assert_equal(len(section_features), 1, "section-1 要素数量")
    assert_equal(section_features[0]["objectType"], "road-section", "section-1 要素类型")
    assert_equal(section_features[0]["properties"].get("sectionId"), "1标段", "section-1 sectionId")

    filtered_features_payload = get_json(
        "/api/esg/gis/features",
        {"projectId": "LUOYI-ESG", "sectionId": "2标段"},
    )
    filtered_features = filtered_features_payload.get("data") or []
    assert_at_least(len(filtered_features), 3, "2标段过滤后的要素数量")
    for feature in filtered_features:
        assert_equal(feature["properties"].get("sectionId"), "2标段", "2标段过滤结果")

    slope_payload = get_json(
        "/api/esg/gis/features",
        {"projectId": "LUOYI-ESG", "layerId": "slope-2"},
    )
    slope_features = slope_payload.get("data") or []
    assert_equal(len(slope_features), 1, "slope-2 要素数量")
    assert_equal(slope_features[0]["status"], "attention", "slope-2 状态")

    print("✅ GIS API 测试通过：图层、要素、图层过滤、标段过滤与状态字段均正常。")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except AssertionError as exc:
        print(f"❌ GIS API 测试失败：{exc}", file=sys.stderr)
        raise SystemExit(1)
