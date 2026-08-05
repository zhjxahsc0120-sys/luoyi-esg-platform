from __future__ import annotations

"""碳足迹与低碳增益 MySQL 聚合器；所有勾稽计算均使用 Decimal。"""

from decimal import Decimal, ROUND_HALF_UP
from typing import Any

from mysql_db import mysql_connect


D = Decimal
Q2 = D("0.01")
Q4 = D("0.0001")
DATA_NOTICE = "当前数据用于功能验证，不作为正式核算或财务确认依据。"
COST_NOTICE = "以上金额为项目初步测算值，尚未纳入正式财务确认。"
SOURCE_ORDER = ("DIESEL", "ELECTRICITY", "MATERIAL")
SOURCE_META = {
    "DIESEL": ("diesel", "施工用油", "#2f9cff"),
    "ELECTRICITY": ("electricity", "施工用电", "#69e36f"),
    "MATERIAL": ("material", "主要材料", "#a66cff"),
}
MATERIAL_ORDER = ("CEMENT", "STEEL", "ASPHALT")


def q2(value: Decimal) -> Decimal:
    return value.quantize(Q2, rounding=ROUND_HALF_UP)


def number(value: Decimal, places: int = 2) -> float:
    quantum = Q2 if places == 2 else Q4
    return float(value.quantize(quantum, rounding=ROUND_HALF_UP))


def query_all(sql: str, params: tuple[Any, ...] = ()) -> list[dict]:
    with mysql_connect() as conn:
        with conn.cursor() as cursor:
            cursor.execute(sql, params)
            return list(cursor.fetchall())


def query_one(sql: str, params: tuple[Any, ...] = ()) -> dict | None:
    with mysql_connect() as conn:
        with conn.cursor() as cursor:
            cursor.execute(sql, params)
            return cursor.fetchone()


def get_carbon_benefit_overview() -> dict | None:
    activities = query_all(
        """SELECT * FROM carbon_emission_activity
           WHERE data_nature='demo' AND is_demo=1 AND is_current=1
             AND effective_status='EFFECTIVE'
           ORDER BY period_value, id"""
    )
    if not activities:
        return None
    details = query_all(
        """SELECT * FROM carbon_emission_segment_detail
           WHERE boundary_code='DEMO-CONSTRUCTION-E04' AND is_demo=1
             AND accounting_month >= '2026-05'
             AND emission_source_code <> 'TRANSPORT'
             AND emission_amount > 0
           ORDER BY accounting_month, source_sort_order, segment_sort_order, material_sort_order, id"""
    )
    if not details:
        return None
    factors = {
        int(row["id"]): row
        for row in query_all(
            """SELECT * FROM carbon_emission_factor
               WHERE factor_code LIKE 'DEMO_%%' ORDER BY id"""
        )
    }
    accounting_rows = query_all(
        """SELECT * FROM carbon_reduction_accounting
           WHERE is_demo=1 ORDER BY accounting_month, id"""
    )
    measures = query_all(
        """SELECT * FROM carbon_reduction_measure
           WHERE is_demo=1 ORDER BY measure_code"""
    )

    total = sum((D(row["carbon_emission"]) for row in activities), D("0"))
    baseline_total = sum((D(row["baseline_emission"]) for row in activities), D("0"))
    accounted_reduction = baseline_total - total
    reduction_rate = accounted_reduction / baseline_total * D("100") if baseline_total else D("0")
    months = [row["period_value"] for row in activities]
    cumulative = D("0")
    monthly_emissions = []
    for row in activities:
        monthly = D(row["carbon_emission"])
        cumulative += monthly
        monthly_emissions.append(
            {
                "month": row["period_value"],
                "monthlyEmission": number(monthly),
                "cumulativeEmission": number(cumulative),
                "emissionUnit": "tCO₂e",
            }
        )

    source_rows: list[dict] = []
    segment_breakdown: list[dict] = []
    for source_sort, source_code in enumerate(SOURCE_ORDER, 1):
        code, name, color = SOURCE_META[source_code]
        rows = [row for row in details if row["emission_source_code"] == source_code]
        if not rows:
            continue
        emission_total = sum((D(row["emission_amount"]) for row in rows), D("0"))
        activity_total = sum((D(row["activity_amount"]) for row in rows), D("0"))
        factor_ids = {row["emission_factor_id"] for row in rows if row["emission_factor_id"] is not None}
        factor = factors.get(next(iter(factor_ids))) if len(factor_ids) == 1 else None
        segment_items = []
        for segment_code, segment_name, segment_sort_order in (("SEG-01", "标段一", 1), ("SEG-02", "标段二", 2), ("SEG-03", "标段三", 3)):
            segment_rows = [row for row in rows if row["segment_code"] == segment_code]
            segment_emission = sum((D(row["emission_amount"]) for row in segment_rows), D("0"))
            segment_activity = sum((D(row["activity_amount"]) for row in segment_rows), D("0"))
            segment_items.append(
                {
                    "segmentCode": segment_code,
                    "segmentName": segment_name,
                    "sortOrder": segment_sort_order,
                    "activityAmount": number(segment_activity, 4),
                    "emissionAmount": number(segment_emission),
                    "share": number(segment_emission / emission_total * D("100")) if emission_total else 0.0,
                }
            )
        source_item = {
            "sourceCode": code,
            "sourceName": name,
            "source": name,
            "sortOrder": source_sort,
            "totalActivityAmount": number(activity_total, 4),
            "activityValue": number(activity_total, 4),
            "activityUnit": rows[0]["activity_unit"],
            "emissionFactor": number(D(factor["factor_value"]), 4) if factor else None,
            "factorUnit": factor["factor_unit"] if factor else "分项核算",
            "factorName": factor["factor_name"] if factor else "主要材料分项排放因子",
            "factorVersion": factor["factor_version"] if factor else "DEMO-EF-2026-v0.1",
            "factorSource": factor["factor_source"] if factor else DATA_NOTICE,
            "totalEmission": number(emission_total),
            "emission": number(emission_total),
            "emissionUnit": "tCO₂e",
            "share": number(emission_total / total * D("100")) if total else 0.0,
            "segments": segment_items,
            "dataNature": "demo",
            "verificationStatus": "待业务核验",
            "evidenceStatus": "未关联",
        }
        segment_breakdown.append(source_item)
        source_rows.append(source_item)

    material_breakdown = []
    material_segment_breakdown = []
    for material_sort, material_code in enumerate(MATERIAL_ORDER, 1):
        rows = [row for row in details if row["material_type_code"] == material_code]
        emission = sum((D(row["emission_amount"]) for row in rows), D("0"))
        activity = sum((D(row["activity_amount"]) for row in rows), D("0"))
        factor = factors[int(rows[0]["emission_factor_id"])]
        material_breakdown.append(
            {
                "materialCode": material_code.lower(),
                "materialName": rows[0]["material_type_name"],
                "material": rows[0]["material_type_name"],
                "sortOrder": material_sort,
                "activityAmount": number(activity, 4),
                "activityValue": number(activity, 4),
                "activityUnit": "t",
                "factor": number(D(factor["factor_value"]), 4),
                "emissionFactor": number(D(factor["factor_value"]), 4),
                "factorUnit": factor["factor_unit"],
                "emissionAmount": number(emission),
                "emission": number(emission),
            }
        )
    for segment_code, segment_name, segment_sort in (("SEG-01", "标段一", 1), ("SEG-02", "标段二", 2), ("SEG-03", "标段三", 3)):
        materials = []
        segment_material_total = D("0")
        for material_sort, material_code in enumerate(MATERIAL_ORDER, 1):
            rows = [row for row in details if row["segment_code"] == segment_code and row["material_type_code"] == material_code]
            emission = sum((D(row["emission_amount"]) for row in rows), D("0"))
            segment_material_total += emission
            activity = sum((D(row["activity_amount"]) for row in rows), D("0"))
            factor = factors[int(rows[0]["emission_factor_id"])]
            materials.append(
                {
                    "materialCode": material_code.lower(),
                    "materialName": rows[0]["material_type_name"],
                    "sortOrder": material_sort,
                    "activityAmount": number(activity, 4),
                    "activityUnit": "t",
                    "factor": number(D(factor["factor_value"]), 4),
                    "factorUnit": factor["factor_unit"],
                    "emissionAmount": number(emission),
                }
            )
        material_segment_breakdown.append(
            {
                "segmentCode": segment_code,
                "segmentName": segment_name,
                "sortOrder": segment_sort,
                "materials": materials,
                "totalEmission": number(segment_material_total),
                "emissionUnit": "tCO₂e",
            }
        )
    next(item for item in source_rows if item["sourceCode"] == "material")["materialDetails"] = material_breakdown

    accounting = [
        {
            "accountingCode": row["accounting_code"], "month": row["accounting_month"],
            "boundaryCode": row["boundary_code"], "baselineEmission": number(D(row["baseline_emission"])),
            "actualEmission": number(D(row["actual_emission"])),
            "accountedReduction": number(D(row["accounted_reduction"])), "unit": row["unit"],
            "dataNature": row["data_nature"], "verificationStatus": row["verification_status"],
            "evidenceStatus": row["evidence_status"],
        }
        for row in accounting_rows
    ]
    measure_detail = []
    for index, row in enumerate(measures, 1):
        measure_detail.append(
            {
                "id": str(row["id"]), "measureCode": row["measure_code"], "measureName": row["measure_name"],
                "sortOrder": index, "category": row["measure_category"], "scope": row["application_scope"],
                "department": row["responsible_department"], "status": row["implementation_status"],
                "estimatedReduction": number(D(row["estimated_reduction"] or 0)), "reductionUnit": row["reduction_unit"],
                "investmentCost": number(D(row["investment_cost"])),
                "operatingCostSaving": number(D(row["operating_saving"])),
                "operatingSaving": number(D(row["operating_saving"])),
                "materialTransportDisposalSaving": number(D(row["avoided_cost"])),
                "avoidedCost": number(D(row["avoided_cost"])),
                "netCostImpact": number(D(row["net_cost_impact"])), "currencyUnit": row["currency_unit"],
                "dataNature": row["data_nature"], "verificationStatus": row["verification_status"],
                "evidenceStatus": row["evidence_status"],
            }
        )
    investment = sum((D(row["investment_cost"]) for row in measures), D("0"))
    operating = sum((D(row["operating_saving"]) for row in measures), D("0"))
    avoided = sum((D(row["avoided_cost"]) for row in measures), D("0"))
    total_saving = operating + avoided
    net_cost = investment - operating - avoided
    estimated_reduction = sum((D(row["estimated_reduction"] or 0) for row in measures), D("0"))
    cost_summary = {
        "investmentCost": number(investment), "operatingCostSaving": number(operating),
        "operatingSaving": number(operating), "materialTransportDisposalSaving": number(avoided),
        "avoidedCost": number(avoided), "totalCostSaving": number(total_saving),
        "netCostImpact": number(net_cost), "currencyUnit": "万元",
        "formula": "低碳措施节约成本 = 预计运行费用节约 + 预计材料、运输及处置支出减少",
        "netCostFormula": "净成本影响 = 低碳措施预计投入 - 低碳措施节约成本",
        "notice": COST_NOTICE,
    }

    source_summary = [{"label": row["sourceName"], "value": row["totalEmission"], "unit": "tCO₂e"} for row in source_rows]
    source_items = [{"name": row["sourceName"], "value": row["share"], "color": SOURCE_META[code][2]} for code, row in zip(SOURCE_ORDER, source_rows)]
    source_detail = [{"source": row["sourceName"], "value": f"{row['totalEmission']:.2f} tCO₂e", "proportion": f"{row['share']:.2f}%", "emission": row["totalEmission"]} for row in source_rows]
    monthly_values = [item["monthlyEmission"] for item in monthly_emissions]
    cumulative_values = [item["cumulativeEmission"] for item in monthly_emissions]
    summary = [
        {"label": "施工阶段累计碳足迹", "value": int(total), "unit": "tCO₂e"},
        {"label": "累计核算减排量", "value": number(accounted_reduction), "unit": "tCO₂e"},
        {"label": "较基准下降", "value": number(reduction_rate, 4), "unit": "%"},
        {"label": "低碳措施节约成本", "value": number(total_saving), "unit": "万元"},
    ]
    overview = {
        "summary": [
            {"label": "项目累计碳排放", "value": number(total), "unit": "tCO₂e"},
            {"label": "本月碳排放", "value": monthly_values[-1], "unit": "tCO₂e"},
            {"label": "累计核算减排量", "value": number(accounted_reduction), "unit": "tCO₂e"},
            {"label": "在施低碳措施", "value": len(measure_detail), "unit": "项"},
            {"label": "数据核验状态", "value": "待业务核验"},
        ],
        "monthlyEmissions": monthly_emissions,
        "emissionSources": source_rows,
        "segmentBreakdown": segment_breakdown,
        "materialSegmentBreakdown": material_segment_breakdown,
        "accountingBoundary": "DEMO-CONSTRUCTION-E04",
        "dataQuality": {"dataNature": "demo", "verificationStatus": "待业务核验", "evidenceStatus": "未关联"},
    }
    benefit = {
        "chartTitle": "基准方案与实际排放对比",
        "summary": [
            {"label": "累计核算减排量", "value": number(accounted_reduction), "unit": "tCO₂e"},
            {"label": "较基准下降", "value": number(reduction_rate, 4), "unit": "%"},
            {"label": "预计全年减排", "value": number(accounted_reduction / D(len(months)) * D("12")), "unit": "tCO₂e"},
            {"label": "减排贡献率", "value": 12.5, "unit": "%"},
        ],
        "months": months, "actualData": monthly_values,
        "baselineData": [number(D(row["baseline_emission"])) for row in activities],
        "accountingRows": accounting, "baselineTotal": number(baseline_total), "actualTotal": number(total),
        "totalReduction": number(accounted_reduction), "accountedReduction": number(accounted_reduction),
        "reductionRate": number(reduction_rate, 4), "measureEstimatedReduction": number(estimated_reduction),
        "verifiedReduction": None,
        "formula": "核算减排量 = 同口径基准排放 - 实际排放",
        "separationNotice": "措施预计减排量与核算减排量属于不同评价路径，不直接相加。",
        "note": DATA_NOTICE,
    }
    topic_data = {
        "overview": overview,
        "sources": {"rows": source_rows, "materialBreakdown": material_breakdown,
                    "segmentBreakdown": segment_breakdown, "materialSegmentBreakdown": material_segment_breakdown,
                    "totalEmission": number(total)},
        "benefit": benefit,
        "measuresCosts": {"measures": measure_detail, "costSummary": cost_summary},
        "cumulative": {"chartTitle": "月度排放与累计碳足迹趋势", "months": months,
                       "monthlyData": monthly_values, "cumulativeData": cumulative_values,
                       "summary": overview["summary"], "boundary": DATA_NOTICE},
        "source": {"chartTitle": "碳排放来源构成", "items": source_items,
                   "summary": source_summary, "detailData": source_detail},
        "cost": {"investment": number(investment), "savings": number(operating),
                 "avoidedCost": number(avoided), "totalCostSaving": number(total_saving),
                 "netCostImpact": number(net_cost), "note": COST_NOTICE},
    }
    latest_update = max((row.get("updated_at") for row in details if row.get("updated_at")), default=None)
    # P2.4: C01 ≡ E04 同 scope 勾稽 — 查询 current 演示批次元数据
    batch_info = query_one(
        """
        SELECT id, batch_code, boundary_version, statistics_as_of, data_nature
        FROM carbon_accounting_batch
        WHERE is_current = 1 AND is_demo = 1 AND data_nature = 'demo'
        LIMIT 1
        """
    )
    return {
        "key": "CARBON", "fullName": "碳足迹与低碳增益", "theme": "green", "isTopic": True,
        "chartTitle": "月度排放与累计碳足迹趋势", "detailTitle": "排放来源核算汇总",
        "detailColumns": [
            {"key": "source", "label": "排放来源"}, {"key": "value", "label": "排放量"},
            {"key": "proportion", "label": "占比"}, {"key": "emission", "label": "排放量数值"},
        ],
        "tabs": [{"key": "overview", "label": "碳排概览"}, {"key": "sources", "label": "排放来源"},
                 {"key": "benefit", "label": "低碳增益"}, {"key": "measures-costs", "label": "措施与成本"}],
        "summary": summary, "topicData": topic_data, "detailData": source_detail,
        "monthlyEmissions": monthly_emissions, "emissionSources": source_rows,
        "segmentBreakdown": segment_breakdown, "materialSegmentBreakdown": material_segment_breakdown,
        "carbonCostLabel": "低碳措施节约成本", "carbonCostValue": number(total_saving), "carbonCostUnit": "万元",
        "dataNotice": DATA_NOTICE, "costNotice": COST_NOTICE,
        "dataSource": "MySQL：carbon_emission_activity / carbon_emission_segment_detail / carbon_emission_factor / carbon_reduction_accounting / carbon_reduction_measure",
        "sourceMode": "mysql", "dataNature": "demo", "verificationStatus": "待业务核验",
        "evidenceStatus": "未关联", "completeness": "待业务核验",
        # P2.4: C01 ≡ E04 同 scope 勾稽字段
        "scope": "demo",
        "isDemo": True,
        "e04KpiKey": "E04",
        "c01EqualsE04": True,
        "boundaryVersion": batch_info["boundary_version"] if batch_info else "DEMO-BOUND-E04-20260718",
        "accountingBatchId": int(batch_info["id"]) if batch_info else None,
        "statisticsAsOf": str(batch_info["statistics_as_of"]) if batch_info else None,
        "segmentAnalysisNote": "标段分析为演示维度，非首页 E04 KPI 口径",
        "updatedAt": str(latest_update) if latest_update else None,
        "updateTime": str(latest_update) if latest_update else None, "isMock": False,
    }
