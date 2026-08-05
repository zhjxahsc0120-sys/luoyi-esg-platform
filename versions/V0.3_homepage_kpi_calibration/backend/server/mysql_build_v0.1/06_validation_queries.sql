USE luoyi_esg;
SET NAMES utf8mb4;

SELECT 'KPI_COUNT' AS check_item, COUNT(*) AS actual_value, 12 AS expected_value
FROM indicator_result;

SELECT 'S01_VALUE' AS check_item, CAST(value AS UNSIGNED) AS actual_value, 368 AS expected_value
FROM indicator_result
WHERE indicator_code = 'S01';

SELECT 'UPLOAD_TASK_COUNT' AS check_item, COUNT(*) AS actual_value, 12 AS expected_value
FROM upload_task;

SELECT 'TASK_T1_REQUIREMENT_COUNT' AS check_item, COUNT(*) AS actual_value, 7 AS expected_value
FROM upload_task_requirement
WHERE task_id = 't1';

SELECT 'TASK_T1_VALIDATION' AS check_item, completed, missing, abnormal
FROM v_task_detail_validation
WHERE task_id = 't1';

SELECT 'DOCUMENT_SAMPLE_COUNT' AS check_item, COUNT(*) AS actual_value, 10 AS expected_value
FROM document_record;

SELECT 'DOCUMENT_MODULE_COVERAGE' AS check_item, GROUP_CONCAT(DISTINCT module_code ORDER BY module_code) AS actual_value, 'E,G,S' AS expected_value
FROM document_record;

SELECT 'REVIEW_COUNT' AS check_item, COUNT(*) AS actual_value, 7 AS expected_value
FROM review_record;

SELECT 'REVIEW_TIMELINE_COUNT' AS check_item, COUNT(*) AS actual_value, '>=19' AS expected_value
FROM review_timeline;

SELECT 'REVIEW_REQUIREMENT_COUNT' AS check_item, COUNT(*) AS actual_value, '>=5' AS expected_value
FROM review_requirement;

SELECT 'FIELD_MAPPING_COUNT' AS check_item, COUNT(*) AS actual_value, '>=27' AS expected_value
FROM ai_field_mapping_rule;

SELECT 'PARSE_JOB_COUNT' AS check_item, COUNT(*) AS actual_value, 3 AS expected_value
FROM ai_parse_job;

SELECT 'MATCH_CANDIDATE_COUNT' AS check_item, COUNT(*) AS actual_value, '>=1' AS expected_value
FROM task_match_candidate;

SELECT 'DASHBOARD_KPI_VALUES' AS check_item, indicator_code, value, unit
FROM v_dashboard_kpi_current
ORDER BY group_code, display_order;
