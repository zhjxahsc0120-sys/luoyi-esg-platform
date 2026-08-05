-- 罗宜高速 ESG 领导层首页 V0.2 扩展
-- 用途：承接领导层首页 11 项 KPI 弹窗、专题弹窗、首页专题面板的结构化 JSON 快照。
-- 说明：当前阶段保持前端接口结构稳定；后续可逐项替换为业务明细表实时聚合。

CREATE TABLE IF NOT EXISTS dashboard_kpi_detail_snapshot (
  indicator_code VARCHAR(20) PRIMARY KEY COMMENT 'KPI 编码，如 E01/S02/G03',
  detail_json JSON NOT NULL COMMENT '弹窗详情完整配置，兼容 KpiDetailConfig',
  data_version VARCHAR(30) NOT NULL DEFAULT 'V0.2',
  data_source VARCHAR(100) NOT NULL DEFAULT 'dashboard_payload_migration',
  published_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  CHECK (JSON_VALID(detail_json))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='领导层 KPI 详情弹窗快照';

CREATE TABLE IF NOT EXISTS dashboard_topic_snapshot (
  topic_key VARCHAR(50) PRIMARY KEY COMMENT '专题编码：carbon/monthly-report',
  detail_json JSON NOT NULL COMMENT '专题弹窗详情完整配置，含 topicData',
  data_version VARCHAR(30) NOT NULL DEFAULT 'V0.2',
  data_source VARCHAR(100) NOT NULL DEFAULT 'dashboard_payload_migration',
  published_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  CHECK (JSON_VALID(detail_json))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='领导层专题弹窗快照';

CREATE TABLE IF NOT EXISTS dashboard_panel_snapshot (
  panel_key VARCHAR(50) PRIMARY KEY COMMENT '面板编码：home-panels',
  panel_json JSON NOT NULL COMMENT '首页右侧专题、GIS、时间线等组合数据',
  data_version VARCHAR(30) NOT NULL DEFAULT 'V0.2',
  data_source VARCHAR(100) NOT NULL DEFAULT 'dashboard_payload_migration',
  published_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  CHECK (JSON_VALID(panel_json))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='领导层首页面板快照';

