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
    content = b"%PDF-1.4\nconfirm-updates-task-" + uuid.uuid4().hex.encode("ascii") + b"\n%%EOF\n"
    filename = "\u6c34\u4fdd\u76d1\u6d4b\u6708\u62a5_2026-07_\u8fdb\u5ea6\u56de\u5199\u6d4b\u8bd5.pdf"

    uploaded = post_multipart_upload(filename, content)
    parse_job = post_json(f"/api/workspace/files/{uploaded['fileId']}/parse", {})
    job_id = parse_job["jobId"]
    candidates = get(f"/api/workspace/parse-jobs/{job_id}/match-candidates")["items"]
    assert_true(candidates, "no match candidates found")
    candidate = candidates[0]
    task_id = candidate["taskId"]

    before = get(f"/api/workspace/tasks/{task_id}/detail")
    before_validation = before["validation"]

    confirmed = post_json(
        f"/api/workspace/parse-jobs/{job_id}/confirm",
        {
            "confirmedFields": [],
            "acceptedCandidateIds": [candidate["candidateId"]],
            "operatorId": 10001,
            "operatorName": "项目管理员",
            "comment": "确认入库后回写任务进度测试",
        },
    )

    assert_true(confirmed.get("linkedTaskCount") == 1, "linkedTaskCount should be 1")
    linked_tasks = confirmed.get("linkedTasks") or []
    assert_true(len(linked_tasks) == 1, "linkedTasks should include one task")
    linked = linked_tasks[0]
    assert_true(linked.get("taskId") == task_id, "linked task id mismatch")
    assert_true(linked.get("requirementId"), "linked requirementId missing")

    after = get(f"/api/workspace/tasks/{task_id}/detail")
    after_validation = after["validation"]
    assert_true(
        after_validation["completed"] >= before_validation["completed"],
        "completed count should not decrease",
    )
    assert_true(
        any(doc["id"] == linked["requirementId"] and doc["status"] == "已关联" for doc in after["documents"]),
        "matched requirement was not marked as 已关联",
    )

    documents = get("/api/workspace/documents")
    assert_true(documents.get("total", 0) >= 368, "document total should keep page baseline")
    assert_true(
        any(str(doc["id"]) == str(confirmed["documentId"]) for doc in documents.get("items", [])),
        "confirmed document is not visible in P05 document list",
    )

    print("✅ 确认入库回写任务测试通过：AI关联后资料要求状态与任务进度同步更新。")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"❌ 确认入库回写任务测试失败：{exc}", file=sys.stderr)
        raise SystemExit(1)
