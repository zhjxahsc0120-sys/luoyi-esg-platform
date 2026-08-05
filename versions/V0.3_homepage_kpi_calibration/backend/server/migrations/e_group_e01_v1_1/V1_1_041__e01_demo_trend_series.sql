-- ============================================================================
-- V1_1_041__e01_demo_trend_series.sql
-- 为二级趋势图补齐 demo 时序（不新增正式标准、不另堆点位）
-- WATER 914001：+4 周；AIR 914003：+5 日均；NOISE 914002：+5 施工日昼夜
-- ============================================================================

-- ---------- WATER weekly (914001) ----------
INSERT INTO e01_monitor_batch
  (id, batch_code, plan_id, quarter_code, report_no, testing_provider_name,
   sample_start_at, sample_end_at, report_issued_at, received_at, batch_status,
   idempotency_key, data_nature, is_demo, effective_status, effective_at)
VALUES
  (922006, 'BATCH-TJ1-WATER-20260625', 916001, '2026-Q2', 'LYHJ-WATER-2026-0625', '河南交通环境监测技术中心',
   '2026-06-25 09:00:00', '2026-06-25 10:00:00', '2026-06-26 10:00:00', '2026-06-26 14:00:00', 'EFFECTIVE',
   'E01:TJ1:WATER:20260625', 'demo', 1, 'EFFECTIVE', '2026-06-26 14:00:00'),
  (922007, 'BATCH-TJ1-WATER-20260702', 916001, '2026-Q3', 'LYHJ-WATER-2026-0702', '河南交通环境监测技术中心',
   '2026-07-02 09:00:00', '2026-07-02 10:00:00', '2026-07-03 10:00:00', '2026-07-03 14:00:00', 'EFFECTIVE',
   'E01:TJ1:WATER:20260702', 'demo', 1, 'EFFECTIVE', '2026-07-03 14:00:00'),
  (922008, 'BATCH-TJ1-WATER-20260709', 916001, '2026-Q3', 'LYHJ-WATER-2026-0709', '河南交通环境监测技术中心',
   '2026-07-09 09:00:00', '2026-07-09 10:00:00', '2026-07-10 10:00:00', '2026-07-10 14:00:00', 'EFFECTIVE',
   'E01:TJ1:WATER:20260709', 'demo', 1, 'EFFECTIVE', '2026-07-10 14:00:00'),
  (922009, 'BATCH-TJ1-WATER-20260722', 916001, '2026-Q3', 'LYHJ-WATER-2026-0722', '河南交通环境监测技术中心',
   '2026-07-22 09:00:00', '2026-07-22 10:00:00', '2026-07-23 10:00:00', '2026-07-23 14:00:00', 'EFFECTIVE',
   'E01:TJ1:WATER:20260722', 'demo', 1, 'EFFECTIVE', '2026-07-23 14:00:00')
ON DUPLICATE KEY UPDATE batch_status=VALUES(batch_status), effective_status=VALUES(effective_status);

INSERT INTO e01_monitor_sample
  (id, sample_code, batch_id, plan_item_id, point_id, monitor_category,
   sampled_at, sample_end_at, planned_sample_at_snapshot, planned_actual_variance_minutes,
   sample_no, idempotency_key, sample_status, data_nature, is_demo,
   verification_status, effective_status, effective_at)
VALUES
  (923006, 'SAMPLE-TJ1-WATER-20260625', 922006, 917001, 914001, 'WATER',
   '2026-06-25 09:15:00', '2026-06-25 09:35:00', '2026-06-25 09:00:00', 15,
   'W-20260625-01', 'E01:SAMPLE:TJ1:WATER:20260625', 'VALID', 'demo', 1, 'VERIFIED', 'EFFECTIVE', '2026-06-26 14:00:00'),
  (923007, 'SAMPLE-TJ1-WATER-20260702', 922007, 917001, 914001, 'WATER',
   '2026-07-02 09:18:00', '2026-07-02 09:38:00', '2026-07-02 09:00:00', 18,
   'W-20260702-01', 'E01:SAMPLE:TJ1:WATER:20260702', 'VALID', 'demo', 1, 'VERIFIED', 'EFFECTIVE', '2026-07-03 14:00:00'),
  (923008, 'SAMPLE-TJ1-WATER-20260709', 922008, 917001, 914001, 'WATER',
   '2026-07-09 09:12:00', '2026-07-09 09:32:00', '2026-07-09 09:00:00', 12,
   'W-20260709-01', 'E01:SAMPLE:TJ1:WATER:20260709', 'VALID', 'demo', 1, 'VERIFIED', 'EFFECTIVE', '2026-07-10 14:00:00'),
  (923009, 'SAMPLE-TJ1-WATER-20260722', 922009, 917001, 914001, 'WATER',
   '2026-07-22 09:20:00', '2026-07-22 09:40:00', '2026-07-22 09:00:00', 20,
   'W-20260722-01', 'E01:SAMPLE:TJ1:WATER:20260722', 'VALID', 'demo', 1, 'VERIFIED', 'EFFECTIVE', '2026-07-23 14:00:00')
ON DUPLICATE KEY UPDATE sample_status=VALUES(sample_status), effective_status=VALUES(effective_status);

INSERT INTO e01_factor_result
  (id, result_code, sample_id, factor_id, standard_version_id, test_stage, judgement, result_validity,
   detected_value_raw, limit_value_raw, standard_name_snapshot, reported_factor_name, reported_unit,
   judgement_source, effective_status, data_nature, is_demo)
VALUES
  (924011, 'RESULT-TJ1-WATER-PH-20260625', 923006, 919001, 920001, 'INITIAL', 'COMPLIANT', 'VALID', '7.2', '6—9', '地表水环境质量标准 GB 3838-2002', 'pH值', '无量纲', 'IMPORTED', 'EFFECTIVE', 'demo', 1),
  (924012, 'RESULT-TJ1-WATER-SS-20260625', 923006, 919002, 920001, 'INITIAL', 'COMPLIANT', 'VALID', '22', '30', '施工期水环境控制要求', '悬浮物', 'mg/L', 'IMPORTED', 'EFFECTIVE', 'demo', 1),
  (924013, 'RESULT-TJ1-WATER-COD-20260625', 923006, 919003, 920001, 'INITIAL', 'COMPLIANT', 'VALID', '14', '20', '地表水环境质量标准 GB 3838-2002', '化学需氧量', 'mg/L', 'IMPORTED', 'EFFECTIVE', 'demo', 1),
  (924014, 'RESULT-TJ1-WATER-PH-20260702', 923007, 919001, 920001, 'INITIAL', 'COMPLIANT', 'VALID', '7.0', '6—9', '地表水环境质量标准 GB 3838-2002', 'pH值', '无量纲', 'IMPORTED', 'EFFECTIVE', 'demo', 1),
  (924015, 'RESULT-TJ1-WATER-SS-20260702', 923007, 919002, 920001, 'INITIAL', 'COMPLIANT', 'VALID', '28', '30', '施工期水环境控制要求', '悬浮物', 'mg/L', 'IMPORTED', 'EFFECTIVE', 'demo', 1),
  (924016, 'RESULT-TJ1-WATER-COD-20260702', 923007, 919003, 920001, 'INITIAL', 'COMPLIANT', 'VALID', '15', '20', '地表水环境质量标准 GB 3838-2002', '化学需氧量', 'mg/L', 'IMPORTED', 'EFFECTIVE', 'demo', 1),
  (924017, 'RESULT-TJ1-WATER-PH-20260709', 923008, 919001, 920001, 'INITIAL', 'COMPLIANT', 'VALID', '7.1', '6—9', '地表水环境质量标准 GB 3838-2002', 'pH值', '无量纲', 'IMPORTED', 'EFFECTIVE', 'demo', 1),
  (924018, 'RESULT-TJ1-WATER-SS-20260709', 923008, 919002, 920001, 'INITIAL', 'COMPLIANT', 'VALID', '34', '30', '施工期水环境控制要求', '悬浮物', 'mg/L', 'IMPORTED', 'EFFECTIVE', 'demo', 1),
  (924019, 'RESULT-TJ1-WATER-COD-20260709', 923008, 919003, 920001, 'INITIAL', 'COMPLIANT', 'VALID', '17', '20', '地表水环境质量标准 GB 3838-2002', '化学需氧量', 'mg/L', 'IMPORTED', 'EFFECTIVE', 'demo', 1),
  (924020, 'RESULT-TJ1-WATER-PH-20260722', 923009, 919001, 920001, 'INITIAL', 'COMPLIANT', 'VALID', '7.0', '6—9', '地表水环境质量标准 GB 3838-2002', 'pH值', '无量纲', 'IMPORTED', 'EFFECTIVE', 'demo', 1),
  (924021, 'RESULT-TJ1-WATER-SS-20260722', 923009, 919002, 920001, 'INITIAL', 'COMPLIANT', 'VALID', '31', '30', '施工期水环境控制要求', '悬浮物', 'mg/L', 'IMPORTED', 'EFFECTIVE', 'demo', 1),
  (924022, 'RESULT-TJ1-WATER-COD-20260722', 923009, 919003, 920001, 'INITIAL', 'COMPLIANT', 'VALID', '15', '20', '地表水环境质量标准 GB 3838-2002', '化学需氧量', 'mg/L', 'IMPORTED', 'EFFECTIVE', 'demo', 1)
ON DUPLICATE KEY UPDATE judgement=VALUES(judgement), detected_value_raw=VALUES(detected_value_raw), effective_status=VALUES(effective_status);

-- ---------- AIR daily PM10 (914003) ----------
INSERT INTO e01_monitor_batch
  (id, batch_code, plan_id, quarter_code, report_no, testing_provider_name,
   sample_start_at, sample_end_at, report_issued_at, received_at, batch_status,
   idempotency_key, data_nature, is_demo, effective_status, effective_at)
VALUES
  (922010, 'BATCH-TJ3-AIR-20260710', 916003, '2026-Q3', 'LYHJ-AIR-2026-0710', '河南交通环境监测技术中心',
   '2026-07-10 00:00:00', '2026-07-10 23:59:59', '2026-07-11 08:00:00', '2026-07-11 09:00:00', 'EFFECTIVE',
   'E01:TJ3:AIR:20260710', 'demo', 1, 'EFFECTIVE', '2026-07-11 09:00:00'),
  (922011, 'BATCH-TJ3-AIR-20260711', 916003, '2026-Q3', 'LYHJ-AIR-2026-0711', '河南交通环境监测技术中心',
   '2026-07-11 00:00:00', '2026-07-11 23:59:59', '2026-07-12 08:00:00', '2026-07-12 09:00:00', 'EFFECTIVE',
   'E01:TJ3:AIR:20260711', 'demo', 1, 'EFFECTIVE', '2026-07-12 09:00:00'),
  (922012, 'BATCH-TJ3-AIR-20260713', 916003, '2026-Q3', 'LYHJ-AIR-2026-0713', '河南交通环境监测技术中心',
   '2026-07-13 00:00:00', '2026-07-13 23:59:59', '2026-07-14 08:00:00', '2026-07-14 09:00:00', 'EFFECTIVE',
   'E01:TJ3:AIR:20260713', 'demo', 1, 'EFFECTIVE', '2026-07-14 09:00:00'),
  (922013, 'BATCH-TJ3-AIR-20260714', 916003, '2026-Q3', 'LYHJ-AIR-2026-0714', '河南交通环境监测技术中心',
   '2026-07-14 00:00:00', '2026-07-14 23:59:59', '2026-07-15 08:00:00', '2026-07-15 09:00:00', 'EFFECTIVE',
   'E01:TJ3:AIR:20260714', 'demo', 1, 'EFFECTIVE', '2026-07-15 09:00:00'),
  (922014, 'BATCH-TJ3-AIR-20260716', 916003, '2026-Q3', 'LYHJ-AIR-2026-0716', '河南交通环境监测技术中心',
   '2026-07-16 00:00:00', '2026-07-16 23:59:59', '2026-07-17 08:00:00', '2026-07-17 09:00:00', 'EFFECTIVE',
   'E01:TJ3:AIR:20260716', 'demo', 1, 'EFFECTIVE', '2026-07-17 09:00:00')
ON DUPLICATE KEY UPDATE batch_status=VALUES(batch_status), effective_status=VALUES(effective_status);

INSERT INTO e01_monitor_sample
  (id, sample_code, batch_id, plan_item_id, point_id, monitor_category,
   sampled_at, sample_end_at, planned_sample_at_snapshot, planned_actual_variance_minutes,
   sample_no, idempotency_key, sample_status, data_nature, is_demo,
   verification_status, effective_status, effective_at)
VALUES
  (923010, 'SAMPLE-TJ3-AIR-20260710', 922010, 917003, 914003, 'AIR',
   '2026-07-10 00:00:00', '2026-07-10 23:59:59', '2026-07-10 00:00:00', 0,
   'A-20260710-DAY', 'E01:SAMPLE:TJ3:AIR:20260710', 'VALID', 'demo', 1, 'VERIFIED', 'EFFECTIVE', '2026-07-11 09:00:00'),
  (923011, 'SAMPLE-TJ3-AIR-20260711', 922011, 917003, 914003, 'AIR',
   '2026-07-11 00:00:00', '2026-07-11 23:59:59', '2026-07-11 00:00:00', 0,
   'A-20260711-DAY', 'E01:SAMPLE:TJ3:AIR:20260711', 'VALID', 'demo', 1, 'VERIFIED', 'EFFECTIVE', '2026-07-12 09:00:00'),
  (923012, 'SAMPLE-TJ3-AIR-20260713', 922012, 917003, 914003, 'AIR',
   '2026-07-13 00:00:00', '2026-07-13 23:59:59', '2026-07-13 00:00:00', 0,
   'A-20260713-DAY', 'E01:SAMPLE:TJ3:AIR:20260713', 'VALID', 'demo', 1, 'VERIFIED', 'EFFECTIVE', '2026-07-14 09:00:00'),
  (923013, 'SAMPLE-TJ3-AIR-20260714', 922013, 917003, 914003, 'AIR',
   '2026-07-14 00:00:00', '2026-07-14 23:59:59', '2026-07-14 00:00:00', 0,
   'A-20260714-DAY', 'E01:SAMPLE:TJ3:AIR:20260714', 'VALID', 'demo', 1, 'VERIFIED', 'EFFECTIVE', '2026-07-15 09:00:00'),
  (923014, 'SAMPLE-TJ3-AIR-20260716', 922014, 917003, 914003, 'AIR',
   '2026-07-16 00:00:00', '2026-07-16 23:59:59', '2026-07-16 00:00:00', 0,
   'A-20260716-DAY', 'E01:SAMPLE:TJ3:AIR:20260716', 'VALID', 'demo', 1, 'VERIFIED', 'EFFECTIVE', '2026-07-17 09:00:00')
ON DUPLICATE KEY UPDATE sample_status=VALUES(sample_status), effective_status=VALUES(effective_status);

INSERT INTO e01_factor_result
  (id, result_code, sample_id, factor_id, standard_version_id, test_stage, judgement, result_validity,
   detected_value_raw, limit_value_raw, standard_name_snapshot, reported_factor_name, reported_unit,
   judgement_source, effective_status, data_nature, is_demo)
VALUES
  (924023, 'RESULT-TJ3-AIR-PM10-20260710', 923010, 919006, 920003, 'INITIAL', 'COMPLIANT', 'VALID', '98', '150', '环境空气质量标准 GB 3095-2012', 'PM10日均浓度', 'μg/m³', 'AUTO_LIMIT', 'EFFECTIVE', 'demo', 1),
  (924024, 'RESULT-TJ3-AIR-PM10-20260711', 923011, 919006, 920003, 'INITIAL', 'COMPLIANT', 'VALID', '132', '150', '环境空气质量标准 GB 3095-2012', 'PM10日均浓度', 'μg/m³', 'AUTO_LIMIT', 'EFFECTIVE', 'demo', 1),
  (924025, 'RESULT-TJ3-AIR-PM10-20260713', 923012, 919006, 920003, 'INITIAL', 'COMPLIANT', 'VALID', '171', '150', '环境空气质量标准 GB 3095-2012', 'PM10日均浓度', 'μg/m³', 'AUTO_LIMIT', 'EFFECTIVE', 'demo', 1),
  (924026, 'RESULT-TJ3-AIR-PM10-20260714', 923013, 919006, 920003, 'INITIAL', 'COMPLIANT', 'VALID', '148', '150', '环境空气质量标准 GB 3095-2012', 'PM10日均浓度', 'μg/m³', 'AUTO_LIMIT', 'EFFECTIVE', 'demo', 1),
  (924027, 'RESULT-TJ3-AIR-PM10-20260716', 923014, 919006, 920003, 'INITIAL', 'COMPLIANT', 'VALID', '105', '150', '环境空气质量标准 GB 3095-2012', 'PM10日均浓度', 'μg/m³', 'AUTO_LIMIT', 'EFFECTIVE', 'demo', 1)
ON DUPLICATE KEY UPDATE judgement=VALUES(judgement), detected_value_raw=VALUES(detected_value_raw), effective_status=VALUES(effective_status);

-- ---------- NOISE multi-day (914002) ----------
INSERT INTO e01_monitor_batch
  (id, batch_code, plan_id, quarter_code, report_no, testing_provider_name,
   sample_start_at, sample_end_at, report_issued_at, received_at, batch_status,
   idempotency_key, data_nature, is_demo, effective_status, effective_at)
VALUES
  (922015, 'BATCH-TJ2-NOISE-20260706', 916002, '2026-Q3', 'LYHJ-NOISE-2026-0706', '河南交通环境监测技术中心',
   '2026-07-06 14:00:00', '2026-07-06 22:30:00', '2026-07-07 10:00:00', '2026-07-07 11:00:00', 'EFFECTIVE',
   'E01:TJ2:NOISE:20260706', 'demo', 1, 'EFFECTIVE', '2026-07-07 11:00:00'),
  (922016, 'BATCH-TJ2-NOISE-20260707', 916002, '2026-Q3', 'LYHJ-NOISE-2026-0707', '河南交通环境监测技术中心',
   '2026-07-07 14:00:00', '2026-07-07 22:30:00', '2026-07-08 10:00:00', '2026-07-08 11:00:00', 'EFFECTIVE',
   'E01:TJ2:NOISE:20260707', 'demo', 1, 'EFFECTIVE', '2026-07-08 11:00:00'),
  (922017, 'BATCH-TJ2-NOISE-20260709', 916002, '2026-Q3', 'LYHJ-NOISE-2026-0709', '河南交通环境监测技术中心',
   '2026-07-09 14:00:00', '2026-07-09 22:30:00', '2026-07-10 10:00:00', '2026-07-10 11:00:00', 'EFFECTIVE',
   'E01:TJ2:NOISE:20260709', 'demo', 1, 'EFFECTIVE', '2026-07-10 11:00:00'),
  (922018, 'BATCH-TJ2-NOISE-20260710', 916002, '2026-Q3', 'LYHJ-NOISE-2026-0710', '河南交通环境监测技术中心',
   '2026-07-10 14:00:00', '2026-07-10 22:30:00', '2026-07-11 10:00:00', '2026-07-11 11:00:00', 'EFFECTIVE',
   'E01:TJ2:NOISE:20260710', 'demo', 1, 'EFFECTIVE', '2026-07-11 11:00:00'),
  (922019, 'BATCH-TJ2-NOISE-20260711', 916002, '2026-Q3', 'LYHJ-NOISE-2026-0711', '河南交通环境监测技术中心',
   '2026-07-11 14:00:00', '2026-07-11 22:30:00', '2026-07-12 10:00:00', '2026-07-12 11:00:00', 'EFFECTIVE',
   'E01:TJ2:NOISE:20260711', 'demo', 1, 'EFFECTIVE', '2026-07-12 11:00:00')
ON DUPLICATE KEY UPDATE batch_status=VALUES(batch_status), effective_status=VALUES(effective_status);

INSERT INTO e01_monitor_sample
  (id, sample_code, batch_id, plan_item_id, point_id, monitor_category,
   sampled_at, sample_end_at, planned_sample_at_snapshot, planned_actual_variance_minutes,
   sample_no, idempotency_key, sample_status, data_nature, is_demo,
   verification_status, effective_status, effective_at)
VALUES
  (923015, 'SAMPLE-TJ2-NOISE-20260706', 922015, 917002, 914002, 'NOISE',
   '2026-07-06 14:10:00', '2026-07-06 22:30:00', '2026-07-06 14:00:00', 10,
   'N-20260706-01', 'E01:SAMPLE:TJ2:NOISE:20260706', 'VALID', 'demo', 1, 'VERIFIED', 'EFFECTIVE', '2026-07-07 11:00:00'),
  (923016, 'SAMPLE-TJ2-NOISE-20260707', 922016, 917002, 914002, 'NOISE',
   '2026-07-07 14:10:00', '2026-07-07 22:30:00', '2026-07-07 14:00:00', 10,
   'N-20260707-01', 'E01:SAMPLE:TJ2:NOISE:20260707', 'VALID', 'demo', 1, 'VERIFIED', 'EFFECTIVE', '2026-07-08 11:00:00'),
  (923017, 'SAMPLE-TJ2-NOISE-20260709', 922017, 917002, 914002, 'NOISE',
   '2026-07-09 14:10:00', '2026-07-09 22:30:00', '2026-07-09 14:00:00', 10,
   'N-20260709-01', 'E01:SAMPLE:TJ2:NOISE:20260709', 'VALID', 'demo', 1, 'VERIFIED', 'EFFECTIVE', '2026-07-10 11:00:00'),
  (923018, 'SAMPLE-TJ2-NOISE-20260710', 922018, 917002, 914002, 'NOISE',
   '2026-07-10 14:10:00', '2026-07-10 22:30:00', '2026-07-10 14:00:00', 10,
   'N-20260710-01', 'E01:SAMPLE:TJ2:NOISE:20260710', 'VALID', 'demo', 1, 'VERIFIED', 'EFFECTIVE', '2026-07-11 11:00:00'),
  (923019, 'SAMPLE-TJ2-NOISE-20260711', 922019, 917002, 914002, 'NOISE',
   '2026-07-11 14:10:00', '2026-07-11 22:30:00', '2026-07-11 14:00:00', 10,
   'N-20260711-01', 'E01:SAMPLE:TJ2:NOISE:20260711', 'VALID', 'demo', 1, 'VERIFIED', 'EFFECTIVE', '2026-07-12 11:00:00')
ON DUPLICATE KEY UPDATE sample_status=VALUES(sample_status), effective_status=VALUES(effective_status);

INSERT INTO e01_factor_result
  (id, result_code, sample_id, factor_id, standard_version_id, test_stage, judgement, result_validity,
   detected_value_raw, limit_value_raw, standard_name_snapshot, reported_factor_name, reported_unit,
   judgement_source, effective_status, data_nature, is_demo)
VALUES
  (924028, 'RESULT-TJ2-NOISE-DAY-20260706', 923015, 919004, 920002, 'INITIAL', 'COMPLIANT', 'VALID', '65.0', '70', '建筑施工场界环境噪声排放标准 GB 12523-2011', '昼间等效声级', 'dB(A)', 'IMPORTED', 'EFFECTIVE', 'demo', 1),
  (924029, 'RESULT-TJ2-NOISE-NIGHT-20260706', 923015, 919005, 920002, 'INITIAL', 'COMPLIANT', 'VALID', '52.0', '55', '建筑施工场界环境噪声排放标准 GB 12523-2011', '夜间等效声级', 'dB(A)', 'IMPORTED', 'EFFECTIVE', 'demo', 1),
  (924030, 'RESULT-TJ2-NOISE-DAY-20260707', 923016, 919004, 920002, 'INITIAL', 'COMPLIANT', 'VALID', '66.0', '70', '建筑施工场界环境噪声排放标准 GB 12523-2011', '昼间等效声级', 'dB(A)', 'IMPORTED', 'EFFECTIVE', 'demo', 1),
  (924031, 'RESULT-TJ2-NOISE-NIGHT-20260707', 923016, 919005, 920002, 'INITIAL', 'COMPLIANT', 'VALID', '54.0', '55', '建筑施工场界环境噪声排放标准 GB 12523-2011', '夜间等效声级', 'dB(A)', 'IMPORTED', 'EFFECTIVE', 'demo', 1),
  (924032, 'RESULT-TJ2-NOISE-DAY-20260709', 923017, 919004, 920002, 'INITIAL', 'COMPLIANT', 'VALID', '68.0', '70', '建筑施工场界环境噪声排放标准 GB 12523-2011', '昼间等效声级', 'dB(A)', 'IMPORTED', 'EFFECTIVE', 'demo', 1),
  (924033, 'RESULT-TJ2-NOISE-NIGHT-20260709', 923017, 919005, 920002, 'INITIAL', 'COMPLIANT', 'VALID', '57.2', '55', '建筑施工场界环境噪声排放标准 GB 12523-2011', '夜间等效声级', 'dB(A)', 'IMPORTED', 'EFFECTIVE', 'demo', 1),
  (924034, 'RESULT-TJ2-NOISE-DAY-20260710', 923018, 919004, 920002, 'INITIAL', 'COMPLIANT', 'VALID', '69.0', '70', '建筑施工场界环境噪声排放标准 GB 12523-2011', '昼间等效声级', 'dB(A)', 'IMPORTED', 'EFFECTIVE', 'demo', 1),
  (924035, 'RESULT-TJ2-NOISE-NIGHT-20260710', 923018, 919005, 920002, 'INITIAL', 'COMPLIANT', 'VALID', '56.1', '55', '建筑施工场界环境噪声排放标准 GB 12523-2011', '夜间等效声级', 'dB(A)', 'IMPORTED', 'EFFECTIVE', 'demo', 1),
  (924036, 'RESULT-TJ2-NOISE-DAY-20260711', 923019, 919004, 920002, 'INITIAL', 'COMPLIANT', 'VALID', '64.0', '70', '建筑施工场界环境噪声排放标准 GB 12523-2011', '昼间等效声级', 'dB(A)', 'IMPORTED', 'EFFECTIVE', 'demo', 1),
  (924037, 'RESULT-TJ2-NOISE-NIGHT-20260711', 923019, 919005, 920002, 'INITIAL', 'COMPLIANT', 'VALID', '53.8', '55', '建筑施工场界环境噪声排放标准 GB 12523-2011', '夜间等效声级', 'dB(A)', 'IMPORTED', 'EFFECTIVE', 'demo', 1)
ON DUPLICATE KEY UPDATE judgement=VALUES(judgement), detected_value_raw=VALUES(detected_value_raw), effective_status=VALUES(effective_status);
