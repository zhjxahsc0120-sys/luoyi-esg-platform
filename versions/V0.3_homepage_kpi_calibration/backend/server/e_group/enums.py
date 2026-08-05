"""
E组公共闭环 & E01 V1.1 枚举常量模块

包含所有 V1.1 DDL 中 CHECK 约束定义的枚举值、
状态转换矩阵、动作码常量及校验辅助函数。
"""

from __future__ import annotations

from enum import Enum
from typing import Final


# ---------------------------------------------------------------------------
# 闭环事项状态 (e_closure_case.current_status)
# ---------------------------------------------------------------------------
class CaseStatus(str, Enum):
    DISCOVERED = "DISCOVERED"
    PENDING_RECTIFICATION = "PENDING_RECTIFICATION"
    RECTIFYING = "RECTIFYING"
    PENDING_REVIEW = "PENDING_REVIEW"
    PENDING_CLOSURE = "PENDING_CLOSURE"
    CLOSED = "CLOSED"
    CANCELLED = "CANCELLED"
    MERGED = "MERGED"
    SUSPENDED = "SUSPENDED"


# ---------------------------------------------------------------------------
# 事项域 (e_closure_case.case_domain)
# ---------------------------------------------------------------------------
class CaseDomain(str, Enum):
    E01_EXCEED = "E01_EXCEED"
    E02_ENV = "E02_ENV"
    E03_WATER = "E03_WATER"


# ---------------------------------------------------------------------------
# 数据性质 (通用 data_nature 字段)
# ---------------------------------------------------------------------------
class DataNature(str, Enum):
    FORMAL = "formal"
    DEMO = "demo"
    PLATFORM_CALC = "platform_calc"


# ---------------------------------------------------------------------------
# 生效状态 (通用 effective_status 字段)
# ---------------------------------------------------------------------------
class EffectiveStatus(str, Enum):
    DRAFT = "DRAFT"
    PENDING_REVIEW = "PENDING_REVIEW"
    EFFECTIVE = "EFFECTIVE"
    INVALID = "INVALID"


# ---------------------------------------------------------------------------
# 核验状态 (通用 verification_status 字段)
# ---------------------------------------------------------------------------
class VerificationStatus(str, Enum):
    PENDING_REVIEW = "PENDING_REVIEW"
    VERIFIED = "VERIFIED"
    REJECTED = "REJECTED"


# ---------------------------------------------------------------------------
# 结果有效性 (e01_factor_result.result_validity)
# ---------------------------------------------------------------------------
class ResultValidity(str, Enum):
    VALID = "VALID"
    VOID = "VOID"
    DUPLICATE = "DUPLICATE"


# ---------------------------------------------------------------------------
# 因子判定 (e01_factor_result.judgement)
# ---------------------------------------------------------------------------
class Judgement(str, Enum):
    EXCEEDED = "EXCEEDED"
    COMPLIANT = "COMPLIANT"
    NO_JUDGEMENT = "NO_JUDGEMENT"


# ---------------------------------------------------------------------------
# 判定来源 (e01_factor_result.judgement_source)
# ---------------------------------------------------------------------------
class JudgementSource(str, Enum):
    REPORT = "REPORT"
    PLATFORM_CALC = "PLATFORM_CALC"
    MANUAL_REVIEW = "MANUAL_REVIEW"


# ---------------------------------------------------------------------------
# 检测阶段 (e01_factor_result.test_stage)
# ---------------------------------------------------------------------------
class TestStage(str, Enum):
    INITIAL = "INITIAL"
    RETEST = "RETEST"


# ---------------------------------------------------------------------------
# 证据角色 (e_case_evidence.evidence_role)
# ---------------------------------------------------------------------------
class EvidenceRole(str, Enum):
    FORMAL_NOTICE = "FORMAL_NOTICE"
    INITIAL_REPORT = "INITIAL_REPORT"
    RAW_RECORD = "RAW_RECORD"
    RECTIFICATION_MATERIAL = "RECTIFICATION_MATERIAL"
    RETEST_REPORT = "RETEST_REPORT"
    REVIEW_OPINION = "REVIEW_OPINION"
    CLOSURE_DOCUMENT = "CLOSURE_DOCUMENT"
    CANCELLATION_DOCUMENT = "CANCELLATION_DOCUMENT"


# ---------------------------------------------------------------------------
# 参与方角色 (e_case_party.party_role)
# ---------------------------------------------------------------------------
class PartyRole(str, Enum):
    DISCOVERER = "DISCOVERER"
    RESPONSIBLE = "RESPONSIBLE"
    HANDLER = "HANDLER"
    REVIEWER = "REVIEWER"
    CLOSER = "CLOSER"
    TEST_PROVIDER = "TEST_PROVIDER"


# ---------------------------------------------------------------------------
# 事项关系类型 (e_case_relation.relation_type)
# ---------------------------------------------------------------------------
class CaseRelationType(str, Enum):
    RELATED = "RELATED"
    DUPLICATE_OF = "DUPLICATE_OF"
    MERGED_INTO = "MERGED_INTO"
    SAME_TASK = "SAME_TASK"


# ---------------------------------------------------------------------------
# 监测类别 (monitor_category 字段)
# ---------------------------------------------------------------------------
class MonitorCategory(str, Enum):
    WATER = "WATER"
    AIR = "AIR"
    NOISE = "NOISE"


class MonitorFrequencyCode(str, Enum):
    CONTINUOUS = "CONTINUOUS"
    DAILY = "DAILY"
    WEEKLY = "WEEKLY"
    MONTHLY = "MONTHLY"
    QUARTERLY = "QUARTERLY"
    EVENT_TRIGGERED = "EVENT_TRIGGERED"


# ---------------------------------------------------------------------------
# 整改任务状态 (e_rectification_task.task_status)
# ---------------------------------------------------------------------------
class TaskStatus(str, Enum):
    PENDING = "PENDING"
    IN_PROGRESS = "IN_PROGRESS"
    SUBMITTED = "SUBMITTED"
    REVIEWED = "REVIEWED"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"


# ---------------------------------------------------------------------------
# 复测结论 (e01_retest_round.outcome / e01_exceed_event.latest_retest_outcome)
# ---------------------------------------------------------------------------
class RetestOutcome(str, Enum):
    COMPLIANT = "COMPLIANT"
    STILL_EXCEEDED = "STILL_EXCEEDED"
    NO_JUDGEMENT = "NO_JUDGEMENT"


# ---------------------------------------------------------------------------
# 复测审核状态 (e01_retest_round.review_status)
# ---------------------------------------------------------------------------
class RetestReviewStatus(str, Enum):
    PENDING_REVIEW = "PENDING_REVIEW"
    PASSED = "PASSED"
    REJECTED = "REJECTED"


# ---------------------------------------------------------------------------
# 轨迹转换结果 (e_case_status_history.transition_result)
# ---------------------------------------------------------------------------
class TransitionResult(str, Enum):
    SUCCESS = "SUCCESS"
    REJECTED = "REJECTED"
    RETURNED = "RETURNED"
    CORRECTION = "CORRECTION"


# ---------------------------------------------------------------------------
# 批次状态 (e01_monitor_batch.batch_status)
# ---------------------------------------------------------------------------
class BatchStatus(str, Enum):
    DRAFT = "DRAFT"
    PARSED = "PARSED"
    VALIDATED = "VALIDATED"
    PENDING_REVIEW = "PENDING_REVIEW"
    EFFECTIVE = "EFFECTIVE"
    REJECTED = "REJECTED"
    INVALID = "INVALID"


# ---------------------------------------------------------------------------
# 采样状态 (e01_monitor_sample.sample_status)
# ---------------------------------------------------------------------------
class SampleStatus(str, Enum):
    VALID = "VALID"
    PENDING_REVIEW = "PENDING_REVIEW"
    VOID = "VOID"
    DUPLICATE = "DUPLICATE"


# ---------------------------------------------------------------------------
# 证据有效性状态 (e_case_evidence.validity_status)
# ---------------------------------------------------------------------------
class EvidenceValidityStatus(str, Enum):
    VALID = "VALID"
    SUPERSEDED = "SUPERSEDED"
    INVALID = "INVALID"


# ---------------------------------------------------------------------------
# 坐标来源类型 (e01_monitor_point.coordinate_source_type)
# ---------------------------------------------------------------------------
class CoordinateSourceType(str, Enum):
    NONE = "NONE"
    DOCUMENT = "DOCUMENT"
    GIS = "GIS"
    GPS = "GPS"
    MANUAL = "MANUAL"


# ---------------------------------------------------------------------------
# 坐标核验状态 (e01_monitor_point.coordinate_verification_status)
# ---------------------------------------------------------------------------
class CoordinateVerificationStatus(str, Enum):
    NOT_PROVIDED = "NOT_PROVIDED"
    PENDING_REVIEW = "PENDING_REVIEW"
    VERIFIED = "VERIFIED"
    REJECTED = "REJECTED"


# ---------------------------------------------------------------------------
# 计划条目执行状态 (e01_monitor_plan_item.execution_status)
# ---------------------------------------------------------------------------
class ExecutionStatus(str, Enum):
    PENDING = "PENDING"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"


# ---------------------------------------------------------------------------
# 计划状态 (e01_monitor_plan.plan_status)
# ---------------------------------------------------------------------------
class PlanStatus(str, Enum):
    DRAFT = "DRAFT"
    PENDING_REVIEW = "PENDING_REVIEW"
    EFFECTIVE = "EFFECTIVE"
    INVALID = "INVALID"


# ---------------------------------------------------------------------------
# 监测点位活跃状态 (e01_monitor_point.active_status)
# ---------------------------------------------------------------------------
class ActiveStatus(str, Enum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"


# ---------------------------------------------------------------------------
# 旧表映射状态 (e01_legacy_record_mapping.mapping_status)
# ---------------------------------------------------------------------------
class MappingStatus(str, Enum):
    MAPPED = "MAPPED"
    AGGREGATE_ONLY = "AGGREGATE_ONLY"
    UNMAPPABLE = "UNMAPPABLE"
    EXCLUDED = "EXCLUDED"


# ---------------------------------------------------------------------------
# 对账分类 (e01_legacy_record_mapping.reconciliation_class)
# ---------------------------------------------------------------------------
class ReconciliationClass(str, Enum):
    TOTAL_MATCH = "TOTAL_MATCH"
    ROW_MAPPABLE = "ROW_MAPPABLE"
    AGGREGATE_MAPPABLE = "AGGREGATE_MAPPABLE"
    UNMAPPABLE = "UNMAPPABLE"
    EXPECTED_DIFFERENCE_DEMO_EXCLUDED = "EXPECTED_DIFFERENCE_DEMO_EXCLUDED"
    EXPECTED_DIFFERENCE_INVALID_EXCLUDED = "EXPECTED_DIFFERENCE_INVALID_EXCLUDED"


# ---------------------------------------------------------------------------
# 案件-整改关联角色 (e_case_rectification_link.link_role)
# ---------------------------------------------------------------------------
class CaseRectLinkRole(str, Enum):
    PRIMARY = "PRIMARY"
    SECONDARY = "SECONDARY"


# ---------------------------------------------------------------------------
# 迁移历史状态 (esg_schema_migration_history.status)
# ---------------------------------------------------------------------------
class MigrationExecutionStatus(str, Enum):
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
    SKIPPED = "SKIPPED"


# ---------------------------------------------------------------------------
# 超标事件最新复测结论 (e01_exceed_event.latest_retest_outcome) 额外值
# ---------------------------------------------------------------------------
class EventLatestRetestOutcome(str, Enum):
    NOT_TESTED = "NOT_TESTED"
    COMPLIANT = "COMPLIANT"
    STILL_EXCEEDED = "STILL_EXCEEDED"
    NO_JUDGEMENT = "NO_JUDGEMENT"


# ===========================================================================
# 动作码常量 — 状态机操作
# ===========================================================================

# 案件生命周期动作码
ACTION_CREATE_CASE: Final = "CREATE_CASE"
ACTION_ISSUE_RECTIFICATION: Final = "ISSUE_RECTIFICATION"
ACTION_START_RECTIFICATION: Final = "START_RECTIFICATION"
ACTION_SUBMIT_RECTIFICATION: Final = "SUBMIT_RECTIFICATION"
ACTION_REVIEW_REJECT: Final = "REVIEW_REJECT"
ACTION_REVIEW_PASS: Final = "REVIEW_PASS"
ACTION_CLOSE_CASE: Final = "CLOSE_CASE"
ACTION_CLOSURE_REJECT: Final = "CLOSURE_REJECT"
ACTION_REOPEN_CASE: Final = "REOPEN_CASE"
ACTION_SUSPEND_CASE: Final = "SUSPEND_CASE"
ACTION_RESUME_CASE: Final = "RESUME_CASE"
ACTION_CANCEL_CASE: Final = "CANCEL_CASE"
ACTION_MERGE_CASE: Final = "MERGE_CASE"

# 历史纠正动作码
ACTION_CORRECT_HISTORY: Final = "CORRECT_HISTORY"


# ===========================================================================
# 状态转换矩阵
# ===========================================================================

# (from_status, action_code) -> to_status
# from_status 为 None 表示初始创建
CASE_TRANSITION_MATRIX: dict[tuple[str | None, str], str] = {
    # 初始创建
    (None, ACTION_CREATE_CASE): CaseStatus.DISCOVERED,
    # 正向流转
    (CaseStatus.DISCOVERED, ACTION_ISSUE_RECTIFICATION): CaseStatus.PENDING_RECTIFICATION,
    (CaseStatus.PENDING_RECTIFICATION, ACTION_START_RECTIFICATION): CaseStatus.RECTIFYING,
    (CaseStatus.RECTIFYING, ACTION_SUBMIT_RECTIFICATION): CaseStatus.PENDING_REVIEW,
    (CaseStatus.PENDING_REVIEW, ACTION_REVIEW_PASS): CaseStatus.PENDING_CLOSURE,
    (CaseStatus.PENDING_CLOSURE, ACTION_CLOSE_CASE): CaseStatus.CLOSED,
    # 退回
    (CaseStatus.PENDING_REVIEW, ACTION_REVIEW_REJECT): CaseStatus.RECTIFYING,
    (CaseStatus.PENDING_CLOSURE, ACTION_CLOSURE_REJECT): CaseStatus.RECTIFYING,
    # 重新打开
    (CaseStatus.CLOSED, ACTION_REOPEN_CASE): CaseStatus.RECTIFYING,
}


# ---------------------------------------------------------------------------
# 特殊动作码集合：需要服务层额外处理
# ---------------------------------------------------------------------------

# SUSPEND 需要存储上一状态（保存到 history.comment 或扩展字段），
# RESUME 需要恢复到 SUSPEND 前的状态
# CANCEL / MERGE 可以从多个非终态出发

# 终态集合
TERMINAL_STATUSES: frozenset[str] = frozenset({
    CaseStatus.CLOSED,
    CaseStatus.CANCELLED,
    CaseStatus.MERGED,
})

# 非终态集合（终态以外 + SUSPENDED 本身也是非终态）
NON_TERMINAL_STATUSES: frozenset[str] = frozenset({
    CaseStatus.DISCOVERED,
    CaseStatus.PENDING_RECTIFICATION,
    CaseStatus.RECTIFYING,
    CaseStatus.PENDING_REVIEW,
    CaseStatus.PENDING_CLOSURE,
    CaseStatus.SUSPENDED,
})

# 允许 SUSPEND 的状态
SUSPENDABLE_STATUSES: frozenset[str] = frozenset({
    CaseStatus.DISCOVERED,
    CaseStatus.PENDING_RECTIFICATION,
    CaseStatus.RECTIFYING,
    CaseStatus.PENDING_REVIEW,
    CaseStatus.PENDING_CLOSURE,
    CaseStatus.SUSPENDED,
})

# 允许 CANCEL 的状态
CANCELLABLE_STATUSES: frozenset[str] = frozenset({
    CaseStatus.DISCOVERED,
    CaseStatus.PENDING_RECTIFICATION,
    CaseStatus.RECTIFYING,
    CaseStatus.PENDING_REVIEW,
    CaseStatus.PENDING_CLOSURE,
    CaseStatus.SUSPENDED,
})

# 允许 MERGE 的状态（合并方必须是非终态，被合并方进入 MERGED 终态）
MERGEABLE_STATUSES: frozenset[str] = frozenset({
    CaseStatus.DISCOVERED,
    CaseStatus.PENDING_RECTIFICATION,
    CaseStatus.RECTIFYING,
    CaseStatus.PENDING_REVIEW,
    CaseStatus.PENDING_CLOSURE,
    CaseStatus.SUSPENDED,
})

# 允许 REOPEN 的状态（仅从 CLOSED）
REOPENABLE_STATUSES: frozenset[str] = frozenset({
    CaseStatus.CLOSED,
})


# ===========================================================================
# source_table 白名单（e_closure_case.source_table 允许值）
# ===========================================================================

E01_SOURCE_TABLE: Final = "e01_factor_result"


# ===========================================================================
# 校验辅助函数
# ===========================================================================


def validate_data_nature_consistency(data_nature: str, is_demo: int) -> bool:
    """校验 data_nature 和 is_demo 的一致性。

    规则：
      - data_nature='demo'   => is_demo=1
      - data_nature='formal' / 'platform_calc' => is_demo=0

    Args:
        data_nature: 数据性质字符串。
        is_demo: 0 或 1。

    Returns:
        一致性校验通过返回 True，否则返回 False。
    """
    if data_nature == DataNature.DEMO and is_demo != 1:
        return False
    if data_nature in (DataNature.FORMAL, DataNature.PLATFORM_CALC) and is_demo != 0:
        return False
    return True


def is_formal_kpi_eligible(
    data_nature: str,
    is_demo: int,
    effective_status: str,
    result_validity: str | None = None,
    verification_status: str | None = None,
) -> bool:
    """判断是否满足正式 KPI 统计条件。

    正式 KPI 统计需要同时满足：
      1. data_nature='formal'
      2. is_demo=0
      3. effective_status='EFFECTIVE'
      4.（可选）result_validity='VALID'
      5.（可选）verification_status='VERIFIED'

    Args:
        data_nature: 数据性质。
        is_demo: 是否演示数据。
        effective_status: 生效状态。
        result_validity: 结果有效性（传入时额外校验）。
        verification_status: 核验状态（传入时额外校验）。

    Returns:
        满足全部条件返回 True，否则返回 False。
    """
    if data_nature != DataNature.FORMAL:
        return False
    if is_demo != 0:
        return False
    if effective_status != EffectiveStatus.EFFECTIVE:
        return False
    if result_validity is not None and result_validity != ResultValidity.VALID:
        return False
    if verification_status is not None and verification_status != VerificationStatus.VERIFIED:
        return False
    return True
