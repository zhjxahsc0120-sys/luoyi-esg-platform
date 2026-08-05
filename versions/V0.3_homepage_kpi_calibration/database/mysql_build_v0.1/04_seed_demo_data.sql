USE luoyi_esg;
SET NAMES utf8mb4;

INSERT INTO upload_task
(id, name, module_code, module_name, cycle, cycle_type, deadline, progress_current, progress_total, status, next_step, assignee_id, assignee_name, assignee_dept, priority_code)
VALUES
('t1', '2026年7月水保监测月报', 'E', '环境环保', '2026-07（月度）', '月度', '2026-08-10 18:00:00', 5, 7, '待上传', '开始办理', 10002, '张建国', '安全环保部', 'HIGH'),
('t2', '高风险作业审批资料', 'S', '社会责任', '2026-07（月度）', '月度', '2026-08-11 18:00:00', 3, 6, '待补正', '继续补正', 10003, '李安全', '工程管理部', 'HIGH'),
('t3', '施工人员工资支付资料', 'S', '社会责任', '2026-06（月度）', '月度', '2026-07-30 18:00:00', 4, 5, '待提交', '提交', 10004, '王佳', '财务管理部', 'URGENT'),
('t4', 'NCR整改关闭资料', 'G', '治理合规', '2026-07（月度）', '月度', '2026-08-12 18:00:00', 2, 4, '待补正', '开始办理', NULL, '陈质量', '工程管理部', 'HIGH'),
('t5', '临时用地合规资料', 'G', '治理合规', '2026-07（一次性）', '一次性', '2026-08-15 18:00:00', 1, 3, '待上传', '开始办理', NULL, '刘工', '工程管理部', 'NORMAL'),
('t6', '碳排放活动数据填报', 'E', '环境环保', '2026-Q2（季度）', '季度', '2026-08-20 18:00:00', 6, 6, '待提交', '提交', 10005, '赵环保', '安全环保部', 'NORMAL'),
('t7', '安全教育培训记录', 'S', '社会责任', '2026-07（月度）', '月度', '2026-08-18 18:00:00', 0, 3, '待上传', '开始办理', 10003, '李安全', '安全环保部', 'NORMAL'),
('t8', '环保设施运行台账', 'E', '环境环保', '2026-07（月度）', '月度', '2026-08-25 18:00:00', 2, 4, '待补正', '继续补正', NULL, '周丽娟', '安全环保部', 'NORMAL'),
('t9', '质量体系内审报告', 'G', '治理合规', '2026-08（月度）', '月度', '2026-09-01 18:00:00', 8, 8, '审核中', '查看进度', NULL, '吴浩', '工程管理部', 'NORMAL'),
('t10', '职业健康体检资料', 'S', '社会责任', '2026年度（年度）', '年度', '2026-09-10 18:00:00', 10, 10, '已完成', '查看详情', NULL, '郑晓燕', '安全环保部', 'NORMAL'),
('t11', '汛期水保专项检查记录', 'E', '环境环保', '2026-07（一次性）', '一次性', '2026-08-05 18:00:00', 3, 3, '已完成', '查看详情', 10002, '张建国', '安全环保部', 'NORMAL'),
('t12', '农民工工资保证金缴纳凭证', 'S', '社会责任', '2026-Q2（季度）', '季度', '2026-07-15 18:00:00', 2, 2, '已归档', '查看档案', 10004, '王佳', '财务管理部', 'NORMAL')
ON DUPLICATE KEY UPDATE status=VALUES(status), progress_current=VALUES(progress_current), progress_total=VALUES(progress_total);

INSERT INTO upload_task_requirement
(id, task_id, name, required, format_rule, status, template_available, sequence_no)
VALUES
('td1', 't1', '水保监测实施方案', 1, 'PDF，≤50MB', '已关联', 1, 1),
('td2', 't1', '本月水保监测记录', 1, 'Excel，≤20MB', '已关联', 1, 2),
('td3', 't1', '水保监测月报', 1, 'PDF，≤50MB', '已关联', 1, 3),
('td4', 't1', '扰动面积变化表', 1, 'Excel，≤20MB', '已关联', 1, 4),
('td5', 't1', '弃渣场巡查记录', 1, 'PDF，≤20MB', '格式异常', 1, 5),
('td6', 't1', '复绿恢复统计表', 0, 'Excel，≤20MB', '已关联', 1, 6),
('td7', 't1', '审核确认单', 1, 'PDF，≤10MB', '缺失', 1, 7)
ON DUPLICATE KEY UPDATE status=VALUES(status);

INSERT INTO task_candidate_document
(id, task_id, name, cycle, unit_name, link_count, match_rate, sequence_no)
VALUES
('c1', 't1', '弃渣场巡查记录_2026-07.pdf', '2026-07', '水保监测单位', 2, 96, 1),
('c2', 't1', '水保监测记录_2026-07.xlsx', '2026-07', '水保监测单位', 1, 92, 2),
('c3', 't1', '水保监测实施方案_2026.pdf', '2026年度', '水保监测单位', 3, 88, 3),
('c4', 't1', '复绿恢复统计表_2026-07.xlsx', '2026-07', '工程管理部', 0, 85, 4),
('c5', 't1', '扰动面积变化表_2026-07.xlsx', '2026-07', '工程管理部', 1, 82, 5)
ON DUPLICATE KEY UPDATE match_rate=VALUES(match_rate);

INSERT INTO task_review_timeline
(id, task_id, event_time, action_text, sequence_no)
VALUES
('rt1', 't1', '2026-08-05 18:00:00', '提交上传（张建国 提交任务）', 1),
('rt2', 't1', '2026-08-05 18:05:00', '完整性校验（系统校验通过，共5/7项资料完整）', 2)
ON DUPLICATE KEY UPDATE action_text=VALUES(action_text);

INSERT INTO workspace_summary
(id, current_todo, pending_upload, pending_correction, pending_submit, under_review, due_soon, completed)
VALUES
(1, 27, 12, 3, 5, 3, 4, 36)
ON DUPLICATE KEY UPDATE
  current_todo=VALUES(current_todo),
  pending_upload=VALUES(pending_upload),
  pending_correction=VALUES(pending_correction),
  pending_submit=VALUES(pending_submit),
  under_review=VALUES(under_review),
  due_soon=VALUES(due_soon),
  completed=VALUES(completed);

INSERT INTO file_asset
(id, file_code, original_name, file_ext, mime_type, file_size, storage_path, storage_bucket, sha256_hash, upload_source, uploader_id, uploader_name, upload_time, duplicate_status, parse_status)
VALUES
(900001, 'FILE-202607-0001', '水保监测记录_2026-07.xlsx', 'xlsx', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', 1310720, '/demo/水保监测记录_2026-07.xlsx', 'local', '8B2F-DEMO-HASH-0001', 'USER_UPLOAD', 10001, '项目管理员', '2026-07-13 10:00:00', 'UNIQUE', 'WAIT_CONFIRM'),
(900002, 'FILE-202607-0002', '弃渣场巡查记录_2026-07.pdf', 'pdf', 'application/pdf', 2285896, '/demo/弃渣场巡查记录_2026-07.pdf', 'local', '8B2F-DEMO-HASH-0002', 'USER_UPLOAD', 10001, '项目管理员', '2026-07-13 10:01:00', 'SIMILAR', 'RUNNING'),
(900003, 'FILE-202607-0003', '安全培训签到表.jpg', 'jpg', 'image/jpeg', 1027604, '/demo/安全培训签到表.jpg', 'local', '8B2F-DEMO-HASH-0003', 'USER_UPLOAD', 10001, '项目管理员', '2026-07-13 10:02:00', 'UNIQUE', 'PENDING')
ON DUPLICATE KEY UPDATE parse_status=VALUES(parse_status);

INSERT INTO ai_parse_job
(id, job_code, file_id, job_status, parse_engine, model_name, rule_version, started_at, finished_at, duration_ms, confidence, raw_result_json)
VALUES
(910001, 'PARSE-202607-0001', 900001, 'SUCCESS', 'ESG智能解析器', 'gpt-esg-parser-demo', 'V0.1', '2026-07-13 10:10:00', '2026-07-13 10:10:08', 8000, 100.00, JSON_OBJECT('document_type','水保监测月报','period','2026-07','module','E')),
(910002, 'PARSE-202607-0002', 900002, 'RUNNING', 'ESG智能解析器', 'gpt-esg-parser-demo', 'V0.1', '2026-07-13 10:11:00', NULL, NULL, 96.00, JSON_OBJECT('document_type','巡查记录','period','2026-07','module','E')),
(910003, 'PARSE-202607-0003', 900003, 'WAIT_CONFIRM', 'ESG智能解析器', 'gpt-esg-parser-demo', 'V0.1', NULL, NULL, NULL, 0.00, JSON_OBJECT('document_type','培训记录','period','2026-07','module','S'))
ON DUPLICATE KEY UPDATE job_status=VALUES(job_status), confidence=VALUES(confidence);

INSERT INTO ai_parse_field_result
(id, parse_job_id, field_key, field_name, field_value, normalized_value, value_type, confidence, confirm_status)
VALUES
(911001, 910001, 'document_name', '资料名称', '水保监测记录_2026-07.xlsx', '水保监测记录_2026-07.xlsx', 'string', 98.00, 'PENDING'),
(911002, 910001, 'document_type', '资料类型', '水保监测月报', '水保监测月报', 'string', 97.50, 'PENDING'),
(911003, 910001, 'esg_module', 'ESG模块', '环境环保', 'E', 'string', 99.00, 'PENDING'),
(911004, 910001, 'period', '资料周期', '2026年7月', '2026-07', 'string', 96.00, 'PENDING'),
(911005, 910001, 'responsible_unit', '责任单位', '安全环保部', '安全环保部', 'string', 93.00, 'PENDING')
ON DUPLICATE KEY UPDATE normalized_value=VALUES(normalized_value), confidence=VALUES(confidence);

INSERT INTO task_match_candidate
(id, parse_job_id, file_id, document_id, task_id, task_name, module_code, match_score, match_reason, reuse_count, candidate_status)
VALUES
(920001, 910001, 900001, NULL, 't1', '2026年7月水保监测月报', 'E', 96.00, '资料类型、周期和ESG模块均匹配', 1, 'PENDING')
ON DUPLICATE KEY UPDATE match_score=VALUES(match_score), candidate_status=VALUES(candidate_status);

INSERT INTO document_record
(id, document_code, document_name, document_type, module_code, period_value, version_no, source_name, relation_count, validity_status, document_status, confirm_status, file_id, parse_job_id, responsible_unit, uploaded_at)
VALUES
(930001, 'DOC-202607-0001', '弃渣场巡查记录_2026-07.pdf', '监测报告', 'E', '2026-07', 'V2', 'ESG智能入库', 3, '有效', 'ACTIVE', 'CONFIRMED', 900001, 910001, '安全环保部', '2026-08-10 18:00:00'),
(930002, 'DOC-202607-0002', '2026年7月水保监测月报.pdf', '监测报告', 'E', '2026-07', 'V1', '用户上传', 2, '有效', 'ACTIVE', 'CONFIRMED', NULL, NULL, '安全环保部', '2026-08-06 09:30:00'),
(930003, 'DOC-202607-0003', '高风险作业审批资料.pdf', '审批资料', 'S', '2026-07', 'V1', '用户上传', 1, '有效', 'ACTIVE', 'CONFIRMED', NULL, NULL, '工程管理部', '2026-08-07 09:15:00'),
(930004, 'DOC-202606-0004', '施工人员工资支付资料.pdf', '审批资料', 'S', '2026-06', 'V2', '用户上传', 2, '即将失效', 'ACTIVE', 'CONFIRMED', NULL, NULL, '财务管理部', '2026-08-06 16:40:00'),
(930005, 'DOC-202607-0005', 'NCR整改关闭资料.pdf', '审批资料', 'G', '2026-07', 'V1', '用户上传', 2, '有效', 'ACTIVE', 'CONFIRMED', NULL, NULL, '工程管理部', '2026-08-12 09:20:00'),
(930006, 'DOC-202607-0006', '临时用地合规资料.pdf', '审批资料', 'G', '2026-07', 'V1', 'ESG智能入库', 1, '有效', 'ACTIVE', 'CONFIRMED', NULL, NULL, '工程管理部', '2026-08-15 10:00:00'),
(930007, 'DOC-2026Q2-0007', '碳排放活动数据填报.xlsx', '台账记录', 'E', '2026-Q2', 'V1', '用户上传', 1, '有效', 'ACTIVE', 'CONFIRMED', NULL, NULL, '安全环保部', '2026-08-20 18:00:00'),
(930008, 'DOC-202607-0008', '安全教育培训记录.pdf', '台账记录', 'S', '2026-07', 'V1', '用户上传', 1, '有效', 'ACTIVE', 'CONFIRMED', NULL, NULL, '安全环保部', '2026-08-18 18:00:00'),
(930009, 'DOC-202607-0009', '植被恢复现场照片.zip', '影像资料', 'E', '2026-07', 'V1', '用户上传', 1, '有效', 'ACTIVE', 'CONFIRMED', NULL, NULL, '工程管理部', '2026-08-09 15:30:00'),
(930010, 'DOC-202606-0010', '环保设施验收报告.pdf', '审批资料', 'E', '2026-06', 'V1', 'ESG智能入库', 2, '已失效', 'EXPIRED', 'CONFIRMED', NULL, NULL, '安全环保部', '2026-07-28 10:00:00')
ON DUPLICATE KEY UPDATE validity_status=VALUES(validity_status), relation_count=VALUES(relation_count);

INSERT INTO document_version(id, document_id, file_id, version_no, version_desc, change_type, uploaded_by, uploaded_at, is_current)
VALUES
(940001, 930001, 900001, 'V2', '补充7月现场巡查照片与整改情况说明', 'UPDATE', 10001, '2026-08-10 18:00:00', 1)
ON DUPLICATE KEY UPDATE is_current=VALUES(is_current);

INSERT INTO document_task_relation(id, document_id, task_id, relation_type, relation_status, match_score, linked_by, linked_at, source)
VALUES
(950001, 930001, 't1', 'REQUIREMENT', 'LINKED', 96.00, 10001, '2026-08-10 18:05:00', 'AI_MATCH')
ON DUPLICATE KEY UPDATE relation_status=VALUES(relation_status);

INSERT INTO review_record
(id, task_id, task_name, module_code, module_name, submit_time, status, reviewer_id, reviewer, comment_summary, next_step)
VALUES
('r1', 't2', '高风险作业审批资料', 'S', '社会责任', '2026-08-07 09:15:00', '已退回', 10003, '李安全', '审批签章页缺失，附件日期与资料周期不一致', '查看意见并补正'),
('r2', 't3', '施工人员工资支付资料', 'S', '社会责任', '2026-08-06 16:40:00', '已退回', NULL, '王财务', '工资表需加盖公章，部分附件清晰度不足', '查看意见并补正'),
('r3', 't5', '临时用地合规资料', 'G', '治理合规', '2026-08-06 10:20:00', '已退回', NULL, '陈质量', '土地权属证明不完整，需补充用地批复文件', '查看意见并补正'),
('r4', 't1', '水保监测月报（2026年7月）', 'E', '环境环保', '2026-08-06 09:30:00', '待审核', NULL, '-', '', '查看进度'),
('r5', 't7', '安全教育培训记录（2026年7月）', 'S', '社会责任', '2026-08-05 17:25:00', '待审核', NULL, '-', '', '查看进度'),
('r6', 't6', '碳排放活动数据填报（2026-Q2）', 'E', '环境环保', '2026-08-04 18:00:00', '已通过', 10005, '赵环保', '资料完整，符合填报要求', '查看结果'),
('r7', NULL, '能源消耗统计表（2026年7月）', 'E', '环境环保', '2026-08-03 16:10:00', '已通过', 10005, '赵环保', '资料完整，符合填报要求', '查看结果')
ON DUPLICATE KEY UPDATE status=VALUES(status), comment_summary=VALUES(comment_summary);

INSERT INTO review_timeline
(id, review_id, event_time, action_text, event_type, operator_name, sequence_no)
VALUES
(970001, 'r1', '2026-08-05 18:00:00', '提交上传（张建国 提交任务）', 'SUBMIT', '张建国', 1),
(970002, 'r1', '2026-08-05 18:05:00', '完整性校验（系统校验通过，共5/7项资料完整）', 'VALIDATE', '系统', 2),
(970003, 'r1', '2026-08-07 09:15:00', '审核退回（审核人：李安全）', 'REJECT', '李安全', 3),
(970004, 'r2', '2026-08-04 14:00:00', '提交上传（王佳 提交任务）', 'SUBMIT', '王佳', 1),
(970005, 'r2', '2026-08-04 14:10:00', '完整性校验（系统校验通过，共4/5项资料完整）', 'VALIDATE', '系统', 2),
(970006, 'r2', '2026-08-06 16:40:00', '审核退回（审核人：王财务）', 'REJECT', '王财务', 3),
(970007, 'r3', '2026-08-03 10:00:00', '提交上传（刘工 提交任务）', 'SUBMIT', '刘工', 1),
(970008, 'r3', '2026-08-03 10:05:00', '完整性校验（系统校验通过，共2/3项资料完整）', 'VALIDATE', '系统', 2),
(970009, 'r3', '2026-08-06 10:20:00', '审核退回（审核人：陈质量）', 'REJECT', '陈质量', 3),
(970010, 'r4', '2026-08-06 09:30:00', '提交上传（赵宇航 提交任务）', 'SUBMIT', '赵宇航', 1),
(970011, 'r4', '2026-08-06 09:35:00', '完整性校验（系统校验通过）', 'VALIDATE', '系统', 2),
(970012, 'r4', '2026-08-06 10:00:00', '进入审核队列（等待分配审核人）', 'QUEUE', '系统', 3),
(970013, 'r5', '2026-08-05 17:25:00', '提交上传（孙德明 提交任务）', 'SUBMIT', '孙德明', 1),
(970014, 'r5', '2026-08-05 17:30:00', '完整性校验（系统校验通过）', 'VALIDATE', '系统', 2),
(970015, 'r5', '2026-08-06 09:00:00', '进入审核队列（等待分配审核人）', 'QUEUE', '系统', 3),
(970016, 'r6', '2026-08-04 18:00:00', '提交上传（赵环保 提交任务）', 'SUBMIT', '赵环保', 1),
(970017, 'r6', '2026-08-04 18:20:00', '审核通过（审核人：赵环保）', 'APPROVE', '赵环保', 2),
(970018, 'r7', '2026-08-03 16:10:00', '提交上传（赵环保 提交任务）', 'SUBMIT', '赵环保', 1),
(970019, 'r7', '2026-08-03 16:30:00', '审核通过（审核人：赵环保）', 'APPROVE', '赵环保', 2)
ON DUPLICATE KEY UPDATE action_text=VALUES(action_text);

INSERT INTO review_requirement
(id, review_id, requirement_text, requirement_status, sequence_no)
VALUES
(980001, 'r1', '审批签章页缺失，请补充完整并加盖单位公章。', '待补正', 1),
(980002, 'r1', '附件日期与资料周期不一致，请核对后重新上传。', '待补正', 2),
(980003, 'r2', '工资表需加盖公章。', '待补正', 1),
(980004, 'r2', '部分附件清晰度不足，请重新上传扫描件。', '待补正', 2),
(980005, 'r3', '土地权属证明不完整，请补充用地批复文件。', '待补正', 1)
ON DUPLICATE KEY UPDATE requirement_text=VALUES(requirement_text);

INSERT INTO safety_production_record
(id, project_start_date, `current_date`, continuous_days, current_stage, current_stage_detail, counting_status, update_time)
VALUES
(1, '2025-07-10', '2026-07-13', 368, '主体工程施工', '路基｜桥梁｜隧道并行施工', 'continuous', '2026-07-13 10:30:00')
ON DUPLICATE KEY UPDATE continuous_days=VALUES(continuous_days);

INSERT INTO indicator_result
(indicator_code, group_code, label, full_name, value, value_text, unit, display_order, calculated_at, published_at)
VALUES
('E01', 'E', '环境监测超标', '环境监测超标项次', 2, NULL, '项次', 1, '2026-07-13 10:20:00', '2026-07-13 10:30:00'),
('E02', 'E', '未闭环环保问题', '当前未闭环环保问题事项数', 5, NULL, '项', 2, '2026-07-13 10:20:00', '2026-07-13 10:30:00'),
('E03', 'E', '未闭环水保问题', '当前未闭环水保问题事项数', 7, NULL, '项', 3, '2026-07-13 10:20:00', '2026-07-13 10:30:00'),
('E04', 'E', '碳排放强度', '碳排放强度', 12856, NULL, 'tCO₂e', 4, '2026-07-13 10:20:00', '2026-07-13 10:30:00'),
('S01', 'S', '连续安全生产天数', '连续安全生产天数', 368, NULL, '天', 1, '2026-07-13 10:20:00', '2026-07-13 10:30:00'),
('S02', 'S', '在管较大及以上风险点', '在管较大及以上安全风险点数', 6, NULL, '项', 2, '2026-07-13 10:20:00', '2026-07-13 10:30:00'),
('S03', 'S', '未办结劳务纠纷', '未办结劳务纠纷事项数', 4, NULL, '项', 3, '2026-07-13 10:20:00', '2026-07-13 10:30:00'),
('S04', 'S', '未办结群众诉求', '未办结群众诉求事项数', 3, NULL, '项', 4, '2026-07-13 10:20:00', '2026-07-13 10:30:00'),
('G01', 'G', '未完成合规手续', '未完成合规手续事项数', 5, NULL, '项', 1, '2026-07-13 10:20:00', '2026-07-13 10:30:00'),
('G02', 'G', '许可临期及逾期', '当前临期及逾期许可事项数', 5, NULL, '项', 2, '2026-07-13 10:20:00', '2026-07-13 10:30:00'),
('G03', 'G', '未关闭整改事项', '未关闭整改事项数', 6, NULL, '项', 3, '2026-07-13 10:20:00', '2026-07-13 10:30:00'),
('G04', 'G', '待补齐合规资料', '待补齐合规资料事项数', 4, NULL, '项', 4, '2026-07-13 10:20:00', '2026-07-13 10:30:00')
ON DUPLICATE KEY UPDATE value=VALUES(value), published_at=VALUES(published_at);
