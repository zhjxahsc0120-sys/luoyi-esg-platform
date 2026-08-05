from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from mysql_db import mysql_connect


ROOT_DIR = Path(__file__).resolve().parents[1]
SHP_DIR = ROOT_DIR / "public" / "data" / "shp"
MANIFEST_PATH = SHP_DIR / "manifest.json"


def dump_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"))


def execute(sql: str, params: tuple[Any, ...] = ()) -> None:
    with mysql_connect() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, params)


def query_one(sql: str, params: tuple[Any, ...] = ()) -> dict | None:
    with mysql_connect() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, params)
            return cur.fetchone()


def create_tables() -> None:
    execute(
        """
        CREATE TABLE IF NOT EXISTS gis_layer (
          id VARCHAR(64) PRIMARY KEY,
          project_id VARCHAR(64) NOT NULL DEFAULT 'LUOYI-ESG',
          name VARCHAR(120) NOT NULL,
          category VARCHAR(64) NULL,
          geometry_type VARCHAR(20) NOT NULL,
          enabled TINYINT(1) NOT NULL DEFAULT 1,
          object_type VARCHAR(64) NULL,
          source_type VARCHAR(32) NOT NULL DEFAULT 'api',
          source_url VARCHAR(255) NULL,
          style_json JSON NOT NULL,
          fields_json JSON NULL,
          feature_count INT NOT NULL DEFAULT 0,
          display_order INT NOT NULL DEFAULT 0,
          created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
          updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci
        """
    )
    execute(
        """
        CREATE TABLE IF NOT EXISTS gis_feature (
          id VARCHAR(96) PRIMARY KEY,
          project_id VARCHAR(64) NOT NULL DEFAULT 'LUOYI-ESG',
          layer_id VARCHAR(64) NOT NULL,
          section_id VARCHAR(64) NULL,
          object_type VARCHAR(64) NOT NULL,
          name VARCHAR(160) NOT NULL,
          geometry_json JSON NOT NULL,
          properties_json JSON NOT NULL,
          status VARCHAR(32) NULL,
          risk_level INT NULL,
          updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
          INDEX idx_gis_feature_layer (layer_id),
          INDEX idx_gis_feature_section (section_id),
          CONSTRAINT fk_gis_feature_layer
            FOREIGN KEY (layer_id) REFERENCES gis_layer(id)
            ON DELETE CASCADE
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci
        """
    )


def section_id_for_layer(layer: dict) -> str | None:
    name = str(layer.get("name") or "")
    object_type = layer.get("objectType")
    if object_type == "road-section":
        return name
    for prefix in ("弃渣点", "水源保护区", "边坡监测点"):
        if name.startswith(prefix):
            suffix = name.removeprefix(prefix)
            if suffix.isdigit():
                return f"{suffix}标段"
    if name == "生态保护区1":
        return "1标段"
    return None


def category_for_layer(layer: dict) -> str:
    object_type = layer.get("objectType")
    return {
        "road-section": "施工标段",
        "spoil-site": "弃渣点",
        "water-source": "水源保护区",
        "ecological-zone": "生态保护区",
        "slope-monitor": "边坡监测点",
        "chainage": "路线桩号",
    }.get(object_type, str(layer.get("name") or "其他"))


SECTION_PROFILES = {
    "1标段": {
        "施工单位": "广西路桥工程集团第一项目部",
        "监理单位": "广西交通工程监理咨询公司",
        "建设进度": "72%",
        "环保问题": "1项",
        "风险点": "1处",
        "计划完工": "2027年06月",
        "资料说明": "演示标段资料，后续可由施工进度、环保问题、安全风险等业务表动态同步。",
    },
    "2标段": {
        "施工单位": "广西路建工程集团第二项目部",
        "监理单位": "北京华通公路桥梁监理公司",
        "建设进度": "58%",
        "环保问题": "3项",
        "风险点": "1处",
        "计划完工": "2027年10月",
        "资料说明": "演示标段资料，后续可由施工进度、环保问题、安全风险等业务表动态同步。",
    },
    "3标段": {
        "施工单位": "中交第四公路工程局项目部",
        "监理单位": "广西桂通工程管理集团",
        "建设进度": "46%",
        "环保问题": "2项",
        "风险点": "2处",
        "计划完工": "2028年03月",
        "资料说明": "演示标段资料，后续可由施工进度、环保问题、安全风险等业务表动态同步。",
    },
}


ENVIRONMENT_PROFILES = {
    "水源保护区1": {
        "保护区编号": "SY-BH-001",
        "保护对象": "沿线村镇集中式饮用水水源",
        "保护级别": "二级保护区",
        "水体类型": "地表水",
        "当前水质": "Ⅲ类",
        "巡查状态": "正常",
        "责任单位": "施工一标项目部环保组",
    },
    "水源保护区2": {
        "保护区编号": "SY-BH-002",
        "保护对象": "河流型饮用水水源补给区",
        "保护级别": "准保护区",
        "水体类型": "河流",
        "当前水质": "Ⅲ类",
        "巡查状态": "正常",
        "责任单位": "施工二标项目部环保组",
    },
    "生态保护区1": {
        "保护区编号": "ST-BH-001",
        "保护类型": "沿线林地与自然植被保护区",
        "敏感等级": "较高",
        "当前扰动情况": "施工边界内局部扰动",
        "植被恢复率": "86%",
        "巡查状态": "正常",
        "责任单位": "施工一标项目部环保组",
    },
}


MONITOR_PROFILES = {
    "边坡监测点1": {
        "监测点编号": "BP-JC-001",
        "设备状态": "在线",
        "地表水平位移": "3.2 mm",
        "垂直沉降": "1.6 mm",
        "深部位移": "2.4 mm",
        "预警状态": "正常",
        "数据更新时间": "2026-07-16 10:30",
    },
    "边坡监测点2": {
        "监测点编号": "BP-JC-002",
        "设备状态": "在线",
        "地表水平位移": "5.8 mm",
        "垂直沉降": "2.1 mm",
        "深部位移": "3.6 mm",
        "预警状态": "关注",
        "数据更新时间": "2026-07-16 10:32",
    },
}


def enrich_properties(layer: dict, feature: dict, feature_name: str, section_id: str | None) -> dict:
    properties = dict(feature.get("properties") or {})
    properties["sourceLayer"] = layer["name"]
    if section_id:
        properties["sectionId"] = section_id

    object_type = layer.get("objectType")
    if object_type == "road-section":
        properties.update(SECTION_PROFILES.get(layer["name"], {}))
    elif object_type in {"water-source", "ecological-zone"}:
        properties.update(ENVIRONMENT_PROFILES.get(layer["name"], {}))
    elif object_type == "slope-monitor":
        properties.update(MONITOR_PROFILES.get(layer["name"], {}))
    elif object_type == "spoil-site":
        properties.update(
            {
                "弃渣场编号": f"QZ-{feature_name[-1].zfill(3)}" if feature_name[-1].isdigit() else "QZ-001",
                "所属标段": section_id,
                "当前状态": "正常管控",
                "最近巡查": "2026-07-15",
                "责任单位": f"施工{section_id[:1]}标项目部环保组" if section_id else "项目环保组",
            }
        )
    return properties


def load_geojson_features(layer: dict) -> list[dict]:
    source_url = (layer.get("source") or {}).get("url")
    if not source_url:
        return []
    source_path = source_url.lstrip("/")
    geojson_path = ROOT_DIR / "public" / source_path if source_path.startswith("data/") else ROOT_DIR / source_path
    collection = json.loads(geojson_path.read_text(encoding="utf-8"))
    return list(collection.get("features") or [])


def upsert_layer(layer: dict, display_order: int, feature_count: int) -> None:
    execute(
        """
        INSERT INTO gis_layer
          (id, project_id, name, category, geometry_type, enabled, object_type,
           source_type, source_url, style_json, fields_json, feature_count, display_order)
        VALUES
          (%s, 'LUOYI-ESG', %s, %s, %s, %s, %s, 'api', %s, CAST(%s AS JSON), CAST(%s AS JSON), %s, %s)
        ON DUPLICATE KEY UPDATE
          name = VALUES(name),
          category = VALUES(category),
          geometry_type = VALUES(geometry_type),
          enabled = VALUES(enabled),
          object_type = VALUES(object_type),
          source_url = VALUES(source_url),
          style_json = VALUES(style_json),
          fields_json = VALUES(fields_json),
          feature_count = VALUES(feature_count),
          display_order = VALUES(display_order),
          updated_at = CURRENT_TIMESTAMP
        """,
        (
            layer["id"],
            layer["name"],
            category_for_layer(layer),
            layer["geometryType"],
            1 if layer.get("enabled", True) else 0,
            layer.get("objectType"),
            (layer.get("source") or {}).get("url"),
            dump_json(layer.get("style") or {}),
            dump_json(layer.get("fields") or []),
            feature_count,
            display_order,
        ),
    )


def upsert_feature(layer: dict, feature: dict, index: int) -> None:
    label_field = (layer.get("style") or {}).get("labelField")
    section_id = section_id_for_layer(layer)
    properties = feature.get("properties") or {}
    feature_name = str(properties.get(label_field) if label_field else layer["name"])
    if feature_name in {"None", ""}:
        feature_name = layer["name"]
    feature_id = str(feature.get("id") or f"{layer['id']}-{index + 1}")
    object_type = layer.get("objectType") or "gis-feature"
    enriched = enrich_properties(layer, feature, feature_name, section_id)
    status = "attention" if layer["id"] == "slope-2" else "normal"
    execute(
        """
        INSERT INTO gis_feature
          (id, project_id, layer_id, section_id, object_type, name, geometry_json,
           properties_json, status, risk_level, updated_at)
        VALUES
          (%s, 'LUOYI-ESG', %s, %s, %s, %s, CAST(%s AS JSON), CAST(%s AS JSON), %s, %s, CURRENT_TIMESTAMP)
        ON DUPLICATE KEY UPDATE
          section_id = VALUES(section_id),
          object_type = VALUES(object_type),
          name = VALUES(name),
          geometry_json = VALUES(geometry_json),
          properties_json = VALUES(properties_json),
          status = VALUES(status),
          risk_level = VALUES(risk_level),
          updated_at = CURRENT_TIMESTAMP
        """,
        (
            feature_id,
            layer["id"],
            section_id,
            object_type,
            feature_name,
            dump_json(feature["geometry"]),
            dump_json(enriched),
            status,
            2 if status == "attention" else None,
        ),
    )


def seed() -> None:
    if not MANIFEST_PATH.exists():
        raise FileNotFoundError(f"GIS manifest not found: {MANIFEST_PATH}")

    create_tables()
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    layers = list(manifest.get("layers") or [])

    with mysql_connect() as conn:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM gis_feature")
            cur.execute("DELETE FROM gis_layer")

    for order, layer in enumerate(layers, start=1):
        features = load_geojson_features(layer)
        upsert_layer(layer, order, len(features))
        for index, feature in enumerate(features):
            upsert_feature(layer, feature, index)

    layer_count = query_one("SELECT COUNT(*) AS c FROM gis_layer")["c"]
    feature_count = query_one("SELECT COUNT(*) AS c FROM gis_feature")["c"]
    print(f"GIS seed complete: {layer_count} layers, {feature_count} features")


if __name__ == "__main__":
    seed()
