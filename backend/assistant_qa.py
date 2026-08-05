"""ESG 智能助手 · 库驱动问答（问题 → intent → 现有 MySQL API → 回答模板）。"""
from __future__ import annotations

import re
from datetime import datetime
from pathlib import Path
from typing import Any, Callable

import mysql_api

ROOT_DIR = Path(__file__).resolve().parent.parent
PACKS_DIR = ROOT_DIR / "public" / "samples" / "assistant-compliance-packs"
MANIFESTS_DIR = PACKS_DIR / "manifests"

# 默认月报账期（与样例资料包 YYYYMM 对齐）
DEFAULT_REPORT_PERIOD = "2026-07"

REGISTERED_QUESTIONS = [
    {"id": "Q01", "text": "当前有哪些未闭环环保问题？"},
    {"id": "Q02", "text": "当前较大及以上安全风险点有多少？"},
    {"id": "Q03", "text": "项目累计碳排放是多少？"},
    {"id": "Q04", "text": "本月还有哪些月报资料待处理？"},
    {"id": "Q05", "text": "查看E/S/G三类指标总体情况"},
    {"id": "Q07", "text": "当前有哪些逾期整改事项？"},
    {"id": "Q08", "text": "三标段安全风险情况"},
    {"id": "Q09", "text": "环境 E"},
    {"id": "Q10", "text": "社会 S"},
    {"id": "Q11", "text": "治理 G"},
    {"id": "Q12", "text": "碳专题"},
    {"id": "Q13", "text": "月报专题"},
    {"id": "C01", "text": "当前有哪些待补齐的关键合规资料？"},
    {"id": "C02", "text": "未完成报批报建手续还有多少项？"},
    {"id": "C03", "text": "应对上级环保检查应准备哪些合规资料？"},
    {"id": "C04", "text": "上级安全检查常见核查项与现有台账缺口？"},
    {"id": "C05", "text": "请给出本轮上级检查可用的合规资料包"},
]


def _now_str() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def _as_of_label() -> str:
    d = datetime.now()
    return f"{d.year}年{d.month}月{d.day}日"


def _basis(
    item_name: str,
    *,
    scope: str = "罗宜高速项目全线",
    data_period: str | None = None,
    stable_id: str,
    sources: list[dict] | None = None,
    caliber: str,
    update_time: str | None = None,
) -> dict:
    ts = update_time or _now_str()[:16]
    return {
        "itemName": item_name,
        "scope": scope,
        "updateTime": ts,
        "dataPeriod": data_period or f"截至{_as_of_label()}",
        "verifyStatus": "已核验",
        "stableId": stable_id,
        "sources": sources
        or [
            {"name": "业务台账（MySQL）", "time": ts[:10], "status": "已关联"},
            {"name": "首页 KPI 同源口径", "time": ts[:10], "status": "已关联"},
        ],
        "caliber": caliber,
    }


def _empty_message(content: str, *, follow_ups: list[str] | None = None, data_basis: dict | None = None) -> dict:
    msg: dict[str, Any] = {
        "role": "assistant",
        "content": content,
        "followUps": follow_ups
        or [
            "当前有哪些未闭环环保问题？",
            "应对上级环保检查应准备哪些合规资料？",
            "上级安全检查常见核查项与现有台账缺口？",
        ],
    }
    if data_basis:
        msg["dataBasis"] = data_basis
    return msg


def _unwrap_api(payload: Any) -> Any:
    if isinstance(payload, dict) and "data" in payload and "code" in payload:
        return payload.get("data")
    return payload


def _load_manifest(name: str) -> dict | None:
    path = MANIFESTS_DIR / name
    if not path.exists():
        return None
    import json

    return json.loads(path.read_text(encoding="utf-8"))


def _package_card_from_manifest(manifest: dict) -> dict:
    docs = manifest.get("requiredDocs") or []
    files = [
        {
            "name": d.get("name") or "",
            "path": d.get("path") or "",
            "kind": d.get("kind") or "other",
            "sizeHint": d.get("sizeHint"),
        }
        for d in docs
    ]
    stats = dict(manifest.get("stats") or {})
    required_count = int(
        stats.get("requiredFileCount")
        or manifest.get("requiredFileCount")
        or len(files)
        or 0
    )
    card = {
        "packageId": manifest.get("packageId") or "",
        "title": manifest.get("title") or "合规资料包",
        "inspectionType": manifest.get("inspectionType") or "comprehensive",
        "nature": manifest.get("nature") or "sample",
        "files": files,
        "downloadUrl": manifest.get("downloadUrl") or "",
        "requiredCount": required_count,
        "updatedAt": manifest.get("updatedAt") or "",
        "subtitle": manifest.get("subtitle") or "",
    }
    if stats:
        card["stats"] = stats
    return card


def _status_label_e02(status_group: str, status: str) -> str:
    mapping = {
        "rectifying": "整改中",
        "pendingReview": "待复查",
        "pendingClosure": "待销项",
    }
    return mapping.get(status_group) or status or "—"


def _time_status(overdue: bool, deadline: Any) -> str:
    if overdue:
        return "逾期"
    return "正常"


def _e02_homepage_scope() -> str:
    """与首页 E02 KPI / E02 工作台默认 scope 一致（E02_ALLOW_DEMO 闸）。"""
    return "demo" if getattr(mysql_api, "E02_ALLOW_DEMO", False) else "formal"


def _get_e02_issues_aligned() -> dict:
    """拉取与首页同源的未闭环环保问题列表。"""
    return mysql_api.get_e02_issues(_e02_homepage_scope())


def _kpi_card_value(message: dict | None, label: str, default: int = 0) -> int:
    for card in (message or {}).get("kpiCards") or []:
        if card.get("label") == label:
            try:
                return int(card.get("value") or 0)
            except (TypeError, ValueError):
                return default
    return default


def _group_label(code: str | None) -> str:
    return {"E": "环境", "S": "社会", "G": "治理"}.get((code or "").strip().upper(), code or "—")


def _pick_str(*values: Any, fallback: str = "—") -> str:
    for value in values:
        if value is None:
            continue
        text = str(value).strip()
        if text and text != "—":
            return text
    return fallback


# ── Intent builders ──────────────────────────────────────────────


def build_e02_open_issues(_question: str) -> dict:
    raw = _get_e02_issues_aligned()
    data = _unwrap_api(raw) or {}
    overview = data.get("overview") or {}
    issues = data.get("issues") or []
    total = int(overview.get("total") or 0)
    if total == 0 and not issues:
        return _empty_message(
            f"截至{_as_of_label()}，暂无未闭环环保问题。",
            data_basis=_basis(
                "未闭环环保问题",
                stable_id="E02-ENV-ISSUES",
                caliber="未闭环环保问题：已发现但尚未完成整改、复查或销项的环境事项；统计与首页 E02 KPI / E02 工作台同源。",
            ),
        )
    rectifying = int(overview.get("rectifying") or 0)
    pending_review = int(overview.get("pendingReview") or 0)
    pending_closure = int(overview.get("pendingClosure") or 0)
    rows = []
    for i, issue in enumerate(issues[:5], start=1):
        rows.append(
            {
                "index": i,
                "name": issue.get("title") or issue.get("issueType") or "—",
                "segment": _guess_segment(issue.get("locationText") or ""),
                "dept": issue.get("responsibleOrgName") or "—",
                "deadline": issue.get("deadline") or "—",
                "handleStatus": _status_label_e02(issue.get("statusGroup") or "", issue.get("status") or ""),
                "timeStatus": _time_status(bool(issue.get("overdue")), issue.get("deadline")),
                "action": "查看",
            }
        )
    return {
        "role": "assistant",
        "content": (
            f"截至{_as_of_label()}，项目当前共有{total}项未闭环环保问题，"
            f"其中整改中{rectifying}项、待复查{pending_review}项、待销项{pending_closure}项。"
        ),
        "kpiCards": [
            {"label": "未闭环问题总数", "value": total, "unit": "项", "color": "blue"},
            {"label": "整改中", "value": rectifying, "unit": "项", "color": "cyan"},
            {"label": "待复查", "value": pending_review, "unit": "项", "color": "orange"},
            {"label": "待销项", "value": pending_closure, "unit": "项", "color": "red"},
        ],
        "tableData": {
            "title": f"未闭环环保问题清单（前{len(rows)}条）",
            "total": total,
            "columns": [
                {"key": "index", "label": "序号", "width": "6%", "align": "center"},
                {"key": "name", "label": "问题名称", "width": "28%", "align": "left"},
                {"key": "segment", "label": "标段", "width": "10%", "align": "center"},
                {"key": "dept", "label": "责任部门", "width": "14%", "align": "left"},
                {"key": "deadline", "label": "截止日期", "width": "14%", "align": "center"},
                {"key": "handleStatus", "label": "办理状态", "width": "10%", "align": "center"},
                {"key": "timeStatus", "label": "时限状态", "width": "10%", "align": "center"},
                {"key": "action", "label": "关联页面", "width": "8%", "align": "center"},
            ],
            "rows": rows,
            "viewAllText": f"查看全部{total}项" if total > len(rows) else None,
        },
        "dataBasis": _basis(
            "未闭环环保问题",
            stable_id="E02-ENV-ISSUES",
            caliber="未闭环环保问题，是指已发现但尚未完成整改、复查或销项的环境环保事项。统计与首页 E02 KPI / E02 工作台同源。",
            sources=[
                {"name": "env_issue_record", "time": _now_str()[:10], "status": "已关联"},
                {"name": "首页 E02 KPI", "time": _now_str()[:10], "status": "已关联"},
                {"name": "E02 工作台", "time": _now_str()[:10], "status": "已关联"},
            ],
        ),
        "followUps": ["查看逾期事项", "按责任部门统计", "查看三标段问题", "导出问题清单"],
    }


def _guess_segment(location: str) -> str:
    for key in ("一标段", "二标段", "三标段", "四标段"):
        if key in (location or ""):
            return key
    return "—"


def build_s02_active_major(_question: str) -> dict:
    raw = mysql_api.get_s02_risks()
    data = _unwrap_api(raw) or {}
    overview = data.get("overview") or {}
    risks = data.get("risks") or []
    total = int(overview.get("total") or len(risks) or 0)
    if total == 0:
        return _empty_message(
            f"截至{_as_of_label()}，暂无较大及以上在管安全风险点。",
            data_basis=_basis(
                "较大及以上安全风险点",
                stable_id="S02-SAFETY-RISKS",
                caliber="较大及以上在管风险：风险等级为重大/较大且未销号的安全风险点，与 S02 工作台同源。",
            ),
        )
    major = int(overview.get("major") or 0)
    larger = int(overview.get("larger") or 0)
    rows = []
    for i, risk in enumerate(risks[:5], start=1):
        rows.append(
            {
                "index": i,
                "name": risk.get("title") or "—",
                "level": risk.get("riskLevel") or "—",
                "type": risk.get("riskType") or "—",
                "location": risk.get("locationText") or "—",
                "status": risk.get("status") or "—",
            }
        )
    return {
        "role": "assistant",
        "content": (
            f"截至{_as_of_label()}，项目在管较大及以上安全风险点共{total}处，"
            f"其中重大{major}处、较大{larger}处。"
        ),
        "kpiCards": [
            {"label": "在管较大及以上", "value": total, "unit": "处", "color": "orange"},
            {"label": "重大", "value": major, "unit": "处", "color": "red"},
            {"label": "较大", "value": larger, "unit": "处", "color": "orange"},
            {"label": "本月新增", "value": int(overview.get("newThisMonth") or 0), "unit": "处", "color": "cyan"},
        ],
        "tableData": {
            "title": f"在管安全风险点（前{len(rows)}条）",
            "total": total,
            "columns": [
                {"key": "index", "label": "序号", "width": "8%", "align": "center"},
                {"key": "name", "label": "风险点名称", "width": "28%", "align": "left"},
                {"key": "level", "label": "等级", "width": "10%", "align": "center"},
                {"key": "type", "label": "类型", "width": "14%", "align": "left"},
                {"key": "location", "label": "位置", "width": "24%", "align": "left"},
                {"key": "status", "label": "管控状态", "width": "16%", "align": "center"},
            ],
            "rows": rows,
            "viewAllText": f"查看全部{total}处" if total > len(rows) else None,
        },
        "dataBasis": _basis(
            "较大及以上安全风险点",
            stable_id="S02-SAFETY-RISKS",
            caliber="较大及以上在管风险统计与 S02 安全风险点工作台同源。",
        ),
        "followUps": ["三标段安全风险情况", "上级安全检查常见核查项与现有台账缺口？", "当前有哪些逾期整改事项？"],
    }


def build_e04_carbon(_question: str) -> dict:
    kpis = mysql_api.get_dashboard_kpis() or {}
    e04_value = None
    e04_unit = "tCO₂e"
    for group in kpis.get("groups") or []:
        for item in group.get("items") or []:
            if item.get("key") == "E04":
                e04_value = item.get("value")
                e04_unit = item.get("unit") or e04_unit
                break
    detail = mysql_api.get_dashboard_kpi_detail("E04")
    if e04_value is None and detail:
        for s in detail.get("summary") or []:
            if "累计" in str(s.get("label") or "") or s.get("unit") in ("tCO₂e", "tCO2e"):
                e04_value = s.get("value")
                e04_unit = s.get("unit") or e04_unit
                break
    if e04_value is None:
        return _empty_message(
            "暂无可用的项目累计碳排放数据。",
            data_basis=_basis("项目累计碳排放", stable_id="E04-CARBON", caliber="与首页 E04 KPI 同源。"),
        )
    cards = [{"label": "项目累计碳排放", "value": e04_value, "unit": e04_unit, "color": "cyan"}]
    if detail:
        for s in (detail.get("summary") or [])[:3]:
            if s.get("label") and s.get("value") is not None and s.get("label") != "项目累计碳排放":
                cards.append(
                    {
                        "label": s["label"],
                        "value": s["value"],
                        "unit": s.get("unit") or "",
                        "color": "blue",
                    }
                )
    return {
        "role": "assistant",
        "content": f"截至{_as_of_label()}，项目累计碳排放为 {e04_value} {e04_unit}（与首页 E04 口径一致）。",
        "kpiCards": cards[:4],
        "dataBasis": _basis(
            "项目累计碳排放",
            stable_id="E04-CARBON",
            caliber="累计碳排放取自正式库已核验活动汇总，与首页 E04 KPI 同源。",
        ),
        "followUps": ["查看E/S/G三类指标总体情况", "碳专题", "本月还有哪些月报资料待处理？"],
    }


def build_monthly_pending(_question: str) -> dict:
    try:
        import monthly_report_overview

        overview = monthly_report_overview.get_monthly_report_overview(DEFAULT_REPORT_PERIOD)
    except Exception:
        overview = None
    if overview is None:
        try:
            import monthly_report_readiness

            overview = monthly_report_readiness.get_monthly_report_readiness(DEFAULT_REPORT_PERIOD)
        except Exception:
            overview = None
    if not overview:
        return _empty_message(
            f"{DEFAULT_REPORT_PERIOD} 月报资料归集数据暂不可用。",
            follow_ups=["查看E/S/G三类指标总体情况", "当前有哪些未闭环环保问题？"],
        )

    pending = 0
    tasks: list[dict] = []
    owner_by_id: dict[str, str] = {}
    if isinstance(overview, dict):
        # overview：taskInstances 含责任人；pendingTasks 为待办摘要（字段名不同）
        for ti in overview.get("taskInstances") or []:
            tid = str(ti.get("id") or "")
            if not tid:
                continue
            owner_by_id[tid] = _pick_str(
                ti.get("responsibleUserName"),
                ti.get("responsibleDepartment"),
                ti.get("responsibleRole"),
                ti.get("responsibleUnit"),
                fallback="",
            )

        summary = overview.get("summary") or overview.get("overview") or {}
        if isinstance(summary, dict):
            pending = int(
                summary.get("pendingTotal")
                or summary.get("pendingCount")
                or summary.get("pending")
                or summary.get("todoCount")
                or summary.get("待处理")
                or 0
            )
            if not pending:
                pending = int(summary.get("pendingSubmitCount") or 0) + int(
                    summary.get("pendingConfirmCount") or 0
                ) + int(summary.get("pendingCorrectionCount") or 0)

        tasks = list(
            overview.get("pendingTasks")
            or overview.get("tasks")
            or overview.get("items")
            or overview.get("materials")
            or []
        )

        # readiness 形态：exceptionTasks
        exception_tasks = overview.get("exceptionTasks") or []
        if not tasks and exception_tasks:
            tasks = list(exception_tasks)
            if not pending:
                pending = len(exception_tasks)

        if not pending and isinstance(tasks, list):
            pending = len(
                [
                    t
                    for t in tasks
                    if (t.get("status") or t.get("monthlyStatus") or "")
                    not in ("已完成", "已提交", "校验通过", "不适用", "不适用（已确认）", "done")
                ]
            )

        modules = overview.get("modules") or overview.get("categories") or []
        if not pending and modules:
            for m in modules:
                pending += int(m.get("pendingCount") or m.get("pending") or 0)
            if not tasks:
                for m in modules:
                    for t in m.get("items") or m.get("tasks") or []:
                        tasks.append({**t, "module": m.get("name") or m.get("label") or ""})

        # 若仅有 pending 计数而无摘要行，从 taskInstances 回填待办
        if pending and not tasks:
            tasks = [
                t
                for t in (overview.get("taskInstances") or [])
                if (t.get("status") or "") in {"待提交", "待确认", "待补正"}
                or bool(t.get("affectsReport"))
            ]

    if pending == 0 and not tasks:
        return _empty_message(
            f"本月（{DEFAULT_REPORT_PERIOD}）暂无待处理月报资料。",
            data_basis=_basis("月报资料待处理", stable_id="MONTHLY-PENDING", caliber="月报归集就绪度与月报专题同源。"),
        )

    rows = []
    for i, task in enumerate(list(tasks)[:8], start=1):
        tid = str(task.get("id") or "")
        group = task.get("groupCode") or task.get("module") or task.get("category") or ""
        rows.append(
            {
                "index": i,
                "name": _pick_str(
                    task.get("taskName"),
                    task.get("name"),
                    task.get("title"),
                    task.get("materialName"),
                    task.get("requiredMaterialName"),
                ),
                "module": _group_label(str(group)) if group in {"E", "S", "G", "e", "s", "g"} else _pick_str(group),
                "status": _pick_str(task.get("status"), task.get("monthlyStatus"), task.get("state"), fallback="待处理"),
                "owner": _pick_str(
                    owner_by_id.get(tid),
                    task.get("responsibleUserName"),
                    task.get("responsibleDepartment"),
                    task.get("responsibleUnit"),
                    task.get("responsibleRole"),
                    task.get("owner"),
                    task.get("assignee"),
                    task.get("responsible"),
                ),
            }
        )

    # 禁止空壳表：若关键字段仍全空，不展示表
    solid_rows = [r for r in rows if r["name"] != "—" or r["owner"] != "—"]
    table = None
    if solid_rows:
        table = {
            "title": "月报待处理清单（摘要）",
            "total": pending or len(solid_rows),
            "columns": [
                {"key": "index", "label": "序号", "width": "8%", "align": "center"},
                {"key": "name", "label": "资料名称", "width": "34%", "align": "left"},
                {"key": "module", "label": "板块", "width": "12%", "align": "center"},
                {"key": "status", "label": "状态", "width": "16%", "align": "center"},
                {"key": "owner", "label": "责任人", "width": "30%", "align": "left"},
            ],
            "rows": solid_rows,
        }

    return {
        "role": "assistant",
        "content": f"本月（{DEFAULT_REPORT_PERIOD}）尚有 {pending or len(solid_rows)} 项月报资料待处理。",
        "kpiCards": [
            {"label": "待处理资料", "value": pending or len(solid_rows), "unit": "项", "color": "orange"},
            {"label": "账期", "value": DEFAULT_REPORT_PERIOD, "unit": "", "color": "blue"},
        ],
        "tableData": table,
        "dataBasis": _basis(
            "月报资料待处理",
            stable_id="MONTHLY-PENDING",
            data_period=DEFAULT_REPORT_PERIOD,
            caliber="月报待处理统计与月报专题 overview / readiness 接口同源；资料名称取 taskName，板块取 E/S/G，责任人取责任人/责任部门。",
        ),
        "followUps": ["月报专题", "当前有哪些待补齐的关键合规资料？", "查看E/S/G三类指标总体情况"],
    }


def build_kpi_esg_overview(_question: str) -> dict:
    kpis = mysql_api.get_dashboard_kpis() or {}
    groups = kpis.get("groups") or []
    if not groups:
        return _empty_message("暂无 E/S/G 指标数据。")
    cards = []
    lines = []
    color_map = {"E": "green", "S": "blue", "G": "purple"}
    for group in groups:
        key = group.get("key") or ""
        items = group.get("items") or []
        lines.append(f"{group.get('title') or key}：{len(items)} 项指标")
        for item in items[:2]:
            cards.append(
                {
                    "label": item.get("label") or item.get("key") or "—",
                    "value": item.get("value") if item.get("value") is not None else "—",
                    "unit": item.get("unit") or "",
                    "color": color_map.get(key, "blue"),
                }
            )
    return {
        "role": "assistant",
        "content": f"截至{_as_of_label()}，E/S/G 三类指标总体情况如下。" + (" " + "；".join(lines) if lines else ""),
        "kpiCards": cards[:8] if len(cards) <= 8 else cards[:4],
        "dataBasis": _basis(
            "E/S/G 指标总览",
            stable_id="KPI-ESG-OVERVIEW",
            caliber="指标值取自 indicator_result / 首页 KPI 同源接口。",
        ),
        "followUps": ["环境 E", "社会 S", "治理 G", "碳专题"],
    }


def build_overdue(_question: str) -> dict:
    raw = _get_e02_issues_aligned()
    data = _unwrap_api(raw) or {}
    issues = [i for i in (data.get("issues") or []) if i.get("overdue")]
    total = len(issues)
    if total == 0:
        return _empty_message(
            f"截至{_as_of_label()}，暂无逾期整改事项（与首页 E02 同源）。",
            data_basis=_basis("逾期整改事项", stable_id="CROSS-OVERDUE", caliber="当前以 E02 同源台账逾期筛选为准。"),
        )
    rows = []
    for i, issue in enumerate(issues[:5], start=1):
        rows.append(
            {
                "index": i,
                "name": issue.get("title") or "—",
                "dept": issue.get("responsibleOrgName") or "—",
                "deadline": issue.get("deadline") or "—",
                "status": _status_label_e02(issue.get("statusGroup") or "", issue.get("status") or ""),
            }
        )
    return {
        "role": "assistant",
        "content": f"截至{_as_of_label()}，共有 {total} 项逾期整改事项（与首页 E02 同源）。",
        "kpiCards": [{"label": "逾期事项", "value": total, "unit": "项", "color": "red"}],
        "tableData": {
            "title": "逾期整改事项（前5条）",
            "total": total,
            "columns": [
                {"key": "index", "label": "序号", "width": "8%", "align": "center"},
                {"key": "name", "label": "事项名称", "width": "40%", "align": "left"},
                {"key": "dept", "label": "责任部门", "width": "20%", "align": "left"},
                {"key": "deadline", "label": "截止日期", "width": "16%", "align": "center"},
                {"key": "status", "label": "状态", "width": "16%", "align": "center"},
            ],
            "rows": rows,
        },
        "dataBasis": _basis("逾期整改事项", stable_id="CROSS-OVERDUE", caliber="以首页同源 E02 台账 overdue 标记筛选。"),
        "followUps": ["当前有哪些未闭环环保问题？", "按责任部门统计", "导出问题清单"],
    }


def build_s02_segment3(_question: str) -> dict:
    raw = mysql_api.get_s02_risks()
    data = _unwrap_api(raw) or {}
    risks = [
        r
        for r in (data.get("risks") or [])
        if "三标段" in (r.get("locationText") or "") or "三标" in (r.get("locationText") or "")
    ]
    total = len(risks)
    if total == 0:
        return _empty_message(
            "三标段暂无较大及以上在管安全风险点。",
            data_basis=_basis("三标段安全风险", stable_id="S02-SEG3", caliber="S02 风险点按位置文本过滤三标段。"),
        )
    rows = [
        {
            "index": i,
            "name": r.get("title") or "—",
            "level": r.get("riskLevel") or "—",
            "location": r.get("locationText") or "—",
            "status": r.get("status") or "—",
        }
        for i, r in enumerate(risks[:5], start=1)
    ]
    return {
        "role": "assistant",
        "content": f"三标段当前在管较大及以上安全风险点共 {total} 处。",
        "kpiCards": [{"label": "三标段在管风险", "value": total, "unit": "处", "color": "orange"}],
        "tableData": {
            "title": "三标段安全风险点",
            "total": total,
            "columns": [
                {"key": "index", "label": "序号", "width": "8%", "align": "center"},
                {"key": "name", "label": "风险点", "width": "32%", "align": "left"},
                {"key": "level", "label": "等级", "width": "12%", "align": "center"},
                {"key": "location", "label": "位置", "width": "30%", "align": "left"},
                {"key": "status", "label": "状态", "width": "18%", "align": "center"},
            ],
            "rows": rows,
        },
        "dataBasis": _basis("三标段安全风险", stable_id="S02-SEG3", caliber="S02 工作台数据按三标段位置过滤。"),
        "followUps": ["当前较大及以上安全风险点有多少？", "上级安全检查常见核查项与现有台账缺口？"],
    }


def build_kpi_group(group_key: str, title: str) -> Callable[[str], dict]:
    def _builder(_question: str) -> dict:
        kpis = mysql_api.get_dashboard_kpis() or {}
        group = next((g for g in (kpis.get("groups") or []) if g.get("key") == group_key), None)
        if not group:
            return _empty_message(f"暂无{title}指标数据。")
        items = group.get("items") or []
        cards = [
            {
                "label": it.get("label") or it.get("key") or "—",
                "value": it.get("value") if it.get("value") is not None else "—",
                "unit": it.get("unit") or "",
                "color": {"E": "green", "S": "blue", "G": "purple"}.get(group_key, "blue"),
            }
            for it in items
        ]
        follow = {
            "E": ["当前有哪些未闭环环保问题？", "项目累计碳排放是多少？", "应对上级环保检查应准备哪些合规资料？"],
            "S": ["当前较大及以上安全风险点有多少？", "三标段安全风险情况", "上级安全检查常见核查项与现有台账缺口？"],
            "G": [
                "当前有哪些待补齐的关键合规资料？",
                "未完成报批报建手续还有多少项？",
                "请给出本轮上级检查可用的合规资料包",
            ],
        }.get(group_key, [])
        return {
            "role": "assistant",
            "content": f"{title}当前共有 {len(items)} 项指标（与首页 KPI 同源）。",
            "kpiCards": cards[:4],
            "dataBasis": _basis(f"{title}指标", stable_id=f"KPI-GROUP-{group_key}", caliber="与首页 KPI 分组同源。"),
            "followUps": follow,
        }

    return _builder


def build_carbon_topic(_question: str) -> dict:
    topic = mysql_api.get_dashboard_topic("carbon")
    if not topic:
        return build_e04_carbon(_question)
    summary = topic.get("summary") or []
    cards = [
        {
            "label": s.get("label") or "—",
            "value": s.get("value") if s.get("value") is not None else "—",
            "unit": s.get("unit") or "",
            "color": "cyan",
        }
        for s in summary[:4]
    ]
    title = topic.get("title") or topic.get("fullName") or "碳专题"
    return {
        "role": "assistant",
        "content": f"以下为「{title}」摘要（与碳专题接口同源）。",
        "kpiCards": cards or None,
        "dataBasis": _basis("碳专题", stable_id="TOPIC-CARBON", caliber="取自 /api/dashboard/topics/carbon 同源数据。"),
        "followUps": ["项目累计碳排放是多少？", "查看E/S/G三类指标总体情况"],
    }


def build_monthly_topic(_question: str) -> dict:
    topic = mysql_api.get_dashboard_topic("monthly-report")
    if not topic:
        return build_monthly_pending(_question)
    summary = topic.get("summary") or []
    cards = [
        {
            "label": s.get("label") or "—",
            "value": s.get("value") if s.get("value") is not None else "—",
            "unit": s.get("unit") or "",
            "color": "orange",
        }
        for s in summary[:4]
    ]
    return {
        "role": "assistant",
        "content": "以下为本月月报专题摘要（与月报专题接口同源）。",
        "kpiCards": cards or None,
        "dataBasis": _basis("月报专题", stable_id="TOPIC-MONTHLY", caliber="取自月报专题快照。"),
        "followUps": ["本月还有哪些月报资料待处理？", "当前有哪些待补齐的关键合规资料？"],
    }


def build_e02_by_department(_question: str) -> dict:
    raw = _get_e02_issues_aligned()
    data = _unwrap_api(raw) or {}
    issues = data.get("issues") or []
    counts: dict[str, int] = {}
    for issue in issues:
        dept = issue.get("responsibleOrgName") or "未指定"
        counts[dept] = counts.get(dept, 0) + 1
    if not counts:
        return _empty_message("暂无按责任部门可统计的未闭环环保问题。")
    rows = [
        {"index": i, "dept": dept, "count": count}
        for i, (dept, count) in enumerate(sorted(counts.items(), key=lambda x: -x[1]), start=1)
    ]
    return {
        "role": "assistant",
        "content": f"未闭环环保问题按责任部门统计共 {len(rows)} 个责任主体、合计 {len(issues)} 项。",
        "tableData": {
            "title": "按责任部门统计",
            "total": len(rows),
            "columns": [
                {"key": "index", "label": "序号", "width": "10%", "align": "center"},
                {"key": "dept", "label": "责任部门", "width": "60%", "align": "left"},
                {"key": "count", "label": "件数", "width": "30%", "align": "center"},
            ],
            "rows": rows[:10],
        },
        "dataBasis": _basis("按责任部门统计", stable_id="E02-BY-DEPT", caliber="与首页同源的 E02 台账按 responsibleOrgName 聚合。"),
        "followUps": ["当前有哪些未闭环环保问题？", "查看逾期事项", "查看三标段问题"],
    }


def build_e02_segment3(_question: str) -> dict:
    raw = _get_e02_issues_aligned()
    data = _unwrap_api(raw) or {}
    issues = [
        i
        for i in (data.get("issues") or [])
        if "三标段" in (i.get("locationText") or "") or "三标" in (i.get("locationText") or "")
    ]
    if not issues:
        return _empty_message("三标段暂无未闭环环保问题。")
    rows = [
        {
            "index": i,
            "name": issue.get("title") or "—",
            "status": _status_label_e02(issue.get("statusGroup") or "", issue.get("status") or ""),
            "deadline": issue.get("deadline") or "—",
        }
        for i, issue in enumerate(issues[:5], start=1)
    ]
    return {
        "role": "assistant",
        "content": f"三标段当前共有 {len(issues)} 项未闭环环保问题。",
        "tableData": {
            "title": "三标段未闭环环保问题",
            "total": len(issues),
            "columns": [
                {"key": "index", "label": "序号", "width": "8%", "align": "center"},
                {"key": "name", "label": "问题名称", "width": "50%", "align": "left"},
                {"key": "status", "label": "状态", "width": "20%", "align": "center"},
                {"key": "deadline", "label": "截止日期", "width": "22%", "align": "center"},
            ],
            "rows": rows,
        },
        "dataBasis": _basis("三标段环保问题", stable_id="E02-SEG3", caliber="与首页同源的 E02 台账按位置过滤三标段。"),
        "followUps": ["当前有哪些未闭环环保问题？", "查看逾期事项"],
    }


def build_e02_export_hint(_question: str) -> dict:
    return {
        "role": "assistant",
        "content": "问题清单导出请前往「环保问题工作台（E02）」使用导出功能。您可打开工作台查看完整清单并导出。",
        "followUps": ["当前有哪些未闭环环保问题？", "查看逾期事项", "按责任部门统计"],
        "dataBasis": _basis(
            "导出问题清单",
            stable_id="E02-EXPORT-HINT",
            caliber="助手侧不生成文件；引导至 E02 工作台导出。",
        ),
    }


def build_g04_gaps(_question: str) -> dict:
    detail = mysql_api.get_g04_material_gap_detail()
    if not detail:
        return _empty_message(
            "暂无待补齐关键合规资料。",
            data_basis=_basis("关键合规资料缺口", stable_id="G04-GAPS", caliber="与 G04 KPI 详情同源。"),
        )
    summary = {s.get("label"): s for s in (detail.get("summary") or [])}
    pending = int((summary.get("待补齐资料") or {}).get("value") or len(detail.get("detailData") or []))
    overdue = int((summary.get("逾期未提交") or {}).get("value") or 0)
    rows = [
        {
            "index": i,
            "name": row.get("name") or "—",
            "module": row.get("module") or "—",
            "deadline": row.get("deadline") or "—",
            "owner": row.get("owner") or "—",
            "status": row.get("status") or "—",
        }
        for i, row in enumerate((detail.get("detailData") or [])[:5], start=1)
    ]
    return {
        "role": "assistant",
        "content": f"截至{_as_of_label()}，待补齐关键合规资料共 {pending} 项，其中逾期未提交 {overdue} 项。",
        "kpiCards": [
            {"label": "待补齐资料", "value": pending, "unit": "项", "color": "orange"},
            {"label": "逾期未提交", "value": overdue, "unit": "项", "color": "red"},
        ],
        "tableData": {
            "title": "待补齐关键合规资料（前5条）",
            "total": pending,
            "columns": [
                {"key": "index", "label": "序号", "width": "8%", "align": "center"},
                {"key": "name", "label": "资料名称", "width": "32%", "align": "left"},
                {"key": "module", "label": "模块", "width": "12%", "align": "center"},
                {"key": "deadline", "label": "截止日期", "width": "16%", "align": "center"},
                {"key": "owner", "label": "责任单位", "width": "18%", "align": "left"},
                {"key": "status", "label": "状态", "width": "14%", "align": "center"},
            ],
            "rows": rows,
        },
        "dataBasis": _basis(
            "关键合规资料缺口",
            stable_id="G04-GAPS",
            caliber="与 G04 关键合规资料台账 / KPI 详情同源。",
            update_time=detail.get("updateTime"),
        ),
        "followUps": ["未完成报批报建手续还有多少项？", "请给出本轮上级检查可用的合规资料包"],
    }


def build_g01_procedures(_question: str) -> dict:
    detail = mysql_api.get_g01_compliance_procedure_detail()
    if not detail:
        return _empty_message(
            "暂无未完成报批报建手续。",
            data_basis=_basis("报批报建手续", stable_id="G01-PROC", caliber="与 G01 KPI 详情同源。"),
        )
    summary = {s.get("label"): s for s in (detail.get("summary") or [])}
    open_count = int((summary.get("未完成事项") or {}).get("value") or len(detail.get("detailData") or []))
    overdue = int((summary.get("逾期未办") or {}).get("value") or 0)
    rows = [
        {
            "index": i,
            "name": row.get("name") or "—",
            "type": row.get("type") or "—",
            "status": row.get("status") or "—",
            "deadline": row.get("deadline") or "—",
            "department": row.get("department") or "—",
        }
        for i, row in enumerate((detail.get("detailData") or [])[:5], start=1)
    ]
    return {
        "role": "assistant",
        "content": f"截至{_as_of_label()}，未完成报批报建手续共 {open_count} 项，其中逾期未办 {overdue} 项。",
        "kpiCards": [
            {"label": "未完成事项", "value": open_count, "unit": "项", "color": "purple"},
            {"label": "逾期未办", "value": overdue, "unit": "项", "color": "red"},
        ],
        "tableData": {
            "title": "未完成报批报建手续（前5条）",
            "total": open_count,
            "columns": [
                {"key": "index", "label": "序号", "width": "8%", "align": "center"},
                {"key": "name", "label": "手续名称", "width": "32%", "align": "left"},
                {"key": "type", "label": "类型", "width": "14%", "align": "left"},
                {"key": "status", "label": "状态", "width": "14%", "align": "center"},
                {"key": "deadline", "label": "截止日期", "width": "16%", "align": "center"},
                {"key": "department", "label": "责任部门", "width": "16%", "align": "left"},
            ],
            "rows": rows,
        },
        "dataBasis": _basis(
            "报批报建手续",
            stable_id="G01-PROC",
            caliber="与 G01 法定报批报建台账 / KPI 详情同源。",
            update_time=detail.get("updateTime"),
        ),
        "followUps": ["当前有哪些待补齐的关键合规资料？", "请给出本轮上级检查可用的合规资料包"],
    }


def _safe_call(builder: Callable[[], Any], default: Any = None) -> Any:
    try:
        return builder()
    except Exception as exc:
        print(f"[assistant_qa] builder failed: {exc}")
        return default


def _g04_gap_items() -> tuple[int, list[dict]]:
    detail = _safe_call(mysql_api.get_g04_material_gap_detail, None)
    if not detail:
        return 0, []
    summary = {s.get("label"): s for s in (detail.get("summary") or [])}
    total = int((summary.get("待补齐资料") or {}).get("value") or len(detail.get("detailData") or []))
    return total, list(detail.get("detailData") or [])


def _e02_open_total() -> int:
    raw = _safe_call(_get_e02_issues_aligned, {})
    data = _unwrap_api(raw) or {}
    return int((data.get("overview") or {}).get("total") or 0)


def _e02_closure_stats() -> dict:
    """历史问题闭环率：已闭环 /（未闭环+已闭环），与首页 E02 scope 同源。"""
    open_count = _e02_open_total()
    closed_count = 0
    try:
        scope = _e02_homepage_scope()
        scope_sql, scope_params = mysql_api._e02_scope_clause(scope)
        row = mysql_api.query_one(
            f"SELECT COUNT(*) AS c FROM env_issue_record WHERE issue_status='已闭环' {scope_sql}",
            scope_params,
        )
        closed_count = int((row or {}).get("c") or 0)
    except Exception:
        closed_count = 0
    historical = open_count + closed_count
    return {
        "openIssueCount": open_count,
        "closedCount": closed_count,
        "historicalTotal": historical,
        "closureRate": f"{closed_count}/{historical}" if historical else "0/0",
    }


def _env_pack_inventory(manifest: dict | None = None) -> tuple[dict, list[dict], list[dict]]:
    """读取环保资料包 manifest：stats / 11 类表行 / 待补齐文件。"""
    manifest = manifest or _load_manifest("pack_superior_env.json") or {}
    stats = {
        "categoryCount": int((manifest.get("stats") or {}).get("categoryCount") or 11),
        "requiredFileCount": int((manifest.get("stats") or {}).get("requiredFileCount") or 0),
        "collectedCount": int((manifest.get("stats") or {}).get("collectedCount") or 0),
        "pendingCount": int((manifest.get("stats") or {}).get("pendingCount") or 0),
    }
    categories = list(manifest.get("categories") or [])
    if not categories:
        # 兜底：与用户标准目录一致的空壳 11 类
        fallback_names = [
            "01_审批文件与环评批复落实",
            "02_环保组织机构与管理制度",
            "03_施工环保方案及交底培训",
            "04_日常巡查与污染防治设施运行",
            "05_施工期环境监测",
            "06_环保监理检查",
            "07_环保问题整改与闭环",
            "08_固废危废及应急管理",
            "09_生态保护与水土保持",
            "10_环保月报及阶段总结",
            "11_上级检查、投诉及处罚整改",
        ]
        categories = [
            {
                "id": f"{i:02d}",
                "name": name,
                "requiredFileCount": 0,
                "collectedCount": 0,
                "pendingCount": 0,
                "note": "",
            }
            for i, name in enumerate(fallback_names, start=1)
        ]
        stats["categoryCount"] = 11

    rows = []
    for i, cat in enumerate(categories, start=1):
        name = str(cat.get("name") or "")
        # 表内类别列展示去编号前缀，便于阅读
        label = name.split("_", 1)[-1] if "_" in name else name
        rows.append(
            {
                "index": i,
                "category": label,
                "required": int(cat.get("requiredFileCount") or 0),
                "collected": int(cat.get("collectedCount") or 0),
                "pending": int(cat.get("pendingCount") or 0),
                "note": cat.get("note") or "",
            }
        )

    pending_files = [
        item
        for item in (manifest.get("inventory") or [])
        if str(item.get("status") or "") == "pending"
    ]
    if not stats["requiredFileCount"] and categories:
        stats["requiredFileCount"] = sum(int(c.get("requiredFileCount") or 0) for c in categories)
        stats["collectedCount"] = sum(int(c.get("collectedCount") or 0) for c in categories)
        stats["pendingCount"] = sum(int(c.get("pendingCount") or 0) for c in categories)

    return stats, rows, pending_files


def _build_env_prep_rows(g04_items: list[dict], e02_total: int) -> list[dict]:
    """兼容旧调用：改为返回 11 类汇总行（忽略稀疏 4 项应备清单）。"""
    _stats, rows, _pending = _env_pack_inventory()
    # 07 类说明可追加当前未闭环数
    for row in rows:
        if "问题整改" in str(row.get("category") or "") and e02_total:
            base = row.get("note") or ""
            row["note"] = f"{base}；当前未闭环 {e02_total} 项".strip("；")
        if "环境监测" in str(row.get("category") or "") and g04_items:
            env_gap = next(
                (
                    i
                    for i in g04_items
                    if "环境监测" in str(i.get("name") or "")
                ),
                None,
            )
            if env_gap and int(row.get("pending") or 0) > 0:
                row["note"] = f"{row.get('note') or ''}（含 G04 缺口「{env_gap.get('name')}」）".strip()
    return rows


def _build_safety_prep_rows(s02_total: int, g04_items: list[dict]) -> list[dict]:
    safety_gaps = [
        i
        for i in g04_items
        if str(i.get("module") or "").upper() in {"S", "社会"}
        or any(k in str(i.get("name") or "") for k in ("安全", "应急", "风险"))
    ]
    rows_spec = [
        {
            "name": "较大及以上在管安全风险台账",
            "category": "风险台账",
            "point": "风险点名称、等级、位置、管控状态与责任人",
            "status": f"库内在管 {s02_total} 处" if s02_total else "当前无在管较大及以上风险",
        },
        {
            "name": "风险管控与销号闭环材料",
            "category": "闭环材料",
            "point": "管控措施、整改期限、销号证据与现场照片",
            "status": "建议对照工作台逐条核验",
        },
        {
            "name": "上级安全检查核查项与台账缺口说明",
            "category": "核查表",
            "point": "检查组常见核查项与现有台账缺口对照",
            "status": "已纳入资料包",
        },
    ]
    known = {r["name"] for r in rows_spec}
    for item in safety_gaps:
        name = str(item.get("name") or "").strip()
        if not name or name in known:
            continue
        rows_spec.append(
            {
                "name": name,
                "category": "关键合规资料",
                "point": f"责任单位：{item.get('owner') or '—'}；截止：{item.get('deadline') or '—'}",
                "status": f"待补齐 · {item.get('status') or '缺口'}",
            }
        )
        known.add(name)
    return [
        {
            "index": i,
            "name": row["name"],
            "category": row["category"],
            "point": row["point"],
            "status": row["status"],
        }
        for i, row in enumerate(rows_spec, start=1)
    ]


def build_pack_superior_env(_question: str) -> dict:
    closure = _e02_closure_stats()
    e02_total = int(closure.get("openIssueCount") or 0)
    _g04_total, g04_items = _g04_gap_items()

    manifest = _load_manifest("pack_superior_env.json") or {
        "packageId": "PACK-SUPERIOR-ENV-202607",
        "title": "上级环保检查 · 合规资料包",
        "inspectionType": "env",
        "nature": "sample",
        "downloadUrl": "/samples/assistant-compliance-packs/上级检查_环保合规资料包_202607.zip",
        "updatedAt": "2026-07-27",
        "subtitle": "合规资料包 · 2026年7月账期",
        "stats": {
            "categoryCount": 11,
            "requiredFileCount": 0,
            "collectedCount": 0,
            "pendingCount": 0,
        },
    }
    stats, prep_rows, pending_files = _env_pack_inventory(manifest)
    stats = {
        **stats,
        "openIssueCount": e02_total,
        "closureRate": closure.get("closureRate") or "0/0",
        "closedCount": int(closure.get("closedCount") or 0),
        "historicalTotal": int(closure.get("historicalTotal") or 0),
    }
    # 将运行时 E02 统计写回 packageCard.stats
    manifest = {**manifest, "stats": {**(manifest.get("stats") or {}), **stats}}
    package_card = _package_card_from_manifest(manifest)
    package_card["stats"] = stats
    package_card["requiredCount"] = int(stats.get("requiredFileCount") or package_card.get("requiredCount") or 0)

    # 强化 07 类说明中的未闭环数
    prep_rows = _build_env_prep_rows(g04_items, e02_total)

    pending_names = [str(p.get("name") or "") for p in pending_files if p.get("name")]
    pending_hint = ""
    if pending_names:
        pending_hint = f"待补齐文件主要包括：{'、'.join(pending_names[:4])}。"
    elif _g04_total:
        pending_hint = f"关键合规资料台账（G04）另有 {_g04_total} 项缺口，其中可归入本包目录者已映射为「待补齐」。"

    return {
        "role": "assistant",
        "content": (
            f"应对上级环保检查，应按「审批要求→现场实施→监测检查→问题整改→复查销项」证据链备齐 11 类合规资料。"
            f"本项目资料包共应备 {stats['requiredFileCount']} 项具体文件，已归集 {stats['collectedCount']} 项，待补齐 {stats['pendingCount']} 项；"
            f"当前未闭环环保问题 {e02_total} 项（与首页 E02 同源），历史问题闭环率 {stats['closureRate']}。"
            f"{pending_hint}"
            f"同条回复已附「上级环保检查 · 合规资料包」，可直接下载。"
        ),
        "kpiCards": [
            {"label": "应备资料类别", "value": stats["categoryCount"], "unit": "类", "color": "green"},
            {"label": "应备具体文件", "value": stats["requiredFileCount"], "unit": "项", "color": "cyan"},
            {"label": "已归集", "value": stats["collectedCount"], "unit": "项", "color": "blue"},
            {"label": "待补齐", "value": stats["pendingCount"], "unit": "项", "color": "orange"},
            {"label": "当前未闭环问题", "value": e02_total, "unit": "项", "color": "red"},
            {"label": "历史问题闭环率", "value": stats["closureRate"], "unit": "", "color": "purple"},
        ],
        "tableData": {
            "title": "上级环保检查 · 11类应备资料进度",
            "total": len(prep_rows),
            "columns": [
                {"key": "index", "label": "序号", "width": "6%", "align": "center"},
                {"key": "category", "label": "类别", "width": "26%", "align": "left"},
                {"key": "required", "label": "应备文件数", "width": "12%", "align": "center"},
                {"key": "collected", "label": "已归集", "width": "10%", "align": "center"},
                {"key": "pending", "label": "待补齐", "width": "10%", "align": "center"},
                {"key": "note", "label": "说明", "width": "36%", "align": "left"},
            ],
            "rows": prep_rows,
        },
        "packageCard": package_card,
        "dataBasis": _basis(
            "上级环保检查合规口径",
            stable_id="PACK-SUPERIOR-ENV",
            caliber=(
                "应备资料按 11 类标准目录统计具体文件归集进度；"
                "未闭环问题与历史闭环率取自首页同源 E02；"
                "待补齐优先映射 G04 环境相关缺口（如环境监测季报），不以「应备仅 4 项」作为主口径；"
                "资料包用于统一下载备检材料。"
            ),
        ),
        "followUps": ["当前有哪些未闭环环保问题？", "当前有哪些待补齐的关键合规资料？", "请给出本轮上级检查可用的合规资料包"],
    }


def build_pack_superior_safety(_question: str) -> dict:
    s02 = _safe_call(lambda: build_s02_active_major(_question), {})
    total = _kpi_card_value(s02, "在管较大及以上", 0)
    if total == 0:
        raw = _safe_call(mysql_api.get_s02_risks, {})
        data = _unwrap_api(raw) or {}
        total = int((data.get("overview") or {}).get("total") or len(data.get("risks") or []) or 0)
    _g04_total, g04_items = _g04_gap_items()

    manifest = _load_manifest("pack_superior_safety.json") or {
        "packageId": "PACK-SUPERIOR-SAFETY-202607",
        "title": "上级安全检查 · 合规资料包",
        "inspectionType": "safety",
        "nature": "sample",
        "downloadUrl": "/samples/assistant-compliance-packs/上级检查_安全合规资料包_202607.zip",
        "updatedAt": "2026-07-27",
        "subtitle": "合规资料包 · 2026年7月账期",
        "requiredDocs": [
            {"name": "合规资料目录", "path": "01_清单_合规资料目录.md", "kind": "checklist"},
            {"name": "在管安全风险台账", "path": "02_风险台账/在管安全风险台账.csv", "kind": "ledger"},
            {"name": "上级安全检查核查项与台账缺口说明", "path": "03_核查表/上级安全检查核查项与台账缺口.md", "kind": "checklist"},
        ],
    }
    package_card = _package_card_from_manifest(manifest)
    prep_rows = _build_safety_prep_rows(total, g04_items)
    return {
        "role": "assistant",
        "content": (
            f"应对上级安全检查，建议按「风险台账—管控闭环—核查清单」口径备检。"
            f"应重点准备：较大及以上在管安全风险台账、风险管控与销号闭环材料、安全生产费用使用台账（如有缺口）、应急预案演练记录，以及上级安全检查核查项。"
            f"当前库内摘要（与首页同源）：在管较大及以上风险点 {total} 处。"
            f"同条回复已附「上级安全检查 · 合规资料包」，可直接下载。"
        ),
        "kpiCards": [
            {"label": "在管较大及以上", "value": total, "unit": "处", "color": "orange"},
            {"label": "应备资料类别", "value": len(prep_rows), "unit": "项", "color": "green"},
        ],
        "tableData": {
            "title": "上级安全检查 · 应备资料清单",
            "total": len(prep_rows),
            "columns": [
                {"key": "index", "label": "序号", "width": "6%", "align": "center"},
                {"key": "name", "label": "资料名称", "width": "26%", "align": "left"},
                {"key": "category", "label": "类别", "width": "12%", "align": "center"},
                {"key": "point", "label": "备检要点", "width": "34%", "align": "left"},
                {"key": "status", "label": "库内/包内状态", "width": "22%", "align": "left"},
            ],
            "rows": prep_rows,
        },
        "packageCard": package_card,
        "dataBasis": _basis(
            "上级安全检查合规口径",
            stable_id="PACK-SUPERIOR-SAFETY",
            caliber="应备资料结合安全检查常规要件与资料包目录；在管风险件数取自首页同源 S02 接口。",
        ),
        "followUps": ["当前较大及以上安全风险点有多少？", "三标段安全风险情况", "请给出本轮上级检查可用的合规资料包"],
    }


def build_pack_superior_comprehensive(_question: str) -> dict:
    g04_total, g04_items = _g04_gap_items()
    g01 = _safe_call(lambda: build_g01_procedures(_question), {})
    g01_n = _kpi_card_value(g01, "未完成事项", 0)
    e02_total = _e02_open_total()

    manifest = _load_manifest("pack_superior_comprehensive.json") or {
        "packageId": "PACK-SUPERIOR-COMP-202607",
        "title": "本轮上级检查 · 综合合规资料包",
        "inspectionType": "comprehensive",
        "nature": "sample",
        "downloadUrl": "/samples/assistant-compliance-packs/上级检查_综合合规资料包_202607.zip",
        "updatedAt": "2026-07-27",
        "subtitle": "合规资料包 · 2026年7月账期",
        "requiredDocs": [
            {"name": "合规资料目录", "path": "01_清单_合规资料目录.md", "kind": "checklist"},
            {"name": "合同与履约合规检查表", "path": "02_合同履约/合同与履约合规检查表.md", "kind": "checklist"},
            {"name": "待补齐关键合规资料摘录", "path": "03_合规资料缺口/待补齐关键合规资料摘录.csv", "kind": "ledger"},
            {"name": "报批报建手续进度摘要", "path": "04_报批报建/未完成报批报建手续进度摘要.txt", "kind": "other"},
        ],
    }
    package_card = _package_card_from_manifest(manifest)

    prep_rows = [
        {
            "index": 1,
            "name": "合同与履约合规检查表",
            "category": "合同履约",
            "point": "合同关键条款、履约节点与检查表勾对",
            "status": "已纳入资料包",
        },
        {
            "index": 2,
            "name": "报批报建手续进度",
            "category": "行政许可",
            "point": "未完成报批报建手续清单与时限",
            "status": f"库内未完成 {g01_n} 项" if g01_n else "当前无未完成项",
        },
        {
            "index": 3,
            "name": "关键合规资料缺口台账",
            "category": "资料缺口",
            "point": "待补齐关键合规资料及责任单位",
            "status": f"库内待补齐 {g04_total} 项" if g04_total else "当前无缺口",
        },
        {
            "index": 4,
            "name": "环保/安全问题与风险摘要",
            "category": "问题摘要",
            "point": "未闭环环保问题与在管安全风险摘要备查",
            "status": f"未闭环环保 {e02_total} 项",
        },
    ]
    # 附上具体缺口名称（最多 4 条）
    for item in g04_items[:4]:
        prep_rows.append(
            {
                "index": len(prep_rows) + 1,
                "name": item.get("name") or "待补齐资料",
                "category": _group_label(item.get("module")),
                "point": f"截止：{item.get('deadline') or '—'}；责任：{item.get('owner') or '—'}",
                "status": f"待补齐 · {item.get('status') or '缺口'}",
            }
        )

    return {
        "role": "assistant",
        "content": (
            f"本轮上级检查可用综合合规资料包如下，覆盖合同履约、报批报建、关键合规资料缺口及环保/安全摘要。"
            f"库内摘要（与首页同源）：待补齐关键合规资料 {g04_total} 项，未完成报批报建 {g01_n} 项，未闭环环保问题 {e02_total} 项。"
            f"请下载资料包统一备检，并优先处理下列待补齐项。"
        ),
        "kpiCards": [
            {"label": "待补齐合规资料", "value": g04_total, "unit": "项", "color": "orange"},
            {"label": "未完成报批报建", "value": g01_n, "unit": "项", "color": "purple"},
            {"label": "综合包应备项", "value": len(prep_rows), "unit": "项", "color": "green"},
        ],
        "tableData": {
            "title": "本轮上级检查 · 综合应备清单",
            "total": len(prep_rows),
            "columns": [
                {"key": "index", "label": "序号", "width": "6%", "align": "center"},
                {"key": "name", "label": "资料名称", "width": "26%", "align": "left"},
                {"key": "category", "label": "类别", "width": "12%", "align": "center"},
                {"key": "point", "label": "备检要点", "width": "34%", "align": "left"},
                {"key": "status", "label": "库内/包内状态", "width": "22%", "align": "left"},
            ],
            "rows": prep_rows,
        },
        "packageCard": package_card,
        "dataBasis": _basis(
            "本轮上级检查综合包",
            stable_id="PACK-SUPERIOR-COMP",
            caliber="摘要数字取自首页同源 G01 / G04 / E02 接口；资料包用于统一下载备检材料。",
        ),
        "followUps": [
            "应对上级环保检查应准备哪些合规资料？",
            "上级安全检查常见核查项与现有台账缺口？",
            "当前有哪些待补齐的关键合规资料？",
        ],
    }


# ── Intent routing ───────────────────────────────────────────────

INTENT_BUILDERS: dict[str, Callable[[str], dict]] = {
    "e02.open_issues": build_e02_open_issues,
    "s02.active_major_risks": build_s02_active_major,
    "e04.cumulative_carbon": build_e04_carbon,
    "monthly.pending": build_monthly_pending,
    "kpi.esg_overview": build_kpi_esg_overview,
    "cross.overdue_rectify": build_overdue,
    "s02.segment_3": build_s02_segment3,
    "kpi.group_E": build_kpi_group("E", "环境 E"),
    "kpi.group_S": build_kpi_group("S", "社会 S"),
    "kpi.group_G": build_kpi_group("G", "治理 G"),
    "carbon.topic": build_carbon_topic,
    "monthly.topic": build_monthly_topic,
    "e02.by_department": build_e02_by_department,
    "e02.segment_3": build_e02_segment3,
    "e02.export_hint": build_e02_export_hint,
    "g04.material_gaps": build_g04_gaps,
    "g01.open_procedures": build_g01_procedures,
    "pack.superior_env": build_pack_superior_env,
    "pack.superior_safety": build_pack_superior_safety,
    "pack.superior_comprehensive": build_pack_superior_comprehensive,
}

# (question_id, patterns, intent_key) — 越靠前优先级越高
QUESTION_ROUTES: list[tuple[str, list[str], str]] = [
    ("C03", ["应对上级环保检查", "上级环保检查应准备", "环保检查.*合规资料"], "pack.superior_env"),
    ("C04", ["上级安全检查", "安全检查常见核查", "安全检查.*台账缺口"], "pack.superior_safety"),
    ("C05", ["本轮上级检查可用的合规资料包", "上级检查可用的合规资料包", "综合合规资料包"], "pack.superior_comprehensive"),
    ("C01", ["待补齐的关键合规资料", "待补齐.*合规资料"], "g04.material_gaps"),
    ("C02", ["未完成报批报建", "报批报建手续"], "g01.open_procedures"),
    ("Q01", ["未闭环环保问题", "环保问题"], "e02.open_issues"),
    ("Q02", ["较大及以上安全风险", "安全风险点有多少"], "s02.active_major_risks"),
    ("Q03", ["累计碳排放", "项目累计碳"], "e04.cumulative_carbon"),
    ("Q04", ["月报资料待处理", "还有哪些月报"], "monthly.pending"),
    ("Q05", ["E/S/G三类", "三类指标总体", "ESG三类"], "kpi.esg_overview"),
    ("Q07", ["逾期整改", "查看逾期事项"], "cross.overdue_rectify"),
    ("Q08", ["三标段安全风险"], "s02.segment_3"),
    ("Q09", ["^环境 E$", "环境 E"], "kpi.group_E"),
    ("Q10", ["^社会 S$", "社会 S"], "kpi.group_S"),
    ("Q11", ["^治理 G$", "治理 G"], "kpi.group_G"),
    ("Q12", ["^碳专题$", "碳专题"], "carbon.topic"),
    ("Q13", ["^月报专题$", "月报专题"], "monthly.topic"),
    ("Q15", ["按责任部门统计"], "e02.by_department"),
    ("Q16", ["查看三标段问题", "三标段问题"], "e02.segment_3"),
    ("Q17", ["导出问题清单"], "e02.export_hint"),
    ("Q06", ["本月月报资料待处理情况"], "monthly.pending"),
    ("Q14", ["查看逾期事项"], "cross.overdue_rectify"),
]

QUESTION_ID_TO_INTENT = {qid: intent for qid, _patterns, intent in QUESTION_ROUTES}


def resolve_intent(question: str | None = None, question_id: str | None = None) -> tuple[str | None, str | None]:
    """返回 (question_id, intent_key)。"""
    if question_id:
        qid = question_id.strip().upper()
        intent = QUESTION_ID_TO_INTENT.get(qid)
        if intent:
            return qid, intent
    text = (question or "").strip()
    if not text:
        return None, None
    for qid, patterns, intent in QUESTION_ROUTES:
        for pat in patterns:
            if re.search(pat, text, flags=re.IGNORECASE):
                return qid, intent
    # 宽松近义
    if "碳排放" in text:
        return "Q03", "e04.cumulative_carbon"
    if "月报" in text and ("待处理" in text or "准备" in text):
        return "Q04", "monthly.pending"
    if "安全风险" in text:
        return "Q02", "s02.active_major_risks"
    if "环保" in text and ("问题" in text or "未闭环" in text):
        return "Q01", "e02.open_issues"
    if "上级" in text and "环保" in text:
        return "C03", "pack.superior_env"
    if "上级" in text and "安全" in text:
        return "C04", "pack.superior_safety"
    if "资料包" in text:
        return "C05", "pack.superior_comprehensive"
    return None, None


def build_fallback(question: str | None = None) -> dict:
    lines = "\n".join(f"· {q['text']}" for q in REGISTERED_QUESTIONS[:8])
    extra = "\n".join(f"· {q['text']}" for q in REGISTERED_QUESTIONS if q["id"].startswith("C"))
    return {
        "role": "assistant",
        "content": (
            "暂未识别到可直接查询的意图。您可以尝试下列问题：\n"
            f"{lines}\n"
            "应对上级检查相关：\n"
            f"{extra}"
        ),
        "followUps": [q["text"] for q in REGISTERED_QUESTIONS if q["id"] in ("Q01", "C03", "C04", "C05")],
    }


def ask(question: str | None = None, question_id: str | None = None) -> dict:
    """组装问答响应。数字一律走现有 mysql_api；失败时返回空态引导。"""
    qid, intent = resolve_intent(question, question_id)
    if not intent or intent not in INTENT_BUILDERS:
        message = build_fallback(question)
        return {
            "code": 0,
            "data": {
                "questionId": qid,
                "intentKey": None,
                "matched": False,
                "registeredQuestions": REGISTERED_QUESTIONS,
                "message": message,
            },
        }
    try:
        message = INTENT_BUILDERS[intent](question or "")
    except Exception as exc:
        print(f"[assistant_qa] intent={intent} error: {exc}")
        message = _empty_message(
            f"查询「{intent}」时数据暂不可用，请稍后重试或改用相关工作台查看。",
            follow_ups=[q["text"] for q in REGISTERED_QUESTIONS if q["id"] in ("Q01", "Q02", "C03")],
        )
    # 清理 None 字段，便于前端
    message = {k: v for k, v in message.items() if v is not None}
    return {
        "code": 0,
        "data": {
            "questionId": qid,
            "intentKey": intent,
            "matched": True,
            "message": message,
        },
    }
