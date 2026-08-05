-- ============================================================================
-- V1_1_042__e01_water_point_near_source_zone.sql
-- Demo only: move WATER monitor 914001 (and synced object 912001) to a WGS84
-- point just outside 水源保护区1 polygon edge, offset toward TJ-1 / 1标段 corridor.
-- 水源保护区1 is closer to section-1 than 水源保护区2 (~0.104° vs ~0.117°).
-- Chosen: lon=109.64732310, lat=24.42328704 (outside polygon, toward corridor).
-- ============================================================================

UPDATE e01_monitor_point
SET longitude = 109.64732310,
    latitude = 24.42328704,
    coordinate_system = 'WGS84',
    coordinate_source_type = 'GIS_ALIGNMENT',
    updated_at = CURRENT_TIMESTAMP(6)
WHERE id = 914001 AND is_demo = 1 AND data_nature = 'demo';

UPDATE project_engineering_object
SET longitude = 109.64732310,
    latitude = 24.42328704
WHERE id = 912001 AND is_demo = 1 AND data_nature = 'demo';
