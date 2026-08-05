"""ESG-AI-DATA-001 数据模型与接口返回模型。

本模块只描述新建的 AI 解析业务数据，不依赖 E01/E02/E03、碳核算、地图或首页 KPI 表。
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Literal


AnalysisStatus = Literal["uploaded", "processing", "completed", "review", "failed"]


@dataclass(frozen=True)
class DocumentDescriptor:
    type: str
    period: str
    confidence: float


@dataclass(frozen=True)
class SummaryPayload:
    overview: str
    key_work: list[str] = field(default_factory=list)
    risk_focus: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class ProjectInfo:
    project_name: str
    construction_stage: str
    route_length: float
    section_count: int
    professional_type_count: int
    period: str


@dataclass(frozen=True)
class ProgressItem:
    section_code: str
    work_type: str
    work_content: str
    supervision_focus: str
    period: str


@dataclass(frozen=True)
class SafetyInfo:
    safe_days: int
    risk_point_count: int
    unfinished_issue_count: int
    inspection_count: int
    period: str


@dataclass(frozen=True)
class EnvironmentInfo:
    environment_issue_count: int
    water_issue_count: int
    rectification_status: str
    monitoring_abnormal_count: int
    period: str


@dataclass(frozen=True)
class ResourceInfo:
    person_count: int
    equipment_count: int
    equipment_type: str
    period: str


@dataclass(frozen=True)
class ReviewInfo:
    need_confirm: list[str] = field(default_factory=list)
    status: str = "completed"


@dataclass(frozen=True)
class AnalysisData:
    project_info: ProjectInfo
    progress: list[ProgressItem]
    safety: SafetyInfo
    environment: EnvironmentInfo
    resource: ResourceInfo


@dataclass(frozen=True)
class AnalysisResult:
    document: DocumentDescriptor
    summary: SummaryPayload
    data: AnalysisData
    review: ReviewInfo = field(default_factory=ReviewInfo)

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass(frozen=True)
class AnalysisRecord:
    id: int
    source_file_id: int
    file_name: str
    file_type: str
    project_name: str
    report_period: str
    analysis_status: AnalysisStatus
    summary_text: str
    confidence_score: float
    ingestion_status: str
    excluded_from_dashboard: bool
    created_at: str
    result: AnalysisResult

    def to_api_dict(self, storage_mode: str) -> dict:
        payload = self.result.to_dict()
        payload.update(
            {
                "analysis_id": self.id,
                "source_file_id": self.source_file_id,
                "file_name": self.file_name,
                "analysis_status": self.analysis_status,
                "ingestion_status": self.ingestion_status,
                "excluded_from_dashboard": self.excluded_from_dashboard,
                "created_at": self.created_at,
                "storage_mode": storage_mode,
            }
        )
        return payload
