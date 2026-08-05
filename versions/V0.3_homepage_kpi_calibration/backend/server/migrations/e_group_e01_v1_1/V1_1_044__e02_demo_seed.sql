-- ============================================================================
-- V1_1_044__e02_demo_seed.sql
-- E02 演示数据双写种子（D01-D07）
-- 对齐 V1_1_020 表结构 + gis_feature_business_relation 现网列
-- 幂等：先按业务键清理，再插入
-- ============================================================================

SET FOREIGN_KEY_CHECKS = 0;

-- --------------------------------------------------------------------------
-- 1. 幂等清理
-- --------------------------------------------------------------------------
DELETE FROM gis_feature_business_relation
 WHERE relation_type = 'environment_problem'
   AND (source_id LIKE 'E02-D%' OR relation_code LIKE 'E02-D%');

DELETE FROM e_case_evidence
 WHERE case_id IN (SELECT id FROM e_closure_case WHERE case_domain = 'E02_ENV' AND is_demo = 1);

DELETE FROM e_case_party
 WHERE case_id IN (SELECT id FROM e_closure_case WHERE case_domain = 'E02_ENV' AND is_demo = 1);

DELETE FROM e_case_status_history
 WHERE case_id IN (SELECT id FROM e_closure_case WHERE case_domain = 'E02_ENV' AND is_demo = 1);

DELETE FROM e_closure_case
 WHERE case_domain = 'E02_ENV' AND is_demo = 1;

DELETE FROM env_issue_record
 WHERE is_demo = 1 AND (business_code LIKE 'E02-D%' OR id BETWEEN 421001 AND 421099);

DELETE FROM document_record
 WHERE id BETWEEN 422001 AND 422099;

SET FOREIGN_KEY_CHECKS = 1;

-- --------------------------------------------------------------------------
-- 2. 占位资料主档（证据 FK 必需 document_id 或 file_id）
-- --------------------------------------------------------------------------
INSERT INTO document_record
  (id, document_code, document_name, document_type, module_code, source_name, validity_status, document_status, confirm_status)
VALUES
  (422001, 'E02-DOC-D01-N', '整改通知单 E02-D01', 'FORMAL_NOTICE', 'E02', '正式检查通知', '有效', 'ACTIVE', 'CONFIRMED'),
  (422002, 'E02-DOC-D02-N', '整改通知单 E02-D02', 'FORMAL_NOTICE', 'E02', '正式检查通知', '有效', 'ACTIVE', 'CONFIRMED'),
  (422003, 'E02-DOC-D03-N', '整改通知单 E02-D03', 'FORMAL_NOTICE', 'E02', '正式检查通知', '有效', 'ACTIVE', 'CONFIRMED'),
  (422004, 'E02-DOC-D03-R', '边坡防护整改资料 E02-D03', 'RECTIFICATION_MATERIAL', 'E02', '整改回复及影像', '有效', 'ACTIVE', 'CONFIRMED'),
  (422005, 'E02-DOC-D04-N', '整改通知单 E02-D04', 'FORMAL_NOTICE', 'E02', '正式检查通知', '有效', 'ACTIVE', 'CONFIRMED'),
  (422006, 'E02-DOC-D04-R', '隔音屏障整改资料 E02-D04', 'RECTIFICATION_MATERIAL', 'E02', '整改回复', '有效', 'ACTIVE', 'CONFIRMED'),
  (422007, 'E02-DOC-D04-V', '复查意见 E02-D04', 'REVIEW_OPINION', 'E02', '复查通过', '有效', 'ACTIVE', 'CONFIRMED'),
  (422008, 'E02-DOC-D05-N', '整改通知单 E02-D05', 'FORMAL_NOTICE', 'E02', '正式检查通知', '有效', 'ACTIVE', 'CONFIRMED'),
  (422009, 'E02-DOC-D05-R', '植被恢复资料 E02-D05', 'RECTIFICATION_MATERIAL', 'E02', '整改回复', '有效', 'ACTIVE', 'CONFIRMED'),
  (422010, 'E02-DOC-D05-V', '验收意见 E02-D05', 'REVIEW_OPINION', 'E02', '复查通过', '有效', 'ACTIVE', 'CONFIRMED'),
  (422011, 'E02-DOC-D05-C', '销项确认记录 E02-D05', 'CLOSURE_CONFIRMATION', 'E02', '确认人：孙总工；时间：2026-07-01；意见：恢复面积达标；依据：验收报告E05-2026', '有效', 'ACTIVE', 'CONFIRMED'),
  (422012, 'E02-DOC-D07-N', '整改通知单 E02-D07', 'FORMAL_NOTICE', 'E02', '正式检查通知', '有效', 'ACTIVE', 'CONFIRMED'),
  (422013, 'E02-DOC-D07-R1', '第一轮整改报告 E02-D07', 'RECTIFICATION_MATERIAL', 'E02', '上轮整改材料', '有效', 'ACTIVE', 'CONFIRMED'),
  (422014, 'E02-DOC-D07-V', '复查退回意见 E02-D07', 'REVIEW_OPINION', 'E02', 'SS仍超标，退回重改', '有效', 'ACTIVE', 'CONFIRMED');

-- --------------------------------------------------------------------------
-- 3. 台账 env_issue_record（D01-D07）
-- 注意：D03 不得使用「水土保持」类型（E03 边界）
-- GIS 关联既有本体要素：弃渣 / 水源 / 生态 / 边坡敏感点（非整条标段）
-- --------------------------------------------------------------------------
INSERT INTO env_issue_record
    (id, issue_type, issue_name, issue_status, overdue, found_date, closed_date, deadline, responsible_org_name, location_text, created_at, is_demo, data_nature, business_code)
VALUES
    (421001, '扬尘管控', '标段一弃渣场扬尘控制不到位', '整改中', 0, '2026-07-02', NULL, '2026-07-20', '工程管理部', '弃渣点1（K12+300）', '2026-07-02 09:00:00', 1, 'demo', 'E02-D01'),
    (421002, '废水处理', '施工废水处理设施临时故障', '整改中', 1, '2026-07-05', NULL, '2026-07-10', '安全环保部', '水源保护区2邻近排水口', '2026-07-05 09:00:00', 1, 'demo', 'E02-D02'),
    (421003, '弃渣场管理', '临时堆土场边坡防护不足', '待复查', 0, '2026-06-28', NULL, '2026-07-20', '工程管理部', '弃渣点2临时堆土区', '2026-06-28 09:00:00', 1, 'demo', 'E02-D03'),
    (421004, '噪声扰民', '夜间施工噪声超标投诉', '待销项', 0, '2026-06-26', NULL, '2026-07-18', '安全环保部', '边坡监测点1邻近居民区', '2026-06-26 09:00:00', 1, 'demo', 'E02-D04'),
    (421005, '生态保护', '生态敏感区施工临时便道恢复', '已闭环', 0, '2026-06-15', '2026-07-01', '2026-06-30', '总工办', '生态保护区1缓冲带', '2026-06-15 09:00:00', 1, 'demo', 'E02-D05'),
    (421006, '扬尘管控', '拌合站粉尘无组织排放（已合并至D01）', '已合并', 0, '2026-07-01', '2026-07-03', '2026-07-15', '工程管理部', '弃渣点1邻近拌合站', '2026-07-01 09:00:00', 1, 'demo', 'E02-D06'),
    (421007, '废水处理', '沉淀池出水SS复检不合格（退回重改）', '整改中', 0, '2026-06-20', NULL, '2026-07-25', '安全环保部', '水源保护区2邻近沉淀池出口', '2026-06-20 09:00:00', 1, 'demo', 'E02-D07');

-- --------------------------------------------------------------------------
-- 4. 案卷 e_closure_case（一对一；responsible_org_id 置空避免未知 org FK）
-- --------------------------------------------------------------------------
INSERT INTO e_closure_case
    (id, case_code, case_domain, source_table, source_record_id, source_business_key, title, location_text, gis_feature_id, current_status, priority, severity, deadline, opened_at, closed_at, closure_reason, merged_into_case_id, data_nature, is_demo, verification_status, effective_status, effective_at, row_version)
VALUES
    (429001, 'E02-D01', 'E02_ENV', 'env_issue_record', 421001, 'E02-D01', '标段一弃渣场扬尘控制不到位', '弃渣点1（K12+300）', 'waste-1-1', 'RECTIFYING', 'MEDIUM', 'GENERAL', '2026-07-20 00:00:00.000000', '2026-07-02 09:00:00.000000', NULL, NULL, NULL, 'demo', 1, 'VERIFIED', 'EFFECTIVE', '2026-07-02 09:00:00.000000', 1),
    (429002, 'E02-D02', 'E02_ENV', 'env_issue_record', 421002, 'E02-D02', '施工废水处理设施临时故障', '水源保护区2邻近排水口', 'water-2-1', 'RECTIFYING', 'HIGH', 'GENERAL', '2026-07-10 00:00:00.000000', '2026-07-05 09:00:00.000000', NULL, NULL, NULL, 'demo', 1, 'VERIFIED', 'EFFECTIVE', '2026-07-05 09:00:00.000000', 1),
    (429003, 'E02-D03', 'E02_ENV', 'env_issue_record', 421003, 'E02-D03', '临时堆土场边坡防护不足', '弃渣点2临时堆土区', 'waste-2-1', 'PENDING_REVIEW', 'MEDIUM', 'GENERAL', '2026-07-20 00:00:00.000000', '2026-06-28 09:00:00.000000', NULL, NULL, NULL, 'demo', 1, 'VERIFIED', 'EFFECTIVE', '2026-06-28 09:00:00.000000', 1),
    (429004, 'E02-D04', 'E02_ENV', 'env_issue_record', 421004, 'E02-D04', '夜间施工噪声超标投诉', '边坡监测点1邻近居民区', 'slope-1-1', 'PENDING_CLOSURE', 'MEDIUM', 'GENERAL', '2026-07-18 00:00:00.000000', '2026-06-26 09:00:00.000000', NULL, NULL, NULL, 'demo', 1, 'VERIFIED', 'EFFECTIVE', '2026-06-26 09:00:00.000000', 1),
    (429005, 'E02-D05', 'E02_ENV', 'env_issue_record', 421005, 'E02-D05', '生态敏感区施工临时便道恢复', '生态保护区1缓冲带', 'eco-1-1', 'CLOSED', 'HIGH', 'GENERAL', '2026-06-30 00:00:00.000000', '2026-06-15 09:00:00.000000', '2026-07-01 15:00:00.000000', '销项确认：恢复面积、植被覆盖率达标', NULL, 'demo', 1, 'VERIFIED', 'EFFECTIVE', '2026-06-15 09:00:00.000000', 1),
    (429006, 'E02-D06', 'E02_ENV', 'env_issue_record', 421006, 'E02-D06', '拌合站粉尘无组织排放（已合并）', '弃渣点1邻近拌合站', 'waste-1-1', 'MERGED', 'LOW', 'GENERAL', '2026-07-15 00:00:00.000000', '2026-07-01 09:00:00.000000', '2026-07-03 10:00:00.000000', '合并至E02-D01', 429001, 'demo', 1, 'VERIFIED', 'EFFECTIVE', '2026-07-01 09:00:00.000000', 1),
    (429007, 'E02-D07', 'E02_ENV', 'env_issue_record', 421007, 'E02-D07', '沉淀池出水SS复检不合格（退回重改）', '水源保护区2邻近沉淀池出口', 'water-2-1', 'RECTIFYING', 'HIGH', 'GENERAL', '2026-07-25 00:00:00.000000', '2026-06-20 09:00:00.000000', NULL, NULL, NULL, 'demo', 1, 'VERIFIED', 'EFFECTIVE', '2026-06-20 09:00:00.000000', 1);

-- --------------------------------------------------------------------------
-- 5. 状态轨迹（含 sequence_no / action_at / client_request_id / data_nature）
-- --------------------------------------------------------------------------
INSERT INTO e_case_status_history
  (id, case_id, sequence_no, from_status, to_status, action_code, transition_result, action_at, operator_name, operator_org_name, comment, client_request_id, data_nature, is_demo)
VALUES
  (429101, 429001, 1, NULL, 'DISCOVERED', 'CREATE_CASE', 'SUCCESS', '2026-07-02 09:00:00', '巡检员A', '安全环保部', '现场巡检发现弃渣场覆盖不到位', 'E02-D01-H1', 'demo', 1),
  (429102, 429001, 2, 'DISCOVERED', 'PENDING_RECTIFICATION', 'ISSUE_RECTIFICATION', 'SUCCESS', '2026-07-02 14:00:00', '安全环保部', '宜罗公司', '下发整改通知单', 'E02-D01-H2', 'demo', 1),
  (429103, 429001, 3, 'PENDING_RECTIFICATION', 'RECTIFYING', 'START_RECTIFICATION', 'SUCCESS', '2026-07-03 08:00:00', '张工', '工程管理部', '施工单位开始覆盖防尘网', 'E02-D01-H3', 'demo', 1),

  (429111, 429002, 1, NULL, 'DISCOVERED', 'CREATE_CASE', 'SUCCESS', '2026-07-05 09:00:00', '王监测', '监测站B', '废水在线监测异常', 'E02-D02-H1', 'demo', 1),
  (429112, 429002, 2, 'DISCOVERED', 'PENDING_RECTIFICATION', 'ISSUE_RECTIFICATION', 'SUCCESS', '2026-07-05 11:00:00', '安全环保部', '宜罗公司', '通知单已下发', 'E02-D02-H2', 'demo', 1),
  (429113, 429002, 3, 'PENDING_RECTIFICATION', 'RECTIFYING', 'START_RECTIFICATION', 'SUCCESS', '2026-07-06 09:00:00', '赵部长', '安全环保部', '维修人员到场排查', 'E02-D02-H3', 'demo', 1),

  (429121, 429003, 1, NULL, 'DISCOVERED', 'CREATE_CASE', 'SUCCESS', '2026-06-28 09:00:00', '陈监理', '监理单位', '雨季边坡冲刷隐患', 'E02-D03-H1', 'demo', 1),
  (429122, 429003, 2, 'DISCOVERED', 'PENDING_RECTIFICATION', 'ISSUE_RECTIFICATION', 'SUCCESS', '2026-06-28 10:30:00', '工程管理部', '宜罗公司', '通知单已下发', 'E02-D03-H2', 'demo', 1),
  (429123, 429003, 3, 'PENDING_RECTIFICATION', 'RECTIFYING', 'START_RECTIFICATION', 'SUCCESS', '2026-06-29 08:00:00', '刘经理', '工程管理部', '开始坡面防护施工', 'E02-D03-H3', 'demo', 1),
  (429124, 429003, 4, 'RECTIFYING', 'PENDING_REVIEW', 'SUBMIT_RECTIFICATION', 'SUCCESS', '2026-07-08 16:00:00', '刘经理', '工程管理部', '提交整改完成报告及影像资料', 'E02-D03-H4', 'demo', 1),

  (429131, 429004, 1, NULL, 'DISCOVERED', 'CREATE_CASE', 'SUCCESS', '2026-06-26 09:00:00', '周受理', '投诉受理中心', '居民投诉夜间噪声', 'E02-D04-H1', 'demo', 1),
  (429132, 429004, 2, 'DISCOVERED', 'PENDING_RECTIFICATION', 'ISSUE_RECTIFICATION', 'SUCCESS', '2026-06-26 10:00:00', '安全环保部', '宜罗公司', '通知单已下发', 'E02-D04-H2', 'demo', 1),
  (429133, 429004, 3, 'PENDING_RECTIFICATION', 'RECTIFYING', 'START_RECTIFICATION', 'SUCCESS', '2026-06-27 08:00:00', '赵部长', '安全环保部', '调整施工时间，加装隔音屏障', 'E02-D04-H3', 'demo', 1),
  (429134, 429004, 4, 'RECTIFYING', 'PENDING_REVIEW', 'SUBMIT_RECTIFICATION', 'SUCCESS', '2026-07-05 15:00:00', '赵部长', '安全环保部', '提交噪声复测报告', 'E02-D04-H4', 'demo', 1),
  (429135, 429004, 5, 'PENDING_REVIEW', 'PENDING_CLOSURE', 'REVIEW_PASS', 'SUCCESS', '2026-07-10 10:00:00', '吴监理', '监理单位', '复测达标，同意销项', 'E02-D04-H5', 'demo', 1),

  (429141, 429005, 1, NULL, 'DISCOVERED', 'CREATE_CASE', 'SUCCESS', '2026-06-15 09:00:00', '郑监测', '生态监测站', '生态巡查发现便道未恢复', 'E02-D05-H1', 'demo', 1),
  (429142, 429005, 2, 'DISCOVERED', 'PENDING_RECTIFICATION', 'ISSUE_RECTIFICATION', 'SUCCESS', '2026-06-15 11:00:00', '总工办', '宜罗公司', '通知单已下发', 'E02-D05-H2', 'demo', 1),
  (429143, 429005, 3, 'PENDING_RECTIFICATION', 'RECTIFYING', 'START_RECTIFICATION', 'SUCCESS', '2026-06-16 08:00:00', '孙总工', '总工办', '开始植被恢复施工', 'E02-D05-H3', 'demo', 1),
  (429144, 429005, 4, 'RECTIFYING', 'PENDING_REVIEW', 'SUBMIT_RECTIFICATION', 'SUCCESS', '2026-06-25 16:00:00', '孙总工', '总工办', '提交恢复验收资料', 'E02-D05-H4', 'demo', 1),
  (429145, 429005, 5, 'PENDING_REVIEW', 'PENDING_CLOSURE', 'REVIEW_PASS', 'SUCCESS', '2026-06-28 10:00:00', '钱专家', '生态专家组', '验收通过', 'E02-D05-H5', 'demo', 1),
  (429146, 429005, 6, 'PENDING_CLOSURE', 'CLOSED', 'CLOSE_CASE', 'SUCCESS', '2026-07-01 15:00:00', '孙总工', '总工办', '销项确认：恢复面积、植被覆盖率达标', 'E02-D05-H6', 'demo', 1),

  (429151, 429006, 1, NULL, 'DISCOVERED', 'CREATE_CASE', 'SUCCESS', '2026-07-01 09:00:00', '巡检员A', '安全环保部', '拌合站粉尘问题', 'E02-D06-H1', 'demo', 1),
  (429152, 429006, 2, 'DISCOVERED', 'MERGED', 'MERGE_CASE', 'SUCCESS', '2026-07-03 10:00:00', '张工', '工程管理部', '合并至E02-D01统一整改', 'E02-D06-H2', 'demo', 1),

  (429161, 429007, 1, NULL, 'DISCOVERED', 'CREATE_CASE', 'SUCCESS', '2026-06-20 09:00:00', '王监测', '监测站B', '出水SS超标', 'E02-D07-H1', 'demo', 1),
  (429162, 429007, 2, 'DISCOVERED', 'PENDING_RECTIFICATION', 'ISSUE_RECTIFICATION', 'SUCCESS', '2026-06-20 11:00:00', '安全环保部', '宜罗公司', '通知单已下发', 'E02-D07-H2', 'demo', 1),
  (429163, 429007, 3, 'PENDING_RECTIFICATION', 'RECTIFYING', 'START_RECTIFICATION', 'SUCCESS', '2026-06-21 08:00:00', '赵部长', '安全环保部', '第一轮：调整加药量', 'E02-D07-H3', 'demo', 1),
  (429164, 429007, 4, 'RECTIFYING', 'PENDING_REVIEW', 'SUBMIT_RECTIFICATION', 'SUCCESS', '2026-07-01 16:00:00', '赵部长', '安全环保部', '提交第一轮整改报告', 'E02-D07-H4', 'demo', 1),
  (429165, 429007, 5, 'PENDING_REVIEW', 'RECTIFYING', 'REVIEW_REJECT', 'RETURNED', '2026-07-05 09:00:00', '吴监理', '监理单位', '复测SS仍超标（45mg/L，限值30mg/L），退回重改', 'E02-D07-H5', 'demo', 1),
  (429166, 429007, 6, 'RECTIFYING', 'PENDING_RECTIFICATION', 'ISSUE_RECTIFICATION', 'SUCCESS', '2026-07-05 14:00:00', '安全环保部', '宜罗公司', '第二轮整改通知', 'E02-D07-H6', 'demo', 1),
  (429167, 429007, 7, 'PENDING_RECTIFICATION', 'RECTIFYING', 'START_RECTIFICATION', 'SUCCESS', '2026-07-06 08:00:00', '赵部长', '安全环保部', '第二轮：更换絮凝剂、清洗沉淀池（进行中）', 'E02-D07-H7', 'demo', 1);

UPDATE e_closure_case SET current_status_history_id = 429103 WHERE id = 429001;
UPDATE e_closure_case SET current_status_history_id = 429113 WHERE id = 429002;
UPDATE e_closure_case SET current_status_history_id = 429124 WHERE id = 429003;
UPDATE e_closure_case SET current_status_history_id = 429135 WHERE id = 429004;
UPDATE e_closure_case SET current_status_history_id = 429146 WHERE id = 429005;
UPDATE e_closure_case SET current_status_history_id = 429152 WHERE id = 429006;
UPDATE e_closure_case SET current_status_history_id = 429167 WHERE id = 429007;

-- --------------------------------------------------------------------------
-- 6. 参与方（user_name / valid_from / data_nature）
-- --------------------------------------------------------------------------
INSERT INTO e_case_party
  (case_id, party_role, org_name, user_name, valid_from, is_current, data_nature, is_demo)
VALUES
  (429001, 'DISCOVERER', '安全环保部', '巡检员A', '2026-07-02 09:00:00', 1, 'demo', 1),
  (429001, 'RESPONSIBLE', '工程管理部', '张工', '2026-07-02 09:00:00', 1, 'demo', 1),
  (429001, 'REVIEWER', '监理单位', '李监理', '2026-07-02 09:00:00', 1, 'demo', 1),
  (429002, 'DISCOVERER', '监测站B', '王监测', '2026-07-05 09:00:00', 1, 'demo', 1),
  (429002, 'RESPONSIBLE', '安全环保部', '赵部长', '2026-07-05 09:00:00', 1, 'demo', 1),
  (429003, 'DISCOVERER', '监理单位', '陈监理', '2026-06-28 09:00:00', 1, 'demo', 1),
  (429003, 'RESPONSIBLE', '工程管理部', '刘经理', '2026-06-28 09:00:00', 1, 'demo', 1),
  (429003, 'REVIEWER', '监理单位', '李监理', '2026-06-28 09:00:00', 1, 'demo', 1),
  (429004, 'DISCOVERER', '投诉受理中心', '周受理', '2026-06-26 09:00:00', 1, 'demo', 1),
  (429004, 'RESPONSIBLE', '安全环保部', '赵部长', '2026-06-26 09:00:00', 1, 'demo', 1),
  (429004, 'REVIEWER', '监理单位', '吴监理', '2026-06-26 09:00:00', 1, 'demo', 1),
  (429005, 'DISCOVERER', '生态监测站', '郑监测', '2026-06-15 09:00:00', 1, 'demo', 1),
  (429005, 'RESPONSIBLE', '总工办', '孙总工', '2026-06-15 09:00:00', 1, 'demo', 1),
  (429005, 'REVIEWER', '生态专家组', '钱专家', '2026-06-15 09:00:00', 1, 'demo', 1),
  (429005, 'CLOSER', '总工办', '孙总工', '2026-06-15 09:00:00', 1, 'demo', 1),
  (429006, 'DISCOVERER', '安全环保部', '巡检员A', '2026-07-01 09:00:00', 1, 'demo', 1),
  (429006, 'RESPONSIBLE', '工程管理部', '张工', '2026-07-01 09:00:00', 1, 'demo', 1),
  (429007, 'DISCOVERER', '监测站B', '王监测', '2026-06-20 09:00:00', 1, 'demo', 1),
  (429007, 'RESPONSIBLE', '安全环保部', '赵部长', '2026-06-20 09:00:00', 1, 'demo', 1),
  (429007, 'REVIEWER', '监理单位', '吴监理', '2026-06-20 09:00:00', 1, 'demo', 1);

-- --------------------------------------------------------------------------
-- 7. 证据（必须挂 document_id；D05 销项为确认类资料；D07 无本轮已交整改）
-- --------------------------------------------------------------------------
INSERT INTO e_case_evidence
  (case_id, document_id, evidence_role, version_no, is_current, validity_status, verification_status, data_nature, is_demo)
VALUES
  (429001, 422001, 'FORMAL_NOTICE', 1, 1, 'VALID', 'VERIFIED', 'demo', 1),
  (429002, 422002, 'FORMAL_NOTICE', 1, 1, 'VALID', 'VERIFIED', 'demo', 1),
  (429003, 422003, 'FORMAL_NOTICE', 1, 1, 'VALID', 'VERIFIED', 'demo', 1),
  (429003, 422004, 'RECTIFICATION_MATERIAL', 1, 1, 'VALID', 'VERIFIED', 'demo', 1),
  (429004, 422005, 'FORMAL_NOTICE', 1, 1, 'VALID', 'VERIFIED', 'demo', 1),
  (429004, 422006, 'RECTIFICATION_MATERIAL', 1, 1, 'VALID', 'VERIFIED', 'demo', 1),
  (429004, 422007, 'REVIEW_OPINION', 1, 1, 'VALID', 'VERIFIED', 'demo', 1),
  (429005, 422008, 'FORMAL_NOTICE', 1, 1, 'VALID', 'VERIFIED', 'demo', 1),
  (429005, 422009, 'RECTIFICATION_MATERIAL', 1, 1, 'VALID', 'VERIFIED', 'demo', 1),
  (429005, 422010, 'REVIEW_OPINION', 1, 1, 'VALID', 'VERIFIED', 'demo', 1),
  (429005, 422011, 'CLOSURE_DOCUMENT', 1, 1, 'VALID', 'VERIFIED', 'demo', 1),
  (429007, 422012, 'FORMAL_NOTICE', 1, 1, 'VALID', 'VERIFIED', 'demo', 1),
  (429007, 422013, 'RECTIFICATION_MATERIAL', 1, 1, 'VALID', 'VERIFIED', 'demo', 1),
  (429007, 422014, 'REVIEW_OPINION', 1, 1, 'VALID', 'VERIFIED', 'demo', 1);

-- --------------------------------------------------------------------------
-- 8. GIS 业务关系（挂本体：弃渣/水源/生态/边坡敏感点，避免整条标段重叠）
-- --------------------------------------------------------------------------
INSERT INTO gis_feature_business_relation
  (project_id, feature_id, relation_type, relation_code, relation_name, relation_status, risk_level, source_table, source_id, summary)
VALUES
  ('LUOYI-ESG', 'waste-1-1', 'environment_problem', 'E02-D01', '弃渣点1扬尘', '整改中', 2, 'env_issue_record', 'E02-D01', '演示：挂弃渣场本体，非整条标段'),
  ('LUOYI-ESG', 'water-2-1', 'environment_problem', 'E02-D02', '水源区邻近废水处理故障', '整改中', 2, 'env_issue_record', 'E02-D02', '演示：挂水源保护区本体'),
  ('LUOYI-ESG', 'waste-2-1', 'environment_problem', 'E02-D03', '弃渣点2堆土防护', '待复查', 2, 'env_issue_record', 'E02-D03', '演示：挂弃渣/堆土本体'),
  ('LUOYI-ESG', 'slope-1-1', 'environment_problem', 'E02-D04', '边坡敏感点邻近噪声投诉', '待销项', 2, 'env_issue_record', 'E02-D04', '演示：挂边坡敏感点（居民区邻近代理）'),
  ('LUOYI-ESG', 'eco-1-1',     'environment_problem', 'E02-D05', '生态敏感区恢复', '已闭环', 2, 'env_issue_record', 'E02-D05', '演示：挂生态保护区本体'),
  ('LUOYI-ESG', 'waste-1-1', 'environment_problem', 'E02-D06', '弃渣点1邻近拌合站粉尘（已合并）', '已合并', 1, 'env_issue_record', 'E02-D06', '演示：已合并不计未闭环'),
  ('LUOYI-ESG', 'water-2-1', 'environment_problem', 'E02-D07', '水源区邻近沉淀池SS超标', '整改中', 2, 'env_issue_record', 'E02-D07', '演示：挂水源保护区本体');
