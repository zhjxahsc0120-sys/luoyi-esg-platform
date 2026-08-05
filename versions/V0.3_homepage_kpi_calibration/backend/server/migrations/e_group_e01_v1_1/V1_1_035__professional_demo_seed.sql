-- E01 专业化测试数据。所有业务编码固定，重复执行只更新本迁移拥有的记录。

INSERT INTO project_section
  (id, project_id, section_code, section_name, chainage_start, chainage_end, start_km, end_km, section_type, active_status, data_nature, is_demo)
VALUES
  (910001, 'LUOYI-ESG', 'TJ-1', '土建施工 TJ-1 合同段', 'K50+000', 'K68+400', 50.000, 68.400, 'CIVIL', 'ACTIVE', 'demo', 1),
  (910002, 'LUOYI-ESG', 'TJ-2', '土建施工 TJ-2 合同段', 'K68+400', 'K86+700', 68.400, 86.700, 'CIVIL', 'ACTIVE', 'demo', 1),
  (910003, 'LUOYI-ESG', 'TJ-3', '土建施工 TJ-3 合同段', 'K86+700', 'K104+500', 86.700, 104.500, 'CIVIL', 'ACTIVE', 'demo', 1)
ON DUPLICATE KEY UPDATE section_name=VALUES(section_name), chainage_start=VALUES(chainage_start), chainage_end=VALUES(chainage_end), start_km=VALUES(start_km), end_km=VALUES(end_km), active_status=VALUES(active_status);

INSERT INTO project_phase_period
  (id, project_id, phase_code, phase_name, phase_type, start_at, end_at, phase_status, data_nature, is_demo)
VALUES
  (911001, 'LUOYI-ESG', 'PH-2026-FOUNDATION', '基础及下部结构施工阶段', 'SUBSTRUCTURE', '2026-05-08 00:00:00', '2026-05-31 23:59:59', 'COMPLETED', 'demo', 1),
  (911002, 'LUOYI-ESG', 'PH-2026-EARTHWORK', '路基土石方及结构施工阶段', 'EARTHWORK', '2026-06-01 00:00:00', '2026-08-31 23:59:59', 'ACTIVE', 'demo', 1),
  (911003, 'LUOYI-ESG', 'PH-2026-PAVEMENT', '路面及附属工程施工阶段', 'PAVEMENT', '2026-09-01 00:00:00', '2026-12-31 23:59:59', 'PLANNED', 'demo', 1)
ON DUPLICATE KEY UPDATE phase_name=VALUES(phase_name), start_at=VALUES(start_at), end_at=VALUES(end_at), phase_status=VALUES(phase_status);

INSERT INTO project_engineering_object
  (id, project_id, section_id, object_code, object_name, object_type, chainage_start, chainage_end, longitude, latitude, active_status, data_nature, is_demo)
VALUES
  (912001, 'LUOYI-ESG', 910001, 'OBJ-TJ1-RIVER-01', 'TJ-1 洛河跨河施工区域', 'CROSS_RIVER_CONSTRUCTION', 'K56+600', 'K57+100', 109.77573460, 24.47807047, 'ACTIVE', 'demo', 1),
  (912002, 'LUOYI-ESG', 910002, 'OBJ-TJ2-HAUL-01', 'TJ-2 施工便道及土石方运输区域', 'HAUL_ROAD', 'K74+200', 'K78+600', 109.68172938, 24.43146235, 'ACTIVE', 'demo', 1),
  (912003, 'LUOYI-ESG', 910003, 'OBJ-TJ3-MIX-01', 'TJ-3 拌和站及周边区域', 'MIXING_PLANT', 'K96+100', 'K96+500', 109.54333615, 24.44165793, 'ACTIVE', 'demo', 1),
  (912004, 'LUOYI-ESG', 910001, 'OBJ-TJ1-CAMP-01', 'TJ-1 临时施工营地排水区域', 'CONSTRUCTION_CAMP', 'K63+100', 'K63+500', 109.78864000, 24.48636000, 'ACTIVE', 'demo', 1)
ON DUPLICATE KEY UPDATE section_id=VALUES(section_id), object_name=VALUES(object_name), object_type=VALUES(object_type), chainage_start=VALUES(chainage_start), chainage_end=VALUES(chainage_end), longitude=VALUES(longitude), latitude=VALUES(latitude), active_status=VALUES(active_status);

INSERT INTO engineering_object_phase
  (id, object_id, phase_id, process_code, process_name, process_start_at, process_end_at, process_status, data_nature, is_demo)
VALUES
  (913001, 912001, 911002, 'PROC-RIVER-COFFERDAM', '跨河围堰及基础施工', '2026-06-05 00:00:00', '2026-08-20 23:59:59', 'ACTIVE', 'demo', 1),
  (913002, 912002, 911002, 'PROC-EARTHWORK-HAUL', '路基填筑及土石方运输', '2026-06-10 00:00:00', '2026-08-31 23:59:59', 'ACTIVE', 'demo', 1),
  (913003, 912003, 911002, 'PROC-MIXING-PRODUCTION', '水稳混合料生产及运输', '2026-06-01 00:00:00', '2026-08-31 23:59:59', 'ACTIVE', 'demo', 1),
  (913004, 912004, 911003, 'PROC-CAMP-DEMOB', '施工营地退场及场地恢复', '2026-09-15 00:00:00', '2026-11-30 23:59:59', 'PLANNED', 'demo', 1)
ON DUPLICATE KEY UPDATE process_name=VALUES(process_name), process_start_at=VALUES(process_start_at), process_end_at=VALUES(process_end_at), process_status=VALUES(process_status);

INSERT INTO e01_monitor_point
  (id, point_code, point_name, source_point_name, chainage, segment_code, segment_name, engineering_object_type, engineering_object_id, engineering_object_name, longitude, latitude, coordinate_system, coordinate_source_type, coordinate_verification_status, coordinate_accuracy, effective_from, active_status, data_nature, is_demo, verification_status, effective_status, effective_at)
VALUES
  (914001, 'E01-TJ1-WATER-01', '洛河跨河施工区下游监测断面', '下游500m水质断面', 'K56+900', 'TJ-1', '土建施工 TJ-1 合同段', 'CROSS_RIVER_CONSTRUCTION', 'OBJ-TJ1-RIVER-01', 'TJ-1 洛河跨河施工区域', 109.77573460, 24.47807047, 'WGS84', 'GIS_ALIGNMENT', 'VERIFIED', 3.000, '2026-05-12 00:00:00', 'ACTIVE', 'demo', 1, 'VERIFIED', 'EFFECTIVE', '2026-05-12 00:00:00'),
  (914002, 'E01-TJ2-NOISE-01', 'TJ-2施工便道居民区侧噪声点', '运输便道敏感点N1', 'K75+600', 'TJ-2', '土建施工 TJ-2 合同段', 'HAUL_ROAD', 'OBJ-TJ2-HAUL-01', 'TJ-2 施工便道及土石方运输区域', 109.68172938, 24.43146235, 'WGS84', 'GIS_ALIGNMENT', 'VERIFIED', 5.000, '2026-06-10 00:00:00', 'ACTIVE', 'demo', 1, 'VERIFIED', 'EFFECTIVE', '2026-06-10 00:00:00'),
  (914003, 'E01-TJ3-AIR-01', 'TJ-3拌和站下风向扬尘点', '拌和站下风向A1', 'K96+300', 'TJ-3', '土建施工 TJ-3 合同段', 'MIXING_PLANT', 'OBJ-TJ3-MIX-01', 'TJ-3 拌和站及周边区域', 109.54333615, 24.44165793, 'WGS84', 'GIS_ALIGNMENT', 'VERIFIED', 5.000, '2026-05-20 00:00:00', 'ACTIVE', 'demo', 1, 'VERIFIED', 'EFFECTIVE', '2026-05-20 00:00:00'),
  (914004, 'E01-TJ2-NOISE-02', 'TJ-2土石方运输备用噪声点', '运输便道敏感点N2', 'K82+100', 'TJ-2', '土建施工 TJ-2 合同段', 'HAUL_ROAD', 'OBJ-TJ2-HAUL-01', 'TJ-2 施工便道及土石方运输区域', 109.69790000, 24.43578000, 'WGS84', 'GIS_ALIGNMENT', 'VERIFIED', 5.000, '2026-07-20 00:00:00', 'ACTIVE', 'demo', 1, 'VERIFIED', 'EFFECTIVE', '2026-07-20 00:00:00')
ON DUPLICATE KEY UPDATE point_name=VALUES(point_name), chainage=VALUES(chainage), segment_code=VALUES(segment_code), segment_name=VALUES(segment_name), engineering_object_type=VALUES(engineering_object_type), engineering_object_id=VALUES(engineering_object_id), engineering_object_name=VALUES(engineering_object_name), longitude=VALUES(longitude), latitude=VALUES(latitude), active_status=VALUES(active_status), effective_status=VALUES(effective_status);

INSERT INTO monitor_point_object_relation
  (id, relation_code, point_id, section_id, object_id, phase_id, object_phase_id, relation_role, valid_from, data_nature, is_demo)
VALUES
  (915001, 'REL-E01-TJ1-WATER-01', 914001, 910001, 912001, 911002, 913001, 'PRIMARY', '2026-06-05 00:00:00', 'demo', 1),
  (915002, 'REL-E01-TJ2-NOISE-01', 914002, 910002, 912002, 911002, 913002, 'PRIMARY', '2026-06-10 00:00:00', 'demo', 1),
  (915003, 'REL-E01-TJ3-AIR-01', 914003, 910003, 912003, 911002, 913003, 'PRIMARY', '2026-05-20 00:00:00', 'demo', 1),
  (915004, 'REL-E01-TJ2-NOISE-02', 914004, 910002, 912002, 911002, 913002, 'BACKGROUND', '2026-07-20 00:00:00', 'demo', 1)
ON DUPLICATE KEY UPDATE section_id=VALUES(section_id), object_id=VALUES(object_id), phase_id=VALUES(phase_id), object_phase_id=VALUES(object_phase_id), relation_role=VALUES(relation_role), valid_from=VALUES(valid_from);

INSERT INTO e01_monitor_plan
  (id, plan_code, plan_year, quarter_code, frequency_code, testing_provider_name, owner_department_name, version_no, plan_status, data_nature, is_demo, verification_status, effective_status, effective_at)
VALUES
  (916001, 'E01-PLAN-TJ1-WATER-2026Q2', 2026, '2026-Q2', 'WEEKLY', '河南交通环境监测技术中心', '安全环保部', 'V1.0', 'EFFECTIVE', 'demo', 1, 'VERIFIED', 'EFFECTIVE', '2026-05-12 00:00:00'),
  (916002, 'E01-PLAN-TJ2-NOISE-2026Q3', 2026, '2026-Q3', 'DAILY', '河南交通环境监测技术中心', '安全环保部', 'V1.0', 'EFFECTIVE', 'demo', 1, 'VERIFIED', 'EFFECTIVE', '2026-06-05 00:00:00'),
  (916003, 'E01-PLAN-TJ3-AIR-2026Q3', 2026, '2026-Q3', 'CONTINUOUS', '罗宜高速环境在线监测中心', '安全环保部', 'V1.0', 'EFFECTIVE', 'demo', 1, 'VERIFIED', 'EFFECTIVE', '2026-05-15 00:00:00')
ON DUPLICATE KEY UPDATE frequency_code=VALUES(frequency_code), testing_provider_name=VALUES(testing_provider_name), owner_department_name=VALUES(owner_department_name), plan_status=VALUES(plan_status), effective_status=VALUES(effective_status);

INSERT INTO e01_monitor_plan_item
  (id, plan_id, point_id, monitor_category, planned_sample_at, planned_factor_scope, execution_status, data_nature, is_demo, effective_status, effective_at)
VALUES
  (917001, 916001, 914001, 'WATER', '2026-06-18 09:00:00', '["PH","SS","CODCR"]', 'COMPLETED', 'demo', 1, 'EFFECTIVE', '2026-05-12 00:00:00'),
  (917002, 916002, 914002, 'NOISE', '2026-07-08 14:00:00', '["LAEQ_DAY","LAEQ_NIGHT"]', 'COMPLETED', 'demo', 1, 'EFFECTIVE', '2026-06-05 00:00:00'),
  (917003, 916003, 914003, 'AIR', '2026-07-12 00:00:00', '["PM10_DAY"]', 'COMPLETED', 'demo', 1, 'EFFECTIVE', '2026-05-15 00:00:00'),
  (917004, 916002, 914004, 'NOISE', '2026-07-25 14:00:00', '["LAEQ_DAY","LAEQ_NIGHT"]', 'PENDING', 'demo', 1, 'EFFECTIVE', '2026-07-20 00:00:00')
ON DUPLICATE KEY UPDATE planned_sample_at=VALUES(planned_sample_at), planned_factor_scope=VALUES(planned_factor_scope), execution_status=VALUES(execution_status), effective_status=VALUES(effective_status);

INSERT INTO monitor_frequency_rule
  (id, rule_code, plan_item_id, frequency_code, interval_value, interval_unit, schedule_expression, aggregation_granularity, trigger_event, effective_from, active_status, data_nature, is_demo)
VALUES
  (918001, 'FREQ-TJ1-WATER-WEEKLY', 917001, 'WEEKLY', 1, 'WEEK', '每周三09:00采样', 'SAMPLE_BATCH', NULL, '2026-05-12 00:00:00', 'ACTIVE', 'demo', 1),
  (918002, 'FREQ-TJ2-NOISE-DAILY', 917002, 'DAILY', 1, 'DAY', '施工期间每日昼间、夜间各1次', 'TIME_PERIOD', NULL, '2026-06-10 00:00:00', 'ACTIVE', 'demo', 1),
  (918003, 'FREQ-TJ3-AIR-CONTINUOUS', 917003, 'CONTINUOUS', NULL, NULL, '在线设备5分钟采集', 'HOUR', NULL, '2026-05-20 00:00:00', 'ACTIVE', 'demo', 1),
  (918004, 'FREQ-TJ3-AIR-RETEST', 917003, 'EVENT_TRIGGERED', NULL, NULL, '超标事件触发复测', 'SAMPLE_BATCH', 'PM10日均值超限', '2026-05-20 00:00:00', 'ACTIVE', 'demo', 1),
  (918005, 'FREQ-TJ2-NOISE-PENDING', 917004, 'DAILY', 1, 'DAY', '启用后按施工日监测', 'TIME_PERIOD', NULL, '2026-07-20 00:00:00', 'ACTIVE', 'demo', 1)
ON DUPLICATE KEY UPDATE frequency_code=VALUES(frequency_code), interval_value=VALUES(interval_value), interval_unit=VALUES(interval_unit), schedule_expression=VALUES(schedule_expression), aggregation_granularity=VALUES(aggregation_granularity), trigger_event=VALUES(trigger_event), active_status=VALUES(active_status);

INSERT INTO e01_factor_definition
  (id, factor_code, factor_name, monitor_category, default_unit, effective_from, data_nature, is_demo, verification_status, effective_status, effective_at)
VALUES
  (919001, 'PH', 'pH值', 'WATER', '无量纲', '2026-01-01 00:00:00', 'demo', 1, 'VERIFIED', 'EFFECTIVE', '2026-01-01 00:00:00'),
  (919002, 'SS', '悬浮物', 'WATER', 'mg/L', '2026-01-01 00:00:00', 'demo', 1, 'VERIFIED', 'EFFECTIVE', '2026-01-01 00:00:00'),
  (919003, 'CODCR', '化学需氧量', 'WATER', 'mg/L', '2026-01-01 00:00:00', 'demo', 1, 'VERIFIED', 'EFFECTIVE', '2026-01-01 00:00:00'),
  (919004, 'LAEQ_DAY', '昼间等效声级', 'NOISE', 'dB(A)', '2026-01-01 00:00:00', 'demo', 1, 'VERIFIED', 'EFFECTIVE', '2026-01-01 00:00:00'),
  (919005, 'LAEQ_NIGHT', '夜间等效声级', 'NOISE', 'dB(A)', '2026-01-01 00:00:00', 'demo', 1, 'VERIFIED', 'EFFECTIVE', '2026-01-01 00:00:00'),
  (919006, 'PM10_DAY', 'PM10日均浓度', 'AIR', 'μg/m³', '2026-01-01 00:00:00', 'demo', 1, 'VERIFIED', 'EFFECTIVE', '2026-01-01 00:00:00')
ON DUPLICATE KEY UPDATE factor_name=VALUES(factor_name), monitor_category=VALUES(monitor_category), default_unit=VALUES(default_unit), effective_status=VALUES(effective_status);

INSERT INTO e01_standard_version
  (id, standard_code, standard_name, version_no, issuing_authority, applicable_from, data_nature, is_demo, verification_status, effective_status, effective_at)
VALUES
  (920001, 'GB3838', '地表水环境质量标准', 'GB 3838-2002', '生态环境部', '2002-06-01 00:00:00', 'demo', 1, 'VERIFIED', 'EFFECTIVE', '2026-01-01 00:00:00'),
  (920002, 'GB12523', '建筑施工场界环境噪声排放标准', 'GB 12523-2011', '生态环境部', '2012-07-01 00:00:00', 'demo', 1, 'VERIFIED', 'EFFECTIVE', '2026-01-01 00:00:00'),
  (920003, 'GB3095', '环境空气质量标准', 'GB 3095-2012', '生态环境部', '2016-01-01 00:00:00', 'demo', 1, 'VERIFIED', 'EFFECTIVE', '2026-01-01 00:00:00')
ON DUPLICATE KEY UPDATE standard_name=VALUES(standard_name), issuing_authority=VALUES(issuing_authority), applicable_from=VALUES(applicable_from), effective_status=VALUES(effective_status);

INSERT INTO e01_standard_limit
  (id, standard_version_id, factor_id, applicable_scene, limit_operator, limit_value_raw, limit_value_num, unit, period_description, data_nature, is_demo, verification_status, effective_status, effective_at)
VALUES
  (921001, 920001, 919001, '跨河施工下游控制断面', '>=', '6', 6.0000000000, '无量纲', '单次采样', 'demo', 1, 'VERIFIED', 'EFFECTIVE', '2026-01-01 00:00:00'),
  (921002, 920001, 919002, '施工影响控制值', '<=', '30', 30.0000000000, 'mg/L', '单次采样', 'demo', 1, 'VERIFIED', 'EFFECTIVE', '2026-01-01 00:00:00'),
  (921003, 920001, 919003, '地表水Ⅲ类控制值', '<=', '20', 20.0000000000, 'mg/L', '单次采样', 'demo', 1, 'VERIFIED', 'EFFECTIVE', '2026-01-01 00:00:00'),
  (921004, 920002, 919004, '施工场界昼间', '<=', '70', 70.0000000000, 'dB(A)', '昼间施工时段', 'demo', 1, 'VERIFIED', 'EFFECTIVE', '2026-01-01 00:00:00'),
  (921005, 920002, 919005, '施工场界夜间', '<=', '55', 55.0000000000, 'dB(A)', '夜间施工时段', 'demo', 1, 'VERIFIED', 'EFFECTIVE', '2026-01-01 00:00:00'),
  (921006, 920003, 919006, '二级标准', '<=', '150', 150.0000000000, 'μg/m³', '24小时平均', 'demo', 1, 'VERIFIED', 'EFFECTIVE', '2026-01-01 00:00:00')
ON DUPLICATE KEY UPDATE applicable_scene=VALUES(applicable_scene), limit_operator=VALUES(limit_operator), limit_value_raw=VALUES(limit_value_raw), limit_value_num=VALUES(limit_value_num), unit=VALUES(unit), period_description=VALUES(period_description), effective_status=VALUES(effective_status);

INSERT INTO e01_monitor_batch
  (id, batch_code, plan_id, quarter_code, report_no, testing_provider_name, sample_start_at, sample_end_at, report_issued_at, received_at, batch_status, idempotency_key, data_nature, is_demo, effective_status, effective_at)
VALUES
  (922001, 'BATCH-TJ1-WATER-20260618', 916001, '2026-Q2', 'LYHJ-WATER-2026-0618', '河南交通环境监测技术中心', '2026-06-18 09:00:00', '2026-06-18 10:00:00', '2026-06-21 10:00:00', '2026-06-21 14:00:00', 'EFFECTIVE', 'E01:TJ1:WATER:20260618', 'demo', 1, 'EFFECTIVE', '2026-06-21 14:00:00'),
  (922002, 'BATCH-TJ2-NOISE-20260708', 916002, '2026-Q3', 'LYHJ-NOISE-2026-0708', '河南交通环境监测技术中心', '2026-07-08 14:00:00', '2026-07-08 23:30:00', '2026-07-10 10:00:00', '2026-07-10 14:00:00', 'EFFECTIVE', 'E01:TJ2:NOISE:20260708', 'demo', 1, 'EFFECTIVE', '2026-07-10 14:00:00'),
  (922003, 'BATCH-TJ3-AIR-20260712', 916003, '2026-Q3', 'LYHJ-AIR-ONLINE-2026-0712', '罗宜高速环境在线监测中心', '2026-07-12 00:00:00', '2026-07-12 23:59:59', '2026-07-13 08:00:00', '2026-07-13 08:05:00', 'EFFECTIVE', 'E01:TJ3:AIR:20260712', 'demo', 1, 'EFFECTIVE', '2026-07-13 08:05:00'),
  (922004, 'BATCH-TJ3-AIR-RETEST-20260715', 916003, '2026-Q3', 'LYHJ-AIR-RETEST-2026-0715', '河南交通环境监测技术中心', '2026-07-15 08:00:00', '2026-07-15 23:59:59', '2026-07-16 10:00:00', '2026-07-16 14:00:00', 'EFFECTIVE', 'E01:TJ3:AIR:RETEST:20260715', 'demo', 1, 'EFFECTIVE', '2026-07-16 14:00:00')
ON DUPLICATE KEY UPDATE report_no=VALUES(report_no), testing_provider_name=VALUES(testing_provider_name), sample_start_at=VALUES(sample_start_at), sample_end_at=VALUES(sample_end_at), report_issued_at=VALUES(report_issued_at), received_at=VALUES(received_at), batch_status=VALUES(batch_status), effective_status=VALUES(effective_status);

INSERT INTO e01_monitor_sample
  (id, sample_code, batch_id, plan_item_id, point_id, monitor_category, sampled_at, sample_end_at, planned_sample_at_snapshot, planned_actual_variance_minutes, sample_no, idempotency_key, sample_status, data_nature, is_demo, verification_status, effective_status, effective_at)
VALUES
  (923001, 'SAMPLE-TJ1-WATER-20260618', 922001, 917001, 914001, 'WATER', '2026-06-18 09:12:00', '2026-06-18 09:35:00', '2026-06-18 09:00:00', 12, 'W-20260618-01', 'E01:SAMPLE:TJ1:WATER:20260618', 'VALID', 'demo', 1, 'VERIFIED', 'EFFECTIVE', '2026-06-21 14:00:00'),
  (923002, 'SAMPLE-TJ2-NOISE-20260708', 922002, 917002, 914002, 'NOISE', '2026-07-08 14:10:00', '2026-07-08 22:30:00', '2026-07-08 14:00:00', 10, 'N-20260708-01', 'E01:SAMPLE:TJ2:NOISE:20260708', 'VALID', 'demo', 1, 'VERIFIED', 'EFFECTIVE', '2026-07-10 14:00:00'),
  (923003, 'SAMPLE-TJ3-AIR-20260712', 922003, 917003, 914003, 'AIR', '2026-07-12 00:00:00', '2026-07-12 23:59:59', '2026-07-12 00:00:00', 0, 'A-20260712-DAY', 'E01:SAMPLE:TJ3:AIR:20260712', 'VALID', 'demo', 1, 'VERIFIED', 'EFFECTIVE', '2026-07-13 08:05:00'),
  (923004, 'SAMPLE-TJ3-AIR-RETEST-20260715', 922004, 917003, 914003, 'AIR', '2026-07-15 00:00:00', '2026-07-15 23:59:59', NULL, NULL, 'A-20260715-RETEST', 'E01:SAMPLE:TJ3:AIR:RETEST:20260715', 'VALID', 'demo', 1, 'VERIFIED', 'EFFECTIVE', '2026-07-16 14:00:00')
ON DUPLICATE KEY UPDATE batch_id=VALUES(batch_id), plan_item_id=VALUES(plan_item_id), point_id=VALUES(point_id), sampled_at=VALUES(sampled_at), sample_end_at=VALUES(sample_end_at), sample_status=VALUES(sample_status), verification_status=VALUES(verification_status), effective_status=VALUES(effective_status);

INSERT INTO e01_factor_result
  (id, result_code, sample_id, factor_id, standard_version_id, test_stage, judgement, result_validity, detected_value_raw, limit_value_raw, standard_name_snapshot, reported_factor_name, reported_unit, judgement_source, effective_status, data_nature, is_demo)
VALUES
  (924001, 'RESULT-TJ1-WATER-PH-20260618', 923001, 919001, 920001, 'INITIAL', 'COMPLIANT', 'VALID', '7.3', '6—9', '地表水环境质量标准 GB 3838-2002', 'pH值', '无量纲', 'IMPORTED', 'EFFECTIVE', 'demo', 1),
  (924002, 'RESULT-TJ1-WATER-SS-20260618', 923001, 919002, 920001, 'INITIAL', 'COMPLIANT', 'VALID', '18', '30', '施工期水环境控制要求', '悬浮物', 'mg/L', 'IMPORTED', 'EFFECTIVE', 'demo', 1),
  (924003, 'RESULT-TJ1-WATER-COD-20260618', 923001, 919003, 920001, 'INITIAL', 'COMPLIANT', 'VALID', '13', '20', '地表水环境质量标准 GB 3838-2002', '化学需氧量', 'mg/L', 'IMPORTED', 'EFFECTIVE', 'demo', 1),
  (924004, 'RESULT-TJ2-NOISE-DAY-20260708', 923002, 919004, 920002, 'INITIAL', 'COMPLIANT', 'VALID', '67.4', '70', '建筑施工场界环境噪声排放标准 GB 12523-2011', '昼间等效声级', 'dB(A)', 'IMPORTED', 'EFFECTIVE', 'demo', 1),
  (924005, 'RESULT-TJ2-NOISE-NIGHT-20260708', 923002, 919005, 920002, 'INITIAL', 'EXCEEDED', 'VALID', '58.6', '55', '建筑施工场界环境噪声排放标准 GB 12523-2011', '夜间等效声级', 'dB(A)', 'IMPORTED', 'EFFECTIVE', 'demo', 1),
  (924006, 'RESULT-TJ3-AIR-PM10-20260712', 923003, 919006, 920003, 'INITIAL', 'EXCEEDED', 'VALID', '186', '150', '环境空气质量标准 GB 3095-2012', 'PM10日均浓度', 'μg/m³', 'AUTO_LIMIT', 'EFFECTIVE', 'demo', 1),
  (924007, 'RESULT-TJ3-AIR-PM10-RETEST-20260715', 923004, 919006, 920003, 'RETEST', 'COMPLIANT', 'VALID', '112', '150', '环境空气质量标准 GB 3095-2012', 'PM10日均浓度', 'μg/m³', 'IMPORTED', 'EFFECTIVE', 'demo', 1)
ON DUPLICATE KEY UPDATE sample_id=VALUES(sample_id), factor_id=VALUES(factor_id), standard_version_id=VALUES(standard_version_id), test_stage=VALUES(test_stage), judgement=VALUES(judgement), result_validity=VALUES(result_validity), detected_value_raw=VALUES(detected_value_raw), limit_value_raw=VALUES(limit_value_raw), judgement_source=VALUES(judgement_source), effective_status=VALUES(effective_status);

INSERT INTO e_closure_case
  (id, case_code, case_domain, source_table, source_record_id, source_business_key, title, location_text, current_status, priority, severity, deadline, opened_at, closed_at, closure_reason, data_nature, is_demo, verification_status, effective_status, effective_at, row_version)
VALUES
  (925001, 'CASE-E01-NOISE-20260708', 'E01_EXCEED', 'e01_factor_result', 924005, 'RESULT-TJ2-NOISE-NIGHT-20260708', 'TJ-2施工便道夜间噪声超标整改', 'TJ-2｜K75+600｜施工便道居民区侧', 'RECTIFYING', 'HIGH', 'GENERAL', '2026-07-25 18:00:00', '2026-07-10 09:00:00', NULL, NULL, 'demo', 1, 'VERIFIED', 'EFFECTIVE', '2026-07-10 09:00:00', 2),
  (925002, 'CASE-E01-AIR-20260712', 'E01_EXCEED', 'e01_factor_result', 924006, 'RESULT-TJ3-AIR-PM10-20260712', 'TJ-3拌和站PM10超标闭环', 'TJ-3｜K96+300｜拌和站下风向', 'CLOSED', 'HIGH', 'GENERAL', '2026-07-20 18:00:00', '2026-07-13 09:00:00', '2026-07-17 16:00:00', '抑尘设施整改完成，复测PM10日均浓度达标，审核后关闭', 'demo', 1, 'VERIFIED', 'EFFECTIVE', '2026-07-13 09:00:00', 5)
ON DUPLICATE KEY UPDATE title=VALUES(title), location_text=VALUES(location_text), current_status=VALUES(current_status), deadline=VALUES(deadline), closed_at=VALUES(closed_at), closure_reason=VALUES(closure_reason), row_version=VALUES(row_version), effective_status=VALUES(effective_status);

INSERT INTO e_case_status_history
  (id, case_id, sequence_no, from_status, to_status, action_code, transition_result, action_at, operator_name, operator_org_name, comment, client_request_id, data_nature, is_demo)
VALUES
  (926001, 925001, 1, NULL, 'DISCOVERED', 'CREATE_CASE', 'SUCCESS', '2026-07-10 09:00:00', '环境监测专员', '安全环保部', '夜间等效声级超限，创建整改事项', 'SEED-CASE-NOISE-01', 'demo', 1),
  (926002, 925001, 2, 'DISCOVERED', 'PENDING_RECTIFICATION', 'ISSUE_RECTIFICATION', 'SUCCESS', '2026-07-10 10:00:00', '环境管理负责人', '安全环保部', '要求优化运输时段并设置临时声屏障', 'SEED-CASE-NOISE-02', 'demo', 1),
  (926003, 925001, 3, 'PENDING_RECTIFICATION', 'RECTIFYING', 'START_RECTIFICATION', 'SUCCESS', '2026-07-11 08:30:00', 'TJ-2环保负责人', 'TJ-2项目经理部', '整改措施实施中', 'SEED-CASE-NOISE-03', 'demo', 1),
  (926011, 925002, 1, NULL, 'DISCOVERED', 'CREATE_CASE', 'SUCCESS', '2026-07-13 09:00:00', '在线监测管理员', '安全环保部', 'PM10日均浓度超限，创建整改事项', 'SEED-CASE-AIR-01', 'demo', 1),
  (926012, 925002, 2, 'DISCOVERED', 'PENDING_RECTIFICATION', 'ISSUE_RECTIFICATION', 'SUCCESS', '2026-07-13 10:00:00', '环境管理负责人', '安全环保部', '要求检修喷淋并封闭上料区域', 'SEED-CASE-AIR-02', 'demo', 1),
  (926013, 925002, 3, 'PENDING_RECTIFICATION', 'RECTIFYING', 'START_RECTIFICATION', 'SUCCESS', '2026-07-13 14:00:00', 'TJ-3环保负责人', 'TJ-3项目经理部', '整改开始', 'SEED-CASE-AIR-03', 'demo', 1),
  (926014, 925002, 4, 'RECTIFYING', 'PENDING_REVIEW', 'SUBMIT_RECTIFICATION', 'SUCCESS', '2026-07-14 18:00:00', 'TJ-3环保负责人', 'TJ-3项目经理部', '喷淋和封闭措施完成，申请复测', 'SEED-CASE-AIR-04', 'demo', 1),
  (926015, 925002, 5, 'PENDING_REVIEW', 'PENDING_CLOSURE', 'REVIEW_PASS', 'SUCCESS', '2026-07-16 16:00:00', '环境监测专员', '安全环保部', '复测结果达标，建议销项', 'SEED-CASE-AIR-05', 'demo', 1),
  (926016, 925002, 6, 'PENDING_CLOSURE', 'CLOSED', 'CLOSE_CASE', 'SUCCESS', '2026-07-17 16:00:00', '环境管理负责人', '安全环保部', '闭环材料齐全，确认关闭', 'SEED-CASE-AIR-06', 'demo', 1)
ON DUPLICATE KEY UPDATE from_status=VALUES(from_status), to_status=VALUES(to_status), action_code=VALUES(action_code), transition_result=VALUES(transition_result), action_at=VALUES(action_at), comment=VALUES(comment);

UPDATE e_closure_case SET current_status_history_id=926003 WHERE id=925001;
UPDATE e_closure_case SET current_status_history_id=926016 WHERE id=925002;

INSERT INTO e01_exceed_event
  (id, event_code, case_id, original_result_id, first_exceeded_at, event_category, current_retest_round, latest_retest_outcome, closure_confirmed_at, effective_status, effective_at, data_nature, is_demo)
VALUES
  (927001, 'EVENT-E01-NOISE-20260708', 925001, 924005, '2026-07-08 22:00:00', 'NOISE', 0, 'NOT_TESTED', NULL, 'EFFECTIVE', '2026-07-10 09:00:00', 'demo', 1),
  (927002, 'EVENT-E01-AIR-20260712', 925002, 924006, '2026-07-12 23:59:59', 'AIR', 1, 'COMPLIANT', '2026-07-17 16:00:00', 'EFFECTIVE', '2026-07-13 09:00:00', 'demo', 1)
ON DUPLICATE KEY UPDATE case_id=VALUES(case_id), original_result_id=VALUES(original_result_id), current_retest_round=VALUES(current_retest_round), latest_retest_outcome=VALUES(latest_retest_outcome), closure_confirmed_at=VALUES(closure_confirmed_at), effective_status=VALUES(effective_status);

INSERT INTO e_rectification_task
  (id, task_code, title, deadline, task_status, data_nature, is_demo, effective_status, effective_at)
VALUES
  (928001, 'TASK-E01-NOISE-20260708', '调整夜间运输时段并增设临时声屏障', '2026-07-25 18:00:00', 'IN_PROGRESS', 'demo', 1, 'EFFECTIVE', '2026-07-10 10:00:00'),
  (928002, 'TASK-E01-AIR-20260712', '检修喷淋系统并封闭拌和站上料区域', '2026-07-15 18:00:00', 'COMPLETED', 'demo', 1, 'EFFECTIVE', '2026-07-13 10:00:00')
ON DUPLICATE KEY UPDATE title=VALUES(title), deadline=VALUES(deadline), task_status=VALUES(task_status), effective_status=VALUES(effective_status);

INSERT INTO e_case_rectification_link
  (id, case_id, task_id, link_role, data_nature, is_demo, effective_status)
VALUES
  (929001, 925001, 928001, 'PRIMARY', 'demo', 1, 'EFFECTIVE'),
  (929002, 925002, 928002, 'PRIMARY', 'demo', 1, 'EFFECTIVE')
ON DUPLICATE KEY UPDATE link_role=VALUES(link_role), effective_status=VALUES(effective_status);

INSERT INTO e01_rectification_round
  (id, event_id, round_no, task_id, started_at, submitted_at, rectification_summary, review_status, data_nature, is_demo, effective_status, effective_at)
VALUES
  (930001, 927001, 1, 928001, '2026-07-11 08:30:00', NULL, '运输时段优化和临时声屏障正在实施', 'PENDING_REVIEW', 'demo', 1, 'EFFECTIVE', '2026-07-11 08:30:00'),
  (930002, 927002, 1, 928002, '2026-07-13 14:00:00', '2026-07-14 18:00:00', '完成喷淋系统检修，上料区域封闭并增加清扫频次', 'PASSED', 'demo', 1, 'EFFECTIVE', '2026-07-14 18:00:00')
ON DUPLICATE KEY UPDATE task_id=VALUES(task_id), started_at=VALUES(started_at), submitted_at=VALUES(submitted_at), rectification_summary=VALUES(rectification_summary), review_status=VALUES(review_status), effective_status=VALUES(effective_status);

INSERT INTO e01_retest_round
  (id, event_id, round_no, retest_batch_id, requested_at, planned_sample_at, actual_sample_at, outcome, review_status, reviewed_at, data_nature, is_demo, effective_status, effective_at)
VALUES
  (931001, 927002, 1, 922004, '2026-07-14 18:00:00', '2026-07-15 00:00:00', '2026-07-15 00:00:00', 'COMPLIANT', 'PASSED', '2026-07-16 16:00:00', 'demo', 1, 'EFFECTIVE', '2026-07-16 16:00:00')
ON DUPLICATE KEY UPDATE retest_batch_id=VALUES(retest_batch_id), requested_at=VALUES(requested_at), planned_sample_at=VALUES(planned_sample_at), actual_sample_at=VALUES(actual_sample_at), outcome=VALUES(outcome), review_status=VALUES(review_status), reviewed_at=VALUES(reviewed_at), effective_status=VALUES(effective_status);

INSERT INTO e01_retest_result_link
  (id, event_id, retest_round_id, factor_result_id, original_result_id, data_nature, is_demo, effective_status, effective_at)
VALUES
  (932001, 927002, 931001, 924007, 924006, 'demo', 1, 'EFFECTIVE', '2026-07-16 16:00:00')
ON DUPLICATE KEY UPDATE event_id=VALUES(event_id), retest_round_id=VALUES(retest_round_id), original_result_id=VALUES(original_result_id), effective_status=VALUES(effective_status);
