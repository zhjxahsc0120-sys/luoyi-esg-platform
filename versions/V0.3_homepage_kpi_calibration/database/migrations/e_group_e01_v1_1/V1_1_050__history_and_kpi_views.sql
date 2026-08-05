-- ============================================================================
-- V1_1_050__history_and_kpi_views.sql
-- E组公共闭环 & E01 V1.1 增量迁移 — 历史与 KPI 视图
-- ============================================================================
-- 包含 6 个视图：
--   v_e_case_effective_history_leaf  案件有效历史叶子节点（排除已被纠正的记录）
--   v_e_case_current_history         案件当前有效历史（最新 sequence_no）
--   v_e01_monthly_exceed_item        月度超标明细
--   v_e01_monthly_exceed_count        月度超标计数
--   v_e01_open_exceed_event          未关闭超标事件
--   v_e01_open_exceed_count          未关闭超标事件计数
-- ============================================================================

CREATE OR REPLACE VIEW v_e_case_effective_history_leaf AS
SELECT h.*
FROM e_case_status_history h
WHERE NOT EXISTS (
    SELECT 1
    FROM e_case_status_history c
    WHERE c.case_id=h.case_id
      AND c.correction_of_history_id=h.id
);

CREATE OR REPLACE VIEW v_e_case_current_history AS
SELECT l.*
FROM v_e_case_effective_history_leaf l
WHERE NOT EXISTS (
    SELECT 1
    FROM v_e_case_effective_history_leaf n
    WHERE n.case_id=l.case_id
      AND n.sequence_no>l.sequence_no
);

CREATE OR REPLACE VIEW v_e01_monthly_exceed_item AS
SELECT DATE_FORMAT(s.sampled_at,'%Y-%m') AS statistic_month,
       r.id AS factor_result_id,
       r.result_code,
       r.reported_factor_name,
       r.reported_unit,
       r.detected_value_raw,
       r.limit_value_raw,
       r.standard_name_snapshot,
       s.id AS sample_id,
       s.sampled_at,
       s.monitor_category,
       b.id AS batch_id,
       b.batch_code,
       p.id AS point_id,
       p.point_code,
       p.point_name,
       ev.id AS event_id,
       ev.event_code,
       ev.case_id
FROM e01_factor_result r
JOIN e01_monitor_sample s ON s.id=r.sample_id
JOIN e01_monitor_batch b ON b.id=s.batch_id
JOIN e01_monitor_point p ON p.id=s.point_id
JOIN e01_standard_version sv ON sv.id=r.standard_version_id
LEFT JOIN e01_factor_definition fd ON fd.id=r.factor_id
LEFT JOIN e01_exceed_event ev
  ON ev.original_result_id=r.id
 AND ev.effective_status='EFFECTIVE'
 AND ev.data_nature='formal'
 AND ev.is_demo=0
WHERE r.test_stage='INITIAL'
  AND r.judgement='EXCEEDED'
  AND r.result_validity='VALID'
  AND r.effective_status='EFFECTIVE'
  AND r.data_nature='formal'
  AND r.is_demo=0
  AND s.sample_status='VALID'
  AND s.verification_status='VERIFIED'
  AND s.effective_status='EFFECTIVE'
  AND s.data_nature='formal'
  AND s.is_demo=0
  AND b.batch_status='EFFECTIVE'
  AND b.effective_status='EFFECTIVE'
  AND b.data_nature='formal'
  AND b.is_demo=0
  AND p.verification_status='VERIFIED'
  AND p.effective_status='EFFECTIVE'
  AND p.data_nature='formal'
  AND p.is_demo=0
  AND sv.verification_status='VERIFIED'
  AND sv.effective_status='EFFECTIVE'
  AND sv.data_nature='formal'
  AND sv.is_demo=0
  AND (fd.id IS NULL OR (fd.verification_status='VERIFIED' AND fd.effective_status='EFFECTIVE' AND fd.data_nature='formal' AND fd.is_demo=0));

CREATE OR REPLACE VIEW v_e01_monthly_exceed_count AS
SELECT statistic_month, monitor_category, COUNT(*) AS exceed_item_count
FROM v_e01_monthly_exceed_item
GROUP BY statistic_month, monitor_category;

CREATE OR REPLACE VIEW v_e01_open_exceed_event AS
SELECT ev.id AS event_id,
       ev.event_code,
       ev.original_result_id,
       ev.event_category,
       ev.first_exceeded_at,
       ev.latest_retest_outcome,
       c.id AS case_id,
       c.case_code,
       c.current_status
FROM e01_exceed_event ev
JOIN e01_factor_result r ON r.id=ev.original_result_id
JOIN e_closure_case c ON c.id=ev.case_id
WHERE ev.effective_status='EFFECTIVE'
  AND ev.data_nature='formal' AND ev.is_demo=0
  AND r.test_stage='INITIAL' AND r.judgement='EXCEEDED'
  AND r.result_validity='VALID' AND r.effective_status='EFFECTIVE'
  AND r.data_nature='formal' AND r.is_demo=0
  AND c.case_domain='E01_EXCEED'
  AND c.effective_status='EFFECTIVE'
  AND c.data_nature='formal' AND c.is_demo=0
  AND c.current_status NOT IN ('CLOSED','CANCELLED','MERGED');

CREATE OR REPLACE VIEW v_e01_open_exceed_count AS
SELECT COUNT(*) AS open_event_count FROM v_e01_open_exceed_event;
