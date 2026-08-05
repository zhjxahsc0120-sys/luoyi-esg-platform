"""
ESG Demo API V0.1 — contract-shaped readers for homepage / KPI detail / risk warnings.

Source of truth: esg_demo_api_contract_v0.1.md
Data: esg_demo_indicator_* + biz_* Demo tables / v_esg_demo_* views.

When Demo tables are missing, functions return None so callers can fall back
to legacy builders (never invent live-looking numbers).
"""

from __future__ import annotations

import json
import logging
from datetime import date, datetime
from decimal import Decimal
from typing import Any

import mysql_api as m

logger = logging.getLogger("esg_demo_api")

DEFAULT_PROJECT_ID = 1001
GROUP_THEME = {"E": "green", "S": "blue", "G": "purple"}
GROUP_TITLE = {"E": "环境环保组", "S": "社会责任组", "G": "治理合规组"}
KPI_ORDER = [
    "E01",
    "E02",
    "E03",
    "E04",
    "S01",
    "S02",
    "S03",
    "S04",
    "G01",
    "G02",
    "G03",
    "G04",
]

SURVEY_LABEL = {
    "COMPLETED": "文物调查已完成",
    "IN_PROGRESS": "文物调查进行中",
    "PENDING": "文物调查待开展",
}

RISK_CN = {
    "NORMAL": "正常",
    "LOW": "低",
    "MEDIUM": "关注",
    "HIGH": "较高",
    "CRITICAL": "严重",
}

LEVEL_TO_RYB = {
    "CRITICAL": "红",
    "HIGH": "红",
    "MEDIUM": "黄",
    "LOW": "蓝",
    "NORMAL": "蓝",
}


def _jf(value: Any) -> Any:
    if isinstance(value, Decimal):
        return int(value) if value == value.to_integral_value() else float(value)
    if isinstance(value, (datetime, date)):
        return value.strftime("%Y-%m-%d %H:%M:%S") if isinstance(value, datetime) else value.isoformat()
    if isinstance(value, str):
        text = value.strip()
        if re_fullmatch_number(text):
            try:
                num = Decimal(text)
                return int(num) if num == num.to_integral_value() else float(num)
            except Exception:
                return value
        return value
    return value


def re_fullmatch_number(text: str) -> bool:
    if not text:
        return False
    try:
        Decimal(text)
        return True
    except Exception:
        return False


def _json_obj(value: Any) -> dict:
    if value is None:
        return {}
    if isinstance(value, dict):
        return value
    if isinstance(value, (bytes, bytearray)):
        return json.loads(value.decode("utf-8"))
    if isinstance(value, str):
        try:
            parsed = json.loads(value)
            return parsed if isinstance(parsed, dict) else {}
        except Exception:
            return {}
    return {}


def demo_available() -> bool:
    try:
        row = m.query_one("SELECT COUNT(*) AS c FROM esg_demo_indicator_result WHERE result_status = 'PUBLISHED'")
        return bool(row and int(row["c"] or 0) > 0)
    except Exception:
        return False


def _latest_period(project_id: int) -> str | None:
    row = m.query_one(
        """
        SELECT MAX(period_end) AS period_end
        FROM esg_demo_indicator_result
        WHERE project_id = %s AND result_status = 'PUBLISHED'
        """,
        (project_id,),
    )
    if not row or not row.get("period_end"):
        return None
    pe = row["period_end"]
    return pe.isoformat() if hasattr(pe, "isoformat") else str(pe)


def get_demo_dashboard_kpis(project_id: int = DEFAULT_PROJECT_ID, period_end: str | None = None) -> dict | None:
    """GET /api/dashboard/kpis — contract items[] + groups for existing UI."""
    if not demo_available():
        return None
    pe = period_end or _latest_period(project_id)
    if not pe:
        return None
    try:
        rows = m.query_all(
            """
            SELECT project_id, `key`, name, `value`, unit, hint, riskLevel, period_end
            FROM v_esg_demo_dashboard_kpis
            WHERE project_id = %s AND period_end = %s
            """,
            (project_id, pe),
        )
    except Exception as exc:
        logger.warning("demo kpis view unavailable: %s", exc)
        return None
    if not rows:
        return None

    by_key = {str(r["key"]): r for r in rows}
    items = []
    for key in KPI_ORDER:
        row = by_key.get(key)
        if not row:
            continue
        items.append(
            {
                "key": key,
                "name": row.get("name") or key,
                "value": _jf(row.get("value")),
                "unit": row.get("unit") or "",
                "hint": row.get("hint") or "",
                "riskLevel": row.get("riskLevel") or "NORMAL",
            }
        )

    groups: dict[str, dict] = {
        g: {
            "key": g,
            "title": GROUP_TITLE[g],
            "theme": GROUP_THEME[g],
            "status": "总体可控",
            "items": [],
        }
        for g in ("E", "S", "G")
    }
    for item in items:
        g = item["key"][0]
        if g not in groups:
            continue
        groups[g]["items"].append(
            {
                "key": item["key"],
                "label": item["name"],
                "fullName": item["name"],
                "value": item["value"],
                "unit": item["unit"],
                "hint": item["hint"],
                "riskLevel": item["riskLevel"],
            }
        )

    # V0.4 live overlays: replace V0.3 published G01/G02 (and verify S02) from fact tables
    try:
        from esg_v04_kpi_aggregate import (
            aggregate_g01_compliance_and_permit,
            aggregate_g02_special_plans,
            aggregate_s02_risk_points,
        )

        live_by_key = {
            "G01": aggregate_g01_compliance_and_permit(),
            "G02": aggregate_g02_special_plans(project_id),
            "S02": aggregate_s02_risk_points(),
        }
        for bucket in (items, *(group["items"] for group in groups.values())):
            for item in bucket:
                live = live_by_key.get(item["key"])
                if not live:
                    continue
                item["value"] = live["value"]
                item["unit"] = live.get("unit") or item.get("unit") or ""
                item["hint"] = live.get("hint") or item.get("hint") or ""
                item["riskLevel"] = live.get("riskLevel") or item.get("riskLevel") or "NORMAL"
                if live.get("name"):
                    item["name"] = live["name"]
                    if "label" in item:
                        item["label"] = live["name"]
                    if "fullName" in item:
                        item["fullName"] = live["name"]
    except Exception as exc:
        logger.warning("V0.4 G01/G02/S02 live aggregate failed: %s", exc)

    # Group status from risk levels
    for gkey, group in groups.items():
        levels = [it.get("riskLevel") for it in group["items"]]
        high = sum(1 for lv in levels if lv in {"HIGH", "CRITICAL"})
        mid = sum(1 for lv in levels if lv == "MEDIUM")
        low = sum(1 for lv in levels if lv == "LOW")
        if high or mid or low:
            group["status"] = f"风险 {high + mid + low} · 红{high} 黄{mid} 蓝{low}"

    return {
        "projectId": project_id,
        "periodEnd": pe,
        "source": "esg_demo",
        "items": items,
        "groups": [groups["E"], groups["S"], groups["G"]],
    }


def _e04_fields(project_id: int) -> dict:
    try:
        row = m.query_one(
            """
            SELECT
              COUNT(*) AS object_count,
              MAX(survey_status) AS survey_status,
              AVG(measure_rate) AS measure_rate,
              MAX(risk_status) AS risk_status
            FROM biz_cultural_relic_object
            WHERE project_id = %s
              AND COALESCE(is_deleted, 0) = 0
            """,
            (project_id,),
        )
    except Exception:
        row = None
    if not row or int(row.get("object_count") or 0) == 0:
        # Contract empty-state: survey done, 0 objects, risk normal
        return {
            "objectCount": 0,
            "surveyStatus": "COMPLETED",
            "measureRate": 100,
            "riskStatus": "NORMAL",
        }
    return {
        "objectCount": int(row["object_count"]),
        "surveyStatus": row.get("survey_status") or "COMPLETED",
        "measureRate": _jf(row.get("measure_rate") if row.get("measure_rate") is not None else 100),
        "riskStatus": row.get("risk_status") or "NORMAL",
    }


def _summary_for_key(key: str, objects: list[dict], result_row: dict) -> dict:
    project_id = int(result_row.get("project_id") or DEFAULT_PROJECT_ID)
    if key == "E01":
        try:
            agg = aggregate_e01(project_id)
            return {
                "total": agg["monitorPointCount"],
                "monitorPointCount": agg["monitorPointCount"],
                "anomalyCount": agg["anomalyCount"],
                "openCount": agg["openCount"],
                "riskLevel": agg["riskLevel"],
                "abnormal": agg["anomalyCount"],
            }
        except Exception:
            pass
    if key == "E02":
        try:
            agg = aggregate_e02(project_id)
            return {
                "total": agg["objectCount"],
                "objectCount": agg["objectCount"],
                "riskCount": agg["riskCount"],
                "completionRate": agg["completionRate"],
                "restoreNormalCount": agg["restoreNormalCount"],
                "abnormal": agg["riskCount"],
            }
        except Exception:
            pass
    if key == "E03":
        try:
            agg = aggregate_e03(project_id)
            return {
                "total": agg["areaCount"] + agg["protectedCount"],
                "areaCount": agg["areaCount"],
                "protectedCount": agg["protectedCount"],
                "riskCount": agg["riskCount"],
                "riskStatus": agg["riskStatus"],
                "abnormal": agg["riskCount"],
            }
        except Exception:
            pass
    if key == "E04":
        fields = _e04_fields(project_id)
        return {
            "total": fields["objectCount"],
            "objectCount": fields["objectCount"],
            "surveyStatus": fields["surveyStatus"],
            "measureRate": fields["measureRate"],
            "riskStatus": fields["riskStatus"],
        }
    if key == "G01":
        completed = sum(
            1
            for o in objects
            if any(tok in str(o.get("status") or "") for tok in ("完成", "办结", "通过", "APPROVED", "DONE", "CLOSED"))
        )
        pending = max(0, len(objects) - completed)
        abnormal = sum(1 for o in objects if (o.get("riskLevel") or "") in {"MEDIUM", "HIGH", "CRITICAL"})
        return {
            "total": len(objects) or _jf(result_row.get("value_decimal")) or 0,
            "completed": completed,
            "pending": pending,
            "abnormal": abnormal,
        }
    if key == "G02":
        # V0.4 fallback when live aggregate unavailable: special-plan completion fields
        drafted = sum(1 for o in objects if (o.get("fields") or {}).get("hasPlan"))
        approved = sum(
            1
            for o in objects
            if any(
                tok in str(o.get("status") or "")
                for tok in ("已审批", "已通过", "通过", "已完成", "APPROVED", "PASSED")
            )
        )
        with_file = sum(1 for o in objects if (o.get("fields") or {}).get("hasApprovalFile"))
        completed = sum(1 for o in objects if (o.get("fields") or {}).get("isComplete"))
        total = len(objects) or _jf(result_row.get("value_decimal")) or 0
        return {
            "total": total,
            "completed": completed,
            "pending": max(0, int(total) - completed),
            "abnormal": max(0, int(total) - completed),
            "drafted": drafted,
            "approved": approved,
            "withFile": with_file,
        }
    if key == "G03":
        pending = sum(1 for o in objects if "PENDING" in str(o.get("status") or "").upper() or "待审批" in str(o.get("status") or ""))
        abnormal = sum(1 for o in objects if (o.get("riskLevel") or "") in {"MEDIUM", "HIGH", "CRITICAL"})
        return {"total": len(objects) or _jf(result_row.get("value_decimal")) or 0, "pending": pending, "abnormal": abnormal}
    if key == "G04":
        open_n = sum(1 for o in objects if str(o.get("status") or "").upper() in {"OPEN", "未关闭"} or o.get("status") == "OPEN")
        closed = sum(1 for o in objects if str(o.get("status") or "").upper() in {"CLOSED", "已关闭"})
        return {"total": len(objects) or _jf(result_row.get("value_decimal")) or 0, "open": open_n, "closed": closed, "abnormal": open_n}
    abnormal = sum(1 for o in objects if (o.get("riskLevel") or "") in {"MEDIUM", "HIGH", "CRITICAL"})
    return {"total": len(objects) or _jf(result_row.get("value_decimal")) or 0, "abnormal": abnormal}


def _modal_summary_cards(key: str, summary: dict) -> list[dict]:
    if key == "E04":
        return [
            {"label": "文物保护对象", "value": summary.get("objectCount", 0), "unit": "处"},
            {"label": "文物调查状态", "value": SURVEY_LABEL.get(str(summary.get("surveyStatus")), summary.get("surveyStatus")), "unit": ""},
            {"label": "保护措施落实率", "value": summary.get("measureRate", 100), "unit": "%"},
            {"label": "风险状态", "value": RISK_CN.get(str(summary.get("riskStatus")), summary.get("riskStatus")), "unit": ""},
        ]
    if key == "G01":
        return [
            {"label": "应完成事项", "value": summary.get("total", 0), "unit": "项"},
            {"label": "已完成", "value": summary.get("completed", 0), "unit": "项"},
            {"label": "审批完成", "value": f"{summary.get('procedureCompleted', 0)}/{summary.get('procedureDue', 0)}", "unit": ""},
            {"label": "许可完成", "value": f"{summary.get('permitCompleted', 0)}/{summary.get('permitDue', 0)}", "unit": ""},
        ]
    if key == "G02":
        return [
            {"label": "应编制专项方案", "value": summary.get("total", 0), "unit": "项"},
            {"label": "已完成闭环", "value": summary.get("completed", 0), "unit": "项"},
            {"label": "已编制", "value": summary.get("drafted", 0), "unit": "项"},
            {"label": "已审批", "value": summary.get("approved", 0), "unit": "项"},
            {"label": "有审批文件", "value": summary.get("withFile", 0), "unit": "项"},
        ]
    if key == "G03":
        return [
            {"label": "设计变更", "value": summary.get("total", 0), "unit": "项"},
            {"label": "待审批", "value": summary.get("pending", 0), "unit": "项"},
            {"label": "异常/风险", "value": summary.get("abnormal", 0), "unit": "项"},
            {"label": "已纳入台账", "value": summary.get("total", 0), "unit": "项"},
        ]
    if key == "G04":
        return [
            {"label": "内控事项", "value": summary.get("total", 0), "unit": "项"},
            {"label": "未关闭", "value": summary.get("open", 0), "unit": "项"},
            {"label": "已关闭", "value": summary.get("closed", 0), "unit": "项"},
            {"label": "风险事项", "value": summary.get("abnormal", 0), "unit": "项"},
        ]
    return [{"label": k, "value": v, "unit": ""} for k, v in summary.items()]


_STATUS_CN = {
    "VALID": "有效",
    "EXPIRING": "临期",
    "OVERDUE": "逾期",
    "PENDING": "待审批",
    "APPROVED": "已审批",
    "OPEN": "未关闭",
    "CLOSED": "已关闭",
    "COMPLETE": "齐全",
    "MISSING": "缺失",
    "IMPLEMENTED": "已实施",
    "NOT_STARTED": "未开始",
    "IN_PROGRESS": "进行中",
    "NORMAL": "正常",
    "HIGH": "较高",
    "MEDIUM": "关注",
    "LOW": "低",
    "CRITICAL": "严重",
}


def _status_cn(value: Any) -> str:
    if value is None or value == "":
        return "—"
    text = str(value)
    mapped = _STATUS_CN.get(text.upper())
    return mapped or text


def _detail_rows_for_modal(key: str, objects: list[dict]) -> list[dict]:
    rows = []
    for obj in objects:
        fields = obj.get("fields") or {}
        if key == "G01":
            rows.append(
                {
                    "name": obj.get("objectName"),
                    "type": fields.get("bucket")
                    or fields.get("procedureType")
                    or fields.get("permitType")
                    or "报批报建",
                    "status": _status_cn(obj.get("status")),
                    "deadline": _jf(fields.get("deadline") or fields.get("expireDate")) or "—",
                    "department": fields.get("department") or "—",
                    "progress": fields.get("progressPercent")
                    if fields.get("progressPercent") is not None
                    else _status_cn(obj.get("status")),
                    "objectId": obj.get("objectId"),
                    "objectType": obj.get("objectType"),
                    "riskLevel": obj.get("riskLevel"),
                }
            )
        elif key == "G02":
            rows.append(
                {
                    "name": obj.get("objectName"),
                    "number": fields.get("planCode") or fields.get("riskPointId") or obj.get("objectId"),
                    "type": fields.get("riskLevel") or "专项方案",
                    "deadline": _jf(fields.get("approvalDate")) or "—",
                    "department": fields.get("location") or "—",
                    "status": _status_cn(obj.get("status")),
                    "approvalStatus": _status_cn(fields.get("approvalStatus") or obj.get("status") or ""),
                    "objectId": obj.get("objectId"),
                    "objectType": obj.get("objectType"),
                    "riskLevel": obj.get("riskLevel"),
                    "hasPlan": fields.get("hasPlan"),
                    "hasApprovalFile": fields.get("hasApprovalFile"),
                    "isComplete": fields.get("isComplete"),
                }
            )
        elif key == "G03":
            rows.append(
                {
                    "name": obj.get("objectName"),
                    "changeType": fields.get("changeType") or "设计变更",
                    "approveStatus": _status_cn(fields.get("approveStatus") or obj.get("status")),
                    "implementation": _status_cn(fields.get("implementationStatus") or "—"),
                    "attachment": _status_cn(fields.get("attachmentStatus") or "—"),
                    "status": _status_cn(obj.get("status")),
                    "locationDesc": fields.get("locationDesc") or "—",
                    "objectId": obj.get("objectId"),
                    "riskLevel": obj.get("riskLevel"),
                }
            )
        elif key == "G04":
            rows.append(
                {
                    "name": obj.get("objectName"),
                    "module": fields.get("issueType") or "内控廉洁",
                    "issueLevel": fields.get("issueLevel") or "—",
                    "deadline": fields.get("deadline") or "—",
                    "owner": fields.get("responsibleUnit") or "—",
                    "status": _status_cn(obj.get("status")),
                    "action": _status_cn(fields.get("evidenceStatus") or ""),
                    "objectId": obj.get("objectId"),
                    "riskLevel": obj.get("riskLevel"),
                }
            )
        else:
            rows.append(
                {
                    "name": obj.get("objectName"),
                    "status": obj.get("status"),
                    "riskLevel": obj.get("riskLevel"),
                    "objectId": obj.get("objectId"),
                    "objectType": obj.get("objectType"),
                }
            )
    return rows


def _load_objects_for_kpi(key: str, project_id: int) -> list[dict]:
    """Prefer demo detail table; enrich from biz tables for G02/G03/G04/E04."""
    objects: list[dict] = []
    try:
        detail_rows = m.query_all(
            """
            SELECT objectType, objectId, objectName, metricLabel, metricValue, metricUnit,
                   status, riskLevel, detailJson
            FROM v_esg_demo_kpi_detail
            WHERE project_id = %s AND kpi_key = %s
            ORDER BY objectId
            """,
            (project_id, key),
        )
    except Exception:
        detail_rows = []

    for row in detail_rows or []:
        fields = _json_obj(row.get("detailJson"))
        objects.append(
            {
                "objectType": row.get("objectType"),
                "objectId": int(row["objectId"]) if row.get("objectId") is not None else None,
                "objectName": row.get("objectName"),
                "status": row.get("status"),
                "riskLevel": row.get("riskLevel") or "NORMAL",
                "fields": fields,
                "metricLabel": row.get("metricLabel"),
                "metricValue": row.get("metricValue"),
                "metricUnit": row.get("metricUnit"),
            }
        )

    # Enrich lists from business tables when only one seeded detail row exists
    if key == "G03":
        try:
            biz = m.query_all(
                """
                SELECT id, change_code, change_type, change_name, approve_status,
                       implementation_status, attachment_status, risk_status, location_desc
                FROM biz_design_change
                WHERE project_id = %s AND COALESCE(is_deleted, 0) = 0
                ORDER BY id
                """,
                (project_id,),
            )
            if biz:
                objects = [
                    {
                        "objectType": "biz_design_change",
                        "objectId": int(r["id"]),
                        "objectName": r.get("change_name") or r.get("change_code"),
                        "status": r.get("approve_status"),
                        "riskLevel": r.get("risk_status") or "NORMAL",
                        "fields": {
                            "changeType": r.get("change_type"),
                            "approveStatus": r.get("approve_status"),
                            "implementationStatus": r.get("implementation_status"),
                            "attachmentStatus": r.get("attachment_status"),
                            "locationDesc": r.get("location_desc"),
                        },
                    }
                    for r in biz
                ]
        except Exception as exc:
            logger.warning("G03 biz_design_change read failed: %s", exc)
    elif key == "G02":
        try:
            from esg_v04_kpi_aggregate import aggregate_g02_special_plans

            live = aggregate_g02_special_plans(project_id)
            if live.get("objects"):
                objects = live["objects"]
        except Exception as exc:
            logger.warning("G02 special_plan_approval read failed: %s", exc)
    elif key == "G01":
        try:
            from esg_v04_kpi_aggregate import aggregate_g01_compliance_and_permit

            live = aggregate_g01_compliance_and_permit()
            if live.get("objects"):
                objects = live["objects"]
        except Exception as exc:
            logger.warning("G01 compliance+permit read failed: %s", exc)
    elif key == "G04":
        try:
            biz = m.query_all(
                """
                SELECT id, issue_code, issue_type, issue_level, issue_description,
                       current_status, deadline, evidence_status, risk_status
                FROM biz_internal_control_issue
                WHERE project_id = %s AND COALESCE(is_deleted, 0) = 0
                ORDER BY id
                """,
                (project_id,),
            )
            if biz:
                objects = [
                    {
                        "objectType": "biz_internal_control_issue",
                        "objectId": int(r["id"]),
                        "objectName": r.get("issue_description") or r.get("issue_code"),
                        "status": r.get("current_status"),
                        "riskLevel": r.get("risk_status") or "NORMAL",
                        "fields": {
                            "issueType": r.get("issue_type"),
                            "issueLevel": r.get("issue_level"),
                            "deadline": _jf(r.get("deadline")),
                            "evidenceStatus": r.get("evidence_status"),
                        },
                    }
                    for r in biz
                ]
        except Exception as exc:
            logger.warning("G04 internal control read failed: %s", exc)
    elif key == "E01":
        try:
            ensure_e01_demo_tables(project_id)
            agg = aggregate_e01(project_id)
            objects = []
            for p in agg["points"]:
                pid = int(p["id"])
                exceed = [
                    r
                    for r in agg["results"]
                    if int(r["point_id"]) == pid and str(r.get("judgement") or "").upper() == "EXCEEDED"
                ]
                latest = exceed[0] if exceed else next((r for r in agg["results"] if int(r["point_id"]) == pid), None)
                objects.append(
                    {
                        "objectType": "biz_env_monitor_point",
                        "objectId": pid,
                        "objectName": p.get("point_name") or p.get("point_code"),
                        "status": p.get("case_status") or ("超标" if exceed else "正常"),
                        "riskLevel": p.get("risk_status") or ("HIGH" if exceed else "NORMAL"),
                        "fields": {
                            "pointCode": p.get("point_code"),
                            "monitorCategory": p.get("monitor_category"),
                            "locationDesc": p.get("location_desc"),
                            "detectedValue": _jf(latest.get("detected_value")) if latest else None,
                            "limitValue": _jf(latest.get("limit_value")) if latest else None,
                            "factorName": latest.get("factor_name") if latest else None,
                            "exceedCount": len(exceed),
                        },
                    }
                )
        except Exception as exc:
            logger.warning("E01 env monitor read failed: %s", exc)
    elif key == "E02":
        try:
            agg = aggregate_e02(project_id)
            objects = [
                {
                    "objectType": o.get("objectTable") or "biz_soil_disposal_site",
                    "objectId": o["id"],
                    "objectName": o["objectName"],
                    "status": o.get("status") or o.get("restoreStatus"),
                    "riskLevel": o.get("riskStatusRaw") or "NORMAL",
                    "fields": {
                        "objectType": o["objectType"],
                        "objectTypeLabel": o["objectTypeLabel"],
                        "locationText": o["locationText"],
                        "completionRate": o["completionRate"],
                        "measureStatus": o["measureStatus"],
                        "responsibleUnit": o["responsibleUnit"],
                    },
                }
                for o in agg["objects"]
            ]
        except Exception as exc:
            logger.warning("E02 soil objects read failed: %s", exc)
    elif key == "E03":
        try:
            agg = aggregate_e03(project_id)
            objects = [
                {
                    "objectType": o.get("objectTable") or "biz_ecological_sensitive_area",
                    "objectId": o["id"],
                    "objectName": o["objectName"],
                    "status": o.get("relatedMatter"),
                    "riskLevel": o.get("riskStatusRaw") or "NORMAL",
                    "fields": {
                        "objectKind": o["objectKind"],
                        "locationText": o["locationText"],
                        "protectionRequirement": o["protectionRequirement"],
                        "responsibleUnit": o["responsibleUnit"],
                    },
                }
                for o in agg["objects"]
            ]
        except Exception as exc:
            logger.warning("E03 eco objects read failed: %s", exc)
    elif key == "E04":
        try:
            agg = aggregate_e04(project_id)
            objects = [
                {
                    "objectType": "biz_cultural_relic_object",
                    "objectId": o["id"],
                    "objectName": o.get("relicName") or o.get("relicCode"),
                    "status": o.get("surveyStatus") or "COMPLETED",
                    "riskLevel": o.get("riskStatus") or "NORMAL",
                    "fields": {
                        "relicType": o.get("relicType"),
                        "protectionLevel": o.get("protectionLevel"),
                        "locationDesc": o.get("locationDesc"),
                        "surveyStatus": o.get("surveyStatus"),
                        "measureRate": o.get("measureRate"),
                        "responsibleUnit": o.get("responsibleUnit"),
                        "protectionMeasure": o.get("protectionMeasure"),
                    },
                }
                for o in agg["objects"]
            ]
        except Exception as exc:
            logger.warning("E04 cultural read failed: %s", exc)

    return objects


def get_demo_kpi_detail(key: str, project_id: int = DEFAULT_PROJECT_ID, period_end: str | None = None) -> dict | None:
    """GET /api/dashboard/kpi/{key} — contract + modal bridge fields."""
    if not demo_available():
        return None
    key = (key or "").upper()
    if key not in KPI_ORDER:
        return None
    pe = period_end or _latest_period(project_id)
    if not pe:
        return None
    result = m.query_one(
        """
        SELECT id, project_id, period_end, kpi_key, kpi_name, domain_code,
               value_decimal, value_text, unit, hint, risk_level, source_summary
        FROM esg_demo_indicator_result
        WHERE project_id = %s AND period_end = %s AND kpi_key = %s AND result_status = 'PUBLISHED'
        """,
        (project_id, pe, key),
    )
    if not result:
        return None

    objects = _load_objects_for_kpi(key, project_id)
    summary = _summary_for_key(key, objects, result)
    value = _jf(result.get("value_decimal"))
    if value is None:
        value = result.get("value_text")

    # Phase B.1: E-group homepage/detail value from same live aggregation as workspace
    if key == "E01":
        try:
            value = aggregate_e01(project_id)["homeValue"]
        except Exception:
            pass
    elif key == "E02":
        try:
            value = aggregate_e02(project_id)["homeValue"]
        except Exception:
            pass
    elif key == "E03":
        try:
            value = aggregate_e03(project_id)["homeValue"]
        except Exception:
            pass
    elif key == "E04":
        try:
            value = aggregate_e04(project_id)["homeValue"]
        except Exception:
            pass
    elif key == "G01":
        try:
            from esg_v04_kpi_aggregate import aggregate_g01_compliance_and_permit

            live = aggregate_g01_compliance_and_permit()
            value = live["value"]
            summary = live["summary"]
            objects = live.get("objects") or objects
            result = dict(result)
            result["unit"] = live.get("unit") or ""
            result["hint"] = live.get("hint") or ""
            result["risk_level"] = live.get("riskLevel") or "NORMAL"
            result["source_summary"] = live.get("dataSource")
            result["kpi_name"] = live.get("name") or "合规审批与许可"
        except Exception as exc:
            logger.warning("G01 live detail aggregate failed: %s", exc)
    elif key == "G02":
        try:
            from esg_v04_kpi_aggregate import aggregate_g02_special_plans

            live = aggregate_g02_special_plans(project_id)
            value = live["value"]
            summary = live["summary"]
            objects = live.get("objects") or objects
            result = dict(result)
            result["unit"] = live.get("unit") or ""
            result["hint"] = live.get("hint") or ""
            result["risk_level"] = live.get("riskLevel") or "NORMAL"
            result["source_summary"] = live.get("dataSource")
            result["kpi_name"] = live.get("name") or "重大风险专项方案"
        except Exception as exc:
            logger.warning("G02 live detail aggregate failed: %s", exc)
    elif key == "S02":
        try:
            from esg_v04_kpi_aggregate import aggregate_s02_risk_points

            live = aggregate_s02_risk_points()
            value = live["value"]
            result = dict(result)
            result["unit"] = live.get("unit") or "项"
            result["hint"] = live.get("hint") or ""
            result["risk_level"] = live.get("riskLevel") or "NORMAL"
            result["source_summary"] = live.get("dataSource")
            result["kpi_name"] = live.get("name") or "重大风险源"
        except Exception as exc:
            logger.warning("S02 live detail aggregate failed: %s", exc)

    trend = [{"periodEnd": pe, "value": value}]
    theme = GROUP_THEME.get(key[0], "purple")
    payload: dict[str, Any] = {
        "key": key,
        "name": result.get("kpi_name") or key,
        "fullName": result.get("kpi_name") or key,
        "value": value,
        "unit": result.get("unit") or "",
        "hint": result.get("hint") or "",
        "riskLevel": result.get("risk_level") or "NORMAL",
        "trend": trend,
        "summary": summary,
        "objects": objects,
        "theme": theme,
        "dataSource": result.get("source_summary") or "esg_demo",
        "updateTime": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "isMock": False,
        "isDemo": True,
        "source": "esg_demo",
        # Modal bridge (legacy UI expects label/value summary list + detailData)
        "summaryCards": _modal_summary_cards(key, summary),
        "detailData": _detail_rows_for_modal(key, objects),
        "detailTitle": f"{result.get('kpi_name') or key}明细",
        "chartTitle": f"{result.get('kpi_name') or key}趋势",
    }

    if key in {"E01", "E02", "E03", "E04"}:
        names = {
            "E01": "环保风险预警",
            "E02": "水保风险预警",
            "E03": "生态保护管控",
            "E04": "文物保护管控",
        }
        payload["name"] = names[key]
        payload["fullName"] = names[key]
        if key == "E01":
            payload["unit"] = "次"
            payload["riskLevel"] = summary.get("riskLevel") or payload["riskLevel"]
            payload["hint"] = f"{summary.get('anomalyCount', value)} 次超标 · 监测点 {summary.get('monitorPointCount', 0)} · 未闭环 {summary.get('openCount', 0)}"
        elif key == "E02":
            payload["unit"] = "%"
            try:
                payload["riskLevel"] = aggregate_e02(project_id).get("riskLevel") or payload["riskLevel"]
            except Exception:
                pass
            payload["hint"] = f"对象 {summary.get('objectCount', 0)} · 落实率 {summary.get('completionRate', value)}% · 风险 {summary.get('riskCount', 0)}"
        elif key == "E03":
            payload["unit"] = "%"
            try:
                payload["riskLevel"] = aggregate_e03(project_id).get("riskLevel") or payload["riskLevel"]
            except Exception:
                pass
            payload["hint"] = f"敏感区 {summary.get('areaCount', 0)} · 保护对象 {summary.get('protectedCount', 0)} · 风险 {summary.get('riskCount', 0)}"
        elif key == "E04":
            fields = _e04_fields(project_id)
            payload.update(fields)
            payload["unit"] = "处"
            payload["summary"] = summary
            payload["modalSummary"] = _modal_summary_cards(key, summary)

    # G-group display names (Phase A / contract) — override Demo seed short names
    g_names = {
        "G01": "合规审批与许可",
        "G02": "重大风险专项方案",
        "G03": "设计变更管理",
        "G04": "合规管理天数",
    }
    if key in g_names:
        payload["name"] = g_names[key]
        payload["fullName"] = g_names[key]

    # Modals read summary as list of {label,value}
    if key in {"G01", "G02", "G03", "G04", "E04"}:
        payload["summaryList"] = _modal_summary_cards(key, summary)

    return payload


def get_demo_kpi_object(
    key: str,
    object_id: int,
    project_id: int = DEFAULT_PROJECT_ID,
) -> dict | None:
    """GET /api/dashboard/kpi/{key}/objects/{objectId}"""
    objects = _load_objects_for_kpi(key.upper(), project_id)
    match = next((o for o in objects if o.get("objectId") == int(object_id)), None)
    if not match:
        return None
    warnings = []
    try:
        warnings = m.query_all(
            """
            SELECT warning_level AS level, domain_code AS domain, kpi_key AS kpiKey,
                   object_id AS objectId, object_name_snapshot AS objectName,
                   responsible_unit AS responsibleUnit, status, warning_reason AS reason,
                   trigger_time AS triggerTime
            FROM biz_risk_warning
            WHERE project_id = %s AND kpi_key = %s AND object_id = %s
            """,
            (project_id, key.upper(), int(object_id)),
        )
    except Exception:
        warnings = []

    return {
        "kpiKey": key.upper(),
        "objectId": int(object_id),
        "objectType": match.get("objectType"),
        "objectName": match.get("objectName"),
        "responsibleUnit": (match.get("fields") or {}).get("responsibleUnit") or "",
        "status": match.get("status"),
        "riskLevel": match.get("riskLevel"),
        "fields": match.get("fields") or {},
        "evidence": [],
        "riskWarnings": [
            {
                "level": w.get("level"),
                "domain": w.get("domain"),
                "kpiKey": w.get("kpiKey"),
                "objectId": w.get("objectId"),
                "objectName": w.get("objectName"),
                "responsibleUnit": w.get("responsibleUnit"),
                "status": w.get("status"),
                "reason": w.get("reason"),
                "triggerTime": _jf(w.get("triggerTime")),
            }
            for w in warnings or []
        ],
        "source": "esg_demo",
    }


def get_demo_risk_warnings(
    project_id: int = DEFAULT_PROJECT_ID,
    status: str | None = None,
    page: int = 1,
    page_size: int = 20,
) -> dict | None:
    """GET /api/dashboard/risk-warnings"""
    if not demo_available():
        # Still try biz_risk_warning alone
        try:
            m.query_one("SELECT 1 AS ok FROM biz_risk_warning LIMIT 1")
        except Exception:
            return None
    try:
        params: list[Any] = [project_id]
        where = "WHERE project_id = %s"
        if status:
            # OPEN maps to OPEN/IN_PROGRESS for demo convenience
            if status.upper() == "OPEN":
                where += " AND status IN ('OPEN', 'IN_PROGRESS')"
            else:
                where += " AND status = %s"
                params.append(status)
        count_row = m.query_one(f"SELECT COUNT(*) AS c FROM biz_risk_warning {where}", tuple(params))
        total = int(count_row["c"]) if count_row else 0
        page = max(1, int(page or 1))
        page_size = max(1, min(100, int(page_size or 20)))
        offset = (page - 1) * page_size
        rows = m.query_all(
            f"""
            SELECT warning_level AS level, domain_code AS domain, kpi_key AS kpiKey,
                   object_id AS objectId, object_name_snapshot AS objectName,
                   responsible_unit AS responsibleUnit, status,
                   warning_reason AS reason, trigger_time AS triggerTime
            FROM biz_risk_warning
            {where}
            ORDER BY trigger_time DESC, id DESC
            LIMIT %s OFFSET %s
            """,
            tuple(params + [page_size, offset]),
        )
    except Exception as exc:
        logger.warning("demo risk-warnings unavailable: %s", exc)
        return None

    items = []
    for r in rows or []:
        items.append(
            {
                "level": r.get("level"),
                "domain": r.get("domain"),
                "kpiKey": r.get("kpiKey"),
                "objectId": int(r["objectId"]) if r.get("objectId") is not None else None,
                "objectName": r.get("objectName"),
                "responsibleUnit": r.get("responsibleUnit"),
                "status": r.get("status"),
                "reason": r.get("reason"),
                "triggerTime": _jf(r.get("triggerTime")),
            }
        )
    return {"items": items, "total": total, "page": page, "pageSize": page_size, "source": "esg_demo"}


def risk_warnings_to_panel_items(payload: dict | None) -> list[dict]:
    """Map contract risk items → ComplianceRiskPanel WarningListItem shape."""
    if not payload:
        return []
    out = []
    for item in payload.get("items") or []:
        level = LEVEL_TO_RYB.get(str(item.get("level") or "").upper(), "蓝")
        domain = (item.get("domain") or "E")[:1].upper()
        if domain not in {"E", "S", "G"}:
            domain = "E"
        title = item.get("objectName") or item.get("reason") or "风险事项"
        trigger = item.get("triggerTime") or ""
        if isinstance(trigger, str) and len(trigger) >= 16:
            updated = trigger[5:16].replace("-", "/")
        else:
            updated = str(trigger)[:16]
        out.append(
            {
                "level": level,
                "title": title,
                "source": domain,
                "status": item.get("status") or "OPEN",
                "updatedAt": updated,
                # Contract navigation keys — required for click drill-down
                "kpiKey": item.get("kpiKey"),
                "objectId": item.get("objectId"),
                "objectName": item.get("objectName"),
                "responsibleUnit": item.get("responsibleUnit"),
                "domain": item.get("domain"),
                "reason": item.get("reason"),
                "contractLevel": item.get("level"),
            }
        )
    return out


def risk_warnings_to_compliance_metrics(payload: dict | None) -> list[dict]:
    items = (payload or {}).get("items") or []
    red = yellow = blue = 0
    for item in items:
        badge = LEVEL_TO_RYB.get(str(item.get("level") or "").upper(), "蓝")
        if badge == "红":
            red += 1
        elif badge == "黄":
            yellow += 1
        else:
            blue += 1
    total = red + yellow + blue
    return [
        {"label": "红色预警", "value": red, "unit": "项", "tone": "red"},
        {"label": "黄色预警", "value": yellow, "unit": "项", "tone": "yellow"},
        {"label": "蓝色提醒", "value": blue, "unit": "项", "tone": "blue"},
        {"label": "预警合计", "value": total, "unit": "项", "tone": "neutral"},
    ]


# ---------------------------------------------------------------------------
# Phase B.1 — E-group Demo closed loop (shared aggregations + workspace APIs)
# ---------------------------------------------------------------------------

CATEGORY_LABEL = {"AIR": "环境空气", "WATER": "水质", "NOISE": "噪声"}
E02_TYPE_META = {
    "SPOIL": ("弃土场", "biz_soil_disposal_site"),
    "TEMP_LAND": ("临时用地", "biz_temporary_land_use"),
    "TOPSOIL": ("表土剥离", "biz_topsoil_stripping"),
    "SLOPE": ("边坡复绿", "biz_construction_slope"),
}
ORG_NAME = {
    4001: "一工区施工单位",
    4002: "二工区施工单位",
}


def _risk_badge(level: str | None) -> str:
    return LEVEL_TO_RYB.get(str(level or "NORMAL").upper(), "蓝")


def _risk_cn(level: str | None) -> str:
    return RISK_CN.get(str(level or "NORMAL").upper(), str(level or "正常"))


def _is_abnormal_risk(level: str | None) -> bool:
    return str(level or "NORMAL").upper() in {"MEDIUM", "HIGH", "CRITICAL"}


def _open_risk_count(project_id: int, kpi_key: str) -> int:
    try:
        row = m.query_one(
            """
            SELECT COUNT(*) AS c
            FROM biz_risk_warning
            WHERE project_id = %s AND kpi_key = %s
              AND status IN ('OPEN', 'IN_PROGRESS')
            """,
            (project_id, kpi_key),
        )
        return int(row["c"] or 0) if row else 0
    except Exception:
        return 0


def _kpi_risk_level(project_id: int, kpi_key: str, fallback: str = "NORMAL") -> str:
    try:
        row = m.query_one(
            """
            SELECT risk_level
            FROM esg_demo_indicator_result
            WHERE project_id = %s AND kpi_key = %s AND result_status = 'PUBLISHED'
            ORDER BY period_end DESC
            LIMIT 1
            """,
            (project_id, kpi_key),
        )
        if row and row.get("risk_level"):
            return str(row["risk_level"])
    except Exception:
        pass
    try:
        row = m.query_one(
            """
            SELECT warning_level
            FROM biz_risk_warning
            WHERE project_id = %s AND kpi_key = %s
              AND status IN ('OPEN', 'IN_PROGRESS')
            ORDER BY FIELD(warning_level,'CRITICAL','HIGH','MEDIUM','LOW','NORMAL'), id DESC
            LIMIT 1
            """,
            (project_id, kpi_key),
        )
        if row and row.get("warning_level"):
            return str(row["warning_level"])
    except Exception:
        pass
    return fallback


def ensure_e01_demo_tables(project_id: int = DEFAULT_PROJECT_ID) -> bool:
    """Create slim Demo env monitor tables when V2 biz_env_monitor_* are absent."""
    try:
        m.query_one("SELECT 1 AS ok FROM biz_env_monitor_point LIMIT 1")
        m.query_one("SELECT 1 AS ok FROM biz_env_monitor_result LIMIT 1")
        return True
    except Exception:
        pass
    try:
        m.execute(
            """
            CREATE TABLE IF NOT EXISTS biz_env_monitor_point (
              id BIGINT UNSIGNED NOT NULL,
              project_id BIGINT UNSIGNED NOT NULL,
              section_id BIGINT UNSIGNED NULL,
              point_code VARCHAR(64) NOT NULL,
              point_name VARCHAR(200) NOT NULL,
              monitor_category VARCHAR(32) NOT NULL,
              location_desc VARCHAR(500) NULL,
              longitude DECIMAL(10,7) NULL,
              latitude DECIMAL(10,7) NULL,
              active_status VARCHAR(16) NOT NULL DEFAULT 'ACTIVE',
              risk_status VARCHAR(16) NOT NULL DEFAULT 'NORMAL',
              case_status VARCHAR(32) NULL,
              responsible_unit VARCHAR(200) NULL,
              updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
              is_deleted TINYINT UNSIGNED NOT NULL DEFAULT 0,
              PRIMARY KEY (id),
              UNIQUE KEY uk_demo_env_point (project_id, point_code)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
            """
        )
        m.execute(
            """
            CREATE TABLE IF NOT EXISTS biz_env_monitor_result (
              id BIGINT UNSIGNED NOT NULL,
              project_id BIGINT UNSIGNED NOT NULL,
              point_id BIGINT UNSIGNED NOT NULL,
              factor_code VARCHAR(64) NOT NULL,
              factor_name VARCHAR(128) NOT NULL,
              detected_value DECIMAL(18,4) NULL,
              limit_value DECIMAL(18,4) NULL,
              unit VARCHAR(32) NULL,
              judgement VARCHAR(20) NOT NULL,
              exceed_multiple DECIMAL(12,4) NULL,
              sampled_at DATETIME NULL,
              case_status VARCHAR(32) NULL,
              is_closed TINYINT UNSIGNED NOT NULL DEFAULT 0,
              rectification_note VARCHAR(500) NULL,
              updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
              is_deleted TINYINT UNSIGNED NOT NULL DEFAULT 0,
              PRIMARY KEY (id),
              KEY idx_demo_env_result_point (project_id, point_id, judgement)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
            """
        )
    except Exception as exc:
        logger.warning("create biz_env_monitor_* failed: %s", exc)
        return False

    try:
        count = m.query_one(
            "SELECT COUNT(*) AS c FROM biz_env_monitor_point WHERE project_id = %s",
            (project_id,),
        )
        if count and int(count["c"] or 0) > 0:
            return True
    except Exception:
        return False

    # Seed aligned with Demo KPI: 3 points, 12 results, 2 exceeds on point 11001
    points = [
        (11001, project_id, 2001, "E01-AIR-001", "K12 扬尘监测点", "AIR", "K12+050 路基作业面", 114.1200000, 30.4100000, "HIGH", "RECTIFYING", "一工区施工单位"),
        (11002, project_id, 2001, "E01-WATER-001", "一标废水排放口", "WATER", "K12+300 施工营地排水口", 114.0800000, 30.4100000, "NORMAL", "CLOSED", "一工区施工单位"),
        (11003, project_id, 2002, "E01-NOISE-001", "二标噪声敏感点", "NOISE", "K18+150 居民点旁", 114.2200000, 30.4800000, "NORMAL", "CLOSED", "二工区施工单位"),
    ]
    for p in points:
        try:
            m.execute(
                """
                INSERT INTO biz_env_monitor_point
                (id, project_id, section_id, point_code, point_name, monitor_category,
                 location_desc, longitude, latitude, active_status, risk_status, case_status,
                 responsible_unit, is_deleted)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,'ACTIVE',%s,%s,%s,0)
                ON DUPLICATE KEY UPDATE point_name=VALUES(point_name), risk_status=VALUES(risk_status)
                """,
                p,
            )
        except Exception as exc:
            logger.warning("seed env point failed: %s", exc)

    results = [
        # 2 exceeds on 11001 (homepage value=2)
        (51001, project_id, 11001, "PM10", "PM10日均浓度", 168, 150, "μg/m³", "EXCEEDED", 1.12, "2026-08-01 08:00:00", "RECTIFYING", 0, "洒水抑尘已启动"),
        (51002, project_id, 11001, "TSP", "总悬浮颗粒物", 320, 300, "μg/m³", "EXCEEDED", 1.07, "2026-08-02 08:00:00", "RECTIFYING", 0, "苫盖复核中"),
        (51003, project_id, 11001, "PM10", "PM10日均浓度", 120, 150, "μg/m³", "COMPLIANT", None, "2026-07-28 08:00:00", "CLOSED", 1, None),
        (51004, project_id, 11001, "PM10", "PM10日均浓度", 110, 150, "μg/m³", "COMPLIANT", None, "2026-07-25 08:00:00", "CLOSED", 1, None),
        (51005, project_id, 11002, "SS", "悬浮物", 45, 70, "mg/L", "COMPLIANT", None, "2026-08-01 09:00:00", "CLOSED", 1, None),
        (51006, project_id, 11002, "SS", "悬浮物", 52, 70, "mg/L", "COMPLIANT", None, "2026-07-28 09:00:00", "CLOSED", 1, None),
        (51007, project_id, 11002, "COD", "化学需氧量", 38, 50, "mg/L", "COMPLIANT", None, "2026-07-25 09:00:00", "CLOSED", 1, None),
        (51008, project_id, 11002, "pH", "pH值", 7.2, 9.0, "", "COMPLIANT", None, "2026-07-22 09:00:00", "CLOSED", 1, None),
        (51009, project_id, 11003, "LAeqD", "昼间等效声级", 58, 70, "dB(A)", "COMPLIANT", None, "2026-08-01 10:00:00", "CLOSED", 1, None),
        (51010, project_id, 11003, "LAeqN", "夜间等效声级", 48, 55, "dB(A)", "COMPLIANT", None, "2026-07-30 22:00:00", "CLOSED", 1, None),
        (51011, project_id, 11003, "LAeqD", "昼间等效声级", 61, 70, "dB(A)", "COMPLIANT", None, "2026-07-25 10:00:00", "CLOSED", 1, None),
        (51012, project_id, 11001, "PM2.5", "PM2.5日均浓度", 55, 75, "μg/m³", "COMPLIANT", None, "2026-07-20 08:00:00", "CLOSED", 1, None),
    ]
    for r in results:
        try:
            m.execute(
                """
                INSERT INTO biz_env_monitor_result
                (id, project_id, point_id, factor_code, factor_name, detected_value, limit_value,
                 unit, judgement, exceed_multiple, sampled_at, case_status, is_closed,
                 rectification_note, is_deleted)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,0)
                ON DUPLICATE KEY UPDATE judgement=VALUES(judgement), detected_value=VALUES(detected_value)
                """,
                r,
            )
        except Exception as exc:
            logger.warning("seed env result failed: %s", exc)
    return True


def _e01_points_rows(project_id: int) -> list[dict]:
    ensure_e01_demo_tables(project_id)
    try:
        return m.query_all(
            """
            SELECT id, point_code, point_name, monitor_category, location_desc,
                   longitude, latitude, risk_status, case_status, responsible_unit,
                   section_id, updated_at
            FROM biz_env_monitor_point
            WHERE project_id = %s AND COALESCE(is_deleted, 0) = 0
            ORDER BY id
            """,
            (project_id,),
        )
    except Exception as exc:
        logger.warning("E01 points read failed: %s", exc)
        return []


def _e01_results_rows(project_id: int, point_id: int | None = None) -> list[dict]:
    ensure_e01_demo_tables(project_id)
    try:
        if point_id is not None:
            return m.query_all(
                """
                SELECT id, point_id, factor_code, factor_name, detected_value, limit_value,
                       unit, judgement, exceed_multiple, sampled_at, case_status, is_closed,
                       rectification_note, updated_at
                FROM biz_env_monitor_result
                WHERE project_id = %s AND point_id = %s AND COALESCE(is_deleted, 0) = 0
                ORDER BY sampled_at DESC, id DESC
                """,
                (project_id, point_id),
            )
        return m.query_all(
            """
            SELECT id, point_id, factor_code, factor_name, detected_value, limit_value,
                   unit, judgement, exceed_multiple, sampled_at, case_status, is_closed,
                   rectification_note, updated_at
            FROM biz_env_monitor_result
            WHERE project_id = %s AND COALESCE(is_deleted, 0) = 0
            ORDER BY sampled_at DESC, id DESC
            """,
            (project_id,),
        )
    except Exception as exc:
        logger.warning("E01 results read failed: %s", exc)
        return []


def aggregate_e01(project_id: int = DEFAULT_PROJECT_ID) -> dict:
    """Shared E01 aggregation for homepage KPI + workspace overview."""
    points = _e01_points_rows(project_id)
    results = _e01_results_rows(project_id)
    exceed = [r for r in results if str(r.get("judgement") or "").upper() == "EXCEEDED"]
    open_exceed = [r for r in exceed if not int(r.get("is_closed") or 0)]
    open_point_ids = {int(r["point_id"]) for r in open_exceed}
    risk_level = _kpi_risk_level(project_id, "E01", "HIGH" if exceed else "NORMAL")
    by_cat = {"WATER": 0, "AIR": 0, "NOISE": 0}
    for p in points:
        cat = str(p.get("monitor_category") or "").upper()
        if cat in by_cat:
            by_cat[cat] += 1
    return {
        "monitorPointCount": len(points),
        "anomalyCount": len(exceed),
        "openCount": len(open_point_ids),
        "riskLevel": risk_level,
        "riskLevelLabel": _risk_badge(risk_level) if _is_abnormal_risk(risk_level) else _risk_cn(risk_level),
        "resultCount": len(results),
        "byCategory": by_cat,
        "points": points,
        "results": results,
        "openPointIds": open_point_ids,
        "homeValue": len(exceed),
        "homeUnit": "次",
    }


def _e02_load_objects(project_id: int) -> list[dict]:
    objects: list[dict] = []
    queries = [
        (
            "SPOIL",
            """
            SELECT id, object_code, object_name, location_desc AS location_text, section_id,
                   disposal_status AS status, control_measure AS measure_text,
                   measure_rate AS completion_rate, risk_status, responsible_org_id,
                   updated_at, '弃土场管控要求：截排水、拦挡、苫盖' AS measure_requirement,
                   CONCAT(COALESCE(location_desc,''),'；容量与状态见台账') AS space_desc
            FROM biz_soil_disposal_site
            WHERE project_id = %s AND COALESCE(is_deleted, 0) = 0
            """,
        ),
        (
            "TEMP_LAND",
            """
            SELECT id, object_code, object_name,
                   CONCAT(COALESCE(land_type,''),' / ',COALESCE(area_mu,''),' 亩') AS location_text,
                   section_id, restore_status AS status,
                   CONCAT('审批', COALESCE(approval_status,''), '；恢复', COALESCE(restore_status,'')) AS measure_text,
                   measure_rate AS completion_rate, risk_status, responsible_org_id,
                   updated_at, '临时用地管控：用毕清运并按期复垦' AS measure_requirement,
                   CONCAT(COALESCE(land_type,''),' 临时用地') AS space_desc
            FROM biz_temporary_land_use
            WHERE project_id = %s AND COALESCE(is_deleted, 0) = 0
            """,
        ),
        (
            "TOPSOIL",
            """
            SELECT id, object_code, object_name,
                   CONCAT('计划', COALESCE(planned_area_mu,''), '亩 / 完成', COALESCE(completed_area_mu,''), '亩') AS location_text,
                   section_id, current_status AS status, storage_measure AS measure_text,
                   completion_rate, risk_status, responsible_org_id, updated_at,
                   '表土剥离：集中堆存覆盖，禁止与弃渣混堆' AS measure_requirement,
                   COALESCE(storage_measure, '表土堆存区') AS space_desc
            FROM biz_topsoil_stripping
            WHERE project_id = %s AND COALESCE(is_deleted, 0) = 0
            """,
        ),
        (
            "SLOPE",
            """
            SELECT id, object_code, object_name,
                   CONCAT(COALESCE(slope_type,''),' ',COALESCE(chainage,'')) AS location_text,
                   section_id, stability_status AS status, protection_measure AS measure_text,
                   greening_rate AS completion_rate, risk_status, responsible_org_id, updated_at,
                   '边坡复绿：防护与植被恢复至稳定' AS measure_requirement,
                   CONCAT(COALESCE(slope_type,''),' @ ',COALESCE(chainage,'')) AS space_desc
            FROM biz_construction_slope
            WHERE project_id = %s AND COALESCE(is_deleted, 0) = 0
            """,
        ),
    ]
    for obj_type, sql in queries:
        try:
            rows = m.query_all(sql, (project_id,))
        except Exception as exc:
            logger.warning("E02 load %s failed: %s", obj_type, exc)
            rows = []
        label, table = E02_TYPE_META[obj_type]
        for r in rows or []:
            risk = r.get("risk_status") or "NORMAL"
            rate = _jf(r.get("completion_rate"))
            if rate is None:
                rate = 0
            status = str(r.get("status") or "")
            restore_ok = status.upper() in {"RESTORED", "COMPLETED", "STABLE", "CLOSED"} or (
                isinstance(rate, (int, float)) and float(rate) >= 100 and not _is_abnormal_risk(risk)
            )
            objects.append(
                {
                    "id": int(r["id"]),
                    "objectCode": r.get("object_code") or "",
                    "objectName": r.get("object_name") or "",
                    "objectType": obj_type,
                    "objectTypeLabel": label,
                    "objectTable": table,
                    "locationText": r.get("location_text") or "",
                    "sectionCode": f"S{r['section_id']}" if r.get("section_id") else None,
                    "riskLevel": _risk_badge(risk),
                    "riskStatus": _risk_cn(risk),
                    "riskStatusRaw": risk,
                    "restoreStatus": "已恢复" if restore_ok else ("整改中" if _is_abnormal_risk(risk) else status or "管控中"),
                    "measureStatus": r.get("measure_text") or "",
                    "completionRate": float(rate) if isinstance(rate, (int, float)) else 0,
                    "responsibleUnit": ORG_NAME.get(int(r["responsible_org_id"]), "责任单位")
                    if r.get("responsible_org_id") is not None
                    else "责任单位",
                    "canLocate": False,
                    "spatialLinks": [],
                    "updateTime": _jf(r.get("updated_at")),
                    "measureRequirement": r.get("measure_requirement") or "",
                    "rectificationStatus": "整改中" if _is_abnormal_risk(risk) else "措施落实",
                    "spaceDesc": r.get("space_desc") or r.get("location_text") or "",
                    "status": status,
                }
            )
    objects.sort(key=lambda o: o["id"])
    return objects


def aggregate_e02(project_id: int = DEFAULT_PROJECT_ID) -> dict:
    objects = _e02_load_objects(project_id)
    by_type = {"SPOIL": 0, "TEMP_LAND": 0, "TOPSOIL": 0, "SLOPE": 0}
    rates: list[float] = []
    risk_count = 0
    restore_ok = 0
    for o in objects:
        by_type[o["objectType"]] = by_type.get(o["objectType"], 0) + 1
        rates.append(float(o.get("completionRate") or 0))
        if _is_abnormal_risk(o.get("riskStatusRaw")):
            risk_count += 1
        if o.get("restoreStatus") == "已恢复":
            restore_ok += 1
    avg = round(sum(rates) / len(rates), 1) if rates else 100.0
    risk_level = _kpi_risk_level(project_id, "E02", "MEDIUM" if risk_count else "NORMAL")
    return {
        "objectCount": len(objects),
        "riskCount": risk_count or _open_risk_count(project_id, "E02"),
        "completionRate": avg,
        "restoreNormalCount": restore_ok,
        "byType": by_type,
        "objects": objects,
        "riskLevel": risk_level,
        "homeValue": avg,
        "homeUnit": "%",
    }


def _e03_load_objects(project_id: int) -> list[dict]:
    objects: list[dict] = []
    try:
        areas = m.query_all(
            """
            SELECT id, object_code, object_name, location_desc, section_id,
                   sensitive_type, protection_measure, monitoring_status, risk_status,
                   responsible_org_id, updated_at, protection_level
            FROM biz_ecological_sensitive_area
            WHERE project_id = %s AND COALESCE(is_deleted, 0) = 0
            ORDER BY id
            """,
            (project_id,),
        )
    except Exception as exc:
        logger.warning("E03 sensitive areas failed: %s", exc)
        areas = []
    for r in areas or []:
        risk = r.get("risk_status") or "NORMAL"
        objects.append(
            {
                "id": int(r["id"]),
                "objectCode": r.get("object_code") or "",
                "objectName": r.get("object_name") or "",
                "objectKind": "SENSITIVE",
                "objectKindLabel": "生态敏感区域",
                "locationText": r.get("location_desc") or "",
                "sectionCode": f"S{r['section_id']}" if r.get("section_id") else None,
                "riskLevel": _risk_badge(risk),
                "riskStatus": _risk_cn(risk),
                "riskStatusRaw": risk,
                "protectionRequirement": r.get("protection_measure") or "",
                "responsibleUnit": ORG_NAME.get(int(r["responsible_org_id"]), "责任单位")
                if r.get("responsible_org_id") is not None
                else "责任单位",
                "relatedMatter": f"{r.get('sensitive_type') or '敏感区'} · {r.get('monitoring_status') or ''}",
                "canLocate": False,
                "spatialLinks": [],
                "updateTime": _jf(r.get("updated_at")),
                "objectTable": "biz_ecological_sensitive_area",
            }
        )
    try:
        prots = m.query_all(
            """
            SELECT id, object_code, object_name, location_desc, section_id,
                   object_type, protection_measure, inspection_status, risk_status,
                   responsible_org_id, updated_at, importance_level
            FROM biz_ecological_protection_object
            WHERE project_id = %s AND COALESCE(is_deleted, 0) = 0
            ORDER BY id
            """,
            (project_id,),
        )
    except Exception as exc:
        logger.warning("E03 protection objects failed: %s", exc)
        prots = []
    for r in prots or []:
        risk = r.get("risk_status") or "NORMAL"
        objects.append(
            {
                "id": int(r["id"]),
                "objectCode": r.get("object_code") or "",
                "objectName": r.get("object_name") or "",
                "objectKind": "PROTECTED",
                "objectKindLabel": "生态保护对象",
                "locationText": r.get("location_desc") or "",
                "sectionCode": f"S{r['section_id']}" if r.get("section_id") else None,
                "riskLevel": _risk_badge(risk),
                "riskStatus": _risk_cn(risk),
                "riskStatusRaw": risk,
                "protectionRequirement": r.get("protection_measure") or "",
                "responsibleUnit": ORG_NAME.get(int(r["responsible_org_id"]), "责任单位")
                if r.get("responsible_org_id") is not None
                else "责任单位",
                "relatedMatter": f"{r.get('object_type') or '保护对象'} · {r.get('inspection_status') or ''}",
                "canLocate": False,
                "spatialLinks": [],
                "updateTime": _jf(r.get("updated_at")),
                "objectTable": "biz_ecological_protection_object",
            }
        )
    return objects


def aggregate_e03(project_id: int = DEFAULT_PROJECT_ID) -> dict:
    objects = _e03_load_objects(project_id)
    area_count = sum(1 for o in objects if o["objectKind"] == "SENSITIVE")
    protected_count = sum(1 for o in objects if o["objectKind"] == "PROTECTED")
    risk_count = sum(1 for o in objects if _is_abnormal_risk(o.get("riskStatusRaw")))
    risk_level = _kpi_risk_level(project_id, "E03", "MEDIUM" if risk_count else "NORMAL")
    # Identification rate: Demo seed all CONFIRMED → 100
    identified = len(objects)
    total = max(identified, 1)
    rate = round(100.0 * identified / total, 1) if objects else 100.0
    return {
        "areaCount": area_count,
        "protectedCount": protected_count,
        "riskCount": risk_count or _open_risk_count(project_id, "E03"),
        "riskStatus": _risk_cn(risk_level),
        "riskLevel": risk_level,
        "objects": objects,
        "homeValue": rate,
        "homeUnit": "%",
    }


def aggregate_e04(project_id: int = DEFAULT_PROJECT_ID) -> dict:
    """Demo project only (1001) — excludes legacy LUOYI-ESG seed rows."""
    fields = _e04_fields(project_id)
    objects = []
    try:
        rows = m.query_all(
            """
            SELECT id, relic_code, relic_name, relic_type, protection_level,
                   location_desc, survey_status, measure_rate, risk_status,
                   responsible_org_id, protection_measure, protection_scope,
                   impact_analysis, longitude, latitude, section_id, updated_at,
                   source_doc_ref
            FROM biz_cultural_relic_object
            WHERE project_id = %s AND COALESCE(is_deleted, 0) = 0
            ORDER BY id
            """,
            (project_id,),
        )
    except Exception:
        try:
            rows = m.query_all(
                """
                SELECT id, relic_code, relic_name, relic_type, protection_level,
                       location_desc, survey_status, measure_rate, risk_status,
                       responsible_unit, protection_measure, protection_scope,
                       construction_impact AS impact_analysis, longitude, latitude,
                       section_id, update_time AS updated_at
                FROM biz_cultural_relic_object
                WHERE CAST(project_id AS CHAR) = %s
                ORDER BY id
                """,
                (str(project_id),),
            )
        except Exception as exc:
            logger.warning("E04 cultural aggregate failed: %s", exc)
            rows = []
    for r in rows or []:
        unit = r.get("responsible_unit")
        if not unit and r.get("responsible_org_id") is not None:
            unit = ORG_NAME.get(int(r["responsible_org_id"]), "")
        objects.append(
            {
                "id": int(r["id"]),
                "relicCode": r.get("relic_code") or "",
                "relicName": r.get("relic_name") or "",
                "relicType": r.get("relic_type") or "",
                "protectionLevel": r.get("protection_level") or "",
                "locationDesc": r.get("location_desc") or "",
                "riskStatus": r.get("risk_status") or "NORMAL",
                "responsibleUnit": unit or "",
                "updateTime": _jf(r.get("updated_at")),
                "surveyStatus": r.get("survey_status") or "COMPLETED",
                "measureRate": _jf(r.get("measure_rate")),
                "protectionMeasure": r.get("protection_measure") or "",
                "protectionScope": r.get("protection_scope") or "",
                "constructionImpact": r.get("impact_analysis") or "",
                "longitude": _jf(r.get("longitude")),
                "latitude": _jf(r.get("latitude")),
                "sectionId": int(r["section_id"]) if r.get("section_id") is not None else None,
                "projectId": str(project_id),
            }
        )
    return {
        **fields,
        "objects": objects,
        "riskCount": sum(1 for o in objects if _is_abnormal_risk(o.get("riskStatus"))),
        "homeValue": fields["objectCount"],
        "homeUnit": "处",
    }


def _apply_live_e_kpi_overlay(items: list[dict], project_id: int) -> None:
    """Align homepage E01–E04 values with workspace shared aggregations."""
    try:
        e01 = aggregate_e01(project_id)
        e02 = aggregate_e02(project_id)
        e03 = aggregate_e03(project_id)
        e04 = aggregate_e04(project_id)
    except Exception as exc:
        logger.warning("live E overlay skipped: %s", exc)
        return
    overlays = {
        "E01": {
            "value": e01["homeValue"],
            "unit": e01["homeUnit"],
            "hint": f"{e01['resultCount']} 个监测结果中有 {e01['anomalyCount']} 次超标，涉及 {e01['openCount']} 个监测点。",
            "riskLevel": e01["riskLevel"],
        },
        "E02": {
            "value": e02["homeValue"],
            "unit": e02["homeUnit"],
            "hint": f"4 类对象共 {e02['objectCount']} 处，措施平均落实率 {e02['completionRate']}%，风险对象 {e02['riskCount']} 个。",
            "riskLevel": e02["riskLevel"],
        },
        "E03": {
            "value": e03["homeValue"],
            "unit": e03["homeUnit"],
            "hint": f"{e03['areaCount']} 个敏感区、{e03['protectedCount']} 个保护对象已识别；风险对象 {e03['riskCount']} 个。",
            "riskLevel": e03["riskLevel"],
        },
        "E04": {
            "value": e04["homeValue"],
            "unit": e04["homeUnit"],
            "hint": f"调查已完成，识别 {e04['objectCount']} 处文物对象，保护措施落实率 {e04.get('measureRate', 100)}%。",
            "riskLevel": e04.get("riskStatus") or "NORMAL",
        },
    }
    for item in items:
        key = item.get("key")
        if key in overlays:
            item.update(overlays[key])
            # Prefer catalog display names for homepage
            names = {"E01": "环保风险预警", "E02": "水保风险预警", "E03": "生态保护管控", "E04": "文物保护管控"}
            item["name"] = names.get(key, item.get("name"))


def get_e01_demo_events(project_id: int = DEFAULT_PROJECT_ID) -> dict | None:
    if not demo_available() and not ensure_e01_demo_tables(project_id):
        return None
    agg = aggregate_e01(project_id)
    points = agg["points"]
    results = agg["results"]
    by_point: dict[int, list] = {}
    for r in results:
        by_point.setdefault(int(r["point_id"]), []).append(r)

    open_points = []
    events = []
    map_points = []
    for p in points:
        pid = int(p["id"])
        cat = str(p.get("monitor_category") or "AIR").upper()
        point_results = by_point.get(pid, [])
        exceed = [r for r in point_results if str(r.get("judgement") or "").upper() == "EXCEEDED"]
        # List focuses on points with open anomalies; include compliant-only as closed context
        focus = exceed or point_results[:1]
        factors = []
        event_ids = []
        for r in focus:
            rid = int(r["id"])
            event_ids.append(rid)
            factors.append(
                {
                    "factorCode": r.get("factor_code"),
                    "factorName": r.get("factor_name"),
                    "detectedValue": _jf(r.get("detected_value")),
                    "limitValue": _jf(r.get("limit_value")),
                    "unit": r.get("unit"),
                    "exceedMultiple": _jf(r.get("exceed_multiple")),
                    "resultId": rid,
                    "eventId": rid,
                }
            )
        primary = event_ids[0] if event_ids else pid
        is_open = pid in agg["openPointIds"]
        status = p.get("case_status") or ("整改中" if is_open else "正常")
        open_points.append(
            {
                "pointId": pid,
                "pointCode": p.get("point_code"),
                "pointName": p.get("point_name"),
                "sectionCode": f"S{p['section_id']}" if p.get("section_id") else None,
                "sectionName": None,
                "locationText": p.get("location_desc"),
                "monitorCategory": cat,
                "monitorCategoryLabel": CATEGORY_LABEL.get(cat, cat),
                "status": status,
                "caseStatus": p.get("case_status"),
                "discoveredAt": _jf((exceed or point_results or [{}])[0].get("sampled_at")) if (exceed or point_results) else None,
                "longitude": _jf(p.get("longitude")),
                "latitude": _jf(p.get("latitude")),
                "gisFeatureId": None,
                "canLocate": p.get("longitude") is not None,
                "primaryEventId": primary,
                "eventIds": event_ids or [primary],
                "factors": factors,
            }
        )
        for f in factors:
            events.append(
                {
                    "eventId": f["eventId"],
                    "eventCode": f"E01-{f['eventId']}",
                    "title": f"{p.get('point_name')}{f.get('factorName') or ''}超标"
                    if any(str(r.get("judgement")).upper() == "EXCEEDED" for r in point_results if int(r["id"]) == f["eventId"])
                    else f"{p.get('point_name')}监测",
                    "pointId": pid,
                    "pointCode": p.get("point_code"),
                    "pointName": p.get("point_name"),
                    "sectionCode": f"S{p['section_id']}" if p.get("section_id") else None,
                    "locationText": p.get("location_desc"),
                    "monitorCategory": cat,
                    "monitorCategoryLabel": CATEGORY_LABEL.get(cat, cat),
                    "factorCode": f.get("factorCode"),
                    "factorName": f.get("factorName"),
                    "detectedValue": f.get("detectedValue"),
                    "limitValue": f.get("limitValue"),
                    "unit": f.get("unit"),
                    "exceedMultiple": f.get("exceedMultiple"),
                    "status": status,
                    "caseStatus": p.get("case_status"),
                    "isOpen": is_open,
                    "discoveredAt": _jf(next((r.get("sampled_at") for r in point_results if int(r["id"]) == f["eventId"]), None)),
                    "longitude": _jf(p.get("longitude")),
                    "latitude": _jf(p.get("latitude")),
                    "resultId": f.get("resultId"),
                    "resultCode": f"R-{f.get('resultId')}",
                    "sampleId": f.get("resultId"),
                }
            )
        map_points.append(
            {
                "pointId": pid,
                "pointCode": p.get("point_code"),
                "pointName": p.get("point_name"),
                "longitude": _jf(p.get("longitude")),
                "latitude": _jf(p.get("latitude")),
                "gisFeatureId": None,
                "openCount": 1 if is_open else 0,
                "eventCount": len(event_ids),
                "eventIds": event_ids,
                "primaryStatus": status,
                "monitorCategory": cat,
            }
        )

    # Prefer listing open/anomaly points first, but keep all monitor points for count consistency
    overview = {
        "totalOpenPoints": len(open_points),
        "waterCount": agg["byCategory"]["WATER"],
        "airCount": agg["byCategory"]["AIR"],
        "noiseCount": agg["byCategory"]["NOISE"],
        "monitorPointCount": agg["monitorPointCount"],
        "anomalyCount": agg["anomalyCount"],
        "openCount": agg["openCount"],
        "riskLevel": agg["riskLevelLabel"],
    }
    return {
        "code": 0,
        "data": {
            "kpi": {
                "exceedItemCount": agg["anomalyCount"],
                "eventCount": len(events),
                "pointCount": agg["monitorPointCount"],
                "openEventCount": agg["openCount"],
            },
            "overview": overview,
            "byCategory": [
                {"name": "水质", "value": agg["byCategory"]["WATER"]},
                {"name": "空气", "value": agg["byCategory"]["AIR"]},
                {"name": "噪声", "value": agg["byCategory"]["NOISE"]},
            ],
            "byStatus": [
                {"name": "未闭环", "value": agg["openCount"]},
                {"name": "异常", "value": agg["anomalyCount"]},
            ],
            "events": events,
            "openPoints": open_points,
            "mapPoints": map_points,
            "isDemo": True,
            "source": "esg_demo",
        },
    }


def get_e01_demo_event_detail(event_id: int, project_id: int = DEFAULT_PROJECT_ID) -> dict | None:
    ensure_e01_demo_tables(project_id)
    try:
        result = m.query_one(
            """
            SELECT id, point_id, factor_code, factor_name, detected_value, limit_value,
                   unit, judgement, exceed_multiple, sampled_at, case_status, is_closed,
                   rectification_note
            FROM biz_env_monitor_result
            WHERE project_id = %s AND id = %s AND COALESCE(is_deleted, 0) = 0
            """,
            (project_id, event_id),
        )
    except Exception:
        result = None
    if not result:
        return None
    point = m.query_one(
        """
        SELECT id, point_code, point_name, monitor_category, location_desc,
               longitude, latitude, case_status, section_id, responsible_unit
        FROM biz_env_monitor_point
        WHERE project_id = %s AND id = %s
        """,
        (project_id, int(result["point_id"])),
    )
    if not point:
        return None
    cat = str(point.get("monitor_category") or "").upper()
    exceeded = str(result.get("judgement") or "").upper() == "EXCEEDED"
    factor = {
        "resultId": int(result["id"]),
        "resultCode": f"R-{result['id']}",
        "testStage": "初检",
        "factorCode": result.get("factor_code"),
        "factorName": result.get("factor_name"),
        "judgement": "超标" if exceeded else "达标",
        "detectedValue": _jf(result.get("detected_value")),
        "limitValue": _jf(result.get("limit_value")),
        "unit": result.get("unit"),
        "exceedMultiple": _jf(result.get("exceed_multiple")),
    }
    history = [
        {
            "sequenceNo": 1,
            "toStatus": result.get("case_status") or point.get("case_status"),
            "toStatusLabel": result.get("case_status") or point.get("case_status"),
            "actionAt": _jf(result.get("sampled_at")),
            "operatorName": "Demo",
            "comment": "监测结果入库",
        }
    ]
    rect = []
    if result.get("rectification_note"):
        rect.append(
            {
                "id": 1,
                "roundNo": 1,
                "startedAt": _jf(result.get("sampled_at")),
                "summary": result.get("rectification_note"),
                "reviewStatus": "进行中" if not int(result.get("is_closed") or 0) else "已完成",
            }
        )
    # Trend companion: other results for same point/factor
    siblings = _e01_results_rows(project_id, int(point["id"]))
    data = {
        "summary": {
            "eventId": int(result["id"]),
            "eventCode": f"E01-{result['id']}",
            "title": f"{point.get('point_name')}{result.get('factor_name') or ''}",
            "pointId": int(point["id"]),
            "pointCode": point.get("point_code"),
            "pointName": point.get("point_name"),
            "sectionCode": f"S{point['section_id']}" if point.get("section_id") else None,
            "locationText": point.get("location_desc"),
            "monitorCategory": cat,
            "monitorCategoryLabel": CATEGORY_LABEL.get(cat, cat),
            "factorCode": result.get("factor_code"),
            "factorName": result.get("factor_name"),
            "detectedValue": _jf(result.get("detected_value")),
            "limitValue": _jf(result.get("limit_value")),
            "unit": result.get("unit"),
            "exceedMultiple": _jf(result.get("exceed_multiple")),
            "status": result.get("case_status") or point.get("case_status"),
            "caseStatus": result.get("case_status"),
            "isOpen": not bool(int(result.get("is_closed") or 0)) and exceeded,
            "discoveredAt": _jf(result.get("sampled_at")),
            "longitude": _jf(point.get("longitude")),
            "latitude": _jf(point.get("latitude")),
            "resultId": int(result["id"]),
            "resultCode": f"R-{result['id']}",
            "sampleId": int(result["id"]),
            "responsibleOrg": {"name": point.get("responsible_unit")},
        },
        "initialFactors": [factor],
        "allSampleFactors": [
            {
                "resultId": int(s["id"]),
                "resultCode": f"R-{s['id']}",
                "testStage": "初检",
                "factorCode": s.get("factor_code"),
                "factorName": s.get("factor_name"),
                "judgement": "超标" if str(s.get("judgement")).upper() == "EXCEEDED" else "达标",
                "detectedValue": _jf(s.get("detected_value")),
                "limitValue": _jf(s.get("limit_value")),
                "unit": s.get("unit"),
                "exceedMultiple": _jf(s.get("exceed_multiple")),
            }
            for s in siblings
        ],
        "rectificationRounds": rect,
        "retestRounds": [],
        "statusHistory": history,
        "evidence": [],
        "closure": {
            "status": result.get("case_status"),
            "statusLabel": result.get("case_status"),
            "openedAt": _jf(result.get("sampled_at")),
            "closedAt": None if not int(result.get("is_closed") or 0) else _jf(result.get("sampled_at")),
        },
    }
    return {"code": 0, "data": data, "meta": {"source": "esg_demo"}}


def get_e01_demo_point_trend(
    point_id: int,
    factor_code: str | None = None,
    project_id: int = DEFAULT_PROJECT_ID,
) -> dict | None:
    ensure_e01_demo_tables(project_id)
    point = m.query_one(
        """
        SELECT id, point_code, point_name, monitor_category, location_desc,
               longitude, latitude, case_status, section_id
        FROM biz_env_monitor_point
        WHERE project_id = %s AND id = %s AND COALESCE(is_deleted, 0) = 0
        """,
        (project_id, point_id),
    )
    if not point:
        return None
    results = _e01_results_rows(project_id, point_id)
    if not results:
        return None
    preferred = factor_code or results[0].get("factor_code")
    series_src = [r for r in results if r.get("factor_code") == preferred] or results
    series_src = list(reversed(series_src))
    factor_row = series_src[-1]
    cat = str(point.get("monitor_category") or "").upper()
    series = []
    exceed_count = 0
    for r in series_src:
        exceeded = str(r.get("judgement") or "").upper() == "EXCEEDED"
        if exceeded:
            exceed_count += 1
        series.append(
            {
                "at": _jf(r.get("sampled_at")),
                "value": _jf(r.get("detected_value")),
                "valueNum": _jf(r.get("detected_value")),
                "limitValue": _jf(r.get("limit_value")),
                "judgement": r.get("judgement"),
                "exceeded": exceeded,
                "exceedMultiple": _jf(r.get("exceed_multiple")),
                "resultId": int(r["id"]),
                "sampleId": int(r["id"]),
                "testStage": "初检",
            }
        )
    factor_options = []
    seen = set()
    for r in results:
        code = r.get("factor_code")
        if code in seen:
            continue
        seen.add(code)
        factor_options.append(
            {
                "factorCode": code,
                "factorName": r.get("factor_name"),
                "unit": r.get("unit"),
                "sampleCount": sum(1 for x in results if x.get("factor_code") == code),
                "exceedCount": sum(
                    1
                    for x in results
                    if x.get("factor_code") == code and str(x.get("judgement")).upper() == "EXCEEDED"
                ),
            }
        )
    return {
        "code": 0,
        "data": {
            "point": {
                "pointId": int(point["id"]),
                "pointCode": point.get("point_code"),
                "pointName": point.get("point_name"),
                "monitorCategory": cat,
                "monitorCategoryLabel": CATEGORY_LABEL.get(cat, cat),
                "sectionCode": f"S{point['section_id']}" if point.get("section_id") else None,
                "locationText": point.get("location_desc"),
                "status": point.get("case_status"),
                "longitude": _jf(point.get("longitude")),
                "latitude": _jf(point.get("latitude")),
            },
            "factor": {
                "factorCode": factor_row.get("factor_code"),
                "factorName": factor_row.get("factor_name"),
                "unit": factor_row.get("unit"),
                "limitValue": _jf(factor_row.get("limit_value")),
                "limitValueNum": _jf(factor_row.get("limit_value")),
            },
            "series": series,
            "companionSeries": None,
            "stats": {
                "sampleCount": len(series),
                "exceedCount": exceed_count,
                "latestValue": series[-1]["value"] if series else None,
                "latestAt": series[-1]["at"] if series else None,
                "latestExceeded": series[-1]["exceeded"] if series else False,
            },
            "factorOptions": factor_options,
        },
        "meta": {"source": "esg_demo"},
    }


def get_e02_demo_objects(project_id: int = DEFAULT_PROJECT_ID) -> dict | None:
    if not demo_available():
        try:
            m.query_one("SELECT 1 AS ok FROM biz_soil_disposal_site LIMIT 1")
        except Exception:
            return None
    agg = aggregate_e02(project_id)
    items = []
    for o in agg["objects"]:
        items.append(
            {
                "id": o["id"],
                "objectCode": o["objectCode"],
                "objectName": o["objectName"],
                "objectType": o["objectType"],
                "objectTypeLabel": o["objectTypeLabel"],
                "locationText": o["locationText"],
                "sectionCode": o.get("sectionCode"),
                "riskLevel": o["riskLevel"],
                "riskStatus": o["riskStatus"],
                "restoreStatus": o["restoreStatus"],
                "measureStatus": o["measureStatus"],
                "completionRate": o["completionRate"],
                "responsibleUnit": o["responsibleUnit"],
                "canLocate": o["canLocate"],
                "spatialLinks": o["spatialLinks"],
                "updateTime": o["updateTime"],
            }
        )
    return {
        "code": 0,
        "data": {
            "overview": {
                "objectCount": agg["objectCount"],
                "riskCount": agg["riskCount"],
                "completionRate": agg["completionRate"],
                "restoreNormalCount": agg["restoreNormalCount"],
                "byType": agg["byType"],
            },
            "objects": items,
            "scope": "demo",
            "isDemo": True,
            "source": "esg_demo",
        },
    }


def get_e02_demo_object_detail(object_id: int, project_id: int = DEFAULT_PROJECT_ID) -> dict | None:
    agg = aggregate_e02(project_id)
    match = next((o for o in agg["objects"] if o["id"] == int(object_id)), None)
    if not match:
        return None
    data = {
        "id": match["id"],
        "objectCode": match["objectCode"],
        "objectName": match["objectName"],
        "objectType": match["objectType"],
        "objectTypeLabel": match["objectTypeLabel"],
        "locationText": match["locationText"],
        "sectionCode": match.get("sectionCode"),
        "riskLevel": match["riskLevel"],
        "riskStatus": match["riskStatus"],
        "restoreStatus": match["restoreStatus"],
        "measureStatus": match["measureStatus"],
        "completionRate": match["completionRate"],
        "responsibleUnit": match["responsibleUnit"],
        "canLocate": match["canLocate"],
        "spatialLinks": match["spatialLinks"],
        "updateTime": match["updateTime"],
        "measureRequirement": match.get("measureRequirement") or "",
        "rectificationStatus": match.get("rectificationStatus") or "",
        "spaceDesc": match.get("spaceDesc") or match["locationText"],
    }
    return {"code": 0, "data": data, "meta": {"source": "esg_demo"}}


def get_e03_demo_eco_objects(project_id: int = DEFAULT_PROJECT_ID) -> dict | None:
    if not demo_available():
        try:
            m.query_one("SELECT 1 AS ok FROM biz_ecological_sensitive_area LIMIT 1")
        except Exception:
            return None
    agg = aggregate_e03(project_id)
    items = []
    for o in agg["objects"]:
        items.append(
            {
                "id": o["id"],
                "objectCode": o["objectCode"],
                "objectName": o["objectName"],
                "objectKind": o["objectKind"],
                "objectKindLabel": o["objectKindLabel"],
                "locationText": o["locationText"],
                "sectionCode": o.get("sectionCode"),
                "riskLevel": o["riskLevel"],
                "riskStatus": o["riskStatus"],
                "protectionRequirement": o["protectionRequirement"],
                "responsibleUnit": o["responsibleUnit"],
                "relatedMatter": o["relatedMatter"],
                "canLocate": o["canLocate"],
                "spatialLinks": o["spatialLinks"],
                "updateTime": o["updateTime"],
            }
        )
    return {
        "code": 0,
        "data": {
            "overview": {
                "areaCount": agg["areaCount"],
                "protectedCount": agg["protectedCount"],
                "riskCount": agg["riskCount"],
                "riskStatus": agg["riskStatus"],
            },
            "objects": items,
            "scope": "demo",
            "isDemo": True,
            "source": "esg_demo",
        },
    }


def get_e03_demo_eco_object_detail(object_id: int, project_id: int = DEFAULT_PROJECT_ID) -> dict | None:
    agg = aggregate_e03(project_id)
    match = next((o for o in agg["objects"] if o["id"] == int(object_id)), None)
    if not match:
        return None
    data = {k: match[k] for k in match if k not in {"riskStatusRaw", "objectTable"}}
    return {"code": 0, "data": data, "meta": {"source": "esg_demo"}}


def get_e04_demo_cultural_objects(project_id: int = DEFAULT_PROJECT_ID) -> dict | None:
    if not demo_available():
        try:
            m.query_one("SELECT 1 AS ok FROM biz_cultural_relic_object LIMIT 1")
        except Exception:
            return None
    agg = aggregate_e04(project_id)
    overview = {
        "surveyStatus": SURVEY_LABEL.get(str(agg.get("surveyStatus")), agg.get("surveyStatus") or "文物调查已完成"),
        "objectCount": agg["objectCount"],
        "measureRate": agg.get("measureRate", 100),
        "riskCount": agg.get("riskCount", 0),
        "riskStatus": _risk_cn(agg.get("riskStatus")),
        "status": _risk_cn(agg.get("riskStatus")),
    }
    objects = []
    for o in agg["objects"]:
        objects.append(
            {
                "id": o["id"],
                "relicCode": o["relicCode"],
                "relicName": o["relicName"],
                "relicType": o["relicType"],
                "protectionLevel": o["protectionLevel"],
                "locationDesc": o["locationDesc"],
                "riskStatus": _risk_cn(o.get("riskStatus")),
                "responsibleUnit": o["responsibleUnit"],
                "updateTime": o["updateTime"],
            }
        )
    return {
        "code": 0,
        "data": {
            "overview": overview,
            "objects": objects,
            "isDemo": True,
            "source": "esg_demo",
        },
    }


def get_e04_demo_cultural_object_detail(object_id: int, project_id: int = DEFAULT_PROJECT_ID) -> dict | None:
    agg = aggregate_e04(project_id)
    match = next((o for o in agg["objects"] if o["id"] == int(object_id)), None)
    if not match:
        return None
    measure = (match.get("protectionMeasure") or "").strip()
    data = {
        "id": match["id"],
        "relicCode": match["relicCode"],
        "relicName": match["relicName"],
        "relicType": match["relicType"],
        "protectionLevel": match["protectionLevel"],
        "locationDesc": match["locationDesc"],
        "riskStatus": _risk_cn(match.get("riskStatus")),
        "responsibleUnit": match["responsibleUnit"],
        "updateTime": match["updateTime"],
        "projectId": match.get("projectId") or str(project_id),
        "sectionId": match.get("sectionId"),
        "longitude": match.get("longitude"),
        "latitude": match.get("latitude"),
        "protectionScope": match.get("protectionScope") or "",
        "constructionImpact": match.get("constructionImpact") or "",
        "protectionMeasure": measure,
        "materialStatus": "资料齐全（演示）" if measure else "待补充",
    }
    return {"code": 0, "data": data, "meta": {"source": "esg_demo"}}
