from __future__ import annotations

import json
import hashlib
import sqlite3
import uuid
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, unquote, urlparse

import mysql_api
import monthly_report_readiness
import monthly_report_overview
import assistant_qa
import ai_document_analysis
import esg_demo_api
from mysql_db import mysql_enabled, mysql_ping

BASE_DIR = Path(__file__).resolve().parent
ROOT_DIR = BASE_DIR.parent
DB_PATH = BASE_DIR / "data" / "luoyi_esg_dev.db"
DASHBOARD_PAYLOAD_PATH = BASE_DIR / "dashboard_payload.json"
MONTHLY_OVERVIEW_SNAPSHOT_PATH = BASE_DIR / "data" / "monthly_report_overview.snapshot.json"
CARBON_OVERVIEW_SNAPSHOT_PATH = BASE_DIR / "data" / "carbon_benefit_overview.snapshot.json"
GIS_MANIFEST_PATH = ROOT_DIR / "public" / "data" / "shp" / "manifest.json"
UPLOAD_DIR = BASE_DIR / "storage" / "uploads" / "202607"
HOST = "127.0.0.1"
PORT = 8765


GROUP_META = {
    "E": {"key": "E", "title": "环境环保组", "theme": "green", "status": "总体可控"},
    "S": {"key": "S", "title": "社会责任组", "theme": "blue", "status": "总体可控"},
    "G": {"key": "G", "title": "治理合规组", "theme": "purple", "status": "总体可控"},
}


def connect() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def row_to_dict(row: sqlite3.Row) -> dict:
    return {key: row[key] for key in row.keys()}


def try_mysql(func, *args):
    if not mysql_enabled():
        return None
    try:
        return func(*args)
    except Exception as exc:
        print(f"[api] MySQL fallback to SQLite: {exc}")
        return None


def load_dashboard_payload() -> dict:
    if not DASHBOARD_PAYLOAD_PATH.exists():
        return {}
    return json.loads(DASHBOARD_PAYLOAD_PATH.read_text(encoding="utf-8"))


def load_monthly_overview_snapshot(report_period: str | None = None) -> dict | None:
    """Load the server-side contract snapshot without reviving the legacy popup values."""
    if not MONTHLY_OVERVIEW_SNAPSHOT_PATH.exists():
        return None
    overview = json.loads(MONTHLY_OVERVIEW_SNAPSHOT_PATH.read_text(encoding="utf-8"))
    if report_period and overview.get("reportMonth") != report_period:
        return None
    overview["sourceMode"] = "server-json"
    overview["isMock"] = False
    return overview


def load_carbon_overview_snapshot() -> dict | None:
    if not CARBON_OVERVIEW_SNAPSHOT_PATH.exists():
        return None
    overview = json.loads(CARBON_OVERVIEW_SNAPSHOT_PATH.read_text(encoding="utf-8"))
    overview["sourceMode"] = "server-json"
    overview["isMock"] = False
    return overview


def monthly_overview_to_topic(overview: dict, base: dict | None = None) -> dict:
    summary_data = overview["summary"]
    topic = dict(base or {})
    topic.update(
        {
            "key": "MONTHLY",
            "fullName": "月报准备与输出",
            "theme": "blue",
            "isTopic": True,
            "summary": [
                {"label": "资料归集率", "value": overview["readinessRate"], "unit": "%"},
                {"label": "已归集", "value": f"{summary_data['collectedCount']}/{summary_data['totalCount']}", "unit": "项"},
                {"label": "待处理", "value": summary_data["pendingTotal"], "unit": "项"},
                {"label": "输出状态", "value": overview["outputStatus"]["label"], "unit": ""},
            ],
            "topicData": {
                "overview": overview,
                "progress": {
                    "groups": [
                        {"key": item["groupCode"], "label": f"{item['groupCode']}组", "value": item["progress"],
                         "collectedCount": item["collectedCount"], "totalCount": item["totalCount"]}
                        for item in overview["groupProgress"]
                    ]
                },
                "chapters": {"list": overview["taskInstances"]},
                "statusChain": overview["processStages"],
            },
            "detailData": overview["pendingTasks"],
            "dataSource": "服务端JSON月报契约快照",
            "updateTime": overview.get("updatedAt"),
            "completeness": f"{overview['readinessRate']}%",
            "sourceMode": overview["sourceMode"],
            "dataNature": overview["dataNature"],
            "isMock": overview["isMock"],
        }
    )
    return topic


def load_gis_manifest() -> dict:
    if not GIS_MANIFEST_PATH.exists():
        return {"layers": []}
    return json.loads(GIS_MANIFEST_PATH.read_text(encoding="utf-8"))


def gis_static_layers(
    project_id: str = "LUOYI-ESG",
    section_id: str | None = None,
    current_time: str | None = None,
    visible_layer_ids: list[str] | None = None,
) -> dict:
    manifest = load_gis_manifest()
    layers = manifest.get("layers") or []
    visible_set = set(visible_layer_ids or [])
    data = []
    for layer in layers:
        if not layer.get("enabled", True):
            continue
        if visible_set and layer.get("id") not in visible_set:
            continue
        if section_id and layer.get("objectType") == "road-section":
            if section_id not in {layer.get("id"), layer.get("name")}:
                continue
        data.append(
            {
                "id": layer.get("id"),
                "name": layer.get("name"),
                "geometryType": layer.get("geometryType"),
                "enabled": bool(layer.get("enabled", True)),
                "objectType": layer.get("objectType"),
                "featureCount": int(layer.get("featureCount") or 0),
                "fields": layer.get("fields") or [],
                "source": {
                    **(layer.get("source") or {}),
                    "type": "api",
                },
                "style": layer.get("style") or {},
            }
        )
    return {
        "code": 0,
        "data": data,
        "meta": {
            "projectId": project_id,
            "sectionId": section_id,
            "currentTime": current_time,
            "total": len(data),
            "dataSource": "fallback",
            "dataNature": "demo",
            "fallback": "static-geojson",
        },
    }


def geojson_path_from_source_url(url: str | None) -> Path | None:
    if not url:
        return None
    normalized = unquote(url)
    if normalized.startswith("/"):
        normalized = normalized.lstrip("/")
    if normalized.startswith("data/"):
        normalized = f"public/{normalized}"
    return ROOT_DIR / normalized.replace("/", "\\")


def gis_empty_relation_summary() -> dict:
    return {"total": 0, "pendingCount": 0, "highRiskCount": 0, "byType": []}


GIS_STATIC_FEATURE_META = {
    "section-1": {"sectionId": "1标段", "status": "normal", "statusLabel": "正常", "riskLevel": 1},
    "section-2": {"sectionId": "2标段", "status": "normal", "statusLabel": "正常", "riskLevel": 1},
    "section-3": {"sectionId": "3标段", "status": "normal", "statusLabel": "正常", "riskLevel": 1},
    "waste-1": {"sectionId": "1标段", "status": "normal", "statusLabel": "正常", "riskLevel": 1},
    "waste-2": {"sectionId": "2标段", "status": "attention", "statusLabel": "关注", "riskLevel": 2},
    "water-1": {"sectionId": "2标段", "status": "normal", "statusLabel": "正常", "riskLevel": 1},
    "water-2": {"sectionId": "3标段", "status": "normal", "statusLabel": "正常", "riskLevel": 1},
    "eco-1": {"sectionId": "1标段", "status": "normal", "statusLabel": "正常", "riskLevel": 1},
    "slope-1": {"sectionId": "1标段", "status": "normal", "statusLabel": "正常", "riskLevel": 1},
    "slope-2": {"sectionId": "2标段", "status": "attention", "statusLabel": "关注", "riskLevel": 2},
}


def gis_static_features(
    project_id: str = "LUOYI-ESG",
    layer_id: str | None = None,
    section_id: str | None = None,
    current_time: str | None = None,
) -> dict:
    manifest = load_gis_manifest()
    layers = manifest.get("layers") or []
    features = []
    for layer in layers:
        if not layer.get("enabled", True):
            continue
        if layer_id and layer.get("id") != layer_id:
            continue
        layer_meta = GIS_STATIC_FEATURE_META.get(layer.get("id"), {})
        layer_section_id = layer_meta.get("sectionId")
        if section_id and section_id != layer_section_id:
            continue
        source = layer.get("source") or {}
        geojson_path = geojson_path_from_source_url(source.get("url"))
        if not geojson_path or not geojson_path.exists():
            continue
        collection = json.loads(geojson_path.read_text(encoding="utf-8"))
        for index, item in enumerate(collection.get("features") or [], 1):
            properties = item.get("properties") or {}
            name = properties.get("NAME") or properties.get("name") or layer.get("name") or layer.get("id")
            feature_id = f"{layer.get('id')}-{index}"
            feature_properties = {
                **properties,
                **layer_meta,
                "sourceMode": "static-geojson",
                "projectId": project_id,
            }
            status = layer_meta.get("status") or "normal"
            status_label = layer_meta.get("statusLabel") or "正常"
            risk_level = int(layer_meta.get("riskLevel") or 1)
            features.append(
                {
                    "id": feature_id,
                    "layerId": layer.get("id"),
                    "objectType": layer.get("objectType"),
                    "name": name,
                    "geometry": item.get("geometry") or {},
                    "properties": feature_properties,
                    "status": status,
                    "statusLabel": status_label,
                    "riskLevel": risk_level,
                    "businessSummary": {
                        "statusCode": status,
                        "statusLabel": status_label,
                        "title": name,
                        "dashboardRows": [
                            {"label": "图层", "value": layer.get("name")},
                            {"label": "来源", "value": "本地 GeoJSON"},
                        ],
                        "dashboardNote": "MySQL 不可用时展示本地 GIS 基础图层；业务关联事项待数据库恢复后显示。",
                        "previewRows": [
                            {"label": key, "value": value}
                            for key, value in properties.items()
                        ],
                        "targetModule": "GIS",
                        "targetRoute": None,
                    },
                    "relationSummary": gis_empty_relation_summary(),
                    "updatedAt": current_time,
                }
            )
    return {
        "code": 0,
        "data": features,
        "meta": {
            "projectId": project_id,
            "sectionId": section_id,
            "currentTime": current_time,
            "layerId": layer_id,
            "total": len(features),
            "dataSource": "fallback",
            "dataNature": "demo",
            "fallback": "static-geojson",
        },
    }


def json_response(handler: BaseHTTPRequestHandler, payload: object, status: int = HTTPStatus.OK) -> None:
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    handler.send_response(status)
    handler.send_header("Content-Type", "application/json; charset=utf-8")
    handler.send_header("Access-Control-Allow-Origin", "*")
    handler.send_header("Access-Control-Allow-Methods", "GET, POST, PATCH, OPTIONS")
    handler.send_header("Access-Control-Allow-Headers", "Content-Type")
    handler.send_header("Content-Length", str(len(body)))
    handler.end_headers()
    handler.wfile.write(body)


def not_found(handler: BaseHTTPRequestHandler) -> None:
    json_response(handler, {"ok": False, "message": "接口不存在"}, HTTPStatus.NOT_FOUND)


def read_json_body(handler: BaseHTTPRequestHandler) -> dict:
    length = int(handler.headers.get("Content-Length") or 0)
    if length <= 0:
        return {}
    body = handler.rfile.read(length).decode("utf-8")
    return json.loads(body) if body else {}


def parse_disposition_params(value: str) -> dict[str, str]:
    params: dict[str, str] = {}
    for part in value.split(";"):
        if "=" not in part:
            continue
        key, raw = part.split("=", 1)
        clean_key = key.strip().lower()
        clean_value = raw.strip().strip('"')
        if clean_key.endswith("*") and "''" in clean_value:
            clean_value = unquote(clean_value.split("''", 1)[1])
            clean_key = clean_key[:-1]
        params[clean_key] = clean_value
    return params


def sanitize_filename(filename: str) -> str:
    safe = "".join(ch for ch in filename if ch not in '<>:"/\\|?*\r\n\t').strip()
    return safe or "未命名资料"


def parse_multipart_upload(handler: BaseHTTPRequestHandler) -> dict:
    content_type = handler.headers.get("Content-Type") or ""
    length = int(handler.headers.get("Content-Length") or 0)
    if length <= 0:
        raise ValueError("未接收到上传文件")
    if length > 220 * 1024 * 1024:
        raise ValueError("单个文件不能超过 200MB")

    boundary_token = ""
    for part in content_type.split(";"):
        part = part.strip()
        if part.startswith("boundary="):
            boundary_token = part.split("=", 1)[1].strip().strip('"')
            break
    if not boundary_token:
        raise ValueError("multipart 请求缺少 boundary")

    body = handler.rfile.read(length)
    boundary = ("--" + boundary_token).encode("utf-8")
    fields: dict[str, str] = {}
    uploaded_file: dict | None = None

    for raw_part in body.split(boundary):
        part = raw_part
        if part.startswith(b"\r\n"):
            part = part[2:]
        if not part or part in (b"--", b"--\r\n"):
            continue
        if part.endswith(b"--\r\n"):
            part = part[:-4]
        elif part.endswith(b"--"):
            part = part[:-2].rstrip(b"\r\n")
        header_blob, sep, content = part.partition(b"\r\n\r\n")
        if not sep:
            continue
        try:
            header_text = header_blob.decode("utf-8")
        except UnicodeDecodeError:
            header_text = header_blob.decode("latin-1", errors="ignore")
        headers = header_text.split("\r\n")
        disposition = next((line for line in headers if line.lower().startswith("content-disposition:")), "")
        disposition_params = parse_disposition_params(disposition.split(":", 1)[1] if ":" in disposition else "")
        name = disposition_params.get("name", "")
        filename = disposition_params.get("filename")
        if filename:
            content_type_line = next((line for line in headers if line.lower().startswith("content-type:")), "")
            mime_type = content_type_line.split(":", 1)[1].strip() if ":" in content_type_line else "application/octet-stream"
            original_name = sanitize_filename(filename)
            file_bytes = content[:-2] if content.endswith(b"\r\n") else content
            sha256_hash = hashlib.sha256(file_bytes).hexdigest()
            UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
            stored_name = f"{uuid.uuid4().hex}_{original_name}"
            stored_path = UPLOAD_DIR / stored_name
            stored_path.write_bytes(file_bytes)
            uploaded_file = {
                "originalName": original_name,
                "fileName": original_name,
                "fileSize": len(file_bytes),
                "mimeType": mime_type,
                "storagePath": str(stored_path.relative_to(BASE_DIR)).replace("\\", "/"),
                "sha256Hash": sha256_hash,
            }
        elif name:
            field_bytes = content[:-2] if content.endswith(b"\r\n") else content
            fields[name] = field_bytes.decode("utf-8", errors="ignore").strip()

    if uploaded_file is None:
        raise ValueError("multipart 请求中未找到文件字段")

    uploaded_file.update(fields)
    return uploaded_file


def read_upload_payload(handler: BaseHTTPRequestHandler) -> dict:
    content_type = handler.headers.get("Content-Type") or ""
    if content_type.lower().startswith("multipart/form-data"):
        return parse_multipart_upload(handler)
    return read_json_body(handler)


def bad_request(handler: BaseHTTPRequestHandler, message: str) -> None:
    json_response(handler, {"ok": False, "message": message}, HTTPStatus.BAD_REQUEST)


def service_unavailable(handler: BaseHTTPRequestHandler, message: str = "MySQL 数据暂不可用") -> None:
    json_response(handler, {"ok": False, "message": message}, HTTPStatus.SERVICE_UNAVAILABLE)


def method_not_allowed(handler: BaseHTTPRequestHandler, message: str) -> None:
    json_response(handler, {"ok": False, "message": message}, HTTPStatus.METHOD_NOT_ALLOWED)


def get_dashboard_kpis() -> dict:
    mysql_payload = try_mysql(mysql_api.get_dashboard_kpis)
    if mysql_payload is not None:
        return mysql_payload

    with connect() as conn:
        rows = conn.execute(
            """
            SELECT indicator_code, group_code, label, full_name, value, unit, display_order
            FROM indicator_result
            ORDER BY group_code, display_order
            """
        ).fetchall()

    groups: dict[str, dict] = {key: {**meta, "items": []} for key, meta in GROUP_META.items()}
    for row in rows:
        is_e04 = row["indicator_code"] == "E04"
        item = {
            "key": row["indicator_code"],
            "label": "文物保护管控" if is_e04 else row["label"],
            "fullName": "文物保护管控" if is_e04 else row["full_name"],
            "value": int(row["value"]) if float(row["value"]).is_integer() else row["value"],
            "unit": "处" if is_e04 else row["unit"],
        }
        groups[row["group_code"]]["items"].append(item)

    return {"groups": [groups["E"], groups["S"], groups["G"]]}


def get_dashboard_risk_warnings(
    project_id: int = 1001,
    status: str | None = None,
    page: int = 1,
    page_size: int = 20,
) -> dict | None:
    return try_mysql(esg_demo_api.get_demo_risk_warnings, project_id, status, page, page_size)


def get_dashboard_kpi_object(kpi_code: str, object_id: int, project_id: int = 1001) -> dict | None:
    return try_mysql(esg_demo_api.get_demo_kpi_object, kpi_code, object_id, project_id)


def get_dashboard_kpi_detail(kpi_code: str) -> dict | None:
    mysql_payload = try_mysql(mysql_api.get_dashboard_kpi_detail, kpi_code)
    if mysql_payload:
        return mysql_payload

    # E01 has a complete MySQL chain; never substitute the legacy JSON snapshot.
    if kpi_code == "E01":
        return None

    payload = load_dashboard_payload()
    detail = (payload.get("kpiDetails") or {}).get(kpi_code)
    if not detail:
        return None
    detail["isMock"] = False
    return detail


def get_dashboard_topic(topic_key: str) -> dict | None:
    mysql_payload = try_mysql(mysql_api.get_dashboard_topic, topic_key)
    if mysql_payload:
        return mysql_payload

    payload = load_dashboard_payload()
    if topic_key == "carbon":
        return load_carbon_overview_snapshot()
    if topic_key in {"monthly", "monthly-report"}:
        overview = load_monthly_overview_snapshot()
        if not overview:
            return None
        return monthly_overview_to_topic(overview, payload.get("monthlyTopicDetail"))
    return None


def get_dashboard_panels() -> dict:
    mysql_payload = try_mysql(mysql_api.get_dashboard_panels)
    if mysql_payload:
        return mysql_payload

    payload = load_dashboard_payload()
    carbon_overview = load_carbon_overview_snapshot()
    carbon_panel = {
        "metrics": payload.get("carbonMetrics") or [],
        "sources": payload.get("carbonSources") or [],
        "reductions": payload.get("reductionMeasures") or [],
    }
    if carbon_overview:
        summary = carbon_overview["summary"]
        carbon_panel = {
            "metrics": summary[:3] + [{
                "label": carbon_overview["carbonCostLabel"],
                "value": carbon_overview["carbonCostValue"],
                "unit": carbon_overview["carbonCostUnit"],
                "sub": "项目初步测算，尚未正式财务确认",
            }],
            "sources": [
                {"name": item["sourceName"], "value": item["totalEmission"]}
                for item in carbon_overview["emissionSources"]
            ],
            "reductions": payload.get("reductionMeasures") or [],
            "carbonCostLabel": carbon_overview["carbonCostLabel"],
            "carbonCostValue": carbon_overview["carbonCostValue"],
            "carbonCostUnit": carbon_overview["carbonCostUnit"],
            "sourceMode": carbon_overview["sourceMode"],
            "isMock": carbon_overview["isMock"],
            "dataNature": carbon_overview["dataNature"],
        }
    monthly_overview = load_monthly_overview_snapshot()
    monthly_panel = payload.get("monthlyReport") or {}
    if monthly_overview:
        summary = monthly_overview["summary"]
        monthly_panel = {
            "month": monthly_overview["reportMonth"],
            "progress": monthly_overview["readinessRate"],
            "pendingCount": summary["pendingTotal"],
            "confirmCount": summary["pendingConfirmCount"],
            "currentStatus": "资料归集",
            "expectedCompletion": None,
            "materials": [
                {"name": item["taskName"], "owner": item["responsibleRole"], "deadline": item["deadline"]}
                for item in monthly_overview["pendingTasks"]
            ],
            "sourceMode": monthly_overview["sourceMode"],
            "isMock": monthly_overview["isMock"],
            "dataNature": monthly_overview["dataNature"],
        }
    return {
        "compliance": {
            "metrics": payload.get("complianceMetrics") or [],
            "effectiveness": payload.get("effectivenessItems") or [],
            "safeguards": payload.get("safeguardItems") or [],
        },
        "carbon": carbon_panel,
        "monthly": monthly_panel,
        "timeline": payload.get("timelineSteps") or [],
        "gis": {
            "routePoints": payload.get("routePoints") or [],
            "routeSegments": payload.get("routeSegments") or [],
            "sensitiveAreas": payload.get("sensitiveAreas") or [],
        },
    }


def get_snapshot(snapshot_type: str) -> dict | None:
    with connect() as conn:
        row = conn.execute(
            """
            SELECT snapshot_type, snapshot_date, payload_json, published_at
            FROM indicator_snapshot
            WHERE snapshot_type = ?
            ORDER BY snapshot_date DESC, published_at DESC
            LIMIT 1
            """,
            (snapshot_type,),
        ).fetchone()
    if row is None:
        return None
    return {
        "snapshotType": row["snapshot_type"],
        "snapshotDate": row["snapshot_date"],
        "publishedAt": row["published_at"],
        "payload": json.loads(row["payload_json"]),
    }


def get_s01_detail() -> dict:
    mysql_payload = try_mysql(mysql_api.get_s01_detail)
    if mysql_payload is not None:
        return mysql_payload

    # P2.7: 收紧 SQLite/MODAL_S01 回退
    # 正式缺数时禁止用旧 368 Mock 充数；无 MySQL 时须明确空/错误
    snapshot = get_snapshot("MODAL_S01")
    if snapshot is not None:
        # 仅在演示模式回退时使用快照（避免正式环境冒充 77/368）
        import os
        if os.environ.get("S01_ALLOW_DEMO", "1").strip() in {"1", "true", "True", "TRUE", "yes"}:
            return snapshot["payload"]

    # 正式环境无 MySQL 时返回明确空值，不冒充数据
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
    }


def get_workspace_summary() -> dict:
    mysql_payload = try_mysql(mysql_api.get_workspace_summary)
    if mysql_payload is not None:
        return mysql_payload

    with connect() as conn:
        row = conn.execute("SELECT * FROM workspace_summary WHERE id = 1").fetchone()
    return {
        "currentTodo": row["current_todo"],
        "pendingUpload": row["pending_upload"],
        "pendingCorrection": row["pending_correction"],
        "pendingSubmit": row["pending_submit"],
        "underReview": row["under_review"],
        "dueSoon": row["due_soon"],
        "completed": row["completed"],
    }


def get_tasks(query: dict[str, list[str]]) -> dict:
    module = (query.get("module") or [""])[0]
    status = (query.get("status") or [""])[0]
    keyword = (query.get("keyword") or [""])[0]
    cycle = (query.get("cycle") or [""])[0]
    cycle_type = (query.get("cycleType") or query.get("cycle_type") or [""])[0]
    deadline_start = (query.get("deadlineStart") or query.get("deadline_start") or [""])[0]
    deadline_end = (query.get("deadlineEnd") or query.get("deadline_end") or [""])[0]
    assignee = (query.get("assignee") or [""])[0]

    mysql_payload = try_mysql(mysql_api.get_tasks, module, status, keyword, cycle, cycle_type, deadline_start, deadline_end, assignee)
    if mysql_payload is not None:
        return mysql_payload

    sql = "SELECT * FROM upload_task WHERE 1=1"
    params: list[str] = []
    if module:
        sql += " AND module_code = ?"
        params.append(module)
    if status:
        sql += " AND status = ?"
        params.append(status)
    if keyword:
        sql += " AND name LIKE ?"
        params.append(f"%{keyword}%")
    sql += " ORDER BY deadline ASC"

    with connect() as conn:
        rows = conn.execute(sql, params).fetchall()

    items = []
    for row in rows:
        items.append(
            {
                "id": row["id"],
                "name": row["name"],
                "module": row["module_code"],
                "moduleName": row["module_name"],
                "cycle": row["cycle"],
                "cycleType": row["cycle_type"],
                "deadline": row["deadline"],
                "deadlineDisplay": row["deadline"],
                "progressCurrent": row["progress_current"],
                "progressTotal": row["progress_total"],
                "status": row["status"],
                "nextStep": row["next_step"],
                "assignee": row["assignee"],
                "assigneeDept": row["assignee_dept"],
                "priorityCode": row["priority_code"],
            }
        )
    return {"total": len(items), "items": items}


def get_task_detail(task_id: str) -> dict | None:
    mysql_payload = try_mysql(mysql_api.get_task_detail, task_id)
    if mysql_payload is not None:
        return mysql_payload

    with connect() as conn:
        task = conn.execute("SELECT * FROM upload_task WHERE id = ?", (task_id,)).fetchone()
        if task is None:
            return None
        requirement_rows = conn.execute(
            """
            SELECT * FROM task_document_requirement
            WHERE task_id IN (?, '*')
            ORDER BY CASE WHEN task_id = ? THEN 0 ELSE 1 END, sequence_no
            """,
            (task_id, task_id),
        ).fetchall()
        candidate_rows = conn.execute(
            """
            SELECT * FROM task_candidate_document
            WHERE task_id IN (?, '*')
            ORDER BY CASE WHEN task_id = ? THEN 0 ELSE 1 END, sequence_no
            """,
            (task_id, task_id),
        ).fetchall()
        timeline_rows = conn.execute(
            """
            SELECT * FROM task_review_timeline
            WHERE task_id IN (?, '*')
            ORDER BY CASE WHEN task_id = ? THEN 0 ELSE 1 END, sequence_no
            """,
            (task_id, task_id),
        ).fetchall()
        review_columns = [row["name"] for row in conn.execute("PRAGMA table_info(review_record)").fetchall()]
        if "task_id" in review_columns:
            review_rows = conn.execute(
                "SELECT * FROM review_record WHERE task_id = ? ORDER BY submit_time DESC",
                (task_id,),
            ).fetchall()
        else:
            review_rows = []

    documents = [
        {
            "id": row["id"],
            "name": row["name"],
            "required": bool(row["required"]),
            "format": row["format_rule"],
            "status": row["status"],
            "templateAvailable": bool(row["template_available"]),
        }
        for row in requirement_rows
    ]
    completed = sum(1 for row in documents if row["status"] in ("已关联", "审核通过"))
    missing = sum(1 for row in documents if row["status"] == "缺失")
    abnormal = sum(1 for row in documents if row["status"] == "格式异常")

    return {
        "task": {
            "id": task["id"],
            "name": task["name"],
            "module": task["module_code"],
            "moduleName": task["module_name"],
            "cycle": task["cycle"],
            "cycleType": task["cycle_type"],
            "deadline": task["deadline"],
            "deadlineDisplay": task["deadline"],
            "progressCurrent": task["progress_current"],
            "progressTotal": task["progress_total"],
            "status": task["status"],
            "nextStep": task["next_step"],
            "assignee": task["assignee"],
            "assigneeDept": task["assignee_dept"],
            "priorityCode": task["priority_code"],
        },
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
        "linkedDocuments": [
            {
                "relationId": row["id"],
                "documentId": row["id"],
                "documentName": row["name"],
                "documentType": row["format_rule"],
                "period": task["cycle"],
                "version": "V1",
                "validityStatus": "有效",
                "source": "SQLite fallback",
                "relationType": "REQUIREMENT",
                "relationStatus": "LINKED",
                "matchScore": 90,
                "linkedAt": "",
                "uploadedAt": "",
            }
            for row in requirement_rows
            if row["status"] in ("已关联", "审核通过")
        ],
        "validationIssues": [
            {
                "id": row["id"],
                "documentRequirementId": row["id"],
                "documentName": row["name"],
                "issueType": row["status"],
                "severity": "warning" if row["status"] == "格式异常" else "error",
                "message": f"{row['name']}当前状态为{row['status']}",
                "canSubmit": False,
            }
            for row in requirement_rows
            if row["status"] in ("缺失", "格式异常")
        ],
        "aiRecommendation": {
            "fileName": "弃渣场巡查记录_2026-07.pdf",
            "matchRate": 96,
            "text": "该资料已用于其他流程，无需重复上传",
        },
        "aiTip": "还缺少“审核确认单”，建议下载模板后补充签章。",
        "reviewTimeline": [
            {
                "time": row["event_time"],
                "action": row["action_text"],
            }
            for row in timeline_rows
        ],
        "reviewRecords": [
            {
                "id": row["id"],
                "taskId": row["task_id"] if "task_id" in row.keys() else task_id,
                "taskName": row["task_name"],
                "submitTime": row["submit_time"],
                "status": row["status"],
                "reviewer": row["reviewer"],
                "commentSummary": row["comment_summary"],
                "nextStep": row["next_step"],
            }
            for row in review_rows
        ],
    }


def get_document_summary() -> dict:
    mysql_payload = try_mysql(mysql_api.get_document_summary)
    if mysql_payload is not None:
        return mysql_payload

    with connect() as conn:
        row = conn.execute("SELECT * FROM document_summary WHERE id = 1").fetchone()
    return {
        "documentTotal": row["document_total"],
        "monthNew": row["month_new"],
        "pendingArchive": row["pending_archive"],
        "expiringSoon": row["expiring_soon"],
    }


def get_documents() -> dict:
    mysql_payload = try_mysql(mysql_api.get_documents)
    if mysql_payload is not None:
        return mysql_payload

    with connect() as conn:
        rows = conn.execute("SELECT * FROM document_record ORDER BY uploaded_at DESC").fetchall()
    return {
        "total": 368,
        "items": [
            {
                "id": row["id"],
                "documentName": row["document_name"],
                "documentType": row["document_type"],
                "module": row["module_code"],
                "period": row["period_value"],
                "version": row["version_no"],
                "source": row["source_name"],
                "relationCount": row["relation_count"],
                "validityStatus": row["validity_status"],
                "uploadedAt": row["uploaded_at"],
            }
            for row in rows
        ],
    }


def get_document_detail_fallback(document_id: str) -> dict | None:
    with connect() as conn:
        row = conn.execute("SELECT * FROM document_record WHERE id = ?", (document_id,)).fetchone()
    if row is None:
        return None
    return {
        "id": row["id"],
        "documentCode": row["id"],
        "documentName": row["document_name"],
        "documentType": row["document_type"],
        "module": row["module_code"],
        "period": row["period_value"],
        "version": row["version_no"],
        "source": row["source_name"],
        "relationCount": row["relation_count"],
        "validityStatus": row["validity_status"],
        "documentStatus": "ACTIVE",
        "confirmStatus": "CONFIRMED",
        "responsibleUnit": row["source_name"],
        "validStartDate": None,
        "validEndDate": None,
        "uploadedAt": row["uploaded_at"],
        "file": {
            "fileId": None,
            "originalName": row["document_name"],
            "fileExt": row["document_name"].split(".")[-1] if "." in row["document_name"] else None,
            "mimeType": None,
            "fileSize": None,
            "fileSizeText": "-",
            "sha256Hash": None,
            "uploadSource": row["source_name"],
            "uploadTime": row["uploaded_at"],
        },
        "tags": [row["document_type"], row["module_code"], row["period_value"]],
        "isUnique": True,
    }


def get_document_versions_fallback(document_id: str) -> dict:
    detail = get_document_detail_fallback(document_id)
    if detail is None:
        return {"items": []}
    return {
        "items": [
            {
                "id": f"{document_id}-v1",
                "documentId": document_id,
                "versionNo": detail["version"],
                "versionDesc": "SQLite fallback 当前版本",
                "changeType": "CURRENT",
                "uploadedByName": "系统",
                "uploadedAt": detail["uploadedAt"],
                "isCurrent": True,
            }
        ]
    }


def get_document_relations_fallback(document_id: str) -> dict:
    return {"items": []}


def get_reviews() -> dict:
    mysql_payload = try_mysql(mysql_api.get_reviews)
    if mysql_payload is not None:
        return mysql_payload

    with connect() as conn:
        rows = conn.execute("SELECT * FROM review_record ORDER BY submit_time DESC").fetchall()
    task_map = {"r1": "t2", "r2": "t3", "r3": "t5", "r4": "t1"}
    return {
        "statusCards": [
            {"label": "待审核", "value": 3, "unit": "项", "color": "#2f9cff"},
            {"label": "已通过", "value": 21, "unit": "项", "color": "#69e36f"},
            {"label": "已退回", "value": 3, "unit": "项", "color": "#ff4f5e"},
            {"label": "补正逾期", "value": 1, "unit": "项", "color": "#ffb347"},
        ],
        "items": [
            {
                "id": row["id"],
                "taskId": row["task_id"] if "task_id" in row.keys() else task_map.get(row["id"], ""),
                "taskName": row["task_name"],
                "module": row["module_code"],
                "moduleName": row["module_name"],
                "submitTime": row["submit_time"],
                "status": row["status"],
                "reviewer": row["reviewer"],
                "commentSummary": row["comment_summary"],
                "nextStep": row["next_step"],
            }
            for row in rows
        ],
    }


def get_review_detail(review_id: str) -> dict | None:
    mysql_payload = try_mysql(mysql_api.get_review_detail, review_id)
    if mysql_payload is not None:
        return mysql_payload
    with connect() as conn:
        row = conn.execute("SELECT * FROM review_record WHERE id = ?", (review_id,)).fetchone()
    if row is None:
        return None
    task_map = {"r1": "t2", "r2": "t3", "r3": "t5", "r4": "t1"}
    return {
        "id": row["id"],
        "taskId": row["task_id"] if "task_id" in row.keys() else task_map.get(row["id"], ""),
        "taskName": row["task_name"],
        "module": row["module_code"],
        "moduleName": row["module_name"],
        "submitTime": row["submit_time"],
        "status": row["status"],
        "reviewer": row["reviewer"],
        "commentSummary": row["comment_summary"],
        "nextStep": row["next_step"],
        "correctionDeadline": None,
        "requirementCount": 0,
    }


def get_review_timeline(review_id: str) -> dict:
    return try_mysql(mysql_api.get_review_timeline, review_id) or {"items": []}


def get_review_requirements(review_id: str) -> dict:
    return try_mysql(mysql_api.get_review_requirements, review_id) or {"items": []}


def get_ai_parse_queue() -> dict:
    mysql_payload = try_mysql(mysql_api.get_ai_parse_queue)
    if mysql_payload is not None:
        return mysql_payload

    with connect() as conn:
        rows = conn.execute("SELECT * FROM ai_parse_item ORDER BY id").fetchall()
    return {
        "items": [
            {
                "id": row["id"],
                "fileName": row["file_name"],
                "size": row["file_size"],
                "progress": row["progress"],
                "status": row["status"],
            }
            for row in rows
        ]
    }


class Handler(BaseHTTPRequestHandler):
    def log_message(self, format: str, *args: object) -> None:
        print(f"[api] {self.address_string()} - {format % args}")

    def do_OPTIONS(self) -> None:
        json_response(self, {"ok": True})

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        path = parsed.path.rstrip("/") or "/"
        query = parse_qs(parsed.query)

        if path == "/health":
            mysql_status = None
            if mysql_enabled():
                try:
                    mysql_status = mysql_ping()
                except Exception as exc:
                    mysql_status = {"ok": False, "engine": "mysql", "message": str(exc)}
            json_response(
                self,
                {
                    "ok": True,
                    "service": "luoyi-esg-api",
                    "mode": "mysql-first" if mysql_enabled() else "sqlite",
                    "sqlite": str(DB_PATH),
                    "mysql": mysql_status,
                },
            )
            return

        if not DB_PATH.exists() and not mysql_enabled():
            json_response(self, {"ok": False, "message": "数据库不存在，请先执行 python server/init_db.py"}, HTTPStatus.SERVICE_UNAVAILABLE)
            return

        if path == "/api/project/sections":
            section_code = (query.get("sectionCode") or [None])[0]
            payload = try_mysql(mysql_api.get_project_sections, section_code)
            if payload is None:
                json_response(self, {"code": 503, "message": "MySQL 项目合同段数据不可用", "data": None}, HTTPStatus.SERVICE_UNAVAILABLE)
            else:
                json_response(self, payload)
            return

        if path == "/api/project/phases":
            at_time = (query.get("at") or query.get("currentTime") or [None])[0]
            payload = try_mysql(mysql_api.get_project_phases, at_time)
            if payload is None:
                json_response(self, {"code": 503, "message": "MySQL 项目阶段数据不可用", "data": None}, HTTPStatus.SERVICE_UNAVAILABLE)
            else:
                json_response(self, payload)
            return

        if path == "/api/project/engineering-objects":
            section_code = (query.get("sectionCode") or [None])[0]
            object_type = (query.get("objectType") or [None])[0]
            at_time = (query.get("at") or query.get("currentTime") or [None])[0]
            payload = try_mysql(mysql_api.get_project_engineering_objects, section_code, object_type, at_time)
            if payload is None:
                json_response(self, {"code": 503, "message": "MySQL 工程对象数据不可用", "data": None}, HTTPStatus.SERVICE_UNAVAILABLE)
            else:
                json_response(self, payload)
            return

        if path == "/api/environment/monitor-points":
            section_code = (query.get("sectionCode") or [None])[0]
            monitor_category = (query.get("monitorCategory") or query.get("monitorType") or [None])[0]
            at_time = (query.get("at") or query.get("currentTime") or [None])[0]
            payload = try_mysql(mysql_api.get_environment_monitor_points, section_code, monitor_category, at_time)
            if payload is None:
                json_response(self, {"code": 503, "message": "MySQL 环境监测点位数据不可用", "data": None}, HTTPStatus.SERVICE_UNAVAILABLE)
            else:
                json_response(self, payload)
            return

        if path == "/api/environment/e01/events":
            demo = try_mysql(esg_demo_api.get_e01_demo_events)
            if demo is not None:
                json_response(self, demo)
                return
            payload = try_mysql(mysql_api.get_e01_events)
            if payload is None:
                json_response(self, {"code": 503, "message": "MySQL E01 超标事件数据不可用", "data": None}, HTTPStatus.SERVICE_UNAVAILABLE)
            else:
                json_response(self, payload)
            return

        if path.startswith("/api/environment/e01/points/") and path.endswith("/trend"):
            point_id_raw = path.removeprefix("/api/environment/e01/points/").removesuffix("/trend").rstrip("/")
            try:
                point_id = int(point_id_raw)
            except ValueError:
                bad_request(self, "E01 点位 ID 必须为整数")
                return
            factor_code = (query.get("factorCode") or query.get("factor_code") or [None])[0]
            demo = try_mysql(esg_demo_api.get_e01_demo_point_trend, point_id, factor_code)
            if demo is not None:
                json_response(self, demo)
                return
            payload = try_mysql(mysql_api.get_e01_point_trend, point_id, factor_code)
            if payload is None:
                json_response(self, {"code": 404, "message": "E01 点位趋势不存在或 MySQL 数据不可用", "data": None}, HTTPStatus.NOT_FOUND)
            else:
                json_response(self, payload)
            return

        if path.startswith("/api/environment/e01/events/"):
            event_id_raw = path.removeprefix("/api/environment/e01/events/").rstrip("/")
            try:
                event_id = int(event_id_raw)
            except ValueError:
                bad_request(self, "E01 事件 ID 必须为整数")
                return
            demo = try_mysql(esg_demo_api.get_e01_demo_event_detail, event_id)
            if demo is not None:
                json_response(self, demo)
                return
            payload = try_mysql(mysql_api.get_e01_event_detail, event_id)
            if payload is None:
                json_response(self, {"code": 404, "message": "E01 超标事件不存在或 MySQL 数据不可用", "data": None}, HTTPStatus.NOT_FOUND)
            else:
                json_response(self, payload)
            return

        if path == "/api/environment/e02/objects":
            demo = try_mysql(esg_demo_api.get_e02_demo_objects)
            if demo is None:
                json_response(self, {"code": 503, "message": "Demo E02 水保对象数据不可用", "data": None}, HTTPStatus.SERVICE_UNAVAILABLE)
            else:
                json_response(self, demo)
            return

        if path.startswith("/api/environment/e02/objects/"):
            object_id_raw = path.removeprefix("/api/environment/e02/objects/").rstrip("/")
            try:
                object_id = int(object_id_raw)
            except ValueError:
                bad_request(self, "E02 对象 ID 必须为整数")
                return
            demo = try_mysql(esg_demo_api.get_e02_demo_object_detail, object_id)
            if demo is None:
                json_response(self, {"code": 404, "message": "E02 水保对象不存在", "data": None}, HTTPStatus.NOT_FOUND)
            else:
                json_response(self, demo)
            return

        if path == "/api/environment/e02/issues":
            scope = (query.get("scope") or [None])[0]
            payload = try_mysql(mysql_api.get_e02_issues, scope)
            if payload is None:
                json_response(self, {"code": 503, "message": "MySQL E02 环保问题数据不可用", "data": None}, HTTPStatus.SERVICE_UNAVAILABLE)
            else:
                json_response(self, payload)
            return

        if path.startswith("/api/environment/e02/issues/"):
            issue_id_raw = path.removeprefix("/api/environment/e02/issues/").rstrip("/")
            try:
                issue_id = int(issue_id_raw)
            except ValueError:
                bad_request(self, "E02 问题 ID 必须为整数")
                return
            payload = try_mysql(mysql_api.get_e02_issue_detail, issue_id)
            if payload is None:
                json_response(self, {"code": 404, "message": "E02 问题不存在或 MySQL 数据不可用", "data": None}, HTTPStatus.NOT_FOUND)
            else:
                json_response(self, payload)
            return

        # E03 水土保持问题工作台 API（legacy）；生态对象走 eco-objects
        if path == "/api/environment/e03/eco-objects":
            demo = try_mysql(esg_demo_api.get_e03_demo_eco_objects)
            if demo is None:
                json_response(self, {"code": 503, "message": "Demo E03 生态对象数据不可用", "data": None}, HTTPStatus.SERVICE_UNAVAILABLE)
            else:
                json_response(self, demo)
            return

        if path.startswith("/api/environment/e03/eco-objects/"):
            object_id_raw = path.removeprefix("/api/environment/e03/eco-objects/").rstrip("/")
            try:
                object_id = int(object_id_raw)
            except ValueError:
                bad_request(self, "E03 生态对象 ID 必须为整数")
                return
            demo = try_mysql(esg_demo_api.get_e03_demo_eco_object_detail, object_id)
            if demo is None:
                json_response(self, {"code": 404, "message": "E03 生态对象不存在", "data": None}, HTTPStatus.NOT_FOUND)
            else:
                json_response(self, demo)
            return

        if path == "/api/environment/e03/issues":
            scope = (query.get("scope") or [None])[0]
            payload = try_mysql(mysql_api.get_e03_issues, scope)
            if payload is None:
                json_response(self, {"code": 503, "message": "MySQL E03 水保问题数据不可用", "data": None}, HTTPStatus.SERVICE_UNAVAILABLE)
            else:
                json_response(self, payload)
            return

        if path.startswith("/api/environment/e03/issues/"):
            issue_id_raw = path.removeprefix("/api/environment/e03/issues/").rstrip("/")
            try:
                issue_id = int(issue_id_raw)
            except ValueError:
                bad_request(self, "E03 问题 ID 必须为整数")
                return
            scope = (query.get("scope") or [None])[0]
            payload = try_mysql(mysql_api.get_e03_issue_detail, issue_id, scope)
            if payload is None:
                json_response(self, {"code": 404, "message": "E03 问题不存在或 MySQL 数据不可用", "data": None}, HTTPStatus.NOT_FOUND)
            else:
                json_response(self, payload)
            return

        # E04 文物保护管控工作台 API（首页 E04；不改动碳足迹专题）
        if path == "/api/environment/e04/cultural-objects":
            demo = try_mysql(esg_demo_api.get_e04_demo_cultural_objects)
            if demo is not None:
                json_response(self, demo)
                return
            try:
                payload = mysql_api.get_e04_cultural_objects()
            except Exception as exc:
                print(f"[api] E04 cultural objects fallback: {exc}")
                payload = {
                    "code": 0,
                    "data": {
                        "overview": {
                            "objectCount": 0,
                            "measureRate": 100,
                            "riskCount": 0,
                            "status": "正常",
                            "riskStatus": "正常",
                            "surveyStatus": "文物调查已完成",
                        },
                        "objects": [],
                        "isDemo": True,
                        "source": "offline-fallback",
                    },
                }
            json_response(self, payload)
            return

        if path.startswith("/api/environment/e04/cultural-objects/"):
            object_id_raw = path.removeprefix("/api/environment/e04/cultural-objects/").rstrip("/")
            try:
                object_id = int(object_id_raw)
            except ValueError:
                bad_request(self, "E04 文物对象 ID 必须为整数")
                return
            demo = try_mysql(esg_demo_api.get_e04_demo_cultural_object_detail, object_id)
            if demo is not None:
                json_response(self, demo)
                return
            try:
                payload = mysql_api.get_e04_cultural_object_detail(object_id)
            except Exception as exc:
                print(f"[api] E04 cultural detail fallback: {exc}")
                payload = None
            if payload is None:
                json_response(self, {"code": 404, "message": "E04 文物保护对象不存在", "data": None}, HTTPStatus.NOT_FOUND)
            else:
                json_response(self, payload)
            return

        # S02 安全风险点工作台 API
        if path == "/api/social/s02/risks":
            payload = try_mysql(mysql_api.get_s02_risks)
            if payload is None:
                json_response(self, {"code": 503, "message": "MySQL S02 安全风险点数据不可用", "data": None}, HTTPStatus.SERVICE_UNAVAILABLE)
            else:
                json_response(self, payload)
            return

        if path.startswith("/api/social/s02/risks/"):
            risk_id_raw = path.removeprefix("/api/social/s02/risks/").rstrip("/")
            try:
                risk_id = int(risk_id_raw)
            except ValueError:
                bad_request(self, "S02 风险点 ID 必须为整数")
                return
            payload = try_mysql(mysql_api.get_s02_risk_detail, risk_id)
            if payload is None:
                json_response(self, {"code": 404, "message": "S02 风险点不存在或 MySQL 数据不可用", "data": None}, HTTPStatus.NOT_FOUND)
            else:
                json_response(self, payload)
            return

        if path.startswith("/api/environment/monitor-points/"):
            point_path = path.removeprefix("/api/environment/monitor-points/")
            is_history = point_path.endswith("/history")
            point_id_raw = point_path.removesuffix("/history").rstrip("/") if is_history else point_path
            try:
                point_id = int(point_id_raw)
            except ValueError:
                bad_request(self, "监测点位 ID 必须为整数")
                return
            if is_history:
                try:
                    limit = int((query.get("limit") or ["20"])[0])
                except ValueError:
                    bad_request(self, "limit 必须为整数")
                    return
                payload = try_mysql(mysql_api.get_environment_monitor_point_history, point_id, limit)
            else:
                at_time = (query.get("at") or query.get("currentTime") or [None])[0]
                payload = try_mysql(mysql_api.get_environment_monitor_point, point_id, at_time)
            if payload is None:
                json_response(self, {"code": 404, "message": "监测点位不存在或 MySQL 数据不可用", "data": None}, HTTPStatus.NOT_FOUND)
            else:
                json_response(self, payload)
            return

        if path == "/api/esg/gis/layers":
            project_id = (query.get("projectId") or ["LUOYI-ESG"])[0]
            section_id = (query.get("sectionId") or [None])[0]
            current_time = (query.get("currentTime") or [None])[0]
            visible_layer_ids_raw = (query.get("visibleLayerIds") or [None])[0]
            visible_layer_ids = [item for item in (visible_layer_ids_raw or "").split(",") if item] or None
            payload = try_mysql(mysql_api.get_gis_layers, project_id, section_id, current_time, visible_layer_ids)
            if payload is None:
                payload = gis_static_layers(project_id, section_id, current_time, visible_layer_ids)
                json_response(self, payload, HTTPStatus.OK)
            else:
                json_response(self, payload)
            return

        if path == "/api/esg/gis/features":
            project_id = (query.get("projectId") or ["LUOYI-ESG"])[0]
            section_id = (query.get("sectionId") or [None])[0]
            current_time = (query.get("currentTime") or [None])[0]
            layer_id = (query.get("layerId") or [None])[0]
            payload = try_mysql(mysql_api.get_gis_features, project_id, layer_id, section_id, current_time)
            if payload is None:
                payload = gis_static_features(project_id, layer_id, section_id, current_time)
                json_response(self, payload, HTTPStatus.OK)
            else:
                json_response(self, payload)
            return

        if path.startswith("/api/esg/gis/features/"):
            project_id = (query.get("projectId") or ["LUOYI-ESG"])[0]
            feature_path = path.removeprefix("/api/esg/gis/features/")
            if feature_path.endswith("/business-links"):
                feature_id = unquote(feature_path.removesuffix("/business-links").rstrip("/"))
                payload = try_mysql(mysql_api.get_gis_feature_business_links, feature_id, project_id)
                if payload is None:
                    json_response(self, {"code": 500, "message": "GIS feature business links MySQL 数据暂不可用", "data": None}, HTTPStatus.OK)
                else:
                    json_response(self, payload)
                return

            if feature_path.endswith("/relations"):
                feature_id = unquote(feature_path.removesuffix("/relations").rstrip("/"))
                payload = try_mysql(mysql_api.get_gis_feature_relations, feature_id, project_id)
                if payload is None:
                    json_response(self, {"code": 500, "message": "GIS feature relations MySQL 数据暂不可用", "data": None}, HTTPStatus.OK)
                else:
                    json_response(self, payload)
                return

            feature_id = unquote(feature_path)
            payload = try_mysql(mysql_api.get_gis_feature_detail, feature_id, project_id)
            if payload is None:
                json_response(self, {"code": 500, "message": "GIS feature detail MySQL 数据暂不可用", "data": None}, HTTPStatus.OK)
            else:
                json_response(self, payload)
            return

        if path == "/api/dashboard/kpis":
            json_response(self, get_dashboard_kpis())
            return

        if path == "/api/dashboard/risk-warnings":
            project_id = int((query.get("projectId") or ["1001"])[0] or 1001)
            status = (query.get("status") or [None])[0]
            page = int((query.get("page") or ["1"])[0] or 1)
            page_size = int((query.get("pageSize") or ["20"])[0] or 20)
            payload = get_dashboard_risk_warnings(project_id, status, page, page_size)
            if payload is None:
                json_response(
                    self,
                    {"items": [], "total": 0, "page": page, "pageSize": page_size, "source": "unavailable"},
                )
            else:
                json_response(self, payload)
            return

        if path == "/api/dashboard/panels":
            json_response(self, get_dashboard_panels())
            return

        if path == "/api/carbon/benefit-overview":
            topic = get_dashboard_topic("carbon")
            if topic is None:
                not_found(self)
            else:
                json_response(self, topic)
            return

        # ESG 智能助手 · 库驱动问答（builders 内部容错；不依赖 try_mysql 短路）
        if path in {"/api/assistant/ask", "/api/assistant/qa"}:
            question = (query.get("question") or query.get("q") or [None])[0]
            question_id = (query.get("question_id") or query.get("questionId") or [None])[0]
            json_response(self, assistant_qa.ask(question, question_id))
            return

        if path == "/api/monthly-report/readiness":
            report_period = (query.get("reportPeriod") or [""])[0]
            if not report_period:
                json_response(
                    self,
                    {"code": 400, "message": "reportPeriod不能为空", "data": None},
                    HTTPStatus.BAD_REQUEST,
                )
                return
            readiness = try_mysql(
                monthly_report_readiness.get_monthly_report_readiness,
                report_period,
            )
            if readiness is None:
                json_response(
                    self,
                    {"code": 404, "message": f"未找到月报资料归集数据：{report_period}", "data": None},
                    HTTPStatus.NOT_FOUND,
                )
            else:
                json_response(self, readiness)
            return

        if path in {"/api/monthly/readiness", "/api/monthly/report-overview"}:
            report_period = (query.get("reportMonth") or query.get("reportPeriod") or [""])[0] or None
            overview = try_mysql(monthly_report_overview.get_monthly_report_overview, report_period)
            if overview is None:
                overview = load_monthly_overview_snapshot(report_period)
            if overview is None:
                not_found(self)
            else:
                json_response(self, overview)
            return

        if path.startswith("/api/dashboard/topics/"):
            topic_key = path.removeprefix("/api/dashboard/topics/")
            topic = get_dashboard_topic(topic_key)
            if topic is None:
                not_found(self)
            else:
                json_response(self, topic)
            return

        if path == "/api/dashboard/snapshot":
            snapshot_type = (query.get("type") or ["LEADER_HOME"])[0]
            snapshot = get_snapshot(snapshot_type)
            json_response(self, snapshot if snapshot is not None else {})
            return

        if path == "/api/dashboard/kpi/S01":
            json_response(self, get_s01_detail())
            return

        if path.startswith("/api/dashboard/kpi/") and "/objects/" in path:
            # GET /api/dashboard/kpi/{key}/objects/{objectId}
            rest = path.removeprefix("/api/dashboard/kpi/")
            parts = rest.split("/objects/")
            if len(parts) == 2 and parts[0] and parts[1]:
                kpi_code = parts[0]
                try:
                    object_id = int(parts[1].split("/")[0])
                except ValueError:
                    not_found(self)
                    return
                project_id = int((query.get("projectId") or ["1001"])[0] or 1001)
                payload = get_dashboard_kpi_object(kpi_code, object_id, project_id)
                if payload is None:
                    not_found(self)
                else:
                    json_response(self, payload)
                return

        if path.startswith("/api/dashboard/kpi/"):
            kpi_code = path.removeprefix("/api/dashboard/kpi/")
            detail = get_dashboard_kpi_detail(kpi_code)
            if detail is None:
                not_found(self)
            else:
                json_response(self, detail)
            return

        if path == "/api/governance/rectification-tasks":
            filters = {
                "taskStatus": (query.get("taskStatus") or [None])[0],
                "dataNature": (query.get("dataNature") or [None])[0],
                "isDemo": (query.get("isDemo") or [None])[0],
                "completed": (query.get("completed") or [None])[0],
            }
            try:
                payload = mysql_api.get_rectification_tasks(filters)
            except ValueError as exc:
                bad_request(self, str(exc))
                return
            except Exception as exc:
                print(f"[api] V0.4 rectification list failed: {exc}")
                service_unavailable(self)
                return
            json_response(self, payload)
            return

        if path.startswith("/api/governance/rectification-tasks/"):
            parts = path.split("/")
            if len(parts) != 5 or not parts[4]:
                bad_request(self, "整改任务 ID 无效")
                return
            try:
                task_id = int(parts[4])
                payload = mysql_api.get_rectification_task(task_id)
            except ValueError as exc:
                bad_request(self, str(exc))
                return
            except Exception as exc:
                print(f"[api] V0.4 rectification detail failed: {exc}")
                service_unavailable(self)
                return
            if payload is None:
                not_found(self)
            else:
                json_response(self, payload)
            return

        if path == "/api/governance/special-plans":
            filters = {
                "projectId": (query.get("projectId") or [None])[0],
                "riskPointId": (query.get("riskPointId") or [None])[0],
                "approvalStatus": (query.get("approvalStatus") or [None])[0],
                "riskLevel": (query.get("riskLevel") or [None])[0],
                "dataNature": (query.get("dataNature") or [None])[0],
                "isDemo": (query.get("isDemo") or [None])[0],
            }
            try:
                payload = mysql_api.get_special_plans(filters)
            except ValueError as exc:
                bad_request(self, str(exc))
                return
            except Exception as exc:
                print(f"[api] V0.4 special plan list failed: {exc}")
                service_unavailable(self)
                return
            json_response(self, payload)
            return

        if path.startswith("/api/governance/special-plans/"):
            parts = path.split("/")
            if len(parts) != 5 or not parts[4]:
                bad_request(self, "专项方案 ID 无效")
                return
            try:
                plan_id = int(parts[4])
                payload = mysql_api.get_special_plan(plan_id)
            except ValueError as exc:
                bad_request(self, str(exc))
                return
            except Exception as exc:
                print(f"[api] V0.4 special plan detail failed: {exc}")
                service_unavailable(self)
                return
            if payload is None:
                not_found(self)
            else:
                json_response(self, payload)
            return

        if path == "/api/workspace/summary":
            json_response(self, get_workspace_summary())
            return

        if path.startswith("/api/esg/document/") and path.endswith("/result"):
            parts = path.split("/")
            try:
                analysis_id = int(parts[4])
            except (IndexError, ValueError):
                bad_request(self, "文档解析 ID 无效")
                return
            try:
                result = ai_document_analysis.get_analysis_result(analysis_id)
            except ValueError as exc:
                bad_request(self, str(exc))
                return
            if result is None:
                not_found(self)
            else:
                json_response(self, result)
            return

        if path == "/api/workspace/tasks":
            json_response(self, get_tasks(query))
            return

        if path.startswith("/api/workspace/tasks/") and path.endswith("/detail"):
            task_id = path.removeprefix("/api/workspace/tasks/").removesuffix("/detail")
            detail = get_task_detail(task_id)
            if detail is None:
                not_found(self)
            else:
                json_response(self, detail)
            return

        if path == "/api/workspace/documents/summary":
            json_response(self, get_document_summary())
            return

        if path == "/api/workspace/documents":
            json_response(self, get_documents())
            return

        if path.startswith("/api/workspace/documents/"):
            parts = path.split("/")
            try:
                document_id_raw = parts[4]
            except IndexError:
                bad_request(self, "资料 ID 无效")
                return
            document_id_for_mysql = int(document_id_raw) if document_id_raw.isdigit() else None
            if len(parts) == 5:
                detail = try_mysql(mysql_api.get_document_detail, document_id_for_mysql) if document_id_for_mysql is not None else None
                if detail is None:
                    detail = get_document_detail_fallback(document_id_raw)
                if detail is None:
                    not_found(self)
                else:
                    json_response(self, detail)
                return
            if len(parts) == 6 and parts[5] == "versions":
                payload = try_mysql(mysql_api.get_document_versions, document_id_for_mysql) if document_id_for_mysql is not None else None
                json_response(self, payload if payload is not None else get_document_versions_fallback(document_id_raw))
                return
            if len(parts) == 6 and parts[5] == "relations":
                payload = try_mysql(mysql_api.get_document_relations, document_id_for_mysql) if document_id_for_mysql is not None else None
                json_response(self, payload if payload is not None else get_document_relations_fallback(document_id_raw))
                return

        if path == "/api/workspace/reviews":
            json_response(self, get_reviews())
            return

        if path.startswith("/api/workspace/reviews/"):
            parts = path.split("/")
            try:
                review_id = parts[4]
            except IndexError:
                bad_request(self, "审核记录 ID 无效")
                return
            if len(parts) == 5:
                detail = get_review_detail(review_id)
                if detail is None:
                    not_found(self)
                else:
                    json_response(self, detail)
                return
            if len(parts) == 6 and parts[5] == "timeline":
                json_response(self, get_review_timeline(review_id))
                return
            if len(parts) == 6 and parts[5] == "requirements":
                json_response(self, get_review_requirements(review_id))
                return

        if path == "/api/workspace/ai/parse-queue":
            json_response(self, get_ai_parse_queue())
            return

        if path.startswith("/api/workspace/parse-jobs/"):
            parts = path.split("/")
            try:
                job_id = int(parts[4])
            except (IndexError, ValueError):
                bad_request(self, "解析任务 ID 无效")
                return
            if len(parts) == 5:
                payload = try_mysql(mysql_api.get_parse_job, job_id)
                json_response(self, payload if payload is not None else {})
                return
            if len(parts) == 6 and parts[5] == "fields":
                payload = try_mysql(mysql_api.get_parse_fields, job_id)
                json_response(self, payload if payload is not None else {"items": []})
                return
            if len(parts) == 6 and parts[5] == "match-candidates":
                payload = try_mysql(mysql_api.get_match_candidates, job_id)
                json_response(self, payload if payload is not None else {"items": []})
                return

        not_found(self)

    def do_POST(self) -> None:
        parsed = urlparse(self.path)
        path = parsed.path.rstrip("/") or "/"

        if path in {"/api/assistant/ask", "/api/assistant/qa"}:
            try:
                body = read_json_body(self)
            except json.JSONDecodeError:
                bad_request(self, "请求体不是合法 JSON")
                return
            question = body.get("question") or body.get("q")
            question_id = body.get("question_id") or body.get("questionId")
            json_response(
                self,
                assistant_qa.ask(
                    question if isinstance(question, str) else None,
                    question_id if isinstance(question_id, str) else None,
                ),
            )
            return

        if path == "/api/workspace/files/upload":
            try:
                payload = read_upload_payload(self)
            except (json.JSONDecodeError, ValueError) as exc:
                bad_request(self, str(exc))
                return
            result = try_mysql(mysql_api.create_file_asset, payload)
            if result is None:
                bad_request(self, "MySQL 不可用，暂不能写入智能入库数据")
            else:
                json_response(self, result)
            return

        try:
            payload = read_json_body(self)
        except json.JSONDecodeError:
            bad_request(self, "请求体不是合法 JSON")
            return

        if path == "/api/esg/document/analyze":
            try:
                result = ai_document_analysis.analyze_document(payload)
            except ValueError as exc:
                bad_request(self, str(exc))
                return
            json_response(self, result, HTTPStatus.CREATED)
            return

        if path == "/api/governance/special-plans":
            try:
                result = mysql_api.create_special_plan(payload)
            except ValueError as exc:
                bad_request(self, str(exc))
                return
            except Exception as exc:
                print(f"[api] V0.4 special plan create failed: {exc}")
                service_unavailable(self)
                return
            json_response(self, result, HTTPStatus.CREATED)
            return

        if path.startswith("/api/workspace/tasks/"):
            parts = path.split("/")
            try:
                task_id = parts[4]
                action = parts[5]
            except IndexError:
                bad_request(self, "任务接口路径无效")
                return
            try:
                if action == "save":
                    result = try_mysql(mysql_api.save_task_draft, task_id, payload)
                elif action == "link-document":
                    result = try_mysql(mysql_api.link_task_document, task_id, payload)
                elif action == "submit":
                    result = try_mysql(mysql_api.submit_task_review, task_id, payload)
                else:
                    result = None
            except ValueError as exc:
                bad_request(self, str(exc))
                return
            if result is None:
                not_found(self)
            else:
                json_response(self, result)
            return

        if path.startswith("/api/workspace/reviews/"):
            parts = path.split("/")
            try:
                review_id = parts[4]
                action = parts[5]
            except IndexError:
                bad_request(self, "审核接口路径无效")
                return
            if action == "approve":
                result = try_mysql(mysql_api.approve_review, review_id, payload)
            elif action == "return":
                result = try_mysql(mysql_api.return_review, review_id, payload)
            else:
                result = None
            if result is None:
                not_found(self)
            else:
                json_response(self, result)
            return

        if path.startswith("/api/workspace/files/") and path.endswith("/parse"):
            try:
                file_id = int(path.removeprefix("/api/workspace/files/").removesuffix("/parse"))
            except ValueError:
                bad_request(self, "文件 ID 无效")
                return
            result = try_mysql(mysql_api.start_parse_job, file_id)
            if result is None:
                bad_request(self, "发起解析失败")
            else:
                json_response(self, result)
            return

        if path.startswith("/api/workspace/parse-jobs/") and path.endswith("/confirm"):
            try:
                job_id = int(path.removeprefix("/api/workspace/parse-jobs/").removesuffix("/confirm"))
            except ValueError:
                bad_request(self, "解析任务 ID 无效")
                return
            result = try_mysql(mysql_api.confirm_parse_job, job_id, payload)
            if result is None:
                bad_request(self, "确认入库失败")
            else:
                json_response(self, result)
            return

        not_found(self)

    def do_PATCH(self) -> None:
        parsed = urlparse(self.path)
        path = parsed.path.rstrip("/") or "/"
        try:
            payload = read_json_body(self)
        except (json.JSONDecodeError, UnicodeDecodeError):
            bad_request(self, "请求体不是合法 JSON")
            return

        if path.startswith("/api/governance/rectification-tasks/"):
            parts = path.split("/")
            if len(parts) != 5 or not parts[4]:
                bad_request(self, "整改任务 ID 无效")
                return
            try:
                result = mysql_api.update_rectification_task(int(parts[4]), payload)
            except ValueError as exc:
                bad_request(self, str(exc))
                return
            except Exception as exc:
                print(f"[api] V0.4 rectification update failed: {exc}")
                service_unavailable(self)
                return
            if result is None:
                not_found(self)
            else:
                json_response(self, result)
            return

        if path.startswith("/api/governance/special-plans/"):
            parts = path.split("/")
            if len(parts) != 5 or not parts[4]:
                bad_request(self, "专项方案 ID 无效")
                return
            try:
                result = mysql_api.update_special_plan(int(parts[4]), payload)
            except ValueError as exc:
                bad_request(self, str(exc))
                return
            except Exception as exc:
                print(f"[api] V0.4 special plan update failed: {exc}")
                service_unavailable(self)
                return
            if result is None:
                not_found(self)
            else:
                json_response(self, result)
            return

        not_found(self)

    def do_DELETE(self) -> None:
        parsed = urlparse(self.path)
        path = parsed.path.rstrip("/") or "/"
        if path.startswith("/api/governance/special-plans/"):
            method_not_allowed(self, "专项方案审批记录禁止物理删除")
            return
        not_found(self)


def main() -> None:
    if not DB_PATH.exists():
        print("数据库不存在，请先执行：python server/init_db.py")
    server = ThreadingHTTPServer((HOST, PORT), Handler)
    print(f"Luoyi ESG API listening on http://{HOST}:{PORT}")
    server.serve_forever()


if __name__ == "__main__":
    main()
