USE luoyi_esg;
SET NAMES utf8mb4;

CREATE OR REPLACE VIEW v_dashboard_kpi_current AS
SELECT
  r.indicator_code,
  r.group_code,
  r.label,
  r.full_name,
  r.value,
  r.value_text,
  r.unit,
  r.display_order,
  r.calculated_at,
  r.published_at,
  d.indicator_name,
  d.source_table,
  d.calculation_desc
FROM indicator_result r
LEFT JOIN indicator_definition d ON d.indicator_code = r.indicator_code;

CREATE OR REPLACE VIEW v_workspace_summary_current AS
SELECT
  COUNT(*) AS current_todo,
  SUM(CASE WHEN status = '待上传' THEN 1 ELSE 0 END) AS pending_upload,
  SUM(CASE WHEN status = '待补正' THEN 1 ELSE 0 END) AS pending_correction,
  SUM(CASE WHEN status = '待提交' THEN 1 ELSE 0 END) AS pending_submit,
  SUM(CASE WHEN status = '审核中' THEN 1 ELSE 0 END) AS under_review,
  SUM(CASE WHEN deadline BETWEEN NOW() AND DATE_ADD(NOW(), INTERVAL 7 DAY) THEN 1 ELSE 0 END) AS due_soon,
  SUM(CASE WHEN status IN ('已完成', '已归档') THEN 1 ELSE 0 END) AS completed
FROM upload_task;

CREATE OR REPLACE VIEW v_document_summary_current AS
SELECT
  COUNT(*) AS sample_count,
  368 AS document_total,
  SUM(CASE WHEN uploaded_at >= '2026-08-01' THEN 1 ELSE 0 END) AS month_new_sample,
  24 AS month_new,
  6 AS pending_archive,
  SUM(CASE WHEN validity_status = '即将失效' THEN 1 ELSE 0 END) AS expiring_soon_sample,
  4 AS expiring_soon
FROM document_record;

CREATE OR REPLACE VIEW v_ai_parse_queue_current AS
SELECT
  j.id AS job_id,
  j.job_code,
  f.id AS file_id,
  f.original_name AS file_name,
  f.file_size,
  j.job_status,
  j.confidence,
  j.started_at,
  j.finished_at
FROM ai_parse_job j
JOIN file_asset f ON f.id = j.file_id;

CREATE OR REPLACE VIEW v_task_detail_validation AS
SELECT
  task_id,
  SUM(CASE WHEN status IN ('已关联', '审核通过') THEN 1 ELSE 0 END) AS completed,
  SUM(CASE WHEN status = '缺失' THEN 1 ELSE 0 END) AS missing,
  SUM(CASE WHEN status = '格式异常' THEN 1 ELSE 0 END) AS abnormal,
  COUNT(*) AS total_required_items
FROM upload_task_requirement
GROUP BY task_id;
