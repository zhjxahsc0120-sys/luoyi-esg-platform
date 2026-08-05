"""Deterministic content parser for Workspace ESG smart ingestion demo.

Reads uploaded CSV / TXT (key-value style) without external LLM keys.
When content matches the sample schema, field values come from the file itself.
"""

from __future__ import annotations

import csv
import io
import re
from pathlib import Path
from typing import Any

# Chinese label / English key → canonical field_key
FIELD_ALIASES: dict[str, str] = {
    "资料名称": "document_name",
    "文件名称": "document_name",
    "document_name": "document_name",
    "资料类型": "document_type",
    "document_type": "document_type",
    "esg模块": "esg_module",
    "esg_module": "esg_module",
    "模块": "esg_module",
    "资料周期": "period",
    "周期": "period",
    "period": "period",
    "责任单位": "responsible_unit",
    "responsible_unit": "responsible_unit",
    "项目标段": "project_section",
    "项目/标段": "project_section",
    "标段": "project_section",
    "project_section": "project_section",
    "工程对象": "engineering_object",
    "工程对象/事项": "engineering_object",
    "engineering_object": "engineering_object",
    "监测日期": "monitor_date",
    "monitor_date": "monitor_date",
    "扬尘超标次数": "dust_exceed_count",
    "dust_exceed_count": "dust_exceed_count",
    "噪声超标次数": "noise_exceed_count",
    "noise_exceed_count": "noise_exceed_count",
    "水保问题数量": "water_protection_issue_count",
    "water_protection_issue_count": "water_protection_issue_count",
    "有效期开始": "valid_start_date",
    "valid_start_date": "valid_start_date",
    "有效期结束": "valid_end_date",
    "valid_end_date": "valid_end_date",
    "建议关联任务": "suggested_task",
    "suggested_task": "suggested_task",
    "建议关联指标编码": "suggested_kpi_code",
    "suggested_kpi_code": "suggested_kpi_code",
    "建议关联指标名称": "suggested_kpi_name",
    "suggested_kpi_name": "suggested_kpi_name",
    "柴油用量": "diesel_usage",
    "电力消耗": "electricity_usage",
    "材料用量": "material_usage",
    "碳排放量": "carbon_emission",
    "风险等级": "risk_level",
    "作业位置": "work_location",
    "管控措施": "control_measure",
    "支付人数": "worker_count",
    "支付金额": "payment_amount",
    "支付月份": "payment_month",
    "许可名称": "permit_name",
    "许可编号": "permit_no",
    "许可到期日": "permit_expire_date",
    "整改事项": "rectification_item",
    "整改状态": "rectification_status",
    "关闭日期": "closed_date",
    "摘要说明": "summary_note",
    "监测单位": "monitor_unit",
}

FIELD_LABELS: dict[str, str] = {
    "document_name": "资料名称",
    "document_type": "资料类型",
    "esg_module": "ESG模块",
    "period": "资料周期",
    "responsible_unit": "责任单位",
    "project_section": "项目标段",
    "engineering_object": "工程对象",
    "monitor_date": "监测日期",
    "dust_exceed_count": "扬尘超标次数",
    "noise_exceed_count": "噪声超标次数",
    "water_protection_issue_count": "水保问题数量",
    "valid_start_date": "有效期开始",
    "valid_end_date": "有效期结束",
    "suggested_task": "建议关联任务",
    "suggested_kpi_code": "建议关联指标编码",
    "suggested_kpi_name": "建议关联指标名称",
    "diesel_usage": "柴油用量",
    "electricity_usage": "电力消耗",
    "material_usage": "材料用量",
    "carbon_emission": "碳排放量",
    "risk_level": "风险等级",
    "work_location": "作业位置",
    "control_measure": "管控措施",
    "worker_count": "支付人数",
    "payment_amount": "支付金额",
    "payment_month": "支付月份",
    "permit_name": "许可名称",
    "permit_no": "许可编号",
    "permit_expire_date": "许可到期日",
    "rectification_item": "整改事项",
    "rectification_status": "整改状态",
    "closed_date": "关闭日期",
    "summary_note": "摘要说明",
    "monitor_unit": "监测单位",
}

VALUE_TYPES: dict[str, str] = {
    "monitor_date": "date",
    "valid_start_date": "date",
    "valid_end_date": "date",
    "permit_expire_date": "date",
    "closed_date": "date",
    "dust_exceed_count": "number",
    "noise_exceed_count": "number",
    "water_protection_issue_count": "number",
    "diesel_usage": "number",
    "electricity_usage": "number",
    "material_usage": "number",
    "carbon_emission": "number",
    "worker_count": "number",
    "payment_amount": "number",
}


def _normalize_key(raw: str) -> str | None:
    original = (raw or "").strip().strip("\ufeff")
    if not original:
        return None
    if original in FIELD_ALIASES:
        return FIELD_ALIASES[original]
    lower = original.lower()
    if lower in FIELD_ALIASES:
        return FIELD_ALIASES[lower]
    for alias, canonical in FIELD_ALIASES.items():
        if alias.lower() == lower:
            return canonical
    return None


def _read_text(path: Path) -> str:
    raw = path.read_bytes()
    for encoding in ("utf-8-sig", "utf-8", "gbk", "gb18030"):
        try:
            return raw.decode(encoding)
        except UnicodeDecodeError:
            continue
    return raw.decode("utf-8", errors="ignore")


def _parse_kv_lines(text: str) -> dict[str, str]:
    result: dict[str, str] = {}
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        matched = re.split(r"[,，:=\t]", line, maxsplit=1)
        if len(matched) != 2:
            continue
        canonical = _normalize_key(matched[0])
        value = matched[1].strip().strip('"').strip("'")
        if canonical and value:
            result[canonical] = value
    return result


def _parse_csv_kv(text: str) -> dict[str, str]:
    result: dict[str, str] = {}
    reader = csv.reader(io.StringIO(text))
    rows = [row for row in reader if row and any(cell.strip() for cell in row)]
    if not rows:
        return result

    header = [c.strip().strip("\ufeff") for c in rows[0]]
    # Two-column schema: 字段,值
    if len(header) >= 2 and (
        header[0] in {"字段", "field", "key", "名称"}
        or header[1] in {"值", "value", "内容"}
        or _normalize_key(header[0]) is None
    ):
        start = 1 if header[0] in {"字段", "field", "key", "名称"} or header[1] in {"值", "value", "内容"} else 0
        for row in rows[start:]:
            if len(row) < 2:
                continue
            canonical = _normalize_key(row[0])
            value = (row[1] or "").strip()
            if canonical and value:
                result[canonical] = value
        if result:
            return result

    # Wide header row: document_type,period,... then one data row
    keys = [_normalize_key(h) for h in header]
    if any(keys) and len(rows) >= 2:
        for row in rows[1:]:
            for idx, canonical in enumerate(keys):
                if not canonical or idx >= len(row):
                    continue
                value = (row[idx] or "").strip()
                if value:
                    result[canonical] = value
            if result:
                break
    return result


def parse_file_content(path: Path | str, original_name: str = "") -> dict[str, Any]:
    """Parse uploaded file content into structured fields.

    Returns:
      {
        "ok": bool,
        "source": "content" | "none",
        "engine": str,
        "fields": {field_key: value},
        "confidence": float,
        "summary": str,
      }
    """
    file_path = Path(path)
    name = original_name or file_path.name
    if not file_path.is_file():
        return {
            "ok": False,
            "source": "none",
            "engine": "ESG规则解析器",
            "fields": {},
            "confidence": 0.0,
            "summary": f"未找到可读取文件：{name}",
        }

    ext = file_path.suffix.lower().lstrip(".")
    text = _read_text(file_path)
    fields: dict[str, str] = {}

    if ext in {"csv", "txt", "tsv", "md"}:
        if ext == "csv" or ("," in text.splitlines()[0] if text.splitlines() else False):
            fields = _parse_csv_kv(text)
        if not fields:
            fields = _parse_kv_lines(text)
    else:
        # Best-effort for other text-like uploads
        fields = _parse_kv_lines(text)
        if not fields and ext == "csv":
            fields = _parse_csv_kv(text)

    if not fields:
        return {
            "ok": False,
            "source": "none",
            "engine": "ESG规则解析器",
            "fields": {},
            "confidence": 0.0,
            "summary": f"未能从文件内容识别结构化字段：{name}",
        }

    # Normalize module
    if "esg_module" in fields:
        module = fields["esg_module"].strip().upper()
        if module.startswith("E"):
            fields["esg_module"] = "E"
        elif module.startswith("S"):
            fields["esg_module"] = "S"
        elif module.startswith("G"):
            fields["esg_module"] = "G"

    confidence = min(98.0, 78.0 + 2.0 * len(fields))
    summary_parts = []
    for key in (
        "document_type",
        "period",
        "responsible_unit",
        "project_section",
        "engineering_object",
        "dust_exceed_count",
        "noise_exceed_count",
        "water_protection_issue_count",
        "suggested_kpi_code",
    ):
        if key in fields:
            label = FIELD_LABELS.get(key, key)
            summary_parts.append(f"{label}={fields[key]}")

    return {
        "ok": True,
        "source": "content",
        "engine": "ESG样例文件识别器",
        "fields": fields,
        "confidence": round(confidence, 2),
        "summary": "；".join(summary_parts) if summary_parts else f"已从 {name} 识别 {len(fields)} 个字段",
    }


def field_meta(field_key: str) -> tuple[str, str]:
    """Return (field_name, value_type)."""
    return FIELD_LABELS.get(field_key, field_key), VALUE_TYPES.get(field_key, "string")
