-- ============================================================================
-- V1_1_045__e02_gis_body_relink.sql
-- 将已落地的 E02 演示事项从「整条标段」改挂到本体要素
-- 幂等：可重复执行
-- ============================================================================

UPDATE env_issue_record
   SET location_text = CASE business_code
     WHEN 'E02-D01' THEN '弃渣点1（K12+300）'
     WHEN 'E02-D02' THEN '水源保护区2邻近排水口'
     WHEN 'E02-D03' THEN '弃渣点2临时堆土区'
     WHEN 'E02-D04' THEN '边坡监测点1邻近居民区'
     WHEN 'E02-D05' THEN '生态保护区1缓冲带'
     WHEN 'E02-D06' THEN '弃渣点1邻近拌合站'
     WHEN 'E02-D07' THEN '水源保护区2邻近沉淀池出口'
     ELSE location_text
   END
 WHERE is_demo = 1
   AND business_code IN ('E02-D01','E02-D02','E02-D03','E02-D04','E02-D05','E02-D06','E02-D07');

UPDATE e_closure_case
   SET location_text = CASE source_business_key
     WHEN 'E02-D01' THEN '弃渣点1（K12+300）'
     WHEN 'E02-D02' THEN '水源保护区2邻近排水口'
     WHEN 'E02-D03' THEN '弃渣点2临时堆土区'
     WHEN 'E02-D04' THEN '边坡监测点1邻近居民区'
     WHEN 'E02-D05' THEN '生态保护区1缓冲带'
     WHEN 'E02-D06' THEN '弃渣点1邻近拌合站'
     WHEN 'E02-D07' THEN '水源保护区2邻近沉淀池出口'
     ELSE location_text
   END,
   gis_feature_id = CASE source_business_key
     WHEN 'E02-D01' THEN 'waste-1-1'
     WHEN 'E02-D02' THEN 'water-2-1'
     WHEN 'E02-D03' THEN 'waste-2-1'
     WHEN 'E02-D04' THEN 'slope-1-1'
     WHEN 'E02-D05' THEN 'eco-1-1'
     WHEN 'E02-D06' THEN 'waste-1-1'
     WHEN 'E02-D07' THEN 'water-2-1'
     ELSE gis_feature_id
   END
 WHERE case_domain = 'E02_ENV'
   AND is_demo = 1
   AND source_business_key IN ('E02-D01','E02-D02','E02-D03','E02-D04','E02-D05','E02-D06','E02-D07');

DELETE FROM gis_feature_business_relation
 WHERE relation_type = 'environment_problem'
   AND (source_id LIKE 'E02-D%' OR relation_code LIKE 'E02-D%');

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
