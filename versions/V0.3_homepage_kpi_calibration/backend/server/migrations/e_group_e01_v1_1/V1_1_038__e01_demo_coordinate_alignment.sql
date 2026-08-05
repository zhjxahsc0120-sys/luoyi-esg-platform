-- ============================================================================
-- V1_1_038__e01_demo_coordinate_alignment.sql
-- 将 E01 演示监测点坐标对齐到首页罗宜高速标段 GeoJSON 范围内（WGS84）
-- 不改统计口径、不覆盖非 demo 正式数据
-- ============================================================================

UPDATE e01_monitor_point
SET longitude = 109.77573460,
    latitude = 24.47807047,
    coordinate_system = 'WGS84',
    coordinate_source_type = 'GIS_ALIGNMENT',
    updated_at = CURRENT_TIMESTAMP(6)
WHERE id = 914001 AND is_demo = 1 AND data_nature = 'demo';

UPDATE e01_monitor_point
SET longitude = 109.68172938,
    latitude = 24.43146235,
    coordinate_system = 'WGS84',
    coordinate_source_type = 'GIS_ALIGNMENT',
    updated_at = CURRENT_TIMESTAMP(6)
WHERE id = 914002 AND is_demo = 1 AND data_nature = 'demo';

UPDATE e01_monitor_point
SET longitude = 109.54333615,
    latitude = 24.44165793,
    coordinate_system = 'WGS84',
    coordinate_source_type = 'GIS_ALIGNMENT',
    updated_at = CURRENT_TIMESTAMP(6)
WHERE id = 914003 AND is_demo = 1 AND data_nature = 'demo';

UPDATE e01_monitor_point
SET longitude = 109.69790000,
    latitude = 24.43578000,
    coordinate_system = 'WGS84',
    coordinate_source_type = 'GIS_ALIGNMENT',
    updated_at = CURRENT_TIMESTAMP(6)
WHERE id = 914004 AND is_demo = 1 AND data_nature = 'demo';

UPDATE project_engineering_object
SET longitude = 109.77573460,
    latitude = 24.47807047
WHERE id = 912001 AND is_demo = 1 AND data_nature = 'demo';

UPDATE project_engineering_object
SET longitude = 109.68172938,
    latitude = 24.43146235
WHERE id = 912002 AND is_demo = 1 AND data_nature = 'demo';

UPDATE project_engineering_object
SET longitude = 109.54333615,
    latitude = 24.44165793
WHERE id = 912003 AND is_demo = 1 AND data_nature = 'demo';
