from __future__ import annotations

import json
import sys
from urllib.request import Request, urlopen

from mysql_api import execute, query_one


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


def cleanup_test_records(document_id: int | None, ingestion_job_id: int | None, target_record_id: int | None) -> None:
    if target_record_id is not None:
        execute("DELETE FROM rectification_record WHERE id = %s AND check_batch = 'P03智能入库'", (target_record_id,))
    if ingestion_job_id is not None:
        execute("DELETE FROM source_record_trace WHERE ingestion_job_id = %s", (ingestion_job_id,))
        execute("DELETE FROM data_quality_check_result WHERE ingestion_job_id = %s", (ingestion_job_id,))
        execute("DELETE FROM data_ingestion_job WHERE id = %s AND job_type = 'FILE_PARSE_CONFIRM'", (ingestion_job_id,))
    if document_id is not None:
        execute("DELETE FROM document_task_relation WHERE document_id = %s", (document_id,))
        execute("DELETE FROM document_version WHERE document_id = %s", (document_id,))
        execute("DELETE FROM document_record WHERE id = %s", (document_id,))


def main() -> int:
    uploaded = post(
        "/api/workspace/files/upload",
        {
            "originalName": "NCR整改关闭资料_2026-07_确认入库追溯测试.pdf",
            "fileSize": 307200,
            "mimeType": "application/pdf",
            "uploaderId": 10001,
            "uploaderName": "项目管理员",
        },
    )
    assert_true(uploaded.get("fileId") is not None, "上传接口未返回 fileId")

    parse_job = post(f"/api/workspace/files/{uploaded['fileId']}/parse", {})
    job_id = parse_job["jobId"]
    assert_true(parse_job.get("jobStatus") == "WAIT_CONFIRM", "解析任务状态不正确")

    candidates = get(f"/api/workspace/parse-jobs/{job_id}/match-candidates")
    accepted_ids = [candidates["items"][0]["candidateId"]] if candidates.get("items") else []

    confirmed = post(
        f"/api/workspace/parse-jobs/{job_id}/confirm",
        {
            "confirmedFields": [
                {"fieldKey": "document_type", "confirmedValue": "NCR整改关闭资料"},
                {"fieldKey": "esg_module", "confirmedValue": "G"},
                {"fieldKey": "period", "confirmedValue": "2026-07"},
                {"fieldKey": "rectification_item", "confirmedValue": "P03确认入库生成整改闭环记录"},
                {"fieldKey": "rectification_status", "confirmedValue": "待复查"},
            ],
            "acceptedCandidateIds": accepted_ids,
            "operatorId": 10001,
            "operatorName": "项目管理员",
            "comment": "确认入库后同步多源追溯与整改闭环测试",
        },
    )

    document_id = confirmed.get("documentId")
    ingestion_job_id = confirmed.get("ingestionJobId")
    target_table = confirmed.get("targetTable")
    business_records = confirmed.get("businessRecords") or []
    target_record_id = business_records[0]["targetRecordId"] if business_records else None

    assert_true(document_id is not None, "确认入库未返回 documentId")
    assert_true(ingestion_job_id is not None, "确认入库未返回 ingestionJobId")
    assert_true(target_table == "rectification_record", f"目标业务表不正确：{target_table}")
    assert_true(target_record_id is not None, "确认入库未返回业务记录 ID")

    ingestion_job = query_one("SELECT * FROM data_ingestion_job WHERE id = %s", (ingestion_job_id,))
    assert_true(ingestion_job is not None, "data_ingestion_job 未写入")
    assert_true(ingestion_job["job_status"] == "SUCCESS", "data_ingestion_job 状态不是 SUCCESS")
    assert_true(ingestion_job["target_table"] == "rectification_record", "入库任务目标表不正确")

    trace = query_one(
        """
        SELECT * FROM source_record_trace
        WHERE ingestion_job_id = %s AND document_id = %s AND target_table = 'rectification_record'
        """,
        (ingestion_job_id, document_id),
    )
    assert_true(trace is not None, "source_record_trace 未写入")
    assert_true(str(trace["target_record_id"]) == str(target_record_id), "追溯目标记录 ID 不一致")

    quality = query_one("SELECT * FROM data_quality_check_result WHERE ingestion_job_id = %s", (ingestion_job_id,))
    assert_true(quality is not None, "data_quality_check_result 未写入")
    assert_true(quality["check_status"] == "PASS", "质量校核状态不是 PASS")

    rectification = query_one("SELECT * FROM rectification_record WHERE id = %s", (target_record_id,))
    assert_true(rectification is not None, "rectification_record 未写入")
    assert_true(rectification["document_id"] == document_id, "整改记录未关联确认入库资料")
    assert_true(rectification["status"] == "待复查", "整改记录状态不正确")

    cleanup_test_records(document_id, ingestion_job_id, target_record_id)
    print("[PASS] 确认入库多源追溯链路通过：上传/解析/确认 -> 入库任务 -> 质量校核 -> 来源追溯 -> 整改闭环记录")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"[FAIL] 确认入库多源追溯链路失败：{exc}", file=sys.stderr)
        raise SystemExit(1)
