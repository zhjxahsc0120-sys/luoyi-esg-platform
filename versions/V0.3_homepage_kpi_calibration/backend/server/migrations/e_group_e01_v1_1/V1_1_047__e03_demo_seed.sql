-- ============================================================================
-- V1_1_047__e03_demo_seed.sql
-- E03 P1 演示双写种子（D01-D07）
-- 幂等：先按业务键/域清理，再插入
-- 权威依据：E03_Trae实施任务单_P1_V1.0 + E03_工作台设计说明_B方案_V1.0冻结稿
-- ============================================================================

SET FOREIGN_KEY_CHECKS = 0;

-- --------------------------------------------------------------------------
-- 1. 幂等清理
-- --------------------------------------------------------------------------
DELETE FROM gis_feature_business_relation
 WHERE relation_type = 'E03_WATER_ISSUE';

DELETE FROM e_case_evidence
 WHERE case_id IN (SELECT id FROM e_closure_case WHERE case_domain = 'E03_WATER' AND is_demo = 1);

DELETE FROM e_case_party
 WHERE case_id IN (SELECT id FROM e_closure_case WHERE case_domain = 'E03_WATER' AND is_demo = 1);

DELETE FROM e_case_status_history
 WHERE case_id IN (SELECT id FROM e_closure_case WHERE case_domain = 'E03_WATER' AND is_demo = 1);

DELETE FROM e_closure_case
 WHERE case_domain = 'E03_WATER' AND is_demo = 1;

DELETE FROM water_protection_issue
 WHERE is_demo = 1 AND (business_code LIKE 'E03-D%' OR id BETWEEN 711001 AND 711099);

DELETE FROM document_record
 WHERE id BETWEEN 423001 AND 423099;

SET FOREIGN_KEY_CHECKS = 1;

-- --------------------------------------------------------------------------
-- 2. 占位资料主档
-- --------------------------------------------------------------------------
INSERT INTO document_record
  (id, document_code, document_name, document_type, module_code, source_name, validity_status, document_status, confirm_status)
VALUES
  -- D01
  (423001, 'E03-DOC-D01-N', '水保整改通知 E03-D01', 'FORMAL_NOTICE', 'E03', '水保检查通知', '有效', 'ACTIVE', 'CONFIRMED'),
  -- D02
  (423002, 'E03-DOC-D02-N', '水保整改通知 E03-D02', 'FORMAL_NOTICE', 'E03', '水保检查通知', '有效', 'ACTIVE', 'CONFIRMED'),
  -- D03
  (423003, 'E03-DOC-D03-N', '水保整改通知 E03-D03', 'FORMAL_NOTICE', 'E03', '水保检查通知', '有效', 'ACTIVE', 'CONFIRMED'),
  (423004, 'E03-DOC-D03-R', '边坡防护整改资料 E03-D03', 'RECTIFICATION_MATERIAL', 'E03', '整改回复及影像', '有效', 'ACTIVE', 'CONFIRMED'),
  -- D04
  (423005, 'E03-DOC-D04-N', '水保整改通知 E03-D04', 'FORMAL_NOTICE', 'E03', '水保检查通知', '有效', 'ACTIVE', 'CONFIRMED'),
  (423006, 'E03-DOC-D04-R', '水土流失防治整改资料 E03-D04', 'RECTIFICATION_MATERIAL', 'E03', '整改回复', '有效', 'ACTIVE', 'CONFIRMED'),
  (423007, 'E03-DOC-D04-V', '复查意见 E03-D04', 'REVIEW_OPINION', 'E03', '复查通过意见', '有效', 'ACTIVE', 'CONFIRMED'),
  -- D05
  (423008, 'E03-DOC-D05-N', '水保整改通知 E03-D05', 'FORMAL_NOTICE', 'E03', '水保检查通知', '有效', 'ACTIVE', 'CONFIRMED'),
  (423009, 'E03-DOC-D05-R', '复绿恢复整改资料 E03-D05', 'RECTIFICATION_MATERIAL', 'E03', '复绿影像及报告', '有效', 'ACTIVE', 'CONFIRMED'),
  (423010, 'E03-DOC-D05-V', '复查意见 E03-D05', 'REVIEW_OPINION', 'E03', '复查通过意见', '有效', 'ACTIVE', 'CONFIRMED'),
  (423011, 'E03-DOC-D05-C', '等价销项确认 E03-D05', 'CLOSURE_DOCUMENT', 'E03', '水保销项确认', '有效', 'ACTIVE', 'CONFIRMED'),
  -- D06
  (423012, 'E03-DOC-D06-N', '水保整改通知 E03-D06', 'FORMAL_NOTICE', 'E03', '水保检查通知', '有效', 'ACTIVE', 'CONFIRMED'),
  -- D07
  (423013, 'E03-DOC-D07-N', '水保整改通知 E03-D07', 'FORMAL_NOTICE', 'E03', '水保检查通知', '有效', 'ACTIVE', 'CONFIRMED'),
  (423014, 'E03-DOC-D07-R1', '表土保护上轮整改资料 E03-D07', 'RECTIFICATION_MATERIAL', 'E03', '上轮整改回复', '有效', 'ACTIVE', 'CONFIRMED'),
  (423015, 'E03-DOC-D07-RET', '复查退回意见 E03-D07', 'REVIEW_OPINION', 'E03', '退回原因说明', '有效', 'ACTIVE', 'CONFIRMED');

-- --------------------------------------------------------------------------
-- 3. 台账 A：water_protection_issue
-- --------------------------------------------------------------------------
INSERT INTO water_protection_issue
  (id, document_id, issue_status, found_date, closed_date, created_at,
   is_demo, data_nature, effective_status, business_code, issue_name, issue_type,
   overdue, deadline, responsible_org_name, location_text, description, discovery_basis)
VALUES
  -- D01：整改中，无逾期
  (711001, NULL, '整改中', '2026-07-02', NULL, '2026-07-02 09:00:00',
   1, 'demo', 'EFFECTIVE', 'E03-D01', '标段一弃渣场挡墙未按设计施工', '弃渣场',
   0, '2026-07-20', '工程管理部', '标段一弃渣场K12+300', '挡墙高度不足，存在安全隐患', '现场巡查'),

  -- D02：整改中，逾期
  (711002, NULL, '整改中', '2026-07-05', NULL, '2026-07-05 09:00:00',
   1, 'demo', 'EFFECTIVE', 'E03-D02', '标段三截排水沟断面不足', '截排水',
   1, '2026-07-10', '安全环保部', '标段三K30+500排水沟', '截排水沟断面偏小，暴雨期排水能力不足', '监理报告'),

  -- D03：待复查
  (711003, NULL, '待复查', '2026-06-28', NULL, '2026-06-28 09:00:00',
   1, 'demo', 'EFFECTIVE', 'E03-D03', '标段一边坡防护措施不到位', '边坡防护',
   0, '2026-07-20', '工程管理部', '标段一K8+200边坡', '边坡拱形骨架施工质量不达标', '现场巡查'),

  -- D04：待销项
  (711004, NULL, '待销项', '2026-06-26', NULL, '2026-06-26 09:00:00',
   1, 'demo', 'EFFECTIVE', 'E03-D04', '标段二水土流失防治措施薄弱', '水土流失防治',
   0, '2026-07-18', '安全环保部', '标段二K20+100填方区', '填方区裸露面积过大，缺少临时防护', '监测报告'),

  -- D05：已闭环，不计KPI
  (711005, NULL, '已闭环', '2026-06-15', '2026-07-01', '2026-06-15 09:00:00',
   1, 'demo', 'EFFECTIVE', 'E03-D05', '生态敏感区临时便道恢复', '复绿恢复',
   0, '2026-06-30', '总工办', '生态敏感区缓冲带', '临时施工便道植被恢复完成', '现场巡查'),

  -- D06：已合并，不计KPI
  (711006, NULL, '已合并', '2026-07-01', '2026-07-03', '2026-07-01 09:00:00',
   1, 'demo', 'EFFECTIVE', 'E03-D06', '标段二临时用地复垦（已合并至D01）', '临时用地',
   0, '2026-07-15', '工程管理部', '标段二K18+000', '临时用地复垦问题已合并处理', '现场巡查'),

  -- D07：退回后整改中（台账状态仍为整改中）
  (711007, NULL, '整改中', '2026-06-20', NULL, '2026-06-20 09:00:00',
   1, 'demo', 'EFFECTIVE', 'E03-D07', '标段二表土保护措施不到位（退回重改）', '表土保护',
   0, '2026-07-25', '安全环保部', '标段二K22+800', '表土剥离厚度不足，保护措施不到位', '监理报告');

-- --------------------------------------------------------------------------
-- 4. 案卷 B：e_closure_case
-- --------------------------------------------------------------------------
INSERT INTO e_closure_case
  (id, case_code, case_domain, source_table, source_record_id, source_business_key,
   title, location_text, current_status, priority, severity, deadline,
   opened_at, closed_at, closure_reason, merged_into_case_id,
   data_nature, is_demo, verification_status, effective_status, created_at)
VALUES
  -- D01
  (731001, 'E03-CC-D01', 'E03_WATER', 'water_protection_issue', 711001, 'E03-D01',
   '标段一弃渣场挡墙未按设计施工', '标段一弃渣场K12+300', 'RECTIFYING', 'HIGH', 'MAJOR', '2026-07-20',
   '2026-07-02 09:00:00', NULL, NULL, NULL,
   'demo', 1, 'PENDING_REVIEW', 'EFFECTIVE', '2026-07-02 09:00:00'),

  -- D02
  (731002, 'E03-CC-D02', 'E03_WATER', 'water_protection_issue', 711002, 'E03-D02',
   '标段三截排水沟断面不足', '标段三K30+500排水沟', 'RECTIFYING', 'HIGH', 'MAJOR', '2026-07-10',
   '2026-07-05 09:00:00', NULL, NULL, NULL,
   'demo', 1, 'PENDING_REVIEW', 'EFFECTIVE', '2026-07-05 09:00:00'),

  -- D03
  (731003, 'E03-CC-D03', 'E03_WATER', 'water_protection_issue', 711003, 'E03-D03',
   '标段一边坡防护措施不到位', '标段一K8+200边坡', 'PENDING_REVIEW', 'MEDIUM', 'MODERATE', '2026-07-20',
   '2026-06-28 09:00:00', NULL, NULL, NULL,
   'demo', 1, 'PENDING_REVIEW', 'EFFECTIVE', '2026-06-28 09:00:00'),

  -- D04
  (731004, 'E03-CC-D04', 'E03_WATER', 'water_protection_issue', 711004, 'E03-D04',
   '标段二水土流失防治措施薄弱', '标段二K20+100填方区', 'PENDING_CLOSURE', 'MEDIUM', 'MODERATE', '2026-07-18',
   '2026-06-26 09:00:00', NULL, NULL, NULL,
   'demo', 1, 'PENDING_REVIEW', 'EFFECTIVE', '2026-06-26 09:00:00'),

  -- D05
  (731005, 'E03-CC-D05', 'E03_WATER', 'water_protection_issue', 711005, 'E03-D05',
   '生态敏感区临时便道恢复', '生态敏感区缓冲带', 'CLOSED', 'LOW', 'MINOR', '2026-06-30',
   '2026-06-15 09:00:00', '2026-07-01 15:00:00', '整改完成，复查通过，销项确认',
   NULL, 'demo', 1, 'APPROVED', 'EFFECTIVE', '2026-06-15 09:00:00'),

  -- D06
  (731006, 'E03-CC-D06', 'E03_WATER', 'water_protection_issue', 711006, 'E03-D06',
   '标段二临时用地复垦（已合并至D01）', '标段二K18+000', 'MERGED', 'MEDIUM', 'MINOR', '2026-07-15',
   '2026-07-01 09:00:00', '2026-07-03 10:00:00', '合并至E03-D01处理',
   731001, 'demo', 1, 'PENDING_REVIEW', 'EFFECTIVE', '2026-07-01 09:00:00'),

  -- D07
  (731007, 'E03-CC-D07', 'E03_WATER', 'water_protection_issue', 711007, 'E03-D07',
   '标段二表土保护措施不到位（退回重改）', '标段二K22+800', 'RECTIFYING', 'HIGH', 'MAJOR', '2026-07-25',
   '2026-06-20 09:00:00', NULL, NULL, NULL,
   'demo', 1, 'PENDING_REVIEW', 'EFFECTIVE', '2026-06-20 09:00:00');

-- --------------------------------------------------------------------------
-- 5. 参与方 C：e_case_party
-- --------------------------------------------------------------------------
/* Legacy draft used columns that do not exist in the V1.1 e_case_party schema.
INSERT INTO e_case_party (case_id, role, role_label, org_name, user_name, created_at) VALUES
  -- D01
  (731001, 'DISCOVERER', '发现问题人', '监理单位', '张监理', '2026-07-02 09:00:00'),
  (731001, 'RESPONSIBLE', '整改责任人', '工程管理部', '李工', '2026-07-02 09:00:00'),
  (731001, 'REVIEWER', '复查人', '安全环保部', '王主任', '2026-07-02 09:00:00'),
  -- D02
  (731002, 'DISCOVERER', '发现问题人', '监理单位', '张监理', '2026-07-05 09:00:00'),
  (731002, 'RESPONSIBLE', '整改责任人', '安全环保部', '赵工', '2026-07-05 09:00:00'),
  (731002, 'REVIEWER', '复查人', '总工办', '陈总', '2026-07-05 09:00:00'),
  -- D03
  (731003, 'DISCOVERER', '发现问题人', '安全环保部', '王主任', '2026-06-28 09:00:00'),
  (731003, 'RESPONSIBLE', '整改责任人', '工程管理部', '李工', '2026-06-28 09:00:00'),
  (731003, 'REVIEWER', '复查人', '监理单位', '张监理', '2026-06-28 09:00:00'),
  -- D04
  (731004, 'DISCOVERER', '发现问题人', '监测单位', '刘工', '2026-06-26 09:00:00'),
  (731004, 'RESPONSIBLE', '整改责任人', '安全环保部', '赵工', '2026-06-26 09:00:00'),
  (731004, 'REVIEWER', '复查人', '总工办', '陈总', '2026-06-26 09:00:00'),
  -- D05
  (731005, 'DISCOVERER', '发现问题人', '监理单位', '张监理', '2026-06-15 09:00:00'),
  (731005, 'RESPONSIBLE', '整改责任人', '总工办', '陈总', '2026-06-15 09:00:00'),
  (731005, 'REVIEWER', '复查人', '安全环保部', '王主任', '2026-06-15 09:00:00'),
  (731005, 'CLOSER', '销项确认人', '安全环保部', '王主任', '2026-07-01 15:00:00'),
  -- D06
  (731006, 'DISCOVERER', '发现问题人', '监理单位', '张监理', '2026-07-01 09:00:00'),
  (731006, 'RESPONSIBLE', '整改责任人', '工程管理部', '李工', '2026-07-01 09:00:00'),
  -- D07
  (731007, 'DISCOVERER', '发现问题人', '监理单位', '张监理', '2026-06-20 09:00:00'),
  (731007, 'RESPONSIBLE', '整改责任人', '安全环保部', '赵工', '2026-06-20 09:00:00'),
  (731007, 'REVIEWER', '复查人', '总工办', '陈总', '2026-06-20 09:00:00');

-- --------------------------------------------------------------------------
-- 6. 状态轨迹 D：e_case_status_history
-- --------------------------------------------------------------------------
*/

INSERT INTO e_case_party
  (case_id, party_role, org_name, user_name, valid_from, data_nature, is_demo, created_at)
VALUES
  (731001, 'DISCOVERER',  '监理单位',   '张监理', '2026-07-02 09:00:00', 'demo', 1, '2026-07-02 09:00:00'),
  (731001, 'RESPONSIBLE', '工程管理部', '李工',   '2026-07-02 09:00:00', 'demo', 1, '2026-07-02 09:00:00'),
  (731001, 'REVIEWER',    '安全环保部', '王主任', '2026-07-02 09:00:00', 'demo', 1, '2026-07-02 09:00:00'),
  (731002, 'DISCOVERER',  '监理单位',   '张监理', '2026-07-05 09:00:00', 'demo', 1, '2026-07-05 09:00:00'),
  (731002, 'RESPONSIBLE', '安全环保部', '赵工',   '2026-07-05 09:00:00', 'demo', 1, '2026-07-05 09:00:00'),
  (731002, 'REVIEWER',    '总工办',     '陈总',   '2026-07-05 09:00:00', 'demo', 1, '2026-07-05 09:00:00'),
  (731003, 'DISCOVERER',  '安全环保部', '王主任', '2026-06-28 09:00:00', 'demo', 1, '2026-06-28 09:00:00'),
  (731003, 'RESPONSIBLE', '工程管理部', '李工',   '2026-06-28 09:00:00', 'demo', 1, '2026-06-28 09:00:00'),
  (731003, 'REVIEWER',    '监理单位',   '张监理', '2026-06-28 09:00:00', 'demo', 1, '2026-06-28 09:00:00'),
  (731004, 'DISCOVERER',  '监测单位',   '刘工',   '2026-06-26 09:00:00', 'demo', 1, '2026-06-26 09:00:00'),
  (731004, 'RESPONSIBLE', '安全环保部', '赵工',   '2026-06-26 09:00:00', 'demo', 1, '2026-06-26 09:00:00'),
  (731004, 'REVIEWER',    '总工办',     '陈总',   '2026-06-26 09:00:00', 'demo', 1, '2026-06-26 09:00:00'),
  (731005, 'DISCOVERER',  '监理单位',   '张监理', '2026-06-15 09:00:00', 'demo', 1, '2026-06-15 09:00:00'),
  (731005, 'RESPONSIBLE', '总工办',     '陈总',   '2026-06-15 09:00:00', 'demo', 1, '2026-06-15 09:00:00'),
  (731005, 'REVIEWER',    '安全环保部', '王主任', '2026-06-15 09:00:00', 'demo', 1, '2026-06-15 09:00:00'),
  (731005, 'CLOSER',      '安全环保部', '王主任', '2026-07-01 15:00:00', 'demo', 1, '2026-07-01 15:00:00'),
  (731006, 'DISCOVERER',  '监理单位',   '张监理', '2026-07-01 09:00:00', 'demo', 1, '2026-07-01 09:00:00'),
  (731006, 'RESPONSIBLE', '工程管理部', '李工',   '2026-07-01 09:00:00', 'demo', 1, '2026-07-01 09:00:00'),
  (731007, 'DISCOVERER',  '监理单位',   '张监理', '2026-06-20 09:00:00', 'demo', 1, '2026-06-20 09:00:00'),
  (731007, 'RESPONSIBLE', '安全环保部', '赵工',   '2026-06-20 09:00:00', 'demo', 1, '2026-06-20 09:00:00'),
  (731007, 'REVIEWER',    '总工办',     '陈总',   '2026-06-20 09:00:00', 'demo', 1, '2026-06-20 09:00:00');

/* Legacy draft omitted required V1.1 audit columns.
INSERT INTO e_case_status_history (case_id, from_status, to_status, action_code, action_at, operator_name, operator_org_name, comment, transition_result, created_at) VALUES
  -- D01: DISCOVERED → RECTIFYING（整改中）
  (731001, NULL, 'DISCOVERED', 'DISCOVER', '2026-07-02 09:00:00', '张监理', '监理单位', '巡查发现弃渣场挡墙施工质量不达标', 'APPROVED', '2026-07-02 09:00:00'),
  (731001, 'DISCOVERED', 'RECTIFYING', 'START_RECTIFICATION', '2026-07-03 10:00:00', '李工', '工程管理部', '开始挡墙返工', 'APPROVED', '2026-07-03 10:00:00'),

  -- D02: DISCOVERED → RECTIFYING（整改中+逾期）
  (731002, NULL, 'DISCOVERED', 'DISCOVER', '2026-07-05 09:00:00', '张监理', '监理单位', '监理报告指出截排水沟断面不满足设计', 'APPROVED', '2026-07-05 09:00:00'),
  (731002, 'DISCOVERED', 'RECTIFYING', 'START_RECTIFICATION', '2026-07-06 10:00:00', '赵工', '安全环保部', '开始排水沟扩建', 'APPROVED', '2026-07-06 10:00:00'),

  -- D03: DISCOVERED → RECTIFYING → PENDING_REVIEW（待复查）
  (731003, NULL, 'DISCOVERED', 'DISCOVER', '2026-06-28 09:00:00', '王主任', '安全环保部', '巡查发现边坡防护施工质量不达标', 'APPROVED', '2026-06-28 09:00:00'),
  (731003, 'DISCOVERED', 'RECTIFYING', 'START_RECTIFICATION', '2026-06-29 10:00:00', '李工', '工程管理部', '开始边坡拱形骨架返工', 'APPROVED', '2026-06-29 10:00:00'),
  (731003, 'RECTIFYING', 'PENDING_REVIEW', 'SUBMIT_REVIEW', '2026-07-15 14:00:00', '李工', '工程管理部', '整改完成提交复查', 'APPROVED', '2026-07-15 14:00:00'),

  -- D04: DISCOVERED → RECTIFYING → PENDING_REVIEW → PENDING_CLOSURE（待销项）
  (731004, NULL, 'DISCOVERED', 'DISCOVER', '2026-06-26 09:00:00', '刘工', '监测单位', '监测报告显示水土流失防治措施薄弱', 'APPROVED', '2026-06-26 09:00:00'),
  (731004, 'DISCOVERED', 'RECTIFYING', 'START_RECTIFICATION', '2026-06-27 10:00:00', '赵工', '安全环保部', '开始填方区临时防护施工', 'APPROVED', '2026-06-27 10:00:00'),
  (731004, 'RECTIFYING', 'PENDING_REVIEW', 'SUBMIT_REVIEW', '2026-07-10 14:00:00', '赵工', '安全环保部', '整改完成提交复查', 'APPROVED', '2026-07-10 14:00:00'),
  (731004, 'PENDING_REVIEW', 'PENDING_CLOSURE', 'REVIEW_PASS', '2026-07-12 16:00:00', '陈总', '总工办', '复查通过，符合水保要求', 'APPROVED', '2026-07-12 16:00:00'),

  -- D05: DISCOVERED → RECTIFYING → PENDING_REVIEW → PENDING_CLOSURE → CLOSED（已闭环）
  (731005, NULL, 'DISCOVERED', 'DISCOVER', '2026-06-15 09:00:00', '张监理', '监理单位', '巡查发现临时便道未恢复植被', 'APPROVED', '2026-06-15 09:00:00'),
  (731005, 'DISCOVERED', 'RECTIFYING', 'START_RECTIFICATION', '2026-06-16 10:00:00', '陈总', '总工办', '开始便道复绿施工', 'APPROVED', '2026-06-16 10:00:00'),
  (731005, 'RECTIFYING', 'PENDING_REVIEW', 'SUBMIT_REVIEW', '2026-06-25 14:00:00', '陈总', '总工办', '复绿完成提交复查', 'APPROVED', '2026-06-25 14:00:00'),
  (731005, 'PENDING_REVIEW', 'PENDING_CLOSURE', 'REVIEW_PASS', '2026-06-28 16:00:00', '王主任', '安全环保部', '复查通过，植被恢复达标', 'APPROVED', '2026-06-28 16:00:00'),
  (731005, 'PENDING_CLOSURE', 'CLOSED', 'CONFIRM_CLOSURE', '2026-07-01 15:00:00', '王主任', '安全环保部', '销项确认，水保问题闭环', 'APPROVED', '2026-07-01 15:00:00'),

  -- D06: DISCOVERED → MERGED（已合并）
  (731006, NULL, 'DISCOVERED', 'DISCOVER', '2026-07-01 09:00:00', '张监理', '监理单位', '巡查发现临时用地复垦问题', 'APPROVED', '2026-07-01 09:00:00'),
  (731006, 'DISCOVERED', 'MERGED', 'MERGE_INTO', '2026-07-03 10:00:00', '李工', '工程管理部', '合并至E03-D01统一处理', 'APPROVED', '2026-07-03 10:00:00'),

  -- D07: DISCOVERED → RECTIFYING → PENDING_REVIEW → (RETURNED) → RECTIFYING（退回后整改中）
  (731007, NULL, 'DISCOVERED', 'DISCOVER', '2026-06-20 09:00:00', '张监理', '监理单位', '监理报告指出表土保护措施不达标', 'APPROVED', '2026-06-20 09:00:00'),
  (731007, 'DISCOVERED', 'RECTIFYING', 'START_RECTIFICATION', '2026-06-21 10:00:00', '赵工', '安全环保部', '开始表土保护整改（上轮）', 'APPROVED', '2026-06-21 10:00:00'),
  (731007, 'RECTIFYING', 'PENDING_REVIEW', 'SUBMIT_REVIEW', '2026-07-08 14:00:00', '赵工', '安全环保部', '上轮整改完成提交复查', 'APPROVED', '2026-07-08 14:00:00'),
  (731007, 'PENDING_REVIEW', 'RECTIFYING', 'REVIEW_RETURN', '2026-07-10 16:00:00', '陈总', '总工办', '退回：表土剥离厚度仍不满足设计要求，需重新施工', 'RETURNED', '2026-07-10 16:00:00');

-- --------------------------------------------------------------------------
-- 7. 证据 E：e_case_evidence（含 rectification_round_id）
-- --------------------------------------------------------------------------
*/

INSERT INTO e_case_status_history
  (case_id, sequence_no, from_status, to_status, action_code, transition_result,
   action_at, operator_name, operator_org_name, comment, client_request_id,
   data_nature, is_demo, created_at)
VALUES
  (731001, 1, NULL, 'DISCOVERED', 'DISCOVER', 'SUCCESS', '2026-07-02 09:00:00', '张监理', '监理单位', '巡查发现弃渣场挡墙问题', 'E03-D01-H1', 'demo', 1, '2026-07-02 09:00:00'),
  (731001, 2, 'DISCOVERED', 'RECTIFYING', 'START_RECTIFICATION', 'SUCCESS', '2026-07-03 10:00:00', '李工', '工程管理部', '开始挡墙返工', 'E03-D01-H2', 'demo', 1, '2026-07-03 10:00:00'),
  (731002, 1, NULL, 'DISCOVERED', 'DISCOVER', 'SUCCESS', '2026-07-05 09:00:00', '张监理', '监理单位', '监理报告指出截排水沟断面不足', 'E03-D02-H1', 'demo', 1, '2026-07-05 09:00:00'),
  (731002, 2, 'DISCOVERED', 'RECTIFYING', 'START_RECTIFICATION', 'SUCCESS', '2026-07-06 10:00:00', '赵工', '安全环保部', '开始排水沟扩建', 'E03-D02-H2', 'demo', 1, '2026-07-06 10:00:00'),
  (731003, 1, NULL, 'DISCOVERED', 'DISCOVER', 'SUCCESS', '2026-06-28 09:00:00', '王主任', '安全环保部', '巡查发现边坡防护质量问题', 'E03-D03-H1', 'demo', 1, '2026-06-28 09:00:00'),
  (731003, 2, 'DISCOVERED', 'RECTIFYING', 'START_RECTIFICATION', 'SUCCESS', '2026-06-29 10:00:00', '李工', '工程管理部', '开始边坡返工', 'E03-D03-H2', 'demo', 1, '2026-06-29 10:00:00'),
  (731003, 3, 'RECTIFYING', 'PENDING_REVIEW', 'SUBMIT_REVIEW', 'SUCCESS', '2026-07-15 14:00:00', '李工', '工程管理部', '整改完成提交复查', 'E03-D03-H3', 'demo', 1, '2026-07-15 14:00:00'),
  (731004, 1, NULL, 'DISCOVERED', 'DISCOVER', 'SUCCESS', '2026-06-26 09:00:00', '刘工', '监测单位', '发现水土流失防治措施薄弱', 'E03-D04-H1', 'demo', 1, '2026-06-26 09:00:00'),
  (731004, 2, 'DISCOVERED', 'RECTIFYING', 'START_RECTIFICATION', 'SUCCESS', '2026-06-27 10:00:00', '赵工', '安全环保部', '开始临时防护施工', 'E03-D04-H2', 'demo', 1, '2026-06-27 10:00:00'),
  (731004, 3, 'RECTIFYING', 'PENDING_REVIEW', 'SUBMIT_REVIEW', 'SUCCESS', '2026-07-10 14:00:00', '赵工', '安全环保部', '整改完成提交复查', 'E03-D04-H3', 'demo', 1, '2026-07-10 14:00:00'),
  (731004, 4, 'PENDING_REVIEW', 'PENDING_CLOSURE', 'REVIEW_PASS', 'SUCCESS', '2026-07-12 16:00:00', '陈总', '总工办', '复查通过', 'E03-D04-H4', 'demo', 1, '2026-07-12 16:00:00'),
  (731005, 1, NULL, 'DISCOVERED', 'DISCOVER', 'SUCCESS', '2026-06-15 09:00:00', '张监理', '监理单位', '发现临时便道未恢复植被', 'E03-D05-H1', 'demo', 1, '2026-06-15 09:00:00'),
  (731005, 2, 'DISCOVERED', 'RECTIFYING', 'START_RECTIFICATION', 'SUCCESS', '2026-06-16 10:00:00', '陈总', '总工办', '开始便道复绿', 'E03-D05-H2', 'demo', 1, '2026-06-16 10:00:00'),
  (731005, 3, 'RECTIFYING', 'PENDING_REVIEW', 'SUBMIT_REVIEW', 'SUCCESS', '2026-06-25 14:00:00', '陈总', '总工办', '复绿完成提交复查', 'E03-D05-H3', 'demo', 1, '2026-06-25 14:00:00'),
  (731005, 4, 'PENDING_REVIEW', 'PENDING_CLOSURE', 'REVIEW_PASS', 'SUCCESS', '2026-06-28 16:00:00', '王主任', '安全环保部', '复查通过', 'E03-D05-H4', 'demo', 1, '2026-06-28 16:00:00'),
  (731005, 5, 'PENDING_CLOSURE', 'CLOSED', 'CONFIRM_CLOSURE', 'SUCCESS', '2026-07-01 15:00:00', '王主任', '安全环保部', '销项确认', 'E03-D05-H5', 'demo', 1, '2026-07-01 15:00:00'),
  (731006, 1, NULL, 'DISCOVERED', 'DISCOVER', 'SUCCESS', '2026-07-01 09:00:00', '张监理', '监理单位', '发现临时用地复垦问题', 'E03-D06-H1', 'demo', 1, '2026-07-01 09:00:00'),
  (731006, 2, 'DISCOVERED', 'MERGED', 'MERGE_INTO', 'SUCCESS', '2026-07-03 10:00:00', '李工', '工程管理部', '合并至E03-D01统一处理', 'E03-D06-H2', 'demo', 1, '2026-07-03 10:00:00'),
  (731007, 1, NULL, 'DISCOVERED', 'DISCOVER', 'SUCCESS', '2026-06-20 09:00:00', '张监理', '监理单位', '发现表土保护措施问题', 'E03-D07-H1', 'demo', 1, '2026-06-20 09:00:00'),
  (731007, 2, 'DISCOVERED', 'RECTIFYING', 'START_RECTIFICATION', 'SUCCESS', '2026-06-21 10:00:00', '赵工', '安全环保部', '开始上一轮整改', 'E03-D07-H2', 'demo', 1, '2026-06-21 10:00:00'),
  (731007, 3, 'RECTIFYING', 'PENDING_REVIEW', 'SUBMIT_REVIEW', 'SUCCESS', '2026-07-08 14:00:00', '赵工', '安全环保部', '上一轮整改完成提交复查', 'E03-D07-H3', 'demo', 1, '2026-07-08 14:00:00'),
  (731007, 4, 'PENDING_REVIEW', 'RECTIFYING', 'REVIEW_RETURN', 'RETURNED', '2026-07-10 16:00:00', '陈总', '总工办', '复查退回，需重新施工', 'E03-D07-H4', 'demo', 1, '2026-07-10 16:00:00');

/* Legacy draft referenced title and description columns that belong to document_record.
INSERT INTO e_case_evidence
  (case_id, evidence_role, document_id, title, description, validity_status, is_current, is_demo, data_nature, rectification_round_id, created_at)
VALUES
  -- D01：通知
  (731001, 'FORMAL_NOTICE', 423001, '水保整改通知 E03-D01', '正式检查发现弃渣场挡墙问题，要求限期整改', 'VALID', 1, 1, 'demo', NULL, '2026-07-02 09:00:00'),

  -- D02：通知
  (731002, 'FORMAL_NOTICE', 423002, '水保整改通知 E03-D02', '监理报告指出截排水沟断面不足', 'VALID', 1, 1, 'demo', NULL, '2026-07-05 09:00:00'),

  -- D03：通知 + 本轮整改材料
  (731003, 'FORMAL_NOTICE', 423003, '水保整改通知 E03-D03', '巡查发现边坡防护施工质量不达标', 'VALID', 1, 1, 'demo', NULL, '2026-06-28 09:00:00'),
  (731003, 'RECTIFICATION_MATERIAL', 423004, '边坡防护整改资料 E03-D03', '拱形骨架返工完成，含施工影像', 'VALID', 1, 1, 'demo', 1, '2026-07-15 14:00:00'),

  -- D04：通知 + 整改材料 + 复查意见
  (731004, 'FORMAL_NOTICE', 423005, '水保整改通知 E03-D04', '监测报告指出水土流失防治措施薄弱', 'VALID', 1, 1, 'demo', NULL, '2026-06-26 09:00:00'),
  (731004, 'RECTIFICATION_MATERIAL', 423006, '水土流失防治整改资料 E03-D04', '填方区临时防护施工完成', 'VALID', 1, 1, 'demo', 1, '2026-07-10 14:00:00'),
  (731004, 'REVIEW_OPINION', 423007, '复查意见 E03-D04', '复查通过，符合水保要求', 'VALID', 1, 1, 'demo', NULL, '2026-07-12 16:00:00'),

  -- D05：通知 + 整改材料 + 复查意见 + 销项材料（完整闭环）
  (731005, 'FORMAL_NOTICE', 423008, '水保整改通知 E03-D05', '巡查发现临时便道未恢复', 'VALID', 1, 1, 'demo', NULL, '2026-06-15 09:00:00'),
  (731005, 'RECTIFICATION_MATERIAL', 423009, '复绿恢复整改资料 E03-D05', '便道复绿施工完成，含影像', 'VALID', 1, 1, 'demo', 1, '2026-06-25 14:00:00'),
  (731005, 'REVIEW_OPINION', 423010, '复查意见 E03-D05', '复查通过，植被恢复达标', 'VALID', 1, 1, 'demo', NULL, '2026-06-28 16:00:00'),
  (731005, 'CLOSURE_DOCUMENT', 423011, '等价销项确认 E03-D05', '水保销项确认：确认人王主任，确认依据现场复查记录，确认意见整改有效可销项', 'VALID', 1, 1, 'demo', NULL, '2026-07-01 15:00:00'),

  -- D06：通知
  (731006, 'FORMAL_NOTICE', 423012, '水保整改通知 E03-D06', '巡查发现临时用地复垦问题', 'VALID', 1, 1, 'demo', NULL, '2026-07-01 09:00:00'),

  -- D07：通知 + 上轮整改(R1) + 退回意见；本轮整改(R2)待补 → 完整度3/4
  (731007, 'FORMAL_NOTICE', 423013, '水保整改通知 E03-D07', '监理报告指出表土保护措施不达标', 'VALID', 1, 1, 'demo', NULL, '2026-06-20 09:00:00'),
  (731007, 'RECTIFICATION_MATERIAL', 423014, '表土保护上轮整改资料 E03-D07', '上轮整改完成，含施工影像', 'VALID', 0, 1, 'demo', 1, '2026-07-08 14:00:00'),
  (731007, 'REVIEW_OPINION', 423015, '复查退回意见 E03-D07', '退回原因：表土剥离厚度仍不满足设计要求，需重新施工', 'VALID', 1, 1, 'demo', NULL, '2026-07-10 16:00:00');

-- --------------------------------------------------------------------------
-- 8. GIS F：gis_feature_business_relation
-- relation_type = 'E03_WATER_ISSUE'（不复用 E02 的 environment_problem）
-- 挂已有本体要素，不修改几何
-- --------------------------------------------------------------------------
*/

INSERT INTO e_case_evidence
  (case_id, evidence_role, document_id, validity_status, is_current, is_demo,
   data_nature, rectification_round_id, created_at)
VALUES
  (731001, 'FORMAL_NOTICE', 423001, 'VALID', 1, 1, 'demo', NULL, '2026-07-02 09:00:00'),
  (731002, 'FORMAL_NOTICE', 423002, 'VALID', 1, 1, 'demo', NULL, '2026-07-05 09:00:00'),
  (731003, 'FORMAL_NOTICE', 423003, 'VALID', 1, 1, 'demo', NULL, '2026-06-28 09:00:00'),
  (731003, 'RECTIFICATION_MATERIAL', 423004, 'VALID', 1, 1, 'demo', 1, '2026-07-15 14:00:00'),
  (731004, 'FORMAL_NOTICE', 423005, 'VALID', 1, 1, 'demo', NULL, '2026-06-26 09:00:00'),
  (731004, 'RECTIFICATION_MATERIAL', 423006, 'VALID', 1, 1, 'demo', 1, '2026-07-10 14:00:00'),
  (731004, 'REVIEW_OPINION', 423007, 'VALID', 1, 1, 'demo', NULL, '2026-07-12 16:00:00'),
  (731005, 'FORMAL_NOTICE', 423008, 'VALID', 1, 1, 'demo', NULL, '2026-06-15 09:00:00'),
  (731005, 'RECTIFICATION_MATERIAL', 423009, 'VALID', 1, 1, 'demo', 1, '2026-06-25 14:00:00'),
  (731005, 'REVIEW_OPINION', 423010, 'VALID', 1, 1, 'demo', NULL, '2026-06-28 16:00:00'),
  (731005, 'CLOSURE_DOCUMENT', 423011, 'VALID', 1, 1, 'demo', NULL, '2026-07-01 15:00:00'),
  (731006, 'FORMAL_NOTICE', 423012, 'VALID', 1, 1, 'demo', NULL, '2026-07-01 09:00:00'),
  (731007, 'FORMAL_NOTICE', 423013, 'VALID', 1, 1, 'demo', NULL, '2026-06-20 09:00:00'),
  (731007, 'RECTIFICATION_MATERIAL', 423014, 'VALID', 0, 1, 'demo', 1, '2026-07-08 14:00:00'),
  (731007, 'REVIEW_OPINION', 423015, 'VALID', 1, 1, 'demo', NULL, '2026-07-10 16:00:00');

INSERT INTO gis_feature_business_relation
  (project_id, feature_id, relation_type, relation_code, relation_name, relation_status, risk_level, source_table, source_id, summary)
VALUES
  ('LUOYI-ESG', 'waste-1-1',   'E03_WATER_ISSUE', 'E03-D01', '弃渣场挡墙未按设计施工', 'RECTIFYING', 2, 'water_protection_issue', '711001', '标段一弃渣场挡墙整改中'),
  ('LUOYI-ESG', 'water-2-1',   'E03_WATER_ISSUE', 'E03-D02', '截排水沟断面不足',       'RECTIFYING', 3, 'water_protection_issue', '711002', '标段三截排水沟整改中，已逾期'),
  ('LUOYI-ESG', 'slope-1-1',   'E03_WATER_ISSUE', 'E03-D03', '边坡防护措施不到位',     'PENDING_REVIEW', 2, 'water_protection_issue', '711003', '标段一边坡防护待复查'),
  ('LUOYI-ESG', 'eco-1-1',     'E03_WATER_ISSUE', 'E03-D04', '水土流失防治措施薄弱',   'PENDING_CLOSURE', 2, 'water_protection_issue', '711004', '标段二水土流失防治待销项'),
  ('LUOYI-ESG', 'eco-1-1',     'E03_WATER_ISSUE', 'E03-D05', '临时便道恢复',           'CLOSED', 1, 'water_protection_issue', '711005', '生态敏感区临时便道已闭环'),
  ('LUOYI-ESG', 'section-2-1', 'E03_WATER_ISSUE', 'E03-D06', '临时用地复垦（已合并）', 'MERGED', 1, 'water_protection_issue', '711006', '标段二临时用地已合并'),
  ('LUOYI-ESG', 'slope-2-1',   'E03_WATER_ISSUE', 'E03-D07', '表土保护措施不到位',     'RECTIFYING', 2, 'water_protection_issue', '711007', '标段二表土保护退回后整改中');
