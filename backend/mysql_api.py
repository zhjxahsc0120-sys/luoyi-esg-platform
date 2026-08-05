from __future__ import annotations

from decimal import Decimal, ROUND_HALF_UP
from datetime import date, datetime, timedelta
from pathlib import Path
import hashlib
import json
import logging
import os
import re
from typing import Any

logger = logging.getLogger("mysql_api")

from mysql_db import mysql_connect
from carbon_benefit_overview import get_carbon_benefit_overview
from monthly_report_overview import get_monthly_report_overview

try:
    from intelligent_ingestion.content_parser import field_meta as content_field_meta
    from intelligent_ingestion.content_parser import parse_file_content
except ImportError:  # pragma: no cover
    content_field_meta = None  # type: ignore[assignment]
    parse_file_content = None  # type: ignore[assignment]

SERVER_DIR = Path(__file__).resolve().parent
CONTENT_EXTRA_FIELD_KEYS = (
    "project_section",
    "engineering_object",
    "suggested_task",
    "suggested_kpi_code",
    "suggested_kpi_name",
    "summary_note",
    "monitor_unit",
)


GROUP_META = {
    "E": {"key": "E", "title": "环境环保组", "theme": "green", "status": "总体可控"},
    "S": {"key": "S", "title": "社会责任组", "theme": "blue", "status": "总体可控"},
    "G": {"key": "G", "title": "治理合规组", "theme": "purple", "status": "总体可控"},
}

# 首页驾驶舱指标正式名称（现场调研优化 V1.0；覆盖 indicator_result 旧文案）
KPI_HOME_LABELS = {
    "E01": {"label": "环境影响事件", "fullName": "环境影响事件", "unit": "项"},
    "E02": {"label": "未闭环环境问题", "fullName": "未闭环环境问题", "unit": "项"},
    "E03": {"label": "生态保护事项", "fullName": "生态保护事项", "unit": "项"},
    "E04": {"label": "文物保护管控", "fullName": "文物保护管控", "unit": "处"},
    "S01": {"label": "连续安全生产天数", "fullName": "连续安全生产天数", "unit": "天"},
    "S02": {"label": "重大风险源管控", "fullName": "重大风险源管控", "unit": "项"},
    "S03": {"label": "农民工权益保障", "fullName": "农民工权益保障", "unit": "项"},
    "S04": {"label": "群众诉求闭环", "fullName": "群众诉求闭环", "unit": "项"},
    "G01": {"label": "合规审批事项", "fullName": "合规审批事项", "unit": "项"},
    "G02": {"label": "合规问题闭环", "fullName": "合规问题闭环", "unit": "项"},
    "G03": {"label": "参建单位履约评价", "fullName": "参建单位履约评价", "unit": ""},
    "G04": {"label": "治理内控风险", "fullName": "治理内控风险", "unit": "项"},
}

# 生态保护事项：水保台账中与弃土/临时用地/表土/复垦/边坡/敏感相关的类型
E03_ECO_TYPE_REGEX = r"(弃土|弃渣|临时用地|表土|复垦|边坡|生态|敏感)"

E01_CONSTRUCTION_START = "2026-05-08 00:00:00"

# E02 demo 闸：演示部署默认允许；正式部署默认拒绝
# 环境变量 E02_ALLOW_DEMO=1 时允许返回 demo 数据
E02_ALLOW_DEMO = os.environ.get("E02_ALLOW_DEMO", "1").strip() in {"1", "true", "True", "TRUE", "yes"}

# E03 demo 闸：演示部署默认允许；正式部署默认拒绝
# 环境变量 E03_ALLOW_DEMO=1 时允许返回 demo 数据
E03_ALLOW_DEMO = os.environ.get("E03_ALLOW_DEMO", "1").strip() in {"1", "true", "True", "TRUE", "yes"}

# E04 demo 闸：演示部署默认允许；正式部署默认拒绝
# 环境变量 E04_ALLOW_DEMO=1 时允许返回 demo 碳排放数据（低碳增益专题仍用；首页 E04 已切文物保护）
E04_ALLOW_DEMO = os.environ.get("E04_ALLOW_DEMO", "1").strip() in {"1", "true", "True", "TRUE", "yes"}

E04_CULTURAL_PROJECT_ID = "LUOYI-ESG"
E04_CULTURAL_DEMO_PROJECT_IDS = ("LUOYI-ESG", 1001, "1001")
# 表未迁移或空表时的诚实演示种子（调查完成 / 0 对象 / 风险正常 — 契约空态）
E04_CULTURAL_DEMO_FALLBACK = {
    "objectCount": 0,
    "measureRate": 100,
    "riskCount": 0,
    "status": "正常",
    "riskStatus": "正常",
    "surveyStatus": "文物调查已完成",
}

# S01 demo 闸：演示部署默认允许；正式部署默认拒绝
# 环境变量 S01_ALLOW_DEMO=1 时允许返回 demo 连续安全生产天数数据
S01_ALLOW_DEMO = os.environ.get("S01_ALLOW_DEMO", "1").strip() in {"1", "true", "True", "TRUE", "yes"}

# S03 demo 闸：演示部署默认允许；正式部署返回甲方口径业务零（无未办结）
# 环境变量 S03_ALLOW_DEMO=1 时允许返回农民工工资类 demo 台账
S03_ALLOW_DEMO = os.environ.get("S03_ALLOW_DEMO", "1").strip() in {"1", "true", "True", "TRUE", "yes"}

# S03 统计范围：仅农民工工资方面上访/纠纷（排除工伤、退场结算、材料商等）
S03_WAGE_DISPUTE_TYPES = ("工资支付", "农民工工资", "工资上访")


def value_for_json(value: Any) -> Any:
    if isinstance(value, Decimal):
        return int(value) if value == value.to_integral_value() else float(value)
    if isinstance(value, (datetime, date)):
        return value.strftime("%Y-%m-%d %H:%M:%S") if isinstance(value, datetime) else value.isoformat()
    return value


def json_column(value: Any) -> dict:
    if value is None:
        return {}
    if isinstance(value, dict):
        return value
    if isinstance(value, (bytes, bytearray)):
        return json.loads(value.decode("utf-8"))
    if isinstance(value, str):
        return json.loads(value)
    return dict(value)


def query_all(sql: str, params: tuple[Any, ...] = ()) -> list[dict]:
    with mysql_connect() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, params)
            return list(cur.fetchall())


def query_one(sql: str, params: tuple[Any, ...] = ()) -> dict | None:
    with mysql_connect() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, params)
            return cur.fetchone()


def execute(sql: str, params: tuple[Any, ...] = ()) -> int:
    with mysql_connect() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, params)
            return cur.rowcount


def next_id(table: str, start: int) -> int:
    row = query_one(f"SELECT COALESCE(MAX(id), %s - 1) + 1 AS next_id FROM {table}", (start,))
    return int(row["next_id"])


def _safe_count(sql: str, params: tuple[Any, ...] = ()) -> int | None:
    """Return COUNT result, or None when table/column unavailable."""
    try:
        row = query_one(sql, params)
        if row is None or row.get("c") is None:
            return 0
        return int(row["c"])
    except Exception:
        return None


def _e04_cultural_summary_from_rows(rows: list[dict]) -> dict:
    total = len(rows)
    if total == 0:
        return dict(E04_CULTURAL_DEMO_FALLBACK)
    # Prefer measure_rate column when present (Demo V0.1)
    rates = [r.get("measure_rate") for r in rows if r.get("measure_rate") is not None]
    if rates:
        measure_rate = round(float(sum(float(x) for x in rates) / len(rates)), 1)
    else:
        measured = sum(
            1
            for r in rows
            if (r.get("protection_measure") or "").strip()
            or (r.get("risk_status") or "").strip() in {"措施已落实", "正常", "无影响", "NORMAL"}
        )
        measure_rate = round(100.0 * measured / total) if total else 0
    risk_count = sum(1 for r in rows if _e04_is_risk_status(r.get("risk_status")))
    status = "正常" if risk_count == 0 else "关注"
    survey_raw = next((r.get("survey_status") for r in rows if r.get("survey_status")), "COMPLETED")
    survey_map = {
        "COMPLETED": "文物调查已完成",
        "IN_PROGRESS": "文物调查进行中",
        "PENDING": "文物调查待开展",
    }
    survey_status = survey_map.get(str(survey_raw).upper(), str(survey_raw) if survey_raw else "文物调查已完成")
    risk_status_raw = next((r.get("risk_status") for r in rows if r.get("risk_status")), "NORMAL")
    risk_cn = {
        "NORMAL": "正常",
        "LOW": "低",
        "MEDIUM": "关注",
        "HIGH": "较高",
        "CRITICAL": "严重",
    }
    risk_status = risk_cn.get(str(risk_status_raw).upper(), str(risk_status_raw) or status)
    return {
        "objectCount": total,
        "measureRate": measure_rate,
        "riskCount": risk_count,
        "status": status,
        "riskStatus": risk_status,
        "surveyStatus": survey_status,
    }


def _e04_cultural_rows() -> list[dict] | None:
    """Read cultural relic rows; None when table unavailable."""
    try:
        return query_all(
            """
            SELECT id, project_id, section_id, relic_code, relic_name, relic_type,
                   protection_level, location_desc, longitude, latitude,
                   protection_scope, construction_impact, protection_measure,
                   responsible_unit, risk_status, update_time,
                   survey_status, measure_rate
            FROM biz_cultural_relic_object
            WHERE CAST(project_id AS CHAR) IN (%s, %s, %s)
            ORDER BY id ASC
            """,
            ("LUOYI-ESG", "1001", "1001"),
        )
    except Exception:
        # Older table without survey_status / measure_rate
        try:
            return query_all(
                """
                SELECT id, project_id, section_id, relic_code, relic_name, relic_type,
                       protection_level, location_desc, longitude, latitude,
                       protection_scope, construction_impact, protection_measure,
                       responsible_unit, risk_status, update_time
                FROM biz_cultural_relic_object
                WHERE CAST(project_id AS CHAR) IN (%s, %s)
                ORDER BY id ASC
                """,
                ("LUOYI-ESG", "1001"),
            )
        except Exception as exc:
            logger.warning("E04 cultural relic table unavailable: %s", exc)
            return None


def _e04_is_risk_status(status: str | None) -> bool:
    text = (status or "").strip().upper()
    if not text:
        return False
    if text in {"正常", "措施已落实", "无影响", "已闭环", "NORMAL", "LOW"}:
        return False
    return True


def _e04_cultural_home_metrics() -> dict:
    rows = _e04_cultural_rows()
    if rows is None or len(rows) == 0:
        return dict(E04_CULTURAL_DEMO_FALLBACK)
    return _e04_cultural_summary_from_rows(rows)


def _e04_cultural_item(row: dict) -> dict:
    return {
        "id": int(row["id"]),
        "relicCode": row.get("relic_code") or "",
        "relicName": row.get("relic_name") or "",
        "relicType": row.get("relic_type") or "",
        "protectionLevel": row.get("protection_level") or "",
        "locationDesc": row.get("location_desc") or "",
        "riskStatus": row.get("risk_status") or "",
        "responsibleUnit": row.get("responsible_unit") or "",
        "updateTime": value_for_json(row.get("update_time")),
    }


def _e04_cultural_detail(row: dict) -> dict:
    item = _e04_cultural_item(row)
    measure = (row.get("protection_measure") or "").strip()
    material_status = "资料齐全（演示）" if measure else "待补充"
    return {
        **item,
        "projectId": row.get("project_id") or E04_CULTURAL_PROJECT_ID,
        "sectionId": int(row["section_id"]) if row.get("section_id") is not None else None,
        "longitude": value_for_json(row.get("longitude")),
        "latitude": value_for_json(row.get("latitude")),
        "protectionScope": row.get("protection_scope") or "",
        "constructionImpact": row.get("construction_impact") or "",
        "protectionMeasure": measure,
        "materialStatus": material_status,
    }


def get_e04_cultural_objects() -> dict:
    """E04 文物保护管控工作台：overview + objects 列表。"""
    rows = _e04_cultural_rows()
    if rows is None:
        # 表不可用：诚实空态（契约：调查完成 / 0 对象 / 风险正常），不编造对象
        return {
            "code": 0,
            "data": {
                "overview": dict(E04_CULTURAL_DEMO_FALLBACK),
                "objects": [],
                "isDemo": True,
                "source": "fallback-empty",
            },
        }
    if len(rows) == 0:
        return {
            "code": 0,
            "data": {
                "overview": dict(E04_CULTURAL_DEMO_FALLBACK),
                "objects": [],
                "isDemo": True,
                "source": "empty-table",
            },
        }
    overview = _e04_cultural_summary_from_rows(rows)
    return {
        "code": 0,
        "data": {
            "overview": overview,
            "objects": [_e04_cultural_item(r) for r in rows],
            "isDemo": True,
            "source": "biz_cultural_relic_object",
        },
    }


def get_e04_cultural_object_detail(object_id: int) -> dict | None:
    """E04 文物保护对象详情。"""
    rows = _e04_cultural_rows()
    if rows is None or len(rows) == 0:
        return None

    row = next((r for r in rows if int(r["id"]) == int(object_id)), None)
    if row is None:
        return None
    return {"code": 0, "data": _e04_cultural_detail(row)}


def get_e04_cultural_kpi_detail() -> dict:
    """首页不再打开碳排放弹窗；若仍请求 /kpi/E04，返回文物保护摘要（含契约四字段）。"""
    metrics = _e04_cultural_home_metrics()
    objects_payload = get_e04_cultural_objects()
    objects = (objects_payload.get("data") or {}).get("objects") or []
    overview = (objects_payload.get("data") or {}).get("overview") or {}
    survey_status = overview.get("surveyStatus") or "COMPLETED"
    risk_status = overview.get("riskStatus") or metrics.get("status") or "NORMAL"
    return {
        "key": "E04",
        "fullName": "文物保护管控",
        "name": "文物保护管控",
        "theme": "green",
        "value": metrics["objectCount"],
        "unit": "处",
        "objectCount": metrics["objectCount"],
        "surveyStatus": survey_status if survey_status in {"COMPLETED", "IN_PROGRESS", "PENDING"} else "COMPLETED",
        "measureRate": metrics["measureRate"],
        "riskStatus": risk_status if str(risk_status).upper() in {"NORMAL", "LOW", "MEDIUM", "HIGH", "CRITICAL"} else ("NORMAL" if risk_status in {"正常", "措施已落实", "无影响"} else "MEDIUM"),
        "summary": {
            "total": metrics["objectCount"],
            "objectCount": metrics["objectCount"],
            "surveyStatus": survey_status,
            "measureRate": metrics["measureRate"],
            "riskStatus": risk_status,
        },
        "summaryList": [
            {"label": "文物保护对象", "value": metrics["objectCount"], "unit": "处"},
            {"label": "文物调查状态", "value": overview.get("surveyStatus") or "文物调查已完成", "unit": ""},
            {"label": "保护措施落实率", "value": metrics["measureRate"], "unit": "%"},
            {"label": "风险状态", "value": overview.get("riskStatus") or metrics["status"], "unit": ""},
        ],
        "objects": objects,
        "chartTitle": "文物保护对象一览",
        "detailTitle": "文物保护对象",
        "detailColumns": [
            {"key": "relicName", "label": "名称", "width": "28%"},
            {"key": "locationDesc", "label": "位置", "width": "16%"},
            {"key": "relicType", "label": "类型", "width": "18%"},
            {"key": "riskStatus", "label": "状态", "width": "18%"},
            {"key": "responsibleUnit", "label": "责任单位", "width": "20%"},
        ],
        "detailData": objects,
        "dataSource": "文物保护对象表 biz_cultural_relic_object",
        "updateTime": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "updateFrequency": "演示更新",
        "completeness": "演示数据",
        "completenessStatus": "pending",
        "isMock": True,
        "isDemo": True,
        "scope": "demo",
    }


def _build_s03_home_hint() -> str:
    """Wage payment rate from salary_payment_record when available; else honest empty."""
    total = _safe_count("SELECT COUNT(*) AS c FROM salary_payment_record")
    if total is None or total == 0:
        return "工资发放达标率：暂无评价数据 · 实名覆盖率：暂无评价数据"
    paid = _safe_count(
        """
        SELECT COUNT(*) AS c FROM salary_payment_record
        WHERE payment_status IN ('已确认', '已发放', '已支付', '正常', '达标')
        """
    )
    if paid is None:
        return "工资发放达标率：暂无评价数据 · 实名覆盖率：暂无评价数据"
    rate = round(100.0 * paid / total)
    return f"工资发放达标率 {rate}% · 实名覆盖率：暂无评价数据"


def _build_s04_home_hint() -> str:
    """Complaint / petition counts + resolve rate from appeal_record."""
    total = _safe_count("SELECT COUNT(*) AS c FROM appeal_record")
    if total is None:
        return "投诉/信访：暂无有效数据"
    if total == 0:
        return "投诉 0 · 信访 0 · 化解率：暂无有效数据"
    complaint = _safe_count(
        """
        SELECT COUNT(*) AS c FROM appeal_record
        WHERE COALESCE(appeal_type, '') LIKE %s
           OR COALESCE(source_channel, '') LIKE %s
           OR COALESCE(source_channel, '') LIKE %s
        """,
        ("%投诉%", "%12345%", "%热线%"),
    ) or 0
    petition = _safe_count(
        """
        SELECT COUNT(*) AS c FROM appeal_record
        WHERE COALESCE(appeal_type, '') LIKE %s
           OR COALESCE(source_channel, '') LIKE %s
           OR COALESCE(source_channel, '') LIKE %s
        """,
        ("%信访%", "%信访%", "%来访%"),
    ) or 0
    closed = _safe_count("SELECT COUNT(*) AS c FROM appeal_record WHERE status = '已办结'")
    if closed is None or total == 0:
        rate_text = "暂无有效数据"
    else:
        rate_text = f"{round(100.0 * closed / total)}%"
    return f"投诉 {complaint} · 信访 {petition} · 化解率 {rate_text}"


def _build_g01_checklist_hint() -> str:
    """Status checklist for 环评/水保/施工许可 — no secret docs."""
    try:
        rows = query_all(
            """
            SELECT procedure_name, status, impact_node
            FROM compliance_procedure
            """
        )
    except Exception:
        return "环评批复：暂无评价数据 · 水保批复：暂无评价数据 · 施工许可：暂无评价数据"

    def mark(keywords: tuple[str, ...]) -> str:
        matched = [
            r for r in rows
            if any(k in (r.get("procedure_name") or "") or k in (r.get("impact_node") or "") for k in keywords)
        ]
        if not matched:
            return "—"
        if any((r.get("status") or "") == "已完成" for r in matched):
            return "√"
        return "…"

    eia = mark(("环评",))
    water = mark(("水保", "水土保持"))
    permit = mark(("施工许可", "专项施工"))
    return f"环评批复{eia} 水保批复{water} 施工许可{permit}"


def _build_g02_home_hint() -> str:
    """Open issues / rectifications / closure rate."""
    open_count = _safe_count("SELECT COUNT(*) AS c FROM rectification_record WHERE status <> '已关闭'")
    total = _safe_count("SELECT COUNT(*) AS c FROM rectification_record")
    closed = _safe_count("SELECT COUNT(*) AS c FROM rectification_record WHERE status = '已关闭'")
    if open_count is None or total is None:
        return "问题/整改：暂无有效数据"
    if total == 0:
        return "问题 0 · 整改 0 · 闭环率：暂无有效数据"
    rate = round(100.0 * (closed or 0) / total)
    return f"问题 {total} · 整改 {open_count} · 闭环率 {rate}%"


def get_dashboard_kpis() -> dict:
    # Demo V0.1 contract wins when esg_demo_indicator_result is published.
    try:
        import esg_demo_api

        demo = esg_demo_api.get_demo_dashboard_kpis()
        if demo and demo.get("items"):
            return demo
    except Exception as exc:
        logger.warning("esg_demo kpis skipped: %s", exc)

    rows = query_all(
        """
        SELECT indicator_code, group_code, label, full_name, value, unit, display_order
        FROM indicator_result
        ORDER BY group_code, display_order
        """
    )
    groups: dict[str, dict] = {key: {**meta, "items": []} for key, meta in GROUP_META.items()}
    for row in rows:
        is_e04 = row["indicator_code"] == "E04"
        groups[row["group_code"]]["items"].append(
            {
                "key": row["indicator_code"],
                "label": "文物保护管控" if is_e04 else row["label"],
                "fullName": "文物保护管控" if is_e04 else row["full_name"],
                "value": value_for_json(row["value"]),
                "unit": "处" if is_e04 else row["unit"],
            }
        )
    e01_row = query_one(
        """
        SELECT COUNT(*) AS total
        FROM e01_factor_result r
        JOIN e01_monitor_sample s ON s.id = r.sample_id
        WHERE s.sampled_at >= %s
          AND r.test_stage = 'INITIAL'
          AND r.judgement = 'EXCEEDED'
          AND r.result_validity = 'VALID'
          AND r.effective_status = 'EFFECTIVE'
          AND r.data_nature <> 'background'
          AND s.data_nature <> 'background'
        """,
        (E01_CONSTRUCTION_START,),
    )
    e02_formal_row = query_one(
        """
        SELECT COUNT(*) AS c FROM env_issue_record
        WHERE issue_status NOT IN ('已闭环','已撤销','已合并')
          AND is_demo = 0 AND data_nature = 'formal'
        """
    )
    e02_demo_row = query_one(
        """
        SELECT COUNT(*) AS c FROM env_issue_record
        WHERE issue_status NOT IN ('已闭环','已撤销','已合并')
          AND is_demo = 1 AND data_nature = 'demo'
        """
    ) if E02_ALLOW_DEMO else None
    e03_formal_row = query_one(
        f"""
        SELECT COUNT(*) AS c FROM water_protection_issue
        WHERE issue_status NOT IN ('已闭环','已撤销','已合并')
          AND is_demo = 0 AND data_nature = 'formal'
          AND effective_status = 'EFFECTIVE'
          AND (
            COALESCE(issue_type, '') REGEXP '{E03_ECO_TYPE_REGEX}'
            OR COALESCE(issue_name, '') REGEXP '{E03_ECO_TYPE_REGEX}'
          )
        """
    )
    e03_demo_row = query_one(
        f"""
        SELECT COUNT(*) AS c FROM water_protection_issue
        WHERE issue_status NOT IN ('已闭环','已撤销','已合并')
          AND is_demo = 1 AND data_nature = 'demo'
          AND effective_status = 'EFFECTIVE'
          AND (
            COALESCE(issue_type, '') REGEXP '{E03_ECO_TYPE_REGEX}'
            OR COALESCE(issue_name, '') REGEXP '{E03_ECO_TYPE_REGEX}'
          )
        """
    ) if E03_ALLOW_DEMO else None
    e03_all_formal_row = query_one(
        """
        SELECT COUNT(*) AS c FROM water_protection_issue
        WHERE issue_status NOT IN ('已闭环','已撤销','已合并')
          AND is_demo = 0 AND data_nature = 'formal'
          AND effective_status = 'EFFECTIVE'
        """
    )
    e03_all_demo_row = query_one(
        """
        SELECT COUNT(*) AS c FROM water_protection_issue
        WHERE issue_status NOT IN ('已闭环','已撤销','已合并')
          AND is_demo = 1 AND data_nature = 'demo'
          AND effective_status = 'EFFECTIVE'
        """
    ) if E03_ALLOW_DEMO else None
    # E04 首页：文物保护管控汇总（碳排放仍由低碳增益专题 / get_e04_carbon_emission_detail 提供）
    e04_cultural = _e04_cultural_home_metrics()
    s02_row = query_one(
        """
        SELECT COUNT(*) AS c
        FROM safety_risk_point
        WHERE risk_level IN ('重大', '较大') AND control_status <> '已销号'
        """
    )
    s03_formal_row = query_one(
        """
        SELECT COUNT(*) AS c FROM labor_dispute_record
        WHERE status <> '已办结'
          AND COALESCE(is_demo, 0) = 0
          AND COALESCE(data_nature, 'formal') = 'formal'
        """
    )
    s03_demo_row = query_one(
        """
        SELECT COUNT(*) AS c FROM labor_dispute_record
        WHERE status <> '已办结'
          AND is_demo = 1 AND data_nature = 'demo'
        """
    ) if S03_ALLOW_DEMO else None
    s04_row = query_one("SELECT COUNT(*) AS c FROM appeal_record WHERE status <> '已办结'")
    s01_detail = _resolve_s01_snapshot()
    g01_row = query_one("SELECT COUNT(*) AS c FROM compliance_procedure WHERE status <> '已完成'")
    g02_permit_row = query_one("SELECT COUNT(*) AS c FROM permit_record WHERE status IN ('临期', '逾期')")
    g02_rect_row = query_one("SELECT COUNT(*) AS c FROM rectification_record WHERE status <> '已关闭'")
    g04_gap_row = query_one("SELECT COUNT(*) AS c FROM compliance_material_gap WHERE status <> '已补齐'")
    e02_formal_count = int(e02_formal_row["c"]) if e02_formal_row and e02_formal_row["c"] is not None else 0
    e02_demo_count = int(e02_demo_row["c"]) if e02_demo_row and e02_demo_row["c"] is not None else 0
    e03_all_formal = int(e03_all_formal_row["c"]) if e03_all_formal_row and e03_all_formal_row["c"] is not None else 0
    e03_all_demo = int(e03_all_demo_row["c"]) if e03_all_demo_row and e03_all_demo_row["c"] is not None else 0
    # E02 升级：未闭环环保 + 未闭环水保
    e02_formal_combined = e02_formal_count + e03_all_formal
    e02_demo_combined = e02_demo_count + e03_all_demo
    e02_display_value = e02_demo_combined if E02_ALLOW_DEMO else e02_formal_combined
    e03_formal_count = int(e03_formal_row["c"]) if e03_formal_row and e03_formal_row["c"] is not None else 0
    e03_demo_count = int(e03_demo_row["c"]) if e03_demo_row and e03_demo_row["c"] is not None else 0
    e03_display_value = e03_demo_count if E03_ALLOW_DEMO else e03_formal_count
    g02_rect_count = int(g02_rect_row["c"]) if g02_rect_row and g02_rect_row["c"] is not None else 0
    g02_permit_count = int(g02_permit_row["c"]) if g02_permit_row and g02_permit_row["c"] is not None else 0
    g04_gap_count = int(g04_gap_row["c"]) if g04_gap_row and g04_gap_row["c"] is not None else 0
    g04_combined = g02_permit_count + g04_gap_count
    dynamic_values = {
        "E01": {"value": round(float(e01_row["total"])) if e01_row and e01_row["total"] is not None else None, "unit": "项"},
        "E02": {
            "value": e02_display_value if e02_display_value > 0 else 0,
            "unit": "项",
            "dataNature": "demo" if E02_ALLOW_DEMO else "formal",
            "isDemo": bool(E02_ALLOW_DEMO and e02_demo_combined > 0),
            "scope": "demo" if E02_ALLOW_DEMO else "formal",
            "formalCount": e02_formal_combined,
            "demoCount": e02_demo_combined,
            "envFormalCount": e02_formal_count,
            "waterFormalCount": e03_all_formal,
        },
        "E03": {
            "value": e03_display_value if e03_display_value > 0 else 0,
            "unit": "项",
            "dataNature": "demo" if E03_ALLOW_DEMO else "formal",
            "isDemo": bool(E03_ALLOW_DEMO and e03_demo_count > 0),
            "scope": "demo" if E03_ALLOW_DEMO else "formal",
            "formalCount": e03_formal_count,
            "demoCount": e03_demo_count,
        },
        "E04": {
            "value": e04_cultural["objectCount"],
            "unit": "处",
            "hint": f"措施落实率 {e04_cultural['measureRate']}% · 风险 {e04_cultural['riskCount']}项 · {e04_cultural['status']}",
            "scope": "demo",
            "isDemo": True,
            "dataNature": "demo",
            "objectCount": e04_cultural["objectCount"],
            "measureRate": e04_cultural["measureRate"],
            "riskCount": e04_cultural["riskCount"],
            "statusText": e04_cultural["status"],
        },
        "S01": {
            "value": int(s01_detail["continuousDays"]) if s01_detail and s01_detail.get("continuousDays") is not None else None,
            "unit": "天",
            "dataNature": s01_detail.get("dataNature"),
            "isDemo": s01_detail.get("isDemo"),
            "scope": s01_detail.get("scope"),
            "statisticsAsOf": s01_detail.get("statisticsAsOf"),
            "confirmationStatus": s01_detail.get("confirmationStatus"),
        },
        "S02": {"value": int(s02_row["c"]) if s02_row and s02_row["c"] is not None else None, "unit": "项"},
        "S03": {
            "value": (
                int(s03_demo_row["c"]) if S03_ALLOW_DEMO and s03_demo_row and s03_demo_row["c"] is not None
                else (int(s03_formal_row["c"]) if s03_formal_row and s03_formal_row["c"] is not None else 0)
            ),
            "unit": "项",
            "dataNature": "demo" if S03_ALLOW_DEMO else "formal",
            "isDemo": bool(S03_ALLOW_DEMO and s03_demo_row and int(s03_demo_row["c"] or 0) > 0),
            "scope": "demo" if S03_ALLOW_DEMO else "formal",
            "formalCount": int(s03_formal_row["c"]) if s03_formal_row and s03_formal_row["c"] is not None else 0,
            "demoCount": int(s03_demo_row["c"]) if s03_demo_row and s03_demo_row["c"] is not None else 0,
            "hint": _build_s03_home_hint(),
        },
        "S04": {"value": int(s04_row["c"]) if s04_row and s04_row["c"] is not None else None, "unit": "项", "hint": _build_s04_home_hint()},
        "G01": {"value": int(g01_row["c"]) if g01_row and g01_row["c"] is not None else None, "unit": "项", "hint": _build_g01_checklist_hint()},
        # G02 = 合规问题闭环 ← 整改台账
        "G02": {"value": g02_rect_count, "unit": "项", "hint": _build_g02_home_hint()},
        # G03 = 履约评价：台账未建，不编造；首页展示「待评价」而非无意义 0家
        "G03": {
            "value": 0,
            "unit": "",
            "displayText": "待评价",
            "ledgerStatus": "pending",
            "hint": "暂无评价数据",
        },
        # G04 = 治理内控风险 ← 许可临期逾期 + 资料缺口
        "G04": {
            "value": g04_combined,
            "unit": "项",
            "permitCount": g02_permit_count,
            "materialGapCount": g04_gap_count,
        },
    }
    for group in groups.values():
        for item in group["items"]:
            code = item["key"]
            label_meta = KPI_HOME_LABELS.get(code)
            if label_meta:
                item["label"] = label_meta["label"]
                item["fullName"] = label_meta["fullName"]
            dynamic = dynamic_values.get(code)
            if dynamic and dynamic.get("value") is not None:
                item["value"] = dynamic["value"]
                item["unit"] = dynamic.get("unit") if "unit" in dynamic else ((label_meta or {}).get("unit") or item.get("unit"))
                for extra_key in ("dataNature", "isDemo", "scope", "formalCount", "demoCount",
                                  "formalValue", "demoValue", "boundaryVersion", "accountingBatchId",
                                  "statisticsAsOf", "statisticsStart", "diffHint", "confirmationStatus",
                                  "ledgerStatus", "permitCount", "materialGapCount",
                                  "envFormalCount", "waterFormalCount",
                                  "displayText", "hint"):
                    if extra_key in dynamic:
                        item[extra_key] = dynamic[extra_key]
            elif dynamic and dynamic.get("displayText"):
                # G03 等：允许仅下发 displayText（即使 value 为 0 已在上面分支处理）
                for extra_key in ("displayText", "hint", "ledgerStatus", "unit"):
                    if extra_key in dynamic:
                        item[extra_key] = dynamic[extra_key]
    return {"groups": [groups["E"], groups["S"], groups["G"]]}


def get_dashboard_kpi_detail_snapshot(indicator_code: str) -> dict | None:
    row = query_one(
        """
        SELECT detail_json
        FROM dashboard_kpi_detail_snapshot
        WHERE indicator_code = %s
        """,
        (indicator_code,),
    )
    if row is None:
        return None
    detail = json_column(row["detail_json"])
    detail["isMock"] = False
    return detail


def with_snapshot_base(indicator_code: str) -> dict:
    return get_dashboard_kpi_detail_snapshot(indicator_code) or {
        "key": indicator_code,
        "fullName": indicator_code,
        "theme": "purple",
        "summary": [],
        "chartTitle": "趋势与构成",
        "detailTitle": "明细列表",
        "detailColumns": [],
        "detailData": [],
        "dataSource": "MySQL 业务明细表",
        "updateTime": "2026-07-13 10:30",
        "isMock": False,
    }


def get_g01_compliance_procedure_detail() -> dict | None:
    rows = query_all(
        """
        SELECT *
        FROM compliance_procedure
        WHERE status <> '已完成'
        ORDER BY overdue DESC, deadline, id
        """
    )
    if not rows:
        return None

    new_count = query_one(
        """
        SELECT COUNT(*) AS c
        FROM compliance_procedure
        WHERE status <> '已完成'
          AND created_at >= '2026-07-01'
          AND created_at < '2026-08-01'
        """
    )["c"]
    completed_count = query_one(
        """
        SELECT COUNT(*) AS c
        FROM compliance_procedure
        WHERE completed_date >= '2026-07-01'
          AND completed_date < '2026-08-01'
        """
    )["c"]
    overdue_count = sum(1 for row in rows if int(row.get("overdue") or 0) == 1)
    expected_this_month = query_one(
        """
        SELECT COUNT(*) AS c
        FROM compliance_procedure
        WHERE status IN ('待评审', '待批复')
          AND expected_complete_date >= '2026-07-01'
          AND expected_complete_date < '2026-08-01'
        """
    )["c"]
    g01_hint = _build_g01_checklist_hint()

    detail = with_snapshot_base("G01")
    detail.update(
        {
            "summary": [
                {"label": "未完成事项", "value": len(rows), "unit": "项"},
                {"label": "本月新增", "value": int(new_count), "unit": "项"},
                {"label": "本月完成", "value": int(completed_count), "unit": "项"},
                {"label": "逾期未办", "value": overdue_count, "unit": "项"},
                {"label": "关键手续清单", "value": g01_hint, "unit": ""},
            ],
            "checklistHint": g01_hint,
            "homeHint": g01_hint,
            "detailData": [
                {
                    "name": row["procedure_name"],
                    "type": row.get("procedure_type") or "行政许可",
                    "status": row["status"],
                    "deadline": value_for_json(row.get("deadline")),
                    "department": row.get("responsible_department") or "",
                    "progress": f"{row.get('progress_percent') or 0}%",
                }
                for row in rows
            ],
            "dataSource": "法定报批报建台账",
            "updateTime": "2026-07-13 08:00",
            "isMock": False,
        }
    )
    return detail


def get_project_sections(section_code: str | None = None) -> dict:
    where = "WHERE ps.active_status = 'ACTIVE'"
    params: list[Any] = []
    if section_code:
        where += " AND ps.section_code = %s"
        params.append(section_code)
    rows = query_all(
        f"""
        SELECT ps.*,
               COUNT(DISTINCT eo.id) AS engineering_object_count,
               COUNT(DISTINCT mpor.point_id) AS monitor_point_count
        FROM project_section ps
        LEFT JOIN project_engineering_object eo ON eo.section_id = ps.id
        LEFT JOIN monitor_point_object_relation mpor ON mpor.section_id = ps.id
        {where}
        GROUP BY ps.id
        ORDER BY ps.start_km, ps.section_code
        """,
        tuple(params),
    )
    data = [
        {
            "id": row["id"], "code": row["section_code"], "name": row["section_name"],
            "chainageStart": row["chainage_start"], "chainageEnd": row["chainage_end"],
            "engineeringObjectCount": int(row["engineering_object_count"]),
            "monitorPointCount": int(row["monitor_point_count"]),
        }
        for row in rows
    ]
    return {"code": 0, "data": data, "meta": {"total": len(data)}}


def get_project_phases(at_time: str | None = None) -> dict:
    at_time = at_time or datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    rows = query_all(
        """
        SELECT ph.*,
               COUNT(DISTINCT eop.object_id) AS engineering_object_count
        FROM project_phase_period ph
        LEFT JOIN engineering_object_phase eop ON eop.phase_id = ph.id
        WHERE ph.project_id = 'LUOYI-ESG'
        GROUP BY ph.id
        ORDER BY ph.start_at
        """
    )
    data = [
        {
            "id": row["id"], "code": row["phase_code"], "name": row["phase_name"],
            "type": row["phase_type"], "startAt": value_for_json(row["start_at"]),
            "endAt": value_for_json(row["end_at"]), "status": row["phase_status"],
            "isCurrent": value_for_json(row["start_at"]) <= at_time <= value_for_json(row["end_at"]),
            "engineeringObjectCount": int(row["engineering_object_count"]),
        }
        for row in rows
    ]
    return {"code": 0, "data": data, "meta": {"total": len(data), "atTime": at_time}}


def get_project_engineering_objects(
    section_code: str | None = None,
    object_type: str | None = None,
    at_time: str | None = None,
) -> dict:
    at_time = at_time or datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    clauses = ["eo.active_status = 'ACTIVE'"]
    params: list[Any] = [at_time, at_time]
    if section_code:
        clauses.append("ps.section_code = %s")
        params.append(section_code)
    if object_type:
        clauses.append("eo.object_type = %s")
        params.append(object_type)
    rows = query_all(
        f"""
        SELECT eo.*, ps.section_code, ps.section_name,
               ph.phase_code, ph.phase_name,
               eop.process_code, eop.process_name,
               COUNT(DISTINCT mpor.point_id) AS monitor_point_count,
               COUNT(DISTINCT s.id) AS sample_count,
               COUNT(DISTINCT CASE WHEN c.current_status <> 'CLOSED' THEN ev.id END) AS open_event_count
        FROM project_engineering_object eo
        JOIN project_section ps ON ps.id = eo.section_id
        LEFT JOIN engineering_object_phase eop
          ON eop.object_id = eo.id
         AND %s BETWEEN eop.process_start_at AND eop.process_end_at
        LEFT JOIN project_phase_period ph ON ph.id = eop.phase_id
        LEFT JOIN monitor_point_object_relation mpor
          ON mpor.object_id = eo.id
         AND %s >= mpor.valid_from
         AND (mpor.valid_to IS NULL OR %s <= mpor.valid_to)
        LEFT JOIN e01_monitor_sample s
          ON s.point_id = mpor.point_id AND s.sampled_at >= '{E01_CONSTRUCTION_START}'
        LEFT JOIN e01_factor_result fr
          ON fr.sample_id = s.id AND fr.test_stage = 'INITIAL' AND fr.judgement = 'EXCEEDED'
        LEFT JOIN e01_exceed_event ev ON ev.original_result_id = fr.id
        LEFT JOIN e_closure_case c ON c.id = ev.case_id
        WHERE {' AND '.join(clauses)}
        GROUP BY eo.id, ps.id, ph.id, eop.id
        ORDER BY ps.start_km, eo.chainage_start, eo.object_code
        """,
        tuple([at_time] + params),
    )
    data = []
    for row in rows:
        point_count = int(row["monitor_point_count"])
        sample_count = int(row["sample_count"])
        state = "UNASSIGNED" if point_count == 0 else ("UNMONITORED" if sample_count == 0 else ("EXCEEDED" if int(row["open_event_count"]) else "NORMAL"))
        data.append(
            {
                "id": row["id"], "code": row["object_code"], "name": row["object_name"],
                "type": row["object_type"], "sectionCode": row["section_code"],
                "sectionName": row["section_name"], "chainageStart": row["chainage_start"],
                "chainageEnd": row["chainage_end"], "longitude": value_for_json(row["longitude"]),
                "latitude": value_for_json(row["latitude"]), "gisFeatureId": row.get("gis_feature_id"),
                "phaseCode": row.get("phase_code"), "phaseName": row.get("phase_name"),
                "processCode": row.get("process_code"), "processName": row.get("process_name"),
                "monitorPointCount": point_count, "monitoringState": state,
            }
        )
    return {"code": 0, "data": data, "meta": {"total": len(data), "atTime": at_time}}


def get_environment_monitor_point_history(point_id: int, limit: int = 20) -> dict:
    limit = max(1, min(int(limit), 100))
    rows = query_all(
        f"""
        SELECT s.id AS sample_id, s.sample_code, s.monitor_category, s.sampled_at,
               b.batch_code, b.report_no, b.report_issued_at,
               fr.id AS result_id, fr.result_code, fr.test_stage, fr.judgement,
               fr.detected_value_raw, fr.limit_value_raw, fr.reported_unit,
               fd.factor_code, fd.factor_name,
               ev.event_code, ev.latest_retest_outcome,
               c.case_code, c.current_status, c.closed_at
        FROM e01_monitor_sample s
        JOIN e01_monitor_batch b ON b.id = s.batch_id
        JOIN e01_factor_result fr ON fr.sample_id = s.id
        JOIN e01_factor_definition fd ON fd.id = fr.factor_id
        LEFT JOIN e01_exceed_event ev ON ev.original_result_id = fr.id
        LEFT JOIN e_closure_case c ON c.id = ev.case_id
        WHERE s.point_id = %s
          AND s.sampled_at >= %s
          AND s.data_nature <> 'background'
          AND fr.data_nature <> 'background'
        ORDER BY s.sampled_at DESC, fr.id
        LIMIT {limit}
        """,
        (point_id, E01_CONSTRUCTION_START),
    )
    data = [
        {
            "sampleId": row["sample_id"], "sampleCode": row["sample_code"],
            "sampledAt": value_for_json(row["sampled_at"]), "category": row["monitor_category"],
            "batchCode": row["batch_code"], "reportNo": row["report_no"],
            "reportIssuedAt": value_for_json(row["report_issued_at"]),
            "resultId": row["result_id"], "resultCode": row["result_code"],
            "testStage": row["test_stage"], "factorCode": row["factor_code"],
            "factorName": row["factor_name"], "detectedValue": row["detected_value_raw"],
            "limitValue": row["limit_value_raw"], "unit": row["reported_unit"],
            "judgement": row["judgement"], "eventCode": row.get("event_code"),
            "caseCode": row.get("case_code"), "closureStatus": row.get("current_status"),
            "closedAt": value_for_json(row.get("closed_at")) if row.get("closed_at") else None,
        }
        for row in rows
    ]
    return {"code": 0, "data": data, "meta": {"pointId": point_id, "total": len(data), "statisticsStart": "2026-05-08"}}


def get_environment_monitor_points(
    section_code: str | None = None,
    monitor_category: str | None = None,
    at_time: str | None = None,
) -> dict:
    at_time = at_time or datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    clauses = ["p.active_status = 'ACTIVE'", "p.effective_from >= %s"]
    params: list[Any] = [at_time, at_time, E01_CONSTRUCTION_START]
    if section_code:
        clauses.append("ps.section_code = %s")
        params.append(section_code)
    if monitor_category:
        clauses.append("pi.monitor_category = %s")
        params.append(monitor_category.upper())
    rows = query_all(
        f"""
        SELECT p.*, ps.section_code, ps.section_name,
               eo.object_code, eo.object_name, eo.object_type,
               ph.phase_code, ph.phase_name, eop.process_code, eop.process_name,
               GROUP_CONCAT(DISTINCT pi.monitor_category ORDER BY pi.monitor_category) AS monitor_categories,
               GROUP_CONCAT(DISTINCT pl.frequency_code ORDER BY pl.frequency_code) AS frequency_codes,
               COUNT(DISTINCT s.id) AS sample_count,
               COUNT(DISTINCT CASE WHEN c.current_status <> 'CLOSED' THEN ev.id END) AS open_event_count
        FROM e01_monitor_point p
        LEFT JOIN monitor_point_object_relation mpor
          ON mpor.point_id = p.id
         AND %s >= mpor.valid_from
         AND (mpor.valid_to IS NULL OR %s <= mpor.valid_to)
        LEFT JOIN project_section ps ON ps.id = mpor.section_id
        LEFT JOIN project_engineering_object eo ON eo.id = mpor.object_id
        LEFT JOIN project_phase_period ph ON ph.id = mpor.phase_id
        LEFT JOIN engineering_object_phase eop ON eop.id = mpor.object_phase_id
        LEFT JOIN e01_monitor_plan_item pi ON pi.point_id = p.id
        LEFT JOIN e01_monitor_plan pl ON pl.id = pi.plan_id
        LEFT JOIN e01_monitor_sample s ON s.point_id = p.id AND s.sampled_at >= '{E01_CONSTRUCTION_START}'
        LEFT JOIN e01_factor_result fr
          ON fr.sample_id = s.id AND fr.test_stage = 'INITIAL' AND fr.judgement = 'EXCEEDED'
        LEFT JOIN e01_exceed_event ev ON ev.original_result_id = fr.id
        LEFT JOIN e_closure_case c ON c.id = ev.case_id
        WHERE {' AND '.join(clauses)}
        GROUP BY p.id, ps.id, eo.id, ph.id, eop.id
        ORDER BY ps.start_km, p.chainage, p.point_code
        """,
        tuple(params),
    )
    data = []
    for row in rows:
        sample_count = int(row["sample_count"])
        state = "UNMONITORED" if sample_count == 0 else ("EXCEEDED" if int(row["open_event_count"]) else "NORMAL")
        data.append(
            {
                "id": row["id"], "code": row["point_code"], "name": row["point_name"],
                "chainage": row["chainage"], "longitude": value_for_json(row["longitude"]),
                "latitude": value_for_json(row["latitude"]), "gisFeatureId": row.get("gis_feature_id"),
                "enabledAt": value_for_json(row["effective_from"]),
                "sectionCode": row.get("section_code") or row.get("segment_code"),
                "sectionName": row.get("section_name") or row.get("segment_name"),
                "engineeringObjectCode": row.get("object_code"), "engineeringObjectName": row.get("object_name"),
                "engineeringObjectType": row.get("object_type") or row.get("engineering_object_type"),
                "phaseCode": row.get("phase_code"), "phaseName": row.get("phase_name"),
                "processCode": row.get("process_code"), "processName": row.get("process_name"),
                "monitorCategories": (row.get("monitor_categories") or "").split(",") if row.get("monitor_categories") else [],
                "frequencyCodes": (row.get("frequency_codes") or "").split(",") if row.get("frequency_codes") else [],
                "sampleCount": sample_count, "monitoringState": state,
            }
        )
    return {"code": 0, "data": data, "meta": {"total": len(data), "atTime": at_time, "statisticsStart": "2026-05-08"}}


def get_environment_monitor_point(point_id: int, at_time: str | None = None) -> dict | None:
    points = get_environment_monitor_points(at_time=at_time)["data"]
    point = next((item for item in points if int(item["id"]) == int(point_id)), None)
    if point is None:
        return None
    history = get_environment_monitor_point_history(point_id, 20)
    point["history"] = history["data"]
    point["latestResults"] = history["data"][:6]
    return {"code": 0, "data": point, "meta": {"statisticsStart": "2026-05-08"}}


def get_e01_env_monitoring_detail() -> dict | None:
    rows = query_all(
        """
        SELECT r.id, r.result_code, s.monitor_category, s.sampled_at,
               p.id AS point_id, p.point_code, p.point_name, p.chainage,
               p.longitude, p.latitude, p.gis_feature_id,
               fd.factor_code, fd.factor_name, r.detected_value_raw,
               r.limit_value_raw, r.reported_unit,
               ps.section_code, ps.section_name,
               eo.object_code, eo.object_name,
               ph.phase_code, ph.phase_name,
               eop.process_code, eop.process_name,
               ev.id AS event_id, ev.event_code, ev.latest_retest_outcome,
               c.case_code, c.current_status, c.closed_at,
               rr.detected_value_raw AS retest_value,
               rr.reported_unit AS retest_unit,
               rs.sampled_at AS retest_at
        FROM e01_factor_result r
        JOIN e01_monitor_sample s ON s.id = r.sample_id
        JOIN e01_monitor_point p ON p.id = s.point_id
        JOIN e01_factor_definition fd ON fd.id = r.factor_id
        LEFT JOIN monitor_point_object_relation mpor
          ON mpor.point_id = p.id
         AND s.sampled_at >= mpor.valid_from
         AND (mpor.valid_to IS NULL OR s.sampled_at <= mpor.valid_to)
        LEFT JOIN project_section ps ON ps.id = mpor.section_id
        LEFT JOIN project_engineering_object eo ON eo.id = mpor.object_id
        LEFT JOIN project_phase_period ph ON ph.id = mpor.phase_id
        LEFT JOIN engineering_object_phase eop ON eop.id = mpor.object_phase_id
        LEFT JOIN e01_exceed_event ev ON ev.original_result_id = r.id
        LEFT JOIN e_closure_case c ON c.id = ev.case_id
        LEFT JOIN e01_retest_result_link rlink ON rlink.original_result_id = r.id
        LEFT JOIN e01_factor_result rr ON rr.id = rlink.factor_result_id
        LEFT JOIN e01_monitor_sample rs ON rs.id = rr.sample_id
        WHERE s.sampled_at >= %s
          AND r.test_stage = 'INITIAL'
          AND r.judgement = 'EXCEEDED'
          AND r.result_validity = 'VALID'
          AND r.effective_status = 'EFFECTIVE'
          AND r.data_nature <> 'background'
          AND s.data_nature <> 'background'
        ORDER BY s.sampled_at, r.id
        """,
        (E01_CONSTRUCTION_START,),
    )
    if not rows:
        return None

    trend_rows = query_all(
        """
        SELECT DATE_FORMAT(s.sampled_at, '%%Y-%%m') AS period,
               s.monitor_category AS category,
               COUNT(*) AS exceed_count
        FROM e01_factor_result r
        JOIN e01_monitor_sample s ON s.id = r.sample_id
        WHERE s.sampled_at >= %s
          AND r.test_stage = 'INITIAL'
          AND r.judgement = 'EXCEEDED'
          AND r.result_validity = 'VALID'
          AND r.effective_status = 'EFFECTIVE'
          AND r.data_nature <> 'background'
          AND s.data_nature <> 'background'
        GROUP BY DATE_FORMAT(s.sampled_at, '%%Y-%%m'), s.monitor_category
        ORDER BY period, category
        """,
        (E01_CONSTRUCTION_START,),
    )
    current_count = len(rows)
    rechecked_count = sum(1 for row in rows if row.get("retest_value") is not None)
    pending_count = sum(1 for row in rows if row.get("retest_value") is None)
    still_exceeded_count = sum(1 for row in rows if row.get("latest_retest_outcome") == "EXCEEDED")
    point_count = len({row["point_id"] for row in rows})
    category_labels = {"AIR": "环境空气/扬尘", "NOISE": "施工噪声", "WATER": "水环境"}

    def ratio(row: dict) -> float | str:
        try:
            limit_value = float(row.get("limit_value_raw"))
            return round(float(row.get("detected_value_raw")) / limit_value, 2) if limit_value else "—"
        except (TypeError, ValueError):
            return "—"

    def status(row: dict) -> str:
        if row.get("current_status") == "CLOSED":
            return "已闭环"
        if row.get("latest_retest_outcome") == "COMPLIANT":
            return "复测达标"
        if row.get("latest_retest_outcome") == "EXCEEDED":
            return "复测仍超标"
        return "整改中/待复测"

    detail = with_snapshot_base("E01")
    detail.update(
        {
            "fullName": "环境监测超标项次",
            "summary": [
                {"label": "施工期超标项次", "value": current_count, "unit": "项次"},
                {"label": "已完成复测", "value": rechecked_count, "unit": "项次"},
                {"label": "待复测", "value": pending_count, "unit": "项次"},
                {"label": "复测仍超标", "value": still_exceeded_count, "unit": "项次"},
                {"label": "涉及监测点", "value": point_count, "unit": "个"},
            ],
            "detailColumns": [
                {"key": "point", "label": "监测点", "width": "21%"},
                {"key": "time", "label": "监测时间", "width": "11%"},
                {"key": "factor", "label": "类别/因子", "width": "16%"},
                {"key": "initialValue", "label": "初检值", "width": "11%"},
                {"key": "recheckValue", "label": "复测值", "width": "13%"},
                {"key": "limit", "label": "标准限值", "width": "12%"},
                {"key": "multiple", "label": "超标倍数", "width": "8%"},
                {"key": "status", "label": "复测状态", "width": "8%"},
            ],
            "categoryData": [
                {"name": category_labels.get(category, category), "value": sum(1 for row in rows if row["monitor_category"] == category)}
                for category in sorted({row["monitor_category"] for row in rows})
            ] + [
                {"name": "合计", "value": current_count},
            ],
            "trendData": [
                {
                    "period": row["period"],
                    "category": category_labels.get(row["category"], row["category"]),
                    "value": int(row["exceed_count"]),
                }
                for row in trend_rows
            ],
            "detailData": [
                {
                    "id": row["result_code"],
                    "sourceId": row["result_code"],
                    "sourceTable": "e01_factor_result",
                    "rawId": row["id"],
                    "gisFeatureId": row.get("gis_feature_id"),
                    "category": category_labels.get(row["monitor_category"], row["monitor_category"]),
                    "point": row["point_name"],
                    "pointCode": row["point_code"],
                    "pointId": row["point_id"],
                    "section": row.get("section_name") or row.get("section_code"),
                    "sectionCode": row.get("section_code"),
                    "engineeringObject": row.get("object_name"),
                    "engineeringObjectCode": row.get("object_code"),
                    "phase": row.get("phase_name"),
                    "process": row.get("process_name"),
                    "chainage": row.get("chainage"),
                    "longitude": value_for_json(row.get("longitude")),
                    "latitude": value_for_json(row.get("latitude")),
                    "time": value_for_json(row["sampled_at"]),
                    "factor": row["factor_name"],
                    "factorCode": row["factor_code"],
                    "initialValue": f"{row['detected_value_raw']} {row.get('reported_unit') or ''}".strip(),
                    "recheckValue": (f"{row['retest_value']} {row.get('retest_unit') or row.get('reported_unit') or ''}".strip()
                                     if row.get("retest_value") is not None else "—"),
                    "recheckTime": value_for_json(row.get("retest_at")) if row.get("retest_at") else None,
                    "limit": f"{row['limit_value_raw']} {row.get('reported_unit') or ''}".strip(),
                    "multiple": ratio(row),
                    "status": status(row),
                    "eventCode": row.get("event_code"),
                    "caseCode": row.get("case_code"),
                }
                for row in rows
            ],
            "statisticsStart": "2026-05-08",
            "dataSource": "MySQL E01逐因子结果与闭环链",
            "updateTime": value_for_json(max(row["sampled_at"] for row in rows)),
            "isMock": False,
        }
    )
    return detail


E01_CATEGORY_LABELS = {"AIR": "环境空气", "NOISE": "噪声", "WATER": "水质"}
E01_CASE_STATUS_LABELS = {
    "DISCOVERED": "已发现",
    "PENDING_RECTIFICATION": "待整改",
    "RECTIFYING": "整改中",
    "PENDING_REVIEW": "待复核",
    "PENDING_CLOSURE": "待销项",
    "CLOSED": "已闭环",
    "CANCELLED": "已取消",
    "MERGED": "已合并",
    "SUSPENDED": "已挂起",
}
E01_NEXT_NODE = {
    "DISCOVERED": "转入待整改",
    "PENDING_RECTIFICATION": "启动整改",
    "RECTIFYING": "提交复测",
    "PENDING_REVIEW": "复核确认",
    "PENDING_CLOSURE": "销项关闭",
    "CLOSED": None,
    "CANCELLED": None,
    "MERGED": None,
    "SUSPENDED": "恢复处置",
}


def _e01_ratio(detected: Any, limit: Any) -> float | None:
    try:
        limit_value = float(limit)
        if not limit_value:
            return None
        return round(float(detected) / limit_value, 2)
    except (TypeError, ValueError):
        return None


def _e01_status_label(case_status: str | None, retest_outcome: str | None) -> str:
    if case_status == "CLOSED":
        return "已闭环"
    if retest_outcome == "COMPLIANT":
        return "复测达标"
    if retest_outcome in {"EXCEEDED", "STILL_EXCEEDED"}:
        return "复测仍超标"
    if case_status:
        return E01_CASE_STATUS_LABELS.get(case_status, case_status)
    return "整改中/待复测"


def _e01_exceed_item_count() -> int:
    row = query_one(
        """
        SELECT COUNT(*) AS total
        FROM e01_factor_result r
        JOIN e01_monitor_sample s ON s.id = r.sample_id
        WHERE s.sampled_at >= %s
          AND r.test_stage = 'INITIAL'
          AND r.judgement = 'EXCEEDED'
          AND r.result_validity = 'VALID'
          AND r.effective_status = 'EFFECTIVE'
          AND r.data_nature <> 'background'
          AND s.data_nature <> 'background'
        """,
        (E01_CONSTRUCTION_START,),
    )
    return int(row["total"]) if row and row.get("total") is not None else 0


def get_e01_events() -> dict:
    """E01 地图联动总览：事件索引 + KPI 分层统计（不改变项次口径）。"""
    rows = query_all(
        """
        SELECT ev.id AS event_id, ev.event_code, ev.event_category, ev.first_exceeded_at,
               ev.latest_retest_outcome, ev.current_retest_round, ev.effective_status AS event_effective,
               r.id AS result_id, r.result_code, r.detected_value_raw, r.limit_value_raw, r.reported_unit,
               r.standard_name_snapshot,
               fd.factor_code, fd.factor_name,
               s.id AS sample_id, s.monitor_category, s.sampled_at,
               p.id AS point_id, p.point_code, p.point_name, p.chainage, p.source_point_name,
               p.longitude, p.latitude, p.gis_feature_id,
               ps.section_code, ps.section_name,
               eo.object_code, eo.object_name,
               c.id AS case_id, c.case_code, c.title AS case_title, c.current_status,
               c.opened_at, c.closed_at, c.location_text, c.gis_feature_id AS case_gis_feature_id
        FROM e01_exceed_event ev
        JOIN e01_factor_result r ON r.id = ev.original_result_id
        JOIN e01_monitor_sample s ON s.id = r.sample_id
        JOIN e01_monitor_point p ON p.id = s.point_id
        JOIN e01_factor_definition fd ON fd.id = r.factor_id
        LEFT JOIN e_closure_case c ON c.id = ev.case_id
        LEFT JOIN monitor_point_object_relation mpor
          ON mpor.point_id = p.id
         AND s.sampled_at >= mpor.valid_from
         AND (mpor.valid_to IS NULL OR s.sampled_at <= mpor.valid_to)
        LEFT JOIN project_section ps ON ps.id = mpor.section_id
        LEFT JOIN project_engineering_object eo ON eo.id = mpor.object_id
        WHERE s.sampled_at >= %s
          AND ev.effective_status = 'EFFECTIVE'
          AND r.test_stage = 'INITIAL'
          AND r.judgement = 'EXCEEDED'
          AND r.result_validity = 'VALID'
          AND r.effective_status = 'EFFECTIVE'
          AND r.data_nature <> 'background'
          AND s.data_nature <> 'background'
          AND ev.data_nature <> 'background'
        ORDER BY ev.first_exceeded_at DESC, ev.id DESC
        """,
        (E01_CONSTRUCTION_START,),
    )

    events = []
    for row in rows:
        status = _e01_status_label(row.get("current_status"), row.get("latest_retest_outcome"))
        category = row["event_category"] or row["monitor_category"]
        multiple = _e01_ratio(row.get("detected_value_raw"), row.get("limit_value_raw"))
        location_text = row.get("location_text") or row.get("source_point_name") or row.get("object_name")
        if location_text and "｜" in str(location_text):
            location_text = str(location_text).split("｜")[-1].strip()
        events.append(
            {
                "eventId": int(row["event_id"]),
                "eventCode": row["event_code"],
                "title": row.get("case_title") or f"{row['point_name']}·{row['factor_name']}",
                "pointId": int(row["point_id"]),
                "pointCode": row["point_code"],
                "pointName": row["point_name"],
                "sectionCode": row.get("section_code"),
                "sectionName": row.get("section_name"),
                "chainage": row.get("chainage"),
                "locationText": location_text,
                "engineeringObject": row.get("object_name"),
                "engineeringObjectCode": row.get("object_code"),
                "monitorCategory": category,
                "monitorCategoryLabel": E01_CATEGORY_LABELS.get(category, category),
                "factorCode": row["factor_code"],
                "factorName": row["factor_name"],
                "detectedValue": value_for_json(row.get("detected_value_raw")),
                "limitValue": value_for_json(row.get("limit_value_raw")),
                "unit": row.get("reported_unit"),
                "exceedMultiple": multiple,
                "status": status,
                "caseStatus": row.get("current_status"),
                "caseStatusLabel": E01_CASE_STATUS_LABELS.get(row.get("current_status") or "", row.get("current_status")),
                "retestOutcome": row.get("latest_retest_outcome"),
                "retestRound": int(row["current_retest_round"] or 0),
                "isOpen": row.get("current_status") not in {"CLOSED", "CANCELLED", "MERGED"},
                "discoveredAt": value_for_json(row.get("first_exceeded_at") or row.get("sampled_at")),
                "longitude": value_for_json(row.get("longitude")),
                "latitude": value_for_json(row.get("latitude")),
                "gisFeatureId": row.get("case_gis_feature_id") or row.get("gis_feature_id"),
                "resultId": int(row["result_id"]),
                "resultCode": row["result_code"],
                "sampleId": int(row["sample_id"]),
                "caseId": int(row["case_id"]) if row.get("case_id") is not None else None,
                "caseCode": row.get("case_code"),
                "closedAt": value_for_json(row.get("closed_at")) if row.get("closed_at") else None,
                "standardName": row.get("standard_name_snapshot"),
            }
        )

    exceed_item_count = _e01_exceed_item_count()
    point_ids = {e["pointId"] for e in events}
    open_events = [e for e in events if e["isOpen"]]

    by_category: dict[str, int] = {}
    by_status: dict[str, int] = {}
    for event in events:
        by_category[event["monitorCategoryLabel"]] = by_category.get(event["monitorCategoryLabel"], 0) + 1
        by_status[event["status"]] = by_status.get(event["status"], 0) + 1

    map_points: dict[int, dict] = {}
    for event in events:
        point_id = event["pointId"]
        bucket = map_points.get(point_id)
        if bucket is None:
            map_points[point_id] = {
                "pointId": point_id,
                "pointCode": event["pointCode"],
                "pointName": event["pointName"],
                "longitude": event["longitude"],
                "latitude": event["latitude"],
                "gisFeatureId": event["gisFeatureId"],
                "openCount": 1 if event["isOpen"] else 0,
                "eventCount": 1,
                "eventIds": [event["eventId"]],
                "primaryStatus": event["status"],
                "monitorCategory": event["monitorCategory"],
            }
        else:
            bucket["eventCount"] += 1
            bucket["eventIds"].append(event["eventId"])
            if event["isOpen"]:
                bucket["openCount"] += 1
                bucket["primaryStatus"] = event["status"]

    # 一级总览：按未闭环点位聚合（同点多因子合并为一行）
    open_point_buckets: dict[int, dict] = {}
    for event in open_events:
        point_id = event["pointId"]
        bucket = open_point_buckets.get(point_id)
        factor = {
            "factorCode": event["factorCode"],
            "factorName": event["factorName"],
            "detectedValue": event["detectedValue"],
            "limitValue": event["limitValue"],
            "unit": event["unit"],
            "exceedMultiple": event["exceedMultiple"],
            "resultId": event["resultId"],
            "eventId": event["eventId"],
        }
        if bucket is None:
            open_point_buckets[point_id] = {
                "pointId": point_id,
                "pointCode": event["pointCode"],
                "pointName": event["pointName"],
                "sectionCode": event.get("sectionCode"),
                "sectionName": event.get("sectionName"),
                "locationText": event.get("locationText") or event.get("engineeringObject") or event.get("chainage"),
                "monitorCategory": event["monitorCategory"],
                "monitorCategoryLabel": event["monitorCategoryLabel"],
                "status": event["status"],
                "caseStatus": event.get("caseStatus"),
                "discoveredAt": event.get("discoveredAt"),
                "longitude": event.get("longitude"),
                "latitude": event.get("latitude"),
                "gisFeatureId": event.get("gisFeatureId"),
                "canLocate": event.get("longitude") is not None and event.get("latitude") is not None,
                "primaryEventId": event["eventId"],
                "eventIds": [event["eventId"]],
                "factors": [factor],
            }
        else:
            bucket["eventIds"].append(event["eventId"])
            bucket["factors"].append(factor)
            # 保留更早发现时间
            if event.get("discoveredAt") and (
                not bucket.get("discoveredAt") or str(event["discoveredAt"]) < str(bucket["discoveredAt"])
            ):
                bucket["discoveredAt"] = event["discoveredAt"]

    open_points = list(open_point_buckets.values())
    open_points.sort(key=lambda item: str(item.get("discoveredAt") or ""), reverse=True)

    open_by_category = {"WATER": 0, "AIR": 0, "NOISE": 0}
    for item in open_points:
        key = item["monitorCategory"]
        if key in open_by_category:
            open_by_category[key] += 1

    return {
        "code": 0,
        "data": {
            "kpi": {
                "exceedItemCount": exceed_item_count,
                "eventCount": len(events),
                "pointCount": len(point_ids),
                "openEventCount": len(open_events),
            },
            "overview": {
                "totalOpenPoints": len(open_points),
                "waterCount": open_by_category["WATER"],
                "airCount": open_by_category["AIR"],
                "noiseCount": open_by_category["NOISE"],
            },
            "byCategory": [{"name": name, "value": value} for name, value in sorted(by_category.items())],
            "byStatus": [{"name": name, "value": value} for name, value in sorted(by_status.items())],
            "events": events,
            "openPoints": open_points,
            "mapPoints": list(map_points.values()),
        },
        "meta": {
            "statisticsStart": "2026-05-08",
            "dataSource": "MySQL e01_exceed_event + e01_factor_result",
            "isMock": False,
            "overviewRule": "open-points-only",
        },
    }


def get_e01_event_detail(event_id: int) -> dict | None:
    """E01 单事件摘要/完整详情：初检保留，整改/复测按实际轮次返回。"""
    overview = get_e01_events()
    event = next((item for item in overview["data"]["events"] if int(item["eventId"]) == int(event_id)), None)
    if event is None:
        return None

    sample_id = event["sampleId"]
    case_id = event.get("caseId")

    sample_factors = query_all(
        """
        SELECT r.id, r.result_code, r.test_stage, r.judgement, r.detected_value_raw,
               r.limit_value_raw, r.reported_unit, r.result_validity,
               r.standard_name_snapshot, r.reported_factor_name,
               fd.factor_code, fd.factor_name,
               sv.standard_code, sv.standard_name, sv.version_no
        FROM e01_factor_result r
        JOIN e01_factor_definition fd ON fd.id = r.factor_id
        LEFT JOIN e01_standard_version sv ON sv.id = r.standard_version_id
        WHERE r.sample_id = %s
          AND r.effective_status = 'EFFECTIVE'
          AND r.data_nature <> 'background'
        ORDER BY r.test_stage, r.id
        """,
        (sample_id,),
    )

    rectification_rounds = query_all(
        """
        SELECT id, round_no, started_at, submitted_at, rectification_summary,
               review_status, effective_status
        FROM e01_rectification_round
        WHERE event_id = %s
          AND effective_status IN ('EFFECTIVE', 'PENDING_REVIEW')
        ORDER BY round_no
        """,
        (event_id,),
    )

    retest_rounds = query_all(
        """
        SELECT rr.id, rr.round_no, rr.outcome, rr.review_status,
               rr.requested_at, rr.planned_sample_at, rr.actual_sample_at,
               rr.reviewed_at, b.batch_code, b.report_no
        FROM e01_retest_round rr
        LEFT JOIN e01_monitor_batch b ON b.id = rr.retest_batch_id
        WHERE rr.event_id = %s
          AND rr.effective_status IN ('EFFECTIVE', 'PENDING_REVIEW')
        ORDER BY rr.round_no
        """,
        (event_id,),
    )

    retest_links = query_all(
        """
        SELECT link.retest_round_id, link.original_result_id,
               r.id AS result_id, r.result_code, r.judgement,
               r.detected_value_raw, r.limit_value_raw, r.reported_unit,
               fd.factor_code, fd.factor_name, s.sampled_at
        FROM e01_retest_result_link link
        JOIN e01_factor_result r ON r.id = link.factor_result_id
        JOIN e01_factor_definition fd ON fd.id = r.factor_id
        JOIN e01_monitor_sample s ON s.id = r.sample_id
        WHERE link.event_id = %s
          AND link.effective_status IN ('EFFECTIVE', 'PENDING_REVIEW')
        ORDER BY link.retest_round_id, r.id
        """,
        (event_id,),
    )
    links_by_round: dict[int, list[dict]] = {}
    for link in retest_links:
        links_by_round.setdefault(int(link["retest_round_id"]), []).append(
            {
                "resultId": int(link["result_id"]),
                "resultCode": link["result_code"],
                "factorCode": link["factor_code"],
                "factorName": link["factor_name"],
                "judgement": link["judgement"],
                "detectedValue": value_for_json(link.get("detected_value_raw")),
                "limitValue": value_for_json(link.get("limit_value_raw")),
                "unit": link.get("reported_unit"),
                "sampledAt": value_for_json(link.get("sampled_at")),
                "exceedMultiple": _e01_ratio(link.get("detected_value_raw"), link.get("limit_value_raw")),
            }
        )

    status_history = []
    evidence = []
    responsible_org = None
    if case_id is not None:
        status_history = query_all(
            """
            SELECT sequence_no, from_status, to_status, action_code, action_at,
                   operator_name, operator_org_name, comment, transition_result
            FROM e_case_status_history
            WHERE case_id = %s
            ORDER BY sequence_no
            """,
            (case_id,),
        )
        evidence = query_all(
            """
            SELECT ce.id, ce.evidence_role, ce.document_id, ce.file_id,
                   ce.validity_status, ce.verification_status, ce.created_at,
                   d.document_code, d.document_name
            FROM e_case_evidence ce
            LEFT JOIN document_record d ON d.id = ce.document_id
            WHERE ce.case_id = %s
              AND ce.validity_status = 'VALID'
            ORDER BY ce.id
            """,
            (case_id,),
        )
        org_row = query_one(
            """
            SELECT o.org_code, o.org_name
            FROM e_closure_case c
            LEFT JOIN org_unit o ON o.id = c.responsible_org_id
            WHERE c.id = %s
            """,
            (case_id,),
        )
        if org_row and org_row.get("org_name"):
            responsible_org = {
                "code": org_row.get("org_code"),
                "name": org_row.get("org_name"),
            }

    case_status = event.get("caseStatus")
    summary = {
        **event,
        "currentNode": event.get("caseStatusLabel") or event["status"],
        "nextNode": E01_NEXT_NODE.get(case_status) if case_status else None,
        "responsibleOrg": responsible_org,
    }

    return {
        "code": 0,
        "data": {
            "summary": summary,
            "initialFactors": [
                {
                    "resultId": int(row["id"]),
                    "resultCode": row["result_code"],
                    "testStage": row["test_stage"],
                    "factorCode": row["factor_code"],
                    "factorName": row["factor_name"],
                    "judgement": row["judgement"],
                    "detectedValue": value_for_json(row.get("detected_value_raw")),
                    "limitValue": value_for_json(row.get("limit_value_raw")),
                    "unit": row.get("reported_unit"),
                    "exceedMultiple": _e01_ratio(row.get("detected_value_raw"), row.get("limit_value_raw")),
                    "standardCode": row.get("standard_code"),
                    "standardName": row.get("standard_name_snapshot") or row.get("standard_name"),
                    "standardVersion": row.get("version_no"),
                }
                for row in sample_factors
                if row.get("test_stage") == "INITIAL"
            ],
            "allSampleFactors": [
                {
                    "resultId": int(row["id"]),
                    "resultCode": row["result_code"],
                    "testStage": row["test_stage"],
                    "factorCode": row["factor_code"],
                    "factorName": row["factor_name"],
                    "judgement": row["judgement"],
                    "detectedValue": value_for_json(row.get("detected_value_raw")),
                    "limitValue": value_for_json(row.get("limit_value_raw")),
                    "unit": row.get("reported_unit"),
                    "exceedMultiple": _e01_ratio(row.get("detected_value_raw"), row.get("limit_value_raw")),
                    "standardCode": row.get("standard_code"),
                    "standardName": row.get("standard_name_snapshot") or row.get("standard_name"),
                    "standardVersion": row.get("version_no"),
                }
                for row in sample_factors
            ],
            "rectificationRounds": [
                {
                    "id": int(row["id"]),
                    "roundNo": int(row["round_no"]),
                    "startedAt": value_for_json(row.get("started_at")),
                    "submittedAt": value_for_json(row.get("submitted_at")),
                    "summary": row.get("rectification_summary"),
                    "reviewStatus": row.get("review_status"),
                }
                for row in rectification_rounds
            ],
            "retestRounds": [
                {
                    "id": int(row["id"]),
                    "roundNo": int(row["round_no"]),
                    "outcome": row.get("outcome"),
                    "reviewStatus": row.get("review_status"),
                    "requestedAt": value_for_json(row.get("requested_at")),
                    "plannedSampleAt": value_for_json(row.get("planned_sample_at")),
                    "actualSampleAt": value_for_json(row.get("actual_sample_at")),
                    "reviewedAt": value_for_json(row.get("reviewed_at")),
                    "batchCode": row.get("batch_code"),
                    "reportNo": row.get("report_no"),
                    "results": links_by_round.get(int(row["id"]), []),
                }
                for row in retest_rounds
            ],
            "statusHistory": [
                {
                    "sequenceNo": int(row["sequence_no"]),
                    "fromStatus": row.get("from_status"),
                    "fromStatusLabel": E01_CASE_STATUS_LABELS.get(row.get("from_status") or "", row.get("from_status")),
                    "toStatus": row.get("to_status"),
                    "toStatusLabel": E01_CASE_STATUS_LABELS.get(row.get("to_status") or "", row.get("to_status")),
                    "actionCode": row.get("action_code"),
                    "actionAt": value_for_json(row.get("action_at")),
                    "operatorName": row.get("operator_name"),
                    "operatorOrgName": row.get("operator_org_name"),
                    "comment": row.get("comment"),
                    "transitionResult": row.get("transition_result"),
                }
                for row in status_history
            ],
            "evidence": [
                {
                    "id": int(row["id"]),
                    "role": row.get("evidence_role"),
                    "documentId": row.get("document_id"),
                    "fileId": row.get("file_id"),
                    "documentCode": row.get("document_code"),
                    "documentName": row.get("document_name"),
                    "validityStatus": row.get("validity_status"),
                    "verificationStatus": row.get("verification_status"),
                    "createdAt": value_for_json(row.get("created_at")),
                }
                for row in evidence
            ],
            "closure": {
                "caseCode": event.get("caseCode"),
                "status": event.get("caseStatus"),
                "statusLabel": event.get("caseStatusLabel"),
                "closedAt": event.get("closedAt"),
                "openedAt": event.get("discoveredAt"),
            },
        },
        "meta": {
            "statisticsStart": "2026-05-08",
            "dataSource": "MySQL e01_exceed_event chain",
            "isMock": False,
        },
    }


E01_DEFAULT_FACTOR_BY_CATEGORY = {
    "WATER": "SS",
    "AIR": "PM10_DAY",
    "NOISE": "LAEQ_NIGHT",
}


def _e01_to_float(value: Any) -> float | None:
    if value is None:
        return None
    text = str(value).strip().replace("—", "-").replace("–", "-")
    if not text:
        return None
    # pH 区间如 6-9：不按单点限值解析
    if "-" in text and not text.lstrip("-").replace(".", "", 1).isdigit():
        return None
    try:
        return float(text.split()[0])
    except (TypeError, ValueError):
        return None


def _e01_series_exceeded(
    detected: Any,
    limit_raw: Any,
    judgement: str | None,
    limit_operator: str | None = "<=",
) -> bool:
    if judgement == "EXCEEDED":
        return True
    detected_num = _e01_to_float(detected)
    limit_num = _e01_to_float(limit_raw)
    if detected_num is None or limit_num is None:
        return False
    op = (limit_operator or "<=").strip()
    if op in {"<=", "<"}:
        return detected_num > limit_num if op == "<=" else detected_num >= limit_num
    if op in {">=", ">"}:
        return detected_num < limit_num if op == ">=" else detected_num <= limit_num
    return False


def get_e01_point_trend(point_id: int, factor_code: str | None = None) -> dict | None:
    """E01 二级摘要：点位因子时序 + 限值基线（数值超限也计入趋势超标次数）。"""
    point = query_one(
        """
        SELECT p.id, p.point_code, p.point_name, p.chainage, p.source_point_name,
               p.longitude, p.latitude, p.gis_feature_id, p.segment_code, p.segment_name
        FROM e01_monitor_point p
        WHERE p.id = %s
        """,
        (point_id,),
    )
    if point is None:
        return None

    open_overview = get_e01_events()
    open_point = next(
        (item for item in open_overview["data"]["openPoints"] if int(item["pointId"]) == int(point_id)),
        None,
    )

    category_row = query_one(
        """
        SELECT s.monitor_category
        FROM e01_monitor_sample s
        WHERE s.point_id = %s
          AND s.sampled_at >= %s
          AND s.data_nature <> 'background'
        ORDER BY s.sampled_at DESC, s.id DESC
        LIMIT 1
        """,
        (point_id, E01_CONSTRUCTION_START),
    )
    monitor_category = (
        (open_point or {}).get("monitorCategory")
        or (category_row or {}).get("monitor_category")
        or "WATER"
    )

    factor_rows = query_all(
        """
        SELECT fd.factor_code, fd.factor_name, fd.default_unit,
               COUNT(*) AS sample_count,
               SUM(CASE WHEN r.judgement = 'EXCEEDED' THEN 1 ELSE 0 END) AS judgement_exceed_count,
               MAX(r.limit_value_raw) AS limit_value_raw,
               MAX(r.reported_unit) AS reported_unit,
               MAX(r.standard_name_snapshot) AS standard_name,
               MAX(sl.limit_operator) AS limit_operator,
               MAX(sl.limit_value_num) AS limit_value_num
        FROM e01_factor_result r
        JOIN e01_monitor_sample s ON s.id = r.sample_id
        JOIN e01_factor_definition fd ON fd.id = r.factor_id
        LEFT JOIN e01_standard_limit sl
          ON sl.factor_id = fd.id
         AND sl.effective_status = 'EFFECTIVE'
        WHERE s.point_id = %s
          AND s.sampled_at >= %s
          AND r.test_stage = 'INITIAL'
          AND r.result_validity = 'VALID'
          AND r.effective_status = 'EFFECTIVE'
          AND r.data_nature <> 'background'
          AND s.data_nature <> 'background'
        GROUP BY fd.factor_code, fd.factor_name, fd.default_unit
        ORDER BY sample_count DESC, fd.factor_code
        """,
        (point_id, E01_CONSTRUCTION_START),
    )
    if not factor_rows:
        return None

    preferred = (factor_code or "").strip().upper() or None
    if not preferred and open_point and open_point.get("factors"):
        preferred = str(open_point["factors"][0].get("factorCode") or "").upper() or None
    if not preferred:
        preferred = E01_DEFAULT_FACTOR_BY_CATEGORY.get(str(monitor_category).upper(), factor_rows[0]["factor_code"])

    available_codes = {str(row["factor_code"]).upper() for row in factor_rows}
    if preferred not in available_codes:
        preferred = str(factor_rows[0]["factor_code"]).upper()

    series_rows = query_all(
        """
        SELECT r.id AS result_id, r.result_code, r.test_stage, r.judgement,
               r.detected_value_raw, r.limit_value_raw, r.reported_unit,
               r.standard_name_snapshot, r.reported_factor_name,
               s.id AS sample_id, s.sampled_at, s.monitor_category,
               fd.factor_code, fd.factor_name, fd.default_unit,
               sl.limit_operator, sl.limit_value_num
        FROM e01_factor_result r
        JOIN e01_monitor_sample s ON s.id = r.sample_id
        JOIN e01_factor_definition fd ON fd.id = r.factor_id
        LEFT JOIN e01_standard_limit sl
          ON sl.factor_id = fd.id
         AND sl.effective_status = 'EFFECTIVE'
        WHERE s.point_id = %s
          AND UPPER(fd.factor_code) = %s
          AND s.sampled_at >= %s
          AND r.test_stage = 'INITIAL'
          AND r.result_validity = 'VALID'
          AND r.effective_status = 'EFFECTIVE'
          AND r.data_nature <> 'background'
          AND s.data_nature <> 'background'
        ORDER BY s.sampled_at ASC, r.id ASC
        """,
        (point_id, preferred, E01_CONSTRUCTION_START),
    )
    if not series_rows:
        return None

    def build_point(row: dict) -> dict:
        exceeded = _e01_series_exceeded(
            row.get("detected_value_raw"),
            row.get("limit_value_raw"),
            row.get("judgement"),
            row.get("limit_operator") or "<=",
        )
        return {
            "at": value_for_json(row.get("sampled_at")),
            "value": value_for_json(row.get("detected_value_raw")),
            "valueNum": _e01_to_float(row.get("detected_value_raw")),
            "limitValue": value_for_json(row.get("limit_value_raw")),
            "judgement": row.get("judgement"),
            "exceeded": exceeded,
            "exceedMultiple": _e01_ratio(row.get("detected_value_raw"), row.get("limit_value_raw")),
            "resultId": int(row["result_id"]),
            "sampleId": int(row["sample_id"]),
            "testStage": row.get("test_stage"),
        }

    series = [build_point(row) for row in series_rows]
    latest = series[-1]
    head = series_rows[-1]
    baseline_num = _e01_to_float(head.get("limit_value_num"))
    if baseline_num is None:
        baseline_num = _e01_to_float(head.get("limit_value_raw"))

    exceed_count = sum(1 for item in series if item["exceeded"])

    factor_options = []
    for row in factor_rows:
        code = str(row["factor_code"]).upper()
        # 用数值超限重算该因子超标次数需二次查询；这里用轻量重算
        option_rows = query_all(
            """
            SELECT r.detected_value_raw, r.limit_value_raw, r.judgement, sl.limit_operator
            FROM e01_factor_result r
            JOIN e01_monitor_sample s ON s.id = r.sample_id
            JOIN e01_factor_definition fd ON fd.id = r.factor_id
            LEFT JOIN e01_standard_limit sl
              ON sl.factor_id = fd.id AND sl.effective_status = 'EFFECTIVE'
            WHERE s.point_id = %s
              AND UPPER(fd.factor_code) = %s
              AND s.sampled_at >= %s
              AND r.test_stage = 'INITIAL'
              AND r.result_validity = 'VALID'
              AND r.effective_status = 'EFFECTIVE'
              AND r.data_nature <> 'background'
              AND s.data_nature <> 'background'
            """,
            (point_id, code, E01_CONSTRUCTION_START),
        )
        opt_exceed = sum(
            1
            for item in option_rows
            if _e01_series_exceeded(
                item.get("detected_value_raw"),
                item.get("limit_value_raw"),
                item.get("judgement"),
                item.get("limit_operator") or "<=",
            )
        )
        factor_options.append(
            {
                "factorCode": code,
                "factorName": row["factor_name"],
                "unit": row.get("reported_unit") or row.get("default_unit"),
                "sampleCount": int(row["sample_count"] or 0),
                "exceedCount": opt_exceed,
            }
        )

    companion_series = None
    if str(monitor_category).upper() == "NOISE" and preferred == "LAEQ_NIGHT" and "LAEQ_DAY" in available_codes:
        day_rows = query_all(
            """
            SELECT r.id AS result_id, r.result_code, r.test_stage, r.judgement,
                   r.detected_value_raw, r.limit_value_raw, r.reported_unit,
                   s.id AS sample_id, s.sampled_at, fd.factor_code, fd.factor_name,
                   sl.limit_operator
            FROM e01_factor_result r
            JOIN e01_monitor_sample s ON s.id = r.sample_id
            JOIN e01_factor_definition fd ON fd.id = r.factor_id
            LEFT JOIN e01_standard_limit sl
              ON sl.factor_id = fd.id AND sl.effective_status = 'EFFECTIVE'
            WHERE s.point_id = %s
              AND UPPER(fd.factor_code) = 'LAEQ_DAY'
              AND s.sampled_at >= %s
              AND r.test_stage = 'INITIAL'
              AND r.result_validity = 'VALID'
              AND r.effective_status = 'EFFECTIVE'
              AND r.data_nature <> 'background'
              AND s.data_nature <> 'background'
            ORDER BY s.sampled_at ASC, r.id ASC
            """,
            (point_id, E01_CONSTRUCTION_START),
        )
        companion_series = {
            "factorCode": "LAEQ_DAY",
            "factorName": "昼间等效声级",
            "points": [build_point(row) for row in day_rows],
        }

    location_text = None
    if open_point:
        location_text = open_point.get("locationText")
    if not location_text:
        location_text = point.get("source_point_name") or point.get("chainage") or point.get("point_name")

    return {
        "code": 0,
        "data": {
            "point": {
                "pointId": int(point["id"]),
                "pointCode": point["point_code"],
                "pointName": point["point_name"],
                "monitorCategory": monitor_category,
                "monitorCategoryLabel": E01_CATEGORY_LABELS.get(monitor_category, monitor_category),
                "sectionCode": (open_point or {}).get("sectionCode") or point.get("segment_code"),
                "sectionName": (open_point or {}).get("sectionName") or point.get("segment_name"),
                "locationText": location_text,
                "status": (open_point or {}).get("status"),
                "discoveredAt": (open_point or {}).get("discoveredAt"),
                "longitude": value_for_json(point.get("longitude")),
                "latitude": value_for_json(point.get("latitude")),
                "primaryEventId": (open_point or {}).get("primaryEventId"),
                "factors": (open_point or {}).get("factors") or [],
            },
            "factor": {
                "factorCode": preferred,
                "factorName": head.get("reported_factor_name") or head.get("factor_name"),
                "unit": head.get("reported_unit") or head.get("default_unit"),
                "limitValue": value_for_json(head.get("limit_value_raw")),
                "limitValueNum": baseline_num,
                "limitOperator": head.get("limit_operator") or "<=",
                "standardName": head.get("standard_name_snapshot"),
            },
            "series": series,
            "companionSeries": companion_series,
            "stats": {
                "sampleCount": len(series),
                "exceedCount": exceed_count,
                "latestValue": latest.get("value"),
                "latestAt": latest.get("at"),
                "latestExceeded": bool(latest.get("exceeded")),
            },
            "factorOptions": factor_options,
        },
        "meta": {
            "statisticsStart": "2026-05-08",
            "dataSource": "MySQL e01_factor_result time series",
            "isMock": False,
            "exceedRule": "judgement-or-numeric-vs-limit",
        },
    }


def get_e02_env_issue_detail() -> dict | None:
    """旧弹窗兼容：切换前仅读台账；默认 formal，演示部署可读 demo。"""
    scope_sql, scope_params = _e02_scope_clause("demo" if E02_ALLOW_DEMO else "formal")
    open_rows = query_all(
        f"""
        SELECT *
        FROM env_issue_record
        WHERE issue_status NOT IN ('已闭环','已撤销','已合并')
          {scope_sql}
        ORDER BY overdue DESC, deadline, id
        """,
        scope_params,
    )
    if not open_rows:
        return None
    overdue_count = sum(1 for row in open_rows if int(row.get("overdue") or 0) == 1)
    rectifying_count = sum(1 for row in open_rows if row.get("issue_status") == "整改中")
    pending_review_count = sum(1 for row in open_rows if row.get("issue_status") == "待复查")
    pending_close_count = sum(1 for row in open_rows if row.get("issue_status") == "待销项")

    detail = with_snapshot_base("E02")

    def e02_source_id(row: dict) -> str:
        mapped = {
            420001: "E02-003",
            420002: "E02-001",
            420003: "E02-002",
            420004: "E02-004",
            420005: "E02-005",
        }
        row_id = int(row.get("id") or 0)
        return mapped.get(row_id, f"E02-{row_id}")

    e02_gis_feature_map = {
        "E02-001": "section-1-1",
        "E02-003": "section-2-1",
        "E02-005": "eco-1-1",
    }

    detail.update(
        {
            "summary": [
                {"label": "当前未闭环", "value": len(open_rows), "unit": "项"},
                {"label": "整改中", "value": rectifying_count, "unit": "项"},
                {"label": "待复查", "value": pending_review_count, "unit": "项"},
                {"label": "待销项", "value": pending_close_count, "unit": "项"},
                {"label": "已逾期", "value": overdue_count, "unit": "项"},
            ],
            "statusData": [
                {"name": "整改中", "value": rectifying_count},
                {"name": "待复查", "value": pending_review_count},
                {"name": "待销项", "value": pending_close_count},
            ],
            "chartTitle": "当前未闭环事项办理状态",
            "detailColumns": [
                {"key": "name", "label": "问题名称", "width": "22%"},
                {"key": "category", "label": "问题类型", "width": "11%"},
                {"key": "time", "label": "发现时间", "width": "11%"},
                {"key": "level", "label": "等级", "width": "8%"},
                {"key": "department", "label": "责任部门", "width": "14%"},
                {"key": "deadline", "label": "整改截止", "width": "11%"},
                {"key": "mainStatus", "label": "办理状态", "width": "11%"},
                {"key": "deadlineStatus", "label": "时限状态", "width": "12%"},
            ],
            "detailData": [
                {
                    "id": e02_source_id(row),
                    "sourceId": e02_source_id(row),
                    "sourceTable": "env_issue_record",
                    "rawId": row.get("id"),
                    "gisFeatureId": e02_gis_feature_map.get(e02_source_id(row)),
                    "category": row.get("issue_type") or "",
                    "name": row.get("issue_name") or row.get("issue_type") or "",
                    "time": value_for_json(row.get("found_date")),
                    "level": row.get("issue_level") or "",
                    "department": row.get("responsible_department") or "",
                    "deadline": value_for_json(row.get("deadline")),
                    "status": row.get("issue_status"),
                    "mainStatus": row.get("issue_status"),
                    "overdue": bool(row.get("overdue")),
                    "deadlineStatus": "已逾期" if int(row.get("overdue") or 0) == 1 else "正常",
                }
                for row in open_rows
            ],
            "dataSource": "环保问题明细表 env_issue_record",
            "statisticsAsOf": "2026-07-13",
            "updateTime": "2026-07-13 09:00",
            "isMock": False,
        }
    )
    return detail


# ============================================================================
# E02 环保问题工作台 API（V1.0 冻结稿）
# ============================================================================

# 台账中文状态 -> 统计分组
def _e02_status_group(issue_status: str) -> str:
    """映射台账中文状态到统计分组"""
    if issue_status in ("整改中", "待整改", "已发现"):
        return "rectifying"
    if issue_status == "待复查":
        return "pendingReview"
    if issue_status == "待销项":
        return "pendingClosure"
    if issue_status in ("已闭环", "已撤销", "已合并"):
        return "terminal"
    return "rectifying"


# 案卷英文状态 -> 统计分组
def _e02_case_status_group(case_status: str) -> str:
    if case_status in ("DISCOVERED", "PENDING_RECTIFICATION", "RECTIFYING"):
        return "rectifying"
    if case_status == "PENDING_REVIEW":
        return "pendingReview"
    if case_status == "PENDING_CLOSURE":
        return "pendingClosure"
    if case_status in ("CLOSED", "CANCELLED", "MERGED"):
        return "terminal"
    return "rectifying"


def _e02_scope_clause(scope: str | None) -> tuple[str, tuple[Any, ...]]:
    """根据 scope 返回 SQL WHERE 子句和参数"""
    if scope == "demo":
        return "AND is_demo = %s AND data_nature = %s", (1, "demo")
    # formal 默认
    return "AND is_demo = %s AND data_nature = %s", (0, "formal")


def get_e02_issues(scope: str | None = None) -> dict:
    """E02 工作台列表 API：overview 统计 + issues + spatialLinks"""
    effective_scope = scope or ("demo" if E02_ALLOW_DEMO else "formal")
    if effective_scope == "demo" and not E02_ALLOW_DEMO:
        return {
            "code": 403,
            "message": "测试数据在当前部署未启用",
            "data": {"overview": {}, "issues": [], "spatialLinks": []},
        }

    scope_sql, scope_params = _e02_scope_clause(effective_scope)

    # 1. issues 列表
    issues_rows = query_all(
        f"""
        SELECT id, business_code, issue_name, issue_type, location_text,
               issue_status, overdue, deadline, responsible_org_name,
               found_date, closed_date
        FROM env_issue_record
        WHERE issue_status NOT IN ('已闭环','已撤销','已合并')
          {scope_sql}
        ORDER BY overdue DESC, deadline ASC, id ASC
        """,
        scope_params,
    )

    # 2. overview 统计
    total = len(issues_rows)
    rectifying = sum(1 for r in issues_rows if _e02_status_group(r["issue_status"]) == "rectifying")
    pending_review = sum(1 for r in issues_rows if _e02_status_group(r["issue_status"]) == "pendingReview")
    pending_closure = sum(1 for r in issues_rows if _e02_status_group(r["issue_status"]) == "pendingClosure")
    overdue_among = sum(1 for r in issues_rows if int(r.get("overdue") or 0) == 1)

    # 3. spatialLinks：从关系表读取
    biz_codes = [r["business_code"] for r in issues_rows if r.get("business_code")]
    spatial_links: list[dict] = []
    if biz_codes:
        placeholders = ",".join(["%s"] * len(biz_codes))
        spatial_rows = query_all(
            f"""
            SELECT feature_id, relation_type, relation_code, relation_name, source_id
            FROM gis_feature_business_relation
            WHERE relation_type = 'environment_problem'
              AND (
                source_id IN ({placeholders})
                OR relation_code IN ({placeholders})
              )
            """,
            tuple(biz_codes) + tuple(biz_codes),
        )
        spatial_links = [
            {
                "featureId": r["feature_id"],
                "geometryType": "unknown",
                "role": "related",
                "isPrimary": False,
                "businessKey": r.get("source_id") or r.get("relation_code") or "",
            }
            for r in spatial_rows
        ]

    # 4. 组装 issues
    issues = []
    for row in issues_rows:
        biz_code = row.get("business_code") or ""
        issue_spatial = [sl for sl in spatial_links if sl.get("businessKey") == biz_code]
        issues.append({
            "id": row["id"],
            "businessCode": biz_code,
            "title": row.get("issue_name") or row.get("issue_type") or "",
            "issueType": row.get("issue_type") or "",
            "locationText": row.get("location_text") or "",
            "status": row.get("issue_status") or "",
            "statusGroup": _e02_status_group(row.get("issue_status") or ""),
            "overdue": bool(row.get("overdue")),
            "deadline": value_for_json(row.get("deadline")),
            "responsibleOrgName": row.get("responsible_org_name") or "",
            "canLocate": len(issue_spatial) > 0,
            "spatialLinks": [{k: v for k, v in sl.items() if k != "businessKey"} for sl in issue_spatial],
        })

    return {
        "code": 0,
        "data": {
            "overview": {
                "total": total,
                "rectifying": rectifying,
                "pendingReview": pending_review,
                "pendingClosure": pending_closure,
                "overdueAmong": overdue_among,
            },
            "issues": issues,
            "spatialLinks": spatial_links,
            "scope": effective_scope,
            "isDemo": effective_scope == "demo",
        },
    }


def get_e02_issue_detail(issue_id: int) -> dict | None:
    """E02 单条详情 API：进度、轨迹、证据、材料完整度"""
    # 1. 台账基础
    row = query_one(
        """
        SELECT id, business_code, issue_name, issue_type, location_text,
               issue_status, overdue, deadline, responsible_org_name,
               found_date, closed_date, is_demo, data_nature
        FROM env_issue_record
        WHERE id = %s
        """,
        (issue_id,),
    )
    if row is None:
        return None

    # 2. 关联案卷
    case_row = query_one(
        """
        SELECT id, case_code, current_status, opened_at, closed_at,
               responsible_org_id, deadline AS case_deadline
        FROM e_closure_case
        WHERE source_table = 'env_issue_record'
          AND source_record_id = %s
        LIMIT 1
        """,
        (issue_id,),
    )
    case_id = case_row["id"] if case_row else None

    # 3. 状态轨迹
    history: list[dict] = []
    if case_id:
        hist_rows = query_all(
            """
            SELECT from_status, to_status, action_code, action_at,
                   operator_name, operator_org_name, comment, transition_result
            FROM e_case_status_history
            WHERE case_id = %s
            ORDER BY action_at ASC
            """,
            (case_id,),
        )
        history = [
            {
                "fromStatus": r.get("from_status"),
                "toStatus": r["to_status"],
                "actionCode": r.get("action_code"),
                "actionAt": value_for_json(r.get("action_at")),
                "operatorName": r.get("operator_name") or "",
                "operatorOrgName": r.get("operator_org_name") or "",
                "comment": r.get("comment") or "",
                "transitionResult": r.get("transition_result") or "SUCCESS",
            }
            for r in hist_rows
        ]

    # 4. 参与方
    parties: list[dict] = []
    if case_id:
        party_rows = query_all(
            """
            SELECT party_role, org_name, user_name
            FROM e_case_party
            WHERE case_id = %s AND IFNULL(is_current, 1) = 1
            ORDER BY party_role
            """,
            (case_id,),
        )
        parties = [
            {
                "role": r["party_role"],
                "roleLabel": {
                    "DISCOVERER": "发现人",
                    "RESPONSIBLE": "责任单位",
                    "HANDLER": "处理人",
                    "REVIEWER": "复查人",
                    "CLOSER": "销项人",
                    "TEST_PROVIDER": "检测方",
                }.get(r["party_role"], r["party_role"]),
                "orgName": r.get("org_name") or "",
                "userName": r.get("user_name") or "",
            }
            for r in party_rows
        ]

    # 5. 证据
    evidence: list[dict] = []
    if case_id:
        ev_rows = query_all(
            """
            SELECT e.evidence_role, e.validity_status, e.created_at, e.document_id,
                   d.document_name, d.document_type, d.source_name
            FROM e_case_evidence e
            LEFT JOIN document_record d ON d.id = e.document_id
            WHERE e.case_id = %s AND e.validity_status = 'VALID'
            ORDER BY e.created_at ASC
            """,
            (case_id,),
        )
        evidence = [
            {
                "role": r["evidence_role"],
                "roleLabel": {
                    "FORMAL_NOTICE": "正式通知",
                    "INITIAL_REPORT": "初始报告",
                    "RAW_RECORD": "原始记录",
                    "RECTIFICATION_MATERIAL": "整改材料",
                    "RETEST_REPORT": "复测报告",
                    "REVIEW_OPINION": "复查意见",
                    "CLOSURE_DOCUMENT": "销项文件",
                    "CANCELLATION_DOCUMENT": "撤销文件",
                }.get(r["evidence_role"], r["evidence_role"]),
                "kind": r.get("document_type") or "",
                "title": r.get("document_name") or r.get("evidence_role") or "",
                "description": r.get("source_name") or "",
                "validityStatus": r.get("validity_status") or "VALID",
                "createdAt": value_for_json(r.get("created_at")),
            }
            for r in ev_rows
        ]

    # 6. 材料完整度（服务端计算）
    material_completeness = _e02_material_completeness(case_row["current_status"] if case_row else None, history, evidence)

    # 7. GIS 关系
    biz_code = row.get("business_code") or ""
    spatial_rows = query_all(
        """
        SELECT feature_id, relation_type, relation_name, source_id, relation_code
        FROM gis_feature_business_relation
        WHERE relation_type = 'environment_problem'
          AND (source_id = %s OR relation_code = %s)
        """,
        (biz_code, biz_code),
    )
    spatial_links = [
        {
            "featureId": r["feature_id"],
            "geometryType": "unknown",
            "role": "related",
            "isPrimary": True,
        }
        for r in spatial_rows
    ]

    return {
        "code": 0,
        "data": {
            "id": row["id"],
            "businessCode": biz_code,
            "title": row.get("issue_name") or row.get("issue_type") or "",
            "issueType": row.get("issue_type") or "",
            "locationText": row.get("location_text") or "",
            "status": row.get("issue_status") or "",
            "statusGroup": _e02_status_group(row.get("issue_status") or ""),
            "overdue": bool(row.get("overdue")),
            "deadline": value_for_json(row.get("deadline")),
            "responsibleOrgName": row.get("responsible_org_name") or "",
            "foundDate": value_for_json(row.get("found_date")),
            "closedDate": value_for_json(row.get("closed_date")),
            "isDemo": bool(row.get("is_demo")),
            "dataNature": row.get("data_nature") or "formal",
            "case": {
                "caseId": case_id,
                "caseCode": case_row["case_code"] if case_row else None,
                "caseStatus": case_row["current_status"] if case_row else None,
                "caseStatusGroup": _e02_case_status_group(case_row["current_status"]) if case_row else None,
                "openedAt": value_for_json(case_row["opened_at"]) if case_row else None,
                "closedAt": value_for_json(case_row["closed_at"]) if case_row else None,
            } if case_row else None,
            "history": history,
            "parties": parties,
            "evidence": evidence,
            "materialCompleteness": material_completeness,
            "spatialLinks": spatial_links,
        },
    }


def _e02_material_completeness(
    case_status: str | None,
    history: list[dict],
    evidence: list[dict],
) -> dict:
    """计算材料完整度（按设计 §8）"""
    covered_roles = {e["role"] for e in evidence}

    # 确定历史上到达的最高阶段
    highest_group = "rectifying"
    if case_status:
        highest_group = _e02_case_status_group(case_status)

    # 从轨迹推断最高阶段（含历史已到达）
    for h in history:
        to_status = h.get("toStatus") or ""
        g = _e02_case_status_group(to_status)
        if g == "pendingClosure":
            highest_group = "pendingClosure"
        elif g == "pendingReview" and highest_group not in ("pendingClosure",):
            highest_group = "pendingReview"

    # 检查是否发生过退回
    has_return = any(
        h.get("transitionResult") in ("RETURNED", "REJECTED")
        or h.get("actionCode") == "REVIEW_REJECT"
        for h in history
    )

    # 基础必需角色
    required: list[str] = ["FORMAL_NOTICE"]
    if highest_group in ("pendingReview", "pendingClosure", "terminal"):
        required.append("RECTIFICATION_MATERIAL")
    if highest_group in ("pendingClosure", "terminal"):
        required.append("REVIEW_OPINION")
    if highest_group == "terminal":
        required.append("CLOSURE_DOCUMENT")

    # 退回后：保留上轮意见角色
    if has_return and "REVIEW_OPINION" not in required:
        required.append("REVIEW_OPINION")

    # 去重并保持顺序
    seen = set()
    required_ordered = []
    for r in required:
        if r not in seen:
            seen.add(r)
            required_ordered.append(r)

    # 退回后再整改：上轮整改材料不计入本轮覆盖，避免退化成「仅通知单」同时又假完整
    effective_covered = set(covered_roles)
    if has_return and case_status in ("RECTIFYING", "PENDING_RECTIFICATION", "DISCOVERED"):
        effective_covered.discard("RECTIFICATION_MATERIAL")

    pending = [r for r in required_ordered if r not in effective_covered]
    ratio_num = len(required_ordered) - len(pending)
    ratio_denom = len(required_ordered)

    notes: list[str] = []
    if has_return and case_status in ("RECTIFYING", "PENDING_RECTIFICATION", "DISCOVERED"):
        notes.append("本轮整改材料待补")
    if pending:
        notes.append(f"待补充：{', '.join(pending)}")

    return {
        "requiredRoles": required_ordered,
        "coveredRoles": sorted(list(effective_covered & set(required_ordered))),
        "pendingRoles": pending,
        "ratio": f"{ratio_num}/{ratio_denom}",
        "notes": notes,
    }


def _e03_material_completeness(
    case_status: str | None,
    history: list[dict],
    evidence: list[dict],
) -> dict:
    """E03 材料完整度。退回后再整改须满足冻结 D07=3/4：上轮整改计入、本轮整改待补。"""
    base = _e02_material_completeness(case_status, history, evidence)
    has_return = any(
        h.get("transitionResult") in ("RETURNED", "REJECTED")
        or h.get("actionCode") == "REVIEW_REJECT"
        for h in history
    )
    if not (
        has_return
        and case_status in ("RECTIFYING", "PENDING_RECTIFICATION", "DISCOVERED")
    ):
        return base

    covered_roles = {e["role"] for e in evidence}
    # 四槽：通知、上轮整改、复查意见、本轮整改（本轮恒待补）
    required_ordered = [
        "FORMAL_NOTICE",
        "RECTIFICATION_MATERIAL",
        "REVIEW_OPINION",
        "CURRENT_RECTIFICATION_MATERIAL",
    ]
    effective_covered = set()
    if "FORMAL_NOTICE" in covered_roles or "INITIAL_REPORT" in covered_roles:
        effective_covered.add("FORMAL_NOTICE")
    if "RECTIFICATION_MATERIAL" in covered_roles:
        effective_covered.add("RECTIFICATION_MATERIAL")
    if "REVIEW_OPINION" in covered_roles:
        effective_covered.add("REVIEW_OPINION")
    # CURRENT_RECTIFICATION_MATERIAL 永不计入 covered（本轮待补）
    pending = [r for r in required_ordered if r not in effective_covered]
    ratio_num = len(required_ordered) - len(pending)
    notes = ["本轮整改材料待补"]
    if pending:
        label_pending = [
            "本轮整改材料" if r == "CURRENT_RECTIFICATION_MATERIAL" else r for r in pending
        ]
        notes.append(f"待补充：{', '.join(label_pending)}")
    return {
        "requiredRoles": required_ordered,
        "coveredRoles": sorted(list(effective_covered)),
        "pendingRoles": pending,
        "ratio": f"{ratio_num}/{len(required_ordered)}",
        "notes": notes,
    }


# ============================================================================
# E03 水土保持问题工作台 API（V1.0 冻结稿）
# ============================================================================

# 台账中文状态 -> 统计分组（与 E02 映射一致）
def _e03_status_group(issue_status: str) -> str:
    """映射台账中文状态到统计分组"""
    if not issue_status:
        return "unknown"
    if issue_status in ("整改中", "待整改", "已发现"):
        return "rectifying"
    if issue_status == "待复查":
        return "pendingReview"
    if issue_status == "待销项":
        return "pendingClosure"
    if issue_status == "暂缓":
        return "suspended"
    if issue_status in ("已闭环", "已撤销", "已合并"):
        return "terminal"
    return "unknown"


# 案卷英文状态 -> 统计分组（与 E02 映射一致）
def _e03_case_status_group(case_status: str) -> str:
    if case_status in ("DISCOVERED", "PENDING_RECTIFICATION", "RECTIFYING"):
        return "rectifying"
    if case_status == "PENDING_REVIEW":
        return "pendingReview"
    if case_status == "PENDING_CLOSURE":
        return "pendingClosure"
    if case_status in ("CLOSED", "CANCELLED", "MERGED"):
        return "terminal"
    return "rectifying"


def _e03_scope_clause(scope: str | None) -> tuple[str, tuple[Any, ...]]:
    """根据 scope 返回 SQL WHERE 子句和参数（含显式 EFFECTIVE）。"""
    if scope == "demo":
        return (
            "AND is_demo = %s AND data_nature = %s AND effective_status = %s",
            (1, "demo", "EFFECTIVE"),
        )
    return (
        "AND is_demo = %s AND data_nature = %s AND effective_status = %s",
        (0, "formal", "EFFECTIVE"),
    )


def _e03_match_spatial_keys(row: dict, spatial_rows: list[dict]) -> list[dict]:
    """按 business_code / relation_code / 台账 id 匹配 GIS 关系（种子 source_id 多为台账主键）。"""
    biz_code = (row.get("business_code") or "").strip()
    ledger_id = str(row.get("id") or "")
    matched: list[dict] = []
    for r in spatial_rows:
        relation_code = (r.get("relation_code") or "").strip()
        source_id = str(r.get("source_id") or "").strip()
        if biz_code and (relation_code == biz_code or source_id == biz_code):
            matched.append(r)
        elif ledger_id and source_id == ledger_id:
            matched.append(r)
    return matched


def get_e03_issues(scope: str | None = None) -> dict:
    """E03 工作台列表 API：overview 统计 + issues + spatialLinks"""
    effective_scope = scope or ("demo" if E03_ALLOW_DEMO else "formal")
    if effective_scope == "demo" and not E03_ALLOW_DEMO:
        return {
            "code": 403,
            "message": "测试数据在当前部署未启用",
            "data": {"overview": {}, "issues": [], "spatialLinks": []},
        }

    scope_sql, scope_params = _e03_scope_clause(effective_scope)

    # 1. issues 列表（空/异常状态不进未闭环；须显式 EFFECTIVE）
    issues_rows = query_all(
        f"""
        SELECT id, business_code, issue_name, issue_type, location_text,
               issue_status, overdue, deadline, responsible_org_name,
               found_date, closed_date, description, discovery_basis
        FROM water_protection_issue
        WHERE issue_status NOT IN ('已闭环','已撤销','已合并')
          AND issue_status IS NOT NULL
          AND TRIM(issue_status) <> ''
          {scope_sql}
        ORDER BY overdue DESC, deadline ASC, id ASC
        """,
        scope_params,
    )
    issues_rows = [
        r for r in issues_rows
        if _e03_status_group(r.get("issue_status") or "") in (
            "rectifying", "pendingReview", "pendingClosure", "suspended",
        )
    ]

    # 2. overview 统计（仅台账映射）
    total = len(issues_rows)
    rectifying = sum(1 for r in issues_rows if _e03_status_group(r["issue_status"]) == "rectifying")
    pending_review = sum(1 for r in issues_rows if _e03_status_group(r["issue_status"]) == "pendingReview")
    pending_closure = sum(1 for r in issues_rows if _e03_status_group(r["issue_status"]) == "pendingClosure")
    overdue_among = sum(1 for r in issues_rows if int(r.get("overdue") or 0) == 1)

    # 3. spatialLinks：business_code 与台账 id 双键查询
    biz_codes = [r["business_code"] for r in issues_rows if r.get("business_code")]
    ledger_ids = [str(r["id"]) for r in issues_rows]
    lookup_keys = list(dict.fromkeys([*biz_codes, *ledger_ids]))
    spatial_rows: list[dict] = []
    if lookup_keys:
        placeholders = ",".join(["%s"] * len(lookup_keys))
        spatial_rows = query_all(
            f"""
            SELECT feature_id, relation_type, relation_code, relation_name, source_id
            FROM gis_feature_business_relation
            WHERE relation_type = 'E03_WATER_ISSUE'
              AND (
                source_id IN ({placeholders})
                OR relation_code IN ({placeholders})
              )
            """,
            tuple(lookup_keys) + tuple(lookup_keys),
        )

    # 4. 组装 issues（businessKey 优先 relation_code，与 business_code 对齐）
    issues = []
    public_spatial: list[dict] = []
    for row in issues_rows:
        biz_code = row.get("business_code") or ""
        matched_rows = _e03_match_spatial_keys(row, spatial_rows)
        issue_spatial = []
        for r in matched_rows:
            link = {
                "featureId": r["feature_id"],
                "geometryType": "unknown",
                "role": "related",
                "isPrimary": False,
                "businessKey": (r.get("relation_code") or biz_code or str(r.get("source_id") or "")),
            }
            issue_spatial.append(link)
            public_spatial.append({k: v for k, v in link.items() if k != "businessKey"})
        issues.append({
            "id": row["id"],
            "businessCode": biz_code,
            "title": row.get("issue_name") or row.get("issue_type") or "",
            "issueType": row.get("issue_type") or "",
            "locationText": row.get("location_text") or "",
            "status": row.get("issue_status") or "",
            "statusGroup": _e03_status_group(row.get("issue_status") or ""),
            "overdue": bool(row.get("overdue")),
            "deadline": value_for_json(row.get("deadline")),
            "responsibleOrgName": row.get("responsible_org_name") or "",
            "canLocate": len(issue_spatial) > 0,
            "spatialLinks": [{k: v for k, v in sl.items() if k != "businessKey"} for sl in issue_spatial],
        })

    return {
        "code": 0,
        "data": {
            "overview": {
                "total": total,
                "rectifying": rectifying,
                "pendingReview": pending_review,
                "pendingClosure": pending_closure,
                "overdueAmong": overdue_among,
            },
            "issues": issues,
            "spatialLinks": public_spatial,
            "scope": effective_scope,
            "isDemo": effective_scope == "demo",
        },
    }


def get_e03_issue_detail(issue_id: int, scope: str | None = None) -> dict | None:
    """E03 单条详情 API：水保概况 + 进度、轨迹、证据、材料完整度"""
    effective_scope = scope or ("demo" if E03_ALLOW_DEMO else "formal")
    if effective_scope == "demo" and not E03_ALLOW_DEMO:
        return {
            "code": 403,
            "message": "测试数据在当前部署未启用",
            "data": None,
        }

    # 1. 台账基础
    row = query_one(
        """
        SELECT id, business_code, issue_name, issue_type, location_text,
               issue_status, overdue, deadline, responsible_org_name,
               found_date, closed_date, is_demo, data_nature,
               description, discovery_basis, effective_status
        FROM water_protection_issue
        WHERE id = %s
        """,
        (issue_id,),
    )
    if row is None:
        return None

    is_demo_row = int(row.get("is_demo") or 0) == 1 and (row.get("data_nature") or "") == "demo"
    if effective_scope == "formal" and is_demo_row:
        return None
    if effective_scope == "demo" and not is_demo_row:
        return None
    if not E03_ALLOW_DEMO and is_demo_row:
        return {
            "code": 403,
            "message": "测试数据在当前部署未启用",
            "data": None,
        }
    case_row = query_one(
        """
        SELECT id, case_code, current_status, opened_at, closed_at,
               responsible_org_id, deadline AS case_deadline
        FROM e_closure_case
        WHERE source_table = 'water_protection_issue'
          AND source_record_id = %s
        LIMIT 1
        """,
        (issue_id,),
    )
    case_id = case_row["id"] if case_row else None

    # 3. 状态轨迹
    history: list[dict] = []
    if case_id:
        hist_rows = query_all(
            """
            SELECT from_status, to_status, action_code, action_at,
                   operator_name, operator_org_name, comment, transition_result
            FROM e_case_status_history
            WHERE case_id = %s
            ORDER BY action_at ASC
            """,
            (case_id,),
        )
        history = [
            {
                "fromStatus": r.get("from_status"),
                "toStatus": r["to_status"],
                "actionCode": r.get("action_code"),
                "actionAt": value_for_json(r.get("action_at")),
                "operatorName": r.get("operator_name") or "",
                "operatorOrgName": r.get("operator_org_name") or "",
                "comment": r.get("comment") or "",
                "transitionResult": r.get("transition_result") or "SUCCESS",
            }
            for r in hist_rows
        ]

    # 4. 参与方
    parties: list[dict] = []
    if case_id:
        party_rows = query_all(
            """
            SELECT party_role, org_name, user_name
            FROM e_case_party
            WHERE case_id = %s AND IFNULL(is_current, 1) = 1
            ORDER BY party_role
            """,
            (case_id,),
        )
        parties = [
            {
                "role": r["party_role"],
                "roleLabel": {
                    "DISCOVERER": "发现人",
                    "RESPONSIBLE": "责任单位",
                    "HANDLER": "处理人",
                    "REVIEWER": "复查人",
                    "CLOSER": "销项人",
                    "TEST_PROVIDER": "检测方",
                }.get(r["party_role"], r["party_role"]),
                "orgName": r.get("org_name") or "",
                "userName": r.get("user_name") or "",
            }
            for r in party_rows
        ]

    # 5. 证据
    evidence: list[dict] = []
    if case_id:
        ev_rows = query_all(
            """
            SELECT e.evidence_role, e.validity_status, e.created_at, e.document_id,
                   e.rectification_round_id, d.document_name, d.document_type, d.source_name
            FROM e_case_evidence e
            LEFT JOIN document_record d ON d.id = e.document_id
            WHERE e.case_id = %s AND e.validity_status = 'VALID'
            ORDER BY e.created_at ASC
            """,
            (case_id,),
        )
        evidence = [
            {
                "role": r["evidence_role"],
                "roleLabel": {
                    "FORMAL_NOTICE": "正式通知",
                    "INITIAL_REPORT": "初始报告",
                    "RAW_RECORD": "原始记录",
                    "RECTIFICATION_MATERIAL": "整改材料",
                    "RETEST_REPORT": "复测报告",
                    "REVIEW_OPINION": "复查意见",
                    "CLOSURE_DOCUMENT": "销项文件",
                    "CANCELLATION_DOCUMENT": "撤销文件",
                }.get(r["evidence_role"], r["evidence_role"]),
                "kind": r.get("document_type") or "",
                "title": r.get("document_name") or r.get("evidence_role") or "",
                "description": r.get("source_name") or "",
                "validityStatus": r.get("validity_status") or "VALID",
                "createdAt": value_for_json(r.get("created_at")),
                "rectificationRoundId": r.get("rectification_round_id"),
                "documentId": r.get("document_id"),
                "hasAttachment": bool(r.get("document_id")),
            }
            for r in ev_rows
        ]

    # 6. 材料完整度（E03：退回后整改 D07=3/4）
    material_completeness = _e03_material_completeness(
        case_row["current_status"] if case_row else None, history, evidence
    )

    # 7. GIS 关系（relation_code=业务键；source_id=台账主键）
    biz_code = row.get("business_code") or ""
    spatial_rows = query_all(
        """
        SELECT feature_id, relation_type, relation_name, source_id, relation_code
        FROM gis_feature_business_relation
        WHERE relation_type = 'E03_WATER_ISSUE'
          AND (source_id = %s OR relation_code = %s OR source_id = %s)
        """,
        (str(issue_id), biz_code, biz_code),
    )
    spatial_links = [
        {
            "featureId": r["feature_id"],
            "geometryType": "unknown",
            "role": "related",
            "isPrimary": True,
        }
        for r in spatial_rows
    ]

    # 8. 台账↔案卷一致性对账标记
    reconcile_warning = None
    if case_row and _e03_status_group(row.get("issue_status") or "") != _e03_case_status_group(case_row["current_status"]):
        reconcile_warning = "台账与案卷状态映射不一致"

    return {
        "code": 0,
        "data": {
            "id": row["id"],
            "businessCode": biz_code,
            "title": row.get("issue_name") or row.get("issue_type") or "",
            "issueType": row.get("issue_type") or "",
            "locationText": row.get("location_text") or "",
            "status": row.get("issue_status") or "",
            "statusGroup": _e03_status_group(row.get("issue_status") or ""),
            "overdue": bool(row.get("overdue")),
            "deadline": value_for_json(row.get("deadline")),
            "responsibleOrgName": row.get("responsible_org_name") or "",
            "foundDate": value_for_json(row.get("found_date")),
            "closedDate": value_for_json(row.get("closed_date")),
            "isDemo": bool(row.get("is_demo")),
            "dataNature": row.get("data_nature") or "formal",
            "description": row.get("description") or "",
            "discoveryBasis": row.get("discovery_basis") or "",
            "case": {
                "caseId": case_id,
                "caseCode": case_row["case_code"] if case_row else None,
                "caseStatus": case_row["current_status"] if case_row else None,
                "caseStatusGroup": _e03_case_status_group(case_row["current_status"]) if case_row else None,
                "openedAt": value_for_json(case_row["opened_at"]) if case_row else None,
                "closedAt": value_for_json(case_row["closed_at"]) if case_row else None,
            } if case_row else None,
            "history": history,
            "parties": parties,
            "evidence": evidence,
            "materialCompleteness": material_completeness,
            "spatialLinks": spatial_links,
            "reconcileWarning": reconcile_warning,
            "gisDisclaimer": "关联位置仅用于验证地图联动，不代表该位置真实发生此问题。" if bool(row.get("is_demo")) else None,
        },
    }


def get_e03_water_protection_detail() -> dict | None:
    """E03 旧详情接口（已弃用；P3 改走 /api/environment/e03/issues/{id}）"""
    # 旧接口仅返回正式数据，避免正式弹窗混 demo
    open_rows = query_all(
        """
        SELECT *
        FROM water_protection_issue
        WHERE issue_status <> '已闭环'
          AND is_demo = 0 AND data_nature = 'formal'
        ORDER BY overdue DESC, deadline, id
        """
    )
    if not open_rows:
        return None
    new_count = query_one(
        """
        SELECT COUNT(*) AS c
        FROM water_protection_issue
        WHERE issue_status <> '已闭环'
          AND is_demo = 0 AND data_nature = 'formal'
          AND found_date >= '2026-07-01'
          AND found_date < '2026-08-01'
        """
    )["c"]
    closed_count = query_one(
        """
        SELECT COUNT(*) AS c
        FROM water_protection_issue
        WHERE closed_date >= '2026-07-01'
          AND closed_date < '2026-08-01'
          AND is_demo = 0 AND data_nature = 'formal'
        """
    )["c"]
    overdue_count = sum(1 for row in open_rows if int(row.get("overdue") or 0) == 1 or row.get("issue_status") == "逾期未闭环")
    segment_count = len({row.get("segment_name") for row in open_rows if row.get("segment_name")})

    detail = with_snapshot_base("E03")
    detail.update(
        {
            "summary": [
                {"label": "当前未闭环", "value": len(open_rows), "unit": "项"},
                {"label": "本月新增未闭环", "value": int(new_count), "unit": "项"},
                {"label": "本月闭环", "value": int(closed_count), "unit": "项"},
                {"label": "逾期未闭环", "value": overdue_count, "unit": "项"},
                {"label": "涉及标段", "value": segment_count, "unit": "个"},
            ],
            "chartTitle": "各标段未闭环水保问题分布",
            "detailTitle": "未闭环水保问题明细",
            "detailColumns": [
                {"key": "name", "label": "问题名称", "width": "20%"},
                {"key": "segment", "label": "所属标段", "width": "10%"},
                {"key": "category", "label": "问题类型", "width": "10%"},
                {"key": "time", "label": "发现时间", "width": "11%"},
                {"key": "department", "label": "责任部门", "width": "14%"},
                {"key": "deadline", "label": "整改截止", "width": "11%"},
                {"key": "mainStatus", "label": "办理状态", "width": "12%"},
                {"key": "deadlineStatus", "label": "时限状态", "width": "12%"},
            ],
            "detailData": [
                {
                    "id": int(row["id"]),
                    "name": row.get("issue_name") or row.get("issue_type") or "水保问题",
                    "segment": row.get("segment_name") or "",
                    "category": row.get("issue_type") or "",
                    "time": value_for_json(row.get("found_date")),
                    "department": row.get("responsible_department") or "",
                    "deadline": value_for_json(row.get("deadline")),
                    "mainStatus": "未闭环" if int(row.get("overdue") or 0) == 1 or row.get("issue_status") == "逾期未闭环" else (row.get("issue_status") or "未闭环"),
                    "overdue": bool(row.get("overdue")),
                    "deadlineStatus": "已逾期" if int(row.get("overdue") or 0) == 1 else "正常",
                    "statusStageKnown": not (int(row.get("overdue") or 0) == 1 or row.get("issue_status") == "逾期未闭环"),
                }
                for row in open_rows
            ],
            "dataSource": "水保问题明细表 water_protection_issue",
            "updateTime": "2026-07-13 08:30",
            "isMock": False,
        }
    )
    return detail


def get_e04_carbon_emission_detail() -> dict | None:
    # P2.3: 边界版本 / 批次 / 因子快照 / 数据质量 / 候选对照
    # 1. 获取当前演示批次（闸控制）
    e04_scope_clause = "AND is_demo = 1 AND data_nature = 'demo'" if E04_ALLOW_DEMO else "AND is_demo = 0 AND data_nature = 'formal'"
    batch_row = query_one(
        f"""
        SELECT id, batch_code, batch_label, boundary_version, statistics_as_of,
               period_start, period_end, data_nature, is_current, is_demo,
               verification_status, boundary_snapshot_note
        FROM carbon_accounting_batch
        WHERE is_current = 1 {e04_scope_clause}
        LIMIT 1
        """
    )
    boundary_version = None
    batch_id = None
    statistics_as_of = None
    batch_data_nature = "demo" if E04_ALLOW_DEMO else "formal"
    batch_verification = "PENDING"
    if batch_row:
        boundary_version = batch_row["boundary_version"]
        batch_id = int(batch_row["id"])
        statistics_as_of = value_for_json(batch_row["statistics_as_of"])
        batch_data_nature = batch_row["data_nature"]
        batch_verification = batch_row.get("verification_status") or "PENDING"
    elif not E04_ALLOW_DEMO:
        # 正式环境无正式批次 → 返回空壳（不混 demo）
        # P3.3: 检查是否存在演示批次，以区分「无数据」与「无权 demo」
        demo_batch_exists = query_one(
            "SELECT 1 FROM carbon_accounting_batch WHERE is_demo = 1 AND data_nature = 'demo' AND is_current = 1 LIMIT 1"
        )
        detail = with_snapshot_base("E04")
        detail.update({
            "summary": [
                {"label": "累计碳排放", "value": None, "unit": "tCO₂e"},
                {"label": "数据性质", "value": "暂无正式数据"},
                {"label": "核验状态", "value": "未核验"},
            ],
            "detailData": [],
            "monthlyData": [],
            "materialDetails": [],
            "dataNature": "formal",
            "isMock": False,
            "scope": "formal",
            "completeness": "暂无正式已核验数据",
            "completenessStatus": "empty",
            "demoDenied": bool(demo_batch_exists),
        })
        return detail

    # 2. 获取边界配置（in_boundary 来源表）
    boundary_rows = query_all(
        """
        SELECT source_code, source_label, in_boundary, sort_order, description
        FROM carbon_accounting_boundary
        WHERE boundary_version = %s
        ORDER BY sort_order
        """,
        (boundary_version,),
    ) if boundary_version else []
    boundary_map = {row["source_code"]: row for row in boundary_rows}

    # 3. 获取因子快照
    snapshot_rows = query_all(
        """
        SELECT id, snapshot_code, factor_id, factor_code, factor_name,
               factor_value, factor_unit, factor_version, factor_source,
               data_nature
        FROM carbon_emission_factor_snapshot
        WHERE snapshot_code LIKE 'E04-SNAP-%%'
        """
    )
    snapshot_by_factor_code = {row["factor_code"]: row for row in snapshot_rows}
    snapshot_by_id = {int(row["id"]): row for row in snapshot_rows}

    rows = query_all(
        f"""
        SELECT *
        FROM carbon_emission_activity
        WHERE 1=1 {e04_scope_clause}
          AND is_current = 1
          AND effective_status = 'EFFECTIVE'
        ORDER BY period_value, id
        """
    )
    if not rows:
        return None

    # P2.5: 使用 Decimal 精度（先 SUM 未舍入中间量，再 ROUND_HALF_UP 至 2 位）
    total_emission_dec = sum((Decimal(str(row.get("carbon_emission") or 0)) for row in rows), Decimal("0"))
    total_emission = float(total_emission_dec.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))
    current_month = next((row for row in reversed(rows) if row.get("period_value") == "2026-07"), rows[-1])
    month_emission_dec = Decimal(str(current_month.get("carbon_emission") or 0))
    month_emission = float(month_emission_dec.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))

    factors = {
        row["factor_code"]: row
        for row in query_all(
            """
            SELECT id, factor_code, factor_name, factor_value, factor_unit,
                   factor_version, factor_source, data_nature, verification_status,
                   evidence_document_id
            FROM carbon_emission_factor
            WHERE factor_version='DEMO-EF-2026-v0.1'
            """
        )
    }
    # 运输因子可保留在库中，但当前 KPI 边界不要求其存在
    required_factor_codes = {
        "DEMO_DIESEL", "DEMO_ELECTRICITY", "DEMO_CEMENT",
        "DEMO_STEEL", "DEMO_ASPHALT",
    }
    if not required_factor_codes.issubset(factors):
        return None

    # 4. 材料明细（仅当前有效月份）
    material_nature = "demo" if E04_ALLOW_DEMO else "formal"
    material_is_demo = 1 if E04_ALLOW_DEMO else 0
    material_rows = query_all(
        """
        SELECT m.id, m.period_value, m.material_name, m.material_usage, m.material_unit,
               m.carbon_activity_id, m.carbon_emission, m.document_id,
               m.data_nature, m.verification_status, m.effective_status,
               m.evidence_status, m.factor_snapshot_id, m.accounting_batch_id,
               f.factor_name, f.factor_value, f.factor_unit, f.factor_version, f.factor_source
        FROM carbon_material_usage m
        JOIN carbon_emission_factor f ON f.id=m.emission_factor_id
        WHERE m.is_current = 1
          AND m.effective_status = 'EFFECTIVE'
          AND m.data_nature = %s
          AND m.is_demo = %s
        ORDER BY m.period_value, m.id
        """,
        (material_nature, material_is_demo),
    )
    material_groups: dict[str, dict] = {}
    for row in material_rows:
        snap = snapshot_by_id.get(int(row["factor_snapshot_id"])) if row.get("factor_snapshot_id") else None
        group = material_groups.setdefault(
            row["material_name"],
            {
                "material": row["material_name"],
                "activityValue": Decimal("0"),
                "activityUnit": row.get("material_unit") or "t",
                "emissionFactor": float(row.get("factor_value") or 0),
                "factorUnit": row.get("factor_unit") or "",
                "emission": Decimal("0"),
                "factorName": row.get("factor_name") or "",
                "factorVersion": row.get("factor_version") or "",
                "factorSource": row.get("factor_source") or "",
                "factorSnapshotId": int(row["factor_snapshot_id"]) if row.get("factor_snapshot_id") else None,
                "factorSnapshotCode": snap["snapshot_code"] if snap else None,
                "dataNature": row.get("data_nature") or "demo",
                "verificationStatus": row.get("verification_status") or "待业务核验",
                "effectiveStatus": row.get("effective_status") or "EFFECTIVE",
                "evidenceStatus": row.get("evidence_status") or "MISSING",
                "monthlyData": [],
            },
        )
        activity_value = Decimal(str(row.get("material_usage") or 0))
        emission_value = Decimal(str(row.get("carbon_emission") or 0))
        group["activityValue"] += activity_value
        group["emission"] += emission_value
        group["monthlyData"].append(
            {
                "period": row.get("period_value") or "",
                "activityValue": float(activity_value.quantize(Decimal("0.00000001"), rounding=ROUND_HALF_UP)),
                "emission": float(emission_value.quantize(Decimal("0.000001"), rounding=ROUND_HALF_UP)),
            }
        )

    material_details = []
    for name in ("水泥", "钢材", "沥青"):
        item = material_groups.get(name)
        if item:
            item["activityValue"] = float(item["activityValue"].quantize(Decimal("0.00000001"), rounding=ROUND_HALF_UP))
            item["emission"] = float(item["emission"].quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))
            material_details.append(item)

    # 5. 来源行（含 in_boundary / 因子快照 / 数据质量）
    def source_item(
        code: str,
        source: str,
        activity_value: float,
        activity_unit: str,
        emission: float,
        factor_code: str | None,
        material_details_value: list[dict] | None = None,
    ) -> dict:
        factor = factors.get(factor_code or "")
        snap = snapshot_by_factor_code.get(factor_code) if factor_code else None
        # 从边界配置获取 in_boundary 标志
        bd = boundary_map.get(code)
        in_boundary = bool(bd["in_boundary"]) if bd else True  # 默认计入
        evidence_status = "MISSING"
        if material_details_value is not None:
            if any(d.get("evidenceStatus") != "MISSING" for d in material_details_value):
                evidence_status = "PENDING"
        item = {
            "sourceCode": code,
            "source": source,
            "inBoundary": in_boundary,
            "activityValue": round(activity_value, 8),
            "activityUnit": activity_unit,
            "emissionFactor": float(factor["factor_value"]) if factor else None,
            "factorUnit": factor.get("factor_unit") if factor else "分项核算",
            "factorName": factor.get("factor_name") if factor else "主要材料分项演示排放因子",
            "factorSnapshotId": int(snap["id"]) if snap else None,
            "factorSnapshotCode": snap["snapshot_code"] if snap else None,
            "emission": round(emission, 2),
            "share": round(emission / total_emission * 100, 2) if total_emission else 0,
            "factorVersion": factor.get("factor_version") if factor else "DEMO-EF-2026-v0.1",
            "factorSource": factor.get("factor_source") if factor else "系统演示测试数据，非正式核算依据",
            "dataNature": factor.get("data_nature") if factor else "demo",
            "verificationStatus": factor.get("verification_status") if factor else "待业务核验",
            "effectiveStatus": "EFFECTIVE",
            "evidenceStatus": evidence_status,
        }
        if material_details_value is not None:
            item["materialDetails"] = material_details_value
        return item

    source_rows = [
        source_item(
            "diesel", "施工用油",
            float(sum((Decimal(str(row.get("diesel_usage") or 0)) for row in rows), Decimal("0")).quantize(Decimal("0.00000001"), rounding=ROUND_HALF_UP)), "L",
            float(sum((Decimal(str(row.get("diesel_emission") or 0)) for row in rows), Decimal("0")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)), "DEMO_DIESEL",
        ),
        source_item(
            "electricity", "施工用电",
            float(sum((Decimal(str(row.get("electricity_usage") or 0)) for row in rows), Decimal("0")).quantize(Decimal("0.00000001"), rounding=ROUND_HALF_UP)), "kWh",
            float(sum((Decimal(str(row.get("electricity_emission") or 0)) for row in rows), Decimal("0")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)), "DEMO_ELECTRICITY",
        ),
        source_item(
            "material", "主要材料",
            float(sum((Decimal(str(row.get("material_usage") or 0)) for row in rows), Decimal("0")).quantize(Decimal("0.00000001"), rounding=ROUND_HALF_UP)), "t",
            float(sum((Decimal(str(row.get("material_emission") or 0)) for row in rows), Decimal("0")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)), None, material_details,
        ),
    ]
    # 运输：甲方暂不纳入 — 仅当边界配置为计入时才进入来源表；默认剔除
    transport_bd = boundary_map.get("transport")
    if transport_bd and bool(transport_bd["in_boundary"]):
        source_rows.append(
            source_item(
                "transport", "施工运输",
                float(sum((Decimal(str(row.get("transport_usage") or 0)) for row in rows), Decimal("0")).quantize(Decimal("0.00000001"), rounding=ROUND_HALF_UP)), "t·km",
                float(sum((Decimal(str(row.get("other_emission") or 0)) for row in rows), Decimal("0")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)), "DEMO_TRANSPORT",
            )
        )

    # 6. 月度趋势（Decimal 精度）
    cumulative_dec = Decimal("0")
    monthly_data = []
    for row in rows:
        monthly_dec = Decimal(str(row.get("carbon_emission") or 0))
        cumulative_dec += monthly_dec
        monthly_data.append(
            {
                "period": row.get("period_value") or "",
                "monthlyEmission": float(monthly_dec.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)),
                "cumulativeEmission": float(cumulative_dec.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)),
            }
        )

    # P3.3: 月份缺口检测
    monthly_gaps = []
    if len(monthly_data) >= 2:
        import datetime as _dt
        periods = []
        for item in monthly_data:
            p = item.get("period") or ""
            if len(p) >= 7:
                try:
                    periods.append(_dt.date(int(p[:4]), int(p[5:7]), 1))
                except (ValueError, IndexError):
                    pass
        if len(periods) >= 2:
            periods.sort()
            current = periods[0]
            while current < periods[-1]:
                next_month = current.replace(day=1) + _dt.timedelta(days=32)
                next_month = next_month.replace(day=1)
                if next_month not in periods:
                    monthly_gaps.append(next_month.strftime("%Y-%m"))
                current = next_month

    period_start = str(rows[0].get("period_value") or "")
    period_end = str(rows[-1].get("period_value") or "")
    period_label = (
        f"{period_start[:4]}年{int(period_start[5:7])}月—{int(period_end[5:7])}月"
        if len(period_start) >= 7 and len(period_end) >= 7
        else f"{period_start}—{period_end}"
    )
    latest_update = max(
        (row.get("updated_at") or row.get("created_at") for row in rows),
        default=None,
    )

    detail = with_snapshot_base("E04")
    detail.update(
        {
            "summary": [
                {"label": "累计碳排放", "value": round(total_emission, 2), "unit": "tCO₂e"},
                {"label": "本期排放", "value": round(month_emission, 2), "unit": "tCO₂e"},
                {"label": "核算期间", "value": period_label},
                {"label": "统计起点", "value": "2026-05-08"},
            ],
            "chartTitle": "月度排放与累计碳排放",
            "detailTitle": "排放来源核算汇总",
            "detailColumns": [
                {"key": "source", "label": "排放来源", "width": "16%"},
                {"key": "activityValue", "label": "活动数据", "width": "22%"},
                {"key": "emissionFactor", "label": "排放因子", "width": "24%"},
                {"key": "emission", "label": "排放量", "width": "14%"},
                {"key": "share", "label": "占比", "width": "10%"},
                {"key": "verificationStatus", "label": "核验状态", "width": "14%"},
            ],
            "detailData": source_rows,
            "monthlyData": monthly_data,
            "materialDetails": material_details,
            "accountingBoundary": [b["source_label"] for b in boundary_rows if b["in_boundary"]] if boundary_rows else ["施工用油", "施工用电", "主要材料"],
            "accountingBatchId": batch_id,
            "statisticsAsOf": statistics_as_of or period_end,
            "statisticsStart": "2026-05-08",
            "scope": "demo" if E04_ALLOW_DEMO else "formal",
            "verificationStatus": batch_verification,
            "dataSource": "碳排放活动明细表 carbon_emission_activity；材料用量表 carbon_material_usage；排放因子表 carbon_emission_factor；边界配置 carbon_accounting_boundary",
            "updateTime": value_for_json(latest_update),
            "completeness": "待业务核验" if E04_ALLOW_DEMO else "暂无正式已核验数据",
            "completenessStatus": "pending" if E04_ALLOW_DEMO else "empty",
            "monthlyGaps": monthly_gaps,
            "isMock": False,
        }
    )
    return detail


def get_carbon_topic_detail() -> dict | None:
    enhanced = get_carbon_benefit_overview()
    if enhanced is not None:
        return enhanced

    rows = query_all(
        """
        SELECT *
        FROM carbon_emission_activity
        ORDER BY period_value, id
        """
    )
    if not rows:
        return None

    base = get_dashboard_topic_snapshot("carbon")
    if base is None:
        base = {
            "key": "CARBON",
            "fullName": "碳足迹与低碳增益",
            "theme": "green",
            "isTopic": True,
            "topicData": {},
        }

    months = [row.get("period_value") for row in rows]
    actual_data = [round(float(row.get("carbon_emission") or 0)) for row in rows]
    baseline_data = [round(float(row.get("baseline_emission") or 0)) for row in rows]
    cumulative_data: list[int] = []
    running_total = 0
    for value in actual_data:
        running_total += value
        cumulative_data.append(running_total)

    total_emission = sum(actual_data)
    baseline_total = sum(baseline_data)
    reduction = round(baseline_total - total_emission)
    reduction_rate = round((baseline_total - total_emission) / baseline_total * 100, 1) if baseline_total else 0
    output_total = sum(float(row.get("output_value_wan") or 0) for row in rows)
    intensity = round(total_emission / output_total, 3) if output_total else 0
    month_emission = actual_data[-1] if actual_data else 0

    source_values = [
        ("施工用油", sum(float(row.get("diesel_emission") or 0) for row in rows), "#2f9cff", "↓ 2.3%", "柴油消耗优化"),
        ("施工用电", sum(float(row.get("electricity_emission") or 0) for row in rows), "#69e36f", "↑ 1.1%", "隧道掘进增加"),
        ("主要材料", sum(float(row.get("material_emission") or 0) for row in rows), "#a66cff", "↓ 3.5%", "低碳材料替代"),
        ("施工运输", sum(float(row.get("other_emission") or 0) for row in rows), "#ffb347", "↑ 0.8%", "系统演示测试数据，非正式核算依据"),
    ]
    source_summary = [
        {"label": name, "value": round(value), "unit": "tCO₂e"}
        for name, value, *_ in source_values
    ]
    source_items = [
        {"name": name, "value": round(value / total_emission * 100, 1) if total_emission else 0, "color": color}
        for name, value, color, *_ in source_values
    ]
    source_detail = [
        {
            "source": name,
            "value": f"{round(value):,} tCO₂e",
            "proportion": f"{round(value / total_emission * 100, 1) if total_emission else 0}%",
            "trend": trend,
            "note": note,
        }
        for name, value, _color, trend, note in source_values
    ]

    factor_rows = query_all(
        """
        SELECT factor_code, factor_name, factor_value, factor_unit, factor_version,
               factor_source, data_nature, verification_status,
               CASE WHEN evidence_document_id IS NULL THEN '未关联' ELSE '已关联' END AS evidence_status
        FROM carbon_emission_factor
        WHERE factor_code LIKE 'DEMO_%%'
        ORDER BY id
        """
    )
    factor_by_code = {row["factor_code"]: row for row in factor_rows}
    material_rows = query_all(
        """
        SELECT m.material_name, SUM(m.material_usage) AS activity_value,
               MAX(m.material_unit) AS activity_unit, SUM(m.carbon_emission) AS emission,
               f.factor_name, f.factor_value, f.factor_unit, f.factor_version,
               f.factor_source, m.data_nature, m.verification_status,
               CASE WHEN f.evidence_document_id IS NULL THEN '未关联' ELSE '已关联' END AS evidence_status
        FROM carbon_material_usage m
        LEFT JOIN carbon_emission_factor f ON f.id = m.emission_factor_id
        GROUP BY m.material_name, f.factor_name, f.factor_value, f.factor_unit,
                 f.factor_version, f.factor_source, m.data_nature,
                 m.verification_status, f.evidence_document_id
        ORDER BY FIELD(m.material_name, '水泥', '钢材', '沥青'), m.material_name
        """
    )
    material_breakdown = [
        {
            "material": row["material_name"],
            "activityValue": round(float(row["activity_value"] or 0), 2),
            "activityUnit": row["activity_unit"],
            "emissionFactor": float(row["factor_value"] or 0),
            "factorUnit": row["factor_unit"],
            "emission": round(float(row["emission"] or 0)),
            "factorName": row["factor_name"],
            "factorVersion": row["factor_version"],
            "factorSource": row["factor_source"],
            "dataNature": row["data_nature"],
            "verificationStatus": row["verification_status"],
            "evidenceStatus": row["evidence_status"],
        }
        for row in material_rows
    ]
    activity_totals = query_one(
        """
        SELECT SUM(diesel_usage) diesel_usage, SUM(electricity_usage) electricity_usage,
               SUM(material_usage) material_usage, SUM(transport_usage) transport_usage
        FROM carbon_emission_activity
        """
    ) or {}
    source_codes = (
        ("diesel", "施工用油", "diesel_usage", "L", "DEMO_DIESEL", 5628),
        ("electricity", "施工用电", "electricity_usage", "kWh", "DEMO_ELECTRICITY", 3857),
        ("material", "主要材料", "material_usage", "t", None, 2486),
        ("transport", "施工运输", "transport_usage", "t·km", "DEMO_TRANSPORT", 885),
    )
    emission_sources = []
    for code, name, activity_field, activity_unit, factor_code, emission in source_codes:
        factor = factor_by_code.get(factor_code or "", {})
        emission_sources.append(
            {
                "sourceCode": code,
                "source": name,
                "activityValue": round(float(activity_totals.get(activity_field) or 0), 2),
                "activityUnit": activity_unit,
                "emissionFactor": float(factor["factor_value"]) if factor else None,
                "factorUnit": factor.get("factor_unit") or "分项核算",
                "factorName": factor.get("factor_name") or "主要材料分项演示排放因子",
                "emission": emission,
                "share": round(emission / total_emission * 100, 1),
                "factorVersion": factor.get("factor_version") or "DEMO-EF-2026-v0.1",
                "dataNature": "demo",
                "verificationStatus": "待业务核验",
                "evidenceStatus": factor.get("evidence_status") or "未关联",
                "materialDetails": material_breakdown if code == "material" else [],
            }
        )

    accounting_rows = query_all(
        """
        SELECT accounting_code, accounting_month, boundary_code, baseline_emission,
               actual_emission, accounted_reduction, unit, data_nature,
               verification_status, evidence_status
        FROM carbon_reduction_accounting
        WHERE is_demo = 1
        ORDER BY accounting_month, id
        """
    )
    measures = query_all(
        """
        SELECT measure_code, measure_name, measure_category, application_scope,
               responsible_department, implementation_status, estimated_reduction,
               accounted_reduction, verified_reduction, reduction_unit,
               investment_cost, operating_saving, avoided_cost, net_cost_impact,
               currency_unit, data_nature, verification_status, evidence_status
        FROM carbon_reduction_measure
        WHERE is_demo = 1
        ORDER BY measure_code
        """
    )
    accounting_detail = [
        {
            "accountingCode": row["accounting_code"],
            "month": row["accounting_month"],
            "boundaryCode": row["boundary_code"],
            "baselineEmission": float(row["baseline_emission"]),
            "actualEmission": float(row["actual_emission"]),
            "accountedReduction": float(row["accounted_reduction"]),
            "unit": row["unit"],
            "dataNature": row["data_nature"],
            "verificationStatus": row["verification_status"],
            "evidenceStatus": row["evidence_status"],
        }
        for row in accounting_rows
    ]
    measure_detail = [
        {
            "measureCode": row["measure_code"],
            "measureName": row["measure_name"],
            "category": row["measure_category"],
            "scope": row["application_scope"],
            "department": row["responsible_department"],
            "status": row["implementation_status"],
            "estimatedReduction": float(row["estimated_reduction"] or 0),
            "accountedReduction": value_for_json(row["accounted_reduction"]),
            "verifiedReduction": value_for_json(row["verified_reduction"]),
            "reductionUnit": row["reduction_unit"],
            "investmentCost": float(row["investment_cost"] or 0),
            "operatingSaving": float(row["operating_saving"] or 0),
            "avoidedCost": float(row["avoided_cost"] or 0),
            "netCostImpact": float(row["net_cost_impact"] or 0),
            "currencyUnit": row["currency_unit"],
            "dataNature": row["data_nature"],
            "verificationStatus": row["verification_status"],
            "evidenceStatus": row["evidence_status"],
        }
        for row in measures
    ]
    measure_estimated_total = round(sum(item["estimatedReduction"] for item in measure_detail))
    cost_summary = {
        "investmentCost": round(sum(item["investmentCost"] for item in measure_detail), 2),
        "operatingSaving": round(sum(item["operatingSaving"] for item in measure_detail), 2),
        "avoidedCost": round(sum(item["avoidedCost"] for item in measure_detail), 2),
        "totalCostSaving": round(
            sum(item["operatingSaving"] + item["avoidedCost"] for item in measure_detail), 2
        ),
        "netCostImpact": round(sum(item["netCostImpact"] for item in measure_detail), 2),
        "currencyUnit": "万元",
        "formula": "低碳措施节约成本 = 预计运行费用节约 + 预计材料、运输及处置支出减少",
        "netCostFormula": "净成本影响 = 低碳措施预计投入 - 低碳措施节约成本",
        "scopeAligned": True,
        "notice": "演示测算，非财务确认结果。",
    }

    summary = [
        {"label": "施工阶段累计碳足迹", "value": total_emission, "unit": "tCO₂e"},
        {"label": "累计核算减排量", "value": reduction, "unit": "tCO₂e"},
        {"label": "低碳措施节约成本", "value": cost_summary["totalCostSaving"], "unit": "万元"},
    ]

    topic_data = base.get("topicData") or {}
    cumulative = topic_data.get("cumulative") or {}
    cumulative.update(
        {
            "chartTitle": "月度排放与累计碳足迹趋势",
            "summary": [
                {"label": "施工阶段累计碳足迹", "value": total_emission, "unit": "tCO₂e"},
                {"label": "本月新增", "value": month_emission, "unit": "tCO₂e"},
                {"label": "较基准下降", "value": reduction_rate, "unit": "%"},
                {"label": "单位产值排放", "value": intensity, "unit": "tCO₂e/万元"},
            ],
            "months": months,
            "monthlyData": actual_data,
            "cumulativeData": cumulative_data,
            "boundary": "当前演示核算边界包括施工用油、施工用电、主要材料和施工运输；活动数据及排放因子均为系统演示测试数据，非正式核算依据。",
        }
    )
    benefit = topic_data.get("benefit") or {}
    benefit.update(
        {
            "chartTitle": "基准方案与实际排放对比",
            "summary": [
                {"label": "累计核算减排量", "value": reduction, "unit": "tCO₂e"},
                {"label": "较基准下降", "value": reduction_rate, "unit": "%"},
                {"label": "预计全年减排", "value": round(reduction / max(len(months), 1) * 12), "unit": "tCO₂e"},
                {"label": "减排贡献率", "value": 12.5, "unit": "%"},
            ],
            "months": months,
            "actualData": actual_data,
            "baselineData": baseline_data,
            "totalReduction": reduction,
            "reductionRate": reduction_rate,
            "note": "当前基准与实际排放均为系统演示测试数据，尚未作为正式核算依据。",
        }
    )
    source = topic_data.get("source") or {}
    source.update(
        {
            "chartTitle": "碳排放来源构成",
            "items": source_items,
            "summary": source_summary,
            "detailData": source_detail,
        }
    )
    overview = {
        "summary": [
            {"label": "项目累计碳排放", "value": total_emission, "unit": "tCO₂e"},
            {"label": "本月碳排放", "value": month_emission, "unit": "tCO₂e"},
            {"label": "累计核算减排量", "value": reduction, "unit": "tCO₂e"},
            {"label": "在施低碳措施", "value": len(measure_detail), "unit": "项"},
            {"label": "数据核验状态", "value": "待业务核验"},
        ],
        "monthlyEmissions": [
            {"month": month, "monthlyEmission": actual, "cumulativeEmission": cumulative_data[index]}
            for index, (month, actual) in enumerate(zip(months, actual_data))
        ],
        "emissionSources": emission_sources,
        "accountingBoundary": "DEMO-CONSTRUCTION-E04",
        "dataQuality": {"dataNature": "demo", "verificationStatus": "待业务核验", "evidenceStatus": "未关联"},
    }
    sources_page = {
        "rows": emission_sources,
        "materialBreakdown": material_breakdown,
        "factorMetadata": [
            {key: value_for_json(value) for key, value in row.items()}
            for row in factor_rows
        ],
        "totalEmission": total_emission,
    }
    benefit.update(
        {
            "accountingRows": accounting_detail,
            "baselineTotal": baseline_total,
            "actualTotal": total_emission,
            "accountedReduction": reduction,
            "measureEstimatedReduction": measure_estimated_total,
            "verifiedReduction": None,
            "formula": "核算减排量 = 同口径基准排放 - 实际排放",
            "separationNotice": "措施预计减排量与核算减排量属于不同评价路径，不直接相加。",
        }
    )
    measures_costs = {"measures": measure_detail, "costSummary": cost_summary}
    topic_data.update(
        {
            "overview": overview,
            "sources": sources_page,
            "benefit": benefit,
            "measuresCosts": measures_costs,
            # 兼容旧组件读取，数据仍来自本次 MySQL 聚合。
            "cumulative": cumulative,
            "source": source,
            "cost": {
                "investment": cost_summary["investmentCost"],
                "savings": cost_summary["operatingSaving"],
                "avoidedCost": cost_summary["avoidedCost"],
                "totalCostSaving": cost_summary["totalCostSaving"],
                "netCostImpact": cost_summary["netCostImpact"],
                "note": cost_summary["notice"],
            },
        }
    )

    base.update(
        {
            "tabs": [
                {"key": "overview", "label": "碳排概览"},
                {"key": "sources", "label": "排放来源"},
                {"key": "benefit", "label": "低碳增益"},
                {"key": "measures-costs", "label": "措施与成本"},
            ],
            "summary": summary,
            "carbonCostLabel": "低碳措施节约成本",
            "carbonCostValue": cost_summary["totalCostSaving"],
            "carbonCostUnit": "万元",
            "topicData": topic_data,
            "detailData": source_detail,
            "dataSource": "MySQL：carbon_emission_activity / carbon_emission_factor / carbon_material_usage / carbon_reduction_accounting / carbon_reduction_measure",
            "sourceMode": "mysql",
            "dataNature": "demo",
            "verificationStatus": "待业务核验",
            "evidenceStatus": "未关联",
            "updateTime": value_for_json(max((row.get("updated_at") for row in rows if row.get("updated_at")), default=None)),
            "isMock": False,
        }
    )
    return base


def get_monthly_report_topic_detail() -> dict | None:
    overview = get_monthly_report_overview()
    if overview is not None:
        base = get_dashboard_topic_snapshot("monthly-report") or {
            "key": "MONTHLY",
            "fullName": "月报准备与输出",
            "theme": "blue",
            "isTopic": True,
        }
        summary_data = overview["summary"]
        summary = [
            {"label": "资料归集率", "value": overview["readinessRate"], "unit": "%"},
            {"label": "已归集", "value": f"{summary_data['collectedCount']}/{summary_data['totalCount']}", "unit": "项"},
            {"label": "待处理", "value": summary_data["pendingTotal"], "unit": "项"},
            {"label": "输出状态", "value": overview["outputStatus"]["label"], "unit": ""},
        ]
        progress_groups = [
            {
                "key": item["groupCode"],
                "label": f"{item['groupCode']}组",
                "value": item["progress"],
                "collectedCount": item["collectedCount"],
                "totalCount": item["totalCount"],
                "color": {"E": "#69e36f", "S": "#2f9cff", "G": "#a66cff"}[item["groupCode"]],
            }
            for item in overview["groupProgress"]
        ]
        task_list = [
            {
                "id": item["id"],
                "taskCode": item["taskCode"],
                "group": item["groupCode"],
                "name": item["taskName"],
                "type": item["taskTypeLabel"],
                "status": item["status"],
                "owner": item["responsibleDepartment"],
                "responsibleRole": item["responsibleRole"],
                "person": item["responsibleUserName"],
                "deadline": item["deadline"],
            }
            for item in overview["taskInstances"]
        ]
        pending_list = [
            {
                "id": item["id"],
                "taskCode": item["taskCode"],
                "name": item["taskName"],
                "group": item["groupCode"],
                "owner": item["responsibleRole"],
                "deadline": item["deadline"],
                "status": item["status"],
                "note": item["issueDescription"],
                "requirement": item["requirement"],
                "nextActionType": item["nextActionType"],
            }
            for item in overview["pendingTasks"]
        ]
        base.update(
            {
                "summary": summary,
                "topicData": {
                    "overview": overview,
                    "progress": {"summary": summary, "groups": progress_groups},
                    "chapters": {"list": task_list},
                    "statusChain": overview["processStages"],
                },
                "detailData": pending_list,
                "dataSource": "MySQL：monthly_report_task_instance / monthly_report_task_material_link / monthly_report_task_validation",
                "updateTime": overview["updatedAt"],
                "completeness": f"{overview['readinessRate']}%",
                "sourceMode": overview["sourceMode"],
                "dataNature": overview["dataNature"],
                "isMock": overview["isMock"],
            }
        )
        return base

    cycle = query_one(
        """
        SELECT *
        FROM monthly_report_cycle
        ORDER BY report_period DESC, id DESC
        LIMIT 1
        """
    )
    if cycle is None:
        return None

    cycle_id = cycle["id"]
    groups = query_all(
        """
        SELECT *
        FROM monthly_report_group_progress
        WHERE cycle_id = %s
        ORDER BY FIELD(group_code, 'E', 'S', 'G'), id
        """,
        (cycle_id,),
    )
    chapters = query_all(
        """
        SELECT *
        FROM monthly_report_chapter
        WHERE cycle_id = %s
        ORDER BY chapter_index, id
        """,
        (cycle_id,),
    )
    gaps = query_all(
        """
        SELECT *
        FROM monthly_report_gap
        WHERE cycle_id = %s
        ORDER BY FIELD(group_name, 'E组', 'S组', 'G组'), deadline, id
        """,
        (cycle_id,),
    )
    chain = query_all(
        """
        SELECT *
        FROM monthly_report_status_chain
        WHERE cycle_id = %s
        ORDER BY display_order, id
        """,
        (cycle_id,),
    )

    base = get_dashboard_topic_snapshot("monthly-report")
    if base is None:
        base = {
            "key": "MONTHLY",
            "fullName": "月报准备与输出",
            "theme": "blue",
            "isTopic": True,
            "topicData": {},
        }

    pending_confirm = sum(1 for row in gaps if row.get("status") == "待确认") + sum(1 for row in chapters if row.get("status") == "待确认")
    summary = [
        {"label": "月报完成度", "value": int(round(float(cycle.get("completion_rate") or 0))), "unit": "%"},
        {"label": "待补资料", "value": len(gaps), "unit": "项"},
        {"label": "待确认", "value": pending_confirm, "unit": "项"},
        {"label": "预计完成", "value": cycle.get("expected_complete_date") or "", "unit": ""},
    ]

    group_items = [
        {
            "key": row.get("group_code"),
            "label": row.get("group_label"),
            "value": int(round(float(row.get("completion_rate") or 0))),
            "color": row.get("color") or "#2f9cff",
        }
        for row in groups
    ]
    chapter_items = [
        {
            "index": row.get("chapter_index"),
            "group": row.get("group_name") or "",
            "name": row.get("chapter_name") or "",
            "type": row.get("material_type") or "",
            "status": row.get("status") or "",
            "owner": row.get("owner") or "",
            "person": row.get("responsible_person") or "",
            "deadline": row.get("deadline") or "",
        }
        for row in chapters
    ]
    gap_items = [
        {
            "name": row.get("material_name") or "",
            "group": row.get("group_name") or "",
            "owner": row.get("owner") or "",
            "deadline": row.get("deadline") or "",
            "status": row.get("status") or "",
            "note": row.get("note") or "",
        }
        for row in gaps
    ]
    chain_items = [
        {
            "key": row.get("chain_key"),
            "label": row.get("label"),
            "status": row.get("status"),
        }
        for row in chain
    ]

    topic_data = base.get("topicData") or {}
    progress = topic_data.get("progress") or {}
    progress.update({"summary": summary, "groups": group_items})
    chapters_topic = topic_data.get("chapters") or {}
    chapters_topic.update({"list": chapter_items})
    topic_data.update(
        {
            "progress": progress,
            "chapters": chapters_topic,
            "statusChain": chain_items,
        }
    )

    base.update(
        {
            "summary": summary,
            "topicData": topic_data,
            "detailData": gap_items,
            "dataSource": "月报编制业务表 monthly_report_cycle / monthly_report_gap",
            "updateTime": value_for_json(cycle.get("update_time"))[:16] if cycle.get("update_time") else "2026-07-13 10:00",
            "completeness": f"{int(round(float(cycle.get('completion_rate') or 0)))}%",
            "isMock": False,
        }
    )
    return base


def _s02_source_id(row: dict) -> str:
    row_id = int(row.get("id") or 0)
    if 430001 <= row_id <= 439999:
        return f"S02-{row_id - 430000:03d}"
    return f"S02-{row_id}"


# S02 GIS 挂接：主/辅要素（与 TrafficGisOverview S02_FEATURE_IDS / seed_s02_risk_display_v0_2 对齐）
_S02_GIS_LINKS: dict[str, list[tuple[str, bool]]] = {
    "S02-001": [("slope-1-1", True)],
    "S02-002": [("section-2-1", True)],
    "S02-003": [("section-3-1", True)],
    "S02-004": [("section-3-1", True)],
    "S02-005": [("waste-1-1", True)],
    "S02-006": [("slope-2-1", True), ("section-3-1", False)],
    "S02-009": [("section-1-1", True)],
    "S02-010": [("section-1-1", True), ("eco-1-1", False)],
}


def _s02_spatial_links_for(business_code: str) -> list[dict]:
    links = _S02_GIS_LINKS.get(business_code) or []
    return [
        {
            "featureId": feature_id,
            "geometryType": "unknown",
            "role": "primary" if is_primary else "related",
            "isPrimary": is_primary,
        }
        for feature_id, is_primary in links
    ]


# L2 管控叙事（与 seed 对齐；不落「演示」措辞）
_S02_CONTROL_PACK: dict[str, dict] = {
    "S02-001": {
        "responsibleOrg": "二标项目经理部",
        "confirmOrg": "建设单位工程部",
        "confirmStatus": "建设单位确认在管",
        "reviewCycle": "周度复核",
        "parties": [
            {"role": "owner", "roleLabel": "建设单位", "orgName": "宜罗公司工程部", "userName": "风险台账管理员"},
            {"role": "contractor", "roleLabel": "施工单位", "orgName": "二标项目经理部", "userName": "现场安全总监"},
        ],
        "history": [
            {"fromStatus": None, "toStatus": "辨识登记", "actionCode": "IDENTIFY", "actionAt": "2026-05-08 10:00:00",
             "operatorName": "现场安全总监", "operatorOrgName": "二标项目经理部",
             "comment": "开工后纳入专项风险清单，编号由建设单位统一维护", "transitionResult": "SUCCESS"},
            {"fromStatus": "辨识登记", "toStatus": "进入在管", "actionCode": "ENTER_CONTROL", "actionAt": "2026-05-08 16:00:00",
             "operatorName": "风险台账管理员", "operatorOrgName": "宜罗公司工程部",
             "comment": "建设单位确认重大风险，起控日期与开工令对齐", "transitionResult": "SUCCESS"},
            {"fromStatus": "进入在管", "toStatus": "持续管控", "actionCode": "REVIEW", "actionAt": "2026-07-18 09:30:00",
             "operatorName": "现场安全总监", "operatorOrgName": "二标项目经理部",
             "comment": "超前地质预报与监控量测正常，维持重大等级持续管控", "transitionResult": "SUCCESS"},
        ],
        "evidence": [
            {"role": "LIST", "roleLabel": "专项清单", "kind": "ledger", "title": "较大及以上安全风险专项清单（隧道）",
             "description": "建设单位统一编号维护", "validityStatus": "VALID", "createdAt": "2026-05-08 16:00:00"},
            {"role": "SCHEME", "roleLabel": "专项方案", "kind": "document", "title": "隧道塌方防控专项方案",
             "description": "含超前预报与短进尺要求", "validityStatus": "VALID", "createdAt": "2026-05-10 11:00:00"},
            {"role": "MONITOR", "roleLabel": "监测记录", "kind": "record", "title": "隧道监控量测周报",
             "description": "位移/收敛未见异常突变", "validityStatus": "VALID", "createdAt": "2026-07-18 09:00:00"},
        ],
    },
    "S02-002": {
        "responsibleOrg": "二标项目经理部",
        "confirmOrg": "建设单位工程部",
        "confirmStatus": "建设单位确认在管",
        "reviewCycle": "周度复核",
        "parties": [
            {"role": "owner", "roleLabel": "建设单位", "orgName": "宜罗公司工程部", "userName": "风险台账管理员"},
            {"role": "contractor", "roleLabel": "施工单位", "orgName": "二标项目经理部", "userName": "路基工区负责人"},
        ],
        "history": [
            {"fromStatus": None, "toStatus": "辨识登记", "actionCode": "IDENTIFY", "actionAt": "2026-05-15 09:00:00",
             "operatorName": "路基工区负责人", "operatorOrgName": "二标项目经理部",
             "comment": "高边坡开挖前辨识为重大风险", "transitionResult": "SUCCESS"},
            {"fromStatus": "辨识登记", "toStatus": "进入在管", "actionCode": "ENTER_CONTROL", "actionAt": "2026-05-15 15:00:00",
             "operatorName": "风险台账管理员", "operatorOrgName": "宜罗公司工程部",
             "comment": "纳入在管重大风险，挂接边坡监测点", "transitionResult": "SUCCESS"},
            {"fromStatus": "进入在管", "toStatus": "持续管控", "actionCode": "REVIEW", "actionAt": "2026-07-20 10:00:00",
             "operatorName": "路基工区负责人", "operatorOrgName": "二标项目经理部",
             "comment": "分级开挖与监测正常，雨季加密巡查", "transitionResult": "SUCCESS"},
        ],
        "evidence": [
            {"role": "LIST", "roleLabel": "专项清单", "kind": "ledger", "title": "较大及以上安全风险专项清单（高边坡）",
             "description": "与周报冲突时以专项清单为准", "validityStatus": "VALID", "createdAt": "2026-05-15 15:00:00"},
            {"role": "MONITOR", "roleLabel": "监测记录", "kind": "record", "title": "高边坡监测日报摘要",
             "description": "测点无超限预警", "validityStatus": "VALID", "createdAt": "2026-07-20 08:30:00"},
            {"role": "SCHEME", "roleLabel": "专项方案", "kind": "document", "title": "高边坡开挖支护专项方案",
             "description": "含临时支护与分级开挖工序", "validityStatus": "VALID", "createdAt": "2026-05-16 14:00:00"},
        ],
    },
    "S02-003": {
        "responsibleOrg": "三标项目经理部",
        "confirmOrg": "建设单位工程部",
        "confirmStatus": "建设单位确认在管",
        "reviewCycle": "作业前复核",
        "parties": [
            {"role": "owner", "roleLabel": "建设单位", "orgName": "宜罗公司工程部", "userName": "风险台账管理员"},
            {"role": "contractor", "roleLabel": "施工单位", "orgName": "三标项目经理部", "userName": "桥梁工区负责人"},
        ],
        "history": [
            {"fromStatus": None, "toStatus": "辨识登记", "actionCode": "IDENTIFY", "actionAt": "2026-07-01 08:30:00",
             "operatorName": "桥梁工区负责人", "operatorOrgName": "三标项目经理部",
             "comment": "梁段吊装前辨识为较大风险", "transitionResult": "SUCCESS"},
            {"fromStatus": "辨识登记", "toStatus": "进入在管", "actionCode": "ENTER_CONTROL", "actionAt": "2026-07-01 14:00:00",
             "operatorName": "风险台账管理员", "operatorOrgName": "宜罗公司工程部",
             "comment": "本月新增纳入在管较大风险", "transitionResult": "SUCCESS"},
            {"fromStatus": "进入在管", "toStatus": "持续管控", "actionCode": "REVIEW", "actionAt": "2026-07-22 09:00:00",
             "operatorName": "桥梁工区负责人", "operatorOrgName": "三标项目经理部",
             "comment": "吊装方案审批有效，旁站监护落实", "transitionResult": "SUCCESS"},
        ],
        "evidence": [
            {"role": "SCHEME", "roleLabel": "专项方案", "kind": "document", "title": "桥梁吊装专项施工方案",
             "description": "含起重指挥与索具检查要求", "validityStatus": "VALID", "createdAt": "2026-06-28 16:00:00"},
            {"role": "PERMIT", "roleLabel": "作业许可", "kind": "permit", "title": "高风险作业审批单",
             "description": "建设单位确认后实施", "validityStatus": "VALID", "createdAt": "2026-07-01 13:30:00"},
        ],
    },
    "S02-004": {
        "responsibleOrg": "三标项目经理部",
        "confirmOrg": "建设单位工程部",
        "confirmStatus": "建设单位确认在管",
        "reviewCycle": "日巡 + 周复核",
        "parties": [
            {"role": "owner", "roleLabel": "建设单位", "orgName": "宜罗公司工程部", "userName": "风险台账管理员"},
            {"role": "contractor", "roleLabel": "施工单位", "orgName": "三标项目经理部", "userName": "桥梁工区负责人"},
        ],
        "history": [
            {"fromStatus": None, "toStatus": "辨识登记", "actionCode": "IDENTIFY", "actionAt": "2026-06-25 09:00:00",
             "operatorName": "桥梁工区负责人", "operatorOrgName": "三标项目经理部",
             "comment": "承台基坑开挖辨识为较大风险，与吊装风险同工点分别建档", "transitionResult": "SUCCESS"},
            {"fromStatus": "辨识登记", "toStatus": "进入在管", "actionCode": "ENTER_CONTROL", "actionAt": "2026-06-25 15:30:00",
             "operatorName": "风险台账管理员", "operatorOrgName": "宜罗公司工程部",
             "comment": "建设单位确认纳入在管", "transitionResult": "SUCCESS"},
            {"fromStatus": "进入在管", "toStatus": "持续管控", "actionCode": "REVIEW", "actionAt": "2026-07-21 11:00:00",
             "operatorName": "桥梁工区负责人", "operatorOrgName": "三标项目经理部",
             "comment": "支护与降水正常，位移监测未见超限", "transitionResult": "SUCCESS"},
        ],
        "evidence": [
            {"role": "SCHEME", "roleLabel": "专项方案", "kind": "document", "title": "深基坑支护与降水方案",
             "description": "含监测预警阈值", "validityStatus": "VALID", "createdAt": "2026-06-24 10:00:00"},
            {"role": "MONITOR", "roleLabel": "监测记录", "kind": "record", "title": "基坑位移监测记录",
             "description": "周汇总无超限", "validityStatus": "VALID", "createdAt": "2026-07-21 10:30:00"},
        ],
    },
    "S02-005": {
        "responsibleOrg": "二标项目经理部",
        "confirmOrg": "建设单位工程部",
        "confirmStatus": "建设单位确认在管",
        "reviewCycle": "爆破前复核",
        "parties": [
            {"role": "owner", "roleLabel": "建设单位", "orgName": "宜罗公司工程部", "userName": "风险台账管理员"},
            {"role": "contractor", "roleLabel": "施工单位", "orgName": "二标项目经理部", "userName": "爆破作业负责人"},
        ],
        "history": [
            {"fromStatus": None, "toStatus": "辨识登记", "actionCode": "IDENTIFY", "actionAt": "2026-06-10 08:00:00",
             "operatorName": "爆破作业负责人", "operatorOrgName": "二标项目经理部",
             "comment": "石方爆破辨识为较大风险", "transitionResult": "SUCCESS"},
            {"fromStatus": "辨识登记", "toStatus": "进入在管", "actionCode": "ENTER_CONTROL", "actionAt": "2026-06-10 14:00:00",
             "operatorName": "风险台账管理员", "operatorOrgName": "宜罗公司工程部",
             "comment": "纳入在管，短周期作业按次复核", "transitionResult": "SUCCESS"},
            {"fromStatus": "进入在管", "toStatus": "持续管控", "actionCode": "REVIEW", "actionAt": "2026-07-19 07:50:00",
             "operatorName": "爆破作业负责人", "operatorOrgName": "二标项目经理部",
             "comment": "审批交底与警戒措施到位", "transitionResult": "SUCCESS"},
        ],
        "evidence": [
            {"role": "PERMIT", "roleLabel": "作业许可", "kind": "permit", "title": "爆破作业审批与警戒记录",
             "description": "持证作业人员名单齐备", "validityStatus": "VALID", "createdAt": "2026-07-19 07:30:00"},
            {"role": "SCHEME", "roleLabel": "专项方案", "kind": "document", "title": "石方爆破专项方案",
             "description": "含飞石防护与疏散半径", "validityStatus": "VALID", "createdAt": "2026-06-09 16:00:00"},
        ],
    },
    "S02-006": {
        "responsibleOrg": "二标项目经理部",
        "confirmOrg": "建设单位工程部",
        "confirmStatus": "建设单位确认在管",
        "reviewCycle": "设备进场复核",
        "parties": [
            {"role": "owner", "roleLabel": "建设单位", "orgName": "宜罗公司工程部", "userName": "风险台账管理员"},
            {"role": "contractor", "roleLabel": "施工单位", "orgName": "二标项目经理部", "userName": "机械管理员"},
        ],
        "history": [
            {"fromStatus": None, "toStatus": "辨识登记", "actionCode": "IDENTIFY", "actionAt": "2026-06-20 09:00:00",
             "operatorName": "机械管理员", "operatorOrgName": "二标项目经理部",
             "comment": "边坡作业面起重设备辨识为较大风险", "transitionResult": "SUCCESS"},
            {"fromStatus": "辨识登记", "toStatus": "进入在管", "actionCode": "ENTER_CONTROL", "actionAt": "2026-06-20 15:00:00",
             "operatorName": "风险台账管理员", "operatorOrgName": "宜罗公司工程部",
             "comment": "建设单位确认在管并挂接监测点", "transitionResult": "SUCCESS"},
            {"fromStatus": "进入在管", "toStatus": "持续管控", "actionCode": "REVIEW", "actionAt": "2026-07-17 14:00:00",
             "operatorName": "机械管理员", "operatorOrgName": "二标项目经理部",
             "comment": "地基承载力与限载检查通过", "transitionResult": "SUCCESS"},
        ],
        "evidence": [
            {"role": "ACCEPT", "roleLabel": "验收记录", "kind": "record", "title": "起重设备进场验收单",
             "description": "含地基处理确认", "validityStatus": "VALID", "createdAt": "2026-06-20 11:00:00"},
            {"role": "MONITOR", "roleLabel": "监测记录", "kind": "record", "title": "作业面沉降观测",
             "description": "未见异常沉降", "validityStatus": "VALID", "createdAt": "2026-07-17 13:30:00"},
        ],
    },
    "S02-009": {
        "responsibleOrg": "一标项目经理部",
        "confirmOrg": "建设单位工程部",
        "confirmStatus": "建设单位确认在管",
        "reviewCycle": "班前交底复核",
        "parties": [
            {"role": "owner", "roleLabel": "建设单位", "orgName": "宜罗公司工程部", "userName": "风险台账管理员"},
            {"role": "contractor", "roleLabel": "施工单位", "orgName": "一标项目经理部", "userName": "高墩工区负责人"},
        ],
        "history": [
            {"fromStatus": None, "toStatus": "辨识登记", "actionCode": "IDENTIFY", "actionAt": "2026-05-20 09:00:00",
             "operatorName": "高墩工区负责人", "operatorOrgName": "一标项目经理部",
             "comment": "高墩爬模施工辨识为较大风险", "transitionResult": "SUCCESS"},
            {"fromStatus": "辨识登记", "toStatus": "进入在管", "actionCode": "ENTER_CONTROL", "actionAt": "2026-05-20 16:00:00",
             "operatorName": "风险台账管理员", "operatorOrgName": "宜罗公司工程部",
             "comment": "建设单位确认纳入在管", "transitionResult": "SUCCESS"},
            {"fromStatus": "进入在管", "toStatus": "持续管控", "actionCode": "REVIEW", "actionAt": "2026-07-16 08:20:00",
             "operatorName": "高墩工区负责人", "operatorOrgName": "一标项目经理部",
             "comment": "防坠落设施验收有效，班前交底落实", "transitionResult": "SUCCESS"},
        ],
        "evidence": [
            {"role": "SCHEME", "roleLabel": "专项方案", "kind": "document", "title": "高墩施工防坠落专项方案",
             "description": "含安全带与爬梯验收标准", "validityStatus": "VALID", "createdAt": "2026-05-19 15:00:00"},
            {"role": "PERMIT", "roleLabel": "作业许可", "kind": "permit", "title": "高处作业审批记录",
             "description": "当日班前交底签字齐全", "validityStatus": "VALID", "createdAt": "2026-07-16 08:00:00"},
        ],
    },
    "S02-010": {
        "responsibleOrg": "一标项目经理部",
        "confirmOrg": "建设单位工程部",
        "confirmStatus": "建设单位确认在管",
        "reviewCycle": "导改阶段复核",
        "parties": [
            {"role": "owner", "roleLabel": "建设单位", "orgName": "宜罗公司工程部", "userName": "风险台账管理员"},
            {"role": "contractor", "roleLabel": "施工单位", "orgName": "一标项目经理部", "userName": "交通导改负责人"},
        ],
        "history": [
            {"fromStatus": None, "toStatus": "辨识登记", "actionCode": "IDENTIFY", "actionAt": "2026-06-05 09:00:00",
             "operatorName": "交通导改负责人", "operatorOrgName": "一标项目经理部",
             "comment": "便道临时导改辨识为较大风险", "transitionResult": "SUCCESS"},
            {"fromStatus": "辨识登记", "toStatus": "进入在管", "actionCode": "ENTER_CONTROL", "actionAt": "2026-06-05 15:00:00",
             "operatorName": "风险台账管理员", "operatorOrgName": "宜罗公司工程部",
             "comment": "建设单位确认在管，邻近生态敏感区辅挂接", "transitionResult": "SUCCESS"},
            {"fromStatus": "进入在管", "toStatus": "持续管控", "actionCode": "REVIEW", "actionAt": "2026-07-15 17:00:00",
             "operatorName": "交通导改负责人", "operatorOrgName": "一标项目经理部",
             "comment": "标志标牌与夜间照明完好，协管值守正常", "transitionResult": "SUCCESS"},
        ],
        "evidence": [
            {"role": "SCHEME", "roleLabel": "专项方案", "kind": "document", "title": "临时交通导改实施方案",
             "description": "含夜间照明与协管配置", "validityStatus": "VALID", "createdAt": "2026-06-04 14:00:00"},
            {"role": "LIST", "roleLabel": "专项清单", "kind": "ledger", "title": "在管较大风险台账摘录（导改）",
             "description": "建设单位统一编号", "validityStatus": "VALID", "createdAt": "2026-06-05 15:00:00"},
        ],
    },
}


def _s02_control_pack(business_code: str, row: dict) -> dict:
    pack = _S02_CONTROL_PACK.get(business_code)
    if pack:
        return pack
    # 销号或未登记叙事时的最小回落
    cancelled = (row.get("control_status") or "") == "已销号"
    start = value_for_json(row.get("control_start_date")) or ""
    end = value_for_json(row.get("cancelled_date")) or ""
    history = [
        {
            "fromStatus": None,
            "toStatus": "辨识登记",
            "actionCode": "IDENTIFY",
            "actionAt": f"{start} 09:00:00" if start else None,
            "operatorName": "现场安全员",
            "operatorOrgName": "项目经理部",
            "comment": "纳入专项风险清单",
            "transitionResult": "SUCCESS",
        },
        {
            "fromStatus": "辨识登记",
            "toStatus": "进入在管",
            "actionCode": "ENTER_CONTROL",
            "actionAt": f"{start} 15:00:00" if start else None,
            "operatorName": "风险台账管理员",
            "operatorOrgName": "宜罗公司工程部",
            "comment": "建设单位确认纳入在管",
            "transitionResult": "SUCCESS",
        },
    ]
    if cancelled:
        history.append(
            {
                "fromStatus": "持续管控",
                "toStatus": "已销号",
                "actionCode": "CANCEL",
                "actionAt": f"{end} 16:00:00" if end else None,
                "operatorName": "风险台账管理员",
                "operatorOrgName": "宜罗公司工程部",
                "comment": "建设单位评估确认解除/销号",
                "transitionResult": "SUCCESS",
            }
        )
    else:
        history.append(
            {
                "fromStatus": "进入在管",
                "toStatus": "持续管控",
                "actionCode": "REVIEW",
                "actionAt": None,
                "operatorName": "现场安全员",
                "operatorOrgName": "项目经理部",
                "comment": row.get("control_measure") or "按专项方案持续管控",
                "transitionResult": "SUCCESS",
            }
        )
    return {
        "responsibleOrg": "项目经理部",
        "confirmOrg": "建设单位工程部",
        "confirmStatus": "已销号" if cancelled else "建设单位确认在管",
        "reviewCycle": "按专项清单",
        "parties": [
            {"role": "owner", "roleLabel": "建设单位", "orgName": "宜罗公司工程部", "userName": "风险台账管理员"},
            {"role": "contractor", "roleLabel": "施工单位", "orgName": "项目经理部", "userName": "现场安全员"},
        ],
        "history": history,
        "evidence": [
            {
                "role": "LIST",
                "roleLabel": "专项清单",
                "kind": "ledger",
                "title": "较大及以上安全风险专项清单",
                "description": "建设单位统一维护编号",
                "validityStatus": "VALID",
                "createdAt": f"{start} 15:00:00" if start else None,
            }
        ],
    }


def get_s02_safety_risk_detail() -> dict | None:
    active_rows = query_all(
        """
        SELECT *
        FROM safety_risk_point
        WHERE risk_level IN ('重大', '较大')
          AND control_status <> '已销号'
        ORDER BY risk_level = '重大' DESC, control_start_date, id
        """
    )
    if not active_rows:
        return None
    major_count = sum(1 for row in active_rows if row.get("risk_level") == "重大")
    larger_count = sum(1 for row in active_rows if row.get("risk_level") == "较大")
    new_count = query_one(
        """
        SELECT COUNT(*) AS c
        FROM safety_risk_point
        WHERE risk_level IN ('重大', '较大')
          AND control_status <> '已销号'
          AND control_start_date >= '2026-07-01'
          AND control_start_date < '2026-08-01'
        """
    )["c"]
    cancelled_count = query_one(
        """
        SELECT COUNT(*) AS c
        FROM safety_risk_point
        WHERE risk_level IN ('重大', '较大')
          AND cancelled_date >= '2026-07-01'
          AND cancelled_date < '2026-08-01'
        """
    )["c"]
    location_count = len({row.get("location") for row in active_rows if row.get("location")})

    detail = with_snapshot_base("S02")

    detail.update(
        {
            "summary": [
                {"label": "较大风险点", "value": larger_count, "unit": "项"},
                {"label": "重大风险点", "value": major_count, "unit": "项"},
                {"label": "本月新增", "value": int(new_count), "unit": "项"},
                {"label": "本月销号", "value": int(cancelled_count), "unit": "项"},
                {"label": "涉及工点", "value": location_count, "unit": "个"},
            ],
            "detailData": [
                {
                    "id": _s02_source_id(row),
                    "sourceId": _s02_source_id(row),
                    "sourceTable": "safety_risk_point",
                    "rawId": row.get("id"),
                    "gisFeatureId": (
                        (_S02_GIS_LINKS.get(_s02_source_id(row)) or [(None, False)])[0][0]
                    ),
                    "name": row.get("risk_name") or "",
                    "level": row.get("risk_level") or "",
                    "location": row.get("location") or "",
                    "type": row.get("risk_type") or "",
                    "time": value_for_json(row.get("control_start_date")),
                    "status": row.get("control_status") or "持续管控",
                }
                for row in active_rows
            ],
            "dataSource": "安全风险点明细表 safety_risk_point",
            "updateTime": "2026-07-13 11:00",
            "isMock": False,
        }
    )
    return detail


def get_s02_risks() -> dict:
    """S02 工作台列表 API：overview + risks + spatialLinks。"""
    active_rows = query_all(
        """
        SELECT *
        FROM safety_risk_point
        WHERE risk_level IN ('重大', '较大')
          AND control_status <> '已销号'
        ORDER BY risk_level = '重大' DESC, control_start_date, id
        """
    )
    major_count = sum(1 for row in active_rows if row.get("risk_level") == "重大")
    larger_count = sum(1 for row in active_rows if row.get("risk_level") == "较大")
    new_count = query_one(
        """
        SELECT COUNT(*) AS c
        FROM safety_risk_point
        WHERE risk_level IN ('重大', '较大')
          AND control_status <> '已销号'
          AND control_start_date >= '2026-07-01'
          AND control_start_date < '2026-08-01'
        """
    )
    cancelled_count = query_one(
        """
        SELECT COUNT(*) AS c
        FROM safety_risk_point
        WHERE risk_level IN ('重大', '较大')
          AND cancelled_date >= '2026-07-01'
          AND cancelled_date < '2026-08-01'
        """
    )
    location_count = len({row.get("location") for row in active_rows if row.get("location")})

    risks: list[dict] = []
    spatial_links: list[dict] = []
    for row in active_rows:
        business_code = _s02_source_id(row)
        links = _s02_spatial_links_for(business_code)
        for link in links:
            spatial_links.append({**link, "businessKey": business_code})
        risks.append(
            {
                "id": int(row["id"]),
                "businessCode": business_code,
                "title": row.get("risk_name") or "",
                "riskLevel": row.get("risk_level") or "",
                "riskType": row.get("risk_type") or "",
                "locationText": row.get("location") or "",
                "status": row.get("control_status") or "持续管控",
                "controlStartDate": value_for_json(row.get("control_start_date")),
                "controlMeasure": row.get("control_measure") or "",
                "canLocate": len(links) > 0,
                "spatialLinks": links,
            }
        )

    return {
        "code": 0,
        "data": {
            "overview": {
                "total": len(active_rows),
                "major": major_count,
                "larger": larger_count,
                "newThisMonth": int((new_count or {}).get("c") or 0),
                "cancelledThisMonth": int((cancelled_count or {}).get("c") or 0),
                "locationCount": location_count,
            },
            "risks": risks,
            "spatialLinks": [
                {k: v for k, v in sl.items() if k != "businessKey"} for sl in spatial_links
            ],
            "scope": "active",
        },
    }


def get_s02_risk_detail(risk_id: int) -> dict | None:
    """S02 单条风险点详情（地图摘要卡 + L2 管控叙事）。"""
    row = query_one(
        """
        SELECT *
        FROM safety_risk_point
        WHERE id = %s
          AND risk_level IN ('重大', '较大')
        """,
        (risk_id,),
    )
    if row is None:
        return None
    business_code = _s02_source_id(row)
    links = _s02_spatial_links_for(business_code)
    pack = _s02_control_pack(business_code, row)
    status = row.get("control_status") or "持续管控"
    return {
        "code": 0,
        "data": {
            "id": int(row["id"]),
            "businessCode": business_code,
            "title": row.get("risk_name") or "",
            "riskLevel": row.get("risk_level") or "",
            "riskType": row.get("risk_type") or "",
            "locationText": row.get("location") or "",
            "status": status,
            "controlStartDate": value_for_json(row.get("control_start_date")),
            "cancelledDate": value_for_json(row.get("cancelled_date")),
            "controlMeasure": row.get("control_measure") or "",
            "canLocate": len(links) > 0,
            "spatialLinks": links,
            "sourceTable": "safety_risk_point",
            "responsibleOrgName": pack.get("responsibleOrg") or "",
            "confirmOrgName": pack.get("confirmOrg") or "",
            "confirmStatus": pack.get("confirmStatus") or (
                "已销号" if status == "已销号" else "建设单位确认在管"
            ),
            "reviewCycle": pack.get("reviewCycle") or "",
            "parties": pack.get("parties") or [],
            "history": pack.get("history") or [],
            "evidence": pack.get("evidence") or [],
        },
    }


def get_s03_labor_dispute_detail() -> dict | None:
    """S03：仅统计农民工工资类用工纠纷；正式闸关闭时返回业务零（甲方：目前无未办结）。"""
    wage_types = S03_WAGE_DISPUTE_TYPES
    placeholders = ", ".join(["%s"] * len(wage_types))
    if S03_ALLOW_DEMO:
        scope_sql = "AND is_demo = 1 AND data_nature = 'demo'"
        scope_params: tuple[Any, ...] = ()
        data_nature = "demo"
        is_demo = True
    else:
        # 正式：甲方确认无历史未办结；不回落 mock，始终返回可渲染空态
        scope_sql = "AND COALESCE(is_demo, 0) = 0 AND COALESCE(data_nature, 'formal') = 'formal'"
        scope_params = ()
        data_nature = "formal"
        is_demo = False

    open_rows = query_all(
        f"""
        SELECT *
        FROM labor_dispute_record
        WHERE status <> '已办结'
          AND dispute_type IN ({placeholders})
          {scope_sql}
        ORDER BY occurred_date, id
        """,
        (*wage_types, *scope_params),
    )
    new_count = query_one(
        f"""
        SELECT COUNT(*) AS c
        FROM labor_dispute_record
        WHERE status <> '已办结'
          AND dispute_type IN ({placeholders})
          {scope_sql}
          AND occurred_date >= '2026-07-01'
          AND occurred_date < '2026-08-01'
        """,
        (*wage_types, *scope_params),
    )["c"]
    closed_count = query_one(
        f"""
        SELECT COUNT(*) AS c
        FROM labor_dispute_record
        WHERE dispute_type IN ({placeholders})
          {scope_sql}
          AND closed_date >= '2026-07-01'
          AND closed_date < '2026-08-01'
        """,
        (*wage_types, *scope_params),
    )["c"]
    people_count = sum(int(row.get("involved_people") or 0) for row in open_rows)
    amount_wan = sum(float(row.get("amount_wan") or 0) for row in open_rows)
    s03_hint = _build_s03_home_hint()

    detail = with_snapshot_base("S03")
    detail.update(
        {
            "summary": [
                {"label": "未办结纠纷", "value": len(open_rows), "unit": "项"},
                {"label": "本月新增", "value": int(new_count or 0), "unit": "项"},
                {"label": "本月办结", "value": int(closed_count or 0), "unit": "项"},
                {"label": "涉及人数", "value": people_count, "unit": "人"},
                {"label": "涉及金额", "value": round(amount_wan), "unit": "万元"},
                {"label": "权益补充口径", "value": s03_hint, "unit": ""},
            ],
            "homeHint": s03_hint,
            "detailData": [
                {
                    "name": row.get("dispute_name") or row.get("dispute_type") or "",
                    "type": row.get("dispute_type") or "",
                    "time": value_for_json(row.get("occurred_date")),
                    "people": str(row.get("involved_people") or 0),
                    "amount": f"{value_for_json(row.get('amount_wan'))}万元",
                    "department": row.get("responsible_department") or "",
                    "status": row.get("status") or "",
                }
                for row in open_rows
            ],
            "dataSource": "劳务用工纠纷台账（农民工工资）",
            "updateTime": "2026-07-13 10:00",
            "dataNature": data_nature,
            "isDemo": is_demo,
            "scope": "demo" if S03_ALLOW_DEMO else "formal",
            "isMock": False,
        }
    )
    return detail


def get_s04_appeal_detail() -> dict | None:
    open_rows = query_all(
        """
        SELECT *
        FROM appeal_record
        WHERE status <> '已办结'
        ORDER BY overdue DESC, accepted_date, id
        """
    )
    if not open_rows:
        return None
    new_count = query_one(
        """
        SELECT COUNT(*) AS c
        FROM appeal_record
        WHERE status <> '已办结'
          AND accepted_date >= '2026-07-01'
          AND accepted_date < '2026-08-01'
        """
    )["c"]
    closed_count = query_one(
        """
        SELECT COUNT(*) AS c
        FROM appeal_record
        WHERE closed_date >= '2026-07-01'
          AND closed_date < '2026-08-01'
        """
    )["c"]
    overdue_count = sum(1 for row in open_rows if int(row.get("overdue") or 0) == 1)
    avg_duration = round(sum(int(row.get("duration_days") or 0) for row in open_rows) / len(open_rows))
    s04_hint = _build_s04_home_hint()
    complaint = _safe_count(
        """
        SELECT COUNT(*) AS c FROM appeal_record
        WHERE COALESCE(appeal_type, '') LIKE %s
           OR COALESCE(source_channel, '') LIKE %s
           OR COALESCE(source_channel, '') LIKE %s
        """,
        ("%投诉%", "%12345%", "%热线%"),
    ) or 0
    petition = _safe_count(
        """
        SELECT COUNT(*) AS c FROM appeal_record
        WHERE COALESCE(appeal_type, '') LIKE %s
           OR COALESCE(source_channel, '') LIKE %s
           OR COALESCE(source_channel, '') LIKE %s
        """,
        ("%信访%", "%信访%", "%来访%"),
    ) or 0
    total_appeal = _safe_count("SELECT COUNT(*) AS c FROM appeal_record") or 0
    closed_appeal = _safe_count("SELECT COUNT(*) AS c FROM appeal_record WHERE status = '已办结'") or 0
    resolve_rate = round(100.0 * closed_appeal / total_appeal) if total_appeal else None

    detail = with_snapshot_base("S04")
    detail.update(
        {
            "summary": [
                {"label": "未办结诉求", "value": len(open_rows), "unit": "项"},
                {"label": "投诉数量", "value": complaint, "unit": "项"},
                {"label": "信访数量", "value": petition, "unit": "项"},
                {"label": "化解率", "value": resolve_rate if resolve_rate is not None else "暂无有效数据", "unit": "%" if resolve_rate is not None else ""},
                {"label": "已逾期", "value": overdue_count, "unit": "项"},
                {"label": "平均办理时长", "value": avg_duration, "unit": "天"},
            ],
            "homeHint": s04_hint,
            "detailData": [
                {
                    "content": row.get("appeal_content") or row.get("appeal_type") or "",
                    "time": value_for_json(row.get("accepted_date")),
                    "source": row.get("source_channel") or "",
                    "location": row.get("location") or "",
                    "deadline": value_for_json(row.get("deadline")),
                    "status": row.get("status") or "",
                }
                for row in open_rows
            ],
            "dataSource": "群众诉求台账",
            "updateTime": "2026-07-13 09:30",
            "isMock": False,
        }
    )
    return detail


def get_g02_permit_detail() -> dict | None:
    rows = query_all("SELECT * FROM permit_record ORDER BY expire_date, id")
    if not rows:
        return None
    current_date = date(2026, 7, 13)
    due_rows = [row for row in rows if row.get("status") == "临期"]
    overdue_rows = [row for row in rows if row.get("status") == "逾期"]
    due_within_30 = [
        row for row in rows
        if row.get("expire_date") and 0 < (row["expire_date"] - current_date).days <= 30
    ]
    dept_count = len({row.get("responsible_department") for row in rows if row.get("responsible_department")})
    positive_days = [(row["expire_date"] - current_date).days for row in due_rows if row.get("expire_date")]
    avg_days = round(sum(positive_days) / len(positive_days)) if positive_days else 0

    detail = with_snapshot_base("G02")
    detail.update(
        {
            "summary": [
                {"label": "临期许可", "value": len(due_rows), "unit": "项"},
                {"label": "逾期许可", "value": len(overdue_rows), "unit": "项"},
                {"label": "30日内到期", "value": len(due_within_30), "unit": "项"},
                {"label": "涉及部门", "value": dept_count, "unit": "个"},
                {"label": "平均剩余有效期", "value": avg_days, "unit": "天"},
            ],
            "detailData": [
                {
                    "name": row["permit_name"],
                    "number": row.get("permit_no") or "",
                    "type": row.get("permit_type") or "",
                    "deadline": value_for_json(row.get("expire_date")),
                    "department": row.get("responsible_department") or "",
                    "status": row.get("status") or "",
                }
                for row in rows
            ],
            "dataSource": "证照许可台账",
            "updateTime": "2026-07-13 00:00",
            "isMock": False,
        }
    )
    return detail


def get_g03_rectification_detail() -> dict | None:
    rows = query_all(
        """
        SELECT *
        FROM rectification_record
        WHERE status <> '已关闭'
        ORDER BY overdue DESC, deadline, id
        """
    )
    if not rows:
        return None

    new_count = query_one(
        """
        SELECT COUNT(*) AS c
        FROM rectification_record
        WHERE status <> '已关闭'
          AND created_at >= '2026-07-01'
          AND created_at < '2026-08-01'
        """
    )["c"]
    closed_count = query_one(
        """
        SELECT COUNT(*) AS c
        FROM rectification_record
        WHERE closed_date >= '2026-07-01'
          AND closed_date < '2026-08-01'
        """
    )["c"]
    overdue_count = sum(1 for row in rows if int(row.get("overdue") or 0) == 1)
    check_count = len({row.get("check_batch") for row in rows if row.get("check_batch")})
    total_rect = _safe_count("SELECT COUNT(*) AS c FROM rectification_record") or 0
    closed_rect = _safe_count("SELECT COUNT(*) AS c FROM rectification_record WHERE status = '已关闭'") or 0
    closure_rate = round(100.0 * closed_rect / total_rect) if total_rect else None
    g02_hint = _build_g02_home_hint()

    detail = with_snapshot_base("G03")
    detail.update(
        {
            "summary": [
                {"label": "问题数量", "value": total_rect, "unit": "项"},
                {"label": "整改数量", "value": len(rows), "unit": "项"},
                {"label": "闭环率", "value": closure_rate if closure_rate is not None else "暂无有效数据", "unit": "%" if closure_rate is not None else ""},
                {"label": "本月新增", "value": int(new_count), "unit": "项"},
                {"label": "逾期未关闭", "value": overdue_count, "unit": "项"},
            ],
            "homeHint": g02_hint,
            "detailData": [
                {
                    "name": row["item_name"],
                    "source": row.get("source_type") or "",
                    "level": row.get("issue_level") or "",
                    "deadline": value_for_json(row.get("deadline")),
                    "department": row.get("responsible_department") or "",
                    "status": row.get("status") or "",
                }
                for row in rows
            ],
            "dataSource": "检查整改台账（正式检查/通报/审计）",
            "updateTime": "2026-07-13 10:30",
            "isMock": False,
        }
    )
    return detail


def get_g04_material_gap_detail() -> dict | None:
    rows = query_all("SELECT * FROM compliance_material_gap WHERE status <> '已补齐' ORDER BY status = '逾期' DESC, deadline, id")
    if not rows:
        return None
    due_this_month = [
        row for row in rows
        if row.get("status") != "逾期" and row.get("deadline") and row["deadline"].year == 2026 and row["deadline"].month == 7
    ]
    overdue_count = sum(1 for row in rows if row.get("status") == "逾期")
    module_count = len({row.get("module_code") for row in rows if row.get("module_code")})

    detail = with_snapshot_base("G04")
    detail.update(
        {
            "summary": [
                {"label": "待补齐资料", "value": len(rows), "unit": "项"},
                {"label": "本月需提交", "value": len(due_this_month), "unit": "项"},
                {"label": "逾期未提交", "value": overdue_count, "unit": "项"},
                {"label": "涉及模块", "value": module_count, "unit": "个"},
                # 完备率无甲方依据，缺省不冒充；摘要卡展示「本阶段待补齐」+ --
                {"label": "本阶段待补齐", "value": None, "unit": ""},
            ],
            "detailData": [
                {
                    "name": row["material_name"],
                    "module": row.get("module_code") or "",
                    "deadline": value_for_json(row.get("deadline")),
                    "owner": row.get("responsible_unit") or "",
                    "status": row.get("status") or "",
                    "action": row.get("action_text") or "上传",
                }
                for row in rows
            ],
            "dataSource": "关键合规资料台账",
            "updateTime": "2026-07-13 09:00",
            "isMock": False,
        }
    )
    return detail


def get_dashboard_kpi_detail(indicator_code: str) -> dict | None:
    # Demo V0.1 contract: G02=许可/夜施, G03=设计变更, G04=内控廉洁, E04=文物四字段
    try:
        import esg_demo_api

        demo = esg_demo_api.get_demo_kpi_detail(indicator_code)
        if demo:
            return demo
    except Exception as exc:
        logger.warning("esg_demo kpi detail skipped for %s: %s", indicator_code, exc)

    business_builders = {
        "E01": get_e01_env_monitoring_detail,
        "E02": get_e02_env_issue_detail,
        "E03": get_e03_water_protection_detail,
        "E04": get_e04_cultural_kpi_detail,
        "S02": get_s02_safety_risk_detail,
        "S03": get_s03_labor_dispute_detail,
        "S04": get_s04_appeal_detail,
        "G01": get_g01_compliance_procedure_detail,
        # Legacy fallback only when Demo tables absent
        "G02": get_g03_rectification_detail,
        "G03": get_g03_contractor_eval_detail,
        "G04": get_g04_material_gap_detail,
    }
    if indicator_code in business_builders:
        detail = business_builders[indicator_code]()
        if detail:
            label_meta = KPI_HOME_LABELS.get(indicator_code)
            if label_meta:
                detail["fullName"] = label_meta["fullName"]
                detail["key"] = indicator_code
            return detail
    return get_dashboard_kpi_detail_snapshot(indicator_code)


def get_g03_contractor_eval_detail() -> dict:
    """参建单位履约评价：台账未接入，返回可追溯空壳，禁止编造排名。"""
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    return {
        "key": "G03",
        "fullName": "参建单位履约评价",
        "theme": "purple",
        "summary": [
            {"label": "纳入评价单位", "value": 0, "unit": "家"},
            {"label": "本周期已评价", "value": 0, "unit": "家"},
            {"label": "待评价", "value": 0, "unit": "家"},
            {"label": "台账状态", "value": "未接入", "unit": ""},
        ],
        "chartTitle": "履约评价分布",
        "detailTitle": "参建单位履约评价明细",
        "detailColumns": [
            {"key": "name", "label": "单位名称", "width": "28%"},
            {"key": "rank", "label": "排名", "width": "12%"},
            {"key": "score", "label": "评价得分", "width": "15%"},
            {"key": "result", "label": "考核结果", "width": "20%"},
            {"key": "department", "label": "责任部门", "width": "25%"},
        ],
        "detailData": [],
        "dataSource": "履约评价台账（待建）",
        "updateTime": now,
        "updateFrequency": "按考核周期",
        "completeness": "0%",
        "completenessStatus": "incomplete",
        "isMock": False,
        "emptyReason": "暂无有效数据：参建单位履约评价台账尚未接入，首页展示「待评价」，不编造排名或得分。",
        "responsibleUnit": "合约部 / 项目经理部",
        "status": "待建台账",
    }


def get_dashboard_topic_snapshot(topic_key: str) -> dict | None:
    row = query_one(
        """
        SELECT detail_json
        FROM dashboard_topic_snapshot
        WHERE topic_key = %s
        """,
        (topic_key,),
    )
    if row is None:
        return None
    detail = json_column(row["detail_json"])
    detail["isMock"] = False
    return detail


def get_dashboard_topic(topic_key: str) -> dict | None:
    normalized_key = "monthly-report" if topic_key == "monthly" else topic_key
    if normalized_key == "carbon":
        detail = get_carbon_topic_detail()
        if detail:
            return detail
    if normalized_key == "monthly-report":
        detail = get_monthly_report_topic_detail()
        if detail:
            return detail
    return get_dashboard_topic_snapshot(normalized_key)


def get_dashboard_panels_snapshot() -> dict | None:
    row = query_one(
        """
        SELECT panel_json
        FROM dashboard_panel_snapshot
        WHERE panel_key = 'home-panels'
        """
    )
    if row is None:
        return None
    return json_column(row["panel_json"])


def get_compliance_panel_data(base: dict) -> dict:
    """综合风险态势与预警：红/黄/蓝/总数，均来自业务台账实算，不编造。"""
    overdue_env = int(
        query_one(
            """
            SELECT COUNT(*) AS c FROM env_issue_record
            WHERE issue_status NOT IN ('已闭环','已撤销','已合并')
              AND COALESCE(overdue, 0) = 1
            """
        )["c"]
        or 0
    )
    major_risk = int(
        query_one(
            """
            SELECT COUNT(*) AS c FROM safety_risk_point
            WHERE risk_level = '重大' AND control_status <> '已销号'
            """
        )["c"]
        or 0
    )
    overdue_permit = int(query_one("SELECT COUNT(*) AS c FROM permit_record WHERE status = '逾期'")["c"] or 0)
    overdue_rect = int(
        query_one(
            """
            SELECT COUNT(*) AS c FROM rectification_record
            WHERE status <> '已关闭' AND COALESCE(overdue, 0) = 1
            """
        )["c"]
        or 0
    )
    red = overdue_env + major_risk + overdue_permit + overdue_rect

    near_permit = int(query_one("SELECT COUNT(*) AS c FROM permit_record WHERE status = '临期'")["c"] or 0)
    larger_risk = int(
        query_one(
            """
            SELECT COUNT(*) AS c FROM safety_risk_point
            WHERE risk_level = '较大' AND control_status <> '已销号'
            """
        )["c"]
        or 0
    )
    open_water = int(
        query_one(
            """
            SELECT COUNT(*) AS c FROM water_protection_issue
            WHERE issue_status NOT IN ('已闭环','已撤销','已合并')
              AND effective_status = 'EFFECTIVE'
            """
        )["c"]
        or 0
    )
    yellow = near_permit + larger_risk + open_water

    open_env = int(
        query_one(
            """
            SELECT COUNT(*) AS c FROM env_issue_record
            WHERE issue_status NOT IN ('已闭环','已撤销','已合并')
              AND COALESCE(overdue, 0) = 0
            """
        )["c"]
        or 0
    )
    material_gap = int(query_one("SELECT COUNT(*) AS c FROM compliance_material_gap WHERE status <> '已补齐'")["c"] or 0)
    open_appeal = int(query_one("SELECT COUNT(*) AS c FROM appeal_record WHERE status <> '已办结'")["c"] or 0)
    blue = open_env + material_gap + open_appeal

    total = red + yellow + blue
    closed_rect = int(query_one("SELECT COUNT(*) AS c FROM rectification_record WHERE closed_date IS NOT NULL")["c"] or 0)
    closed_env = int(query_one("SELECT COUNT(*) AS c FROM env_issue_record WHERE closed_date IS NOT NULL")["c"] or 0)
    closed_water = int(query_one("SELECT COUNT(*) AS c FROM water_protection_issue WHERE closed_date IS NOT NULL")["c"] or 0)
    closed_total = closed_rect + closed_env + closed_water

    recent_permit = query_one(
        """
        SELECT permit_name, expire_date, status
        FROM permit_record
        WHERE status IN ('临期', '逾期')
        ORDER BY FIELD(status, '逾期', '临期'), expire_date
        LIMIT 1
        """
    )
    recent_env = query_one(
        """
        SELECT COALESCE(issue_name, issue_type) AS title, overdue
        FROM env_issue_record
        WHERE issue_status NOT IN ('已闭环','已撤销','已合并')
        ORDER BY COALESCE(overdue, 0) DESC, found_date DESC
        LIMIT 1
        """
    )
    recent_water = query_one(
        """
        SELECT COALESCE(issue_name, issue_type) AS title
        FROM water_protection_issue
        WHERE issue_status NOT IN ('已闭环','已撤销','已合并')
          AND effective_status = 'EFFECTIVE'
        ORDER BY found_date DESC
        LIMIT 1
        """
    )

    safeguards = []
    if recent_env:
        level = "红色预警" if int(recent_env.get("overdue") or 0) == 1 else "蓝色提醒"
        safeguards.append(f"{level}：{recent_env['title']}，纳入未闭环环境问题跟踪")
    if recent_permit:
        level = "红色预警" if recent_permit.get("status") == "逾期" else "黄色预警"
        safeguards.append(f"{level}：{recent_permit['permit_name']}（{recent_permit['status']}）")
    if recent_water:
        safeguards.append(f"蓝色提醒：{recent_water['title']}，持续跟踪销项")

    warning_items = _build_compliance_warning_items()

    return {
        "metrics": [
            {"label": "红色预警", "value": red, "unit": "项", "tone": "red", "meaning": "立即督办"},
            {"label": "黄色预警", "value": yellow, "unit": "项", "tone": "yellow", "meaning": "重点关注"},
            {"label": "蓝色提醒", "value": blue, "unit": "项", "tone": "blue", "meaning": "持续跟踪"},
            {"label": "风险事项总数", "value": total, "unit": "项", "tone": "neutral", "meaning": "事项汇总"},
        ],
        "effectiveness": [
            {"label": "红色·立即督办", "value": red},
            {"label": "黄色·重点关注", "value": yellow},
            {"label": "蓝色·持续跟踪", "value": blue},
            {"label": "已闭环事项", "value": closed_total},
        ],
        "safeguards": safeguards or (base.get("compliance") or {}).get("safeguards") or [],
        "warningItems": warning_items,
        "panelTitle": "综合风险态势与预警",
        "dataSource": "env_issue_record / safety_risk_point / permit_record / rectification_record / compliance_material_gap / appeal_record",
        "updateTime": datetime.now().strftime("%Y-%m-%d %H:%M"),
    }


def _build_compliance_warning_items() -> list[dict]:
    """红黄蓝预警清单：等级/事项/来源/状态/时间，红色优先。"""
    items: list[dict] = []

    def add_rows(sql: str, mapper):
        try:
            for row in query_all(sql):
                items.append(mapper(row))
        except Exception:
            return

    add_rows(
        """
        SELECT COALESCE(issue_name, issue_type) AS title,
               issue_status AS status,
               COALESCE(overdue, 0) AS overdue,
               DATE_FORMAT(COALESCE(found_date, created_at), '%Y-%m-%d') AS updated_at
        FROM env_issue_record
        WHERE issue_status NOT IN ('已闭环','已撤销','已合并')
        ORDER BY COALESCE(overdue, 0) DESC, found_date DESC
        LIMIT 8
        """,
        lambda row: {
            "level": "红" if int(row.get("overdue") or 0) == 1 else "蓝",
            "title": row.get("title") or "环境问题",
            "source": "E",
            "status": "立即督办" if int(row.get("overdue") or 0) == 1 else (row.get("status") or "持续跟踪"),
            "updatedAt": row.get("updated_at") or "",
        },
    )

    add_rows(
        """
        SELECT COALESCE(issue_name, issue_type) AS title,
               issue_status AS status,
               DATE_FORMAT(COALESCE(found_date, created_at), '%Y-%m-%d') AS updated_at
        FROM water_protection_issue
        WHERE issue_status NOT IN ('已闭环','已撤销','已合并')
          AND effective_status = 'EFFECTIVE'
        ORDER BY found_date DESC
        LIMIT 6
        """,
        lambda row: {
            "level": "黄",
            "title": row.get("title") or "水保事项",
            "source": "E",
            "status": row.get("status") or "重点关注",
            "updatedAt": row.get("updated_at") or "",
        },
    )

    add_rows(
        """
        SELECT risk_name AS title, risk_level, control_status AS status,
               DATE_FORMAT(created_at, '%Y-%m-%d') AS updated_at
        FROM safety_risk_point
        WHERE control_status <> '已销号' AND risk_level IN ('重大', '较大')
        ORDER BY FIELD(risk_level, '重大', '较大'), id
        LIMIT 6
        """,
        lambda row: {
            "level": "红" if (row.get("risk_level") or "") == "重大" else "黄",
            "title": row.get("title") or "安全风险点",
            "source": "S",
            "status": "立即督办" if (row.get("risk_level") or "") == "重大" else (row.get("status") or "重点关注"),
            "updatedAt": row.get("updated_at") or "",
        },
    )

    add_rows(
        """
        SELECT permit_name AS title, status,
               DATE_FORMAT(expire_date, '%Y-%m-%d') AS updated_at
        FROM permit_record
        WHERE status IN ('临期', '逾期')
        ORDER BY FIELD(status, '逾期', '临期'), expire_date
        LIMIT 6
        """,
        lambda row: {
            "level": "红" if (row.get("status") or "") == "逾期" else "黄",
            "title": row.get("title") or "许可事项",
            "source": "G",
            "status": "立即督办" if (row.get("status") or "") == "逾期" else "重点关注",
            "updatedAt": row.get("updated_at") or "",
        },
    )

    add_rows(
        """
        SELECT item_name AS title, status,
               DATE_FORMAT(COALESCE(deadline, created_at), '%Y-%m-%d') AS updated_at,
               COALESCE(overdue, 0) AS overdue
        FROM rectification_record
        WHERE status <> '已关闭'
        ORDER BY COALESCE(overdue, 0) DESC, deadline
        LIMIT 6
        """,
        lambda row: {
            "level": "红" if int(row.get("overdue") or 0) == 1 or (row.get("status") or "") == "逾期" else "黄",
            "title": row.get("title") or "整改事项",
            "source": "G",
            "status": (
                "立即督办"
                if int(row.get("overdue") or 0) == 1 or (row.get("status") or "") == "逾期"
                else (row.get("status") or "重点关注")
            ),
            "updatedAt": row.get("updated_at") or "",
        },
    )

    add_rows(
        """
        SELECT material_name AS title, status,
               DATE_FORMAT(COALESCE(deadline, created_at), '%Y-%m-%d') AS updated_at
        FROM compliance_material_gap
        WHERE status <> '已补齐'
        ORDER BY status = '逾期' DESC, deadline
        LIMIT 4
        """,
        lambda row: {
            "level": "蓝",
            "title": row.get("title") or "资料缺口",
            "source": "G",
            "status": row.get("status") or "持续跟踪",
            "updatedAt": row.get("updated_at") or "",
        },
    )

    add_rows(
        """
        SELECT COALESCE(appeal_content, appeal_type) AS title, status,
               DATE_FORMAT(COALESCE(accepted_date, created_at), '%Y-%m-%d') AS updated_at
        FROM appeal_record
        WHERE status <> '已办结'
        ORDER BY overdue DESC, accepted_date
        LIMIT 4
        """,
        lambda row: {
            "level": "蓝",
            "title": row.get("title") or "群众诉求",
            "source": "S",
            "status": row.get("status") or "持续跟踪",
            "updatedAt": row.get("updated_at") or "",
        },
    )

    level_rank = {"红": 0, "黄": 1, "蓝": 2}
    items.sort(key=lambda x: (level_rank.get(x.get("level") or "蓝", 9), x.get("updatedAt") or ""))
    seen: set[str] = set()
    unique: list[dict] = []
    for item in items:
        key = f"{item.get('level')}|{item.get('title')}"
        if key in seen:
            continue
        seen.add(key)
        unique.append(item)
        if len(unique) >= 12:
            break
    return unique



def get_carbon_panel_data(base: dict) -> dict:
    topic = get_carbon_topic_detail()
    if not topic:
        return (base.get("carbon") or {})
    summary = topic.get("summary") or []
    source_detail = ((topic.get("topicData") or {}).get("source") or {}).get("summary") or []
    total = next((item for item in summary if item.get("label") == "施工阶段累计碳足迹"), {"value": 0})
    reduction = next((item for item in summary if item.get("label") == "累计核算减排量"), {"value": 0})
    rate = next((item for item in summary if item.get("label") == "较基准下降"), {"value": 0})
    existing = base.get("carbon") or {}
    carbon_cost_label = topic.get("carbonCostLabel") or "低碳措施节约成本"
    carbon_cost_value = topic.get("carbonCostValue")
    carbon_cost_unit = topic.get("carbonCostUnit") or "万元"
    return {
        "metrics": [
            {
                "label": "施工阶段累计碳足迹",
                "value": total.get("value"),
                "unit": "tCO₂e",
                "sub": f"较基准下降 {rate.get('value')}%",
            },
            {
                "label": "累计核算减排量",
                "value": reduction.get("value"),
                "unit": "tCO₂e",
                "sub": f"预计全年 {(((topic.get('topicData') or {}).get('benefit') or {}).get('summary') or [{}, {}, {'value': 0}])[2].get('value', 0)} tCO₂e",
            },
            {
                "label": carbon_cost_label,
                "value": carbon_cost_value,
                "unit": carbon_cost_unit,
                "sub": "项目初步测算，尚未正式财务确认",
            },
        ],
        "carbonCostLabel": carbon_cost_label,
        "carbonCostValue": carbon_cost_value,
        "carbonCostUnit": carbon_cost_unit,
        # 首页右侧旧面板保留“其他”标签，专题弹窗仍使用可追溯的“施工运输”。
        "sources": [
            {"name": "其他" if item.get("label") == "施工运输" else item.get("label"), "value": item.get("value")}
            for item in source_detail
        ],
        "reductions": existing.get("reductions") or existing.get("measures") or [],
        "measures": existing.get("measures") or existing.get("reductions") or [],
    }


def get_monthly_panel_data(base: dict) -> dict:
    overview = get_monthly_report_overview()
    if not overview:
        return base.get("monthly") or {}
    summary = overview["summary"]
    period = overview["reportMonth"]
    active_node = next((item for item in overview["processStages"] if item.get("status") == "IN_PROGRESS"), None)
    return {
        "month": f"{period[:4]}年{int(period[5:7])}月" if period and len(period) >= 7 else period,
        "progress": overview["readinessRate"],
        "pendingCount": summary["pendingTotal"],
        "confirmCount": summary["pendingConfirmCount"],
        "currentStatus": active_node.get("label") if active_node else "报告编制",
        "expectedCompletion": None,
        "materials": [
            {
                "name": item.get("taskName"),
                "owner": item.get("responsibleRole"),
                "deadline": item.get("deadline"),
            }
            for item in overview["pendingTasks"]
        ],
    }


def get_dashboard_panels() -> dict | None:
    base = get_dashboard_panels_snapshot()
    if base is None:
        return None
    base["compliance"] = get_compliance_panel_data(base)
    base["carbon"] = get_carbon_panel_data(base)
    base["monthly"] = get_monthly_panel_data(base)
    # Overlay Demo risk-warnings when available (contract fields + click keys)
    try:
        import esg_demo_api

        risks = esg_demo_api.get_demo_risk_warnings(status="OPEN")
        if risks and risks.get("items"):
            warning_items = esg_demo_api.risk_warnings_to_panel_items(risks)
            metrics = esg_demo_api.risk_warnings_to_compliance_metrics(risks)
            compliance = base.get("compliance") or {}
            compliance["warningItems"] = warning_items
            compliance["metrics"] = metrics
            compliance["effectiveness"] = [
                {"label": "红色", "value": metrics[0]["value"]},
                {"label": "黄色", "value": metrics[1]["value"]},
                {"label": "蓝色", "value": metrics[2]["value"]},
            ]
            compliance["safeguards"] = [
                f"{w.get('title')}，{w.get('reason') or w.get('status')}"
                for w in warning_items[:3]
            ]
            base["compliance"] = compliance
            base["riskWarnings"] = risks
    except Exception as exc:
        logger.warning("demo risk overlay skipped: %s", exc)
    return base


def ensure_s01_business_tables() -> None:
    execute(
        """
        CREATE TABLE IF NOT EXISTS safety_incident_record (
          id BIGINT PRIMARY KEY,
          document_id BIGINT NULL,
          incident_date DATE NOT NULL,
          incident_name VARCHAR(255) NULL,
          incident_type VARCHAR(100) NULL,
          incident_level VARCHAR(50) NULL,
          interrupt_counting TINYINT NOT NULL DEFAULT 1,
          responsible_department VARCHAR(100) NULL,
          handling_status VARCHAR(50) NULL,
          interrupt_reason VARCHAR(255) NULL,
          created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
          INDEX idx_safety_incident_date(incident_date),
          INDEX idx_safety_incident_interrupt(interrupt_counting)
        ) ENGINE=InnoDB COMMENT='安全生产事故台账'
        """
    )
    execute(
        """
        CREATE TABLE IF NOT EXISTS construction_stage_record (
          id BIGINT PRIMARY KEY,
          stage_key VARCHAR(50) NOT NULL,
          stage_name VARCHAR(100) NOT NULL,
          stage_status VARCHAR(30) NOT NULL,
          stage_detail VARCHAR(255) NULL,
          sequence_no INT NOT NULL,
          start_date DATE NULL,
          end_date DATE NULL,
          created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
          UNIQUE KEY uk_construction_stage_key(stage_key)
        ) ENGINE=InnoDB COMMENT='项目工期主阶段'
        """
    )
    # P2.5: 中和 ensure_s01_business_tables 冲突
    # 若 P1 迁移已应用（safety_production_record 含 is_current 列），
    # 不再 UPSERT 旧 CSR 测数，避免将「主体工程施工」写回 current
    # 与 P1 测数（路基桥涵施工 / 77 天 / 旧 368 retired）冲突。
    p1_applied = query_one(
        """
        SELECT COUNT(*) AS c FROM information_schema.columns
        WHERE table_schema = DATABASE()
          AND table_name = 'safety_production_record'
          AND column_name = 'is_current'
        """
    )
    if p1_applied and int(p1_applied["c"]) > 0:
        # P1 已应用：跳过旧 CSR 种子
        return
    stages = [
        (1, "preparation", "施工准备", "completed", None, 1, "2025-07-10", "2025-10-31"),
        (2, "main-construction", "主体工程施工", "current", "路基｜桥梁｜隧道并行施工", 2, "2025-11-01", None),
        (3, "pavement", "路面及附属工程", "not_started", None, 3, None, None),
        (4, "handover", "交工验收", "not_started", None, 4, None, None),
    ]
    for stage in stages:
        execute(
            """
            INSERT INTO construction_stage_record
            (id, stage_key, stage_name, stage_status, stage_detail, sequence_no, start_date, end_date)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE
              stage_name = VALUES(stage_name),
              stage_status = VALUES(stage_status),
              stage_detail = VALUES(stage_detail),
              sequence_no = VALUES(sequence_no),
              start_date = VALUES(start_date),
              end_date = VALUES(end_date)
            """,
            stage,
        )


def month_ticks(start_date: date, end_date: date) -> list[str]:
    ticks: list[str] = []
    year = start_date.year
    month = start_date.month
    while year < end_date.year or (year == end_date.year and month <= end_date.month):
        ticks.append(f"{year}-{month:02d}")
        month += 1
        if month > 12:
            month = 1
            year += 1
    return ticks


def _resolve_s01_snapshot(scope: str | None = None) -> dict:
    """解析 S01 当前有效确认快照（首页 KPI 与详情同源）。

    冻结稿 §4 谓词：
      demo: data_nature='demo', is_demo=1, effective_status='EFFECTIVE', is_current=1
      formal: data_nature='formal', is_demo=0, effective_status='EFFECTIVE',
              verification_status='VERIFIED', confirmation_status='CONFIRMED', is_current=1
    主值: 优先使用快照列 continuous_days；正式无快照 → null。
    """
    effective_scope = scope or ("demo" if S01_ALLOW_DEMO else "formal")

    if effective_scope == "demo" and not S01_ALLOW_DEMO:
        return {
            "continuousDays": None,
            "statisticsStart": None,
            "cycleStartDate": None,
            "statisticsAsOf": None,
            "countingStatus": "CONTINUOUS",
            "latestInterruptDate": None,
            "latestInterruptReason": None,
            "pendingDeterminationCount": 0,
            "confirmationStatus": None,
            "confirmationBatchId": None,
            "demoBatchCode": None,
            "currentConstructionStage": None,
            "currentStage": None,
            "currentStageDetail": None,
            "dataNature": "formal",
            "isDemo": False,
            "scope": "formal",
            "conclusion": "待建设单位确认",
            "projectStartDate": None,
            "currentDate": None,
            "updateTime": None,
            "gateError": "S01_ALLOW_DEMO=0, demo access denied",
        }

    if effective_scope == "demo":
        where_clause = (
            "data_nature = 'demo' AND is_demo = 1 "
            "AND effective_status = 'EFFECTIVE' AND is_current = 1"
        )
        target_data_nature = "demo"
        target_is_demo = 1
    else:
        where_clause = (
            "data_nature = 'formal' AND is_demo = 0 "
            "AND effective_status = 'EFFECTIVE' "
            "AND verification_status = 'VERIFIED' "
            "AND confirmation_status = 'CONFIRMED' "
            "AND is_current = 1"
        )
        target_data_nature = "formal"
        target_is_demo = 0

    rows = query_all(
        f"""
        SELECT id, project_id, project_start_date, `current_date`,
               cycle_start_date, statistics_as_of,
               continuous_days, current_stage, current_stage_detail,
               counting_status,
               confirmation_batch_id, confirmation_status,
               verification_status, effective_status, is_current,
               data_nature, is_demo,
               confirmed_at, confirmed_by,
               update_time, created_at
        FROM safety_production_record
        WHERE {where_clause}
        ORDER BY statistics_as_of DESC, id DESC
        """
    )

    if not rows:
        return {
            "continuousDays": None,
            "statisticsStart": None,
            "cycleStartDate": None,
            "statisticsAsOf": None,
            "countingStatus": "CONTINUOUS",
            "latestInterruptDate": None,
            "latestInterruptReason": None,
            "pendingDeterminationCount": 0,
            "confirmationStatus": None,
            "confirmationBatchId": None,
            "demoBatchCode": None,
            "currentConstructionStage": None,
            "currentStage": None,
            "currentStageDetail": None,
            "dataNature": effective_scope,
            "isDemo": effective_scope == "demo",
            "scope": effective_scope,
            "conclusion": "待建设单位确认" if effective_scope == "formal" else "暂无演示数据",
            "projectStartDate": None,
            "currentDate": None,
            "updateTime": None,
        }

    if len(rows) > 1:
        logger.warning(
            "S01 gate: multiple current rows found (scope=%s, count=%d)",
            effective_scope, len(rows),
        )

    row = rows[0]

    # P2.3: 重置与待认定 — 读路径（冻结稿 §3.1）
    # 仅当同时满足才算生效重置：项目边界内 + 责任认定=RESPONSIBLE + fatality_count>=1 + 认定已生效 + 当前有效版本
    reset_incidents = query_all(
        """
        SELECT id, occurred_date, incident_date, incident_name, incident_type,
               fatality_count, injury_count,
               responsibility_determination_status,
               determination_effective_date, determination_summary,
               effective_status, is_current, data_nature, is_demo
        FROM safety_incident_record
        WHERE effective_status = 'EFFECTIVE' AND is_current = 1
          AND responsibility_determination_status = 'RESPONSIBLE'
          AND fatality_count >= 1
          AND data_nature = %s AND is_demo = %s
        ORDER BY occurred_date DESC, incident_date DESC, id DESC
        """,
        (target_data_nature, target_is_demo),
    )

    pending_incidents = query_all(
        """
        SELECT id, occurred_date, incident_date, incident_name
        FROM safety_incident_record
        WHERE effective_status = 'EFFECTIVE' AND is_current = 1
          AND responsibility_determination_status = 'PENDING'
          AND data_nature = %s AND is_demo = %s
        ORDER BY occurred_date DESC, incident_date DESC, id DESC
        """,
        (target_data_nature, target_is_demo),
    )

    # P2.4: 工期阶段 — 只读 construction_stage_record 当前有效阶段
    stage_row = query_one(
        """
        SELECT stage_name, stage_detail, stage_status
        FROM construction_stage_record
        WHERE is_current = 1 AND stage_status = 'current'
          AND data_nature = %s AND is_demo = %s
        ORDER BY sequence_no, id
        LIMIT 1
        """,
        (target_data_nature, target_is_demo),
    )

    # 主值：优先使用快照列 continuous_days
    continuous_days = row["continuous_days"]
    cycle_start_date = row["cycle_start_date"] or row["project_start_date"]
    statistics_as_of = row["statistics_as_of"] or row["current_date"]
    statistics_start = row["project_start_date"]

    # 计数状态机
    if reset_incidents:
        counting_status = "RESET_CYCLE"
        latest_interrupt = reset_incidents[0]
        latest_interrupt_date = latest_interrupt.get("occurred_date") or latest_interrupt.get("incident_date")
        latest_interrupt_reason = (
            latest_interrupt.get("incident_name")
            or latest_interrupt.get("determination_summary")
            or "安全生产责任事故"
        )
    elif pending_incidents:
        counting_status = "PENDING_DETERMINATION"
        latest_interrupt_date = None
        latest_interrupt_reason = None
    else:
        counting_status = "CONTINUOUS"
        latest_interrupt_date = None
        latest_interrupt_reason = None

    # 兼容旧枚举映射
    raw_counting = (row.get("counting_status") or "").lower()
    if raw_counting in ("interrupted", "reset") and not reset_incidents and not pending_incidents:
        counting_status = "CONTINUOUS"

    # 查询批次编码
    batch_code = None
    if row.get("confirmation_batch_id"):
        batch_row = query_one(
            "SELECT batch_code FROM s01_confirmation_batch WHERE id = %s",
            (row["confirmation_batch_id"],),
        )
        batch_code = batch_row["batch_code"] if batch_row else None

    current_stage_name = stage_row["stage_name"] if stage_row else "资料待补齐"
    current_stage_detail = stage_row["stage_detail"] if stage_row else None

    # 结论句（展示层口语；硬条件脚注由前端展示）
    as_of_str = value_for_json(statistics_as_of)
    if continuous_days is not None:
        if counting_status == "CONTINUOUS":
            conclusion = (
                f"项目开工以来，截至 {as_of_str}，已连续安全生产 {continuous_days} 天，"
                f"期间未因责任死亡事故中断。"
            )
        elif counting_status == "PENDING_DETERMINATION":
            conclusion = (
                f"项目开工以来，截至 {as_of_str}，已连续安全生产 {continuous_days} 天；"
                f"有事故待认定，认定前连续天数暂不改。"
            )
        else:
            conclusion = (
                f"项目曾因责任死亡事故中断连续计数，"
                f"当前周期自重新起算日起已连续安全生产 {continuous_days} 天。"
            )
    else:
        conclusion = "待建设单位确认"

    return {
        "continuousDays": int(continuous_days) if continuous_days is not None else None,
        "statisticsStart": value_for_json(statistics_start),
        "cycleStartDate": value_for_json(cycle_start_date),
        "statisticsAsOf": as_of_str,
        "countingStatus": counting_status,
        "latestInterruptDate": value_for_json(latest_interrupt_date) if latest_interrupt_date else None,
        "latestInterruptReason": latest_interrupt_reason,
        "pendingDeterminationCount": len(pending_incidents),
        "confirmationStatus": row.get("confirmation_status"),
        "confirmationBatchId": row.get("confirmation_batch_id"),
        "demoBatchCode": batch_code if effective_scope == "demo" else None,
        "currentConstructionStage": current_stage_name,
        "currentStage": current_stage_name,
        "currentStageDetail": current_stage_detail,
        "dataNature": row.get("data_nature", effective_scope),
        "isDemo": bool(row.get("is_demo")),
        "scope": effective_scope,
        "conclusion": conclusion,
        "projectStartDate": value_for_json(statistics_start),
        "currentDate": as_of_str,
        "updateTime": value_for_json(row["update_time"])[:16] if row.get("update_time") else None,
    }


def get_s01_detail() -> dict:
    snapshot = _resolve_s01_snapshot()
    return snapshot


def get_workspace_summary() -> dict:
    row = query_one("SELECT * FROM workspace_summary WHERE id = 1")
    if row is None:
        return {}
    return {
        "currentTodo": row["current_todo"],
        "pendingUpload": row["pending_upload"],
        "pendingCorrection": row["pending_correction"],
        "pendingSubmit": row["pending_submit"],
        "underReview": row["under_review"],
        "dueSoon": row["due_soon"],
        "completed": row["completed"],
    }


def normalize_cycle_type(cycle_type: str) -> str:
    mapping = {
        "MONTHLY": "月度",
        "MONTH": "月度",
        "QUARTERLY": "季度",
        "QUARTER": "季度",
        "ANNUAL": "年度",
        "YEARLY": "年度",
        "ONCE": "一次性",
        "ONE_TIME": "一次性",
    }
    return mapping.get((cycle_type or "").strip().upper(), cycle_type)


def get_tasks(
    module: str = "",
    status: str = "",
    keyword: str = "",
    cycle: str = "",
    cycle_type: str = "",
    deadline_start: str = "",
    deadline_end: str = "",
    assignee: str = "",
) -> dict:
    sql = "SELECT * FROM upload_task WHERE 1=1"
    params: list[Any] = []
    if module:
        sql += " AND module_code = %s"
        params.append(module)
    if status:
        sql += " AND status = %s"
        params.append(status)
    if keyword:
        sql += " AND name LIKE %s"
        params.append(f"%{keyword}%")
    if cycle:
        sql += " AND cycle LIKE %s"
        params.append(f"%{cycle}%")
    if cycle_type:
        sql += " AND cycle_type = %s"
        params.append(normalize_cycle_type(cycle_type))
    if deadline_start:
        sql += " AND deadline >= %s"
        params.append(deadline_start)
    if deadline_end:
        sql += " AND deadline <= %s"
        params.append(deadline_end)
    if assignee:
        sql += " AND (assignee_name = %s OR assignee_dept = %s)"
        params.extend([assignee, assignee])
    sql += " ORDER BY deadline ASC"
    rows = query_all(sql, tuple(params))
    return {"total": len(rows), "items": [task_row_to_item(row) for row in rows]}


def task_row_to_item(row: dict) -> dict:
    return {
        "id": row["id"],
        "name": row["name"],
        "module": row["module_code"],
        "moduleName": row["module_name"],
        "cycle": row["cycle"],
        "cycleType": row["cycle_type"],
        "deadline": value_for_json(row["deadline"]),
        "deadlineDisplay": value_for_json(row["deadline"]),
        "progressCurrent": row["progress_current"],
        "progressTotal": row["progress_total"],
        "status": row["status"],
        "nextStep": row["next_step"],
        "assignee": row.get("assignee_name"),
        "assigneeDept": row.get("assignee_dept"),
        "priorityCode": row.get("priority_code"),
    }


def get_task_detail(task_id: str) -> dict | None:
    task = query_one("SELECT * FROM upload_task WHERE id = %s", (task_id,))
    if task is None:
        return None
    req_rows = query_all("SELECT * FROM upload_task_requirement WHERE task_id = %s ORDER BY sequence_no", (task_id,))
    candidate_rows = query_all("SELECT * FROM task_candidate_document WHERE task_id = %s ORDER BY sequence_no", (task_id,))
    timeline_rows = query_all("SELECT * FROM task_review_timeline WHERE task_id = %s ORDER BY sequence_no", (task_id,))

    documents = [
        {
            "id": row["id"],
            "name": row["name"],
            "required": bool(row["required"]),
            "format": row["format_rule"],
            "status": row["status"],
            "templateAvailable": bool(row["template_available"]),
        }
        for row in req_rows
    ]
    completed = sum(1 for row in documents if row["status"] in ("已关联", "审核通过"))
    missing = sum(1 for row in documents if row["status"] == "缺失")
    abnormal = sum(1 for row in documents if row["status"] == "格式异常")

    return {
        "task": task_row_to_item(task),
        "tabs": ["资料要求", "已关联资料", "校验问题", "审核记录"],
        "documents": documents,
        "validation": {
            "completed": completed,
            "missing": missing,
            "abnormal": abnormal,
            "canSubmit": missing == 0 and abnormal == 0,
        },
        "candidateDocuments": [
            {
                "id": row["id"],
                "name": row["name"],
                "cycle": row["cycle"],
                "unit": row["unit_name"],
                "linkCount": row["link_count"],
                "matchRate": row["match_rate"],
            }
            for row in candidate_rows
        ],
        "aiRecommendation": {
            "fileName": "弃渣场巡查记录_2026-07.pdf",
            "matchRate": 96,
            "text": "该资料已用于其他流程，无需重复上传",
        },
        "aiTip": "还缺少“审核确认单”，建议下载模板后补充签章。",
        "reviewTimeline": [
            {"time": value_for_json(row["event_time"]), "action": row["action_text"]}
            for row in timeline_rows
        ],
    }


def _task_validation_from_documents(documents: list[dict]) -> dict:
    completed = sum(1 for row in documents if row["status"] in ("已关联", "审核通过"))
    missing = sum(1 for row in documents if row["status"] == "缺失")
    abnormal = sum(1 for row in documents if row["status"] == "格式异常")
    return {"completed": completed, "missing": missing, "abnormal": abnormal, "canSubmit": missing == 0 and abnormal == 0}


def _task_validation_issues(documents: list[dict]) -> list[dict]:
    issues = []
    for row in documents:
        if row["status"] == "缺失":
            issues.append(
                {
                    "id": f"missing-{row['id']}",
                    "documentRequirementId": row["id"],
                    "documentName": row["name"],
                    "issueType": "缺失",
                    "severity": "high" if row["required"] else "medium",
                    "message": f"{row['name']}尚未关联或上传，请补齐后再提交审核。",
                    "canSubmit": False,
                }
            )
        elif row["status"] == "格式异常":
            issues.append(
                {
                    "id": f"format-{row['id']}",
                    "documentRequirementId": row["id"],
                    "documentName": row["name"],
                    "issueType": "格式异常",
                    "severity": "medium",
                    "message": f"{row['name']}存在格式异常，请重新上传或从资料中心关联有效版本。",
                    "canSubmit": False,
                }
            )
    return issues


def find_matching_requirement_id(task_id: str, document_name: str, candidate_name: str = "", document_type: str = "") -> str | None:
    names = [candidate_name, document_name, document_type]
    stems = []
    for name in names:
        if not name:
            continue
        stem = name.rsplit(".", 1)[0]
        stems.append(stem)
        stems.append(stem.split("_", 1)[0])

    requirements = query_all("SELECT id, name FROM upload_task_requirement WHERE task_id = %s ORDER BY sequence_no", (task_id,))
    for req in requirements:
        req_name = req["name"]
        for stem in stems:
            if stem and (req_name in stem or stem in req_name):
                return req["id"]
    unfinished = query_one(
        """
        SELECT id
        FROM upload_task_requirement
        WHERE task_id = %s AND status NOT IN ('已关联', '审核通过')
        ORDER BY required DESC, sequence_no
        LIMIT 1
        """,
        (task_id,),
    )
    if unfinished:
        return unfinished["id"]
    return None


def candidate_document_payload(task_id: str, row: dict) -> dict:
    document_id = resolve_document_id_for_link(task_id, row["id"])
    requirement_id = None
    if document_id is not None:
        document = query_one("SELECT document_name FROM document_record WHERE id = %s", (document_id,))
        requirement_id = find_matching_requirement_id(task_id, (document or {}).get("document_name", ""), row["name"], (document or {}).get("document_type", ""))
    return {
        "id": row["id"],
        "documentId": str(document_id) if document_id is not None else None,
        "requirementId": requirement_id,
        "name": row["name"],
        "cycle": row["cycle"],
        "unit": row["unit_name"],
        "linkCount": row["link_count"],
        "matchRate": row["match_rate"],
    }


def get_task_detail(task_id: str) -> dict | None:
    task = query_one("SELECT * FROM upload_task WHERE id = %s", (task_id,))
    if task is None:
        return None
    req_rows = query_all("SELECT * FROM upload_task_requirement WHERE task_id = %s ORDER BY sequence_no", (task_id,))
    candidate_rows = query_all("SELECT * FROM task_candidate_document WHERE task_id = %s ORDER BY sequence_no", (task_id,))
    timeline_rows = query_all("SELECT * FROM task_review_timeline WHERE task_id = %s ORDER BY sequence_no", (task_id,))
    linked_rows = query_all(
        """
        SELECT r.*, d.document_name, d.document_type, d.period_value, d.version_no,
               d.validity_status, d.source_name, d.uploaded_at
        FROM document_task_relation r
        JOIN document_record d ON d.id = r.document_id
        WHERE r.task_id = %s
        ORDER BY r.linked_at DESC, r.id DESC
        """,
        (task_id,),
    )
    review_rows = query_all("SELECT * FROM review_record WHERE task_id = %s ORDER BY submit_time DESC, id DESC", (task_id,))

    documents = [
        {
            "id": row["id"],
            "name": row["name"],
            "required": bool(row["required"]),
            "format": row["format_rule"],
            "status": row["status"],
            "templateAvailable": bool(row["template_available"]),
        }
        for row in req_rows
    ]
    validation = _task_validation_from_documents(documents)

    return {
        "task": task_row_to_item(task),
        "tabs": ["资料要求", "已关联资料", "校验问题", "审核记录"],
        "documents": documents,
        "linkedDocuments": [
            {
                "relationId": row["id"],
                "documentId": str(row["document_id"]),
                "documentName": row["document_name"],
                "documentType": row["document_type"],
                "period": row["period_value"],
                "version": row["version_no"],
                "validityStatus": row["validity_status"],
                "source": row["source_name"],
                "relationType": row["relation_type"],
                "relationStatus": row["relation_status"],
                "matchScore": value_for_json(row["match_score"]),
                "linkedAt": value_for_json(row["linked_at"]),
                "uploadedAt": value_for_json(row["uploaded_at"]),
            }
            for row in linked_rows
        ],
        "validation": validation,
        "validationIssues": _task_validation_issues(documents),
        "candidateDocuments": [candidate_document_payload(task_id, row) for row in candidate_rows],
        "aiRecommendation": {
            "fileName": "弃渣场巡查记录_2026-07.pdf",
            "matchRate": 96,
            "text": "该资料已用于其他流程，无需重复上传",
        },
        "aiTip": "若存在缺失或格式异常，请先从资料中心关联有效资料或上传新资料。",
        "reviewTimeline": [
            {"time": value_for_json(row["event_time"]), "action": row["action_text"]}
            for row in timeline_rows
        ],
        "reviewRecords": [
            {
                "id": row["id"],
                "taskId": row["task_id"],
                "taskName": row["task_name"],
                "submitTime": value_for_json(row["submit_time"]),
                "status": row["status"],
                "reviewer": row["reviewer"],
                "commentSummary": row["comment_summary"],
                "nextStep": row["next_step"],
            }
            for row in review_rows
        ],
    }


def recalculate_task_progress(task_id: str) -> dict:
    documents = [
        {
            "id": row["id"],
            "name": row["name"],
            "required": bool(row["required"]),
            "status": row["status"],
        }
        for row in query_all("SELECT * FROM upload_task_requirement WHERE task_id = %s", (task_id,))
    ]
    validation = _task_validation_from_documents(documents)
    execute(
        "UPDATE upload_task SET progress_current = %s, progress_total = %s WHERE id = %s",
        (validation["completed"], len(documents), task_id),
    )
    validation["total"] = len(documents)
    return validation


def mark_task_requirement_linked(
    task_id: str,
    document_name: str,
    candidate_name: str = "",
    requirement_id: str | None = None,
    document_type: str = "",
) -> dict:
    target_requirement_id = requirement_id or find_matching_requirement_id(task_id, document_name, candidate_name, document_type)
    updated_requirement = None
    if target_requirement_id:
        execute(
            "UPDATE upload_task_requirement SET status = '已关联' WHERE id = %s AND task_id = %s",
            (target_requirement_id, task_id),
        )
        updated_requirement = query_one(
            "SELECT id, name, status FROM upload_task_requirement WHERE id = %s AND task_id = %s",
            (target_requirement_id, task_id),
        )
    progress = recalculate_task_progress(task_id)
    return {
        "requirementId": target_requirement_id,
        "requirementName": (updated_requirement or {}).get("name"),
        "progress": progress,
    }


def append_task_timeline(task_id: str, action_text: str) -> None:
    row = query_one("SELECT COALESCE(MAX(sequence_no), 0) + 1 AS next_seq FROM task_review_timeline WHERE task_id = %s", (task_id,))
    timeline_id = f"rt-{task_id}-{datetime.now().strftime('%Y%m%d%H%M%S%f')}"
    execute(
        """
        INSERT INTO task_review_timeline(id, task_id, event_time, action_text, sequence_no)
        VALUES (%s, %s, NOW(), %s, %s)
        """,
        (timeline_id, task_id, action_text, int(row["next_seq"] if row else 1)),
    )


def append_review_timeline(review_id: str, action_text: str, event_type: str, operator_name: str = "系统") -> None:
    row = query_one("SELECT COALESCE(MAX(sequence_no), 0) + 1 AS next_seq FROM review_timeline WHERE review_id = %s", (review_id,))
    execute(
        """
        INSERT INTO review_timeline(id, review_id, event_time, action_text, event_type, operator_name, sequence_no)
        VALUES (%s, %s, NOW(), %s, %s, %s, %s)
        """,
        (
            next_id("review_timeline", 970100),
            review_id,
            action_text,
            event_type,
            operator_name,
            int(row["next_seq"] if row else 1),
        ),
    )


def sync_workspace_summary() -> None:
    status_counts = {
        row["status"]: int(row["count"])
        for row in query_all("SELECT status, COUNT(*) AS count FROM upload_task GROUP BY status")
    }
    current = query_one("SELECT * FROM workspace_summary WHERE id = 1")
    if current is None:
        return
    pending_upload = max(12, status_counts.get("待上传", 0))
    pending_correction = max(3, status_counts.get("待补正", 0))
    pending_submit = max(5, status_counts.get("待提交", 0))
    under_review = max(3, status_counts.get("审核中", 0))
    completed = max(36, status_counts.get("已完成", 0) + status_counts.get("已归档", 0))
    current_todo = max(27, pending_upload + pending_correction + pending_submit + under_review)
    execute(
        """
        UPDATE workspace_summary
        SET current_todo = %s,
            pending_upload = %s,
            pending_correction = %s,
            pending_submit = %s,
            under_review = %s,
            completed = %s,
            updated_at = NOW()
        WHERE id = 1
        """,
        (current_todo, pending_upload, pending_correction, pending_submit, under_review, completed),
    )


def save_task_draft(task_id: str, payload: dict) -> dict | None:
    task = query_one("SELECT * FROM upload_task WHERE id = %s", (task_id,))
    if task is None:
        return None
    append_task_timeline(task_id, payload.get("comment") or "暂存任务办理进度")
    return {"ok": True, "taskId": task_id, "status": task["status"], "message": "已暂存任务办理进度"}


def resolve_document_id_for_link(task_id: str, raw_document_id: Any) -> int | None:
    if raw_document_id is None:
        return None

    raw_value = str(raw_document_id).strip()
    if raw_value.isdigit():
        return int(raw_value)

    candidate = query_one(
        "SELECT * FROM task_candidate_document WHERE id = %s AND task_id = %s",
        (raw_value, task_id),
    )
    if candidate is None:
        return None

    candidate_name = candidate["name"]
    document = query_one(
        """
        SELECT id
        FROM document_record
        WHERE document_name = %s
        ORDER BY uploaded_at DESC, id DESC
        LIMIT 1
        """,
        (candidate_name,),
    )
    if document is not None:
        return int(document["id"])

    stem = candidate_name.rsplit(".", 1)[0]
    document = query_one(
        """
        SELECT id
        FROM document_record
        WHERE document_name LIKE %s
        ORDER BY uploaded_at DESC, id DESC
        LIMIT 1
        """,
        (f"%{stem}%",),
    )
    if document is not None:
        return int(document["id"])

    short_name = stem.split("_", 1)[0]
    document = query_one(
        """
        SELECT id
        FROM document_record
        WHERE document_name LIKE %s
        ORDER BY uploaded_at DESC, id DESC
        LIMIT 1
        """,
        (f"%{short_name}%",),
    )
    return int(document["id"]) if document is not None else None


def link_task_document(task_id: str, payload: dict) -> dict | None:
    task = query_one("SELECT * FROM upload_task WHERE id = %s", (task_id,))
    if task is None:
        return None
    document_id = resolve_document_id_for_link(task_id, payload.get("documentId"))
    if document_id is None:
        raise ValueError("documentId 或候选资料 ID 不存在")
    document = query_one("SELECT * FROM document_record WHERE id = %s", (document_id,))
    if document is None:
        raise ValueError("documentId 不存在")
    relation_id = next_id("document_task_relation", 950100)
    execute(
        """
        INSERT INTO document_task_relation
        (id, document_id, task_id, relation_type, relation_status, match_score, linked_by, linked_at, source)
        VALUES (%s, %s, %s, 'REQUIREMENT', 'LINKED', %s, %s, NOW(), %s)
        ON DUPLICATE KEY UPDATE relation_status='LINKED', linked_at=VALUES(linked_at), source=VALUES(source)
        """,
        (
            relation_id,
            document_id,
            task_id,
            payload.get("matchScore") or 90,
            payload.get("operatorId") or 10001,
            payload.get("source") or "MANUAL",
        ),
    )
    requirement_id = payload.get("requirementId")
    if not requirement_id:
        raw_document_id = str(payload.get("documentId") or "")
        candidate = query_one(
            "SELECT * FROM task_candidate_document WHERE id = %s AND task_id = %s",
            (raw_document_id, task_id),
        )
        requirement_id = find_matching_requirement_id(
            task_id,
            document["document_name"],
            candidate["name"] if candidate else "",
        )
    linked = mark_task_requirement_linked(task_id, document["document_name"], candidate["name"] if candidate else "", requirement_id, document["document_type"])
    progress = linked["progress"]
    append_task_timeline(task_id, f"关联资料：{document['document_name']}")
    return {
        "ok": True,
        "taskId": task_id,
        "documentId": str(document_id),
        "requirementId": linked["requirementId"],
        "requirementName": linked["requirementName"],
        "progress": progress,
    }


def submit_task_review(task_id: str, payload: dict) -> dict | None:
    task = query_one("SELECT * FROM upload_task WHERE id = %s", (task_id,))
    if task is None:
        return None
    existing_review = None
    if task["status"] == "审核中":
        existing_review = query_one(
            """
            SELECT id
            FROM review_record
            WHERE task_id = %s AND status = '待审核'
            ORDER BY submit_time DESC
            LIMIT 1
            """,
            (task_id,),
        )
    if existing_review:
        validation = recalculate_task_progress(task_id)
        return {
            "ok": True,
            "taskId": task_id,
            "reviewId": existing_review["id"],
            "status": "审核中",
            "message": "该任务已在审核中，请勿重复提交",
            "validation": validation,
        }

    validation = recalculate_task_progress(task_id)
    if not validation["canSubmit"]:
        return {
            "ok": False,
            "taskId": task_id,
            "message": "所选任务存在资料缺失或格式异常，暂不可提交",
            "validation": validation,
        }
    latest_returned_review = query_one(
        """
        SELECT id
        FROM review_record
        WHERE task_id = %s AND status = '已退回'
        ORDER BY submit_time DESC, updated_at DESC
        LIMIT 1
        """,
        (task_id,),
    )
    if latest_returned_review:
        execute(
            "UPDATE review_requirement SET requirement_status = '已补正' WHERE review_id = %s",
            (latest_returned_review["id"],),
        )
        append_review_timeline(latest_returned_review["id"], "补正提交（任务资料已重新提交审核）", "RESUBMIT", payload.get("operatorName") or task.get("assignee_name") or "项目管理员")

    review_id = f"r-{task_id}-{datetime.now().strftime('%Y%m%d%H%M%S%f')}"
    operator_name = payload.get("operatorName") or task.get("assignee_name") or "项目管理员"
    comment = payload.get("comment") or "资料完整，提交审核"
    execute(
        """
        INSERT INTO review_record
        (id, task_id, task_name, module_code, module_name, submit_time, status, reviewer_id, reviewer, comment_summary, next_step)
        VALUES (%s, %s, %s, %s, %s, NOW(), '待审核', NULL, '-', %s, '查看进度')
        """,
        (review_id, task_id, task["name"], task["module_code"], task["module_name"], comment),
    )
    execute("UPDATE upload_task SET status = '审核中', next_step = '查看进度' WHERE id = %s", (task_id,))
    append_task_timeline(task_id, comment)
    append_review_timeline(review_id, f"提交审核（{operator_name} 提交任务）", "SUBMIT", operator_name)
    append_review_timeline(
        review_id,
        f"完整性校验（系统校验通过，共{validation['completed']}/{validation['total']}项资料完整）",
        "VALIDATE",
        "系统",
    )
    sync_workspace_summary()
    return {
        "ok": True,
        "taskId": task_id,
        "reviewId": review_id,
        "status": "审核中",
        "message": "已提交审核",
        "validation": validation,
    }


def approve_review(review_id: str, payload: dict) -> dict | None:
    review = query_one("SELECT * FROM review_record WHERE id = %s", (review_id,))
    if review is None:
        return None
    if review["status"] != "待审核":
        return {
            "ok": False,
            "reviewId": review_id,
            "taskId": review["task_id"],
            "status": review["status"],
            "message": "该审核记录当前状态不可重复审核",
        }
    reviewer = payload.get("reviewer") or payload.get("operatorName") or "项目审核人"
    comment = payload.get("comment") or "资料完整，审核通过"
    execute(
        """
        UPDATE review_record
        SET status = '已通过',
            reviewer = %s,
            comment_summary = %s,
            next_step = '查看结果',
            updated_at = NOW()
        WHERE id = %s
        """,
        (reviewer, comment, review_id),
    )
    execute(
        """
        UPDATE upload_task
        SET status = '已完成',
            next_step = '查看结果',
            updated_at = NOW()
        WHERE id = %s
        """,
        (review["task_id"],),
    )
    append_review_timeline(review_id, f"审核通过（{reviewer}：{comment}）", "APPROVE", reviewer)
    append_task_timeline(review["task_id"], f"审核通过：{comment}")
    sync_workspace_summary()
    return {
        "ok": True,
        "reviewId": review_id,
        "taskId": review["task_id"],
        "status": "已通过",
        "taskStatus": "已完成",
        "message": "审核已通过，任务已完成",
    }


def return_review(review_id: str, payload: dict) -> dict | None:
    review = query_one("SELECT * FROM review_record WHERE id = %s", (review_id,))
    if review is None:
        return None
    if review["status"] != "待审核":
        return {
            "ok": False,
            "reviewId": review_id,
            "taskId": review["task_id"],
            "status": review["status"],
            "message": "该审核记录当前状态不可退回",
        }
    reviewer = payload.get("reviewer") or payload.get("operatorName") or "项目审核人"
    comment = payload.get("comment") or "资料需补正后重新提交"
    requirements = payload.get("requirements") or [
        "请补充缺失资料或重新关联有效资料。",
        "请修正格式异常资料后重新提交审核。",
    ]
    if isinstance(requirements, str):
        requirements = [requirements]
    normalized_requirements = [str(item).strip() for item in requirements if str(item).strip()]
    if not normalized_requirements:
        normalized_requirements = ["请根据审核意见完成资料补正后重新提交。"]

    execute(
        """
        UPDATE review_record
        SET status = '已退回',
            reviewer = %s,
            comment_summary = %s,
            next_step = '进入补正',
            updated_at = NOW()
        WHERE id = %s
        """,
        (reviewer, comment, review_id),
    )
    execute(
        """
        UPDATE upload_task
        SET status = '待补正',
            next_step = '继续补正',
            updated_at = NOW()
        WHERE id = %s
        """,
        (review["task_id"],),
    )
    execute("DELETE FROM review_requirement WHERE review_id = %s", (review_id,))
    for sequence_no, requirement in enumerate(normalized_requirements, 1):
        execute(
            """
            INSERT INTO review_requirement(id, review_id, requirement_text, requirement_status, sequence_no)
            VALUES (%s, %s, %s, '待补正', %s)
            """,
            (next_id("review_requirement", 980100), review_id, requirement, sequence_no),
        )
    append_review_timeline(review_id, f"审核退回（{reviewer}：{comment}）", "RETURN", reviewer)
    append_task_timeline(review["task_id"], f"审核退回：{comment}")
    sync_workspace_summary()
    return {
        "ok": True,
        "reviewId": review_id,
        "taskId": review["task_id"],
        "status": "已退回",
        "taskStatus": "待补正",
        "message": "审核已退回，任务已转入待补正",
        "requirements": normalized_requirements,
    }


def get_document_summary() -> dict:
    row = query_one(
        """
        SELECT
          COUNT(*) AS sample_count,
          SUM(CASE WHEN uploaded_at >= '2026-08-01' THEN 1 ELSE 0 END) AS month_new_sample,
          SUM(CASE WHEN validity_status = '即将失效' THEN 1 ELSE 0 END) AS expiring_soon_sample
        FROM document_record
        """
    )
    sample_count = int((row or {}).get("sample_count") or 0)
    extra_count = max(0, sample_count - 10)
    return {
        "documentTotal": 368 + extra_count,
        "monthNew": 24 + extra_count,
        "pendingArchive": 6,
        "expiringSoon": max(4, int((row or {}).get("expiring_soon_sample") or 0)),
    }


def get_documents() -> dict:
    rows = query_all("SELECT * FROM document_record ORDER BY id DESC")
    extra_count = max(0, len(rows) - 10)
    return {
        "total": 368 + extra_count,
        "items": [
            {
                "id": str(row["id"]),
                "documentName": row["document_name"],
                "documentType": row["document_type"],
                "module": row["module_code"],
                "period": row["period_value"],
                "version": row["version_no"],
                "source": row["source_name"],
                "relationCount": row["relation_count"],
                "validityStatus": row["validity_status"],
                "uploadedAt": value_for_json(row["uploaded_at"]),
            }
            for row in rows
        ],
    }


def get_reviews() -> dict:
    rows = query_all("SELECT * FROM review_record ORDER BY submit_time DESC")
    status_counts = {row["status"]: int(row["count"]) for row in query_all("SELECT status, COUNT(*) AS count FROM review_record GROUP BY status")}
    pending_review = max(3, status_counts.get("待审核", 0))
    passed = max(21, status_counts.get("已通过", 0))
    returned = max(3, status_counts.get("已退回", 0))
    return {
        "statusCards": [
            {"label": "待审核", "value": pending_review, "unit": "项", "color": "#2f9cff"},
            {"label": "已通过", "value": passed, "unit": "项", "color": "#69e36f"},
            {"label": "已退回", "value": returned, "unit": "项", "color": "#ff4f5e"},
            {"label": "补正逾期", "value": 1, "unit": "项", "color": "#ffb347"},
        ],
        "items": [
            {
                "id": row["id"],
                "taskId": row["task_id"],
                "taskName": row["task_name"],
                "module": row["module_code"],
                "moduleName": row["module_name"],
                "submitTime": value_for_json(row["submit_time"]),
                "status": row["status"],
                "reviewer": row["reviewer"],
                "commentSummary": row["comment_summary"],
                "nextStep": row["next_step"],
            }
            for row in rows
        ],
    }


def get_review_detail(review_id: str) -> dict | None:
    row = query_one("SELECT * FROM review_record WHERE id = %s", (review_id,))
    if row is None:
        return None

    requirement_count = query_one(
        "SELECT COUNT(*) AS total FROM review_requirement WHERE review_id = %s",
        (review_id,),
    )
    correction_deadline = None
    if requirement_count and int(requirement_count["total"]) > 0 and row.get("submit_time"):
        correction_deadline = row["submit_time"] + timedelta(days=3)

    return {
        "id": row["id"],
        "taskId": row["task_id"],
        "taskName": row["task_name"],
        "module": row["module_code"],
        "moduleName": row["module_name"],
        "submitTime": value_for_json(row["submit_time"]),
        "status": row["status"],
        "reviewer": row["reviewer"],
        "commentSummary": row["comment_summary"],
        "nextStep": row["next_step"],
        "correctionDeadline": value_for_json(correction_deadline) if correction_deadline else None,
        "requirementCount": int(requirement_count["total"]) if requirement_count else 0,
    }


def get_review_timeline(review_id: str) -> dict:
    rows = query_all(
        """
        SELECT *
        FROM review_timeline
        WHERE review_id = %s
        ORDER BY sequence_no, event_time, id
        """,
        (review_id,),
    )
    return {
        "items": [
            {
                "id": row["id"],
                "reviewId": row["review_id"],
                "time": value_for_json(row["event_time"]),
                "action": row["action_text"],
                "eventType": row["event_type"],
                "operatorName": row["operator_name"],
            }
            for row in rows
        ]
    }


def get_review_requirements(review_id: str) -> dict:
    rows = query_all(
        """
        SELECT *
        FROM review_requirement
        WHERE review_id = %s
        ORDER BY sequence_no, id
        """,
        (review_id,),
    )
    return {
        "items": [
            {
                "id": row["id"],
                "reviewId": row["review_id"],
                "requirement": row["requirement_text"],
                "requirementText": row["requirement_text"],
                "status": row["requirement_status"],
            }
            for row in rows
        ]
    }


def get_ai_parse_queue() -> dict:
    rows = query_all("SELECT * FROM v_ai_parse_queue_current ORDER BY job_id")
    status_map = {
        "SUCCESS": "解析完成",
        "RUNNING": "匹配中 96%",
        "WAIT_CONFIRM": "待确认",
        "PENDING": "待确认",
        "ARCHIVED": "已入库",
        "FAILED": "解析失败",
    }
    progress_map = {"SUCCESS": 100, "RUNNING": 96, "WAIT_CONFIRM": 0, "PENDING": 0, "ARCHIVED": 100, "FAILED": 0}
    return {
        "items": [
            {
                "id": f"p{index + 1}",
                "jobId": row["job_id"],
                "fileId": row["file_id"],
                "fileName": row["file_name"],
                "size": format_size(row.get("file_size") or 0),
                "progress": progress_map.get(row["job_status"], 0),
                "status": status_map.get(row["job_status"], row["job_status"]),
            }
            for index, row in enumerate(rows)
        ]
    }


def format_size(size: int) -> str:
    if size >= 1024 * 1024:
        return f"{size / 1024 / 1024:.2f}MB"
    if size >= 1024:
        return f"{size / 1024:.2f}KB"
    return f"{size}B"


def find_duplicate_file(sha256_hash: str) -> dict | None:
    if not sha256_hash:
        return None
    return query_one(
        """
        SELECT f.*, d.id AS matched_document_id
        FROM file_asset f
        LEFT JOIN document_record d ON d.file_id = f.id
        WHERE f.sha256_hash = %s
        ORDER BY f.upload_time DESC, f.id DESC
        LIMIT 1
        """,
        (sha256_hash,),
    )


def create_deduplication_record(file_id: int, duplicate_file: dict | None) -> None:
    if duplicate_file is None:
        return
    execute(
        """
        INSERT INTO deduplication_record
        (id, file_id, matched_file_id, matched_document_id, match_type, match_score,
         hash_equal, name_similar, content_similar, decision_status, created_at)
        VALUES (%s, %s, %s, %s, 'EXACT_HASH', 100.00, 1, 0, 1, 'PENDING', NOW())
        """,
        (
            next_id("deduplication_record", 990100),
            file_id,
            duplicate_file["id"],
            duplicate_file.get("matched_document_id"),
        ),
    )


def create_file_asset(payload: dict) -> dict:
    file_id = next_id("file_asset", 900100)
    original_name = payload.get("originalName") or payload.get("fileName") or "未命名资料.pdf"
    file_size = int(payload.get("fileSize") or payload.get("size") or 0)
    file_ext = original_name.rsplit(".", 1)[-1].lower() if "." in original_name else ""
    sha256_hash = payload.get("sha256Hash") or hashlib.sha256(f"{original_name}|{file_size}|{datetime.now().isoformat()}".encode("utf-8")).hexdigest()
    duplicate_file = find_duplicate_file(sha256_hash)
    duplicate_status = "DUPLICATE" if duplicate_file else "UNIQUE"
    file_code = f"FILE-202607-{file_id}"
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    storage_path = payload.get("storagePath") or f"/demo/{original_name}"
    mime_type = payload.get("mimeType") or "application/octet-stream"
    uploader_name = payload.get("uploaderName") or "项目管理员"
    uploader_id = int(payload.get("uploaderId") or 10001)

    execute(
        """
        INSERT INTO file_asset
        (id, file_code, original_name, file_ext, mime_type, file_size, storage_path, storage_bucket,
         sha256_hash, upload_source, uploader_id, uploader_name, upload_time, duplicate_status, parse_status)
        VALUES (%s, %s, %s, %s, %s, %s, %s, 'local', %s, 'USER_UPLOAD', %s, %s, %s, %s, 'PENDING')
        """,
        (file_id, file_code, original_name, file_ext, mime_type, file_size, storage_path, sha256_hash, uploader_id, uploader_name, now, duplicate_status),
    )
    create_deduplication_record(file_id, duplicate_file)
    return {
        "fileId": file_id,
        "fileCode": file_code,
        "originalName": original_name,
        "fileSize": file_size,
        "storagePath": storage_path,
        "sha256Hash": sha256_hash,
        "duplicateStatus": duplicate_status,
        "matchedFileId": duplicate_file["id"] if duplicate_file else None,
        "matchedDocumentId": duplicate_file.get("matched_document_id") if duplicate_file else None,
        "parseStatus": "PENDING",
    }


def responsible_unit_for(document_type: str, module: str) -> str:
    if document_type == "工资支付资料":
        return "财务管理部"
    if module == "S":
        return "工程管理部"
    if module == "G":
        return "质量合规部"
    return "安全环保部"


def infer_valid_period(period: str, document_type: str) -> tuple[str, str]:
    if period == "2026-Q2":
        return "2026-04-01", "2026-06-30"
    if period == "2026-07":
        if document_type in {"临时用地合规资料", "高风险作业审批资料"}:
            return "2026-07-01", "2026-12-31"
        return "2026-07-01", "2026-08-31"
    return "2026-07-01", "2026-08-31"


def get_mapping_rules(document_type: str) -> list[dict]:
    return query_all(
        """
        SELECT *
        FROM ai_field_mapping_rule
        WHERE enabled = 1 AND document_type IN ('通用资料', %s)
        ORDER BY CASE WHEN document_type = '通用资料' THEN 0 ELSE 1 END, id
        """,
        (document_type,),
    )


def resolve_file_storage_path(storage_path: str | None) -> Path | None:
    if not storage_path:
        return None
    raw = Path(str(storage_path))
    candidates = [
        raw,
        SERVER_DIR / str(storage_path),
        SERVER_DIR.parent / str(storage_path),
    ]
    for candidate in candidates:
        try:
            if candidate.is_file():
                return candidate
        except OSError:
            continue
    return None


def read_uploaded_content_fields(file_row: dict) -> dict[str, Any]:
    """Read real file bytes and extract structured fields when possible."""
    empty = {
        "ok": False,
        "source": "none",
        "engine": "ESG规则解析器",
        "fields": {},
        "confidence": 0.0,
        "summary": "",
    }
    if parse_file_content is None:
        return empty
    path = resolve_file_storage_path(file_row.get("storage_path"))
    if path is None:
        return empty
    try:
        return parse_file_content(path, original_name=file_row.get("original_name") or path.name)
    except Exception as exc:  # pragma: no cover
        logger.warning("content parse failed for file_id=%s: %s", file_row.get("id"), exc)
        return empty


def inferred_field_value(field_key: str, context: dict) -> tuple[str, str, float]:
    content_fields: dict[str, str] = context.get("content_fields") or {}
    content_confidence = float(context.get("content_confidence") or 92.0)
    if field_key in content_fields and str(content_fields[field_key]).strip():
        value = str(content_fields[field_key]).strip()
        normalized = re.sub(r"[^\d.\-]", "", value) if field_key.endswith("_count") or field_key in {
            "diesel_usage", "electricity_usage", "material_usage", "carbon_emission",
            "worker_count", "payment_amount",
        } else value
        if not normalized:
            normalized = value
        return value, normalized, min(98.0, content_confidence)

    name = context["original_name"]
    document_type = context["document_type"]
    module = context["module"]
    period = context["period"]
    valid_start, valid_end = context["valid_period"]
    defaults = {
        "document_name": (name, name, 96.0),
        "document_type": (document_type, document_type, 92.0),
        "esg_module": (module, module, 95.0),
        "period": (period, period, 90.0),
        "responsible_unit": (context["responsible_unit"], context["responsible_unit"], 88.0),
        "valid_start_date": (valid_start, valid_start, 86.0),
        "valid_end_date": (valid_end, valid_end, 86.0),
        "monitor_date": (period + "-13" if period == "2026-07" else "2026-06-30", period + "-13" if period == "2026-07" else "2026-06-30", 82.0),
        "dust_exceed_count": ("1", "1", 78.0),
        "noise_exceed_count": ("1", "1", 78.0),
        "water_protection_issue_count": ("5", "5", 80.0),
        "diesel_usage": ("1280 L", "1280", 76.0),
        "electricity_usage": ("8600 kWh", "8600", 76.0),
        "material_usage": ("320 t", "320", 74.0),
        "carbon_emission": ("1360 tCO2e", "1360", 80.0),
        "risk_level": ("较大风险", "较大风险", 82.0),
        "work_location": ("K12+000-K18+000", "K12+000-K18+000", 78.0),
        "control_measure": ("专项方案审批、现场旁站、班前交底", "专项方案审批、现场旁站、班前交底", 76.0),
        "worker_count": ("23", "23", 78.0),
        "payment_amount": ("1280000 元", "1280000", 78.0),
        "payment_month": (period, period, 82.0),
        "permit_name": ("临时用地许可", "临时用地许可", 82.0),
        "permit_no": ("LYGS-TD-2026-07", "LYGS-TD-2026-07", 76.0),
        "permit_expire_date": (valid_end, valid_end, 82.0),
        "rectification_item": ("NCR整改关闭资料", "NCR整改关闭资料", 78.0),
        "rectification_status": ("待复查", "待复查", 80.0),
        "closed_date": (valid_end, valid_end, 70.0),
    }
    return defaults.get(field_key, ("", "", 60.0))


def build_parse_fields(
    original_name: str,
    document_type: str,
    module: str,
    period: str,
    content_fields: dict[str, str] | None = None,
    content_confidence: float = 0.0,
) -> list[tuple[str, str, str, str, str, float]]:
    content_fields = content_fields or {}
    valid_start = content_fields.get("valid_start_date")
    valid_end = content_fields.get("valid_end_date")
    if valid_start and valid_end:
        valid_period = (valid_start, valid_end)
    else:
        valid_period = infer_valid_period(period, document_type)
    context = {
        "original_name": original_name,
        "document_type": document_type,
        "module": module,
        "period": period,
        "responsible_unit": content_fields.get("responsible_unit") or responsible_unit_for(document_type, module),
        "valid_period": valid_period,
        "content_fields": content_fields,
        "content_confidence": content_confidence or 92.0,
    }
    fields: list[tuple[str, str, str, str, str, float]] = []
    seen: set[str] = set()
    for rule in get_mapping_rules(document_type):
        key = rule["field_key"]
        if key in seen:
            continue
        seen.add(key)
        value, normalized, confidence = inferred_field_value(key, context)
        if value == "" and not rule.get("required"):
            continue
        fields.append((key, rule["field_name"], value, normalized, rule["value_type"], confidence))

    # Content-only extras (标段/工程对象/KPI 建议等) not always present in mapping rules
    for key in CONTENT_EXTRA_FIELD_KEYS:
        if key in seen or key not in content_fields or not str(content_fields[key]).strip():
            continue
        seen.add(key)
        value = str(content_fields[key]).strip()
        if content_field_meta is not None:
            field_name, value_type = content_field_meta(key)
        else:
            field_name, value_type = key, "string"
        fields.append((key, field_name, value, value, value_type, min(98.0, content_confidence or 92.0)))
    return fields


def _match_tasks_for_parse(
    module: str,
    period: str,
    document_type: str,
    content_fields: dict[str, str],
) -> list[dict]:
    """Return up to 2 task candidates ranked by content / type / period."""
    suggested_name = (content_fields.get("suggested_task") or "").strip()
    candidates: list[dict] = []
    seen_ids: set[str] = set()

    def _push(row: dict | None, score: float, reason: str) -> None:
        if row is None:
            return
        task_id = str(row["id"])
        if task_id in seen_ids:
            return
        seen_ids.add(task_id)
        candidates.append({
            "id": row["id"],
            "name": row["name"],
            "module_code": row["module_code"],
            "match_score": score,
            "match_reason": reason,
        })

    if suggested_name:
        _push(
            query_one(
                """
                SELECT id, name, module_code FROM upload_task
                WHERE name = %s OR name LIKE %s
                ORDER BY CASE WHEN name = %s THEN 0 ELSE 1 END, deadline ASC
                LIMIT 1
                """,
                (suggested_name, f"%{suggested_name}%", suggested_name),
            ),
            96.0,
            f"文件内容建议关联任务：{suggested_name}",
        )

    type_keyword = document_type[:4] if document_type else ""
    if "水保" in document_type or "水保" in suggested_name:
        type_keyword = "水保"
    elif "碳" in document_type:
        type_keyword = "碳"
    elif "安全" in document_type:
        type_keyword = "安全"

    if type_keyword:
        _push(
            query_one(
                """
                SELECT id, name, module_code FROM upload_task
                WHERE module_code = %s AND name LIKE %s
                ORDER BY deadline ASC LIMIT 1
                """,
                (module, f"%{type_keyword}%"),
            ),
            92.0 if content_fields else 88.0,
            f"资料类型「{document_type}」与任务名称关键词匹配",
        )

    _push(
        query_one(
            """
            SELECT id, name, module_code FROM upload_task
            WHERE module_code = %s AND name LIKE %s
            ORDER BY deadline ASC LIMIT 1
            """,
            (module, f"%{period[:4]}%" if period else "%"),
        ),
        86.0,
        "ESG模块与周期特征匹配",
    )
    _push(
        query_one(
            "SELECT id, name, module_code FROM upload_task WHERE module_code = %s ORDER BY deadline ASC LIMIT 1",
            (module,),
        ),
        80.0,
        "同模块默认任务候选",
    )
    return candidates[:2]


def start_parse_job(file_id: int) -> dict:
    file_row = query_one("SELECT * FROM file_asset WHERE id = %s", (file_id,))
    if file_row is None:
        raise ValueError(f"file_id 不存在：{file_id}")

    job_id = next_id("ai_parse_job", 910100)
    job_code = f"PARSE-202607-{job_id}"
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    original_name = file_row["original_name"]

    content_result = read_uploaded_content_fields(file_row)
    content_fields: dict[str, str] = dict(content_result.get("fields") or {})
    content_ok = bool(content_result.get("ok") and content_fields)

    inferred_type = content_fields.get("document_type") or infer_document_type(original_name)
    module = content_fields.get("esg_module") or infer_module(inferred_type)
    if module not in {"E", "S", "G"}:
        module = infer_module(inferred_type)
    period = content_fields.get("period") or infer_period(original_name)
    if content_fields.get("document_name"):
        # keep original file name as document_name fallback already handled
        pass
    elif "document_name" not in content_fields:
        content_fields.setdefault("document_name", original_name)

    parse_engine = content_result.get("engine") or "ESG规则解析器"
    model_name = "sample-file-content-parser" if content_ok else "filename-rule-parser"
    confidence = float(content_result.get("confidence") or 0.0) if content_ok else 88.0
    raw_payload = {
        "document_type": inferred_type,
        "period": period,
        "module": module,
        "parse_source": content_result.get("source") or "none",
        "summary": content_result.get("summary") or "",
        "content_field_count": len(content_fields) if content_ok else 0,
    }

    execute(
        """
        INSERT INTO ai_parse_job
        (id, job_code, file_id, job_status, parse_engine, model_name, rule_version,
         started_at, finished_at, duration_ms, confidence, raw_result_json)
        VALUES (%s, %s, %s, 'WAIT_CONFIRM', %s, %s, 'V0.2-content',
                %s, %s, 1200, %s, %s)
        """,
        (
            job_id,
            job_code,
            file_id,
            parse_engine,
            model_name,
            now,
            now,
            confidence,
            json.dumps(raw_payload, ensure_ascii=False),
        ),
    )
    execute("UPDATE file_asset SET parse_status = 'WAIT_CONFIRM' WHERE id = %s", (file_id,))

    fields = build_parse_fields(
        original_name,
        inferred_type,
        module,
        period,
        content_fields=content_fields if content_ok else {},
        content_confidence=confidence if content_ok else 0.0,
    )
    field_id = next_id("ai_parse_field_result", 911100)
    for offset, field in enumerate(fields):
        execute(
            """
            INSERT INTO ai_parse_field_result
            (id, parse_job_id, field_key, field_name, field_value, normalized_value, value_type, confidence, confirm_status)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, 'PENDING')
            """,
            (field_id + offset, job_id, *field),
        )

    candidate_id = next_id("task_match_candidate", 920100)
    matched_tasks = _match_tasks_for_parse(module, period, inferred_type, content_fields if content_ok else {})
    for offset, task in enumerate(matched_tasks):
        execute(
            """
            INSERT INTO task_match_candidate
            (id, parse_job_id, file_id, document_id, task_id, task_name, module_code, match_score, match_reason, reuse_count, candidate_status)
            VALUES (%s, %s, %s, NULL, %s, %s, %s, %s, %s, 0, 'PENDING')
            """,
            (
                candidate_id + offset,
                job_id,
                file_id,
                task["id"],
                task["name"],
                task["module_code"],
                task["match_score"],
                task["match_reason"],
            ),
        )

    return {
        "jobId": job_id,
        "jobCode": job_code,
        "jobStatus": "WAIT_CONFIRM",
        "parseSource": content_result.get("source") or "none",
        "parseEngine": parse_engine,
        "confidence": confidence,
        "summary": content_result.get("summary") or "",
    }

def infer_document_type(name: str) -> str:
    if "环境监测" in name or "监测报告" in name or "扬尘监测" in name or "噪声监测" in name:
        return "环境监测报告"
    if "碳" in name:
        return "碳排放活动数据表"
    if "环保" in name or "环境问题" in name or "扬尘" in name or "噪声" in name:
        return "环保问题整改资料"
    if "高风险" in name:
        return "高风险作业审批资料"
    if "安全事故" in name or "事故台账" in name or "事故记录" in name or "中断事故" in name:
        return "安全事故台账"
    if "劳务纠纷" in name or "纠纷台账" in name or "欠薪" in name or "劳务" in name:
        return "劳务纠纷台账"
    if "群众诉求" in name or "诉求台账" in name or "投诉" in name or "信访" in name:
        return "群众诉求台账"
    if "工资" in name:
        return "工资支付资料"
    if "临时用地" in name:
        return "临时用地合规资料"
    if "合规资料" in name or "待补齐" in name or "缺口" in name or "合规性评价" in name:
        return "合规资料补齐材料"
    if "报批报建" in name or "报建" in name or "报批" in name or "手续" in name or "审批" in name:
        return "报批报建资料"
    if "NCR" in name or "整改" in name:
        return "NCR整改关闭资料"
    if "水保" in name:
        return "水保监测月报"
    if "安全" in name or "培训" in name:
        return "安全教育培训记录"
    return "通用资料"


def infer_module(document_type: str) -> str:
    if document_type in {"高风险作业审批资料", "工资支付资料", "安全教育培训记录", "安全事故台账", "劳务纠纷台账", "群众诉求台账"}:
        return "S"
    if document_type in {"临时用地合规资料", "NCR整改关闭资料"}:
        return "G"
    return "E"


def infer_period(name: str) -> str:
    if "2026-07" in name or "7月" in name:
        return "2026-07"
    if "Q2" in name:
        return "2026-Q2"
    return "2026-07"


def get_parse_job(job_id: int) -> dict | None:
    row = query_one(
        """
        SELECT j.*, f.original_name
        FROM ai_parse_job j
        JOIN file_asset f ON f.id = j.file_id
        WHERE j.id = %s
        """,
        (job_id,),
    )
    if row is None:
        return None
    raw = json_column(row.get("raw_result_json"))
    return {
        "jobId": row["id"],
        "jobCode": row["job_code"],
        "fileId": row["file_id"],
        "fileName": row["original_name"],
        "jobStatus": row["job_status"],
        "confidence": value_for_json(row["confidence"]),
        "startedAt": value_for_json(row["started_at"]),
        "finishedAt": value_for_json(row["finished_at"]),
        "parseEngine": row.get("parse_engine") or "",
        "modelName": row.get("model_name") or "",
        "parseSource": raw.get("parse_source") or "",
        "summary": raw.get("summary") or "",
    }


def get_parse_fields(job_id: int) -> dict:
    rows = query_all("SELECT * FROM ai_parse_field_result WHERE parse_job_id = %s ORDER BY id", (job_id,))
    return {
        "items": [
            {
                "id": row["id"],
                "fieldKey": row["field_key"],
                "fieldName": row["field_name"],
                "fieldValue": row["field_value"],
                "normalizedValue": row["normalized_value"],
                "valueType": row["value_type"],
                "confidence": value_for_json(row["confidence"]),
                "confirmStatus": row["confirm_status"],
                "confirmedValue": row["confirmed_value"],
            }
            for row in rows
        ]
    }


def get_match_candidates(job_id: int) -> dict:
    rows = query_all("SELECT * FROM task_match_candidate WHERE parse_job_id = %s ORDER BY match_score DESC", (job_id,))
    return {
        "items": [
            {
                "candidateId": row["id"],
                "taskId": row["task_id"],
                "taskName": row["task_name"],
                "module": row["module_code"],
                "matchScore": value_for_json(row["match_score"]),
                "matchReason": row["match_reason"],
                "reuseCount": row["reuse_count"],
                "candidateStatus": row["candidate_status"],
            }
            for row in rows
        ]
    }


def _text_contains_any(text: str, keywords: list[str]) -> bool:
    return any(keyword and keyword in text for keyword in keywords)


def _parse_decimal(value: Any, default: float = 0.0) -> float:
    if value is None:
        return default
    if isinstance(value, (int, float, Decimal)):
        return float(value)
    match = re.search(r"-?\d+(?:\.\d+)?", str(value).replace(",", ""))
    return float(match.group(0)) if match else default


def _business_domain(module: str, document_type: str, document_name: str) -> str:
    text = f"{document_type} {document_name}"
    if _text_contains_any(text, ["碳", "纰"]):
        return "CARBON"
    if module == "G":
        return "GOVERNANCE"
    if module == "S":
        if _text_contains_any(text, ["工资", "宸ヨ祫", "劳务", "纠纷", "群众", "诉求", "投诉", "信访"]):
            return "SOCIAL"
        return "SAFETY"
    return "ENVIRONMENT"


def _target_table_for_document(document_type: str, document_name: str) -> str:
    text = f"{document_type} {document_name}"
    if _text_contains_any(text, ["环境监测", "监测报告", "扬尘监测", "噪声监测"]):
        return "env_monitoring_record"
    if _text_contains_any(text, ["环保问题", "环境问题", "扬尘", "噪声"]):
        return "env_issue_record"
    if _text_contains_any(text, ["高风险", "楂橀", "作业审批"]):
        return "safety_risk_point"
    if _text_contains_any(text, ["安全事故", "事故台账", "事故记录", "中断事故"]):
        return "safety_incident_record"
    if _text_contains_any(text, ["劳务纠纷", "纠纷台账", "欠薪", "劳务争议"]):
        return "labor_dispute_record"
    if _text_contains_any(text, ["群众诉求", "诉求台账", "投诉", "信访", "来访"]):
        return "appeal_record"
    if _text_contains_any(text, ["NCR", "整改", "鏁存敼"]):
        return "rectification_record"
    if _text_contains_any(text, ["临时用地", "涓存椂鐢ㄥ湴", "许可", "许可证"]):
        return "permit_record"
    if _text_contains_any(text, ["合规资料", "待补齐", "缺口", "合规性评价"]):
        return "compliance_material_gap"
    if _text_contains_any(text, ["报批报建", "报建", "报批", "手续", "审批"]):
        return "compliance_procedure"
    if _text_contains_any(text, ["工资", "宸ヨ祫"]):
        return "salary_payment_record"
    if _text_contains_any(text, ["碳", "纰"]):
        return "carbon_emission_activity"
    if _text_contains_any(text, ["水保", "姘翠繚"]):
        return "water_protection_issue"
    return "document_record"


def _insert_ingestion_job(
    *,
    source_id: int,
    job_type: str,
    business_domain: str,
    target_table: str,
    operator_id: int,
    operator_name: str,
) -> int:
    ingestion_job_id = next_id("data_ingestion_job", 660100)
    execute(
        """
        INSERT INTO data_ingestion_job
        (id, source_id, job_type, job_status, business_domain, target_table,
         started_at, finished_at, total_count, success_count, failed_count, operator_id, operator_name)
        VALUES (%s, %s, %s, 'SUCCESS', %s, %s, NOW(), NOW(), 1, 1, 0, %s, %s)
        """,
        (ingestion_job_id, source_id, job_type, business_domain, target_table, operator_id, operator_name),
    )
    return ingestion_job_id


def _insert_quality_check(
    *,
    ingestion_job_id: int,
    source_record_key: str,
    target_table: str,
    target_record_id: int | str,
    check_status: str,
    check_message: str,
) -> None:
    execute(
        """
        INSERT INTO data_quality_check_result
        (id, ingestion_job_id, source_record_key, target_table, target_record_id,
         check_type, check_status, check_message)
        VALUES (%s, %s, %s, %s, %s, 'FIELD_COMPLETENESS', %s, %s)
        """,
        (
            next_id("data_quality_check_result", 670100),
            ingestion_job_id,
            source_record_key,
            target_table,
            str(target_record_id),
            check_status,
            check_message,
        ),
    )


def _insert_source_trace(
    *,
    ingestion_job_id: int,
    source_id: int,
    source_record_key: str,
    document_id: int,
    file_id: int,
    target_table: str,
    target_record_id: int | str,
    operation_type: str,
    trace_payload: dict,
) -> None:
    execute(
        """
        INSERT INTO source_record_trace
        (id, ingestion_job_id, source_id, source_type, source_record_key,
         document_id, file_id, target_table, target_record_id, operation_type, trace_payload)
        VALUES (%s, %s, %s, 'FILE_UPLOAD', %s, %s, %s, %s, %s, %s, %s)
        """,
        (
            next_id("source_record_trace", 680100),
            ingestion_job_id,
            source_id,
            source_record_key,
            document_id,
            file_id,
            target_table,
            str(target_record_id),
            operation_type,
            json.dumps(trace_payload, ensure_ascii=False),
        ),
    )


def _sync_confirmed_document_to_business_table(
    *,
    job_id: int,
    file_id: int,
    document_id: int,
    document_name: str,
    document_type: str,
    module: str,
    period: str,
    field_value: Any,
    operator_id: int,
    operator_name: str,
) -> dict:
    source_id = 610001
    target_table = _target_table_for_document(document_type, document_name)
    business_domain = _business_domain(module, document_type, document_name)
    ingestion_job_id = _insert_ingestion_job(
        source_id=source_id,
        job_type="FILE_PARSE_CONFIRM",
        business_domain=business_domain,
        target_table=target_table,
        operator_id=operator_id,
        operator_name=operator_name,
    )
    source_record_key = f"PARSE_JOB:{job_id}:DOC:{document_id}"
    trace_payload = {
        "parseJobId": job_id,
        "documentId": document_id,
        "documentName": document_name,
        "documentType": document_type,
        "module": module,
        "period": period,
        "syncMode": "confirm_parse_job",
    }

    synced_records: list[dict] = []
    operation_type = "INSERT"

    if target_table == "env_monitoring_record":
        target_id = next_id("env_monitoring_record", 410100)
        monitor_type = field_value("monitor_type", "扬尘")
        dust_count = int(_parse_decimal(field_value("dust_exceed_count", "1" if monitor_type == "扬尘" else "0"), 0))
        noise_count = int(_parse_decimal(field_value("noise_exceed_count", "1" if monitor_type == "噪声" else "0"), 0))
        exceed_count = max(1, dust_count + noise_count)
        execute(
            """
            INSERT INTO env_monitoring_record
            (id, document_id, monitor_date, monitor_type, exceed_count, dust_exceed_count,
             noise_exceed_count, module_code, monitor_point, factor_name, detected_value,
             initial_detected_value, recheck_detected_value, limit_value, exceed_multiple, recheck_status)
            VALUES (%s, %s, '2026-07-13', %s, %s, %s, %s, 'E', %s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                target_id,
                document_id,
                monitor_type,
                exceed_count,
                dust_count,
                noise_count,
                field_value("monitor_point", "K18+500 弃渣场监测点"),
                field_value("factor_name", "扬尘/PM10" if monitor_type == "扬尘" else "噪声/昼间等效声级"),
                field_value("detected_value", "186 μg/m³" if monitor_type == "扬尘" else "72 dB(A)"),
                field_value("initial_detected_value", field_value("detected_value", "186 μg/m³" if monitor_type == "扬尘" else "72 dB(A)")),
                field_value("recheck_detected_value", None),
                field_value("limit_value", "150 μg/m³" if monitor_type == "扬尘" else "70 dB(A)"),
                _parse_decimal(field_value("exceed_multiple", "1.24"), 1.24),
                field_value("recheck_status", "待复测"),
            ),
        )
        check_message = "已根据环境监测资料生成超标监测记录。"
    elif target_table == "water_protection_issue":
        target_id = next_id("water_protection_issue", 710100)
        issue_count = int(_parse_decimal(field_value("water_protection_issue_count", "1"), 1))
        execute(
            """
            INSERT INTO water_protection_issue
            (id, document_id, issue_status, found_date, closed_date)
            VALUES (%s, %s, '未闭环', '2026-07-13', NULL)
            """,
            (target_id, document_id),
        )
        trace_payload["extractedIssueCount"] = issue_count
        check_message = f"已根据水保资料生成未闭环问题样例，抽取问题数 {issue_count} 项。"
    elif target_table == "env_issue_record":
        target_id = next_id("env_issue_record", 420100)
        execute(
            """
            INSERT INTO env_issue_record
            (id, document_id, issue_type, issue_count, issue_status, overdue,
             found_date, closed_date, issue_name, issue_level, responsible_department, deadline, duration_days)
            VALUES (%s, %s, %s, 1, %s, 0, '2026-07-13', NULL, %s, %s, %s, '2026-08-10', 0)
            """,
            (
                target_id,
                document_id,
                field_value("issue_type", "环保问题"),
                field_value("issue_status", "整改中"),
                field_value("issue_name", document_name),
                field_value("issue_level", "一般"),
                field_value("responsible_department", "安全环保部"),
            ),
        )
        check_message = "已根据环保问题资料生成未闭环环保问题记录。"
    elif target_table == "carbon_emission_activity":
        target_id = next_id("carbon_emission_activity", 720100)
        execute(
            """
            INSERT INTO carbon_emission_activity
            (id, document_id, period_value, diesel_usage, electricity_usage, material_usage, carbon_emission)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            """,
            (
                target_id,
                document_id,
                period,
                _parse_decimal(field_value("diesel_usage", "1280")),
                _parse_decimal(field_value("electricity_usage", "8600")),
                _parse_decimal(field_value("material_usage", "320")),
                _parse_decimal(field_value("carbon_emission", "1360")),
            ),
        )
        material_id = next_id("carbon_material_usage", 720500)
        execute(
            """
            INSERT INTO carbon_material_usage
            (id, document_id, period_value, material_name, material_usage, material_unit)
            VALUES (%s, %s, %s, '主要材料', %s, 't')
            """,
            (material_id, document_id, period, _parse_decimal(field_value("material_usage", "320"))),
        )
        trace_payload["materialRecordId"] = material_id
        check_message = "已根据碳排放活动数据生成排放活动与材料用量样例。"
    elif target_table == "safety_risk_point":
        target_id = next_id("safety_risk_point", 730100)
        risk_level = field_value("risk_level", "较大风险").replace("风险", "")
        execute(
            """
            INSERT INTO safety_risk_point
            (id, document_id, risk_name, risk_level, control_status, control_measure, location, risk_type, control_start_date)
            VALUES (%s, %s, %s, %s, '持续管控', %s, %s, '高风险作业', '2026-07-13')
            """,
            (
                target_id,
                document_id,
                document_name,
                risk_level,
                field_value("control_measure", "专项方案审批与现场旁站"),
                field_value("work_location", "K12+000-K18+000"),
            ),
        )
        check_message = "已根据高风险作业资料生成安全风险点管控记录。"
    elif target_table == "safety_incident_record":
        ensure_s01_business_tables()
        target_id = next_id("safety_incident_record", 530100)
        execute(
            """
            INSERT INTO safety_incident_record
            (id, document_id, incident_date, incident_name, incident_type, incident_level,
             interrupt_counting, responsible_department, handling_status, interrupt_reason)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                target_id,
                document_id,
                field_value("incident_date", "2026-07-01"),
                field_value("incident_name", document_name),
                field_value("incident_type", "安全生产事故"),
                field_value("incident_level", "一般"),
                0 if field_value("interrupt_counting", "1") in {"0", "否", "不计入"} else 1,
                field_value("responsible_department", "安全环保部"),
                field_value("handling_status", "已记录"),
                field_value("interrupt_reason", "触发连续安全生产记录中断条件"),
            ),
        )
        check_message = "已根据安全事故台账生成连续安全生产中断记录。"
    elif target_table == "labor_dispute_record":
        target_id = next_id("labor_dispute_record", 510100)
        execute(
            """
            INSERT INTO labor_dispute_record
            (id, document_id, dispute_type, status, involved_people, overdue, created_at,
             dispute_name, occurred_date, amount_wan, responsible_department, closed_date)
            VALUES (%s, %s, %s, %s, %s, %s, NOW(), %s, %s, %s, %s, NULL)
            """,
            (
                target_id,
                document_id,
                field_value("dispute_type", "工资支付"),
                field_value("dispute_status", "协调中"),
                int(_parse_decimal(field_value("involved_people", "5"), 5)),
                1 if field_value("overdue", "0") in {"1", "是", "逾期"} else 0,
                field_value("dispute_name", document_name),
                field_value("occurred_date", "2026-07-13"),
                _parse_decimal(field_value("amount_wan", "12"), 12),
                field_value("responsible_department", "财务管理部"),
            ),
        )
        check_message = "已根据劳务纠纷资料生成未办结劳务纠纷记录。"
    elif target_table == "appeal_record":
        target_id = next_id("appeal_record", 520100)
        overdue_flag = 1 if field_value("overdue", "0") in {"1", "是", "逾期"} else 0
        execute(
            """
            INSERT INTO appeal_record
            (id, document_id, appeal_type, status, source_channel, overdue, created_at,
             appeal_content, accepted_date, location, deadline, closed_date, duration_days)
            VALUES (%s, %s, %s, %s, %s, %s, NOW(), %s, %s, %s, %s, NULL, %s)
            """,
            (
                target_id,
                document_id,
                field_value("appeal_type", "群众诉求"),
                field_value("appeal_status", "办理中" if not overdue_flag else "逾期"),
                field_value("source_channel", "现场来访"),
                overdue_flag,
                field_value("appeal_content", document_name),
                field_value("accepted_date", "2026-07-13"),
                field_value("location", "K18+500 弃渣场"),
                field_value("deadline", "2026-07-20"),
                int(_parse_decimal(field_value("duration_days", "7"), 7)),
            ),
        )
        check_message = "已根据群众诉求资料生成未办结群众诉求记录。"
    elif target_table == "salary_payment_record":
        target_id = next_id("salary_payment_record", 740100)
        execute(
            """
            INSERT INTO salary_payment_record
            (id, document_id, payment_month, worker_count, payment_amount, payment_status)
            VALUES (%s, %s, %s, %s, %s, '已确认')
            """,
            (
                target_id,
                document_id,
                field_value("payment_month", period),
                int(_parse_decimal(field_value("worker_count", "23"), 23)),
                _parse_decimal(field_value("payment_amount", "1280000"), 1280000),
            ),
        )
        check_message = "已根据工资支付资料生成工资支付确认记录。"
    elif target_table == "permit_record":
        target_id = next_id("permit_record", 750100)
        expire_date = field_value("permit_expire_date", "2026-07-30")
        permit_status = "临期"
        if expire_date < "2026-07-13":
            permit_status = "逾期"
        elif expire_date > "2026-08-12":
            permit_status = "有效"
        execute(
            """
            INSERT INTO permit_record
            (id, document_id, permit_name, permit_no, expire_date, status, permit_type, responsible_department)
            VALUES (%s, %s, %s, %s, %s, %s, '临时用地', '工程管理部')
            """,
            (
                target_id,
                document_id,
                field_value("permit_name", "临时用地许可"),
                field_value("permit_no", f"LYGS-PERMIT-{document_id}"),
                expire_date,
                permit_status,
            ),
        )
        check_message = "已根据许可资料生成许可台账记录。"
    elif target_table == "compliance_procedure":
        target_id = next_id("compliance_procedure", 310100)
        execute(
            """
            INSERT INTO compliance_procedure
            (id, document_id, procedure_name, status, impact_node, overdue, procedure_type,
             deadline, responsible_department, progress_percent, completed_date, expected_complete_date)
            VALUES (%s, %s, %s, %s, %s, 0, %s, '2026-08-10', %s, %s, NULL, '2026-07-31')
            """,
            (
                target_id,
                document_id,
                field_value("procedure_name", document_name),
                field_value("procedure_status", "待批复"),
                field_value("impact_node", "报批报建"),
                field_value("procedure_type", "行政许可"),
                field_value("responsible_department", "工程管理部"),
                int(_parse_decimal(field_value("progress_percent", "50"), 50)),
            ),
        )
        check_message = "已根据报批报建资料生成未完成合规手续记录。"
    elif target_table == "compliance_material_gap":
        gap = query_one(
            """
            SELECT *
            FROM compliance_material_gap
            WHERE status <> '已补齐'
            ORDER BY status = '逾期' DESC, deadline, id
            LIMIT 1
            """
        )
        if gap is None:
            target_id = next_id("compliance_material_gap", 340100)
            execute(
                """
                INSERT INTO compliance_material_gap
                (id, task_id, material_name, status, responsible_unit, module_code, deadline, action_text)
                VALUES (%s, NULL, %s, '已补齐', %s, 'G', '2026-07-25', '已补齐')
                """,
                (target_id, field_value("material_name", document_name), responsible_unit),
            )
        else:
            target_id = int(gap["id"])
            execute(
                """
                UPDATE compliance_material_gap
                SET status = '已补齐', action_text = '已补齐'
                WHERE id = %s
                """,
                (target_id,),
            )
        operation_type = "UPDATE"
        check_message = "已根据合规资料上传结果更新合规资料缺口状态。"
    elif target_table == "rectification_record":
        target_id = next_id("rectification_record", 760100)
        status = field_value("rectification_status", "待复查")
        closed_date = field_value("closed_date", "") if status in {"已关闭", "已销项"} else None
        execute(
            """
            INSERT INTO rectification_record
            (id, document_id, item_name, status, source_type, overdue, closed_date,
             issue_level, deadline, responsible_department, check_batch)
            VALUES (%s, %s, %s, %s, '资料上传确认', 0, %s, '一般', '2026-08-10', '工程管理部', 'P03智能入库')
            """,
            (target_id, document_id, field_value("rectification_item", document_name), status, closed_date),
        )
        check_message = "已根据整改关闭资料生成整改闭环记录。"
    else:
        target_id = document_id
        check_message = "资料已确认入库，暂未配置对应业务闭环表，保留资料级追溯。"

    _insert_quality_check(
        ingestion_job_id=ingestion_job_id,
        source_record_key=source_record_key,
        target_table=target_table,
        target_record_id=target_id,
        check_status="PASS",
        check_message=check_message,
    )
    _insert_source_trace(
        ingestion_job_id=ingestion_job_id,
        source_id=source_id,
        source_record_key=source_record_key,
        document_id=document_id,
        file_id=file_id,
        target_table=target_table,
        target_record_id=target_id,
        operation_type=operation_type,
        trace_payload=trace_payload,
    )
    synced_records.append({"targetTable": target_table, "targetRecordId": target_id, "operationType": operation_type})
    return {
        "ingestionJobId": ingestion_job_id,
        "sourceRecordKey": source_record_key,
        "businessDomain": business_domain,
        "targetTable": target_table,
        "businessRecords": synced_records,
    }


def confirm_parse_job(job_id: int, payload: dict) -> dict:
    job = query_one("SELECT * FROM ai_parse_job WHERE id = %s", (job_id,))
    if job is None:
        raise ValueError(f"parse_job 不存在：{job_id}")

    fields = {row["field_key"]: row for row in query_all("SELECT * FROM ai_parse_field_result WHERE parse_job_id = %s", (job_id,))}
    confirmed_fields = payload.get("confirmedFields") or []
    for field in confirmed_fields:
        execute(
            """
            UPDATE ai_parse_field_result
            SET confirmed_value = %s, confirm_status = 'CONFIRMED', confirmed_by = %s, confirmed_at = NOW()
            WHERE parse_job_id = %s AND field_key = %s
            """,
            (field.get("confirmedValue"), payload.get("operatorId") or 10001, job_id, field.get("fieldKey")),
        )

    def field_value(key: str, default: str = "") -> str:
        override = next((item.get("confirmedValue") for item in confirmed_fields if item.get("fieldKey") == key), None)
        if override is not None:
            return override
        row = fields.get(key)
        return (row or {}).get("normalized_value") or (row or {}).get("field_value") or default

    document_id = next_id("document_record", 930100)
    document_code = f"DOC-202607-{document_id}"
    document_name = field_value("document_name", f"解析资料_{document_id}")
    document_type = field_value("document_type", "通用资料")
    module = field_value("esg_module", infer_module(document_type))
    period = field_value("period", "2026-07")
    responsible_unit = field_value("responsible_unit", "项目管理部")
    default_valid_start, default_valid_end = infer_valid_period(period, document_type)
    valid_start_date = field_value("valid_start_date", default_valid_start)
    valid_end_date = field_value("valid_end_date", default_valid_end)

    execute(
        """
        INSERT INTO document_record
        (id, document_code, document_name, document_type, module_code, period_value, version_no, source_name,
         relation_count, validity_status, document_status, confirm_status, file_id, parse_job_id,
         responsible_unit, valid_start_date, valid_end_date, uploaded_at)
        VALUES (%s, %s, %s, %s, %s, %s, 'V1', 'ESG智能入库', 0, '有效', 'ACTIVE', 'CONFIRMED',
                %s, %s, %s, %s, %s, NOW())
        """,
        (
            document_id,
            document_code,
            document_name,
            document_type,
            module,
            period,
            job["file_id"],
            job_id,
            responsible_unit,
            valid_start_date,
            valid_end_date,
        ),
    )
    execute(
        """
        INSERT INTO document_version
        (id, document_id, file_id, version_no, version_desc, change_type, uploaded_by, uploaded_at, is_current)
        VALUES (%s, %s, %s, 'V1', '智能入库确认生成首版资料', 'CREATE', %s, NOW(), 1)
        """,
        (next_id("document_version", 940100), document_id, job["file_id"], payload.get("operatorId") or 10001),
    )
    execute("UPDATE ai_parse_job SET job_status = 'ARCHIVED' WHERE id = %s", (job_id,))
    execute("UPDATE file_asset SET parse_status = 'ARCHIVED' WHERE id = %s", (job["file_id"],))

    accepted_ids = payload.get("acceptedCandidateIds") or []
    linked_tasks: list[dict] = []
    for candidate_id in accepted_ids:
        candidate = query_one("SELECT * FROM task_match_candidate WHERE id = %s", (candidate_id,))
        if candidate is None:
            continue
        relation_id = next_id("document_task_relation", 950100)
        execute(
            """
            INSERT INTO document_task_relation
            (id, document_id, task_id, relation_type, relation_status, match_score, linked_by, linked_at, source)
            VALUES (%s, %s, %s, 'REQUIREMENT', 'LINKED', %s, %s, NOW(), 'AI_MATCH')
            """,
            (relation_id, document_id, candidate["task_id"], candidate["match_score"], payload.get("operatorId") or 10001),
        )
        execute("UPDATE task_match_candidate SET candidate_status = 'ACCEPTED', document_id = %s, confirmed_by = %s, confirmed_at = NOW() WHERE id = %s", (document_id, payload.get("operatorId") or 10001, candidate_id))
        linked = mark_task_requirement_linked(candidate["task_id"], document_name, candidate["task_name"], document_type=document_type)
        append_task_timeline(
            candidate["task_id"],
            f"智能入库关联资料：{document_name}" + (f"（匹配要求：{linked['requirementName']}）" if linked.get("requirementName") else ""),
        )
        linked_tasks.append(
            {
                "taskId": candidate["task_id"],
                "taskName": candidate["task_name"],
                "requirementId": linked["requirementId"],
                "requirementName": linked["requirementName"],
                "progress": linked["progress"],
            }
        )

    execute(
        """
        INSERT INTO manual_confirmation_log
        (id, target_type, target_id, action_type, before_json, after_json, comment, operator_id, operator_name, operated_at)
        VALUES (%s, 'PARSE_JOB', %s, 'CONFIRM_ARCHIVE', NULL, JSON_OBJECT('documentId', %s), %s, %s, %s, NOW())
        """,
        (next_id("manual_confirmation_log", 960100), job_id, document_id, payload.get("comment"), payload.get("operatorId") or 10001, payload.get("operatorName") or "项目管理员"),
    )
    ingestion_result = _sync_confirmed_document_to_business_table(
        job_id=job_id,
        file_id=job["file_id"],
        document_id=document_id,
        document_name=document_name,
        document_type=document_type,
        module=module,
        period=period,
        field_value=field_value,
        operator_id=payload.get("operatorId") or 10001,
        operator_name=payload.get("operatorName") or "项目管理员",
    )
    linked_count = len(accepted_ids)
    if linked_count:
        execute("UPDATE document_record SET relation_count = %s WHERE id = %s", (linked_count, document_id))

    return {
        "documentId": document_id,
        "documentCode": document_code,
        "documentStatus": "ACTIVE",
        "linkedTaskCount": linked_count,
        "linkedTasks": linked_tasks,
        **ingestion_result,
    }


def get_document_detail(document_id: int) -> dict | None:
    row = query_one(
        """
        SELECT d.*, f.original_name, f.file_ext, f.mime_type, f.file_size, f.sha256_hash, f.upload_source, f.upload_time
        FROM document_record d
        LEFT JOIN file_asset f ON f.id = d.file_id
        WHERE d.id = %s
        """,
        (document_id,),
    )
    if row is None:
        return None
    return {
        "id": str(row["id"]),
        "documentCode": row["document_code"],
        "documentName": row["document_name"],
        "documentType": row["document_type"],
        "module": row["module_code"],
        "period": row["period_value"],
        "version": row["version_no"],
        "source": row["source_name"],
        "relationCount": row["relation_count"],
        "validityStatus": row["validity_status"],
        "documentStatus": row["document_status"],
        "confirmStatus": row["confirm_status"],
        "responsibleUnit": row["responsible_unit"],
        "validStartDate": value_for_json(row["valid_start_date"]),
        "validEndDate": value_for_json(row["valid_end_date"]),
        "uploadedAt": value_for_json(row["uploaded_at"]),
        "file": {
            "fileId": row["file_id"],
            "originalName": row["original_name"] or row["document_name"],
            "fileExt": row["file_ext"],
            "mimeType": row["mime_type"],
            "fileSize": row["file_size"],
            "fileSizeText": format_size(row["file_size"] or 0),
            "sha256Hash": row["sha256_hash"],
            "uploadSource": row["upload_source"],
            "uploadTime": value_for_json(row["upload_time"]),
        },
        "tags": infer_document_tags(row),
        "isUnique": True,
    }


def infer_document_tags(row: dict) -> list[str]:
    tags = [row["document_type"], row["module_code"]]
    if row.get("source_name"):
        tags.append(row["source_name"])
    if row.get("period_value"):
        tags.append(row["period_value"])
    return [str(tag) for tag in tags if tag]


def get_document_versions(document_id: int) -> dict:
    rows = query_all(
        """
        SELECT v.*, u.display_name AS uploaded_by_name
        FROM document_version v
        LEFT JOIN user_account u ON u.id = v.uploaded_by
        WHERE v.document_id = %s
        ORDER BY v.uploaded_at DESC, v.id DESC
        """,
        (document_id,),
    )
    if not rows:
        doc = query_one("SELECT * FROM document_record WHERE id = %s", (document_id,))
        if doc is None:
            return {"items": []}
        return {
            "items": [
                {
                    "id": f"v-{doc['id']}",
                    "documentId": str(doc["id"]),
                    "versionNo": doc["version_no"],
                    "versionDesc": "当前资料版本",
                    "changeType": "CURRENT",
                    "uploadedBy": doc.get("created_by"),
                    "uploadedByName": "系统",
                    "uploadedAt": value_for_json(doc["uploaded_at"]),
                    "isCurrent": True,
                }
            ]
        }
    return {
        "items": [
            {
                "id": row["id"],
                "documentId": str(row["document_id"]),
                "fileId": row["file_id"],
                "versionNo": row["version_no"],
                "versionDesc": row["version_desc"],
                "changeType": row["change_type"],
                "uploadedBy": row["uploaded_by"],
                "uploadedByName": row["uploaded_by_name"] or "系统",
                "uploadedAt": value_for_json(row["uploaded_at"]),
                "isCurrent": bool(row["is_current"]),
            }
            for row in rows
        ]
    }


def get_document_relations(document_id: int) -> dict:
    rows = query_all(
        """
        SELECT r.*, t.name AS task_name, t.module_code, t.module_name, t.cycle, t.status AS task_status
        FROM document_task_relation r
        LEFT JOIN upload_task t ON t.id = r.task_id
        WHERE r.document_id = %s
        ORDER BY r.linked_at DESC, r.id DESC
        """,
        (document_id,),
    )
    return {
        "items": [
            {
                "id": row["id"],
                "documentId": str(row["document_id"]),
                "taskId": row["task_id"],
                "taskName": row["task_name"] or row["task_id"],
                "module": row["module_code"],
                "moduleName": row["module_name"],
                "cycle": row["cycle"],
                "status": row["task_status"] or row["relation_status"],
                "relationType": row["relation_type"],
                "relationStatus": row["relation_status"],
                "matchScore": value_for_json(row["match_score"]),
                "source": row["source"],
                "referenceCount": 1,
                "lastReference": value_for_json(row["linked_at"]),
            }
            for row in rows
        ]
    }


def json_value(value: Any, default: Any = None) -> Any:
    if value is None:
        return default
    if isinstance(value, (dict, list)):
        return value
    if isinstance(value, (bytes, bytearray)):
        value = value.decode("utf-8")
    if isinstance(value, str):
        return json.loads(value)
    return value


def get_gis_layers(
    project_id: str = "LUOYI-ESG",
    section_id: str | None = None,
    current_time: str | None = None,
    visible_layer_ids: list[str] | None = None,
) -> dict:
    params: list[Any] = [project_id]
    where = ["project_id = %s", "enabled = 1"]
    if visible_layer_ids:
        placeholders = ", ".join(["%s"] * len(visible_layer_ids))
        where.append(f"id IN ({placeholders})")
        params.extend(visible_layer_ids)
    rows = query_all(
        f"""
        SELECT id, name, category, geometry_type, enabled, object_type, source_type,
               source_url, style_json, fields_json, feature_count, display_order
        FROM gis_layer
        WHERE {" AND ".join(where)}
        ORDER BY display_order, id
        """,
        tuple(params),
    )
    return {
        "code": 0,
        "data": [
            {
                "id": row["id"],
                "name": row["name"],
                "geometryType": row["geometry_type"],
                "enabled": bool(row["enabled"]),
                "objectType": row["object_type"],
                "featureCount": int(row["feature_count"] or 0),
                "fields": json_value(row["fields_json"], []),
                "source": {"type": "api", "url": row["source_url"]},
                "style": json_value(row["style_json"], {}),
            }
            for row in rows
        ],
        "meta": {
            "projectId": project_id,
            "sectionId": section_id,
            "currentTime": current_time,
            "total": len(rows),
            "dataSource": "mysql",
            "dataNature": "business",
        },
    }


GIS_RELATION_TYPE_LABELS = {
    "environment_problem": "环保问题",
    "safety_risk": "安全风险",
    "inspection_record": "巡查记录",
    "compliance_document": "合规资料",
    "monthly_report": "月报资料",
}

GIS_RELATION_TARGETS = {
    "environment_problem": {
        "kpiCode": "E02",
        "module": "环境环保",
        "moduleGroup": "E",
        "actionLabel": "查看环保问题来源",
    },
    "safety_risk": {
        "kpiCode": "S02",
        "module": "社会责任",
        "moduleGroup": "S",
        "actionLabel": "查看安全风险来源",
    },
    "inspection_record": {
        "kpiCode": None,
        "module": "项目现场一张图",
        "moduleGroup": "GIS",
        "actionLabel": "查看巡查来源",
    },
    "compliance_document": {
        "kpiCode": "G04",
        "module": "治理合规",
        "moduleGroup": "G",
        "actionLabel": "查看合规资料来源",
    },
    "monthly_report": {
        "kpiCode": None,
        "module": "月报管理",
        "moduleGroup": "REPORT",
        "actionLabel": "查看月报资料来源",
    },
}

GIS_RELATION_PENDING_STATUSES = {
    "整改中",
    "待复查",
    "待销项",
    "持续管控",
    "关注",
    "逾期",
}


def gis_relation_items(rows: list[dict]) -> list[dict]:
    return [
        {
            "type": item["relation_type"],
            "typeLabel": GIS_RELATION_TYPE_LABELS.get(item["relation_type"], item["relation_type"]),
            "code": item["relation_code"],
            "name": item["relation_name"],
            "status": item["relation_status"],
            "riskLevel": item["risk_level"],
            "sourceTable": item["source_table"],
            "sourceId": item["source_id"],
            "summary": item["summary"],
            "updatedAt": value_for_json(item["updated_at"]),
        }
        for item in rows
    ]


def gis_relation_summary(rows: list[dict]) -> dict:
    by_type: dict[str, dict] = {}
    pending_count = 0
    high_risk_count = 0
    for item in rows:
        relation_type = item["relation_type"]
        bucket = by_type.setdefault(
            relation_type,
            {
                "type": relation_type,
                "typeLabel": GIS_RELATION_TYPE_LABELS.get(relation_type, relation_type),
                "count": 0,
            },
        )
        bucket["count"] += 1
        status = str(item.get("relation_status") or "")
        if status in GIS_RELATION_PENDING_STATUSES or "逾期" in status:
            pending_count += 1
        risk_level = item.get("risk_level")
        if risk_level is not None and int(risk_level) >= 3:
            high_risk_count += 1
    return {
        "total": len(rows),
        "pendingCount": pending_count,
        "highRiskCount": high_risk_count,
        "byType": list(by_type.values()),
    }


def get_gis_relation_rows(project_id: str, feature_ids: list[str]) -> dict[str, list[dict]]:
    if not feature_ids:
        return {}
    placeholders = ", ".join(["%s"] * len(feature_ids))
    rows = query_all(
        f"""
        SELECT feature_id, relation_type, relation_code, relation_name, relation_status,
               risk_level, source_table, source_id, summary, updated_at
        FROM gis_feature_business_relation
        WHERE project_id = %s AND feature_id IN ({placeholders})
        ORDER BY risk_level DESC, id
        """,
        tuple([project_id, *feature_ids]),
    )
    grouped: dict[str, list[dict]] = {}
    for row in rows:
        grouped.setdefault(row["feature_id"], []).append(row)
    return grouped


def get_gis_features(
    project_id: str = "LUOYI-ESG",
    layer_id: str | None = None,
    section_id: str | None = None,
    current_time: str | None = None,
) -> dict:
    params: list[Any] = [project_id]
    where = ["project_id = %s"]
    if layer_id:
        where.append("layer_id = %s")
        params.append(layer_id)
    if section_id:
        where.append("section_id = %s")
        params.append(section_id)

    rows = query_all(
        f"""
        SELECT f.id, f.layer_id, f.object_type, f.name, f.geometry_json, f.properties_json,
               f.status, f.risk_level, f.updated_at,
               s.status_code AS business_status_code,
               s.status_label AS business_status_label,
               s.dashboard_title,
               s.dashboard_summary_json,
               s.dashboard_note,
               s.preview_detail_json,
               s.target_module,
               s.target_route
        FROM gis_feature f
        LEFT JOIN gis_feature_business_summary s
          ON s.feature_id = f.id AND s.project_id = f.project_id
        WHERE {" AND ".join([item.replace("project_id", "f.project_id").replace("layer_id", "f.layer_id").replace("section_id", "f.section_id") for item in where])}
        ORDER BY f.layer_id, f.id
        """,
        tuple(params),
    )
    relations_by_feature = get_gis_relation_rows(project_id, [row["id"] for row in rows])
    return {
        "code": 0,
        "data": [
            {
                "id": row["id"],
                "layerId": row["layer_id"],
                "objectType": row["object_type"],
                "name": row["name"],
                "geometry": json_value(row["geometry_json"], {}),
                "properties": json_value(row["properties_json"], {}),
                "status": row["status"],
                "statusLabel": row.get("business_status_label"),
                "riskLevel": row["risk_level"],
                "businessSummary": {
                    "statusCode": row.get("business_status_code"),
                    "statusLabel": row.get("business_status_label"),
                    "title": row.get("dashboard_title"),
                    "dashboardRows": json_value(row.get("dashboard_summary_json"), []),
                    "dashboardNote": row.get("dashboard_note"),
                    "previewRows": json_value(row.get("preview_detail_json"), []),
                    "targetModule": row.get("target_module"),
                    "targetRoute": row.get("target_route"),
                }
                if row.get("dashboard_summary_json") is not None
                else None,
                "relationSummary": gis_relation_summary(relations_by_feature.get(row["id"], [])),
                "updatedAt": value_for_json(row["updated_at"]),
            }
            for row in rows
        ],
        "meta": {
            "projectId": project_id,
            "layerId": layer_id,
            "sectionId": section_id,
            "currentTime": current_time,
            "total": len(rows),
        },
    }


def get_gis_feature_detail(
    feature_id: str,
    project_id: str = "LUOYI-ESG",
) -> dict:
    row = query_one(
        """
        SELECT f.id, f.layer_id, f.object_type, f.name, f.status, f.risk_level, f.updated_at,
               s.status_code AS business_status_code,
               s.status_label AS business_status_label,
               s.dashboard_title,
               s.dashboard_summary_json,
               s.dashboard_note,
               s.preview_detail_json,
               s.target_module,
               s.target_route
        FROM gis_feature f
        LEFT JOIN gis_feature_business_summary s
          ON s.feature_id = f.id AND s.project_id = f.project_id
        WHERE f.id = %s AND f.project_id = %s
        """,
        (feature_id, project_id),
    )
    if row is None:
        return {"code": 404, "message": "GIS feature not found", "data": None}

    relation_rows = get_gis_relation_rows(project_id, [feature_id]).get(feature_id, [])
    return {
        "code": 0,
        "data": {
            "id": row["id"],
            "layerId": row["layer_id"],
            "objectType": row["object_type"],
            "name": row["name"],
            "status": row["status"],
            "statusLabel": row.get("business_status_label"),
            "riskLevel": row["risk_level"],
            "businessSummary": {
                "statusCode": row.get("business_status_code"),
                "statusLabel": row.get("business_status_label"),
                "title": row.get("dashboard_title"),
                "dashboardRows": json_value(row.get("dashboard_summary_json"), []),
                "dashboardNote": row.get("dashboard_note"),
                "previewRows": json_value(row.get("preview_detail_json"), []),
                "targetModule": row.get("target_module"),
                "targetRoute": row.get("target_route"),
            }
            if row.get("dashboard_summary_json") is not None
            else None,
            "relationSummary": gis_relation_summary(relation_rows),
            "relations": gis_relation_items(relation_rows),
            "updatedAt": value_for_json(row["updated_at"]),
        },
    }


def get_gis_feature_relations(
    feature_id: str,
    project_id: str = "LUOYI-ESG",
) -> dict:
    feature = query_one(
        """
        SELECT id, name, object_type
        FROM gis_feature
        WHERE id = %s AND project_id = %s
        """,
        (feature_id, project_id),
    )
    if feature is None:
        return {"code": 404, "message": "GIS feature not found", "data": None}
    relation_rows = get_gis_relation_rows(project_id, [feature_id]).get(feature_id, [])
    return {
        "code": 0,
        "data": {
            "featureId": feature_id,
            "featureName": feature["name"],
            "objectType": feature["object_type"],
            "summary": gis_relation_summary(relation_rows),
            "items": gis_relation_items(relation_rows),
        },
        "meta": {
            "projectId": project_id,
            "total": len(relation_rows),
        },
    }


def get_gis_feature_business_links(
    feature_id: str,
    project_id: str = "LUOYI-ESG",
) -> dict:
    feature = query_one(
        """
        SELECT f.id, f.name, f.object_type,
               s.status_label, s.dashboard_title
        FROM gis_feature f
        LEFT JOIN gis_feature_business_summary s
          ON s.feature_id = f.id AND s.project_id = f.project_id
        WHERE f.id = %s AND f.project_id = %s
        """,
        (feature_id, project_id),
    )
    if feature is None:
        return {"code": 404, "message": "GIS feature not found", "data": None}

    relation_rows = get_gis_relation_rows(project_id, [feature_id]).get(feature_id, [])
    items = []
    for item in gis_relation_items(relation_rows):
        target = GIS_RELATION_TARGETS.get(item["type"], {})
        items.append(
            {
                "id": f"{feature_id}:{item.get('type')}:{item.get('code') or item.get('sourceId') or item.get('name')}",
                "type": item["type"],
                "typeLabel": item.get("typeLabel"),
                "code": item.get("code"),
                "title": item.get("name"),
                "status": item.get("status"),
                "riskLevel": item.get("riskLevel"),
                "summary": item.get("summary"),
                "sourceTable": item.get("sourceTable"),
                "sourceId": item.get("sourceId"),
                "targetKpiCode": target.get("kpiCode"),
                "targetModule": target.get("module"),
                "targetModuleGroup": target.get("moduleGroup"),
                "actionLabel": target.get("actionLabel", "查看来源"),
                "actionEnabled": False,
                "actionTip": "关联业务跳转为原型预留，尚未接入页面联动。",
                "updatedAt": item.get("updatedAt"),
            }
        )

    return {
        "code": 0,
        "data": {
            "featureId": feature_id,
            "featureName": feature["name"],
            "objectType": feature["object_type"],
            "statusLabel": feature.get("status_label"),
            "title": feature.get("dashboard_title") or "关联业务",
            "summary": gis_relation_summary(relation_rows),
            "items": items,
            "permissions": {
                "canView": True,
                "canSupervise": False,
                "canHandle": False,
                "notice": "领导层仅查看关联业务线索，不在地图侧办理事项。",
            },
        },
        "meta": {
            "projectId": project_id,
            "total": len(items),
        },
    }


# V0.4 governance APIs. These functions intentionally do not participate in
# homepage KPI assembly and do not expose a DELETE operation for approval facts.
def _v04_int(value: Any, field_name: str, *, allow_none: bool = False) -> int | None:
    if value is None and allow_none:
        return None
    if isinstance(value, bool):
        raise ValueError(f"{field_name} 必须为整数")
    try:
        return int(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{field_name} 必须为整数") from exc


def _v04_date(value: Any, field_name: str, *, allow_none: bool = True) -> str | None:
    if value is None or value == "":
        if allow_none:
            return None
        raise ValueError(f"{field_name} 不能为空")
    if isinstance(value, datetime):
        return value.date().isoformat()
    if isinstance(value, date):
        return value.isoformat()
    text = str(value).strip()
    try:
        return date.fromisoformat(text).isoformat()
    except ValueError as exc:
        raise ValueError(f"{field_name} 必须为 YYYY-MM-DD") from exc


def _v04_bool(value: Any, field_name: str, default: bool | None = None) -> bool | None:
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    if value in (0, 1):
        return bool(value)
    if isinstance(value, str) and value.strip().lower() in {"0", "1", "true", "false"}:
        return value.strip().lower() in {"1", "true"}
    raise ValueError(f"{field_name} 必须为布尔值")


def _v04_text(value: Any, field_name: str, max_length: int, *, required: bool = True) -> str | None:
    if value is None:
        if required:
            raise ValueError(f"{field_name} 不能为空")
        return None
    text = str(value).strip()
    if not text and required:
        raise ValueError(f"{field_name} 不能为空")
    if len(text) > max_length:
        raise ValueError(f"{field_name} 长度不能超过 {max_length}")
    return text or None


def _rectification_task_item(row: dict) -> dict:
    return {
        "id": row["id"],
        "taskCode": row["task_code"],
        "title": row["title"],
        "responsibleOrgId": row.get("responsible_org_id"),
        "deadline": value_for_json(row.get("deadline")),
        "taskStatus": row.get("task_status"),
        "dataNature": row.get("data_nature"),
        "isDemo": bool(row.get("is_demo")),
        "effectiveStatus": row.get("effective_status"),
        "effectiveAt": value_for_json(row.get("effective_at")),
        "effectiveBy": row.get("effective_by"),
        "rectificationCompletedDate": value_for_json(row.get("rectification_completed_date")),
        "rectificationCompletedBy": row.get("rectification_completed_by"),
        "createdAt": value_for_json(row.get("created_at")),
        "updatedAt": value_for_json(row.get("updated_at")),
    }


def get_rectification_tasks(filters: dict | None = None) -> dict:
    filters = filters or {}
    sql = """
        SELECT id, task_code, title, responsible_org_id, deadline, task_status,
               data_nature, is_demo, effective_status, effective_at, effective_by,
               rectification_completed_date, rectification_completed_by,
               created_at, updated_at
        FROM e_rectification_task
        WHERE 1 = 1
    """
    params: list[Any] = []
    task_status = filters.get("taskStatus")
    data_nature = filters.get("dataNature")
    is_demo = filters.get("isDemo")
    completed = filters.get("completed")
    if task_status:
        sql += " AND task_status = %s"
        params.append(str(task_status))
    if data_nature:
        sql += " AND data_nature = %s"
        params.append(str(data_nature))
    if is_demo not in (None, ""):
        sql += " AND is_demo = %s"
        params.append(1 if _v04_bool(is_demo, "isDemo") else 0)
    if completed not in (None, ""):
        sql += " AND (rectification_completed_date IS NOT NULL) = %s"
        params.append(1 if _v04_bool(completed, "completed") else 0)
    sql += " ORDER BY deadline ASC, id ASC"
    rows = query_all(sql, tuple(params))
    return {"total": len(rows), "items": [_rectification_task_item(row) for row in rows]}


def get_rectification_task(task_id: int) -> dict | None:
    task_id = _v04_int(task_id, "整改任务 ID")
    row = query_one(
        """
        SELECT id, task_code, title, responsible_org_id, deadline, task_status,
               data_nature, is_demo, effective_status, effective_at, effective_by,
               rectification_completed_date, rectification_completed_by,
               created_at, updated_at
        FROM e_rectification_task
        WHERE id = %s
        """,
        (task_id,),
    )
    return _rectification_task_item(row) if row else None


def update_rectification_task(task_id: int, payload: dict) -> dict | None:
    task_id = _v04_int(task_id, "整改任务 ID")
    payload = payload or {}
    allowed = {"rectificationCompletedDate", "rectificationCompletedBy"}
    unknown = set(payload) - allowed
    if unknown:
        raise ValueError("整改任务接口只允许修改整改完成日期和填报人")
    if not payload:
        raise ValueError("至少提供一个可修改字段")
    if get_rectification_task(task_id) is None:
        return None

    updates: list[str] = []
    params: list[Any] = []
    if "rectificationCompletedDate" in payload:
        updates.append("rectification_completed_date = %s")
        params.append(_v04_date(payload.get("rectificationCompletedDate"), "rectificationCompletedDate"))
    if "rectificationCompletedBy" in payload:
        completed_by = _v04_int(
            payload.get("rectificationCompletedBy"),
            "rectificationCompletedBy",
            allow_none=True,
        )
        if completed_by is not None and query_one("SELECT id FROM user_account WHERE id = %s", (completed_by,)) is None:
            raise ValueError("rectificationCompletedBy 对应的用户不存在")
        updates.append("rectification_completed_by = %s")
        params.append(completed_by)

    params.append(task_id)
    execute(f"UPDATE e_rectification_task SET {', '.join(updates)} WHERE id = %s", tuple(params))
    return get_rectification_task(task_id)


def _special_plan_file(row: dict) -> dict | None:
    if row.get("linked_file_id") is None:
        return None
    return {
        "id": row["linked_file_id"],
        "fileCode": row.get("linked_file_code"),
        "originalName": row.get("linked_original_name"),
        "fileExt": row.get("linked_file_ext"),
        "mimeType": row.get("linked_mime_type"),
        "fileSize": row.get("linked_file_size"),
        "uploadTime": value_for_json(row.get("linked_upload_time")),
        "parseStatus": row.get("linked_parse_status"),
    }


def _special_plan_item(row: dict) -> dict:
    return {
        "id": row["id"],
        "projectId": row["project_id"],
        "riskPointId": row["risk_point_id"],
        "planCode": row["plan_code"],
        "planName": row["plan_name"],
        "riskLevel": row["risk_level"],
        "approvalStatus": row["approval_status"],
        "approvalDate": value_for_json(row.get("approval_date")),
        "approvalFileId": row.get("approval_file_id"),
        "approvalFile": _special_plan_file(row),
        "sourceDocRef": row.get("source_doc_ref"),
        "dataNature": row.get("data_nature"),
        "isDemo": bool(row.get("is_demo")),
        "createdAt": value_for_json(row.get("created_at")),
        "updatedAt": value_for_json(row.get("updated_at")),
    }


_SPECIAL_PLAN_SELECT = """
    SELECT spa.*,
           f.id AS linked_file_id,
           f.file_code AS linked_file_code,
           f.original_name AS linked_original_name,
           f.file_ext AS linked_file_ext,
           f.mime_type AS linked_mime_type,
           f.file_size AS linked_file_size,
           f.upload_time AS linked_upload_time,
           f.parse_status AS linked_parse_status
    FROM special_plan_approval spa
    LEFT JOIN file_asset f
      ON f.id = spa.approval_file_id
     AND f.is_deleted = 0
"""


def get_special_plans(filters: dict | None = None) -> dict:
    filters = filters or {}
    sql = _SPECIAL_PLAN_SELECT + " WHERE 1 = 1"
    params: list[Any] = []
    mappings = (
        ("projectId", "spa.project_id"),
        ("riskPointId", "spa.risk_point_id"),
        ("approvalStatus", "spa.approval_status"),
        ("riskLevel", "spa.risk_level"),
        ("dataNature", "spa.data_nature"),
    )
    for key, column in mappings:
        value = filters.get(key)
        if value in (None, ""):
            continue
        if key in {"projectId", "riskPointId"}:
            value = _v04_int(value, key)
        sql += f" AND {column} = %s"
        params.append(value)
    if filters.get("isDemo") not in (None, ""):
        sql += " AND spa.is_demo = %s"
        params.append(1 if _v04_bool(filters.get("isDemo"), "isDemo") else 0)
    sql += " ORDER BY spa.project_id ASC, spa.approval_date DESC, spa.id DESC"
    rows = query_all(sql, tuple(params))
    return {"total": len(rows), "items": [_special_plan_item(row) for row in rows]}


def get_special_plan(plan_id: int) -> dict | None:
    plan_id = _v04_int(plan_id, "专项方案 ID")
    row = query_one(_SPECIAL_PLAN_SELECT + " WHERE spa.id = %s", (plan_id,))
    return _special_plan_item(row) if row else None


def _validate_special_plan_references(risk_point_id: int, approval_file_id: int | None) -> None:
    if query_one("SELECT id FROM safety_risk_point WHERE id = %s", (risk_point_id,)) is None:
        raise ValueError("riskPointId 对应的风险源不存在")
    if approval_file_id is not None and query_one(
        "SELECT id FROM file_asset WHERE id = %s AND is_deleted = 0", (approval_file_id,)
    ) is None:
        raise ValueError("approvalFileId 对应的有效文件不存在")


def create_special_plan(payload: dict) -> dict:
    payload = payload or {}
    required = ("projectId", "riskPointId", "planCode", "planName", "riskLevel", "approvalStatus")
    missing = [key for key in required if payload.get(key) in (None, "")]
    if missing:
        raise ValueError(f"缺少必填字段：{', '.join(missing)}")
    project_id = _v04_int(payload.get("projectId"), "projectId")
    risk_point_id = _v04_int(payload.get("riskPointId"), "riskPointId")
    plan_code = _v04_text(payload.get("planCode"), "planCode", 80)
    plan_name = _v04_text(payload.get("planName"), "planName", 255)
    risk_level = _v04_text(payload.get("riskLevel"), "riskLevel", 50)
    approval_status = _v04_text(payload.get("approvalStatus"), "approvalStatus", 40)
    approval_date = _v04_date(payload.get("approvalDate"), "approvalDate")
    approval_file_id = _v04_int(payload.get("approvalFileId"), "approvalFileId", allow_none=True)
    source_doc_ref = _v04_text(payload.get("sourceDocRef"), "sourceDocRef", 255, required=False)
    data_nature = _v04_text(payload.get("dataNature", "demo"), "dataNature", 20)
    is_demo = _v04_bool(payload.get("isDemo"), "isDemo", True)
    _validate_special_plan_references(risk_point_id, approval_file_id)
    if query_one(
        "SELECT id FROM special_plan_approval WHERE project_id = %s AND plan_code = %s",
        (project_id, plan_code),
    ) is not None:
        raise ValueError("同一项目下 planCode 已存在")

    plan_id = next_id("special_plan_approval", 950100)
    execute(
        """
        INSERT INTO special_plan_approval
        (id, project_id, risk_point_id, plan_code, plan_name, risk_level,
         approval_status, approval_date, approval_file_id, source_doc_ref,
         data_nature, is_demo)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """,
        (
            plan_id, project_id, risk_point_id, plan_code, plan_name, risk_level,
            approval_status, approval_date, approval_file_id, source_doc_ref,
            data_nature, 1 if is_demo else 0,
        ),
    )
    return get_special_plan(plan_id) or {}


def update_special_plan(plan_id: int, payload: dict) -> dict | None:
    plan_id = _v04_int(plan_id, "专项方案 ID")
    payload = payload or {}
    immutable = {"id", "projectId", "riskPointId", "planCode", "dataNature", "isDemo"}
    if immutable.intersection(payload):
        raise ValueError("专项方案的项目、风险源、编码和数据性质不可修改")
    allowed = {"planName", "riskLevel", "approvalStatus", "approvalDate", "approvalFileId", "sourceDocRef"}
    unknown = set(payload) - allowed
    if unknown:
        raise ValueError("专项方案包含不允许修改的字段")
    if not payload:
        raise ValueError("至少提供一个可修改字段")
    if get_special_plan(plan_id) is None:
        return None

    column_map = {
        "planName": ("plan_name", lambda value: _v04_text(value, "planName", 255)),
        "riskLevel": ("risk_level", lambda value: _v04_text(value, "riskLevel", 50)),
        "approvalStatus": ("approval_status", lambda value: _v04_text(value, "approvalStatus", 40)),
        "approvalDate": ("approval_date", lambda value: _v04_date(value, "approvalDate")),
        "approvalFileId": ("approval_file_id", lambda value: _v04_int(value, "approvalFileId", allow_none=True)),
        "sourceDocRef": ("source_doc_ref", lambda value: _v04_text(value, "sourceDocRef", 255, required=False)),
    }
    updates: list[str] = []
    params: list[Any] = []
    for key, value in payload.items():
        column, converter = column_map[key]
        converted = converter(value)
        if key == "approvalFileId":
            _validate_special_plan_references(
                _v04_int(get_special_plan(plan_id)["riskPointId"], "riskPointId"),
                converted,
            )
        updates.append(f"{column} = %s")
        params.append(converted)
    params.append(plan_id)
    execute(f"UPDATE special_plan_approval SET {', '.join(updates)} WHERE id = %s", tuple(params))
    return get_special_plan(plan_id)
