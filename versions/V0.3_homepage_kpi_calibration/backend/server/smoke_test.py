from __future__ import annotations

import json
import sys
from urllib.parse import quote
from urllib.error import URLError
from urllib.request import Request, urlopen


BASE_URL = "http://127.0.0.1:8765"


def get_json(path: str) -> dict:
    safe_path = quote(path, safe="/:?=&")
    try:
        with urlopen(f"{BASE_URL}{safe_path}", timeout=5) as response:
            return json.loads(response.read().decode("utf-8"))
    except URLError as exc:
        raise AssertionError(f"接口不可访问：{path}；请先启动 server/start_backend.ps1。原始错误：{exc}") from exc


def post_json(path: str, payload: dict) -> dict:
    data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    request = Request(
        f"{BASE_URL}{path}",
        data=data,
        method="POST",
        headers={"Content-Type": "application/json"},
    )
    try:
        with urlopen(request, timeout=5) as response:
            return json.loads(response.read().decode("utf-8"))
    except URLError as exc:
        raise AssertionError(f"POST interface unavailable: {path}; {exc}") from exc


def assert_equal(actual: object, expected: object, message: str) -> None:
    if actual != expected:
        raise AssertionError(f"{message}：期望 {expected!r}，实际 {actual!r}")


def assert_at_least(actual: int, expected_min: int, message: str) -> None:
    if actual < expected_min:
        raise AssertionError(f"{message}：期望至少 {expected_min!r}，实际 {actual!r}")


def main() -> int:
    health = get_json("/health")
    mysql_ok = health.get("mysql", {}).get("ok") is True
    assert_equal(health.get("ok"), True, "健康检查")

    kpis = get_json("/api/dashboard/kpis")
    actual_kpis = {
        item["key"]: item["value"]
        for group in kpis["groups"]
        for item in group["items"]
    }
    expected_kpis = {
        "E01": 2,
        "E02": 5,
        "E03": 7,
        "E04": 12856,
        "S01": 368,
        "S02": 6,
        "S03": 4,
        "S04": 3,
        "G01": 5,
        "G02": 5,
        "G03": 6,
        "G04": 4,
    }
    assert_equal(actual_kpis, expected_kpis, "首页 12 项 KPI")

    s01 = get_json("/api/dashboard/kpi/S01")
    assert_equal(s01.get("continuousDays"), 368, "S01 连续安全生产天数")
    assert_equal(s01.get("projectStartDate"), "2025-07-10", "S01 开工日期")
    assert_equal(s01.get("currentDate"), "2026-07-13", "S01 当前日期")
    assert_equal(s01.get("currentStage"), "主体工程施工", "S01 当前工期阶段")
    assert_equal(s01.get("currentStageDetail"), "路基｜桥梁｜隧道并行施工", "S01 阶段详情")
    assert_equal(len(s01.get("constructionStages", [])), 4, "S01 工期节点数量")

    summary = get_json("/api/workspace/summary")
    expected_summary = {
        "currentTodo": 27,
        "pendingUpload": 12,
        "pendingCorrection": 3,
        "pendingSubmit": 5,
        "underReview": 3,
        "dueSoon": 4,
        "completed": 36,
    }
    for key, expected_min in expected_summary.items():
        assert_at_least(summary.get(key, 0), expected_min, f"工作台摘要 {key}")

    tasks = get_json("/api/workspace/tasks")
    assert_at_least(tasks.get("total", 0), 12, "上传任务总数")
    assert_at_least(len(tasks.get("items", [])), 12, "上传任务返回条数")

    filtered_tasks = get_json("/api/workspace/tasks?module=S&cycleType=月度&assignee=工程管理部")
    assert_at_least(filtered_tasks.get("total", 0), 1, "task filter result count")

    task_detail = get_json("/api/workspace/tasks/t1/detail")
    assert_equal(len(task_detail.get("tabs", [])), 4, "任务弹窗标签数量")
    assert_equal(len(task_detail.get("documents", [])), 7, "任务弹窗资料要求数量")
    assert_at_least(task_detail.get("validation", {}).get("completed"), 5, "任务弹窗已满足数量")
    assert_equal(task_detail.get("validation", {}).get("missing"), 1, "任务弹窗缺失数量")
    assert_equal(task_detail.get("validation", {}).get("abnormal") in (0, 1), True, "任务弹窗格式异常数量")
    assert_equal(len(task_detail.get("candidateDocuments", [])), 5, "任务弹窗候选资料数量")
    assert_at_least(len(task_detail.get("reviewTimeline", [])), 2, "task review timeline count")

    assert_at_least(len(task_detail.get("linkedDocuments", [])), 1, "task linked document count")
    assert_at_least(len(task_detail.get("validationIssues", [])), 1, "task validation issue count")
    if mysql_ok:
        assert_at_least(len(task_detail.get("reviewRecords", [])), 1, "task review record count")
        draft_result = post_json("/api/workspace/tasks/t1/save", {"comment": "API smoke test draft"})
        assert_equal(draft_result.get("ok"), True, "task draft save")
        submit_result = post_json("/api/workspace/tasks/t1/submit", {"comment": "API smoke test submit"})
        assert_equal(submit_result.get("ok"), False, "task submit blocked by validation")
    else:
        assert_equal("reviewRecords" in task_detail, True, "task review record field")

    documents_summary = get_json("/api/workspace/documents/summary")
    assert_at_least(documents_summary.get("documentTotal"), 368, "资料中心资料总数")
    assert_at_least(documents_summary.get("monthNew"), 24, "资料中心本月新增")

    documents = get_json("/api/workspace/documents")
    assert_at_least(documents.get("total"), 368, "资料中心分页总数")
    assert_at_least(len(documents.get("items", [])), 10, "资料中心样例条数")
    modules = sorted({item.get("module") for item in documents.get("items", [])})
    assert_equal(modules, ["E", "G", "S"], "资料中心 E/S/G 模块覆盖")
    first_document_id = documents["items"][0]["id"]
    document_detail = get_json(f"/api/workspace/documents/{first_document_id}")
    assert_equal(document_detail.get("id"), str(first_document_id), "资料详情 ID")
    document_versions = get_json(f"/api/workspace/documents/{first_document_id}/versions")
    assert_at_least(len(document_versions.get("items", [])), 1, "资料版本数量")
    document_relations = get_json(f"/api/workspace/documents/{first_document_id}/relations")
    assert_at_least(len(document_relations.get("items", [])), 0, "资料关联数量")

    reviews = get_json("/api/workspace/reviews")
    assert_equal(len(reviews.get("statusCards", [])), 4, "审核结果状态卡数量")
    assert_at_least(len(reviews.get("items", [])), 7, "审核记录条数")

    first_review_id = reviews["items"][0]["id"]
    review_detail = get_json(f"/api/workspace/reviews/{first_review_id}")
    assert_equal(review_detail.get("id"), first_review_id, "review detail id")
    review_timeline = get_json(f"/api/workspace/reviews/{first_review_id}/timeline")
    if mysql_ok:
        assert_at_least(len(review_timeline.get("items", [])), 1, "review timeline count")
    else:
        assert_equal("items" in review_timeline, True, "review timeline field")
    review_requirements = get_json(f"/api/workspace/reviews/{first_review_id}/requirements")
    if review_detail.get("requirementCount", 0) > 0:
        assert_at_least(len(review_requirements.get("items", [])), 1, "review requirement count")

    parse_queue = get_json("/api/workspace/ai/parse-queue")
    assert_at_least(len(parse_queue.get("items", [])), 3, "AI 解析队列条数")

    print("✅ 后端 API 冒烟测试通过：当前接口与前端联调基线一致。")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except AssertionError as exc:
        print(f"❌ 后端 API 冒烟测试失败：{exc}", file=sys.stderr)
        raise SystemExit(1)
