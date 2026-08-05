from __future__ import annotations

import sys

from mysql_db import mysql_ping, mysql_connect


def assert_equal(actual: object, expected: object, message: str) -> None:
    if actual != expected:
        raise AssertionError(f"{message}：期望 {expected!r}，实际 {actual!r}")


def assert_at_least(actual: int, expected_min: int, message: str) -> None:
    if actual < expected_min:
        raise AssertionError(f"{message}：期望至少 {expected_min!r}，实际 {actual!r}")


def scalar(sql: str) -> object:
    with mysql_connect() as conn:
        with conn.cursor() as cur:
            cur.execute(sql)
            row = cur.fetchone()
    return next(iter(row.values()))


def main() -> int:
    info = mysql_ping()
    assert_equal(info["database"], "luoyi_esg", "数据库名")

    assert_equal(scalar("SELECT COUNT(*) FROM indicator_result"), 12, "首页 KPI 数量")
    assert_equal(int(scalar("SELECT value FROM indicator_result WHERE indicator_code='S01'")), 368, "S01 指标值")
    assert_at_least(int(scalar("SELECT COUNT(*) FROM upload_task")), 12, "上传任务数量")
    assert_equal(scalar("SELECT COUNT(*) FROM upload_task_requirement WHERE task_id='t1'"), 7, "t1 资料要求数量")
    assert_at_least(int(scalar("SELECT COUNT(*) FROM document_record")), 10, "资料样例数量")
    assert_at_least(int(scalar("SELECT COUNT(*) FROM review_record")), 7, "审核记录数量")
    assert_equal(scalar("SELECT COUNT(*) FROM ai_field_mapping_rule"), 27, "字段映射规则数量")
    assert_at_least(int(scalar("SELECT COUNT(*) FROM ai_parse_job")), 3, "AI 解析任务数量")

    print("✅ MySQL 冒烟测试通过：luoyi_esg 数据库与建库包 V0.1 一致。")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"❌ MySQL 冒烟测试失败：{exc}", file=sys.stderr)
        raise SystemExit(1)
