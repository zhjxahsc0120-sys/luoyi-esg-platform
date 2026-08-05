-- 罗宜高速 ESG 数字化管理平台
-- Demo 初始化数据 V0.1
-- 用途：演示验证；不复制、不初始化 mdm_* 主数据；引用项目 1001、标段 2001/2002、工点 3001/3002 的现有主数据。
-- 可重复执行：使用 INSERT ... ON DUPLICATE KEY UPDATE。

SET NAMES utf8mb4;
SET time_zone = '+08:00';

-- ==================== E02 水土保持 ====================
INSERT INTO biz_soil_disposal_site
(id,project_id,section_id,work_point_id,object_code,object_name,location_desc,approved_flag,capacity_m3,disposal_status,control_measure,measure_rate,risk_status,responsible_org_id,source_doc_ref)
VALUES
(21001,1001,2001,3001,'E02-SITE-001','K12+800 弃土场','K12+800 左侧临时弃土场',1,18000,'IN_USE','截排水沟、拦挡和苫盖已落实',100.00,'NORMAL',4001,'DEMO-DOC-E02-001'),
(21002,1001,2002,3002,'E02-SITE-002','K18+200 弃渣场','K18+200 右侧弃渣场',1,12000,'RECTIFYING','边坡绿化待复核',65.00,'MEDIUM',4002,'DEMO-DOC-E02-002')
ON DUPLICATE KEY UPDATE object_name=VALUES(object_name), disposal_status=VALUES(disposal_status), measure_rate=VALUES(measure_rate), risk_status=VALUES(risk_status);

INSERT INTO biz_temporary_land_use
(id,project_id,section_id,work_point_id,object_code,object_name,land_type,area_mu,approval_status,restore_status,measure_rate,risk_status,responsible_org_id,source_doc_ref)
VALUES
(21101,1001,2001,3001,'E02-LAND-001','一工区施工便道临时用地','施工便道',12.50,'APPROVED','RESTORED',100.00,'NORMAL',4001,'DEMO-DOC-E02-003'),
(21102,1001,2002,3002,'E02-LAND-002','二工区拌合站临时用地','拌合站',18.00,'APPROVED','PENDING',50.00,'MEDIUM',4002,'DEMO-DOC-E02-004')
ON DUPLICATE KEY UPDATE restore_status=VALUES(restore_status), measure_rate=VALUES(measure_rate), risk_status=VALUES(risk_status);

INSERT INTO biz_topsoil_stripping
(id,project_id,section_id,work_point_id,object_code,object_name,planned_area_mu,completed_area_mu,completion_rate,storage_measure,current_status,risk_status,responsible_org_id,source_doc_ref)
VALUES
(21201,1001,2001,3001,'E02-TOP-001','一工区路基表土剥离',30.00,30.00,100.00,'集中堆存并覆盖','COMPLETED','NORMAL',4001,'DEMO-DOC-E02-005'),
(21202,1001,2002,3002,'E02-TOP-002','二工区互通区表土剥离',24.00,18.00,75.00,'堆存区排水措施待补强','IN_PROGRESS','MEDIUM',4002,'DEMO-DOC-E02-006')
ON DUPLICATE KEY UPDATE completion_rate=VALUES(completion_rate), current_status=VALUES(current_status), risk_status=VALUES(risk_status);

INSERT INTO biz_construction_slope
(id,project_id,section_id,work_point_id,object_code,object_name,slope_type,chainage,greening_rate,stability_status,protection_measure,risk_status,responsible_org_id,source_doc_ref)
VALUES
(21301,1001,2001,3001,'E02-SLOPE-001','K10+600 路堑边坡','路堑边坡','K10+600',92.00,'STABLE','挂网喷播与截水沟','NORMAL',4001,'DEMO-DOC-E02-007'),
(21302,1001,2002,3002,'E02-SLOPE-002','K17+300 高边坡','高边坡','K17+300',68.00,'REVIEWING','锚杆框架梁，待专项复核','MEDIUM',4002,'DEMO-DOC-E02-008')
ON DUPLICATE KEY UPDATE greening_rate=VALUES(greening_rate), stability_status=VALUES(stability_status), risk_status=VALUES(risk_status);

-- ==================== E03 生态保护 ====================
INSERT INTO biz_ecological_sensitive_area
(id,project_id,section_id,object_code,object_name,sensitive_type,location_desc,area_mu,protection_level,identification_status,monitoring_status,protection_measure,risk_status,responsible_org_id,source_doc_ref)
VALUES
(22001,1001,2001,'E03-AREA-001','白水河饮用水水源保护区','水源保护区','K8+500 至 K9+200',35.00,'重点','CONFIRMED','MONITORING','设置隔离带，雨污分流，月度巡查','NORMAL',4001,'DEMO-DOC-E03-001'),
(22002,1001,2002,'E03-AREA-002','南山林地生态敏感区','林地','K20+100 附近',48.00,'一般','CONFIRMED','RECTIFYING','施工边界标识待补充','MEDIUM',4002,'DEMO-DOC-E03-002')
ON DUPLICATE KEY UPDATE monitoring_status=VALUES(monitoring_status), protection_measure=VALUES(protection_measure), risk_status=VALUES(risk_status);

INSERT INTO biz_ecological_protection_object
(id,project_id,section_id,object_code,object_name,object_type,importance_level,location_desc,identification_status,inspection_status,protection_measure,risk_status,responsible_org_id,source_doc_ref)
VALUES
(22101,1001,2001,'E03-OBJ-001','白水河鱼类栖息地','水生生物','重点','K8+800 河段','CONFIRMED','COMPLETED','避让施工、设置沉淀池','NORMAL',4001,'DEMO-DOC-E03-003'),
(22102,1001,2002,'E03-OBJ-002','南山古树群','古树名木','重点','K20+300 林地','CONFIRMED','PENDING','保护范围标识待复核','MEDIUM',4002,'DEMO-DOC-E03-004')
ON DUPLICATE KEY UPDATE inspection_status=VALUES(inspection_status), protection_measure=VALUES(protection_measure), risk_status=VALUES(risk_status);

-- ==================== E04 文物保护 ====================
INSERT INTO biz_cultural_relic_object
(id,project_id,section_id,relic_code,relic_name,relic_type,protection_level,location_desc,protection_scope,impact_analysis,protection_measure,survey_status,measure_rate,responsible_org_id,risk_status,source_doc_ref)
VALUES
(23001,1001,2002,'E04-RELIC-001','青石桥遗址','古遗址','县级文保','K18+950 西侧 120 米','以遗址中心向外 50 米','当前线路不穿越本体，施工运输需避让','设置警示标识、专人巡查、施工前复核','COMPLETED',100.00,4002,'NORMAL','DEMO-DOC-E04-001')
ON DUPLICATE KEY UPDATE survey_status=VALUES(survey_status), measure_rate=VALUES(measure_rate), risk_status=VALUES(risk_status);

-- ==================== S03 工资支付 ====================
INSERT INTO biz_worker_payment_summary
(id,project_id,section_id,period_start,period_end,responsible_org_id,worker_count,payable_amount,paid_amount,payment_rate,payment_status,overdue_amount,dispute_count,risk_status,source_doc_ref)
VALUES
(24001,1001,2001,'2026-07-01','2026-07-31',4001,168,1268000.00,1268000.00,100.00,'PAID',0.00,0,'NORMAL','DEMO-DOC-S03-001'),
(24002,1001,2002,'2026-07-01','2026-07-31',4002,152,1145000.00,1127800.00,98.50,'PARTIAL',17200.00,1,'LOW','DEMO-DOC-S03-002')
ON DUPLICATE KEY UPDATE paid_amount=VALUES(paid_amount), payment_rate=VALUES(payment_rate), payment_status=VALUES(payment_status), risk_status=VALUES(risk_status);

-- ==================== G02 夜间施工 ====================
INSERT INTO biz_night_construction_record
(id,project_id,section_id,work_point_id,record_code,construction_date,start_time,end_time,permit_id,permit_status,approval_status,noise_measure,responsible_org_id,risk_status,source_doc_ref)
VALUES
(25001,1001,2001,3001,'G02-NIGHT-001','2026-08-02','2026-08-02 22:00:00','2026-08-03 02:00:00',51001,'VALID','APPROVED','使用低噪设备并布置噪声监测点',4001,'NORMAL','DEMO-DOC-G02-001'),
(25002,1001,2002,3002,'G02-NIGHT-002','2026-08-03','2026-08-03 23:00:00','2026-08-04 03:00:00',51002,'EXPIRING','PENDING','已提交续期，等待审批',4002,'HIGH','DEMO-DOC-G02-002')
ON DUPLICATE KEY UPDATE permit_status=VALUES(permit_status), approval_status=VALUES(approval_status), risk_status=VALUES(risk_status);

-- ==================== G03 设计变更 ====================
INSERT INTO biz_design_change
(id,project_id,section_id,work_point_id,change_code,change_type,change_name,location_desc,change_reason,apply_date,approve_status,approve_date,implementation_status,attachment_status,responsible_org_id,risk_status,source_doc_ref)
VALUES
(26001,1001,2001,3001,'G03-CHANGE-001','一般变更','K12 段排水沟断面优化','K12+300','现场排水条件变化','2026-07-16','APPROVED','2026-07-20','IMPLEMENTED','COMPLETE',4001,'NORMAL','DEMO-DOC-G03-001'),
(26002,1001,2002,3002,'G03-CHANGE-002','重大变更','K18 段边坡防护方案调整','K18+100','地质条件与原勘察不一致','2026-07-28','PENDING',NULL,'NOT_STARTED','MISSING',4002,'MEDIUM','DEMO-DOC-G03-002'),
(26003,1001,2002,3002,'G03-CHANGE-003','一般变更','互通匝道标高微调','K19+400','施工组织优化','2026-07-30','APPROVED','2026-08-01','IN_PROGRESS','COMPLETE',4002,'LOW','DEMO-DOC-G03-003'),
(26004,1001,2001,3001,'G03-CHANGE-004','一般变更','临建用电方案补充','一工区临建区','临时设施调整','2026-08-01','APPROVED','2026-08-02','IMPLEMENTED','COMPLETE',4001,'NORMAL','DEMO-DOC-G03-004')
ON DUPLICATE KEY UPDATE approve_status=VALUES(approve_status), implementation_status=VALUES(implementation_status), attachment_status=VALUES(attachment_status), risk_status=VALUES(risk_status);

-- ==================== G04 内控廉洁 ====================
INSERT INTO biz_internal_control_issue
(id,project_id,section_id,issue_code,issue_type,issue_level,issue_description,found_at,responsible_org_id,current_status,deadline,closed_at,recurrence_flag,evidence_status,risk_status,source_doc_ref)
VALUES
(27001,1001,2001,'G04-CTRL-001','采购比选留痕','一般','供应商比选记录缺少经办人签字','2026-07-22 10:00:00',4001,'CLOSED','2026-07-29','2026-07-28',0,'COMPLETE','NORMAL','DEMO-DOC-G04-001'),
(27002,1001,2002,'G04-CTRL-002','廉洁风险排查','较高','分包合同廉洁承诺附件缺失','2026-08-01 14:00:00',4002,'OPEN','2026-08-08',NULL,0,'MISSING','HIGH','DEMO-DOC-G04-002')
ON DUPLICATE KEY UPDATE current_status=VALUES(current_status), evidence_status=VALUES(evidence_status), risk_status=VALUES(risk_status);

-- ==================== 风险规则 ====================
INSERT INTO cfg_warning_rule
(id,rule_code,kpi_key,domain_code,rule_name,trigger_condition_json,warning_level,version_no,enabled)
VALUES
(31001,'RULE-E02-MEASURE','E02','E','水土保持措施未完成','{"field":"measure_rate","operator":"<","value":80}','MEDIUM','DEMO-0.1',1),
(31002,'RULE-E03-MONITOR','E03','E','生态敏感对象未完成巡查','{"field":"inspection_status","operator":"in","value":["PENDING","RECTIFYING"]}','MEDIUM','DEMO-0.1',1),
(31003,'RULE-E04-SURVEY','E04','E','文物调查未完成或保护措施不足','{"field":"survey_status","operator":"!=","value":"COMPLETED"}','HIGH','DEMO-0.1',1),
(31004,'RULE-S03-PAYMENT','S03','S','工资支付存在逾期金额','{"field":"overdue_amount","operator":">","value":0}','LOW','DEMO-0.1',1),
(31005,'RULE-G02-NIGHT','G02','G','夜间施工许可临期或审批未完成','{"any":[{"field":"permit_status","operator":"=","value":"EXPIRING"},{"field":"approval_status","operator":"!=","value":"APPROVED"}]}','HIGH','DEMO-0.1',1),
(31006,'RULE-G03-CHANGE','G03','G','设计变更待审批或附件缺失','{"any":[{"field":"approve_status","operator":"=","value":"PENDING"},{"field":"attachment_status","operator":"=","value":"MISSING"}]}','MEDIUM','DEMO-0.1',1),
(31007,'RULE-G04-CONTROL','G04','G','内控廉洁问题未关闭','{"field":"current_status","operator":"!=","value":"CLOSED"}','HIGH','DEMO-0.1',1)
ON DUPLICATE KEY UPDATE trigger_condition_json=VALUES(trigger_condition_json), warning_level=VALUES(warning_level), enabled=VALUES(enabled);

-- ==================== 风险预警与处置 ====================
INSERT INTO biz_risk_warning
(id,warning_code,project_id,domain_code,kpi_key,object_type,object_id,object_name_snapshot,warning_level,warning_reason,trigger_time,responsible_org_id,responsible_unit,status,source_rule_id)
VALUES
(32001,'WARN-E02-001',1001,'E','E02','biz_soil_disposal_site',21002,'K18+200 弃渣场','MEDIUM','边坡绿化与复核措施落实率 65%，低于 Demo 阈值 80%。','2026-08-04 09:00:00',4002,'二工区施工单位','IN_PROGRESS',31001),
(32002,'WARN-E03-001',1001,'E','E03','biz_ecological_protection_object',22102,'南山古树群','MEDIUM','生态保护对象巡查状态为待复核。','2026-08-04 09:05:00',4002,'二工区施工单位','OPEN',31002),
(32003,'WARN-G02-001',1001,'G','G02','biz_night_construction_record',25002,'2026-08-03 夜间施工记录','HIGH','夜间施工许可临期且续期审批未完成。','2026-08-04 09:10:00',4002,'二工区施工单位','OPEN',31005),
(32004,'WARN-G03-001',1001,'G','G03','biz_design_change',26002,'K18 段边坡防护方案调整','MEDIUM','设计变更尚未完成审批，附件状态为缺失。','2026-08-04 09:15:00',4002,'二工区施工单位','OPEN',31006),
(32005,'WARN-G04-001',1001,'G','G04','biz_internal_control_issue',27002,'分包合同廉洁承诺附件缺失','HIGH','内控廉洁问题未关闭且证据附件缺失。','2026-08-04 09:20:00',4002,'二工区施工单位','OPEN',31007),
(32006,'WARN-S03-001',1001,'S','S03','biz_worker_payment_summary',24002,'二工区 2026年7月工资支付','LOW','存在 17,200 元待支付金额及 1 起劳资争议。','2026-08-04 09:25:00',4002,'二工区施工单位','IN_PROGRESS',31004)
ON DUPLICATE KEY UPDATE warning_level=VALUES(warning_level), warning_reason=VALUES(warning_reason), status=VALUES(status);

INSERT INTO biz_risk_disposal
(id,warning_id,project_id,responsible_unit,action_content,handler,disposal_status,disposal_time,close_time,close_evidence)
VALUES
(33001,32001,1001,'二工区施工单位','补充边坡绿化并完成现场复核','张工','IN_PROGRESS','2026-08-04 10:00:00',NULL,NULL),
(33002,32003,1001,'二工区施工单位','完成夜间施工许可续期并补充审批单','李工','PENDING',NULL,NULL,NULL),
(33003,32005,1001,'二工区施工单位','补齐廉洁承诺附件并复核分包合同','王工','PENDING',NULL,NULL,NULL),
(33004,32006,1001,'二工区施工单位','补发工资差额并回访劳务人员','赵工','IN_PROGRESS','2026-08-04 11:00:00',NULL,NULL)
ON DUPLICATE KEY UPDATE disposal_status=VALUES(disposal_status), action_content=VALUES(action_content);

-- ==================== Demo 12 项指标结果 ====================
INSERT INTO esg_demo_indicator_result
(id,project_id,period_end,kpi_key,kpi_name,domain_code,value_decimal,value_text,unit,hint,risk_level,source_summary,rule_version,result_status,calculated_at,published_at)
VALUES
(40001,1001,'2026-08-04','E01','环境监测与污染控制','E',2,NULL,'次','12 个监测结果中有 2 次超标，涉及 1 个监测点。','HIGH','复用 biz_env_monitor_point/batch/result；Demo 展示结果','DEMO-0.1','PUBLISHED','2026-08-04 08:00:00','2026-08-04 08:30:00'),
(40002,1001,'2026-08-04','E02','水土保持与临时用地','E',75.00,NULL,'%','4 类对象中主要措施平均落实率 75%，2 个对象需复核。','MEDIUM','biz_soil_disposal_site/temporary_land_use/topsoil_stripping/construction_slope','DEMO-0.1','PUBLISHED','2026-08-04 08:00:00','2026-08-04 08:30:00'),
(40003,1001,'2026-08-04','E03','生态敏感区与保护对象','E',100.00,NULL,'%','2 个敏感区、2 个保护对象已完成识别；1 个对象待复核。','MEDIUM','biz_ecological_sensitive_area/ecological_protection_object','DEMO-0.1','PUBLISHED','2026-08-04 08:00:00','2026-08-04 08:30:00'),
(40004,1001,'2026-08-04','E04','文物保护','E',1.00,NULL,'处','调查已完成，识别 1 处文物对象，保护措施落实率 100%。','NORMAL','biz_cultural_relic_object；不是碳排放指标','DEMO-0.1','PUBLISHED','2026-08-04 08:00:00','2026-08-04 08:30:00'),
(40005,1001,'2026-08-04','S01','安全生产','S',216.00,NULL,'天','连续安全生产 216 天，当前无已确认事故。','NORMAL','复用 biz_safety_event/biz_safety_daily_status','DEMO-0.1','PUBLISHED','2026-08-04 08:00:00','2026-08-04 08:30:00'),
(40006,1001,'2026-08-04','S02','安全风险管控','S',66.70,NULL,'%','6 个重点风险点中 4 个处于有效管控状态。','MEDIUM','复用 biz_safety_risk_point','DEMO-0.1','PUBLISHED','2026-08-04 08:00:00','2026-08-04 08:30:00'),
(40007,1001,'2026-08-04','S03','工资支付与劳资权益','S',98.50,NULL,'%','2 个标段均已生成工资支付汇总，存在 1 起待处理争议。','LOW','biz_worker_payment_summary + biz_labor_dispute','DEMO-0.1','PUBLISHED','2026-08-04 08:00:00','2026-08-04 08:30:00'),
(40008,1001,'2026-08-04','S04','社会沟通与公众诉求','S',3.00,NULL,'件','本周期受理 3 件公众诉求，2 件已办结。','LOW','复用 biz_public_appeal','DEMO-0.1','PUBLISHED','2026-08-04 08:00:00','2026-08-04 08:30:00'),
(40009,1001,'2026-08-04','G01','项目合规审批','G',100.00,NULL,'%','当前适用审批事项均已完成。','NORMAL','复用 biz_project_approval + biz_approval_catalog','DEMO-0.1','PUBLISHED','2026-08-04 08:00:00','2026-08-04 08:30:00'),
(40010,1001,'2026-08-04','G02','许可合规','G',2.00,NULL,'项','2 条夜间施工记录中 1 条许可临期且审批待完成。','HIGH','复用 biz_permit + biz_night_construction_record','DEMO-0.1','PUBLISHED','2026-08-04 08:00:00','2026-08-04 08:30:00'),
(40011,1001,'2026-08-04','G03','设计变更管理','G',4.00,NULL,'项','4 项设计变更中 1 项待审批且附件缺失。','MEDIUM','biz_design_change；不是整改事项','DEMO-0.1','PUBLISHED','2026-08-04 08:00:00','2026-08-04 08:30:00'),
(40012,1001,'2026-08-04','G04','内控与廉洁','G',2.00,NULL,'项','2 项内控问题中 1 项未关闭且证据缺失。','HIGH','biz_internal_control_issue；不是合规资料缺失统计','DEMO-0.1','PUBLISHED','2026-08-04 08:00:00','2026-08-04 08:30:00')
ON DUPLICATE KEY UPDATE value_decimal=VALUES(value_decimal),hint=VALUES(hint),risk_level=VALUES(risk_level),source_summary=VALUES(source_summary),result_status=VALUES(result_status);

-- ==================== 指标对象明细 ====================
INSERT INTO esg_demo_indicator_detail
(id,result_id,project_id,kpi_key,object_type,object_id,object_name,metric_label,metric_value,metric_unit,status,risk_level,detail_json)
VALUES
(41001,40001,1001,'E01','biz_env_monitor_point',11001,'K12 扬尘监测点','超标次数','2','次','超标','HIGH','{"factor":"PM10","exceedRate":16.67}'),
(41002,40002,1001,'E02','biz_soil_disposal_site',21002,'K18+200 弃渣场','措施落实率','65','%','整改中','MEDIUM','{"measureRate":65,"riskStatus":"MEDIUM"}'),
(41003,40003,1001,'E03','biz_ecological_protection_object',22102,'南山古树群','巡查状态','待复核',NULL,'待复核','MEDIUM','{"inspectionStatus":"PENDING"}'),
(41004,40004,1001,'E04','biz_cultural_relic_object',23001,'青石桥遗址','文物保护摘要','objectCount=1; surveyStatus=COMPLETED; measureRate=100; riskStatus=NORMAL',NULL,'已完成','NORMAL','{"objectCount":1,"surveyStatus":"COMPLETED","measureRate":100,"riskStatus":"NORMAL"}'),
(41005,40005,1001,'S01','biz_safety_daily_status',12001,'项目整体','连续安全天数','216','天','正常','NORMAL','{"resetRule":"DEMO-S01"}'),
(41006,40006,1001,'S02','biz_safety_risk_point',13001,'K17+300 高边坡','管控状态','待复核',NULL,'需复核','MEDIUM','{"riskLevel":"MAJOR","controlStatus":"REVIEWING"}'),
(41007,40007,1001,'S03','biz_worker_payment_summary',24002,'二工区 2026年7月工资支付','支付率','98.5','%','部分支付','LOW','{"overdueAmount":17200,"disputeCount":1}'),
(41008,40008,1001,'S04','biz_public_appeal',14001,'K15 村民诉求','办理状态','已办结',NULL,'已关闭','LOW','{"receivedAt":"2026-07-30","closedAt":"2026-08-02"}'),
(41009,40009,1001,'G01','biz_project_approval',15001,'环评批复','审批状态','已完成',NULL,'已完成','NORMAL','{"required":true}'),
(41010,40010,1001,'G02','biz_night_construction_record',25002,'2026-08-03 夜间施工记录','许可状态','EXPIRING',NULL,'审批中','HIGH','{"permitId":51002,"permitStatus":"EXPIRING","approvalStatus":"PENDING"}'),
(41011,40011,1001,'G03','biz_design_change',26002,'K18 段边坡防护方案调整','变更状态','PENDING / MISSING',NULL,'待审批','MEDIUM','{"approveStatus":"PENDING","attachmentStatus":"MISSING"}'),
(41012,40012,1001,'G04','biz_internal_control_issue',27002,'分包合同廉洁承诺附件缺失','问题状态','OPEN',NULL,'未关闭','HIGH','{"issueLevel":"HIGH","evidenceStatus":"MISSING"}')
ON DUPLICATE KEY UPDATE metric_value=VALUES(metric_value),status=VALUES(status),risk_level=VALUES(risk_level),detail_json=VALUES(detail_json);
