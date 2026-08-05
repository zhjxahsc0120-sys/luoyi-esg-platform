-- 罗宜高速 ESG 数字化管理平台
-- 首页一级指标业务事实校正 V0.3
-- 作用范围：project_id=1001、period_end=2026-08-04 的 12 个首页 KPI。
-- 不修改前端、API 路径、API 字段结构、二级页面及明细业务表。

START TRANSACTION;

UPDATE esg_demo_indicator_result
SET
  kpi_name = CASE kpi_key
    WHEN 'E01' THEN '环境监测异常'
    WHEN 'E02' THEN '水保风险对象'
    WHEN 'E03' THEN '生态保护对象'
    WHEN 'E04' THEN '文物保护对象'
    WHEN 'S01' THEN '连续安全生产'
    WHEN 'S02' THEN '较大及以上风险源'
    WHEN 'S03' THEN '工资支付达标率'
    WHEN 'S04' THEN '未闭环群众诉求'
    WHEN 'G01' THEN '审批合规率'
    WHEN 'G02' THEN '许可管控完成率'
    WHEN 'G03' THEN '设计变更受控率'
    WHEN 'G04' THEN '内控合规状态'
    ELSE kpi_name
  END,
  value_decimal = CASE kpi_key
    WHEN 'E01' THEN 2.00
    WHEN 'E02' THEN 4.00
    WHEN 'E03' THEN 2.00
    WHEN 'E04' THEN 0.00
    WHEN 'S01' THEN NULL
    WHEN 'S02' THEN 6.00
    WHEN 'S03' THEN 100.00
    WHEN 'S04' THEN 3.00
    WHEN 'G01' THEN NULL
    WHEN 'G02' THEN NULL
    WHEN 'G03' THEN NULL
    WHEN 'G04' THEN NULL
    ELSE value_decimal
  END,
  value_text = CASE kpi_key
    WHEN 'S01' THEN '2026-05-08'
    WHEN 'G01' THEN '12/12'
    WHEN 'G02' THEN '2/2'
    WHEN 'G03' THEN '4/4'
    WHEN 'G04' THEN '正常'
    ELSE NULL
  END,
  unit = CASE kpi_key
    WHEN 'E01' THEN '项'
    WHEN 'E02' THEN '处'
    WHEN 'E03' THEN '处'
    WHEN 'E04' THEN '处'
    WHEN 'S01' THEN '天'
    WHEN 'S02' THEN '处'
    WHEN 'S03' THEN '%'
    WHEN 'S04' THEN '项'
    WHEN 'G01' THEN '100%'
    WHEN 'G02' THEN '100%'
    WHEN 'G03' THEN '100%'
    WHEN 'G04' THEN ''
    ELSE unit
  END,
  hint = CASE kpi_key
    WHEN 'E01' THEN '表示当前异常监测事项数量。'
    WHEN 'E02' THEN '表示当前纳入管理的水保风险对象数量。'
    WHEN 'E03' THEN '表示当前纳入管理的生态保护对象数量。'
    WHEN 'E04' THEN '已完成文物调查，无涉文物影响'
    WHEN 'S01' THEN '自2026-05-08起连续安全生产，按统计截止日动态计算。'
    WHEN 'S02' THEN '当前纳入管理的较大及以上风险源共6处。'
    WHEN 'S03' THEN '工资按期足额支付。'
    WHEN 'S04' THEN '表示当前未关闭诉求数量。'
    WHEN 'G01' THEN '12项审批事项全部满足要求。'
    WHEN 'G02' THEN '2/2项许可及施工管控事项均已完成。'
    WHEN 'G03' THEN '4/4项设计变更均完成审批及闭环。'
    WHEN 'G04' THEN '检查事项无异常，内控与廉洁状态正常。'
    ELSE hint
  END,
  risk_level = CASE kpi_key
    WHEN 'E01' THEN 'HIGH'
    WHEN 'E02' THEN 'MEDIUM'
    WHEN 'E03' THEN 'MEDIUM'
    WHEN 'E04' THEN 'NORMAL'
    WHEN 'S01' THEN 'NORMAL'
    WHEN 'S02' THEN 'MEDIUM'
    WHEN 'S03' THEN 'NORMAL'
    WHEN 'S04' THEN 'LOW'
    WHEN 'G01' THEN 'NORMAL'
    WHEN 'G02' THEN 'NORMAL'
    WHEN 'G03' THEN 'NORMAL'
    WHEN 'G04' THEN 'NORMAL'
    ELSE risk_level
  END,
  source_summary = CASE kpi_key
    WHEN 'S01' THEN '业务事实：连续生产起算日期=2026-05-08；按period_end计算，起算日计第1天'
    ELSE '首页一级指标业务事实校正 V0.3'
  END,
  rule_version = 'DEMO-0.3',
  calculated_at = CURRENT_TIMESTAMP,
  published_at = CURRENT_TIMESTAMP
WHERE project_id = 1001
  AND period_end = '2026-08-04'
  AND kpi_key IN ('E01','E02','E03','E04','S01','S02','S03','S04','G01','G02','G03','G04')
  AND result_status = 'PUBLISHED';

COMMIT;

-- S01 的 value_text 保存业务起算日期；视图按 period_end 动态计算连续天数。
-- 2026-05-08 至 2026-08-04，起算日计第1天，结果为 89 天。
CREATE OR REPLACE ALGORITHM=UNDEFINED
SQL SECURITY DEFINER
VIEW v_esg_demo_dashboard_kpis AS
SELECT
  r.project_id AS project_id,
  r.kpi_key AS `key`,
  r.kpi_name AS name,
  CASE
    WHEN r.kpi_key = 'S01' AND r.value_text IS NOT NULL
      THEN DATEDIFF(r.period_end, STR_TO_DATE(r.value_text, '%Y-%m-%d')) + 1
    ELSE COALESCE(r.value_decimal, r.value_text)
  END AS `value`,
  r.unit AS unit,
  r.hint AS hint,
  r.risk_level AS riskLevel,
  r.period_end AS period_end
FROM esg_demo_indicator_result r
WHERE r.result_status = 'PUBLISHED';

-- 验证：应返回 12 行；S01=89，E04=0，S03=100，G01/G02/G03 为比值，G04=正常。
SELECT project_id, `key`, name, `value`, unit, hint, riskLevel, period_end
FROM v_esg_demo_dashboard_kpis
WHERE project_id = 1001
  AND period_end = '2026-08-04'
ORDER BY FIELD(`key`,'E01','E02','E03','E04','S01','S02','S03','S04','G01','G02','G03','G04');
