from __future__ import annotations

import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))

from mysql_db import mysql_connect  # noqa: E402


BASE_DIR = Path(__file__).resolve().parent
SCHEMA_PATH = BASE_DIR / "multisource_data_flow_v1.0" / "01_multisource_schema.sql"


def execute_script(sql_text: str) -> None:
    statements = [stmt.strip() for stmt in sql_text.split(";") if stmt.strip()]
    with mysql_connect() as conn:
        with conn.cursor() as cur:
            for stmt in statements:
                cur.execute(stmt)


def seed_sources() -> None:
    sources = [
        (610001, "UPLOAD_WORKSPACE", "数据填报与上传工作台", "UPLOAD", "项目管理部", "罗宜高速ESG平台", None, "资料上传、AI解析、人工确认"),
        (610002, "ENV_MONITOR_API", "第三方环境监测机构接口", "API", "安全环保部", "第三方监测机构", "https://example.local/env-monitor", "环境监测数据同步"),
        (610003, "ENV_ISSUE_MANUAL", "环保问题人工填报", "MANUAL", "安全环保部", "罗宜高速ESG平台", None, "环保问题人工维护"),
        (610004, "SAFETY_RISK_SYSTEM", "安全风险分级管控系统", "API", "安全环保部", "安全风险系统", "https://example.local/safety-risk", "安全风险点同步"),
        (610005, "LABOR_SYSTEM", "劳务实名制与工资支付系统", "API", "综合管理部", "劳务系统", "https://example.local/labor", "劳务纠纷和工资支付数据"),
        (610006, "APPEAL_SYSTEM", "信访与12345诉求系统", "API", "综合管理部", "信访系统", "https://example.local/appeal", "群众诉求同步"),
        (610007, "PERMIT_SYSTEM", "证照许可管理系统", "API", "合约法务部", "证照系统", "https://example.local/permit", "许可事项同步"),
        (610008, "RECTIFICATION_SYSTEM", "整改闭环管理系统", "API", "安全环保部", "整改系统", "https://example.local/rectification", "整改事项同步"),
        (610009, "CARBON_ACTIVITY_IMPORT", "碳排活动数据导入", "BATCH", "安全环保部", "罗宜高速ESG平台", None, "碳排活动批量导入"),
        (610010, "MONTHLY_REPORT_ENGINE", "月报生成与资料状态引擎", "SCHEDULE", "项目管理部", "罗宜高速ESG平台", None, "月报章节和缺项状态计算"),
        (610011, "GIS_ROUTE_DATA", "GIS路线与空间点位数据", "GIS", "工程管理部", "GIS系统", "https://example.local/gis", "路线、敏感区、风险点空间数据"),
    ]
    with mysql_connect() as conn:
        with conn.cursor() as cur:
            cur.executemany(
                """
                INSERT INTO data_source_registry
                (id, source_code, source_name, source_type, owner_department, provider_name, endpoint_url, remark)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE
                  source_name = VALUES(source_name),
                  source_type = VALUES(source_type),
                  owner_department = VALUES(owner_department),
                  provider_name = VALUES(provider_name),
                  endpoint_url = VALUES(endpoint_url),
                  remark = VALUES(remark),
                  enabled = 1
                """,
                sources,
            )


def seed_mapping_rules() -> None:
    rules = [
        (620001, 610002, "env_monitor", "monitorPoint", "env_monitoring_record", "monitor_point", "string", None, 1),
        (620002, 610002, "env_monitor", "monitorDate", "env_monitoring_record", "monitor_date", "date", "date_normalize", 1),
        (620003, 610002, "env_monitor", "factorName", "env_monitoring_record", "factor_name", "string", None, 1),
        (620004, 610002, "env_monitor", "exceedCount", "env_monitoring_record", "exceed_count", "number", "number_normalize", 1),
        (620005, 610003, "env_issue", "issueName", "env_issue_record", "issue_name", "string", None, 1),
        (620006, 610003, "env_issue", "issueStatus", "env_issue_record", "issue_status", "string", "env_issue_status_dictionary", 1),
        (620007, 610004, "risk_point", "riskName", "safety_risk_point", "risk_name", "string", None, 1),
        (620008, 610004, "risk_point", "riskLevel", "safety_risk_point", "risk_level", "string", "risk_level_dictionary", 1),
        (620009, 610005, "labor_dispute", "disputeName", "labor_dispute_record", "dispute_name", "string", None, 1),
        (620010, 610006, "appeal", "appealContent", "appeal_record", "appeal_content", "string", None, 1),
        (620011, 610007, "permit", "permitName", "permit_record", "permit_name", "string", None, 1),
        (620012, 610007, "permit", "expireDate", "permit_record", "expire_date", "date", "date_normalize", 1),
        (620013, 610008, "rectification", "itemName", "rectification_record", "item_name", "string", None, 1),
        (620014, 610009, "carbon_activity", "carbonEmission", "carbon_emission_activity", "carbon_emission", "number", "number_with_unit_normalize", 1),
    ]
    with mysql_connect() as conn:
        with conn.cursor() as cur:
            cur.executemany(
                """
                INSERT INTO data_mapping_rule
                (id, source_id, source_object, source_field, target_table, target_field,
                 target_data_type, transform_rule, required)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE
                  source_id = VALUES(source_id),
                  source_object = VALUES(source_object),
                  source_field = VALUES(source_field),
                  target_table = VALUES(target_table),
                  target_field = VALUES(target_field),
                  target_data_type = VALUES(target_data_type),
                  transform_rule = VALUES(transform_rule),
                  required = VALUES(required),
                  enabled = 1
                """,
                rules,
            )


def seed_indicator_dependencies() -> None:
    dependencies = [
        (630001, "E01", "env_monitoring_record", "PRIMARY", "统计当前周期扬尘、噪声等环境监测超标项次"),
        (630002, "E02", "env_issue_record", "PRIMARY", "统计未闭环环保问题、状态构成和逾期标记"),
        (630003, "E03", "water_protection_issue", "PRIMARY", "统计未闭环水保问题"),
        (630004, "E04", "carbon_emission_activity", "PRIMARY", "统计施工阶段碳排放强度"),
        (630005, "S01", "safety_production_record", "PRIMARY", "统计连续安全生产天数"),
        (630006, "S02", "safety_risk_point", "PRIMARY", "统计在管较大及以上安全风险点"),
        (630007, "S03", "labor_dispute_record", "PRIMARY", "统计未办结劳务纠纷"),
        (630008, "S04", "appeal_record", "PRIMARY", "统计未办结群众诉求"),
        (630009, "G01", "compliance_procedure", "PRIMARY", "统计未完成合规手续"),
        (630010, "G02", "permit_record", "PRIMARY", "统计临期及逾期许可事项"),
        (630011, "G03", "rectification_record", "PRIMARY", "统计未关闭整改事项"),
        (630012, "G04", "compliance_material_gap", "PRIMARY", "统计待补齐合规资料"),
        (630013, "CARBON", "carbon_material_usage", "SECONDARY", "统计碳排来源构成"),
        (630014, "MONTHLY", "document_record", "SECONDARY", "统计月报资料准备状态"),
        (630015, "MONTHLY", "upload_task", "SECONDARY", "统计月报缺项任务状态"),
    ]
    with mysql_connect() as conn:
        with conn.cursor() as cur:
            cur.executemany(
                """
                INSERT INTO indicator_source_dependency
                (id, indicator_code, source_table, dependency_type, calculation_desc)
                VALUES (%s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE
                  dependency_type = VALUES(dependency_type),
                  calculation_desc = VALUES(calculation_desc),
                  enabled = 1
                """,
                dependencies,
            )


def seed_minimal_trace_and_jobs() -> None:
    with mysql_connect() as conn:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM source_record_trace WHERE id BETWEEN 640001 AND 640099")
            cur.execute("DELETE FROM data_quality_check_result WHERE id BETWEEN 650001 AND 650099")
            cur.execute("DELETE FROM data_ingestion_job WHERE id BETWEEN 660001 AND 660099")
            cur.execute("DELETE FROM indicator_calculation_job WHERE id BETWEEN 670001 AND 670099")
            cur.execute("DELETE FROM indicator_history WHERE id BETWEEN 680001 AND 680099")

            cur.executemany(
                """
                INSERT INTO data_ingestion_job
                (id, source_id, job_type, job_status, business_domain, target_table,
                 started_at, finished_at, total_count, success_count, failed_count, operator_name)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                [
                    (660001, 610002, "API_SYNC", "SUCCESS", "ENV", "env_monitoring_record", "2026-07-13 09:55:00", "2026-07-13 10:00:00", 2, 2, 0, "系统同步"),
                    (660002, 610007, "API_SYNC", "SUCCESS", "GOVERNANCE", "permit_record", "2026-07-13 08:55:00", "2026-07-13 09:00:00", 5, 5, 0, "系统同步"),
                    (660003, 610001, "FILE_PARSE", "SUCCESS", "GOVERNANCE", "rectification_record", "2026-07-13 10:15:00", "2026-07-13 10:20:00", 6, 6, 0, "项目管理员"),
                ],
            )

            cur.executemany(
                """
                INSERT INTO source_record_trace
                (id, ingestion_job_id, source_id, source_type, source_record_key, document_id, file_id,
                 target_table, target_record_id, operation_type, trace_payload)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                [
                    (640001, 660001, 610002, "API", "ENV-410001", None, None, "env_monitoring_record", "410001", "UPSERT", json.dumps({"monitorPoint": "K12+000 路基监测点", "exceedCount": 1}, ensure_ascii=False)),
                    (640002, 660001, 610002, "API", "ENV-410002", None, None, "env_monitoring_record", "410002", "UPSERT", json.dumps({"monitorPoint": "K18+500 弃渣场监测点", "exceedCount": 1}, ensure_ascii=False)),
                    (640003, 660002, 610007, "API", "PERMIT-320005", None, None, "permit_record", "320005", "UPSERT", json.dumps({"permitName": "临时占用林地审批", "expireDate": "2026-07-05"}, ensure_ascii=False)),
                    (640004, 660003, 610001, "UPLOAD", "RECT-330004", None, None, "rectification_record", "330004", "UPSERT", json.dumps({"itemName": "应急预案未及时修订", "status": "逾期"}, ensure_ascii=False)),
                ],
            )

            cur.executemany(
                """
                INSERT INTO data_quality_check_result
                (id, ingestion_job_id, source_record_key, target_table, target_record_id,
                 check_type, check_status, check_message)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """,
                [
                    (650001, 660001, "ENV-410001", "env_monitoring_record", "410001", "REQUIRED", "PASS", "必填字段完整"),
                    (650002, 660001, "ENV-410002", "env_monitoring_record", "410002", "BUSINESS_RULE", "PASS", "超标项次与因子分类一致"),
                    (650003, 660002, "PERMIT-320005", "permit_record", "320005", "BUSINESS_RULE", "WARN", "许可已逾期，需纳入 G02 预警"),
                    (650004, 660003, "RECT-330004", "rectification_record", "330004", "BUSINESS_RULE", "WARN", "整改事项逾期未关闭"),
                ],
            )

            cur.executemany(
                """
                INSERT INTO indicator_calculation_job
                (id, indicator_code, calculation_type, trigger_source, trigger_record_id,
                 job_status, calculation_period, started_at, finished_at, result_value, result_payload)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                [
                    (670001, "E01", "EVENT_TRIGGER", "env_monitoring_record", "410002", "SUCCESS", "2026-07", "2026-07-13 10:00:00", "2026-07-13 10:00:02", 2, json.dumps({"当前超标项": 2, "扬尘": 1, "噪声": 1}, ensure_ascii=False)),
                    (670002, "G02", "SCHEDULED", "permit_record", None, "SUCCESS", "2026-07", "2026-07-13 09:00:00", "2026-07-13 09:00:02", 5, json.dumps({"临期许可": 4, "逾期许可": 1, "30日内到期": 4}, ensure_ascii=False)),
                ],
            )

            cur.executemany(
                """
                INSERT INTO indicator_history
                (id, indicator_code, result_date, result_value, result_text, unit, calculation_job_id, detail_payload)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE
                  result_value = VALUES(result_value),
                  result_text = VALUES(result_text),
                  unit = VALUES(unit),
                  calculation_job_id = VALUES(calculation_job_id),
                  detail_payload = VALUES(detail_payload)
                """,
                [
                    (680001, "E01", "2026-07-13", 2, "2项", "项", 670001, json.dumps({"source": "env_monitoring_record"}, ensure_ascii=False)),
                    (680002, "G02", "2026-07-13", 5, "5项", "项", 670002, json.dumps({"source": "permit_record"}, ensure_ascii=False)),
                ],
            )


def main() -> int:
    execute_script(SCHEMA_PATH.read_text(encoding="utf-8"))
    seed_sources()
    seed_mapping_rules()
    seed_indicator_dependencies()
    seed_minimal_trace_and_jobs()
    print("✅ 多源数据流 V1.0 治理表已落库并写入基础种子与最小闭环样例。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

