-- ============================================================================
-- V1_1_049__e04_demo_seed.sql
-- E04 P1 数据登记与补链：边界注册 / 批次 / 因子快照 / 演示数据回填
-- 权威依据：E04_Trae实施任务单_P1_V1.0 + E04_累计碳排放工作台设计说明_B方案_V1.0冻结稿
-- 幂等：先按业务键清理再插入；不改 12,856.00 锚定值
-- ============================================================================

SET FOREIGN_KEY_CHECKS = 0;

-- --------------------------------------------------------------------------
-- 1. 幂等清理（先删子表再删主表）
-- --------------------------------------------------------------------------
DELETE FROM carbon_emission_factor_snapshot
 WHERE snapshot_code LIKE 'E04-SNAP-%';

DELETE FROM carbon_accounting_batch
 WHERE batch_code IN ('DEMO-BATCH-E04-20260718');

DELETE FROM carbon_accounting_boundary
 WHERE boundary_version IN ('DEMO-BOUND-E04-20260718', 'BOUND-E04-V1-CANDIDATE');

SET FOREIGN_KEY_CHECKS = 1;

-- --------------------------------------------------------------------------
-- 2. 边界注册：DEMO-BOUND-E04-20260718（ACTIVE，演示通道）
--    四来源全部计入，运输包含在内（与已落地 12,856 勾稽一致）
-- --------------------------------------------------------------------------
INSERT INTO carbon_accounting_boundary
  (boundary_version, boundary_label, boundary_status, source_code, source_label, in_boundary, sort_order, description, is_demo, data_nature)
VALUES
  ('DEMO-BOUND-E04-20260718', '既有演示核算边界（2026-07-18 冻结）', 'ACTIVE',
   'diesel', '施工用油', 1, 1, '演示边界包含施工用油', 1, 'demo'),
  ('DEMO-BOUND-E04-20260718', '既有演示核算边界（2026-07-18 冻结）', 'ACTIVE',
   'electricity', '施工用电', 1, 2, '演示边界包含施工用电', 1, 'demo'),
  ('DEMO-BOUND-E04-20260718', '既有演示核算边界（2026-07-18 冻结）', 'ACTIVE',
   'material', '主要材料', 1, 3, '演示边界包含主要材料', 1, 'demo'),
  ('DEMO-BOUND-E04-20260718', '既有演示核算边界（2026-07-18 冻结）', 'ACTIVE',
   'transport', '施工运输', 1, 4, '演示边界包含施工运输（885.04 tCO₂e）', 1, 'demo');

-- --------------------------------------------------------------------------
-- 3. 候选边界：BOUND-E04-V1-CANDIDATE（CANDIDATE，仅只读对照）
--    运输 in_boundary=0（暂不纳入）；对照试算约 11,970.96
-- --------------------------------------------------------------------------
INSERT INTO carbon_accounting_boundary
  (boundary_version, boundary_label, boundary_status, source_code, source_label, in_boundary, sort_order, description, is_demo, data_nature)
VALUES
  ('BOUND-E04-V1-CANDIDATE', '正式候选边界（依据 7.14 意见）', 'CANDIDATE',
   'diesel', '施工用油', 1, 1, '候选边界：施工用油计入', 0, 'formal'),
  ('BOUND-E04-V1-CANDIDATE', '正式候选边界（依据 7.14 意见）', 'CANDIDATE',
   'electricity', '施工用电', 1, 2, '候选边界：施工用电计入', 0, 'formal'),
  ('BOUND-E04-V1-CANDIDATE', '正式候选边界（依据 7.14 意见）', 'CANDIDATE',
   'material', '主要材料', 1, 3, '候选边界：主要材料计入', 0, 'formal'),
  ('BOUND-E04-V1-CANDIDATE', '正式候选边界（依据 7.14 意见）', 'CANDIDATE',
   'transport', '施工运输', 0, 4,
   '运输暂不纳入正式候选边界。对照试算值约 11,970.96（=12,856-885.04），仅只读参考，不替换首页演示主值，不进入任何正式 KPI。',
   0, 'formal');

-- --------------------------------------------------------------------------
-- 4. 演示核算批次：DEMO-BATCH-E04-20260718（current=1，演示通道）
-- --------------------------------------------------------------------------
INSERT INTO carbon_accounting_batch
  (id, batch_code, batch_label, boundary_version, statistics_as_of,
   period_start, period_end, data_nature, is_current, is_demo,
   verification_status, boundary_snapshot_note)
VALUES
  (1, 'DEMO-BATCH-E04-20260718', '演示核算批次（2026-07-18 冻结）',
   'DEMO-BOUND-E04-20260718', '2026-07-18',
   '2026-02', '2026-07', 'demo', 1, 1,
   'PENDING',
   '基于既有演示核算包（12,856.00）创建；四来源含运输。当前演示主路径生效批次。');

-- --------------------------------------------------------------------------
-- 5. 因子不可变快照：E04-SNAP-001 ~ 006（对应 740001~740006）
--    快照记录因子核算时的完整信息，一旦被历史批次引用则不可变（§5.4）
-- --------------------------------------------------------------------------
INSERT INTO carbon_emission_factor_snapshot
  (id, snapshot_code, factor_id, factor_code, factor_name, factor_value, factor_unit,
   numerator_unit, denominator_unit, activity_unit,
   conversion_factor, conversion_path, factor_version, factor_source,
   gwp_version, precision_rule, effective_from, effective_until, snapshot_at, data_nature)
VALUES
  -- 740001 施工用油 DEMO_DIESEL
  (740101, 'E04-SNAP-001', 740001, 'DEMO_DIESEL', '施工用油演示排放因子',
   2.680000000000, 'kgCO₂e/L',
   'kgCO₂e', 'L', 'L',
   NULL, NULL, 'DEMO-EF-2026-v0.1', '系统演示测试数据，非正式核算依据',
   NULL, 'ROUND_HALF_UP to 2 decimal', NULL, NULL, '2026-07-18 00:00:00', 'demo'),
  -- 740002 施工用电 DEMO_ELECTRICITY
  (740102, 'E04-SNAP-002', 740002, 'DEMO_ELECTRICITY', '施工用电演示排放因子',
   0.570000000000, 'kgCO₂e/kWh',
   'kgCO₂e', 'kWh', 'kWh',
   NULL, NULL, 'DEMO-EF-2026-v0.1', '系统演示测试数据，非正式核算依据',
   NULL, 'ROUND_HALF_UP to 2 decimal', NULL, NULL, '2026-07-18 00:00:00', 'demo'),
  -- 740003 水泥 DEMO_CEMENT
  (740103, 'E04-SNAP-003', 740003, 'DEMO_CEMENT', '水泥演示排放因子',
   0.800000000000, 'tCO₂e/t',
   'tCO₂e', 't', 't',
   NULL, NULL, 'DEMO-EF-2026-v0.1', '系统演示测试数据，非正式核算依据',
   NULL, 'ROUND_HALF_UP to 2 decimal', NULL, NULL, '2026-07-18 00:00:00', 'demo'),
  -- 740004 钢材 DEMO_STEEL
  (740104, 'E04-SNAP-004', 740004, 'DEMO_STEEL', '钢材演示排放因子',
   0.750000000000, 'tCO₂e/t',
   'tCO₂e', 't', 't',
   NULL, NULL, 'DEMO-EF-2026-v0.1', '系统演示测试数据，非正式核算依据',
   NULL, 'ROUND_HALF_UP to 2 decimal', NULL, NULL, '2026-07-18 00:00:00', 'demo'),
  -- 740005 沥青 DEMO_ASPHALT
  (740105, 'E04-SNAP-005', 740005, 'DEMO_ASPHALT', '沥青演示排放因子',
   0.680000000000, 'tCO₂e/t',
   'tCO₂e', 't', 't',
   NULL, NULL, 'DEMO-EF-2026-v0.1', '系统演示测试数据，非正式核算依据',
   NULL, 'ROUND_HALF_UP to 2 decimal', NULL, NULL, '2026-07-18 00:00:00', 'demo'),
  -- 740006 施工运输 DEMO_TRANSPORT
  (740106, 'E04-SNAP-006', 740006, 'DEMO_TRANSPORT', '施工运输演示排放因子',
   0.000885000000, 'tCO₂e/(t·km)',
   'tCO₂e', 't·km', 't·km',
   NULL, NULL, 'DEMO-EF-2026-v0.1', '系统演示测试数据，非正式核算依据',
   NULL, 'ROUND_HALF_UP to 2 decimal', NULL, NULL, '2026-07-18 00:00:00', 'demo');

-- --------------------------------------------------------------------------
-- 6. 演示数据回填：carbon_emission_activity（720001~720006）
--    补链 is_demo / effective_status / evidence_status / boundary /
--    accounting_batch / factor_snapshot_id
--    不改 12,856.00 锚定值！
-- --------------------------------------------------------------------------
UPDATE carbon_emission_activity
SET is_demo = 1,
    effective_status = 'EFFECTIVE',
    evidence_status = 'MISSING',
    boundary_version = 'DEMO-BOUND-E04-20260718',
    accounting_batch_id = 1,
    is_current = 1,
    diesel_factor_snapshot_id = 740101,
    electricity_factor_snapshot_id = 740102,
    material_factor_snapshot_id = 740103,
    transport_factor_snapshot_id = 740106
WHERE id BETWEEN 720001 AND 720006;

-- --------------------------------------------------------------------------
-- 7. 演示数据回填：carbon_material_usage（720501~720518）
--    按材料类型绑定因子快照；水泥→740103、钢材→740104、沥青→740105
-- --------------------------------------------------------------------------
UPDATE carbon_material_usage
SET is_demo = 1,
    effective_status = 'EFFECTIVE',
    evidence_status = 'MISSING',
    accounting_batch_id = 1,
    is_current = 1,
    factor_snapshot_id = CASE
      WHEN material_name = '水泥' THEN 740103
      WHEN material_name = '钢材' THEN 740104
      WHEN material_name = '沥青' THEN 740105
      ELSE factor_snapshot_id
    END
WHERE id BETWEEN 720501 AND 720518;