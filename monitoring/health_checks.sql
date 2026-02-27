-- monitoring/health_checks.sql
-- Comprehensive health checks for the solar data pipeline
-- Run this periodically to monitor system health

-- ============================================================
-- HEALTH CHECK SUMMARY
-- ============================================================
SELECT '==================================================' as line;
SELECT 'SOLAR PIPELINE HEALTH CHECK' as title;
SELECT '==================================================' as line;
SELECT NOW() as check_time;
SELECT '==================================================' as line;

-- ============================================================
-- 1. DATA FRESHNESS CHECK
-- ============================================================
SELECT '\n1. DATA FRESHNESS' as section;
SELECT '--------------------------------------------------' as line;

WITH freshness AS (
    SELECT 
        'weather_data' as table_name,
        MAX(timestamp) as last_record,
        EXTRACT(EPOCH FROM (NOW() - MAX(timestamp)))/3600 as hours_ago
    FROM weather_data
    UNION ALL
    SELECT 
        'solar_panel_readings',
        MAX(timestamp),
        EXTRACT(EPOCH FROM (NOW() - MAX(timestamp)))/3600
    FROM solar_panel_readings
    UNION ALL
    SELECT 
        'silver_solar',
        MAX(timestamp),
        EXTRACT(EPOCH FROM (NOW() - MAX(timestamp)))/3600
    FROM silver_solar
)
SELECT 
    table_name,
    last_record,
    ROUND(hours_ago, 2) as hours_since_last_record,
    CASE 
        WHEN hours_ago < 1 THEN '✅ Real-time'
        WHEN hours_ago < 6 THEN '⚠️ Slight delay'
        WHEN hours_ago < 24 THEN '🔸 Batch mode'
        ELSE '❌ Stale data'
    END as status
FROM freshness
ORDER BY hours_ago;

-- ============================================================
-- 2. DATA VOLUME CHECK
-- ============================================================
SELECT '\n2. DATA VOLUME (LAST 24 HOURS)' as section;
SELECT '--------------------------------------------------' as line;

WITH volume AS (
    SELECT 
        'weather_data' as table_name,
        COUNT(*) as records_last_24h,
        COUNT(*) / 24.0 as avg_records_per_hour
    FROM weather_data
    WHERE timestamp > NOW() - INTERVAL '24 hours'
    UNION ALL
    SELECT 
        'solar_panel_readings',
        COUNT(*),
        COUNT(*) / 24.0
    FROM solar_panel_readings
    WHERE timestamp > NOW() - INTERVAL '24 hours'
    UNION ALL
    SELECT 
        'silver_solar',
        COUNT(*),
        COUNT(*) / 24.0
    FROM silver_solar
    WHERE timestamp > NOW() - INTERVAL '24 hours'
)
SELECT 
    table_name,
    records_last_24h,
    ROUND(avg_records_per_hour, 0) as avg_per_hour,
    CASE 
        WHEN records_last_24h = 0 THEN '❌ No data'
        WHEN avg_records_per_hour < 100 THEN '⚠️ Low volume'
        ELSE '✅ Normal'
    END as status
FROM volume
ORDER BY records_last_24h DESC;

-- ============================================================
-- 3. PANEL HEALTH CHECK
-- ============================================================
SELECT '\n3. PANEL HEALTH' as section;
SELECT '--------------------------------------------------' as line;

WITH panel_stats AS (
    SELECT 
        panel_id,
        COUNT(*) as total_readings,
        AVG(production_kw) as avg_production,
        MAX(timestamp) as last_seen,
        EXTRACT(EPOCH FROM (NOW() - MAX(timestamp)))/3600 as hours_offline
    FROM solar_panel_readings
    GROUP BY panel_id
)
SELECT 
    panel_id,
    total_readings,
    ROUND(avg_production, 2) as avg_production_kw,
    last_seen,
    CASE 
        WHEN hours_offline < 1 THEN '✅ Online'
        WHEN hours_offline < 6 THEN '⚠️ Intermittent'
        ELSE '❌ Offline'
    END as status
FROM panel_stats
ORDER BY 
    CASE 
        WHEN hours_offline < 1 THEN 1
        WHEN hours_offline < 6 THEN 2
        ELSE 3
    END,
    panel_id;

-- ============================================================
-- 4. ANOMALY SUMMARY
-- ============================================================
SELECT '\n4. ACTIVE ANOMALIES' as section;
SELECT '--------------------------------------------------' as line;

SELECT 
    anomaly_type,
    severity,
    COUNT(*) as count,
    MIN(anomaly_date) as oldest,
    MAX(anomaly_date) as latest,
    STRING_AGG(DISTINCT panel_id, ', ') as affected_panels
FROM gold_anomalies
WHERE resolution_status = 'Open'
GROUP BY anomaly_type, severity
ORDER BY 
    CASE severity
        WHEN 'Critical' THEN 1
        WHEN 'Warning' THEN 2
        ELSE 3
    END,
    count DESC;

-- ============================================================
-- 5. DATA QUALITY CHECK
-- ============================================================
SELECT '\n5. DATA QUALITY (LAST 7 DAYS)' as section;
SELECT '--------------------------------------------------' as line;

SELECT 
    date,
    AVG(data_quality_pct) as avg_quality,
    SUM(valid_readings) as total_valid,
    SUM(invalid_readings) as total_invalid,
    ROUND(100.0 * SUM(valid_readings) / NULLIF(SUM(valid_readings) + SUM(invalid_readings), 0), 2) as overall_quality
FROM gold_daily_panel
WHERE date >= CURRENT_DATE - 7
GROUP BY date
ORDER BY date DESC;

-- ============================================================
-- 6. SYSTEM PERFORMANCE (LAST 24 HOURS)
-- ============================================================
SELECT '\n6. HOURLY PERFORMANCE (LAST 24 HOURS)' as section;
SELECT '--------------------------------------------------' as line;

SELECT 
    DATE_TRUNC('hour', hour) as hour,
    active_panels,
    ROUND(total_production_kw, 2) as total_kw,
    ROUND(avg_production_per_panel, 3) as avg_per_panel,
    ROUND(avg_system_efficiency, 3) as efficiency,
    valid_readings
FROM gold_hourly_system
WHERE hour >= NOW() - INTERVAL '24 hours'
ORDER BY hour DESC
LIMIT 24;

-- ============================================================
-- 7. STORAGE USAGE
-- ============================================================
SELECT '\n7. TABLE SIZES' as section;
SELECT '--------------------------------------------------' as line;

SELECT 
    table_name,
    pg_size_pretty(pg_total_relation_size(table_name::regclass)) as total_size,
    pg_size_pretty(pg_relation_size(table_name::regclass)) as data_size,
    pg_size_pretty(pg_total_relation_size(table_name::regclass) - pg_relation_size(table_name::regclass)) as index_size,
    reltuples::bigint as approx_row_count
FROM (
    SELECT 'weather_data' as table_name UNION ALL
    SELECT 'solar_panel_readings' UNION ALL
    SELECT 'silver_weather' UNION ALL
    SELECT 'silver_solar' UNION ALL
    SELECT 'gold_daily_panel' UNION ALL
    SELECT 'gold_hourly_system' UNION ALL
    SELECT 'gold_monthly_kpis' UNION ALL
    SELECT 'gold_anomalies'
) tables
JOIN pg_class ON relname = table_name
JOIN pg_namespace ON relnamespace = pg_namespace.oid AND nspname = 'public'
ORDER BY pg_total_relation_size(table_name::regclass) DESC;

-- ============================================================
-- 8. PIPELINE LAG CHECK
-- ============================================================
SELECT '\n8. PIPELINE LAG (Bronze → Silver → Gold)' as section;
SELECT '--------------------------------------------------' as line;

WITH lag_check AS (
    SELECT 
        MAX(timestamp) as bronze_latest,
        (SELECT MAX(timestamp) FROM silver_solar) as silver_latest,
        (SELECT MAX(date) FROM gold_daily_panel) as gold_latest
    FROM solar_panel_readings
)
SELECT 
    bronze_latest,
    silver_latest,
    gold_latest,
    EXTRACT(EPOCH FROM (silver_latest - bronze_latest))/60 as bronze_to_silver_minutes,
    EXTRACT(EPOCH FROM (NOW() - gold_latest::timestamp))/3600 as gold_freshness_hours
FROM lag_check;

-- ============================================================
-- 9. FINAL HEALTH SCORE
-- ============================================================
SELECT '\n9. OVERALL HEALTH SCORE' as section;
SELECT '==================================================' as line;

WITH scores AS (
    -- Freshness score (30 points)
    SELECT 
        CASE 
            WHEN (SELECT MAX(timestamp) FROM solar_panel_readings) > NOW() - INTERVAL '1 hour' THEN 30
            WHEN (SELECT MAX(timestamp) FROM solar_panel_readings) > NOW() - INTERVAL '6 hours' THEN 20
            WHEN (SELECT MAX(timestamp) FROM solar_panel_readings) > NOW() - INTERVAL '24 hours' THEN 10
            ELSE 0
        END as freshness_score,
    
    -- Anomaly score (40 points)
    SELECT 
        GREATEST(0, 40 - (
            SELECT COUNT(*) * 5 FROM gold_anomalies 
            WHERE resolution_status = 'Open' AND severity = 'Critical'
        ) - (
            SELECT COUNT(*) * 2 FROM gold_anomalies 
            WHERE resolution_status = 'Open' AND severity = 'Warning'
        )) as anomaly_score,
    
    -- Data quality score (30 points)
    SELECT 
        CASE 
            WHEN AVG(data_quality_pct) > 98 THEN 30
            WHEN AVG(data_quality_pct) > 95 THEN 25
            WHEN AVG(data_quality_pct) > 90 THEN 20
            WHEN AVG(data_quality_pct) > 80 THEN 10
            ELSE 0
        END as quality_score
    FROM gold_daily_panel
    WHERE date >= CURRENT_DATE - 7
)
SELECT 
    freshness_score,
    anomaly_score,
    quality_score,
    (freshness_score + anomaly_score + quality_score) as total_score,
    CASE 
        WHEN (freshness_score + anomaly_score + quality_score) >= 90 THEN '✅ EXCELLENT'
        WHEN (freshness_score + anomaly_score + quality_score) >= 70 THEN '👍 GOOD'
        WHEN (freshness_score + anomaly_score + quality_score) >= 50 THEN '⚠️ FAIR'
        ELSE '❌ CRITICAL'
    END as health_status
FROM scores;

SELECT '==================================================' as line;
SELECT 'HEALTH CHECK COMPLETE' as message;
SELECT '==================================================' as line;