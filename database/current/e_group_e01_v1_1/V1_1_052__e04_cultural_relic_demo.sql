-- ============================================================================
-- V1_1_052__e04_cultural_relic_demo.sql
-- E04 首页口径切换：文物保护管控演示表 + 3 条种子
-- 幂等：先按业务键清理再插入；不改动碳排放表
-- ============================================================================

CREATE TABLE IF NOT EXISTS biz_cultural_relic_object (
  id BIGINT NOT NULL AUTO_INCREMENT,
  project_id VARCHAR(64) NOT NULL,
  section_id BIGINT NULL,
  relic_code VARCHAR(64) NOT NULL,
  relic_name VARCHAR(200) NOT NULL,
  relic_type VARCHAR(64) NOT NULL,
  protection_level VARCHAR(64) NULL,
  location_desc VARCHAR(200) NULL,
  longitude DECIMAL(12, 8) NULL,
  latitude DECIMAL(12, 8) NULL,
  protection_scope VARCHAR(500) NULL,
  construction_impact VARCHAR(500) NULL,
  protection_measure VARCHAR(500) NULL,
  responsible_unit VARCHAR(200) NULL,
  risk_status VARCHAR(64) NOT NULL DEFAULT '正常',
  update_time DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  UNIQUE KEY uk_biz_cultural_relic_code (project_id, relic_code),
  KEY idx_biz_cultural_relic_section (section_id),
  KEY idx_biz_cultural_relic_risk (risk_status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
  COMMENT='E04 文物保护管控对象演示台账';

DELETE FROM biz_cultural_relic_object
 WHERE project_id = 'LUOYI-ESG'
   AND relic_code IN ('E04-CR-001', 'E04-CR-002', 'E04-CR-003');

INSERT INTO biz_cultural_relic_object
  (id, project_id, section_id, relic_code, relic_name, relic_type, protection_level,
   location_desc, longitude, latitude, protection_scope, construction_impact,
   protection_measure, responsible_unit, risk_status, update_time)
VALUES
  (440001, 'LUOYI-ESG', 910001, 'E04-CR-001', 'K45+600文物调查点', '历史遗迹', '一般保护',
   'K45+600', 109.79010000, 24.49220000,
   '调查点周边 50m 缓冲管控区', '临近路基施工，已划定绕行便道',
   '现场围挡标识 + 施工前交底 + 专人巡查', '安全环保部', '正常', '2026-08-01 10:00:00'),
  (440002, 'LUOYI-ESG', 910002, 'E04-CR-002', 'K78+200传统村落保护点', '文化资源', '重点关注',
   'K78+200', 109.69050000, 24.43080000,
   '村落建筑群及入口缓冲区', '运输通道绕开村落主街，噪声时段管控',
   '绕行运输方案已落实，防尘降噪措施到位', '工程管理部', '措施已落实', '2026-08-01 10:05:00'),
  (440003, 'LUOYI-ESG', 910003, 'E04-CR-003', 'K102+500调查点', '调查对象', '一般调查',
   'K102+500', 109.52080000, 24.44510000,
   '调查点本体及 30m 观察带', '现状评估为无施工直接扰动',
   '台账跟踪 + 季度复核', '总工办', '无影响', '2026-08-01 10:10:00');
