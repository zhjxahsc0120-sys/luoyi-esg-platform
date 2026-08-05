from __future__ import annotations

import json
import sys
import uuid
from urllib.request import Request, urlopen

sys.path.insert(0, "server")
from mysql_db import mysql_connect  # noqa: E402
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


def mysql_available() -> bool:
    try:
        with mysql_connect() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT 1")
        return True
    except Exception:
        return False


def seed_ready_task(prefix: str) -> str:
    suffix = uuid.uuid4().hex[:10]
    task_id = f"{prefix}-{suffix}"
    execute(
        """
        INSERT INTO upload_task
        (id, name, module_code, module_name, cycle, cycle_type, deadline,
         progress_current, progress_total, status, next_step, assignee_id, assignee_name, assignee_dept, priority_code)
        VALUES (%s, %s, 'S', '社会责任', '2026-07（月度）', '月度', '2026-08-18 18:00:00',
                2, 2, '待提交', '提交', 10001, '项目管理员', '工程管理部', 'NORMAL')
        """,
        (task_id, f"审核动作闭环测试任务-{suffix}"),
    )
    execute(
        """
        INSERT INTO upload_task_requirement
        (id, task_id, name, required, format_rule, status, template_available, sequence_no)
        VALUES
        (%s, %s, '施工人员工资支付资料', 1, 'PDF，≤50MB', '已关联', 1, 1),
        (%s, %s, '审核确认单', 1, 'PDF，≤10MB', '已关联', 1, 2)
        """,
        (f"{task_id}-r1", task_id, f"{task_id}-r2", task_id),
    )
    return task_id


def submit_task(task_id: str) -> str:
    result = post_json(
        f"/api/workspace/tasks/{task_id}/submit",
        {
            "comment": "审核动作闭环自动化测试提交",
            "operatorName": "项目管理员",
        },
    )
    assert_true(result.get("ok") is True, "submit should succeed")
    review_id = result.get("reviewId")
    assert_true(bool(review_id), "submit response missing reviewId")
    return review_id


def main() -> int:
    if not mysql_available():
        print("⚠️ 审核处理闭环测试已跳过：MySQL 未启动；当前仅验证 SQLite/JSON fallback 只读联调基线。")
        return 0

    approve_task_id = seed_ready_task("approve")
    approve_review_id = submit_task(approve_task_id)
    approve_result = post_json(
        f"/api/workspace/reviews/{approve_review_id}/approve",
        {
            "reviewer": "项目审核人",
            "comment": "资料完整，审核通过",
        },
    )
    assert_true(approve_result.get("ok") is True, "approve should succeed")
    assert_true(approve_result.get("status") == "已通过", "review should be 已通过")
    assert_true(approve_result.get("taskStatus") == "已完成", "task should be 已完成")
    approve_task = get(f"/api/workspace/tasks/{approve_task_id}/detail")
    assert_true(approve_task["task"]["status"] == "已完成", "approved task detail not updated")
    approve_timeline = get(f"/api/workspace/reviews/{approve_review_id}/timeline")
    assert_true(
        any("审核通过" in item["action"] for item in approve_timeline.get("items", [])),
        "review timeline missing approve action",
    )

    return_task_id = seed_ready_task("return")
    return_review_id = submit_task(return_task_id)
    requirements = ["请补充工资支付凭证签章页。", "请重新上传附件日期清晰的扫描件。"]
    return_result = post_json(
        f"/api/workspace/reviews/{return_review_id}/return",
        {
            "reviewer": "项目审核人",
            "comment": "附件签章和日期信息需补正",
            "requirements": requirements,
        },
    )
    assert_true(return_result.get("ok") is True, "return should succeed")
    assert_true(return_result.get("status") == "已退回", "review should be 已退回")
    assert_true(return_result.get("taskStatus") == "待补正", "task should be 待补正")
    return_task = get(f"/api/workspace/tasks/{return_task_id}/detail")
    assert_true(return_task["task"]["status"] == "待补正", "returned task detail not updated")
    return_requirements = get(f"/api/workspace/reviews/{return_review_id}/requirements")
    requirement_texts = [item["requirement"] for item in return_requirements.get("items", [])]
    assert_true(requirement_texts == requirements, "return requirements mismatch")
    assert_true(
        all(item["status"] == "待补正" for item in return_requirements.get("items", [])),
        "returned requirements should be pending correction",
    )
    return_timeline = get(f"/api/workspace/reviews/{return_review_id}/timeline")
    assert_true(
        any("审核退回" in item["action"] for item in return_timeline.get("items", [])),
        "review timeline missing return action",
    )

    duplicate_return = post_json(f"/api/workspace/reviews/{return_review_id}/return", {"comment": "重复退回"})
    assert_true(duplicate_return.get("ok") is False, "duplicate return should be blocked")

    resubmit_result = post_json(
        f"/api/workspace/tasks/{return_task_id}/submit",
        {
            "comment": "补正完成，重新提交审核",
            "operatorName": "项目管理员",
        },
    )
    assert_true(resubmit_result.get("ok") is True, "resubmit after correction should succeed")
    resubmit_review_id = resubmit_result.get("reviewId")
    assert_true(resubmit_review_id != return_review_id, "resubmit should create a new review")
    corrected_requirements = get(f"/api/workspace/reviews/{return_review_id}/requirements")
    assert_true(
        all(item["status"] == "已补正" for item in corrected_requirements.get("items", [])),
        "old return requirements should be marked corrected",
    )
    corrected_timeline = get(f"/api/workspace/reviews/{return_review_id}/timeline")
    assert_true(
        any("补正提交" in item["action"] for item in corrected_timeline.get("items", [])),
        "old review timeline missing resubmit action",
    )
    resubmit_detail = get(f"/api/workspace/reviews/{resubmit_review_id}")
    assert_true(resubmit_detail.get("status") == "待审核", "resubmit review should be pending")

    reviews = get("/api/workspace/reviews")
    assert_true(any(item["id"] == approve_review_id and item["status"] == "已通过" for item in reviews.get("items", [])), "P04 missing approved review")
    assert_true(any(item["id"] == return_review_id and item["status"] == "已退回" for item in reviews.get("items", [])), "P04 missing returned review")
    assert_true(any(item["id"] == resubmit_review_id and item["status"] == "待审核" for item in reviews.get("items", [])), "P04 missing resubmit review")

    print("✅ 审核处理闭环测试通过：审核通过/退回/补正再提交、任务状态回写、补正要求与审核轨迹均正常。")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"❌ 审核处理闭环测试失败：{exc}", file=sys.stderr)
        raise SystemExit(1)
