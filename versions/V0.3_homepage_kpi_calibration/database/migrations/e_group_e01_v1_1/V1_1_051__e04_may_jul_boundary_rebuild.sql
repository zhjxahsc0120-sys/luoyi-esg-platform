-- ============================================================================
-- V1_1_051__e04_may_jul_boundary_rebuild.sql
-- E04 按甲方 7.14 意见重构测试核算包（可完全重建 5–7 月测数）
--
-- 权威依据（最高标准）：
--   《罗宜高速ESG首页指标数据需求调研说明书(7.14意见说明)》
--   + Downloads/罗宜高速ESG_甲方7.14意见_Codex快速核查包.md
-- 可用边界：材料为主；燃油、电力原则上可提供；运输暂不纳入；
--           设备可提供但不得与油耗/电耗双计（本包不单列设备来源）。
-- 统计起点：开工令日期 2026-05-08；核算期间 2026-05 — 2026-07。
--
-- 设计变更说明：用户 2026-07-24 确认 5–7 月测数可完全重构，并以甲方 7.14 为
-- 可用数据最高标准；本迁移覆盖旧演示主值 12,856（含运输）勾稽包。
-- 幂等：可重复执行。
-- ============================================================================

SET FOREIGN_KEY_CHECKS = 0;

-- --------------------------------------------------------------------------
-- 1. 当前生效边界：BOUND-E04-V1-ACTIVE（甲方 7.14 倾向）
-- --------------------------------------------------------------------------
DELETE FROM carbon_accounting_boundary
 WHERE boundary_version IN (
   'DEMO-BOUND-E04-20260718',
   'BOUND-E04-V1-CANDIDATE',
   'BOUND-E04-V1-ACTIVE'
 );

INSERT INTO carbon_accounting_boundary
  (boundary_version, boundary_label, boundary_status, source_code, source_label, in_boundary, sort_order, description, is_demo, data_nature)
VALUES
  ('BOUND-E04-V1-ACTIVE', '甲方7.14核算边界（测试生效）', 'ACTIVE',
   'diesel', '施工用油', 1, 1, '燃油原则上可提供，计入累计', 1, 'demo'),
  ('BOUND-E04-V1-ACTIVE', '甲方7.14核算边界（测试生效）', 'ACTIVE',
   'electricity', '施工用电', 1, 2, '电力原则上可提供，计入累计', 1, 'demo'),
  ('BOUND-E04-V1-ACTIVE', '甲方7.14核算边界（测试生效）', 'ACTIVE',
   'material', '主要材料', 1, 3, '材料为主要统计基础，计入累计', 1, 'demo'),
  ('BOUND-E04-V1-ACTIVE', '甲方7.14核算边界（测试生效）', 'ACTIVE',
   'transport', '施工运输', 0, 4, '甲方意见：运输暂不纳入', 1, 'demo');

-- --------------------------------------------------------------------------
-- 2. 当前核算批次：期间改为 2026-05 — 2026-07；绑定 ACTIVE 边界
-- --------------------------------------------------------------------------
UPDATE carbon_accounting_batch
SET batch_code = 'TEST-BATCH-E04-20260724',
    batch_label = '测试核算批次（甲方7.14 · 开工后至2026-07）',
    boundary_version = 'BOUND-E04-V1-ACTIVE',
    statistics_as_of = '2026-07-24',
    period_start = '2026-05',
    period_end = '2026-07',
    data_nature = 'demo',
    is_current = 1,
    is_demo = 1,
    verification_status = 'PENDING',
    boundary_snapshot_note = '按甲方7.14：材料+燃油+电力计入，运输暂不纳入；统计起点开工令 2026-05-08；5–7月测数完全重构，不含开工前月份。'
WHERE id = 1
   OR batch_code IN ('DEMO-BATCH-E04-20260718', 'TEST-BATCH-E04-20260724');

INSERT INTO carbon_accounting_batch
  (id, batch_code, batch_label, boundary_version, statistics_as_of,
   period_start, period_end, data_nature, is_current, is_demo,
   verification_status, boundary_snapshot_note)
SELECT 1, 'TEST-BATCH-E04-20260724', '测试核算批次（甲方7.14 · 开工后至2026-07）',
       'BOUND-E04-V1-ACTIVE', '2026-07-24',
       '2026-05', '2026-07', 'demo', 1, 1,
       'PENDING',
       '按甲方7.14：材料+燃油+电力计入，运输暂不纳入；统计起点开工令 2026-05-08；5–7月测数完全重构，不含开工前月份。'
WHERE NOT EXISTS (SELECT 1 FROM carbon_accounting_batch WHERE id = 1);

-- --------------------------------------------------------------------------
-- 3. 开工前月份（2026-02—04）退出当前有效集
-- --------------------------------------------------------------------------
UPDATE carbon_emission_activity
SET is_current = 0,
    effective_status = 'INEFFECTIVE',
    accounting_batch_id = NULL,
    demo_note = '开工令前月份，已退出当前 E04 有效核算集（开工 2026-05-08）'
WHERE id BETWEEN 720001 AND 720003
   OR period_value IN ('2026-02', '2026-03', '2026-04');

UPDATE carbon_material_usage
SET is_current = 0,
    effective_status = 'INEFFECTIVE',
    accounting_batch_id = NULL
WHERE id BETWEEN 720501 AND 720509
   OR period_value IN ('2026-02', '2026-03', '2026-04');

-- --------------------------------------------------------------------------
-- 4. 2026-05—07：剔除运输贡献，重算月度合计（燃油+电力+材料）
--    保留既有柴油/电力/材料活动量与分项排放，仅清零运输。
-- --------------------------------------------------------------------------
UPDATE carbon_emission_activity
SET other_emission = 0,
    transport_usage = 0,
    carbon_emission = ROUND(COALESCE(diesel_emission, 0) + COALESCE(electricity_emission, 0) + COALESCE(material_emission, 0), 4),
    boundary_version = 'BOUND-E04-V1-ACTIVE',
    accounting_batch_id = 1,
    is_current = 1,
    is_demo = 1,
    data_nature = 'demo',
    effective_status = 'EFFECTIVE',
    evidence_status = 'MISSING',
    verification_status = '待业务核验',
    diesel_factor_snapshot_id = COALESCE(diesel_factor_snapshot_id, 740101),
    electricity_factor_snapshot_id = COALESCE(electricity_factor_snapshot_id, 740102),
    material_factor_snapshot_id = COALESCE(material_factor_snapshot_id, 740103),
    transport_factor_snapshot_id = NULL,
    demo_note = '甲方7.14测试包：材料+燃油+电力；运输暂不纳入；统计起点 2026-05-08'
WHERE id BETWEEN 720004 AND 720006
   OR period_value IN ('2026-05', '2026-06', '2026-07');

UPDATE carbon_material_usage
SET is_current = 1,
    is_demo = 1,
    data_nature = 'demo',
    effective_status = 'EFFECTIVE',
    evidence_status = 'MISSING',
    accounting_batch_id = 1,
    factor_snapshot_id = CASE
      WHEN material_name = '水泥' THEN 740103
      WHEN material_name = '钢材' THEN 740104
      WHEN material_name = '沥青' THEN 740105
      ELSE factor_snapshot_id
    END
WHERE (id BETWEEN 720510 AND 720518)
   OR period_value IN ('2026-05', '2026-06', '2026-07');

-- --------------------------------------------------------------------------
-- 5. 标段明细 / 碳专题：同期对齐（剔除运输；开工前月份清零）
-- --------------------------------------------------------------------------
UPDATE carbon_emission_segment_detail
SET emission_amount = 0,
    activity_amount = 0,
    is_demo = 1
WHERE boundary_code = 'DEMO-CONSTRUCTION-E04'
  AND (
    accounting_month IN ('2026-02', '2026-03', '2026-04')
    OR emission_source_code = 'TRANSPORT'
  );

UPDATE carbon_emission_segment_detail
SET is_demo = 1
WHERE boundary_code = 'DEMO-CONSTRUCTION-E04'
  AND accounting_month IN ('2026-05', '2026-06', '2026-07')
  AND emission_source_code <> 'TRANSPORT';

-- 活动表侧已重算月度合计后，标段 DIESEL/ELECTRICITY/MATERIAL 行保持原分摊比例
-- （运输已清零）；碳专题 API 将按 is_current 活动月聚合。

SET FOREIGN_KEY_CHECKS = 1;
