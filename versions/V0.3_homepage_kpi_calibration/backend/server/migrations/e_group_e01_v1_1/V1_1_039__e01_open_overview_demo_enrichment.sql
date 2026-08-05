-- ============================================================================
-- V1_1_039__e01_open_overview_demo_enrichment.sql
-- E01 一级总览演示补齐：
-- 1) 新增水质超标未闭环演示事项（原水质样本均为 COMPLIANT，无超标事件）
-- 2) 将已闭环空气演示事项恢复为整改中，供“仅未闭环”总览同时展示三类
-- 仅操作 data_nature='demo' / is_demo=1，不触碰正式数据
-- ============================================================================

-- 空气演示事项：重新打开为整改中（保留历史闭环轨迹记录，仅改当前状态）
UPDATE e_closure_case
SET current_status = 'RECTIFYING',
    closed_at = NULL,
    closure_reason = NULL,
    current_status_history_id = 926013,
    row_version = row_version + 1,
    updated_at = CURRENT_TIMESTAMP(6)
WHERE id = 925002 AND is_demo = 1 AND data_nature = 'demo';

UPDATE e01_exceed_event
SET current_retest_round = 0,
    latest_retest_outcome = 'NOT_TESTED',
    closure_confirmed_at = NULL,
    updated_at = CURRENT_TIMESTAMP(6)
WHERE id = 927002 AND is_demo = 1 AND data_nature = 'demo';

-- 水质超标演示：新批次 / 样本 / 超标因子结果（悬浮物）
INSERT INTO e01_monitor_batch
  (id, batch_code, plan_id, quarter_code, report_no, testing_provider_name,
   sample_start_at, sample_end_at, report_issued_at, received_at, batch_status,
   idempotency_key, data_nature, is_demo, effective_status, effective_at)
VALUES
  (922005, 'BATCH-TJ1-WATER-20260715', 916001, '2026-Q3', 'LYHJ-WATER-2026-0715',
   '河南交通环境监测技术中心',
   '2026-07-15 09:00:00', '2026-07-15 10:00:00', '2026-07-16 10:00:00', '2026-07-16 14:00:00',
   'EFFECTIVE', 'E01:TJ1:WATER:20260715', 'demo', 1, 'EFFECTIVE', '2026-07-16 14:00:00')
ON DUPLICATE KEY UPDATE batch_status=VALUES(batch_status), effective_status=VALUES(effective_status);

INSERT INTO e01_monitor_sample
  (id, sample_code, batch_id, plan_item_id, point_id, monitor_category,
   sampled_at, sample_end_at, planned_sample_at_snapshot, planned_actual_variance_minutes,
   sample_no, idempotency_key, sample_status, data_nature, is_demo,
   verification_status, effective_status, effective_at)
VALUES
  (923005, 'SAMPLE-TJ1-WATER-20260715', 922005, 917001, 914001, 'WATER',
   '2026-07-15 09:20:00', '2026-07-15 09:40:00', '2026-07-15 09:00:00', 20,
   'W-20260715-01', 'E01:SAMPLE:TJ1:WATER:20260715', 'VALID', 'demo', 1,
   'VERIFIED', 'EFFECTIVE', '2026-07-16 14:00:00')
ON DUPLICATE KEY UPDATE sample_status=VALUES(sample_status), effective_status=VALUES(effective_status);

INSERT INTO e01_factor_result
  (id, result_code, sample_id, factor_id, standard_version_id, test_stage, judgement, result_validity,
   detected_value_raw, limit_value_raw, standard_name_snapshot, reported_factor_name, reported_unit,
   judgement_source, effective_status, data_nature, is_demo)
VALUES
  (924008, 'RESULT-TJ1-WATER-SS-20260715', 923005, 919002, 920001, 'INITIAL', 'EXCEEDED', 'VALID',
   '45', '30', '施工期水环境控制要求', '悬浮物', 'mg/L',
   'IMPORTED', 'EFFECTIVE', 'demo', 1),
  (924009, 'RESULT-TJ1-WATER-PH-20260715', 923005, 919001, 920001, 'INITIAL', 'COMPLIANT', 'VALID',
   '7.1', '6—9', '地表水环境质量标准 GB 3838-2002', 'pH值', '无量纲',
   'IMPORTED', 'EFFECTIVE', 'demo', 1),
  (924010, 'RESULT-TJ1-WATER-COD-20260715', 923005, 919003, 920001, 'INITIAL', 'COMPLIANT', 'VALID',
   '16', '20', '地表水环境质量标准 GB 3838-2002', '化学需氧量', 'mg/L',
   'IMPORTED', 'EFFECTIVE', 'demo', 1)
ON DUPLICATE KEY UPDATE judgement=VALUES(judgement), detected_value_raw=VALUES(detected_value_raw),
  limit_value_raw=VALUES(limit_value_raw), effective_status=VALUES(effective_status);

INSERT INTO e_closure_case
  (id, case_code, case_domain, source_table, source_record_id, source_business_key, title, location_text,
   current_status, priority, severity, deadline, opened_at, closed_at, closure_reason,
   data_nature, is_demo, verification_status, effective_status, effective_at, row_version)
VALUES
  (925003, 'CASE-E01-WATER-20260715', 'E01_EXCEED', 'e01_factor_result', 924008, 'RESULT-TJ1-WATER-SS-20260715',
   'TJ-1施工营地排水口水环境超标整改', 'TJ-1｜K56+900｜施工营地排水口',
   'RECTIFYING', 'HIGH', 'GENERAL', '2026-07-28 18:00:00', '2026-07-16 14:30:00', NULL, NULL,
   'demo', 1, 'VERIFIED', 'EFFECTIVE', '2026-07-16 14:30:00', 1)
ON DUPLICATE KEY UPDATE title=VALUES(title), location_text=VALUES(location_text),
  current_status=VALUES(current_status), deadline=VALUES(deadline), effective_status=VALUES(effective_status);

INSERT INTO e_case_status_history
  (id, case_id, sequence_no, from_status, to_status, action_code, transition_result, action_at,
   operator_name, operator_org_name, comment, client_request_id, data_nature, is_demo)
VALUES
  (926020, 925003, 1, NULL, 'DISCOVERED', 'CREATE_CASE', 'SUCCESS', '2026-07-16 14:30:00',
   '环境监测专员', '安全环保部', '悬浮物超限，创建水质超标整改事项', 'SEED-CASE-WATER-01', 'demo', 1),
  (926021, 925003, 2, 'DISCOVERED', 'PENDING_RECTIFICATION', 'ISSUE_RECTIFICATION', 'SUCCESS', '2026-07-16 15:00:00',
   '环境管理负责人', '安全环保部', '要求核查排水口沉淀与清掏', 'SEED-CASE-WATER-02', 'demo', 1),
  (926022, 925003, 3, 'PENDING_RECTIFICATION', 'RECTIFYING', 'START_RECTIFICATION', 'SUCCESS', '2026-07-17 08:30:00',
   'TJ-1环保负责人', 'TJ-1项目经理部', '整改措施实施中', 'SEED-CASE-WATER-03', 'demo', 1)
ON DUPLICATE KEY UPDATE to_status=VALUES(to_status), action_at=VALUES(action_at), comment=VALUES(comment);

UPDATE e_closure_case SET current_status_history_id = 926022 WHERE id = 925003 AND is_demo = 1;

INSERT INTO e01_exceed_event
  (id, event_code, case_id, original_result_id, first_exceeded_at, event_category,
   current_retest_round, latest_retest_outcome, closure_confirmed_at,
   effective_status, effective_at, data_nature, is_demo)
VALUES
  (927003, 'EVENT-E01-WATER-20260715', 925003, 924008, '2026-07-15 09:40:00', 'WATER',
   0, 'NOT_TESTED', NULL,
   'EFFECTIVE', '2026-07-16 14:30:00', 'demo', 1)
ON DUPLICATE KEY UPDATE case_id=VALUES(case_id), original_result_id=VALUES(original_result_id),
  effective_status=VALUES(effective_status);

INSERT INTO e_rectification_task
  (id, task_code, title, deadline, task_status, data_nature, is_demo, effective_status, effective_at)
VALUES
  (928003, 'TASK-E01-WATER-20260715', '清掏排水口沉淀池并加强巡检', '2026-07-28 18:00:00',
   'IN_PROGRESS', 'demo', 1, 'EFFECTIVE', '2026-07-16 15:00:00')
ON DUPLICATE KEY UPDATE title=VALUES(title), task_status=VALUES(task_status), effective_status=VALUES(effective_status);

INSERT INTO e_case_rectification_link
  (id, case_id, task_id, link_role, data_nature, is_demo, effective_status)
VALUES
  (929003, 925003, 928003, 'PRIMARY', 'demo', 1, 'EFFECTIVE')
ON DUPLICATE KEY UPDATE link_role=VALUES(link_role), effective_status=VALUES(effective_status);

INSERT INTO e01_rectification_round
  (id, event_id, round_no, task_id, started_at, submitted_at, rectification_summary, review_status,
   data_nature, is_demo, effective_status, effective_at)
VALUES
  (930003, 927003, 1, 928003, '2026-07-17 08:30:00', NULL, '沉淀池清掏与排水口巡检整改中', 'PENDING_REVIEW',
   'demo', 1, 'EFFECTIVE', '2026-07-17 08:30:00')
ON DUPLICATE KEY UPDATE rectification_summary=VALUES(rectification_summary), review_status=VALUES(review_status);
