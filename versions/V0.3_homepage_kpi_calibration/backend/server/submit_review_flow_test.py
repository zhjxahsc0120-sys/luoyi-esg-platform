from __future__ import annotations

import json
import sys
import uuid
from urllib.request import Request, urlopen

sys.path.insert(0, "server")
from mysql_api import execute  # noqa: E402


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


def seed_ready_task() -> str:
    suffix = uuid.uuid4().hex[:10]
    task_id = f"submit-{suffix}"
    execute(
        """
        INSERT INTO upload_task
        (id, name, module_code, module_name, cycle, cycle_type, deadline,
         progress_current, progress_total, status, next_step, assignee_id, assignee_name, assignee_dept, priority_code)
        VALUES (%s, %s, 'E', '环境环保', '2026-07（月度）', '月度', '2026-08-20 18:00:00',
                2, 2, '待提交', '提交', 10001, '项目管理员', '安全环保部', 'NORMAL')
        """,
        (task_id, f"提交审核闭环测试任务-{suffix}"),
    )
    execute(
        """
        INSERT INTO upload_task_requirement
        (id, task_id, name, required, format_rule, status, template_available, sequence_no)
        VALUES
        (%s, %s, '水保监测月报', 1, 'PDF，≤50MB', '已关联', 1, 1),
        (%s, %s, '审核确认单', 1, 'PDF，≤10MB', '已关联', 1, 2)
        """,
        (f"{task_id}-r1", task_id, f"{task_id}-r2", task_id),
    )
    return task_id


def main() -> int:
    task_id = seed_ready_task()
    submit = post_json(
        f"/api/workspace/tasks/{task_id}/submit",
        {
            "comment": "提交审核闭环自动化测试",
            "operatorId": 10001,
            "operatorName": "项目管理员",
        },
    )
    assert_true(submit.get("ok") is True, "submit should succeed")
    review_id = submit.get("reviewId")
    assert_true(review_id, "submit response missing reviewId")
    assert_true(submit.get("status") == "审核中", "task status should be 审核中")

    task_detail = get(f"/api/workspace/tasks/{task_id}/detail")
    assert_true(task_detail["task"]["status"] == "审核中", "task detail status was not updated")
    assert_true(task_detail["task"]["nextStep"] == "查看进度", "task nextStep was not updated")

    reviews = get("/api/workspace/reviews")
    assert_true(any(item["id"] == review_id for item in reviews.get("items", [])), "P04 reviews does not include new review")
    pending_card = next((card for card in reviews.get("statusCards", []) if card["label"] == "待审核"), None)
    assert_true(pending_card and pending_card["value"] >= 3, "pending review card not updated")

    review_detail = get(f"/api/workspace/reviews/{review_id}")
    assert_true(review_detail.get("taskId") == task_id, "review detail taskId mismatch")
    assert_true(review_detail.get("status") == "待审核", "review status should be 待审核")

    timeline = get(f"/api/workspace/reviews/{review_id}/timeline")
    actions = [item["action"] for item in timeline.get("items", [])]
    assert_true(any("提交审核" in action for action in actions), "review timeline missing submit action")
    assert_true(any("完整性校验" in action for action in actions), "review timeline missing validation action")

    duplicate_submit = post_json(f"/api/workspace/tasks/{task_id}/submit", {"comment": "重复提交测试"})
    assert_true(duplicate_submit.get("ok") is True, "duplicate submit should return ok")
    assert_true(duplicate_submit.get("reviewId") == review_id, "duplicate submit should reuse existing review")

    print("✅ 提交审核闭环测试通过：任务进入审核中，P04 可见审核记录与审核轨迹，重复提交被拦截复用。")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"❌ 提交审核闭环测试失败：{exc}", file=sys.stderr)
        raise SystemExit(1)
