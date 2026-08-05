from __future__ import annotations

import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))

from mysql_db import mysql_connect  # noqa: E402


BASE_DIR = Path(__file__).resolve().parent
PAYLOAD_PATH = BASE_DIR / "dashboard_payload.json"
SCHEMA_PATH = BASE_DIR / "mysql_build_v0.2_dashboard" / "01_dashboard_snapshot_extension.sql"


def execute_script(sql_text: str) -> None:
    statements = [stmt.strip() for stmt in sql_text.split(";") if stmt.strip()]
    with mysql_connect() as conn:
        with conn.cursor() as cur:
            for stmt in statements:
                cur.execute(stmt)


def upsert_snapshots(payload: dict) -> None:
    kpi_details = payload.get("kpiDetails") or {}
    carbon_detail = dict(payload.get("carbonTopicDetail") or {})
    carbon_detail["topicData"] = payload.get("carbonTabData") or {}
    monthly_detail = dict(payload.get("monthlyTopicDetail") or {})
    monthly_detail["topicData"] = payload.get("monthlyTabData") or {}

    panel_payload = {
        "compliance": {
            "metrics": payload.get("complianceMetrics") or [],
            "effectiveness": payload.get("effectivenessItems") or [],
            "safeguards": payload.get("safeguardItems") or [],
        },
        "carbon": {
            "metrics": payload.get("carbonMetrics") or [],
            "sources": payload.get("carbonSources") or [],
            "reductions": payload.get("reductionMeasures") or [],
            "measures": payload.get("reductionMeasures") or [],
        },
        "monthly": payload.get("monthlyReport") or {},
        "timeline": payload.get("timelineSteps") or [],
        "gis": {
            "routePoints": payload.get("routePoints") or [],
            "routeSegments": payload.get("routeSegments") or [],
            "sensitiveAreas": payload.get("sensitiveAreas") or [],
        },
    }

    with mysql_connect() as conn:
        with conn.cursor() as cur:
            for code, detail in kpi_details.items():
                if code == "S01":
                    continue
                detail_for_db = dict(detail)
                detail_for_db["isMock"] = False
                cur.execute(
                    """
                    INSERT INTO dashboard_kpi_detail_snapshot
                    (indicator_code, detail_json, data_version, data_source, published_at)
                    VALUES (%s, %s, 'V0.2', 'dashboard_payload_migration', NOW())
                    ON DUPLICATE KEY UPDATE
                      detail_json = VALUES(detail_json),
                      data_version = VALUES(data_version),
                      data_source = VALUES(data_source),
                      published_at = VALUES(published_at)
                    """,
                    (code, json.dumps(detail_for_db, ensure_ascii=False)),
                )

            for topic_key, detail in {
                "carbon": carbon_detail,
                "monthly-report": monthly_detail,
            }.items():
                detail_for_db = dict(detail)
                detail_for_db["isMock"] = False
                cur.execute(
                    """
                    INSERT INTO dashboard_topic_snapshot
                    (topic_key, detail_json, data_version, data_source, published_at)
                    VALUES (%s, %s, 'V0.2', 'dashboard_payload_migration', NOW())
                    ON DUPLICATE KEY UPDATE
                      detail_json = VALUES(detail_json),
                      data_version = VALUES(data_version),
                      data_source = VALUES(data_source),
                      published_at = VALUES(published_at)
                    """,
                    (topic_key, json.dumps(detail_for_db, ensure_ascii=False)),
                )

            cur.execute(
                """
                INSERT INTO dashboard_panel_snapshot
                (panel_key, panel_json, data_version, data_source, published_at)
                VALUES ('home-panels', %s, 'V0.2', 'dashboard_payload_migration', NOW())
                ON DUPLICATE KEY UPDATE
                  panel_json = VALUES(panel_json),
                  data_version = VALUES(data_version),
                  data_source = VALUES(data_source),
                  published_at = VALUES(published_at)
                """,
                (json.dumps(panel_payload, ensure_ascii=False),),
            )


def main() -> int:
    if not PAYLOAD_PATH.exists():
        raise FileNotFoundError(PAYLOAD_PATH)
    if not SCHEMA_PATH.exists():
        raise FileNotFoundError(SCHEMA_PATH)

    execute_script(SCHEMA_PATH.read_text(encoding="utf-8"))
    payload = json.loads(PAYLOAD_PATH.read_text(encoding="utf-8"))
    upsert_snapshots(payload)
    print("✅ 领导层首页 V0.2 快照扩展已写入 MySQL：11项KPI详情、2个专题、首页面板。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
