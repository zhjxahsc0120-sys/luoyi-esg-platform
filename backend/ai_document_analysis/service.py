"""工程资料解析服务。

当前阶段使用确定性的罗宜高速测试结果建立接口契约；后续 OCR、LLM、RAG 只需替换
``build_analysis_result``，数据库和 API 返回结构无需变化。
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from threading import Lock
from typing import Protocol

from mysql_db import mysql_connect

from .models import (
    AnalysisData,
    AnalysisRecord,
    AnalysisResult,
    DocumentDescriptor,
    EnvironmentInfo,
    ProgressItem,
    ProjectInfo,
    ResourceInfo,
    ReviewInfo,
    SafetyInfo,
    SummaryPayload,
)


PROJECT_NAME = "罗宜高速公路项目"
TEST_FILES = {
    985: ("罗宜高速2026年5月工程监理月报.pdf", "工程监理月报", "2026-05"),
    986: ("罗宜高速2026年6月工程监理月报.pdf", "工程监理月报", "2026-06"),
    987: ("罗宜高速2026年6月安全监理月报.pdf", "安全监理月报", "2026-06"),
}


class AnalysisRepository(Protocol):
    storage_mode: str

    def save(self, source_file_id: int, file_name: str, result: AnalysisResult) -> AnalysisRecord: ...

    def get(self, analysis_id: int) -> AnalysisRecord | None: ...


def _now_string() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def _engineering_progress(period: str) -> list[ProgressItem]:
    return [
        ProgressItem("TJ-01", "路基工程", "路基填筑、边坡防护", "汛期排水与高边坡稳定检查", period),
        ProgressItem("QL-02", "桥梁工程", "桥梁下部结构施工", "桩基质量与高处作业防护", period),
        ProgressItem("SD-03", "隧道工程", "隧道初期支护", "围岩变化与超前地质预报", period),
        ProgressItem("HT-04", "互通工程", "互通区土石方及结构物施工", "交叉作业与交通组织", period),
    ]


def _engineering_result(period: str, confidence: float) -> AnalysisResult:
    is_june = period == "2026-06"
    return AnalysisResult(
        document=DocumentDescriptor("工程监理月报", period, confidence),
        summary=SummaryPayload(
            overview=(
                f"罗宜高速公路项目{period.replace('-', '年')}月处于主体施工阶段，"
                "路基、桥梁、隧道及互通工程按计划推进，工程质量、安全生产、环保水保总体受控。"
            ),
            key_work=["路基填筑", "桥梁下部结构", "隧道初期支护", "互通施工"],
            risk_focus=["汛期排水", "高边坡稳定", "隧道围岩变化", "交叉作业交通组织"],
        ),
        data=AnalysisData(
            project_info=ProjectInfo(PROJECT_NAME, "主体施工阶段", 78.6, 5, 4, period),
            progress=_engineering_progress(period),
            safety=SafetyInfo(355 if is_june else 324, 2, 4 if is_june else 3, 12 if is_june else 10, period),
            environment=EnvironmentInfo(3 if is_june else 2, 2, "整改推进中", 0, period),
            resource=ResourceInfo(
                1328 if is_june else 1260,
                446 if is_june else 428,
                "挖掘机、压路机、架桥机、混凝土运输车、隧道台车",
                period,
            ),
        ),
        review=ReviewInfo([], "completed"),
    )


def _safety_result() -> AnalysisResult:
    period = "2026-06"
    return AnalysisResult(
        document=DocumentDescriptor("安全监理月报", period, 0.93),
        summary=SummaryPayload(
            overview=(
                "罗宜高速公路项目本期安全生产总体受控，持续开展高边坡、隧道、桥梁高处作业、"
                "临时用电与汛期施工检查，较大风险点2处，未关闭整改4项。"
            ),
            key_work=["安全专项检查", "风险点巡查", "隐患整改闭环", "防汛应急准备"],
            risk_focus=["较大风险点2处", "未关闭整改4项", "高处作业", "临时用电"],
        ),
        data=AnalysisData(
            project_info=ProjectInfo(PROJECT_NAME, "主体施工阶段", 78.6, 5, 4, period),
            progress=_engineering_progress(period),
            safety=SafetyInfo(355, 2, 4, 18, period),
            environment=EnvironmentInfo(2, 1, "整改推进中", 0, period),
            resource=ResourceInfo(1328, 446, "安全巡检车辆、应急排水设备、临时用电检测设备", period),
        ),
        review=ReviewInfo([], "completed"),
    )


def build_analysis_result(source_file_id: int, file_name: str = "") -> tuple[str, AnalysisResult]:
    normalized_name = file_name.strip()
    if not normalized_name and source_file_id in TEST_FILES:
        normalized_name = TEST_FILES[source_file_id][0]

    if source_file_id == 987 or "安全监理" in normalized_name:
        return normalized_name or TEST_FILES[987][0], _safety_result()
    if source_file_id == 986 or "2026年6月" in normalized_name:
        return normalized_name or TEST_FILES[986][0], _engineering_result("2026-06", 0.91)
    if source_file_id == 985 or "2026年5月" in normalized_name:
        return normalized_name or TEST_FILES[985][0], _engineering_result("2026-05", 0.87)

    result = _engineering_result("2026-05", 0.82)
    return normalized_name or f"工程资料_{source_file_id}.pdf", result


class MemoryAnalysisRepository:
    storage_mode = "memory"

    def __init__(self) -> None:
        self._records: dict[int, AnalysisRecord] = {}
        self._next_id = 900001
        self._lock = Lock()

    def save(self, source_file_id: int, file_name: str, result: AnalysisResult) -> AnalysisRecord:
        with self._lock:
            analysis_id = self._next_id
            self._next_id += 1
            record = _make_record(analysis_id, source_file_id, file_name, result)
            self._records[analysis_id] = record
        return record

    def get(self, analysis_id: int) -> AnalysisRecord | None:
        return self._records.get(analysis_id)


class MySQLAnalysisRepository:
    storage_mode = "mysql"

    def save(self, source_file_id: int, file_name: str, result: AnalysisResult) -> AnalysisRecord:
        document = result.document
        data = result.data
        with mysql_connect() as conn:
            conn.begin()
            try:
                with conn.cursor() as cursor:
                    cursor.execute(
                        """
                        INSERT INTO ai_document_analysis (
                            source_file_id, file_name, file_type, project_name, report_period,
                            analysis_status, summary_text, confidence_score, ingestion_status,
                            excluded_from_dashboard
                        ) VALUES (%s, %s, %s, %s, %s, 'completed', %s, %s, 'stored', 1)
                        """,
                        (
                            source_file_id,
                            file_name,
                            document.type,
                            data.project_info.project_name,
                            document.period,
                            result.summary.overview,
                            document.confidence,
                        ),
                    )
                    analysis_id = int(cursor.lastrowid)
                    project = data.project_info
                    cursor.execute(
                        """
                        INSERT INTO ai_extracted_project_info (
                            analysis_id, project_name, construction_stage, route_length,
                            section_count, professional_type_count, period
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s)
                        """,
                        (
                            analysis_id,
                            project.project_name,
                            project.construction_stage,
                            project.route_length,
                            project.section_count,
                            project.professional_type_count,
                            project.period,
                        ),
                    )
                    cursor.executemany(
                        """
                        INSERT INTO ai_extracted_progress (
                            analysis_id, section_code, work_type, work_content, supervision_focus, period
                        ) VALUES (%s, %s, %s, %s, %s, %s)
                        """,
                        [
                            (
                                analysis_id,
                                item.section_code,
                                item.work_type,
                                item.work_content,
                                item.supervision_focus,
                                item.period,
                            )
                            for item in data.progress
                        ],
                    )
                    safety = data.safety
                    cursor.execute(
                        """
                        INSERT INTO ai_extracted_safety (
                            analysis_id, safe_days, risk_point_count, unfinished_issue_count,
                            inspection_count, period
                        ) VALUES (%s, %s, %s, %s, %s, %s)
                        """,
                        (
                            analysis_id,
                            safety.safe_days,
                            safety.risk_point_count,
                            safety.unfinished_issue_count,
                            safety.inspection_count,
                            safety.period,
                        ),
                    )
                    environment = data.environment
                    cursor.execute(
                        """
                        INSERT INTO ai_extracted_environment (
                            analysis_id, environment_issue_count, water_issue_count,
                            rectification_status, monitoring_abnormal_count, period
                        ) VALUES (%s, %s, %s, %s, %s, %s)
                        """,
                        (
                            analysis_id,
                            environment.environment_issue_count,
                            environment.water_issue_count,
                            environment.rectification_status,
                            environment.monitoring_abnormal_count,
                            environment.period,
                        ),
                    )
                    resource = data.resource
                    cursor.execute(
                        """
                        INSERT INTO ai_extracted_resource (
                            analysis_id, person_count, equipment_count, equipment_type, period
                        ) VALUES (%s, %s, %s, %s, %s)
                        """,
                        (
                            analysis_id,
                            resource.person_count,
                            resource.equipment_count,
                            resource.equipment_type,
                            resource.period,
                        ),
                    )
                conn.commit()
            except Exception:
                conn.rollback()
                raise
        return _make_record(analysis_id, source_file_id, file_name, result)

    def get(self, analysis_id: int) -> AnalysisRecord | None:
        with mysql_connect() as conn:
            with conn.cursor() as cursor:
                cursor.execute("SELECT * FROM ai_document_analysis WHERE id = %s", (analysis_id,))
                document = cursor.fetchone()
                if document is None:
                    return None
                cursor.execute("SELECT * FROM ai_extracted_project_info WHERE analysis_id = %s", (analysis_id,))
                project = cursor.fetchone()
                cursor.execute(
                    "SELECT * FROM ai_extracted_progress WHERE analysis_id = %s ORDER BY id",
                    (analysis_id,),
                )
                progress = list(cursor.fetchall())
                cursor.execute("SELECT * FROM ai_extracted_safety WHERE analysis_id = %s", (analysis_id,))
                safety = cursor.fetchone()
                cursor.execute("SELECT * FROM ai_extracted_environment WHERE analysis_id = %s", (analysis_id,))
                environment = cursor.fetchone()
                cursor.execute("SELECT * FROM ai_extracted_resource WHERE analysis_id = %s", (analysis_id,))
                resource = cursor.fetchone()
        return _record_from_rows(document, project, progress, safety, environment, resource)


def _make_record(analysis_id: int, source_file_id: int, file_name: str, result: AnalysisResult) -> AnalysisRecord:
    return AnalysisRecord(
        id=analysis_id,
        source_file_id=source_file_id,
        file_name=file_name,
        file_type=result.document.type,
        project_name=result.data.project_info.project_name,
        report_period=result.document.period,
        analysis_status="completed",
        summary_text=result.summary.overview,
        confidence_score=result.document.confidence,
        ingestion_status="stored",
        excluded_from_dashboard=True,
        created_at=_now_string(),
        result=result,
    )


def _number(value: object) -> float:
    return float(value) if isinstance(value, Decimal) else float(value or 0)


def _record_from_rows(document: dict, project: dict, progress: list[dict], safety: dict, environment: dict, resource: dict) -> AnalysisRecord:
    progress_items = [
        ProgressItem(
            str(item["section_code"]),
            str(item["work_type"]),
            str(item["work_content"]),
            str(item.get("supervision_focus") or ""),
            str(item["period"]),
        )
        for item in progress
    ]
    project_info = ProjectInfo(
        str(project["project_name"]),
        str(project.get("construction_stage") or ""),
        _number(project.get("route_length")),
        int(project.get("section_count") or 0),
        int(project.get("professional_type_count") or 0),
        str(project["period"]),
    )
    safety_info = SafetyInfo(
        int(safety.get("safe_days") or 0),
        int(safety.get("risk_point_count") or 0),
        int(safety.get("unfinished_issue_count") or 0),
        int(safety.get("inspection_count") or 0),
        str(safety["period"]),
    )
    environment_info = EnvironmentInfo(
        int(environment.get("environment_issue_count") or 0),
        int(environment.get("water_issue_count") or 0),
        str(environment.get("rectification_status") or ""),
        int(environment.get("monitoring_abnormal_count") or 0),
        str(environment["period"]),
    )
    resource_info = ResourceInfo(
        int(resource.get("person_count") or 0),
        int(resource.get("equipment_count") or 0),
        str(resource.get("equipment_type") or ""),
        str(resource["period"]),
    )
    result = AnalysisResult(
        document=DocumentDescriptor(
            str(document["file_type"]),
            str(document["report_period"]),
            _number(document.get("confidence_score")),
        ),
        summary=SummaryPayload(
            str(document.get("summary_text") or ""),
            [item.work_content for item in progress_items],
            [item.supervision_focus for item in progress_items if item.supervision_focus],
        ),
        data=AnalysisData(project_info, progress_items, safety_info, environment_info, resource_info),
        review=ReviewInfo([], "completed"),
    )
    created_at = document.get("created_at")
    return AnalysisRecord(
        id=int(document["id"]),
        source_file_id=int(document["source_file_id"]),
        file_name=str(document["file_name"]),
        file_type=str(document["file_type"]),
        project_name=str(document["project_name"]),
        report_period=str(document["report_period"]),
        analysis_status=str(document["analysis_status"]),  # type: ignore[arg-type]
        summary_text=str(document.get("summary_text") or ""),
        confidence_score=_number(document.get("confidence_score")),
        ingestion_status=str(document.get("ingestion_status") or "pending"),
        excluded_from_dashboard=bool(document.get("excluded_from_dashboard", 1)),
        created_at=created_at.strftime("%Y-%m-%d %H:%M:%S") if hasattr(created_at, "strftime") else str(created_at),
        result=result,
    )


_memory_repository = MemoryAnalysisRepository()


def _validate_payload(payload: dict) -> tuple[int, str]:
    file_id = payload.get("fileId", payload.get("file_id"))
    if isinstance(file_id, bool):
        raise ValueError("fileId 必须为正整数")
    try:
        source_file_id = int(file_id)
    except (TypeError, ValueError) as exc:
        raise ValueError("fileId 必须为正整数") from exc
    if source_file_id <= 0:
        raise ValueError("fileId 必须为正整数")
    file_name = str(payload.get("fileName") or payload.get("file_name") or "").strip()
    if len(file_name) > 500:
        raise ValueError("fileName 长度不能超过 500 个字符")
    return source_file_id, file_name


def analyze_document(payload: dict, repository: AnalysisRepository | None = None) -> dict:
    source_file_id, requested_name = _validate_payload(payload)
    file_name, result = build_analysis_result(source_file_id, requested_name)

    if repository is not None:
        record = repository.save(source_file_id, file_name, result)
        return record.to_api_dict(repository.storage_mode)

    mysql_repository = MySQLAnalysisRepository()
    try:
        record = mysql_repository.save(source_file_id, file_name, result)
        return record.to_api_dict(mysql_repository.storage_mode)
    except Exception as exc:
        record = _memory_repository.save(source_file_id, file_name, result)
        payload_result = record.to_api_dict(_memory_repository.storage_mode)
        payload_result["storage_notice"] = f"MySQL AI 解析表暂不可用，结果仅保留在当前服务进程：{type(exc).__name__}"
        return payload_result


def get_analysis_result(analysis_id: int, repository: AnalysisRepository | None = None) -> dict | None:
    if analysis_id <= 0:
        raise ValueError("文档解析 ID 必须为正整数")

    if repository is not None:
        record = repository.get(analysis_id)
        return record.to_api_dict(repository.storage_mode) if record else None

    mysql_repository = MySQLAnalysisRepository()
    try:
        record = mysql_repository.get(analysis_id)
        if record is not None:
            return record.to_api_dict(mysql_repository.storage_mode)
    except Exception:
        pass
    record = _memory_repository.get(analysis_id)
    return record.to_api_dict(_memory_repository.storage_mode) if record else None
