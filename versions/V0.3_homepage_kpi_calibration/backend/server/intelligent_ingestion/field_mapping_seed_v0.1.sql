-- 罗宜高速 ESG 智能入库字段映射样例 V0.1
-- 用途：定义 AI 抽取字段应写入哪个目标表和目标字段。

INSERT INTO ai_field_mapping_rule
(id, document_type, field_key, field_name, target_table, target_column, value_type, required, normalize_rule, enabled, created_at, updated_at)
VALUES
(1001, '通用资料', 'document_name', '资料名称', 'document_record', 'document_name', 'string', 1, NULL, 1, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
(1002, '通用资料', 'document_type', '资料类型', 'document_record', 'document_type', 'string', 1, 'match_document_type_dictionary', 1, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
(1003, '通用资料', 'esg_module', 'ESG模块', 'document_record', 'module_code', 'string', 1, 'E/S/G_normalize', 1, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
(1004, '通用资料', 'period', '资料周期', 'document_record', 'period_value', 'string', 1, 'period_normalize', 1, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
(1005, '通用资料', 'responsible_unit', '责任单位', 'document_record', 'responsible_unit', 'string', 0, 'org_name_normalize', 1, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
(1006, '通用资料', 'valid_start_date', '有效期开始', 'document_record', 'valid_start_date', 'date', 0, 'date_normalize', 1, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
(1007, '通用资料', 'valid_end_date', '有效期结束', 'document_record', 'valid_end_date', 'date', 0, 'date_normalize', 1, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),

(2001, '水保监测月报', 'monitor_date', '监测日期', 'env_monitoring_record', 'monitor_date', 'date', 0, 'date_normalize', 1, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
(2002, '水保监测月报', 'dust_exceed_count', '扬尘超标次数', 'env_monitoring_record', 'dust_exceed_count', 'number', 0, 'number_normalize', 1, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
(2003, '水保监测月报', 'noise_exceed_count', '噪声超标次数', 'env_monitoring_record', 'noise_exceed_count', 'number', 0, 'number_normalize', 1, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
(2004, '水保监测月报', 'water_protection_issue_count', '水保问题数量', 'env_issue_record', 'issue_count', 'number', 0, 'number_normalize', 1, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),

(3001, '碳排放活动数据表', 'diesel_usage', '柴油用量', 'carbon_emission_activity', 'diesel_usage', 'number', 0, 'number_with_unit_normalize', 1, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
(3002, '碳排放活动数据表', 'electricity_usage', '电力消耗', 'carbon_emission_activity', 'electricity_usage', 'number', 0, 'number_with_unit_normalize', 1, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
(3003, '碳排放活动数据表', 'material_usage', '材料用量', 'carbon_material_usage', 'material_usage', 'number', 0, 'number_with_unit_normalize', 1, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
(3004, '碳排放活动数据表', 'carbon_emission', '碳排放量', 'carbon_emission_activity', 'carbon_emission', 'number', 0, 'number_with_unit_normalize', 1, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),

(4001, '高风险作业审批资料', 'risk_level', '风险等级', 'safety_risk_point', 'risk_level', 'string', 0, 'risk_level_dictionary', 1, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
(4002, '高风险作业审批资料', 'work_location', '作业位置', 'safety_risk_point', 'location', 'string', 0, NULL, 1, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
(4003, '高风险作业审批资料', 'control_measure', '管控措施', 'safety_risk_point', 'control_measure', 'string', 0, NULL, 1, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),

(5001, '工资支付资料', 'worker_count', '支付人数', 'salary_payment_record', 'worker_count', 'number', 0, 'number_normalize', 1, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
(5002, '工资支付资料', 'payment_amount', '支付金额', 'salary_payment_record', 'payment_amount', 'number', 0, 'money_normalize', 1, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
(5003, '工资支付资料', 'payment_month', '支付月份', 'salary_payment_record', 'payment_month', 'string', 0, 'period_normalize', 1, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),

(6001, '临时用地合规资料', 'permit_name', '许可名称', 'permit_record', 'permit_name', 'string', 0, NULL, 1, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
(6002, '临时用地合规资料', 'permit_no', '许可编号', 'permit_record', 'permit_no', 'string', 0, NULL, 1, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
(6003, '临时用地合规资料', 'permit_expire_date', '许可到期日', 'permit_record', 'expire_date', 'date', 0, 'date_normalize', 1, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),

(7001, 'NCR整改关闭资料', 'rectification_item', '整改事项', 'rectification_record', 'item_name', 'string', 0, NULL, 1, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
(7002, 'NCR整改关闭资料', 'rectification_status', '整改状态', 'rectification_record', 'status', 'string', 0, 'rectification_status_dictionary', 1, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
(7003, 'NCR整改关闭资料', 'closed_date', '关闭日期', 'rectification_record', 'closed_date', 'date', 0, 'date_normalize', 1, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP);
