from __future__ import annotations

import json
import sys
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from mysql_api import execute


BASE_URL = "http://127.0.0.1:8765"


def post(path: str, payload: dict) -> dict:
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    request = Request(
        f"{BASE_URL}{path}",
        data=body,
        headers={"Content-Type": "application/json; charset=utf-8"},
        method="POST",
    )
    with urlopen(request, timeout=10) as response:
        assert response.status == 201
        return json.loads(response.read().decode("utf-8"))


def get(path: str) -> dict:
    with urlopen(f"{BASE_URL}{path}", timeout=10) as response:
        return json.loads(response.read().decode("utf-8"))


def main() -> int:
    created = post(
        "/api/esg/document/analyze",
        {"fileId": 985, "fileName": "罗宜高速2026年5月工程监理月报_API测试.pdf"},
    )
    analysis_id = int(created["analysis_id"])
    try:
        assert created["document"]["type"] == "工程监理月报"
        assert created["document"]["period"] == "2026-05"
        assert created["data"]["project_info"]["route_length"] == 78.6
        assert len(created["data"]["progress"]) == 4
        assert created["excluded_from_dashboard"] is True
        assert created["ingestion_status"] == "stored"

        fetched = get(f"/api/esg/document/{analysis_id}/result")
        assert fetched["analysis_id"] == analysis_id
        assert fetched["data"]["project_info"]["project_name"] == "罗宜高速公路项目"

        try:
            get("/api/esg/document/999999999/result")
        except HTTPError as exc:
            assert exc.code == 404
        else:
            raise AssertionError("不存在的解析记录应返回 404")
    finally:
        execute("DELETE FROM ai_document_analysis WHERE id = %s", (analysis_id,))

    print("[OK] 工程资料 AI 解析 API 测试通过：创建、查询、404 与数据隔离标记均正确。")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"[FAIL] 工程资料 AI 解析 API 测试失败：{exc}", file=sys.stderr)
        raise SystemExit(1)
