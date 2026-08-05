from __future__ import annotations

import json
import sys
from urllib.request import Request, urlopen

from mysql_api import execute


BASE_URL = "http://127.0.0.1:8765"


def post(path: str, payload: dict) -> dict:
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


def cleanup_confirmed_document(confirmed: dict) -> None:
    document_id = confirmed.get("documentId")
    ingestion_job_id = confirmed.get("ingestionJobId")
    for record in confirmed.get("businessRecords") or []:
        if record.get("targetTable") == "water_protection_issue":
            execute("DELETE FROM water_protection_issue WHERE id = %s", (record.get("targetRecordId"),))
    if ingestion_job_id:
        execute("DELETE FROM source_record_trace WHERE ingestion_job_id = %s", (ingestion_job_id,))
        execute("DELETE FROM data_quality_check_result WHERE ingestion_job_id = %s", (ingestion_job_id,))
        execute("DELETE FROM data_ingestion_job WHERE id = %s AND job_type = 'FILE_PARSE_CONFIRM'", (ingestion_job_id,))
    if document_id:
        execute("DELETE FROM document_task_relation WHERE document_id = %s", (document_id,))
        execute("DELETE FROM document_version WHERE document_id = %s", (document_id,))
        execute("DELETE FROM document_record WHERE id = %s", (document_id,))


def main() -> int:
    uploaded = post(
        "/api/workspace/files/upload",
        {
            "originalName": "2026年7月水保监测月报_智能入库测试.pdf",
            "fileSize": 2048000,
            "mimeType": "application/pdf",
            "uploaderId": 10001,
            "uploaderName": "项目管理员",
        },
    )
    assert_true(uploaded.get("fileId") is not None, "上传接口未返回 fileId")

    parse_job = post(f"/api/workspace/files/{uploaded['fileId']}/parse", {})
    job_id = parse_job["jobId"]
    assert_true(parse_job.get("jobStatus") == "WAIT_CONFIRM", "解析任务状态不正确")

    job_detail = get(f"/api/workspace/parse-jobs/{job_id}")
    assert_true(job_detail.get("jobId") == job_id, "解析任务详情不正确")

    fields = get(f"/api/workspace/parse-jobs/{job_id}/fields")
    assert_true(len(fields.get("items", [])) >= 5, "抽取字段数量不足")

    candidates = get(f"/api/workspace/parse-jobs/{job_id}/match-candidates")
    assert_true(len(candidates.get("items", [])) >= 1, "候选任务数量不足")

    accepted_id = candidates["items"][0]["candidateId"]
    confirmed = post(
        f"/api/workspace/parse-jobs/{job_id}/confirm",
        {
            "confirmedFields": [
                {"fieldKey": "document_type", "confirmedValue": "水保监测月报"},
                {"fieldKey": "period", "confirmedValue": "2026-07"},
            ],
            "acceptedCandidateIds": [accepted_id],
            "operatorId": 10001,
            "operatorName": "项目管理员",
            "comment": "智能入库接口自动化测试确认",
        },
    )
    assert_true(confirmed.get("documentId") is not None, "确认入库未返回 documentId")
    assert_true(confirmed.get("linkedTaskCount") == 1, "确认入库未关联任务")
    assert_true(confirmed.get("ingestionJobId") is not None, "确认入库未返回 ingestionJobId")
    assert_true(confirmed.get("targetTable") == "water_protection_issue", "确认入库业务表同步不正确")
    cleanup_confirmed_document(confirmed)

    print("✅ 智能入库 API 端到端测试通过：上传→解析→字段→候选→确认入库。")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"❌ 智能入库 API 端到端测试失败：{exc}", file=sys.stderr)
        raise SystemExit(1)
