"""E组公共闭环事务服务层骨架。

V1.1 只建立骨架和校验方法，不接入现有正式接口。
所有方法接收 conn (pymysql.connections.Connection) 参数，
由调用方管理事务边界。
"""

from __future__ import annotations

import json
from datetime import datetime
from decimal import Decimal
from typing import Any, Optional

from .enums import (
    CaseStatus, DataNature, EffectiveStatus, TestStage,
    Judgement, ResultValidity, RetestOutcome, RetestReviewStatus,
    TransitionResult, validate_data_nature_consistency,
    TERMINAL_STATUSES, CASE_TRANSITION_MATRIX,
    E01_SOURCE_TABLE, NON_TERMINAL_STATUSES,
    SUSPENDABLE_STATUSES, CANCELLABLE_STATUSES, MERGEABLE_STATUSES,
    REOPENABLE_STATUSES,
    # 动作码
    ACTION_CREATE_CASE,
    ACTION_ISSUE_RECTIFICATION,
    ACTION_START_RECTIFICATION,
    ACTION_SUBMIT_RECTIFICATION,
    ACTION_REVIEW_REJECT,
    ACTION_REVIEW_PASS,
    ACTION_CLOSE_CASE,
    ACTION_CLOSURE_REJECT,
    ACTION_REOPEN_CASE,
    ACTION_SUSPEND_CASE,
    ACTION_RESUME_CASE,
    ACTION_CANCEL_CASE,
    ACTION_MERGE_CASE,
    ACTION_CORRECT_HISTORY,
)


class CaseTransitionError(Exception):
    """状态转换校验失败"""
    pass


class OptimisticLockError(Exception):
    """乐观锁冲突"""
    pass


class IdempotencyConflictError(Exception):
    """幂等请求号冲突"""
    pass


class CorrectionTargetError(Exception):
    """纠错目标不是当前最终轨迹"""
    pass


class RetestChainError(Exception):
    """复测链校验失败"""
    pass


class DataNatureConsistencyError(Exception):
    """数据性质不一致"""
    pass


# ============================================================================
# SQL 常量 —— 供骨架方法使用
# ============================================================================

# ---- lock_case_for_transition ----
SQL_LOCK_CASE = """
SELECT
    id, case_code, case_domain, source_table, source_record_id,
    source_business_key, title, current_status, current_status_history_id,
    data_nature, is_demo, row_version,
    merged_into_case_id
FROM e_closure_case
WHERE id = %s
FOR UPDATE
"""

# ---- get_current_effective_history ----
SQL_GET_CURRENT_LEAF_HISTORY = """
SELECT h.id, h.sequence_no, h.from_status, h.to_status,
       h.action_code, h.transition_result, h.action_at,
       h.correction_of_history_id, h.data_nature, h.is_demo
FROM e_case_status_history h
WHERE h.case_id = %s
  AND h.id NOT IN (
      SELECT DISTINCT correction_of_history_id
      FROM e_case_status_history
      WHERE case_id = %s
        AND correction_of_history_id IS NOT NULL
        AND effective_status = 'EFFECTIVE'
  )
ORDER BY h.sequence_no DESC
LIMIT 1
"""

# ---- append_status_history ----
SQL_INSERT_STATUS_HISTORY = """
INSERT INTO e_case_status_history (
    case_id, sequence_no, from_status, to_status, action_code,
    transition_result, action_at, operator_id, operator_name,
    operator_org_id, operator_org_name, comment,
    source_document_id, correction_of_history_id,
    data_nature, is_demo, client_request_id
) VALUES (
    %s, %s, %s, %s, %s,
    %s, %s, %s, %s,
    %s, %s, %s,
    %s, %s,
    %s, %s, %s
)
"""

# ---- update_case_status (在 execute_case_transition 中) ----
SQL_UPDATE_CASE_AFTER_TRANSITION = """
UPDATE e_closure_case
SET current_status = %s,
    current_status_history_id = %s,
    row_version = row_version + 1,
    updated_at = NOW(6)
WHERE id = %s
  AND row_version = %s
"""

# ---- update_case_closed_fields ----
SQL_UPDATE_CASE_CLOSED_FIELDS = """
UPDATE e_closure_case
SET closed_at = %s,
    closure_reason = %s,
    row_version = row_version + 1,
    updated_at = NOW(6)
WHERE id = %s
"""

# ---- update_case_merged_fields ----
SQL_UPDATE_CASE_MERGED_FIELDS = """
UPDATE e_closure_case
SET merged_into_case_id = %s,
    row_version = row_version + 1,
    updated_at = NOW(6)
WHERE id = %s
"""

# ---- check_idempotency ----
SQL_CHECK_IDEMPOTENCY = """
SELECT id
FROM e_case_status_history
WHERE case_id = %s
  AND client_request_id = %s
LIMIT 1
"""

# ---- validate_single_effective_event_per_result ----
SQL_CHECK_EVENT_PER_RESULT = """
SELECT id
FROM e01_exceed_event
WHERE original_result_id = %s
  AND data_nature = %s
  AND is_demo = %s
  AND effective_status = 'EFFECTIVE'
LIMIT 1
"""

# ---- validate_chain_data_nature (result -> sample -> batch -> point) ----
SQL_RESULT_SAMPLE_CHAIN = """
SELECT r.data_nature AS result_nature, r.is_demo AS result_demo,
       s.data_nature AS sample_nature, s.is_demo AS sample_demo,
       b.data_nature AS batch_nature, b.is_demo AS batch_demo,
       p.data_nature AS point_nature, p.is_demo AS point_demo
FROM e01_factor_result r
JOIN e01_monitor_sample s ON s.id = r.sample_id
JOIN e01_monitor_batch b ON b.id = s.batch_id
JOIN e01_monitor_point p ON p.id = s.point_id
WHERE r.id = %s
LIMIT 1
"""

# ---- validate_retest_result_link checks ----
SQL_RETEST_RESULT_INFO = """
SELECT test_stage, sample_id, factor_id, data_nature, is_demo
FROM e01_factor_result
WHERE id = %s
LIMIT 1
"""

SQL_ORIGINAL_RESULT_INFO = """
SELECT id, test_stage, judgement, result_validity, effective_status,
       sample_id, factor_id, data_nature, is_demo
FROM e01_factor_result
WHERE id = %s
LIMIT 1
"""

SQL_EVENT_INFO = """
SELECT original_result_id, data_nature, is_demo
FROM e01_exceed_event
WHERE id = %s
LIMIT 1
"""

SQL_RETEST_ROUND_INFO = """
SELECT retest_batch_id, event_id, data_nature, is_demo
FROM e01_retest_round
WHERE id = %s
LIMIT 1
"""

SQL_RETEST_RESULT_EXISTS = """
SELECT id
FROM e01_retest_result_link
WHERE factor_result_id = %s
LIMIT 1
"""

# ---- validate_retest_round_caches ----
SQL_LATEST_RETEST_ROUND = """
SELECT round_no, outcome, review_status
FROM e01_retest_round
WHERE event_id = %s
  AND effective_status = 'EFFECTIVE'
  AND data_nature = %s
  AND is_demo = %s
ORDER BY round_no DESC
LIMIT 1
"""

# ---- validate_closure_prerequisites ----
SQL_LAST_RETEST_OUTCOME = """
SELECT outcome, review_status
FROM e01_retest_round
WHERE event_id = %s
  AND effective_status = 'EFFECTIVE'
ORDER BY round_no DESC
LIMIT 1
"""

SQL_HAS_REVIEW_PASS_HISTORY = """
SELECT id
FROM e_case_status_history
WHERE case_id = %s
  AND action_code = 'REVIEW_PASS'
  AND transition_result = 'SUCCESS'
LIMIT 1
"""

SQL_HAS_CLOSE_CASE_HISTORY = """
SELECT id
FROM e_case_status_history
WHERE case_id = %s
  AND action_code = 'CLOSE_CASE'
  AND transition_result = 'SUCCESS'
LIMIT 1
"""

SQL_HAS_CLOSURE_EVIDENCE = """
SELECT id
FROM e_case_evidence
WHERE case_id = %s
  AND evidence_role = 'CLOSURE_DOCUMENT'
  AND validity_status = 'VALID'
  AND is_current = 1
LIMIT 1
"""

# ---- validate_e01_event_chain: result info ----
SQL_E01_RESULT_DETAIL = """
SELECT r.id, r.test_stage, r.judgement, r.result_validity,
       r.effective_status, r.data_nature, r.is_demo,
       r.sample_id, r.factor_id, r.standard_version_id,
       s.batch_id, s.point_id, s.monitor_category AS sample_category,
       b.quarter_code, p.monitor_category AS point_category,
       p.data_nature AS point_nature, p.is_demo AS point_demo
FROM e01_factor_result r
JOIN e01_monitor_sample s ON s.id = r.sample_id
JOIN e01_monitor_batch b ON b.id = s.batch_id
JOIN e01_monitor_point p ON p.id = s.point_id
WHERE r.id = %s
LIMIT 1
"""


# ============================================================================
# 事项状态流转服务
# ============================================================================


def lock_case_for_transition(
    conn,
    case_id: int,
    expected_row_version: int,
) -> dict:
    """锁定事项并返回当前状态快照。

    使用 SELECT ... FOR UPDATE 锁定行，
    校验 row_version 匹配后返回事项当前状态。

    Args:
        conn: PyMySQL 数据库连接，调用方负责事务管理。
        case_id: 事项 ID。
        expected_row_version: 预期的行版本号（乐观锁）。

    Returns:
        包含事项当前快照的字典，键包括 id, case_code, case_domain,
        current_status, current_status_history_id, row_version 等。

    Raises:
        OptimisticLockError: row_version 不匹配。
        LookupError: 事项不存在。
    """
    # SQL: SQL_LOCK_CASE
    # cursor = conn.cursor()
    # cursor.execute(SQL_LOCK_CASE, (case_id,))
    # row = cursor.fetchone()
    #
    # if row is None:
    #     raise LookupError(f"Case {case_id} not found")
    #
    # locked_case = dict_from_row(cursor.description, row)
    #
    # if locked_case['row_version'] != expected_row_version:
    #     raise OptimisticLockError(
    #         f"OPTIMISTIC_LOCK: case_id={case_id}, "
    #         f"expected_version={expected_row_version}, "
    #         f"actual_version={locked_case['row_version']}"
    #     )
    #
    # return locked_case
    raise NotImplementedError("需要数据库连接")


def get_current_effective_history(conn, case_id: int) -> dict | None:
    """获取事项的当前有效历史轨迹。

    算法：
    1. 查询未被后续更正轨迹指向的叶子
    2. 取最大 sequence_no 的叶子

    Args:
        conn: PyMySQL 数据库连接。
        case_id: 事项 ID。

    Returns:
        当前有效历史轨迹字典，或 None（无历史记录）。
    """
    # SQL: SQL_GET_CURRENT_LEAF_HISTORY
    # cursor = conn.cursor()
    # cursor.execute(SQL_GET_CURRENT_LEAF_HISTORY, (case_id, case_id))
    # row = cursor.fetchone()
    #
    # if row is None:
    #     return None
    #
    # return dict_from_row(cursor.description, row)
    raise NotImplementedError("需要数据库连接")


def validate_transition(
    current_status: str | None,
    action_code: str,
    case_domain: str,
    data_nature: str,
    **kwargs,
) -> str:
    """校验状态转换是否合法，返回目标状态。

    规则：
    - CREATE_CASE: current_status 必须为 None
    - 正常流转: 查 CASE_TRANSITION_MATRIX
    - SUSPEND_CASE: 必须在 SUSPENDABLE_STATUSES 中
    - RESUME_CASE: 当前必须为 SUSPENDED
    - CANCEL_CASE: 必须在 CANCELLABLE_STATUSES 中
    - MERGE_CASE: 必须在 MERGEABLE_STATUSES 中，需 merged_into_case_id
    - CORRECT_HISTORY: 特殊处理

    Args:
        current_status: 当前状态，创建时为 None。
        action_code: 动作码。
        case_domain: 事项域（E01_EXCEED 等）。
        data_nature: 数据性质。
        **kwargs: 额外参数（如 merged_into_case_id）。

    Returns:
        目标状态字符串。

    Raises:
        CaseTransitionError: 转换不合法。
    """
    # --- CREATE_CASE ---
    if action_code == ACTION_CREATE_CASE:
        if current_status is not None:
            raise CaseTransitionError(
                f"CREATE_CASE requires current_status=None, "
                f"got {current_status}"
            )
        return CaseStatus.DISCOVERED

    # --- CORRECT_HISTORY ---
    if action_code == ACTION_CORRECT_HISTORY:
        # 纠错会指向当前最终轨迹，目标状态取决于纠错逻辑
        # 服务层在 execute_case_transition 中额外处理纠错目标校验
        return current_status  # 纠错保持当前状态，创建纠正轨迹

    # --- SUSPEND_CASE ---
    if action_code == ACTION_SUSPEND_CASE:
        if current_status not in SUSPENDABLE_STATUSES:
            raise CaseTransitionError(
                f"SUSPEND_CASE not allowed from {current_status}. "
                f"Must be one of {sorted(SUSPENDABLE_STATUSES)}"
            )
        return CaseStatus.SUSPENDED

    # --- RESUME_CASE ---
    if action_code == ACTION_RESUME_CASE:
        if current_status != CaseStatus.SUSPENDED:
            raise CaseTransitionError(
                f"RESUME_CASE requires current_status=SUSPENDED, "
                f"got {current_status}"
            )
        # RESUME 恢复到 SUSPEND 前的状态，
        # 需从 history.comment 或扩展字段中取出 pre_suspend_status
        pre_suspend_status = kwargs.get("pre_suspend_status")
        if pre_suspend_status is None:
            raise CaseTransitionError(
                "RESUME_CASE requires pre_suspend_status in kwargs"
            )
        if pre_suspend_status in TERMINAL_STATUSES:
            raise CaseTransitionError(
                f"Cannot resume to terminal status {pre_suspend_status}"
            )
        return pre_suspend_status

    # --- CANCEL_CASE ---
    if action_code == ACTION_CANCEL_CASE:
        if current_status not in CANCELLABLE_STATUSES:
            raise CaseTransitionError(
                f"CANCEL_CASE not allowed from {current_status}. "
                f"Must be one of {sorted(CANCELLABLE_STATUSES)}"
            )
        return CaseStatus.CANCELLED

    # --- MERGE_CASE ---
    if action_code == ACTION_MERGE_CASE:
        if current_status not in MERGEABLE_STATUSES:
            raise CaseTransitionError(
                f"MERGE_CASE not allowed from {current_status}. "
                f"Must be one of {sorted(MERGEABLE_STATUSES)}"
            )
        merged_into_case_id = kwargs.get("merged_into_case_id")
        if merged_into_case_id is None:
            raise CaseTransitionError(
                "MERGE_CASE requires merged_into_case_id in kwargs"
            )
        return CaseStatus.MERGED

    # --- 正常流转：查矩阵 ---
    key = (current_status, action_code)
    if key in CASE_TRANSITION_MATRIX:
        return CASE_TRANSITION_MATRIX[key]

    raise CaseTransitionError(
        f"No transition defined: from={current_status}, "
        f"action={action_code}"
    )


def append_status_history(
    conn,
    case_id: int,
    to_status: str,
    action_code: str,
    operator_id: int | None,
    operator_name: str | None,
    operator_org_id: int | None,
    operator_org_name: str | None,
    action_at: datetime,
    client_request_id: str,
    comment: str | None = None,
    source_document_id: int | None = None,
    correction_of_history_id: int | None = None,
    data_nature: str = 'formal',
    is_demo: int = 0,
    transition_result: str = 'SUCCESS',
) -> int:
    """追加一条状态历史轨迹。

    不更新任何既有历史记录。
    返回新插入的 history_id。

    Args:
        conn: PyMySQL 数据库连接。
        case_id: 事项 ID。
        to_status: 目标状态。
        action_code: 动作码。
        operator_id: 操作人 ID。
        operator_name: 操作人姓名。
        operator_org_id: 操作人组织 ID。
        operator_org_name: 操作人组织名称。
        action_at: 操作时间。
        client_request_id: 幂等请求号。
        comment: 备注。
        source_document_id: 来源文档 ID。
        correction_of_history_id: 纠错指向的历史 ID（仅 CORRECT_HISTORY）。
        data_nature: 数据性质。
        is_demo: 是否演示。
        transition_result: 转换结果。

    Returns:
        新插入的 history_id。

    Raises:
        IdempotencyConflictError: client_request_id 已存在。
    """
    # 1. 检查幂等
    # check_idempotency(conn, case_id, client_request_id)
    #
    # 2. 查询当前最大 sequence_no
    # cursor.execute(
    #     "SELECT COALESCE(MAX(sequence_no), 0) FROM e_case_status_history WHERE case_id=%s",
    #     (case_id,)
    # )
    # (max_seq,) = cursor.fetchone()
    # next_seq = max_seq + 1
    #
    # 3. 确定从状态
    # if action_code == ACTION_CREATE_CASE:
    #     from_status = None
    # elif action_code == ACTION_CORRECT_HISTORY:
    #     from_status = to_status  # 纠错从当前状态回到当前状态
    # else:
    #     from_status = locked_case['current_status']
    #
    # 4. 插入
    # cursor.execute(SQL_INSERT_STATUS_HISTORY, (
    #     case_id, next_seq, from_status, to_status, action_code,
    #     transition_result, action_at, operator_id, operator_name,
    #     operator_org_id, operator_org_name, comment,
    #     source_document_id, correction_of_history_id,
    #     data_nature, is_demo, client_request_id,
    # ))
    # return cursor.lastrowid
    raise NotImplementedError("需要数据库连接")


def execute_case_transition(
    conn,
    case_id: int,
    action_code: str,
    operator_id: int | None,
    operator_name: str | None,
    operator_org_id: int | None,
    operator_org_name: str | None,
    action_at: datetime,
    client_request_id: str,
    comment: str | None = None,
    source_document_id: int | None = None,
    expected_row_version: int | None = None,
    **kwargs,
) -> dict:
    """执行完整的状态转换事务。

    步骤：
    1. lock_case_for_transition
    2. validate_transition
    3. 纠错时校验 correction_of_history_id == current_status_history_id
    4. append_status_history
    5. UPDATE e_closure_case SET current_status, current_status_history_id,
       row_version=row_version+1
    6. 返回更新后快照

    纠错特殊处理：
    - CORRECT_HISTORY 必须指向锁定时的 current_status_history_id
    - 更正目标不等于当前最终轨迹时抛 CorrectionTargetError
    - 不更新被指向的旧轨迹

    Args:
        conn: PyMySQL 数据库连接。
        case_id: 事项 ID。
        action_code: 动作码。
        operator_id: 操作人 ID。
        operator_name: 操作人姓名。
        operator_org_id: 操作人组织 ID。
        operator_org_name: 操作人组织名称。
        action_at: 操作时间。
        client_request_id: 幂等请求号。
        comment: 备注。
        source_document_id: 来源文档 ID。
        expected_row_version: 预期行版本号。
        **kwargs: 额外参数。

    Returns:
        更新后的事项快照字典。

    Raises:
        CaseTransitionError: 状态转换不合法。
        OptimisticLockError: 乐观锁冲突。
        CorrectionTargetError: 纠错目标不是当前轨迹。
        IdempotencyConflictError: 幂等请求号冲突。
    """
    # Step 1: 锁定事项
    # locked = lock_case_for_transition(conn, case_id, expected_row_version)
    # current_status = locked['current_status']
    # current_history_id = locked['current_status_history_id']
    # data_nature = locked['data_nature']
    # is_demo = locked['is_demo']
    #
    # Step 2: 校验转换
    # to_status = validate_transition(
    #     current_status=current_status,
    #     action_code=action_code,
    #     case_domain=locked['case_domain'],
    #     data_nature=data_nature,
    #     **kwargs,
    # )
    #
    # Step 3: 纠错目标校验
    # correction_of_history_id = kwargs.get('correction_of_history_id')
    # if action_code == ACTION_CORRECT_HISTORY:
    #     validate_correction_target(
    #         conn, case_id,
    #         correction_of_history_id=correction_of_history_id,
    #         current_status_history_id=current_history_id,
    #     )
    #
    # Step 4: 幂等检查
    # check_idempotency(conn, case_id, client_request_id)
    #
    # Step 5: 追加历史
    # history_id = append_status_history(
    #     conn, case_id, to_status, action_code,
    #     operator_id, operator_name, operator_org_id, operator_org_name,
    #     action_at, client_request_id, comment,
    #     source_document_id, correction_of_history_id,
    #     data_nature, is_demo,
    #     transition_result=(
    #         TransitionResult.CORRECTION
    #         if action_code == ACTION_CORRECT_HISTORY
    #         else TransitionResult.SUCCESS
    #     ),
    # )
    #
    # Step 6: 更新事项表
    # cursor = conn.cursor()
    # cursor.execute(SQL_UPDATE_CASE_AFTER_TRANSITION, (
    #     to_status, history_id, case_id, locked['row_version'],
    # ))
    # if cursor.rowcount == 0:
    #     raise OptimisticLockError(
    #         f"Failed to update case {case_id}: row_version mismatch "
    #         f"during UPDATE (concurrent modification)"
    #     )
    #
    # Step 7: 特殊字段更新
    # if to_status == CaseStatus.CLOSED:
    #     closed_at = kwargs.get('closed_at', action_at)
    #     closure_reason = kwargs.get('closure_reason')
    #     if closure_reason:
    #         cursor.execute(SQL_UPDATE_CASE_CLOSED_FIELDS, (
    #             closed_at, closure_reason, case_id,
    #         ))
    # elif to_status == CaseStatus.MERGED:
    #     cursor.execute(SQL_UPDATE_CASE_MERGED_FIELDS, (
    #         kwargs['merged_into_case_id'], case_id,
    #     ))
    #
    # Step 8: 返回更新后快照
    # return {
    #     'case_id': case_id,
    #     'current_status': to_status,
    #     'current_status_history_id': history_id,
    #     'row_version': locked['row_version'] + 1,
    #     'action_code': action_code,
    #     'transition_result': (
    #         TransitionResult.CORRECTION
    #         if action_code == ACTION_CORRECT_HISTORY
    #         else TransitionResult.SUCCESS
    #     ),
    # }
    raise NotImplementedError("需要数据库连接")


# ============================================================================
# E01 事件创建服务
# ============================================================================


def validate_and_create_e01_event_chain(
    conn,
    factor_result_id: int,
    event_code: str,
    operator_id: int | None,
    operator_name: str | None,
    action_at: datetime,
    client_request_id: str,
    data_nature: str = 'formal',
    is_demo: int = 0,
) -> dict:
    """校验并创建 E01 超标事件—事项—初始轨迹完整链。

    校验：
    1. 结果必须是 INITIAL + EXCEEDED + VALID + EFFECTIVE
    2. 同一结果不得已有另一个有效事件
    3. 采样、批次、点位、标准链路有效且数据性质一致
    4. 创建 event, case, history, source追踪在同一事务

    返回 {event_id, case_id, history_id}

    Args:
        conn: PyMySQL 数据库连接。
        factor_result_id: 因子结果 ID。
        event_code: 事件编码。
        operator_id: 操作人 ID。
        operator_name: 操作人姓名。
        action_at: 操作时间。
        client_request_id: 幂等请求号。
        data_nature: 数据性质。
        is_demo: 是否演示。

    Returns:
        {'event_id': int, 'case_id': int, 'history_id': int}

    Raises:
        CaseTransitionError: 结果条件不满足。
        DataNatureConsistencyError: 数据性质不一致。
        IdempotencyConflictError: 事件已存在。
    """
    # Step 1: 查询结果详情
    # cursor = conn.cursor()
    # cursor.execute(SQL_E01_RESULT_DETAIL, (factor_result_id,))
    # result = dict_from_row(cursor.description, cursor.fetchone())
    # if result is None:
    #     raise CaseTransitionError(f"Factor result {factor_result_id} not found")
    #
    # Step 2: 校验结果条件
    # if result['test_stage'] != TestStage.INITIAL:
    #     raise CaseTransitionError(
    #         f"Result must be INITIAL, got {result['test_stage']}"
    #     )
    # if result['judgement'] != Judgement.EXCEEDED:
    #     raise CaseTransitionError(
    #         f"Result must be EXCEEDED, got {result['judgement']}"
    #     )
    # if result['result_validity'] != ResultValidity.VALID:
    #     raise CaseTransitionError(
    #         f"Result must be VALID, got {result['result_validity']}"
    #     )
    # if result['effective_status'] != EffectiveStatus.EFFECTIVE:
    #     raise CaseTransitionError(
    #         f"Result must be EFFECTIVE, got {result['effective_status']}"
    #     )
    #
    # Step 3: 校验同一结果无重复事件
    # validate_single_effective_event_per_result(
    #     conn, factor_result_id, data_nature, is_demo
    # )
    #
    # Step 4: 校验数据性质链路一致
    # if result['data_nature'] != data_nature:
    #     raise DataNatureConsistencyError(...)
    # if result['is_demo'] != is_demo:
    #     raise DataNatureConsistencyError(...)
    # if result['point_nature'] != data_nature:
    #     raise DataNatureConsistencyError(...)
    # if result['point_demo'] != is_demo:
    #     raise DataNatureConsistencyError(...)
    # if result['batch_nature'] != data_nature:
    #     raise DataNatureConsistencyError(...)
    # if result['batch_demo'] != is_demo:
    #     raise DataNatureConsistencyError(...)
    #
    # Step 5: 创建事项 (INSERT e_closure_case)
    # case_code = generate_case_code(...)
    # cursor.execute("""
    #     INSERT INTO e_closure_case (
    #         case_code, case_domain, source_table, source_record_id,
    #         title, current_status, data_nature, is_demo,
    #         opened_at, source_business_key
    #     ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    # """, (
    #     case_code, 'E01_EXCEED', E01_SOURCE_TABLE, factor_result_id,
    #     f"E01超标-{result.get('reported_factor_name', '')}", 
    #     CaseStatus.DISCOVERED, data_nature, is_demo,
    #     action_at, str(factor_result_id),
    # ))
    # case_id = cursor.lastrowid
    #
    # Step 6: 创建初始历史 (append_status_history)
    # history_id = append_status_history(
    #     conn, case_id, CaseStatus.DISCOVERED, ACTION_CREATE_CASE,
    #     operator_id, operator_name, operator_org_id, operator_org_name,
    #     action_at, client_request_id,
    #     data_nature=data_nature, is_demo=is_demo,
    # )
    #
    # Step 7: 更新事项的 current_status_history_id
    # cursor.execute(
    #     "UPDATE e_closure_case SET current_status_history_id=%s WHERE id=%s",
    #     (history_id, case_id),
    # )
    #
    # Step 8: 创建超标事件
    # cursor.execute("""
    #     INSERT INTO e01_exceed_event (
    #         event_code, case_id, original_result_id,
    #         first_exceeded_at, event_category,
    #         effective_status, data_nature, is_demo
    #     ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
    # """, (
    #     event_code, case_id, factor_result_id,
    #     action_at, result['sample_category'],
    #     EffectiveStatus.EFFECTIVE, data_nature, is_demo,
    # ))
    # event_id = cursor.lastrowid
    #
    # return {'event_id': event_id, 'case_id': case_id, 'history_id': history_id}
    raise NotImplementedError("需要数据库连接")


def validate_single_effective_event_per_result(
    conn,
    result_id: int,
    data_nature: str = 'formal',
    is_demo: int = 0,
) -> None:
    """校验一条结果最多一个有效事件。

    Args:
        conn: PyMySQL 数据库连接。
        result_id: 因子结果 ID。
        data_nature: 数据性质。
        is_demo: 是否演示。

    Raises:
        CaseTransitionError: 已存在有效事件。
    """
    # cursor = conn.cursor()
    # cursor.execute(SQL_CHECK_EVENT_PER_RESULT, (result_id, data_nature, is_demo))
    # row = cursor.fetchone()
    # if row is not None:
    #     raise CaseTransitionError(
    #         f"Result {result_id} already has an effective event "
    #         f"(event_id={row[0]})"
    #     )
    raise NotImplementedError("需要数据库连接")


# ============================================================================
# 复测链服务
# ============================================================================


def validate_retest_result_link(
    conn,
    retest_round_id: int,
    factor_result_id: int,
    original_result_id: int,
    event_id: int,
    data_nature: str = 'formal',
    is_demo: int = 0,
) -> None:
    """校验复测结果关联。

    规则：
    1. factor_result_id 的 test_stage 必须为 RETEST
    2. original_result_id 必须为有效 INITIAL+EXCEEDED 结果
    3. original_result_id 必须等于事件的 original_result_id
    4. 复测结果所在批次必须等于复测轮次批次
    5. 复测因子/类别与原结果相同
    6. factor_result_id != original_result_id
    7. 同一复测结果不得关联多个原结果（唯一约束）

    Args:
        conn: PyMySQL 数据库连接。
        retest_round_id: 复测轮次 ID。
        factor_result_id: 复测因子结果 ID。
        original_result_id: 原结果 ID。
        event_id: 事件 ID。
        data_nature: 数据性质。
        is_demo: 是否演示。

    Raises:
        RetestChainError: 校验失败。
    """
    # cursor = conn.cursor()
    #
    # Rule 1: 复测结果 test_stage 必须为 RETEST
    # cursor.execute(SQL_RETEST_RESULT_INFO, (factor_result_id,))
    # retest_info = dict_from_row(cursor.description, cursor.fetchone())
    # if retest_info is None:
    #     raise RetestChainError(f"Retest result {factor_result_id} not found")
    # if retest_info['test_stage'] != TestStage.RETEST:
    #     raise RetestChainError(
    #         f"Retest result test_stage must be RETEST, "
    #         f"got {retest_info['test_stage']}"
    #     )
    #
    # Rule 2: 原结果必须 INITIAL + EXCEEDED + VALID + EFFECTIVE
    # cursor.execute(SQL_ORIGINAL_RESULT_INFO, (original_result_id,))
    # orig_info = dict_from_row(cursor.description, cursor.fetchone())
    # if orig_info is None:
    #     raise RetestChainError(f"Original result {original_result_id} not found")
    # if orig_info['test_stage'] != TestStage.INITIAL:
    #     raise RetestChainError(
    #         f"Original result must be INITIAL, got {orig_info['test_stage']}"
    #     )
    # if orig_info['judgement'] != Judgement.EXCEEDED:
    #     raise RetestChainError(
    #         f"Original result must be EXCEEDED, got {orig_info['judgement']}"
    #     )
    # if orig_info['result_validity'] != ResultValidity.VALID:
    #     raise RetestChainError(
    #         f"Original result must be VALID, got {orig_info['result_validity']}"
    #     )
    # if orig_info['effective_status'] != EffectiveStatus.EFFECTIVE:
    #     raise RetestChainError(
    #         f"Original result must be EFFECTIVE, got {orig_info['effective_status']}"
    #     )
    #
    # Rule 3: 原结果必须等于事件的 original_result_id
    # cursor.execute(SQL_EVENT_INFO, (event_id,))
    # event_info = dict_from_row(cursor.description, cursor.fetchone())
    # if event_info is None:
    #     raise RetestChainError(f"Event {event_id} not found")
    # if event_info['original_result_id'] != original_result_id:
    #     raise RetestChainError(
    #         f"Original result {original_result_id} does not match "
    #         f"event's original_result_id {event_info['original_result_id']}"
    #     )
    #
    # Rule 4: 复测结果所在批次 = 复测轮次批次
    # cursor.execute(SQL_RETEST_ROUND_INFO, (retest_round_id,))
    # round_info = dict_from_row(cursor.description, cursor.fetchone())
    # retest_sample = lookup_sample_by_result(conn, factor_result_id)
    # if retest_sample['batch_id'] != round_info['retest_batch_id']:
    #     raise RetestChainError(
    #         f"Retest result batch {retest_sample['batch_id']} != "
    #         f"retest round batch {round_info['retest_batch_id']}"
    #     )
    #
    # Rule 5: 复测因子/类别与原结果相同
    # if retest_info['factor_id'] != orig_info['factor_id']:
    #     raise RetestChainError("Factor mismatch between retest and original")
    #
    # Rule 6: factor_result_id != original_result_id
    # if factor_result_id == original_result_id:
    #     raise RetestChainError(
    #         "factor_result_id and original_result_id must be distinct"
    #     )
    #
    # Rule 7: 同一复测结果不得关联多个原结果
    # cursor.execute(SQL_RETEST_RESULT_EXISTS, (factor_result_id,))
    # if cursor.fetchone() is not None:
    #     raise RetestChainError(
    #         f"Retest result {factor_result_id} already linked to another original"
    #     )
    raise NotImplementedError("需要数据库连接")


def validate_retest_round_caches(conn, event_id: int) -> None:
    """校验事件的 current_retest_round 和 latest_retest_outcome
    与最大有效复测轮次和结论一致。

    Args:
        conn: PyMySQL 数据库连接。
        event_id: 事件 ID。

    Raises:
        RetestChainError: 缓存不一致。
    """
    # cursor = conn.cursor()
    #
    # 获取事件缓存值
    # cursor.execute(
    #     "SELECT current_retest_round, latest_retest_outcome, "
    #     "data_nature, is_demo FROM e01_exceed_event WHERE id=%s",
    #     (event_id,),
    # )
    # event = dict_from_row(cursor.description, cursor.fetchone())
    #
    # 获取实际最大轮次
    # cursor.execute(SQL_LATEST_RETEST_ROUND, (
    #     event_id, event['data_nature'], event['is_demo'],
    # ))
    # latest = cursor.fetchone()
    # if latest is None:
    #     # 无复测轮次，缓存应为 0 / NOT_TESTED
    #     if event['current_retest_round'] != 0:
    #         raise RetestChainError(
    #             f"Event cache current_retest_round={event['current_retest_round']} "
    #             f"but no retest rounds exist"
    #         )
    #     if event['latest_retest_outcome'] != 'NOT_TESTED':
    #         raise RetestChainError(
    #             f"Event cache latest_retest_outcome={event['latest_retest_outcome']} "
    #             f"but no retest rounds exist"
    #         )
    # else:
    #     round_no, outcome, review_status = latest
    #     if event['current_retest_round'] != round_no:
    #         raise RetestChainError(
    #             f"Event cache current_retest_round={event['current_retest_round']} "
    #             f"but actual max round_no={round_no}"
    #         )
    #     if event['latest_retest_outcome'] != outcome:
    #         raise RetestChainError(
    #             f"Event cache latest_retest_outcome={event['latest_retest_outcome']} "
    #             f"but actual latest outcome={outcome}"
    #         )
    raise NotImplementedError("需要数据库连接")


def validate_closure_prerequisites(conn, event_id: int, case_id: int) -> None:
    """校验销项前提。

    必须满足：
    1. 最后有效复测为 COMPLIANT 且 review_status='PASSED'
    2. 存在 REVIEW_PASS 轨迹
    3. 存在 CLOSE_CASE 轨迹
    4. 存在有效 CLOSURE_DOCUMENT 证据

    Args:
        conn: PyMySQL 数据库连接。
        event_id: 事件 ID。
        case_id: 事项 ID。

    Raises:
        RetestChainError: 销项前提不满足。
    """
    # cursor = conn.cursor()
    #
    # Prerequisite 1: 最后有效复测达标且审核通过
    # cursor.execute(SQL_LAST_RETEST_OUTCOME, (event_id,))
    # retest = cursor.fetchone()
    # if retest is not None:
    #     outcome, review_status = retest
    #     if outcome != RetestOutcome.COMPLIANT:
    #         raise RetestChainError(
    #             f"Last retest outcome is {outcome}, need COMPLIANT"
    #         )
    #     if review_status != RetestReviewStatus.PASSED:
    #         raise RetestChainError(
    #             f"Last retest review_status is {review_status}, need PASSED"
    #         )
    #
    # Prerequisite 2: 存在 REVIEW_PASS 轨迹
    # cursor.execute(SQL_HAS_REVIEW_PASS_HISTORY, (case_id,))
    # if cursor.fetchone() is None:
    #     raise RetestChainError("No REVIEW_PASS history found")
    #
    # Prerequisite 3: 存在 CLOSE_CASE 轨迹
    # cursor.execute(SQL_HAS_CLOSE_CASE_HISTORY, (case_id,))
    # if cursor.fetchone() is None:
    #     raise RetestChainError("No CLOSE_CASE history found")
    #
    # Prerequisite 4: 存在有效 CLOSURE_DOCUMENT 证据
    # cursor.execute(SQL_HAS_CLOSURE_EVIDENCE, (case_id,))
    # if cursor.fetchone() is None:
    #     raise RetestChainError("No valid CLOSURE_DOCUMENT evidence found")
    raise NotImplementedError("需要数据库连接")


# ============================================================================
# 历史纠错服务
# ============================================================================


def validate_correction_target(
    conn,
    case_id: int,
    correction_of_history_id: int,
    current_status_history_id: int,
) -> None:
    """校验纠错目标。

    V1.1 规则：
    - correction_of_history_id 必须等于 current_status_history_id
    - 不允许纠正任意较早历史节点
    - 纠错目标必须为紧邻前一轨迹（sequence_no = 当前sequence_no，
      因为纠错指向当前叶子）

    Args:
        conn: PyMySQL 数据库连接。
        case_id: 事项 ID。
        correction_of_history_id: 纠错指向的历史 ID。
        current_status_history_id: 当前有效历史 ID。

    Raises:
        CorrectionTargetError: 纠错目标不合法。
    """
    if correction_of_history_id != current_status_history_id:
        raise CorrectionTargetError(
            f"CORRECTION_TARGET_NOT_IMMEDIATE_PREVIOUS_HISTORY: "
            f"correction target {correction_of_history_id} != "
            f"current {current_status_history_id}"
        )

    # 额外校验：被指向的轨迹必须属于同一事项
    # cursor = conn.cursor()
    # cursor.execute(
    #     "SELECT case_id FROM e_case_status_history WHERE id = %s",
    #     (correction_of_history_id,),
    # )
    # row = cursor.fetchone()
    # if row is None:
    #     raise CorrectionTargetError(
    #         f"Correction target history {correction_of_history_id} not found"
    #     )
    # if row[0] != case_id:
    #     raise CorrectionTargetError(
    #         f"Correction target {correction_of_history_id} belongs to "
    #         f"case {row[0]}, not case {case_id}"
    #     )


# ============================================================================
# 数据性质校验服务
# ============================================================================


def validate_chain_data_nature(
    conn,
    result_id: int,
    expected_nature: str,
    expected_is_demo: int,
) -> None:
    """校验结果-采样-批次-点位-事件-事项整条链的数据性质一致。

    Args:
        conn: PyMySQL 数据库连接。
        result_id: 因子结果 ID。
        expected_nature: 期望的数据性质。
        expected_is_demo: 期望的 is_demo 值。

    Raises:
        DataNatureConsistencyError: 链路中数据性质不一致。
    """
    # cursor = conn.cursor()
    # cursor.execute(SQL_RESULT_SAMPLE_CHAIN, (result_id,))
    # row = cursor.fetchone()
    # if row is None:
    #     raise DataNatureConsistencyError(f"Result chain not found for {result_id}")
    #
    # names = ['result_nature', 'result_demo', 'sample_nature', 'sample_demo',
    #          'batch_nature', 'batch_demo', 'point_nature', 'point_demo']
    # chain = dict(zip(names, row))
    #
    # for field_name, val in chain.items():
    #     if field_name.endswith('_nature'):
    #         if val != expected_nature:
    #             raise DataNatureConsistencyError(
    #                 f"Chain data_nature mismatch: {field_name}={val}, "
    #                 f"expected={expected_nature}, result_id={result_id}"
    #             )
    #     elif field_name.endswith('_demo'):
    #         if val != expected_is_demo:
    #             raise DataNatureConsistencyError(
    #                 f"Chain is_demo mismatch: {field_name}={val}, "
    #                 f"expected={expected_is_demo}, result_id={result_id}"
    #             )
    raise NotImplementedError("需要数据库连接")


def validate_formal_chain_no_demo_or_unverified(conn, result_id: int) -> None:
    """校验正式链不引用演示或未核验对象。

    遍历结果-采样-批次-点位链路，
    确保无 is_demo=1 或 verification_status != 'VERIFIED'。

    Args:
        conn: PyMySQL 数据库连接。
        result_id: 因子结果 ID。

    Raises:
        DataNatureConsistencyError: 引用了演示或未核验对象。
    """
    # cursor = conn.cursor()
    # cursor.execute(SQL_RESULT_SAMPLE_CHAIN, (result_id,))
    # row = cursor.fetchone()
    # if row is None:
    #     raise DataNatureConsistencyError(f"Result chain not found for {result_id}")
    #
    # chain = dict(zip(
    #     ['result_demo', 'sample_demo', 'batch_demo', 'point_demo'],
    #     [row[1], row[3], row[5], row[7]],
    # ))
    #
    # for name, val in chain.items():
    #     if val == 1:
    #         raise DataNatureConsistencyError(
    #             f"Formal chain references demo data: {name}={val}"
    #         )
    raise NotImplementedError("需要数据库连接")


# ============================================================================
# 幂等和并发保护
# ============================================================================


def check_idempotency(conn, case_id: int, client_request_id: str) -> None:
    """检查幂等请求号是否已存在。

    Args:
        conn: PyMySQL 数据库连接。
        case_id: 事项 ID。
        client_request_id: 客户端幂等请求号。

    Raises:
        IdempotencyConflictError: 请求号已存在。
    """
    # cursor = conn.cursor()
    # cursor.execute(SQL_CHECK_IDEMPOTENCY, (case_id, client_request_id))
    # row = cursor.fetchone()
    # if row is not None:
    #     raise IdempotencyConflictError(
    #         f"Idempotency conflict: case_id={case_id}, "
    #         f"client_request_id={client_request_id}, "
    #         f"existing_history_id={row[0]}"
    #     )
    raise NotImplementedError("需要数据库连接")


def check_concurrent_modification(
    locked_case: dict,
    expected_row_version: int,
) -> None:
    """检查乐观锁。

    Args:
        locked_case: lock_case_for_transition 返回的事项快照。
        expected_row_version: 预期的行版本号。

    Raises:
        OptimisticLockError: 版本号不匹配。
    """
    if locked_case['row_version'] != expected_row_version:
        raise OptimisticLockError(
            f"CONCURRENT_MODIFICATION: case_id={locked_case.get('id')}, "
            f"expected_row_version={expected_row_version}, "
            f"actual_row_version={locked_case['row_version']}"
        )
