-- ============================================================================
-- V1_0_030__s01_demo_seed.sql
-- S01 V1.0 增量迁移 — 演示测数重建（基于冻结稿 77 天基线）
-- ============================================================================
-- 幂等策略：
--   - 旧 v0.1 演示行(id=1)：标记 is_current=0, data_nature='demo', is_demo=1
--   - 新演示批次(DEMO-S01-20260724)：INSERT IGNORE
--   - 新演示快照(77天)：INSERT IGNORE
--   - 工期阶段：INSERT IGNORE
-- ============================================================================

-- --------------------------------------------------------------------------
-- 0. 回退旧 v0.1 演示行：退出 current 有效集
--    原行 id=1, project_start_date=2025-07-10, current_date=2026-07-13,
--    continuous_days=368, counting_status='continuous'
--    → 设置 is_current=0, data_nature='demo', is_demo=1（不删除）
-- --------------------------------------------------------------------------
UPDATE safety_production_record
SET is_current = 0,
    data_nature = 'demo',
    is_demo = 1,
    cycle_start_date = '2025-07-10',
    statistics_as_of = `current_date`,
    confirmation_status = 'PENDING',
    verification_status = 'PENDING_REVIEW',
    effective_status = 'INEFFECTIVE'
WHERE id = 1
  AND project_start_date = '2025-07-10';

-- --------------------------------------------------------------------------
-- 1. 演示确认批次
--    批次编码: DEMO-S01-20260724
--    统计期末: 2026-07-24
--    周期起点: 2026-05-08（开工令）
--    连续天数: 77
-- --------------------------------------------------------------------------
INSERT IGNORE INTO s01_confirmation_batch (
    batch_code, project_id, confirmation_month,
    statistics_as_of, cycle_start_date, continuous_days,
    counting_status, confirmation_unit, confirmed_by, confirmed_at,
    confirmation_status, verification_status, effective_status, effective_at,
    data_nature, is_demo, version_no, remark
) VALUES (
    'DEMO-S01-20260724',
    'LUOYI-ESG',
    '2026-07',
    '2026-07-24',
    '2026-05-08',
    77,
    'CONTINUOUS',
    '建设单位（演示）',
    '系统管理员',
    '2026-07-24 18:00:00',
    'CONFIRMED',
    'VERIFIED',
    'EFFECTIVE',
    '2026-07-24 18:00:00',
    'demo',
    1,
    1,
    '演示数据：无触发重置事故，自开工令起连续安全生产 77 天（冻结稿验收基线）'
);

-- --------------------------------------------------------------------------
-- 2. 演示确认快照（safety_production_record）
--    使用新 ID(1001)避免与旧 id=1 冲突
--    勾稽要求：
--      continuous_days = 77
--      cycle_start_date = 2026-05-08
--      statistics_as_of = 2026-07-24
--      data_nature = 'demo', is_demo = 1
--      is_current = 1
--      counting_status = 'continuous'（兼容旧枚举值）
-- --------------------------------------------------------------------------
INSERT IGNORE INTO safety_production_record (
    id, project_id, project_start_date, `current_date`,
    cycle_start_date, statistics_as_of,
    continuous_days, current_stage, current_stage_detail,
    counting_status,
    confirmation_batch_id, confirmation_status,
    verification_status, effective_status, is_current,
    data_nature, is_demo,
    confirmed_at, confirmed_by,
    update_time, created_at
) SELECT
    1001, 'LUOYI-ESG', '2026-05-08', '2026-07-24',
    '2026-05-08', '2026-07-24',
    77, '路基桥涵施工', '路基｜桥梁并行施工',
    'continuous',
    cb.id, 'CONFIRMED',
    'VERIFIED', 'EFFECTIVE', 1,
    'demo', 1,
    '2026-07-24 18:00:00', '系统管理员',
    '2026-07-24 18:00:00', NOW()
FROM s01_confirmation_batch cb
WHERE cb.batch_code = 'DEMO-S01-20260724'
  AND NOT EXISTS (
      SELECT 1 FROM safety_production_record spr
      WHERE spr.id = 1001
  );

-- --------------------------------------------------------------------------
-- 3. 工期阶段记录
--    当前有效阶段：路基桥涵施工
--    验收名必须一致
--    旧表 NOT NULL 无默认：id（依赖 V1_0_015 AUTO_INCREMENT）、stage_key、
--    stage_name、stage_status、sequence_no — seed 须显式写入 stage_key
--    幂等：使用 NOT EXISTS 防重复（stage_key 有 UNIQUE）
-- --------------------------------------------------------------------------

-- 3a. 其他仍标记为 current 的阶段退出现役（保留主体工程等历史行）
UPDATE construction_stage_record
SET stage_status = CASE
        WHEN stage_status = 'current' THEN 'completed'
        ELSE stage_status
    END,
    is_current = 0
WHERE project_id = 'LUOYI-ESG'
  AND is_current = 1
  AND stage_name <> '路基桥涵施工';

INSERT INTO construction_stage_record (
    project_id, stage_key, stage_name, stage_status, start_date, end_date,
    detail, stage_detail, sequence_no, effective_status, is_current,
    data_nature, is_demo
)
SELECT 'LUOYI-ESG','roadbed-bridge-culvert','路基桥涵施工','current','2026-05-08',NULL,
       '路基填筑、桥梁基础及下部结构施工',
       '路基填筑、桥梁基础及下部结构施工',
       1,'EFFECTIVE',1,'demo',1
FROM DUAL
WHERE NOT EXISTS (
    SELECT 1 FROM construction_stage_record
    WHERE project_id = 'LUOYI-ESG'
      AND (
          stage_key = 'roadbed-bridge-culvert'
          OR (stage_name = '路基桥涵施工' AND stage_status = 'current' AND is_current = 1 AND is_demo = 1)
      )
);

-- 3b. 若行已存在但未现役，恢复为 current（幂等重跑）
UPDATE construction_stage_record
SET stage_status = 'current',
    is_current = 1,
    effective_status = 'EFFECTIVE',
    start_date = '2026-05-08',
    end_date = NULL,
    detail = '路基填筑、桥梁基础及下部结构施工',
    stage_detail = '路基填筑、桥梁基础及下部结构施工',
    data_nature = 'demo',
    is_demo = 1
WHERE project_id = 'LUOYI-ESG'
  AND stage_key = 'roadbed-bridge-culvert';

-- --------------------------------------------------------------------------
-- 4. 无事故演示记录（确保 PENDING_DETERMINATION 场景可扩展）
--    当前无事故，不插入 safety_incident_record
--    仅为自验完整性提供注释说明
-- --------------------------------------------------------------------------
-- 注意：本 seed 不插入事故记录。
-- 无事故 → 无需重置 → counting_status = CONTINUOUS → 77 天

-- --------------------------------------------------------------------------
-- 5. 验证查询（不修改数据）
-- --------------------------------------------------------------------------
SELECT '--- S01 P1 Demo Seed Verification ---' AS section;

SELECT 'V-demo-snapshot' AS check_item,
       COUNT(*) AS cnt,
       CASE WHEN COUNT(*) = 1 THEN 'PASS' ELSE 'FAIL' END AS result
FROM safety_production_record
WHERE is_demo = 1 AND is_current = 1 AND continuous_days = 77;

SELECT 'V-old-retired' AS check_item,
       COUNT(*) AS cnt,
       CASE WHEN COUNT(*) = 1 THEN 'PASS' ELSE 'FAIL' END AS result
FROM safety_production_record
WHERE id = 1 AND is_current = 0 AND data_nature = 'demo';

SELECT 'V-no-fake-formal' AS check_item,
       COUNT(*) AS bad_count,
       CASE WHEN COUNT(*) = 0 THEN 'PASS' ELSE 'FAIL' END AS result
FROM safety_production_record
WHERE data_nature = 'formal' AND confirmation_status = 'CONFIRMED' AND is_current = 1
  AND continuous_days = 77 AND is_demo = 1;

SELECT 'V-batch-exists' AS check_item,
       COUNT(*) AS cnt,
       CASE WHEN COUNT(*) = 1 THEN 'PASS' ELSE 'FAIL' END AS result
FROM s01_confirmation_batch
WHERE batch_code = 'DEMO-S01-20260724' AND is_demo = 1 AND effective_status = 'EFFECTIVE';

SELECT 'V-stage-name' AS check_item,
       stage_name,
       stage_status,
       CASE WHEN stage_name = '路基桥涵施工' AND stage_status = 'current' THEN 'PASS' ELSE 'FAIL' END AS result
FROM construction_stage_record
WHERE is_current = 1 AND stage_status = 'current'
ORDER BY sequence_no LIMIT 1;