from __future__ import annotations

import json
import sys
import uuid
from urllib.request import Request, urlopen

from multipart_upload_test import post_multipart_upload


BASE_URL = "http://127.0.0.1:8765"


def post_json(path: str, payload: dict) -> dict:
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    req = Request(
        f"{BASE_URL}{path}",
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urlopen(req, timeout=10) as response:
        return json.loads(response.read().decode("utf-8"))


def get(path: str) -> dict:
    with urlopen(f"{BASE_URL}{path}", timeout=10) as response:
        return json.loads(response.read().decode("utf-8"))


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> int:
    token = uuid.uuid4().hex.encode("ascii")
    content = b"%PDF-1.4\nrule-and-dedup-test-" + token + b"\n%%EOF\n"
    filename = "\u6c34\u4fdd\u76d1\u6d4b\u6708\u62a5_2026-07_\u89c4\u5219\u6d4b\u8bd5.pdf"

    first = post_multipart_upload(filename, content)
    assert_true(first.get("duplicateStatus") == "UNIQUE", "first upload should be UNIQUE")

    second = post_multipart_upload(filename, content)
    assert_true(second.get("duplicateStatus") == "DUPLICATE", "second upload should be DUPLICATE")
    assert_true(second.get("matchedFileId") == first.get("fileId"), "duplicate matchedFileId mismatch")

    parse_job = post_json(f"/api/workspace/files/{first['fileId']}/parse", {})
    job_id = parse_job["jobId"]
    fields = get(f"/api/workspace/parse-jobs/{job_id}/fields")["items"]
    field_map = {item["fieldKey"]: item for item in fields}

    for required_key in [
        "document_name",
        "document_type",
        "esg_module",
        "period",
        "responsible_unit",
        "valid_start_date",
        "valid_end_date",
        "monitor_date",
        "dust_exceed_count",
        "noise_exceed_count",
        "water_protection_issue_count",
    ]:
        assert_true(required_key in field_map, f"missing mapped field: {required_key}")

    assert_true(field_map["document_type"]["normalizedValue"] == "水保监测月报", "document_type inference mismatch")
    assert_true(field_map["valid_start_date"]["normalizedValue"] == "2026-07-01", "valid_start_date mismatch")
    assert_true(field_map["valid_end_date"]["normalizedValue"] == "2026-08-31", "valid_end_date mismatch")

    confirmed = post_json(
        f"/api/workspace/parse-jobs/{job_id}/confirm",
        {
            "confirmedFields": [
                {"fieldKey": "document_type", "confirmedValue": "水保监测月报"},
                {"fieldKey": "period", "confirmedValue": "2026-07"},
            ],
            "acceptedCandidateIds": [],
            "operatorId": 10001,
            "operatorName": "项目管理员",
            "comment": "规则解析与去重自动化测试",
        },
    )
    detail = get(f"/api/workspace/documents/{confirmed['documentId']}")
    assert_true(detail.get("validStartDate") == "2026-07-01", "document validStartDate mismatch")
    assert_true(detail.get("validEndDate") == "2026-08-31", "document validEndDate mismatch")

    print("✅ 解析规则与去重测试通过：规则字段生成、重复文件识别、有效期入库均正常。")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"❌ 解析规则与去重测试失败：{exc}", file=sys.stderr)
        raise SystemExit(1)
