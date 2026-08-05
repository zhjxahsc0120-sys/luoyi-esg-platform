-- Reuse the current GIS section features for E01 dashboard-to-map linkage.
-- Point coordinates remain the authoritative E01 coordinates; these IDs drive UI selection.
UPDATE project_engineering_object
SET gis_feature_id = CASE id
    WHEN 912001 THEN 'section-1-1'
    WHEN 912002 THEN 'section-2-1'
    WHEN 912003 THEN 'section-3-1'
    ELSE gis_feature_id
END
WHERE id IN (912001, 912002, 912003) AND is_demo = 1;

UPDATE e01_monitor_point
SET gis_feature_id = CASE id
    WHEN 914001 THEN 'section-1-1'
    WHEN 914002 THEN 'section-2-1'
    WHEN 914003 THEN 'section-3-1'
    WHEN 914004 THEN 'section-2-1'
    ELSE gis_feature_id
END
WHERE id IN (914001, 914002, 914003, 914004) AND is_demo = 1;
