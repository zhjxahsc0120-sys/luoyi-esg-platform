-- ============================================================================
-- V1_1_060__consistency_views.sql
-- E组公共闭环 & E01 V1.1 增量迁移 — 一致性检查视图
-- ============================================================================
-- 包含 6 个一致性视图 + 1 个跨月复测追溯视图：
--   v_e_case_status_inconsistency          案件状态缓存一致性
--   v_e01_event_result_inconsistency       超标事件与检测结果链一致性
--   v_e01_retest_chain_inconsistency       复测链一致性
--   v_e01_core_data_nature_inconsistency   核心链路 data_nature/is_demo 一致性
--   v_e01_configuration_data_nature_inconsistency 配置对象 data_nature 一致性
--   v_e01_time_quarter_inconsistency       时间/季度一致性
--   v_e01_cross_month_retest_trace         跨月复测追溯
-- ============================================================================

CREATE OR REPLACE VIEW v_e_case_status_inconsistency AS
SELECT c.id AS case_id,
       c.case_code,
       c.current_status AS cached_status,
       c.current_status_history_id AS cached_history_id,
       h.id AS expected_history_id,
       h.to_status AS expected_status,
       CASE
         WHEN h.id IS NULL THEN 'NO_EFFECTIVE_HISTORY'
         WHEN c.current_status_history_id<>h.id THEN 'CURRENT_HISTORY_ID_MISMATCH'
         WHEN c.current_status<>h.to_status THEN 'CURRENT_STATUS_MISMATCH'
         WHEN h.case_id<>c.id THEN 'CURRENT_HISTORY_WRONG_CASE'
       END AS issue_code
FROM e_closure_case c
LEFT JOIN v_e_case_current_history h ON h.case_id=c.id
WHERE h.id IS NULL
   OR c.current_status_history_id IS NULL
   OR c.current_status_history_id<>h.id
   OR c.current_status<>h.to_status
UNION ALL
SELECT c.id AS case_id,
       c.case_code,
       c.current_status AS cached_status,
       c.current_status_history_id AS cached_history_id,
       target.id AS expected_history_id,
       target.to_status AS expected_status,
       'CORRECTION_TARGET_NOT_IMMEDIATE_PREVIOUS_HISTORY' AS issue_code
FROM e_case_status_history correction
JOIN e_case_status_history target ON target.id=correction.correction_of_history_id
JOIN e_closure_case c ON c.id=correction.case_id
WHERE correction.action_code='CORRECT_HISTORY'
  AND (target.case_id<>correction.case_id OR target.sequence_no<>correction.sequence_no-1);

CREATE OR REPLACE VIEW v_e01_event_result_inconsistency AS
SELECT ev.id AS event_id, ev.original_result_id AS result_id, ev.case_id, 'EVENT_CASE_DOMAIN_MISMATCH' AS issue_code
FROM e01_exceed_event ev JOIN e_closure_case c ON c.id=ev.case_id
WHERE ev.effective_status='EFFECTIVE' AND c.case_domain<>'E01_EXCEED'
UNION ALL
SELECT ev.id, r.id, ev.case_id, 'ORIGINAL_RESULT_NOT_VALID_INITIAL_EXCEEDED'
FROM e01_exceed_event ev JOIN e01_factor_result r ON r.id=ev.original_result_id
WHERE ev.effective_status='EFFECTIVE'
  AND NOT(r.test_stage='INITIAL' AND r.judgement='EXCEEDED' AND r.result_validity='VALID' AND r.effective_status='EFFECTIVE')
UNION ALL
SELECT ev.id, r.id, ev.case_id, 'EVENT_CATEGORY_SAMPLE_MISMATCH'
FROM e01_exceed_event ev
JOIN e01_factor_result r ON r.id=ev.original_result_id
JOIN e01_monitor_sample s ON s.id=r.sample_id
WHERE ev.effective_status='EFFECTIVE' AND ev.event_category<>s.monitor_category
UNION ALL
SELECT ev.id, r.id, ev.case_id, 'CHAIN_DATA_NATURE_MISMATCH'
FROM e01_exceed_event ev
JOIN e01_factor_result r ON r.id=ev.original_result_id
JOIN e01_monitor_sample s ON s.id=r.sample_id
JOIN e01_monitor_batch b ON b.id=s.batch_id
JOIN e01_monitor_point p ON p.id=s.point_id
JOIN e_closure_case c ON c.id=ev.case_id
LEFT JOIN e01_standard_version sv ON sv.id=r.standard_version_id
WHERE ev.effective_status='EFFECTIVE' AND (
      ev.data_nature<>r.data_nature OR ev.is_demo<>r.is_demo
   OR r.data_nature<>s.data_nature OR r.is_demo<>s.is_demo
   OR s.data_nature<>b.data_nature OR s.is_demo<>b.is_demo
   OR s.data_nature<>p.data_nature OR s.is_demo<>p.is_demo
   OR ev.data_nature<>c.data_nature OR ev.is_demo<>c.is_demo
   OR (sv.id IS NOT NULL AND (sv.data_nature<>r.data_nature OR sv.is_demo<>r.is_demo)))
UNION ALL
SELECT ev.id, r.id, ev.case_id, 'FORMAL_CHAIN_REFERENCES_NONFORMAL_OR_UNVERIFIED_OBJECT'
FROM e01_exceed_event ev
JOIN e01_factor_result r ON r.id=ev.original_result_id
JOIN e01_monitor_sample s ON s.id=r.sample_id
JOIN e01_monitor_batch b ON b.id=s.batch_id
JOIN e01_monitor_point p ON p.id=s.point_id
JOIN e_closure_case c ON c.id=ev.case_id
LEFT JOIN e01_standard_version sv ON sv.id=r.standard_version_id
WHERE ev.effective_status='EFFECTIVE' AND ev.data_nature='formal' AND (
      ev.is_demo<>0 OR r.data_nature<>'formal' OR r.is_demo<>0
   OR s.data_nature<>'formal' OR s.is_demo<>0
   OR b.data_nature<>'formal' OR b.is_demo<>0
   OR p.data_nature<>'formal' OR p.is_demo<>0
   OR c.data_nature<>'formal' OR c.is_demo<>0
   OR sv.id IS NULL OR sv.data_nature<>'formal' OR sv.is_demo<>0
   OR p.verification_status<>'VERIFIED' OR b.effective_status<>'EFFECTIVE' OR sv.effective_status<>'EFFECTIVE')
UNION ALL
SELECT ev.id, r.id, ev.case_id, 'CASE_SOURCE_KEY_MISMATCH'
FROM e01_exceed_event ev
JOIN e01_factor_result r ON r.id=ev.original_result_id
JOIN e_closure_case c ON c.id=ev.case_id
WHERE ev.effective_status='EFFECTIVE'
  AND (c.source_table<>'e01_factor_result' OR c.source_record_id<>r.id OR c.source_business_key<>CONCAT('E01_RESULT:',r.result_code))
UNION ALL
SELECT MIN(ev.id), ev.original_result_id, MIN(ev.case_id), 'MULTIPLE_EFFECTIVE_EVENTS_FOR_RESULT'
FROM e01_exceed_event ev
WHERE ev.effective_status='EFFECTIVE'
GROUP BY ev.original_result_id HAVING COUNT(*)>1
UNION ALL
SELECT ev.id, ev.original_result_id, ev.case_id, 'EVENT_MISSING_SINGLE_EFFECTIVE_CASE'
FROM e01_exceed_event ev
LEFT JOIN e_closure_case c ON c.id=ev.case_id AND c.effective_status='EFFECTIVE'
WHERE ev.effective_status='EFFECTIVE' AND c.id IS NULL
UNION ALL
SELECT NULL, r.id, NULL, 'EFFECTIVE_INITIAL_EXCEED_RESULT_MISSING_EVENT'
FROM e01_factor_result r
JOIN e01_monitor_sample s ON s.id=r.sample_id
JOIN e01_monitor_batch b ON b.id=s.batch_id
JOIN e01_monitor_point p ON p.id=s.point_id
WHERE r.test_stage='INITIAL' AND r.judgement='EXCEEDED' AND r.result_validity='VALID'
  AND r.effective_status='EFFECTIVE' AND r.data_nature='formal' AND r.is_demo=0
  AND s.sample_status='VALID' AND s.effective_status='EFFECTIVE' AND s.data_nature='formal' AND s.is_demo=0
  AND b.batch_status='EFFECTIVE' AND b.effective_status='EFFECTIVE' AND b.data_nature='formal' AND b.is_demo=0
  AND p.effective_status='EFFECTIVE' AND p.data_nature='formal' AND p.is_demo=0
  AND NOT EXISTS (SELECT 1 FROM e01_exceed_event ev WHERE ev.original_result_id=r.id AND ev.effective_status='EFFECTIVE')
UNION ALL
SELECT ev.id, ev.original_result_id, ev.case_id, 'CLOSED_EVENT_MISSING_RETEST_REVIEW_OR_CLOSURE_BASIS'
FROM e01_exceed_event ev
JOIN e_closure_case c ON c.id=ev.case_id
WHERE ev.effective_status='EFFECTIVE' AND c.current_status='CLOSED'
  AND (ev.latest_retest_outcome<>'COMPLIANT'
    OR NOT EXISTS (SELECT 1 FROM e01_retest_round rr WHERE rr.event_id=ev.id AND rr.effective_status='EFFECTIVE' AND rr.outcome='COMPLIANT' AND rr.review_status='PASSED')
    OR NOT EXISTS (SELECT 1 FROM v_e_case_effective_history_leaf h WHERE h.case_id=c.id AND h.action_code='REVIEW_PASS')
    OR NOT EXISTS (SELECT 1 FROM v_e_case_effective_history_leaf h WHERE h.case_id=c.id AND h.action_code='CLOSE_CASE')
    OR NOT EXISTS (SELECT 1 FROM e_case_evidence ce WHERE ce.case_id=c.id AND ce.evidence_role='CLOSURE_DOCUMENT' AND ce.validity_status='VALID' AND ce.verification_status='VERIFIED' AND ce.data_nature='formal' AND ce.is_demo=0));

CREATE OR REPLACE VIEW v_e01_retest_chain_inconsistency AS
SELECT l.id AS link_id, rr.event_id, l.retest_round_id, l.factor_result_id, l.original_result_id, 'LINK_RESULT_NOT_RETEST' AS issue_code
FROM e01_retest_result_link l
JOIN e01_retest_round rr ON rr.id=l.retest_round_id
JOIN e01_factor_result r ON r.id=l.factor_result_id
WHERE l.effective_status='EFFECTIVE' AND r.test_stage<>'RETEST'
UNION ALL
SELECT l.id, rr.event_id, l.retest_round_id, l.factor_result_id, l.original_result_id, 'ORIGINAL_NOT_VALID_INITIAL_EXCEEDED'
FROM e01_retest_result_link l
JOIN e01_retest_round rr ON rr.id=l.retest_round_id
JOIN e01_factor_result o ON o.id=l.original_result_id
WHERE l.effective_status='EFFECTIVE'
  AND NOT(o.test_stage='INITIAL' AND o.judgement='EXCEEDED' AND o.result_validity='VALID' AND o.effective_status='EFFECTIVE')
UNION ALL
SELECT l.id, rr.event_id, l.retest_round_id, l.factor_result_id, l.original_result_id, 'ORIGINAL_NOT_EVENT_ORIGINAL'
FROM e01_retest_result_link l
JOIN e01_retest_round rr ON rr.id=l.retest_round_id
JOIN e01_exceed_event ev ON ev.id=rr.event_id
WHERE l.effective_status='EFFECTIVE' AND (l.event_id<>ev.id OR l.original_result_id<>ev.original_result_id)
UNION ALL
SELECT l.id, rr.event_id, l.retest_round_id, l.factor_result_id, l.original_result_id, 'RETEST_RESULT_BATCH_ROUND_MISMATCH'
FROM e01_retest_result_link l
JOIN e01_retest_round rr ON rr.id=l.retest_round_id
JOIN e01_factor_result r ON r.id=l.factor_result_id
JOIN e01_monitor_sample s ON s.id=r.sample_id
WHERE l.effective_status='EFFECTIVE' AND s.batch_id<>rr.retest_batch_id
UNION ALL
SELECT l.id, rr.event_id, l.retest_round_id, l.factor_result_id, l.original_result_id, 'RETEST_FACTOR_OR_CATEGORY_MISMATCH'
FROM e01_retest_result_link l
JOIN e01_retest_round rr ON rr.id=l.retest_round_id
JOIN e01_factor_result r ON r.id=l.factor_result_id
JOIN e01_factor_result o ON o.id=l.original_result_id
JOIN e01_monitor_sample rs ON rs.id=r.sample_id
JOIN e01_monitor_sample os ON os.id=o.sample_id
WHERE l.effective_status='EFFECTIVE' AND (NOT(r.factor_id<=>o.factor_id) OR rs.monitor_category<>os.monitor_category)
UNION ALL
SELECT MIN(l.id), MIN(l.event_id), MIN(l.retest_round_id), l.factor_result_id, MIN(l.original_result_id), 'RETEST_RESULT_LINKED_TO_MULTIPLE_ORIGINALS'
FROM e01_retest_result_link l
WHERE l.effective_status='EFFECTIVE'
GROUP BY l.factor_result_id HAVING COUNT(DISTINCT l.original_result_id)>1
UNION ALL
SELECT NULL, ev.id, NULL, NULL, ev.original_result_id, 'CURRENT_RETEST_ROUND_NOT_MAX_EFFECTIVE_ROUND'
FROM e01_exceed_event ev
WHERE ev.effective_status='EFFECTIVE'
  AND ev.current_retest_round<>COALESCE((SELECT MAX(rr.round_no) FROM e01_retest_round rr WHERE rr.event_id=ev.id AND rr.effective_status='EFFECTIVE'),0)
UNION ALL
SELECT NULL, ev.id, rr.id, NULL, ev.original_result_id, 'LATEST_RETEST_OUTCOME_MISMATCH'
FROM e01_exceed_event ev
JOIN e01_retest_round rr ON rr.event_id=ev.id AND rr.effective_status='EFFECTIVE' AND rr.round_no=(SELECT MAX(x.round_no) FROM e01_retest_round x WHERE x.event_id=ev.id AND x.effective_status='EFFECTIVE')
WHERE ev.effective_status='EFFECTIVE' AND ev.latest_retest_outcome<>rr.outcome
UNION ALL
SELECT l.id, rr.event_id, rr.id, l.factor_result_id, l.original_result_id, 'RETEST_ROUND_OUTCOME_RESULT_MISMATCH'
FROM e01_retest_round rr
LEFT JOIN e01_retest_result_link l ON l.retest_round_id=rr.id AND l.effective_status='EFFECTIVE'
LEFT JOIN e01_factor_result r ON r.id=l.factor_result_id
WHERE rr.effective_status='EFFECTIVE'
  AND (l.id IS NULL OR (rr.outcome='COMPLIANT' AND r.judgement<>'COMPLIANT') OR (rr.outcome='STILL_EXCEEDED' AND r.judgement<>'EXCEEDED') OR (rr.outcome='NO_JUDGEMENT' AND r.judgement<>'NO_JUDGEMENT'))
UNION ALL
SELECT NULL, ev.id, NULL, NULL, ev.original_result_id, 'CLOSED_CHAIN_MISSING_COMPLIANT_RETEST_REVIEW_CLOSURE'
FROM e01_exceed_event ev
JOIN e_closure_case c ON c.id=ev.case_id
WHERE ev.effective_status='EFFECTIVE' AND c.current_status='CLOSED'
  AND (ev.latest_retest_outcome<>'COMPLIANT'
    OR NOT EXISTS (SELECT 1 FROM e01_retest_round rr WHERE rr.event_id=ev.id AND rr.effective_status='EFFECTIVE' AND rr.outcome='COMPLIANT' AND rr.review_status='PASSED')
    OR NOT EXISTS (SELECT 1 FROM v_e_case_effective_history_leaf h WHERE h.case_id=c.id AND h.action_code='REVIEW_PASS')
    OR NOT EXISTS (SELECT 1 FROM v_e_case_effective_history_leaf h WHERE h.case_id=c.id AND h.action_code='CLOSE_CASE')
    OR NOT EXISTS (SELECT 1 FROM e_case_evidence ce WHERE ce.case_id=c.id AND ce.evidence_role='CLOSURE_DOCUMENT' AND ce.validity_status='VALID' AND ce.verification_status='VERIFIED' AND ce.data_nature='formal' AND ce.is_demo=0));

CREATE OR REPLACE VIEW v_e01_core_data_nature_inconsistency AS
SELECT 'BATCH_SAMPLE' AS relation_name, s.id AS entity_id, 'SAMPLE_DIFFERS_FROM_BATCH' AS issue_code
FROM e01_monitor_sample s JOIN e01_monitor_batch b ON b.id=s.batch_id
WHERE s.data_nature<>b.data_nature OR s.is_demo<>b.is_demo
UNION ALL SELECT 'POINT_SAMPLE',s.id,'SAMPLE_DIFFERS_FROM_POINT'
FROM e01_monitor_sample s JOIN e01_monitor_point p ON p.id=s.point_id WHERE s.data_nature<>p.data_nature OR s.is_demo<>p.is_demo
UNION ALL SELECT 'SAMPLE_RESULT',r.id,'RESULT_DIFFERS_FROM_SAMPLE'
FROM e01_factor_result r JOIN e01_monitor_sample s ON s.id=r.sample_id WHERE r.data_nature<>s.data_nature OR r.is_demo<>s.is_demo
UNION ALL SELECT 'RESULT_EVENT',ev.id,'EVENT_DIFFERS_FROM_RESULT'
FROM e01_exceed_event ev JOIN e01_factor_result r ON r.id=ev.original_result_id WHERE ev.data_nature<>r.data_nature OR ev.is_demo<>r.is_demo
UNION ALL SELECT 'EVENT_CASE',c.id,'CASE_DIFFERS_FROM_EVENT'
FROM e01_exceed_event ev JOIN e_closure_case c ON c.id=ev.case_id WHERE ev.data_nature<>c.data_nature OR ev.is_demo<>c.is_demo
UNION ALL SELECT 'CASE_HISTORY',h.id,'HISTORY_DIFFERS_FROM_CASE'
FROM e_case_status_history h JOIN e_closure_case c ON c.id=h.case_id WHERE h.data_nature<>c.data_nature OR h.is_demo<>c.is_demo
UNION ALL SELECT 'CASE_EVIDENCE',ce.id,'EVIDENCE_DIFFERS_FROM_CASE'
FROM e_case_evidence ce JOIN e_closure_case c ON c.id=ce.case_id WHERE ce.data_nature<>c.data_nature OR ce.is_demo<>c.is_demo
UNION ALL SELECT 'EVENT_RECTIFICATION_ROUND',er.id,'RECTIFICATION_ROUND_DIFFERS_FROM_EVENT'
FROM e01_rectification_round er JOIN e01_exceed_event ev ON ev.id=er.event_id WHERE er.data_nature<>ev.data_nature OR er.is_demo<>ev.is_demo
UNION ALL SELECT 'EVENT_RETEST_ROUND',rr.id,'RETEST_ROUND_DIFFERS_FROM_EVENT'
FROM e01_retest_round rr JOIN e01_exceed_event ev ON ev.id=rr.event_id WHERE rr.data_nature<>ev.data_nature OR rr.is_demo<>ev.is_demo
UNION ALL SELECT 'RETEST_RESULT_LINK',l.id,'RETEST_LINK_CHAIN_NATURE_MISMATCH'
FROM e01_retest_result_link l
JOIN e01_retest_round rr ON rr.id=l.retest_round_id
JOIN e01_factor_result r ON r.id=l.factor_result_id
JOIN e01_factor_result o ON o.id=l.original_result_id
WHERE l.data_nature<>rr.data_nature OR l.is_demo<>rr.is_demo OR l.data_nature<>r.data_nature OR l.is_demo<>r.is_demo OR l.data_nature<>o.data_nature OR l.is_demo<>o.is_demo
UNION ALL SELECT 'CASE_TASK_LINK',l.id,'TASK_LINK_CHAIN_NATURE_MISMATCH'
FROM e_case_rectification_link l
JOIN e_closure_case c ON c.id=l.case_id
JOIN e_rectification_task t ON t.id=l.task_id
WHERE l.data_nature<>c.data_nature OR l.is_demo<>c.is_demo OR l.data_nature<>t.data_nature OR l.is_demo<>t.is_demo;

CREATE OR REPLACE VIEW v_e01_configuration_data_nature_inconsistency AS
SELECT 'PLAN_ITEM_PLAN' AS relation_name, pi.id AS entity_id, 'PLAN_ITEM_DIFFERS_FROM_PLAN' AS issue_code
FROM e01_monitor_plan_item pi JOIN e01_monitor_plan p ON p.id=pi.plan_id
WHERE pi.data_nature<>p.data_nature OR pi.is_demo<>p.is_demo
UNION ALL SELECT 'PLAN_ITEM_POINT',pi.id,'PLAN_ITEM_DIFFERS_FROM_POINT'
FROM e01_monitor_plan_item pi JOIN e01_monitor_point p ON p.id=pi.point_id
WHERE pi.data_nature<>p.data_nature OR pi.is_demo<>p.is_demo
UNION ALL SELECT 'BATCH_PLAN',b.id,'BATCH_DIFFERS_FROM_PLAN'
FROM e01_monitor_batch b JOIN e01_monitor_plan p ON p.id=b.plan_id
WHERE b.data_nature<>p.data_nature OR b.is_demo<>p.is_demo
UNION ALL SELECT 'RESULT_FACTOR',r.id,'RESULT_DIFFERS_FROM_FACTOR'
FROM e01_factor_result r JOIN e01_factor_definition f ON f.id=r.factor_id
WHERE r.data_nature<>f.data_nature OR r.is_demo<>f.is_demo
UNION ALL SELECT 'STANDARD_LIMIT_STANDARD',sl.id,'LIMIT_DIFFERS_FROM_STANDARD'
FROM e01_standard_limit sl JOIN e01_standard_version sv ON sv.id=sl.standard_version_id
WHERE sl.data_nature<>sv.data_nature OR sl.is_demo<>sv.is_demo
UNION ALL SELECT 'STANDARD_LIMIT_FACTOR',sl.id,'LIMIT_DIFFERS_FROM_FACTOR'
FROM e01_standard_limit sl JOIN e01_factor_definition f ON f.id=sl.factor_id
WHERE sl.data_nature<>f.data_nature OR sl.is_demo<>f.is_demo
UNION ALL SELECT 'RESULT_STANDARD',r.id,'RESULT_DIFFERS_FROM_STANDARD'
FROM e01_factor_result r JOIN e01_standard_version sv ON sv.id=r.standard_version_id
WHERE r.data_nature<>sv.data_nature OR r.is_demo<>sv.is_demo;

CREATE OR REPLACE VIEW v_e01_time_quarter_inconsistency AS
SELECT 'PLAN_YEAR_QUARTER_MISMATCH' AS issue_code, p.id AS entity_id, p.plan_code AS business_code
FROM e01_monitor_plan p WHERE CAST(LEFT(p.quarter_code,4) AS UNSIGNED)<>p.plan_year
UNION ALL SELECT 'BATCH_PLAN_QUARTER_MISMATCH',b.id,b.batch_code
FROM e01_monitor_batch b JOIN e01_monitor_plan p ON p.id=b.plan_id WHERE b.quarter_code<>p.quarter_code
UNION ALL SELECT 'SAMPLE_OUTSIDE_BATCH_RANGE',s.id,s.sample_code
FROM e01_monitor_sample s JOIN e01_monitor_batch b ON b.id=s.batch_id
WHERE s.sampled_at<b.sample_start_at OR s.sampled_at>b.sample_end_at OR (s.sample_end_at IS NOT NULL AND s.sample_end_at>b.sample_end_at)
UNION ALL SELECT 'PLANNED_ACTUAL_VARIANCE_NOT_TRACEABLE',s.id,s.sample_code
FROM e01_monitor_sample s
WHERE s.plan_item_id IS NOT NULL AND (s.planned_sample_at_snapshot IS NULL OR s.planned_actual_variance_minutes IS NULL OR s.planned_actual_variance_minutes<>TIMESTAMPDIFF(MINUTE,s.planned_sample_at_snapshot,s.sampled_at))
UNION ALL SELECT 'FIRST_EXCEEDED_AT_NOT_INITIAL_SAMPLE_AT',ev.id,ev.event_code
FROM e01_exceed_event ev JOIN e01_factor_result r ON r.id=ev.original_result_id JOIN e01_monitor_sample s ON s.id=r.sample_id
WHERE ev.first_exceeded_at<>s.sampled_at
UNION ALL SELECT 'RETEST_BEFORE_INITIAL_SAMPLE',rr.id,CONCAT(ev.event_code,'#',rr.round_no)
FROM e01_retest_round rr
JOIN e01_exceed_event ev ON ev.id=rr.event_id
JOIN e01_factor_result o ON o.id=ev.original_result_id
JOIN e01_monitor_sample os ON os.id=o.sample_id
WHERE rr.actual_sample_at IS NOT NULL AND rr.actual_sample_at<os.sampled_at
UNION ALL SELECT 'CLOSURE_BEFORE_LAST_RETEST_OR_REVIEW',ev.id,ev.event_code
FROM e01_exceed_event ev
JOIN e_closure_case c ON c.id=ev.case_id
WHERE c.current_status='CLOSED' AND (
    c.closed_at IS NULL OR ev.closure_confirmed_at IS NULL OR
    c.closed_at<COALESCE((SELECT MAX(COALESCE(rr.reviewed_at,rr.actual_sample_at)) FROM e01_retest_round rr WHERE rr.event_id=ev.id AND rr.effective_status='EFFECTIVE'),'1000-01-01') OR
    ev.closure_confirmed_at<COALESCE((SELECT MAX(COALESCE(rr.reviewed_at,rr.actual_sample_at)) FROM e01_retest_round rr WHERE rr.event_id=ev.id AND rr.effective_status='EFFECTIVE'),'1000-01-01'));

CREATE OR REPLACE VIEW v_e01_cross_month_retest_trace AS
SELECT ev.id AS event_id,
       ev.event_code,
       o.id AS original_result_id,
       os.sampled_at AS initial_sampled_at,
       DATE_FORMAT(os.sampled_at,'%Y-%m') AS exceed_statistic_month,
       rr.id AS retest_round_id,
       rr.round_no,
       rr.actual_sample_at AS retest_sampled_at,
       DATE_FORMAT(rr.actual_sample_at,'%Y-%m') AS retest_month,
       rr.outcome
FROM e01_exceed_event ev
JOIN e01_factor_result o ON o.id=ev.original_result_id
JOIN e01_monitor_sample os ON os.id=o.sample_id
JOIN e01_retest_round rr ON rr.event_id=ev.id AND rr.effective_status='EFFECTIVE'
WHERE rr.actual_sample_at IS NOT NULL
  AND DATE_FORMAT(rr.actual_sample_at,'%Y-%m')<>DATE_FORMAT(os.sampled_at,'%Y-%m');
