USE luoyi_esg;
SET NAMES utf8mb4;

INSERT INTO dict_esg_module(module_code, module_name, display_order) VALUES
('E', '环境环保', 1),
('S', '社会责任', 2),
('G', '治理合规', 3)
ON DUPLICATE KEY UPDATE module_name=VALUES(module_name), display_order=VALUES(display_order);

INSERT INTO org_unit(id, org_code, org_name, parent_id, org_type) VALUES
(100, 'LYGS', '罗宜高速项目公司', NULL, 'PROJECT'),
(101, 'SAFETY_ENV', '安全环保部', 100, 'DEPARTMENT'),
(102, 'ENGINEERING', '工程管理部', 100, 'DEPARTMENT'),
(103, 'FINANCE', '财务管理部', 100, 'DEPARTMENT'),
(104, 'QUALITY', '质量管理部', 100, 'DEPARTMENT')
ON DUPLICATE KEY UPDATE org_name=VALUES(org_name), parent_id=VALUES(parent_id), org_type=VALUES(org_type);

INSERT INTO user_account(id, username, display_name, org_id, role_name) VALUES
(10001, 'project_admin', '项目管理员', 100, '上传用户'),
(10002, 'zhang_jianguo', '张建国', 101, '资料填报人'),
(10003, 'li_anquan', '李安全', 102, '审核人'),
(10004, 'wang_jia', '王佳', 103, '资料填报人'),
(10005, 'zhao_huanbao', '赵环保', 101, '审核人')
ON DUPLICATE KEY UPDATE display_name=VALUES(display_name), org_id=VALUES(org_id), role_name=VALUES(role_name);

INSERT INTO dict_document_type(id, type_code, type_name, module_code) VALUES
(1001, 'MONITOR_REPORT', '监测报告', 'E'),
(1002, 'APPROVAL_MATERIAL', '审批资料', 'G'),
(1003, 'LEDGER_RECORD', '台账记录', 'E'),
(1004, 'IMAGE_MATERIAL', '影像资料', 'E'),
(1005, 'TRAINING_RECORD', '培训记录', 'S'),
(1006, 'CARBON_ACTIVITY', '碳排放活动数据表', 'E'),
(1007, 'WATER_PROTECTION_MONTHLY', '水保监测月报', 'E'),
(1008, 'HIGH_RISK_APPROVAL', '高风险作业审批资料', 'S'),
(1009, 'SALARY_PAYMENT', '工资支付资料', 'S'),
(1010, 'TEMP_LAND_COMPLIANCE', '临时用地合规资料', 'G'),
(1011, 'NCR_RECTIFICATION', 'NCR整改关闭资料', 'G')
ON DUPLICATE KEY UPDATE type_name=VALUES(type_name), module_code=VALUES(module_code);

INSERT INTO indicator_definition
(indicator_code, group_code, indicator_name, unit, source_table, calculation_desc, display_order)
VALUES
('E01', 'E', '环境监测超标项次', '项次', 'env_monitoring_record', '统计当前周期扬尘、噪声等环境监测超标项次', 1),
('E02', 'E', '当前未闭环环保问题事项数', '项', 'env_issue_record', '统计当前未闭环环保问题', 2),
('E03', 'E', '当前未闭环水保问题事项数', '项', 'water_protection_issue', '统计当前未闭环水保问题', 3),
('E04', 'E', '碳排放强度', 'tCO₂e/万元', 'carbon_emission_activity', '统计施工阶段碳排放强度', 4),
('S01', 'S', '连续安全生产天数', '天', 'safety_production_record', '统计项目连续安全生产天数', 1),
('S02', 'S', '在管较大及以上安全风险点数', '项', 'safety_risk_point', '统计在管较大及以上安全风险点', 2),
('S03', 'S', '未办结劳务纠纷事项数', '项', 'labor_dispute_record', '统计未办结劳务纠纷', 3),
('S04', 'S', '未办结群众诉求事项数', '项', 'appeal_record', '统计未办结群众诉求', 4),
('G01', 'G', '未完成合规手续事项数', '项', 'compliance_procedure', '统计未完成合规手续', 1),
('G02', 'G', '当前临期及逾期许可事项数', '项', 'permit_record', '统计临期及逾期许可事项', 2),
('G03', 'G', '未关闭整改事项数', '项', 'rectification_record', '统计未关闭整改事项', 3),
('G04', 'G', '待补齐合规资料事项数', '项', 'compliance_material_gap', '统计待补齐合规资料', 4)
ON DUPLICATE KEY UPDATE
  indicator_name=VALUES(indicator_name),
  unit=VALUES(unit),
  source_table=VALUES(source_table),
  calculation_desc=VALUES(calculation_desc),
  display_order=VALUES(display_order);
