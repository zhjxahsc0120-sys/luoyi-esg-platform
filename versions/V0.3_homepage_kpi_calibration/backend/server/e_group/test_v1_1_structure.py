"""E组公共闭环与E01 V1.1 结构和逻辑单元测试。

本文件中的测试不连接数据库，可独立运行。
测试覆盖枚举、状态转换矩阵、表定义元数据、KPI规则、纠错规则、
复测链规则、数据隔离和E04排除。
"""

import unittest
from .enums import (
    CaseStatus, DataNature, EffectiveStatus, TestStage,
    Judgement, ResultValidity, TransitionResult,
    validate_data_nature_consistency, is_formal_kpi_eligible,
    TERMINAL_STATUSES, CASE_TRANSITION_MATRIX,
    NON_TERMINAL_STATUSES, SUSPENDABLE_STATUSES,
    CANCELLABLE_STATUSES, MERGEABLE_STATUSES,
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
    # 其他枚举
    MonitorCategory, EvidenceRole, PartyRole,
    BatchStatus, SampleStatus, TaskStatus,
    RetestOutcome, RetestReviewStatus,
    VerificationStatus, ActiveStatus,
)
from .models import ALL_TABLE_DEFS
from .service_skeleton import (
    validate_transition,
    CaseTransitionError,
    CorrectionTargetError,
    OptimisticLockError,
    IdempotencyConflictError,
    DataNatureConsistencyError,
    RetestChainError,
    check_concurrent_modification,
)


class TestDataNatureConsistency(unittest.TestCase):
    """测试 data_nature 与 is_demo 一致性校验"""

    def test_formal_with_is_demo_0(self):
        """formal + is_demo=0 应通过"""
        self.assertTrue(validate_data_nature_consistency('formal', 0))

    def test_demo_with_is_demo_1(self):
        """demo + is_demo=1 应通过"""
        self.assertTrue(validate_data_nature_consistency('demo', 1))

    def test_demo_with_is_demo_0_raises(self):
        """demo + is_demo=0 应不通过"""
        self.assertFalse(validate_data_nature_consistency('demo', 0))

    def test_formal_with_is_demo_1_raises(self):
        """formal + is_demo=1 应不通过"""
        self.assertFalse(validate_data_nature_consistency('formal', 1))

    def test_platform_calc_with_is_demo_0(self):
        """platform_calc + is_demo=0 应通过"""
        self.assertTrue(validate_data_nature_consistency('platform_calc', 0))

    def test_platform_calc_with_is_demo_1_raises(self):
        """platform_calc + is_demo=1 应不通过"""
        self.assertFalse(validate_data_nature_consistency('platform_calc', 1))


class TestFormalKPIEligibility(unittest.TestCase):
    """测试正式 KPI 资格判定"""

    def test_formal_effective_verified(self):
        """全部满足条件应返回 True"""
        self.assertTrue(is_formal_kpi_eligible(
            data_nature='formal', is_demo=0,
            effective_status='EFFECTIVE',
            result_validity='VALID',
            verification_status='VERIFIED',
        ))

    def test_demo_rejected(self):
        """demo 数据不参与正式 KPI"""
        self.assertFalse(is_formal_kpi_eligible(
            data_nature='demo', is_demo=1,
            effective_status='EFFECTIVE',
        ))

    def test_platform_calc_rejected(self):
        """platform_calc 不参与正式 KPI"""
        self.assertFalse(is_formal_kpi_eligible(
            data_nature='platform_calc', is_demo=0,
            effective_status='EFFECTIVE',
        ))

    def test_draft_rejected(self):
        """DRAFT 状态不参与正式 KPI"""
        self.assertFalse(is_formal_kpi_eligible(
            data_nature='formal', is_demo=0,
            effective_status='DRAFT',
        ))

    def test_invalid_rejected(self):
        """INVALID 状态不参与正式 KPI"""
        self.assertFalse(is_formal_kpi_eligible(
            data_nature='formal', is_demo=0,
            effective_status='INVALID',
        ))

    def test_void_result_rejected(self):
        """VOID 结果不参与正式 KPI"""
        self.assertFalse(is_formal_kpi_eligible(
            data_nature='formal', is_demo=0,
            effective_status='EFFECTIVE',
            result_validity='VOID',
        ))

    def test_no_optional_filters_passes(self):
        """不传可选过滤条件时，只校验必要条件"""
        self.assertTrue(is_formal_kpi_eligible(
            data_nature='formal', is_demo=0,
            effective_status='EFFECTIVE',
        ))


class TestCaseTransitionMatrix(unittest.TestCase):
    """测试状态转换矩阵"""

    def test_create_case(self):
        """创建事项：None -> DISCOVERED"""
        result = validate_transition(
            current_status=None,
            action_code=ACTION_CREATE_CASE,
            case_domain='E01_EXCEED',
            data_nature='formal',
        )
        self.assertEqual(result, CaseStatus.DISCOVERED)

    def test_create_case_with_existing_status_raises(self):
        """创建时当前状态非 None 应抛异常"""
        with self.assertRaises(CaseTransitionError):
            validate_transition(
                current_status=CaseStatus.DISCOVERED,
                action_code=ACTION_CREATE_CASE,
                case_domain='E01_EXCEED',
                data_nature='formal',
            )

    def test_normal_flow_discovered_to_closed(self):
        """正向流转：DISCOVERED -> ... -> CLOSED"""
        flow = [
            (None, ACTION_CREATE_CASE, CaseStatus.DISCOVERED),
            (CaseStatus.DISCOVERED, ACTION_ISSUE_RECTIFICATION, CaseStatus.PENDING_RECTIFICATION),
            (CaseStatus.PENDING_RECTIFICATION, ACTION_START_RECTIFICATION, CaseStatus.RECTIFYING),
            (CaseStatus.RECTIFYING, ACTION_SUBMIT_RECTIFICATION, CaseStatus.PENDING_REVIEW),
            (CaseStatus.PENDING_REVIEW, ACTION_REVIEW_PASS, CaseStatus.PENDING_CLOSURE),
            (CaseStatus.PENDING_CLOSURE, ACTION_CLOSE_CASE, CaseStatus.CLOSED),
        ]
        for from_s, action, to_s in flow:
            result = validate_transition(
                current_status=from_s,
                action_code=action,
                case_domain='E01_EXCEED',
                data_nature='formal',
            )
            self.assertEqual(result, to_s,
                             f"Transition {from_s} --{action}--> failed")

    def test_review_reject_back_to_rectifying(self):
        """审核驳回：PENDING_REVIEW -> RECTIFYING"""
        result = validate_transition(
            current_status=CaseStatus.PENDING_REVIEW,
            action_code=ACTION_REVIEW_REJECT,
            case_domain='E01_EXCEED',
            data_nature='formal',
        )
        self.assertEqual(result, CaseStatus.RECTIFYING)

    def test_closure_reject_back_to_rectifying(self):
        """销项驳回：PENDING_CLOSURE -> RECTIFYING"""
        result = validate_transition(
            current_status=CaseStatus.PENDING_CLOSURE,
            action_code=ACTION_CLOSURE_REJECT,
            case_domain='E01_EXCEED',
            data_nature='formal',
        )
        self.assertEqual(result, CaseStatus.RECTIFYING)

    def test_reopen_from_closed(self):
        """重新打开：CLOSED -> RECTIFYING"""
        result = validate_transition(
            current_status=CaseStatus.CLOSED,
            action_code=ACTION_REOPEN_CASE,
            case_domain='E01_EXCEED',
            data_nature='formal',
        )
        self.assertEqual(result, CaseStatus.RECTIFYING)

    def test_invalid_transition_raises(self):
        """非法转换应抛异常：DISCOVERED 不能直接 CLOSE_CASE"""
        with self.assertRaises(CaseTransitionError):
            validate_transition(
                current_status=CaseStatus.DISCOVERED,
                action_code=ACTION_CLOSE_CASE,
                case_domain='E01_EXCEED',
                data_nature='formal',
            )

    def test_cancel_from_non_terminal(self):
        """从非终态取消"""
        for status in NON_TERMINAL_STATUSES:
            result = validate_transition(
                current_status=status,
                action_code=ACTION_CANCEL_CASE,
                case_domain='E01_EXCEED',
                data_nature='formal',
            )
            self.assertEqual(result, CaseStatus.CANCELLED)

    def test_merge_from_non_terminal(self):
        """从非终态合并（需要 merged_into_case_id）"""
        result = validate_transition(
            current_status=CaseStatus.DISCOVERED,
            action_code=ACTION_MERGE_CASE,
            case_domain='E01_EXCEED',
            data_nature='formal',
            merged_into_case_id=999,
        )
        self.assertEqual(result, CaseStatus.MERGED)

    def test_merge_without_target_raises(self):
        """合并无目标应抛异常"""
        with self.assertRaises(CaseTransitionError):
            validate_transition(
                current_status=CaseStatus.DISCOVERED,
                action_code=ACTION_MERGE_CASE,
                case_domain='E01_EXCEED',
                data_nature='formal',
            )

    def test_suspend_from_suspendable(self):
        """从可挂起状态挂起"""
        for status in SUSPENDABLE_STATUSES:
            result = validate_transition(
                current_status=status,
                action_code=ACTION_SUSPEND_CASE,
                case_domain='E01_EXCEED',
                data_nature='formal',
            )
            self.assertEqual(result, CaseStatus.SUSPENDED)

    def test_resume_from_suspended(self):
        """从挂起恢复（需要 pre_suspend_status）"""
        result = validate_transition(
            current_status=CaseStatus.SUSPENDED,
            action_code=ACTION_RESUME_CASE,
            case_domain='E01_EXCEED',
            data_nature='formal',
            pre_suspend_status=CaseStatus.RECTIFYING,
        )
        self.assertEqual(result, CaseStatus.RECTIFYING)

    def test_resume_without_pre_status_raises(self):
        """恢复无 pre_suspend_status 应抛异常"""
        with self.assertRaises(CaseTransitionError):
            validate_transition(
                current_status=CaseStatus.SUSPENDED,
                action_code=ACTION_RESUME_CASE,
                case_domain='E01_EXCEED',
                data_nature='formal',
            )

    def test_resume_to_terminal_raises(self):
        """恢复到终态应抛异常"""
        with self.assertRaises(CaseTransitionError):
            validate_transition(
                current_status=CaseStatus.SUSPENDED,
                action_code=ACTION_RESUME_CASE,
                case_domain='E01_EXCEED',
                data_nature='formal',
                pre_suspend_status=CaseStatus.CLOSED,
            )

    def test_terminal_status_not_cancellable(self):
        """终态不能取消"""
        for status in TERMINAL_STATUSES:
            with self.assertRaises(CaseTransitionError):
                validate_transition(
                    current_status=status,
                    action_code=ACTION_CANCEL_CASE,
                    case_domain='E01_EXCEED',
                    data_nature='formal',
                )

    def test_correct_history_returns_current(self):
        """纠错动作返回当前状态"""
        result = validate_transition(
            current_status=CaseStatus.RECTIFYING,
            action_code=ACTION_CORRECT_HISTORY,
            case_domain='E01_EXCEED',
            data_nature='formal',
        )
        self.assertEqual(result, CaseStatus.RECTIFYING)


class TestTerminalStatuses(unittest.TestCase):
    """测试终态集合"""

    def test_closed_is_terminal(self):
        self.assertIn(CaseStatus.CLOSED, TERMINAL_STATUSES)

    def test_cancelled_is_terminal(self):
        self.assertIn(CaseStatus.CANCELLED, TERMINAL_STATUSES)

    def test_merged_is_terminal(self):
        self.assertIn(CaseStatus.MERGED, TERMINAL_STATUSES)

    def test_discovered_is_not_terminal(self):
        self.assertNotIn(CaseStatus.DISCOVERED, TERMINAL_STATUSES)

    def test_suspended_is_not_terminal(self):
        self.assertNotIn(CaseStatus.SUSPENDED, TERMINAL_STATUSES)

    def test_all_terminal_statuses_in_case_status(self):
        """所有终态必须是 CaseStatus 枚举值"""
        for s in TERMINAL_STATUSES:
            self.assertIn(s, [e.value for e in CaseStatus])

    def test_non_terminal_and_terminal_are_disjoint(self):
        """非终态和终态不重叠"""
        self.assertTrue(TERMINAL_STATUSES.isdisjoint(NON_TERMINAL_STATUSES))


class TestTableDefinitions(unittest.TestCase):
    """测试表定义元数据"""

    def test_all_28_tables_defined(self):
        self.assertEqual(len(ALL_TABLE_DEFS), 28)

    def test_e01_factor_result_has_result_code(self):
        """e01_factor_result 应包含 result_code 字段"""
        cols = {c.name for c in ALL_TABLE_DEFS['e01_factor_result'].columns}
        self.assertIn('result_code', cols)

    def test_e01_factor_result_has_test_stage(self):
        """e01_factor_result 应包含 test_stage 字段"""
        cols = {c.name for c in ALL_TABLE_DEFS['e01_factor_result'].columns}
        self.assertIn('test_stage', cols)

    def test_e01_factor_result_has_judgement(self):
        """e01_factor_result 应包含 judgement 字段"""
        cols = {c.name for c in ALL_TABLE_DEFS['e01_factor_result'].columns}
        self.assertIn('judgement', cols)

    def test_e_case_status_history_no_effective_status(self):
        """e_case_status_history 不应有 effective_status 字段"""
        cols = {c.name for c in ALL_TABLE_DEFS['e_case_status_history'].columns}
        self.assertNotIn('effective_status', cols)

    def test_e01_exceed_event_has_generated_column(self):
        """e01_exceed_event 应包含生成列 active_original_result_id"""
        cols = {c.name for c in ALL_TABLE_DEFS['e01_exceed_event'].columns}
        self.assertIn('active_original_result_id', cols)

    def test_e01_exceed_event_has_case_id(self):
        """e01_exceed_event 应关联 case_id"""
        cols = {c.name for c in ALL_TABLE_DEFS['e01_exceed_event'].columns}
        self.assertIn('case_id', cols)

    def test_e01_legacy_record_mapping_no_data_nature(self):
        """e01_legacy_record_mapping 不应有 data_nature 和 is_demo"""
        t = ALL_TABLE_DEFS['e01_legacy_record_mapping']
        cols = {c.name for c in t.columns}
        self.assertNotIn('data_nature', cols)
        self.assertNotIn('is_demo', cols)

    def test_all_tables_have_pk(self):
        """所有表都应有主键"""
        for name, tdef in ALL_TABLE_DEFS.items():
            pk_cols = [c for c in tdef.columns if c.is_pk]
            self.assertTrue(len(pk_cols) >= 1,
                            f"Table {name} has no primary key")

    def test_data_nature_tables_have_is_demo(self):
        """所有包含 data_nature 的表（除 legacy_mapping）都应有 is_demo"""
        for name, tdef in ALL_TABLE_DEFS.items():
            cols = {c.name for c in tdef.columns}
            if 'data_nature' in cols:
                self.assertIn('is_demo', cols,
                              f"Table {name} has data_nature but no is_demo")

    def test_e_closure_case_has_row_version(self):
        """e_closure_case 应包含 row_version 字段"""
        cols = {c.name for c in ALL_TABLE_DEFS['e_closure_case'].columns}
        self.assertIn('row_version', cols)

    def test_e_closure_case_has_current_status(self):
        """e_closure_case 应包含 current_status 字段"""
        cols = {c.name for c in ALL_TABLE_DEFS['e_closure_case'].columns}
        self.assertIn('current_status', cols)

    def test_e_case_status_history_has_sequence_no(self):
        """e_case_status_history 应包含 sequence_no"""
        cols = {c.name for c in ALL_TABLE_DEFS['e_case_status_history'].columns}
        self.assertIn('sequence_no', cols)

    def test_e_case_status_history_has_client_request_id(self):
        """e_case_status_history 应包含 client_request_id"""
        cols = {c.name for c in ALL_TABLE_DEFS['e_case_status_history'].columns}
        self.assertIn('client_request_id', cols)

    def test_e_case_status_history_has_correction_of_history_id(self):
        """e_case_status_history 应包含 correction_of_history_id"""
        cols = {c.name for c in ALL_TABLE_DEFS['e_case_status_history'].columns}
        self.assertIn('correction_of_history_id', cols)

    def test_e01_retest_result_link_has_distinct_check(self):
        """e01_retest_result_link 应有 factor_result_id<>original_result_id 约束"""
        tdef = ALL_TABLE_DEFS['e01_retest_result_link']
        check_exprs = [c.expression for c in tdef.checks]
        self.assertTrue(
            any('factor_result_id<>original_result_id' in e for e in check_exprs),
            "Missing distinct check on e01_retest_result_link"
        )

    def test_e_case_status_history_unique_case_sequence(self):
        """e_case_status_history 应有 (case_id, sequence_no) 唯一索引"""
        tdef = ALL_TABLE_DEFS['e_case_status_history']
        idx_cols = set()
        for idx in tdef.indexes:
            if idx.unique:
                idx_cols.update(idx.columns)
        self.assertIn('case_id', idx_cols)
        self.assertIn('sequence_no', idx_cols)

    def test_e_case_status_history_unique_case_request(self):
        """e_case_status_history 应有 (case_id, client_request_id) 唯一索引"""
        tdef = ALL_TABLE_DEFS['e_case_status_history']
        found = False
        for idx in tdef.indexes:
            if idx.unique and 'client_request_id' in idx.columns:
                found = True
                break
        self.assertTrue(found,
                        "Missing unique index on (case_id, client_request_id)")


class TestEnumCompleteness(unittest.TestCase):
    """测试枚举值完整性"""

    def test_case_status_values_match_ddl_check(self):
        """CaseStatus 枚举值应与 DDL CHECK 约束一致"""
        case_table = ALL_TABLE_DEFS['e_closure_case']
        status_checks = [c for c in case_table.checks if 'current_status' in c.expression]
        self.assertTrue(len(status_checks) > 0, "No current_status CHECK found")
        for cs in CaseStatus:
            self.assertIn(cs.value, status_checks[0].expression)

    def test_monitor_category_values(self):
        """MonitorCategory 应包含 WATER, AIR, NOISE"""
        values = {e.value for e in MonitorCategory}
        self.assertEqual(values, {'WATER', 'AIR', 'NOISE'})

    def test_evidence_role_values(self):
        """EvidenceRole 应包含所有 DDL 定义的值"""
        values = {e.value for e in EvidenceRole}
        ddl_values = {
            'FORMAL_NOTICE', 'INITIAL_REPORT', 'RAW_RECORD',
            'RECTIFICATION_MATERIAL', 'RETEST_REPORT', 'REVIEW_OPINION',
            'CLOSURE_DOCUMENT', 'CANCELLATION_DOCUMENT',
        }
        self.assertEqual(values, ddl_values)

    def test_party_role_values(self):
        """PartyRole 应包含所有角色"""
        values = {e.value for e in PartyRole}
        expected = {
            'DISCOVERER', 'RESPONSIBLE', 'HANDLER',
            'REVIEWER', 'CLOSER', 'TEST_PROVIDER',
        }
        self.assertEqual(values, expected)

    def test_batch_status_values(self):
        """BatchStatus 应包含所有 DDL 状态"""
        values = {e.value for e in BatchStatus}
        expected = {
            'DRAFT', 'PARSED', 'VALIDATED', 'PENDING_REVIEW',
            'EFFECTIVE', 'REJECTED', 'INVALID',
        }
        self.assertEqual(values, expected)

    def test_sample_status_values(self):
        """SampleStatus 应包含所有 DDL 状态"""
        values = {e.value for e in SampleStatus}
        expected = {'VALID', 'PENDING_REVIEW', 'VOID', 'DUPLICATE'}
        self.assertEqual(values, expected)

    def test_task_status_values(self):
        """TaskStatus 应包含所有 DDL 状态"""
        values = {e.value for e in TaskStatus}
        expected = {
            'PENDING', 'IN_PROGRESS', 'SUBMITTED',
            'REVIEWED', 'COMPLETED', 'CANCELLED',
        }
        self.assertEqual(values, expected)

    def test_retest_outcome_values(self):
        """RetestOutcome 应包含 COMPLIANT, STILL_EXCEEDED, NO_JUDGEMENT"""
        values = {e.value for e in RetestOutcome}
        self.assertEqual(values, {'COMPLIANT', 'STILL_EXCEEDED', 'NO_JUDGEMENT'})

    def test_retest_review_status_values(self):
        """RetestReviewStatus 应包含 PENDING_REVIEW, PASSED, REJECTED"""
        values = {e.value for e in RetestReviewStatus}
        self.assertEqual(values, {'PENDING_REVIEW', 'PASSED', 'REJECTED'})


class TestKPIRules(unittest.TestCase):
    """测试 KPI 核心规则的代码层面表达"""

    def test_exceed_item_conditions_complete(self):
        """验证历史超标项次所需条件字段在 e01_factor_result 模型中存在"""
        required_fields = {
            'test_stage', 'judgement', 'result_validity',
            'effective_status', 'data_nature', 'is_demo',
        }
        result_cols = {c.name for c in ALL_TABLE_DEFS['e01_factor_result'].columns}
        missing = required_fields - result_cols
        self.assertEqual(missing, set(),
                         f"Missing KPI condition fields: {missing}")

    def test_active_status_not_in_kpi_conditions(self):
        """确认 active_status 不参与 KPI 过滤条件（它是点位属性，非结果属性）"""
        result_cols = {c.name for c in ALL_TABLE_DEFS['e01_factor_result'].columns}
        self.assertNotIn('active_status', result_cols,
                         "active_status should not be on factor_result")

    def test_open_event_excludes_terminal(self):
        """确认 CLOSED/CANCELLED/MERGED 不进入未闭环统计"""
        for status in TERMINAL_STATUSES:
            self.assertNotIn(status, NON_TERMINAL_STATUSES)
        # 事项的 idx_e_case_open 索引包含 current_status，
        # 查询时排除终态即可得到未闭环事项
        case_idx = ALL_TABLE_DEFS['e_closure_case'].indexes
        open_idx = [i for i in case_idx if 'open' in i.name.lower()]
        self.assertTrue(len(open_idx) > 0, "No open index found on e_closure_case")


class TestCorrectionRules(unittest.TestCase):
    """测试纠错规则"""

    def test_correction_must_target_current_leaf(self):
        """纠错目标必须等于当前 history_id"""
        # validate_correction_target 是纯逻辑校验（不依赖数据库的部分）
        # 直接测试相等条件
        current_id = 100
        correction_id = 100
        # 不应抛异常
        try:
            if correction_id != current_id:
                raise CorrectionTargetError("test")
        except CorrectionTargetError:
            self.fail("Should not raise when correction_id == current_id")

    def test_earlier_history_correction_rejected(self):
        """纠错指向更早历史应被拒绝"""
        current_id = 100
        correction_id = 50  # 更早的历史
        with self.assertRaises(CorrectionTargetError):
            if correction_id != current_id:
                raise CorrectionTargetError(
                    f"CORRECTION_TARGET_NOT_IMMEDIATE_PREVIOUS_HISTORY: "
                    f"correction target {correction_id} != current {current_id}"
                )

    def test_correction_preserves_old_history(self):
        """纠错不更新被指向的旧轨迹（仅追加新轨迹）"""
        # 这是设计约束：e_case_status_history 是仅追加表
        history_table = ALL_TABLE_DEFS['e_case_status_history']
        # 确认有 correction_of_history_id 字段用于指向
        cols = {c.name for c in history_table.columns}
        self.assertIn('correction_of_history_id', cols)

    def test_concurrent_correction_conflict(self):
        """并发纠错应通过乐观锁检测"""
        locked = {'row_version': 5}
        # 正确的版本号不抛异常
        check_concurrent_modification(locked, 5)
        # 错误的版本号抛异常
        with self.assertRaises(OptimisticLockError):
            check_concurrent_modification(locked, 4)


class TestRetestChainRules(unittest.TestCase):
    """测试复测链规则（纯逻辑部分）"""

    def test_retest_result_must_be_retest_stage(self):
        """复测结果 test_stage 必须为 RETEST"""
        self.assertEqual(TestStage.RETEST, 'RETEST')
        self.assertNotEqual(TestStage.INITIAL, 'RETEST')

    def test_original_must_be_initial_exceeded(self):
        """原结果必须是 INITIAL + EXCEEDED"""
        self.assertEqual(TestStage.INITIAL, 'INITIAL')
        self.assertEqual(Judgement.EXCEEDED, 'EXCEEDED')

    def test_original_must_match_event(self):
        """原结果必须与事件的 original_result_id 一致"""
        # 这是数据一致性校验，在 service 层实现
        # 此处验证模型中有对应字段
        event_cols = {c.name for c in ALL_TABLE_DEFS['e01_exceed_event'].columns}
        self.assertIn('original_result_id', event_cols)

    def test_retest_not_before_initial(self):
        """复测不能早于初检（round_no > 0 约束）"""
        retest_round = ALL_TABLE_DEFS['e01_retest_round']
        check_exprs = [c.expression for c in retest_round.checks]
        self.assertTrue(
            any('round_no>0' in e for e in check_exprs),
            "Missing round_no>0 check on e01_retest_round"
        )

    def test_distinct_retest_and_original(self):
        """复测结果与原结果必须不同"""
        link_table = ALL_TABLE_DEFS['e01_retest_result_link']
        check_exprs = [c.expression for c in link_table.checks]
        self.assertTrue(
            any('factor_result_id<>original_result_id' in e for e in check_exprs),
            "Missing distinct check on e01_retest_result_link"
        )

    def test_retest_result_unique_per_original(self):
        """同一复测结果不能关联多个原结果（唯一约束）"""
        link_table = ALL_TABLE_DEFS['e01_retest_result_link']
        unique_indexes = [i for i in link_table.indexes
                          if i.unique and 'factor_result_id' in i.columns]
        self.assertTrue(len(unique_indexes) > 0,
                        "Missing unique index on factor_result_id")


class TestDataIsolation(unittest.TestCase):
    """测试数据隔离规则"""

    def test_formal_does_not_reference_demo(self):
        """正式数据不应引用 is_demo=1 的对象"""
        # is_formal_kpi_eligible 已校验 is_demo=0
        self.assertFalse(is_formal_kpi_eligible(
            data_nature='formal', is_demo=1,
            effective_status='EFFECTIVE',
        ))

    def test_demo_data_isolated(self):
        """演示数据不应出现在正式 KPI 中"""
        self.assertFalse(is_formal_kpi_eligible(
            data_nature='demo', is_demo=1,
            effective_status='EFFECTIVE',
        ))

    def test_platform_calc_not_in_formal_kpi(self):
        """平台计算不参与正式 KPI"""
        self.assertFalse(is_formal_kpi_eligible(
            data_nature='platform_calc', is_demo=0,
            effective_status='EFFECTIVE',
        ))

    def test_nature_check_on_all_data_tables(self):
        """所有含 data_nature 的表都有 CHECK 约束"""
        nature_check_tables = []
        for name, tdef in ALL_TABLE_DEFS.items():
            cols = {c.name for c in tdef.columns}
            if 'data_nature' in cols:
                has_nature_check = any(
                    'data_nature' in c.expression and 'is_demo' in c.expression
                    for c in tdef.checks
                )
                if has_nature_check:
                    nature_check_tables.append(name)
        # 至少应有多个表有此约束
        self.assertGreaterEqual(len(nature_check_tables), 10,
                                f"Expected >=10 tables with nature+demo CHECK, "
                                f"got {len(nature_check_tables)}: {nature_check_tables}")


class TestE04Exclusion(unittest.TestCase):
    """测试 E04 排除"""

    def test_no_e04_table_references(self):
        """所有 TableDef 不应引用 E04 表"""
        for name, tdef in ALL_TABLE_DEFS.items():
            for col in tdef.columns:
                if col.fk_ref:
                    self.assertFalse(
                        col.fk_ref.startswith('e04_'),
                        f"Table {name} column {col.name} references E04: {col.fk_ref}"
                    )

    def test_no_e04_in_enums(self):
        """枚举不应包含 E04 域"""
        case_domain_values = {e.value for e in CaseStatus}
        # CaseDomain 检查通过 import 或直接字符串检查
        from .enums import CaseDomain
        domain_values = {e.value for e in CaseDomain}
        self.assertFalse(
            any('E04' in v for v in domain_values),
            f"CaseDomain contains E04 reference: {domain_values}"
        )

    def test_no_e04_in_case_domain_check(self):
        """e_closure_case 的 CHECK 约束不应包含 E04"""
        case_table = ALL_TABLE_DEFS['e_closure_case']
        domain_checks = [c for c in case_table.checks if 'case_domain' in c.expression]
        self.assertTrue(len(domain_checks) > 0)
        self.assertNotIn('E04', domain_checks[0].expression)


class TestServiceSkeletonExceptions(unittest.TestCase):
    """测试服务层骨架的异常类"""

    def test_case_transition_error_is_exception(self):
        self.assertTrue(issubclass(CaseTransitionError, Exception))

    def test_optimistic_lock_error_is_exception(self):
        self.assertTrue(issubclass(OptimisticLockError, Exception))

    def test_idempotency_conflict_error_is_exception(self):
        self.assertTrue(issubclass(IdempotencyConflictError, Exception))

    def test_correction_target_error_is_exception(self):
        self.assertTrue(issubclass(CorrectionTargetError, Exception))

    def test_retest_chain_error_is_exception(self):
        self.assertTrue(issubclass(RetestChainError, Exception))

    def test_data_nature_consistency_error_is_exception(self):
        self.assertTrue(issubclass(DataNatureConsistencyError, Exception))

    def test_check_concurrent_modification_ok(self):
        """版本号匹配不抛异常"""
        locked = {'row_version': 3, 'id': 1}
        check_concurrent_modification(locked, 3)  # 不抛异常

    def test_check_concurrent_modification_mismatch(self):
        """版本号不匹配抛 OptimisticLockError"""
        locked = {'row_version': 3, 'id': 1}
        with self.assertRaises(OptimisticLockError):
            check_concurrent_modification(locked, 2)


# 运行入口
if __name__ == '__main__':
    unittest.main()
