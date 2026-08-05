from __future__ import annotations

from collections import Counter
from datetime import date, datetime
from decimal import Decimal, ROUND_HALF_UP
from typing import Any

from mysql_db import mysql_connect


STATUS_ORDER = ("待提交", "待确认", "待补正", "校验通过", "不适用")
TASK_TYPE_ORDER = ("MONTHLY_FIXED", "CONDITIONAL", "PERIODIC_REFERENCE")
TASK_TYPE_LABELS = {
    "MONTHLY_FIXED": "固定月度",
    "CONDITIONAL": "条件触发",
    "PERIODIC_REFERENCE": "周期引用",
}
LEGACY_STATUS_MAP = {
    "待补齐": "待补正",
    "待补件": "待补正",
    "待审核": "待确认",
    "已完成": "校验通过",
    "编制中": "待提交",
    "不适用（已确认）": "不适用",
}


def _date(value: Any) -> str | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.strftime("%Y-%m-%d %H:%M:%S")
    if isinstance(value, date):
        return value.isoformat()
    return str(value)


def _normalize_status(value: str | None) -> str:
    status = LEGACY_STATUS_MAP.get(value or "", value or "")
    if status not in STATUS_ORDER:
        raise RuntimeError(f"月报任务存在未映射状态：{value}")
    return status


def _next_action(status: str, validation_action: str | None) -> str:
    if validation_action:
        return validation_action
    return {
        "待提交": "SUBMIT_MATERIAL",
        "待确认": "CONFIRM_RESPONSIBILITY",
        "待补正": "CORRECT_MATERIAL",
        "校验通过": "VIEW_RESULT",
        "不适用": "VIEW_RESULT",
    }[status]


def get_monthly_report_overview(report_period: str | None = None) -> dict | None:
    with mysql_connect() as conn:
        with conn.cursor() as cur:
            if report_period:
                cur.execute(
                    "SELECT * FROM monthly_report_cycle WHERE report_period=%s ORDER BY id DESC LIMIT 1",
                    (report_period,),
                )
            else:
                cur.execute("SELECT * FROM monthly_report_cycle ORDER BY report_period DESC, id DESC LIMIT 1")
            cycle = cur.fetchone()
            if cycle is None:
                return None
            cycle_id = cycle["id"]

            cur.execute(
                """
                SELECT t.*,
                       v.id AS validation_id, v.validation_result, v.issue_description, v.correction_requirement,
                       v.next_action_type, v.validated_at,
                       COUNT(DISTINCT ml.id) AS required_material_count,
                       COUNT(DISTINCT CASE WHEN ml.relation_status='LINKED' AND dr.id IS NOT NULL THEN ml.document_id END) AS linked_material_count
                FROM monthly_report_task_instance t
                LEFT JOIN monthly_report_task_validation v ON v.task_instance_id=t.id
                LEFT JOIN monthly_report_task_material_link ml ON ml.task_instance_id=t.id
                LEFT JOIN document_record dr ON dr.id=ml.document_id
                WHERE t.report_cycle_id=%s
                  AND (t.include_in_denominator=1 OR t.monthly_status IN ('不适用','不适用（已确认）'))
                GROUP BY t.id, v.id
                ORDER BY FIELD(t.group_code,'E','S','G'), t.task_code, t.id
                """,
                (cycle_id,),
            )
            rows = list(cur.fetchall())

            cur.execute(
                """
                SELECT ml.task_instance_id, ml.document_id, ml.relation_status,
                       ml.required_material_code, ml.required_material_name,
                       ml.data_nature, d.document_code, d.document_name,
                       d.document_type, d.period_value, d.validity_status,
                       d.document_status, d.confirm_status
                FROM monthly_report_task_material_link ml
                JOIN monthly_report_task_instance t ON t.id=ml.task_instance_id
                JOIN document_record d ON d.id=ml.document_id
                WHERE t.report_cycle_id=%s AND ml.relation_status='LINKED'
                ORDER BY ml.task_instance_id, ml.id, d.id
                """,
                (cycle_id,),
            )
            linked_material_rows = list(cur.fetchall())

            cur.execute(
                """
                SELECT COUNT(*) AS output_table_count
                FROM information_schema.TABLES
                WHERE TABLE_SCHEMA=DATABASE() AND TABLE_NAME='monthly_report_output'
                """
            )
            output_table_exists = int(cur.fetchone()["output_table_count"] or 0) > 0
            output_count = 0
            if output_table_exists:
                cur.execute("SELECT COUNT(*) n FROM monthly_report_output WHERE report_cycle_id=%s", (cycle_id,))
                output_count = int(cur.fetchone()["n"] or 0)

    linked_materials_by_task: dict[int, list[dict]] = {}
    for material in linked_material_rows:
        linked_materials_by_task.setdefault(int(material["task_instance_id"]), []).append(
            {
                "id": str(material["document_id"]),
                "documentCode": material["document_code"],
                "documentName": material["document_name"],
                "documentType": material["document_type"],
                "period": material["period_value"],
                "relationStatus": material["relation_status"],
                "validityStatus": material["validity_status"],
                "documentStatus": material["document_status"],
                "confirmStatus": material["confirm_status"],
                "requiredMaterialCode": material["required_material_code"],
                "requiredMaterialName": material["required_material_name"],
                "dataNature": material["data_nature"],
            }
        )

    task_instances = []
    for row in rows:
        status = _normalize_status(row.get("monthly_status"))
        linked_materials = linked_materials_by_task.get(int(row["id"]), [])
        linked_ids = [item["id"] for item in linked_materials]
        required_count = int(row.get("required_material_count") or 0)
        linked_count = len(linked_materials)
        if status == "校验通过" and (
            required_count < 1
            or linked_count < required_count
            or row.get("validation_result") != "校验通过"
            or row.get("validated_at") is None
        ):
            raise RuntimeError(f"校验通过任务的资料或校验链不完整：{row['task_code']}")
        if required_count == 0 and status == "不适用":
            chain_status = "EXEMPT"
        elif linked_count >= required_count and required_count > 0:
            chain_status = "LINKED"
        elif linked_count > 0:
            chain_status = "PARTIAL"
        else:
            chain_status = "UNLINKED"
        task_instances.append(
            {
                "id": str(row["id"]),
                "taskCode": row["task_code"],
                "taskName": row["task_name"],
                # 历史种子把两项跨域月报标为 X；新版契约只暴露 E/S/G，
                # 跨域治理资料稳定归入 G，避免前端自行猜测或丢项。
                "groupCode": "G" if row["group_code"] == "X" else row["group_code"],
                "taskType": row["task_mechanism"],
                "taskTypeLabel": TASK_TYPE_LABELS[row["task_mechanism"]],
                "responsibleDepartment": row.get("responsible_department") or row.get("responsible_unit"),
                "responsibleRole": row.get("responsible_role"),
                "responsibleUserId": row.get("responsible_user_id"),
                "responsibleUserName": row.get("responsible_user_name"),
                "status": status,
                "deadline": _date(row.get("deadline")),
                "requiredMaterialCount": required_count,
                "linkedMaterialCount": linked_count,
                "linkedMaterials": linked_materials,
                "validationId": str(row["validation_id"]) if row.get("validation_id") is not None else None,
                "validationResult": _normalize_status(row.get("validation_result") or status),
                "lastValidationAt": _date(row.get("validated_at")),
                "affectsReport": status in {"待提交", "待确认", "待补正"},
                "nextActionType": _next_action(status, row.get("next_action_type")),
                "materialChain": {
                    "sourceTaskId": row.get("upload_task_id"),
                    "linkedDocumentIds": linked_ids,
                    "linkedDocuments": linked_materials,
                    "requiredMaterialCount": required_count,
                    "linkedMaterialCount": linked_count,
                    "manualEvidenceOnly": True,
                    "status": chain_status,
                },
                "issueDescription": row.get("issue_description"),
                "correctionRequirement": row.get("correction_requirement"),
                "dataNature": row.get("data_nature") or "demo",
                "updatedAt": _date(row.get("updated_at")),
            }
        )

    total = len(task_instances)
    status_counter = Counter(item["status"] for item in task_instances)
    collected = status_counter["校验通过"]
    denominator = total - status_counter["不适用"]
    exact_rate = (
        Decimal(collected) * Decimal(100) / Decimal(denominator)
        if denominator else Decimal("0")
    ).quantize(Decimal("0.1"), rounding=ROUND_HALF_UP)
    readiness_rate = int(exact_rate.quantize(Decimal("1"), rounding=ROUND_HALF_UP))
    deadlines = [item["deadline"] for item in task_instances if item["status"] != "不适用" and item["deadline"]]

    task_type_counter = Counter(item["taskType"] for item in task_instances)
    group_progress = []
    for group_code in ("E", "S", "G"):
        group_tasks = [item for item in task_instances if item["groupCode"] == group_code]
        group_passed = sum(item["status"] == "校验通过" for item in group_tasks)
        group_total = len(group_tasks)
        group_progress.append(
            {
                "groupCode": group_code,
                "collectedCount": group_passed,
                "totalCount": group_total,
                "progress": round(group_passed * 100 / group_total) if group_total else 0,
            }
        )

    pending_tasks = [
        {
            "id": item["id"],
            "taskCode": item["taskCode"],
            "taskName": item["taskName"],
            "groupCode": item["groupCode"],
            "status": item["status"],
            "issueDescription": item["issueDescription"],
            "requirement": item["correctionRequirement"],
            "deadline": item["deadline"],
            "responsibleRole": item["responsibleRole"],
            "nextActionType": item["nextActionType"],
            "materialChain": item["materialChain"],
        }
        for item in task_instances
        if item["status"] in {"待提交", "待确认", "待补正"}
    ]

    process_stages = [
        {"key": "collection", "label": "资料归集", "status": "IN_PROGRESS", "detail": f"{collected}/{denominator}"},
        {"key": "validation", "label": "完整性校验", "status": "IN_PROGRESS", "detail": f"{status_counter['待补正']}项待补正"},
        {"key": "confirmation", "label": "责任确认", "status": "PENDING", "detail": f"{status_counter['待确认']}项待确认"},
        {"key": "generation", "label": "月报生成", "status": "NOT_STARTED", "detail": "待触发"},
        {"key": "finalization", "label": "审核定稿", "status": "NOT_STARTED", "detail": "未开始"},
    ]

    updated_values = [item["updatedAt"] for item in task_instances if item["updatedAt"]]
    return {
        "reportMonth": cycle["report_period"],
        "summary": {
            "collectedCount": collected,
            "totalCount": denominator,
            "pendingSubmitCount": status_counter["待提交"],
            "pendingConfirmCount": status_counter["待确认"],
            "pendingCorrectionCount": status_counter["待补正"],
            "pendingTotal": status_counter["待提交"] + status_counter["待确认"] + status_counter["待补正"],
            "notApplicableCount": status_counter["不适用"],
        },
        "readinessRate": readiness_rate,
        "exactReadinessRate": float(exact_rate),
        "deadlineRange": {"start": min(deadlines) if deadlines else None, "end": max(deadlines) if deadlines else None},
        "statusCounts": [{"status": status, "count": status_counter[status]} for status in STATUS_ORDER],
        "taskTypeCounts": [
            {"taskType": task_type, "label": TASK_TYPE_LABELS[task_type], "count": task_type_counter[task_type]}
            for task_type in TASK_TYPE_ORDER
        ],
        "groupProgress": group_progress,
        "processStages": process_stages,
        "taskInstances": task_instances,
        "pendingTasks": pending_tasks,
        "outputStatus": {
            "status": "NOT_CREATED" if output_count == 0 else "CREATED",
            "label": "未生成" if output_count == 0 else "已生成",
            "hasOutputRecord": output_count > 0,
            "outputCount": output_count,
        },
        "sourceMode": "mysql",
        "isMock": False,
        "dataNature": "demo" if all(item["dataNature"] == "demo" for item in task_instances) else "mixed",
        "updatedAt": max(updated_values) if updated_values else _date(cycle.get("update_time")),
    }
