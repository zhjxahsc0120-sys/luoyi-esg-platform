"""G01/G02 V0.4 homepage KPI live aggregation (no DDL).

G01: compliance_procedure + permit_record → completed/due (not string concat of old ratios)
G02: safety_risk_point → special_plan_approval → completed/due
"""
from __future__ import annotations

from datetime import date, datetime
from typing import Any


# Permit statuses treated as NOT yet compliant for G01 merge.
_G01_PERMIT_OPEN_STATUSES = {"临期", "逾期", "过期", "失效", "作废", "EXPIRING", "OVERDUE", "EXPIRED", "INVALID"}

# Special-plan statuses treated as approval completed.
_G02_PLAN_APPROVED_STATUSES = {
    "已审批",
    "已通过",
    "通过",
    "已完成",
    "APPROVED",
    "PASSED",
    "COMPLETE",
    "COMPLETED",
}


def _norm_status(value: Any) -> str:
    return str(value or "").strip().upper()


def _as_json(value: Any) -> Any:
    """Make MySQL date/datetime JSON-safe for detail payloads."""
    if isinstance(value, datetime):
        return value.strftime("%Y-%m-%d %H:%M:%S")
    if isinstance(value, date):
        return value.isoformat()
    return value


def aggregate_g01_compliance_and_permit() -> dict[str, Any]:
    """Merge compliance_procedure + permit_record into one X/X homepage value."""
    from mysql_api import query_all  # local import avoids circular init issues

    procedures = query_all(
        """
        SELECT id, procedure_name, procedure_type, status, deadline,
               responsible_department, progress_percent, completed_date, overdue
        FROM compliance_procedure
        ORDER BY overdue DESC, deadline, id
        """
    ) or []
    permits = query_all(
        """
        SELECT id, permit_name, permit_no, permit_type, status, expire_date,
               responsible_department
        FROM permit_record
        ORDER BY expire_date, id
        """
    ) or []

    proc_total = len(procedures)
    proc_done = sum(1 for row in procedures if str(row.get("status") or "").strip() == "已完成")
    perm_total = len(permits)
    perm_done = 0
    for row in permits:
        status = str(row.get("status") or "").strip()
        if not status:
            continue
        if status in _G01_PERMIT_OPEN_STATUSES or _norm_status(status) in _G01_PERMIT_OPEN_STATUSES:
            continue
        perm_done += 1

    due = proc_total + perm_total
    done = proc_done + perm_done
    rate = int(round(100.0 * done / due)) if due else 0
    value = f"{done}/{due}" if due else "0/0"
    objects: list[dict[str, Any]] = []
    for row in procedures:
        objects.append(
            {
                "objectType": "compliance_procedure",
                "objectId": int(row["id"]),
                "objectName": row.get("procedure_name") or f"审批事项#{row['id']}",
                "status": row.get("status"),
                "riskLevel": "HIGH" if int(row.get("overdue") or 0) == 1 else "NORMAL",
                "fields": {
                    "sourceTable": "compliance_procedure",
                    "procedureType": row.get("procedure_type"),
                    "deadline": _as_json(row.get("deadline")),
                    "department": row.get("responsible_department"),
                    "progressPercent": row.get("progress_percent"),
                    "completedDate": _as_json(row.get("completed_date")),
                    "bucket": "合规审批",
                },
            }
        )
    for row in permits:
        status = str(row.get("status") or "").strip()
        open_flag = status in _G01_PERMIT_OPEN_STATUSES or _norm_status(status) in _G01_PERMIT_OPEN_STATUSES
        objects.append(
            {
                "objectType": "permit_record",
                "objectId": int(row["id"]),
                "objectName": row.get("permit_name") or row.get("permit_no") or f"许可#{row['id']}",
                "status": status,
                "riskLevel": "HIGH" if open_flag else "NORMAL",
                "fields": {
                    "sourceTable": "permit_record",
                    "permitNo": row.get("permit_no"),
                    "permitType": row.get("permit_type"),
                    "expireDate": _as_json(row.get("expire_date")),
                    "department": row.get("responsible_department"),
                    "bucket": "许可及施工管控",
                },
            }
        )

    risk = "HIGH" if done < due else "NORMAL"
    return {
        "key": "G01",
        "value": value,
        "unit": f"{rate}%",
        "hint": f"审批 {proc_done}/{proc_total} · 许可 {perm_done}/{perm_total}",
        "riskLevel": risk,
        "name": "合规审批与许可",
        "completed": done,
        "due": due,
        "procedureCompleted": proc_done,
        "procedureDue": proc_total,
        "permitCompleted": perm_done,
        "permitDue": perm_total,
        "objects": objects,
        "summary": {
            "total": due,
            "completed": done,
            "pending": max(due - done, 0),
            "abnormal": max(due - done, 0),
            "procedureCompleted": proc_done,
            "procedureDue": proc_total,
            "permitCompleted": perm_done,
            "permitDue": perm_total,
        },
        "dataSource": "compliance_procedure + permit_record (V0.4 merge)",
    }


def _plan_is_complete(plan: dict[str, Any]) -> bool:
    status = str(plan.get("approval_status") or "").strip()
    status_u = _norm_status(status)
    approved = status in _G02_PLAN_APPROVED_STATUSES or status_u in {
        s.upper() for s in _G02_PLAN_APPROVED_STATUSES
    }
    has_file = plan.get("approval_file_id") is not None
    has_date = plan.get("approval_date") is not None
    # 编制=有方案行；审查/审批=状态通过；文件关联=approval_file_id
    return bool(approved and has_file) or bool(approved and has_date and has_file)


def aggregate_g02_special_plans(project_id: int | None = None) -> dict[str, Any]:
    """Major/larger risk points × special_plan_approval → completed/due."""
    from mysql_api import query_all, query_one

    risks = query_all(
        """
        SELECT id, risk_name, risk_level, control_status, location, control_measure
        FROM safety_risk_point
        WHERE risk_level IN ('重大', '较大')
          AND control_status <> '已销号'
        ORDER BY risk_level = '重大' DESC, id
        """
    ) or []

    plan_sql = """
        SELECT id, project_id, risk_point_id, plan_code, plan_name, risk_level,
               approval_status, approval_date, approval_file_id, source_doc_ref
        FROM special_plan_approval
    """
    params: tuple[Any, ...] = ()
    if project_id is not None:
        plan_sql += " WHERE project_id = %s"
        params = (project_id,)
    plan_sql += " ORDER BY id"
    plans = query_all(plan_sql, params) or []

    plans_by_risk: dict[int, list[dict[str, Any]]] = {}
    for plan in plans:
        rid = int(plan["risk_point_id"])
        plans_by_risk.setdefault(rid, []).append(plan)

    due = len(risks)
    done = 0
    drafted = 0
    approved = 0
    with_file = 0
    objects: list[dict[str, Any]] = []

    for risk in risks:
        rid = int(risk["id"])
        related = plans_by_risk.get(rid, [])
        if related:
            drafted += 1
        best = None
        for plan in related:
            status = str(plan.get("approval_status") or "").strip()
            if status in _G02_PLAN_APPROVED_STATUSES or _norm_status(status) in {
                s.upper() for s in _G02_PLAN_APPROVED_STATUSES
            }:
                approved += 1
                best = plan
                break
            if best is None:
                best = plan
        if best and best.get("approval_file_id") is not None:
            with_file += 1
        complete = bool(best) and _plan_is_complete(best)
        if complete:
            done += 1

        objects.append(
            {
                "objectType": "special_plan_approval" if best else "safety_risk_point",
                "objectId": int(best["id"]) if best else rid,
                "objectName": (best.get("plan_name") if best else None)
                or risk.get("risk_name")
                or f"风险源#{rid}",
                "status": (best.get("approval_status") if best else "未编制"),
                "riskLevel": "HIGH"
                if risk.get("risk_level") == "重大"
                else ("MEDIUM" if not complete else "NORMAL"),
                "fields": {
                    "riskPointId": rid,
                    "riskName": risk.get("risk_name"),
                    "riskLevel": risk.get("risk_level"),
                    "controlStatus": risk.get("control_status"),
                    "location": risk.get("location"),
                    "planCode": best.get("plan_code") if best else None,
                    "planName": best.get("plan_name") if best else None,
                    "approvalStatus": best.get("approval_status") if best else None,
                    "approvalDate": _as_json(best.get("approval_date")) if best else None,
                    "approvalFileId": best.get("approval_file_id") if best else None,
                    "hasPlan": bool(related),
                    "hasApprovalFile": bool(best and best.get("approval_file_id") is not None),
                    "isComplete": complete,
                    "sourceTable": "special_plan_approval" if best else "safety_risk_point",
                },
            }
        )

    rate = int(round(100.0 * done / due)) if due else 0
    value = f"{done}/{due}" if due else "0/0"
    risk_level = "HIGH" if due and done < due else "NORMAL"
    return {
        "key": "G02",
        "value": value,
        "unit": f"{rate}%",
        "hint": f"编制 {drafted}/{due} · 审批通过 {approved}/{due} · 有审批文件 {with_file}/{due}",
        "riskLevel": risk_level,
        "name": "重大风险专项方案",
        "completed": done,
        "due": due,
        "drafted": drafted,
        "approved": approved,
        "withFile": with_file,
        "objects": objects,
        "summary": {
            "total": due,
            "completed": done,
            "pending": max(due - done, 0),
            "abnormal": max(due - done, 0),
            "drafted": drafted,
            "approved": approved,
            "withFile": with_file,
        },
        "dataSource": "safety_risk_point → special_plan_approval (V0.4)",
    }


def aggregate_s02_risk_points() -> dict[str, Any]:
    """Homepage S02: count major/larger active risk objects only."""
    from mysql_api import query_one

    row = query_one(
        """
        SELECT COUNT(*) AS c
        FROM safety_risk_point
        WHERE risk_level IN ('重大', '较大')
          AND control_status <> '已销号'
        """
    )
    count = int(row["c"] or 0) if row else 0
    return {
        "key": "S02",
        "value": count,
        "unit": "项",
        "hint": f"当前纳入管理的重大/较大风险源共{count}项。",
        "riskLevel": "MEDIUM" if count else "NORMAL",
        "name": "重大风险源",
        "dataSource": "safety_risk_point",
    }
