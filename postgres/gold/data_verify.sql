-- postgres/gold/data_verify.sql
-- Gold Layer - Data Verification

\c solar_data;

-- ============================================================
-- GOLD LAYER VERIFICATION
-- ============================================================

SELECT '==================================================' as line;
SELECT 'GOLD LAYER DATA VERIFICATION' as title;
SELECT '==================================================' as line;

-- ============================================================
-- 1. GOLD TABLES ROW COUNTS
-- ============================================================
SELECT '1. GOLD TABLES ROW COUNTS' as section;

SELECT 
    'gold_daily_panel' as table_name,
    COUNT(*) as row_count
FROM gold_daily_panel
UNION ALL
SELECT 
    'gold_hourly_system',
    COUNT(*)
FROM gold_hourly_system
UNION ALL
SELECT 
    'gold_weather_impact',
    COUNT(*)
FROM gold_weather_impact
UNION ALL
SELECT 
    'gold_monthly_kpis',
    COUNT(*)
FROM gold_monthly_kpis
UNION ALL
SELECT 
    'gold_anomalies',
    COUNT(*)
FROM gold_anomalies;

-- ============================================================
-- 2. DAILY PANEL PERFORMANCE SUMMARY
-- ============================================================
SELECT '2. DAILY PANEL PERFORMANCE' as section;

SELECT 
    date,
    COUNT(DISTINCT panel_id) as panels_reporting,
    ROUND(SUM(total_production_kwh)::numeric, 2) as total_production,
    ROUND(AVG(avg_efficiency)::numeric, 3) as avg_efficiency,
    ROUND(AVG(data_quality_pct)::numeric, 1) as avg_quality
FROM gold_daily_panel
GROUP BY date
ORDER BY date DESC
LIMIT 7;

-- ============================================================
-- 3. TOP PERFORMING PANELS (Last 7 days)
-- ============================================================
SELECT '3. TOP 5 PERFORMING PANELS (Last 7 days)' as section;

SELECT 
    panel_id,
    SUM(total_production_kwh) as total_7day_production,
    ROUND(AVG(avg_efficiency)::numeric, 3) as avg_efficiency,
    ROUND(AVG(data_quality_pct)::numeric, 1) as data_quality
FROM gold_daily_panel
WHERE date >= CURRENT_DATE - 7
GROUP BY panel_id
ORDER BY total_7day_production DESC
LIMIT 5;

-- ============================================================
-- 4. BOTTOM PERFORMING PANELS (Last 7 days)
-- ============================================================
SELECT '4. BOTTOM 5 PERFORMING PANELS (Last 7 days)' as section;

SELECT 
    panel_id,
    SUM(total_production_kwh) as total_7day_production,
    ROUND(AVG(avg_efficiency)::numeric, 3) as avg_efficiency,
    ROUND(AVG(data_quality_pct)::numeric, 1) as data_quality
FROM gold_daily_panel
WHERE date >= CURRENT_DATE - 7
GROUP BY panel_id
ORDER BY total_7day_production ASC
LIMIT 5;

-- ============================================================
-- 5. HOURLY SYSTEM PERFORMANCE (Last 24h)
-- ============================================================
SELECT '5. HOURLY PERFORMANCE (Last 24h)' as section;

SELECT 
    hour,
    active_panels,
    ROUND(total_production_kw::numeric, 2) as total_kw,
    ROUND(avg_production_per_panel::numeric, 3) as avg_per_panel,
    ROUND(avg_system_efficiency::numeric, 3) as efficiency
FROM gold_hourly_system
WHERE hour >= NOW() - INTERVAL '24 hours'
ORDER BY hour DESC;

-- ============================================================
-- 6. WEATHER IMPACT ANALYSIS
-- ============================================================
SELECT '6. WEATHER IMPACT ON PRODUCTION' as section;

SELECT 
    sky_condition,
    COUNT(*) as samples,
    ROUND(AVG(avg_solar_production)::numeric, 3) as avg_production,
    ROUND(AVG(temperature)::numeric, 1) as avg_temperature,
    ROUND(AVG(cloud_cover)::numeric, 1) as avg_clouds
FROM gold_weather_impact
GROUP BY sky_condition
ORDER BY avg_production DESC;

-- ============================================================
-- 7. MONTHLY KPIs
-- ============================================================
SELECT '7. MONTHLY KPIs' as section;

SELECT 
    year,
    month,
    total_panels,
    ROUND(total_production_kwh::numeric, 2) as total_production_kwh,
    ROUND(avg_production_kw::numeric, 3) as avg_production_kw,
    ROUND(avg_efficiency::numeric, 3) as avg_efficiency,
    data_quality_pct
FROM gold_monthly_kpis
ORDER BY year DESC, month DESC;

-- ============================================================
-- 8. ACTIVE ANOMALIES
-- ============================================================
SELECT '8. ACTIVE ANOMALIES' as section;

SELECT 
    anomaly_type,
    severity,
    COUNT(*) as count,
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
-- 9. DATA COMPLETENESS CHECK
-- ============================================================
SELECT '9. DATA COMPLETENESS' as section;

WITH date_range AS (
    SELECT MIN(date) as first_date, MAX(date) as last_date FROM gold_daily_panel
)
SELECT 
    CONCAT(first_date, ' to ', last_date) as coverage_period,
    EXTRACT(DAY FROM last_date - first_date) + 1 as days_covered,
    (SELECT COUNT(DISTINCT date) FROM gold_daily_panel) as days_with_data
FROM date_range;

-- ============================================================
-- 10. GOLD LAYER VERDICT
-- ============================================================
SELECT '==================================================' as line;
SELECT 'GOLD LAYER VERDICT' as verdict;
SELECT '==================================================' as line;

WITH checks AS (
    SELECT 
        (SELECT COUNT(*) > 0 FROM gold_daily_panel) as has_daily,
        (SELECT COUNT(*) > 0 FROM gold_hourly_system) as has_hourly,
        (SELECT COUNT(*) > 0 FROM gold_monthly_kpis) as has_monthly,
        (SELECT COUNT(*) FROM gold_anomalies WHERE resolution_status = 'Open') as open_anomalies
)
SELECT 
    CASE 
        WHEN has_daily AND has_hourly AND has_monthly THEN '✅ PASS - All gold tables populated'
        ELSE '❌ FAIL - Some gold tables are empty'
    END as tables_check,
    CASE 
        WHEN open_anomalies = 0 THEN '✅ PASS - No open anomalies'
        WHEN open_anomalies < 5 THEN '⚠️ WARNING - ' || open_anomalies || ' open anomalies'
        ELSE '❌ CRITICAL - ' || open_anomalies || ' open anomalies require attention'
    END as anomalies_check
FROM checks;

SELECT '==================================================' as line;