-- Construction-period E01 data must not precede the unified construction start.
SET @construction_start = TIMESTAMP('2026-05-08 00:00:00');

SET @time_failures = (
    SELECT COUNT(*) FROM e01_monitor_point
    WHERE effective_from < @construction_start
      AND data_nature <> 'background'
) + (
    SELECT COUNT(*) FROM e01_monitor_plan
    WHERE effective_at < @construction_start
      AND data_nature <> 'background'
) + (
    SELECT COUNT(*) FROM e01_monitor_batch
    WHERE sample_start_at < @construction_start
      AND data_nature <> 'background'
) + (
    SELECT COUNT(*) FROM e01_monitor_sample
    WHERE sampled_at < @construction_start
      AND data_nature <> 'background'
) + (
    SELECT COUNT(*)
    FROM e01_monitor_sample s
    JOIN e01_monitor_point p ON p.id = s.point_id
    WHERE s.sampled_at < p.effective_from
) + (
    SELECT COUNT(*)
    FROM e01_monitor_batch b
    WHERE b.sample_end_at < b.sample_start_at
       OR b.report_issued_at < b.sample_end_at
       OR b.received_at < b.report_issued_at
) + (
    SELECT COUNT(*)
    FROM e01_exceed_event e
    JOIN e01_factor_result r ON r.id = e.original_result_id
    JOIN e01_monitor_sample s ON s.id = r.sample_id
    WHERE e.first_exceeded_at < s.sampled_at
       OR e.first_exceeded_at < @construction_start
) + (
    SELECT COUNT(*)
    FROM e01_rectification_round rr
    JOIN e01_exceed_event e ON e.id = rr.event_id
    WHERE rr.started_at < e.first_exceeded_at
) + (
    SELECT COUNT(*)
    FROM e01_retest_round rt
    JOIN e01_exceed_event e ON e.id = rt.event_id
    WHERE rt.requested_at < e.first_exceeded_at
       OR rt.actual_sample_at < rt.requested_at
       OR rt.reviewed_at < rt.actual_sample_at
) + (
    SELECT COUNT(*)
    FROM e01_exceed_event e
    WHERE e.closure_confirmed_at IS NOT NULL
      AND e.closure_confirmed_at < e.first_exceeded_at
);

SET @time_gate_sql = IF(
    @time_failures = 0,
    'SELECT ''E01_TIME_CONSISTENCY_PASS'' AS result',
    CONCAT(
        'SIGNAL SQLSTATE ''45000'' SET MESSAGE_TEXT = ''E01 construction time consistency failed: ',
        @time_failures,
        ' issue(s)'''
    )
);
PREPARE stmt_time_gate FROM @time_gate_sql;
EXECUTE stmt_time_gate;
DEALLOCATE PREPARE stmt_time_gate;
