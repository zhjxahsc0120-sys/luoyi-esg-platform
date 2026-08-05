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


def assert_keys(payload: dict, keys: list[str], message: str) -> None:
    missing = [key for key in keys if key not in payload]
    assert_true(not missing, f"{message} missing keys: {', '.join(missing)}")


def main() -> int:
    health = get_json("/health")
    assert_true(health.get("ok") is True, "backend health should be ok")

    kpis = get_json("/api/dashboard/kpis")
    groups = kpis.get("groups", [])
    assert_true(len(groups) == 3, "dashboard should return E/S/G groups")
    assert_true(sum(len(group.get("items", [])) for group in groups) == 12, "dashboard should return 12 KPI items")

    s01 = get_json("/api/dashboard/kpi/S01")
    assert_keys(
        s01,
        ["projectStartDate", "currentDate", "continuousDays", "currentStage", "constructionStages"],
        "S01 detail",
    )
    assert_true(s01.get("continuousDays") == 368, "S01 continuous days should be 368")

    summary = get_json("/api/workspace/summary")
    assert_keys(
        summary,
        ["currentTodo", "pendingUpload", "pendingCorrection", "pendingSubmit", "underReview", "completed"],
        "workspace summary",
    )

    tasks = get_json("/api/workspace/tasks")
    task_items = tasks.get("items", [])
    assert_true(tasks.get("total", 0) >= 12, "workspace tasks should keep baseline data")
    assert_true(len(task_items) > 0, "workspace tasks should return items")
    first_task = task_items[0]
    assert_keys(first_task, ["id", "name", "module", "status", "nextStep"], "task item")

    task_detail = get_json(f"/api/workspace/tasks/{first_task['id']}/detail")
    assert_keys(task_detail, ["task", "documents", "validation", "reviewRecords"], "task detail")
    assert_true(task_detail["task"]["id"] == first_task["id"], "task detail id should match list item")

    documents_summary = get_json("/api/workspace/documents/summary")
    assert_true(documents_summary.get("documentTotal", 0) >= 368, "document summary should keep baseline total")

    documents = get_json("/api/workspace/documents")
    document_items = documents.get("items", [])
    assert_true(len(document_items) >= 10, "documents should return sample rows")
    first_document_id = document_items[0]["id"]
    document_detail = get_json(f"/api/workspace/documents/{first_document_id}")
    assert_keys(document_detail, ["id", "documentName", "documentType", "file", "tags"], "document detail")
    document_versions = get_json(f"/api/workspace/documents/{first_document_id}/versions")
    assert_true(len(document_versions.get("items", [])) >= 1, "document versions should return at least one item")
    get_json(f"/api/workspace/documents/{first_document_id}/relations")

    reviews = get_json("/api/workspace/reviews")
    review_items = reviews.get("items", [])
    assert_true(len(review_items) >= 7, "reviews should keep baseline data")
    first_review = review_items[0]
    assert_keys(first_review, ["id", "taskId", "taskName", "status", "nextStep"], "review item")

    review_detail = get_json(f"/api/workspace/reviews/{first_review['id']}")
    assert_true(review_detail.get("id") == first_review["id"], "review detail id should match list item")
    review_timeline = get_json(f"/api/workspace/reviews/{first_review['id']}/timeline")
    assert_true("items" in review_timeline, "review timeline should expose items")
    review_requirements = get_json(f"/api/workspace/reviews/{first_review['id']}/requirements")
    for item in review_requirements.get("items", []):
        assert_true("requirementText" in item, "review requirement should expose requirementText for P04")
        assert_true("status" in item, "review requirement should expose status for P04 label")

    parse_queue = get_json("/api/workspace/ai/parse-queue")
    assert_true(len(parse_queue.get("items", [])) >= 3, "parse queue should keep baseline data")

    print("✅ 工作台最终验收只读校核通过：P01-P05、S01、领导 S01、资料中心、审核结果与解析队列接口均可支撑当前前端。")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"❌ 工作台最终验收只读校核失败：{exc}", file=sys.stderr)
        raise SystemExit(1)
