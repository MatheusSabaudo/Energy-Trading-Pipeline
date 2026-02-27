-- postgres/bronze/data_verify.sql
-- Bronze Layer - Data Verification

\c solar_data;

-- ============================================================
-- BRONZE LAYER VERIFICATION
-- ============================================================

SELECT '==================================================' as line;
SELECT 'BRONZE LAYER DATA VERIFICATION' as title;
SELECT '==================================================' as line;

-- ============================================================
-- 1. BASIC ROW COUNTS
-- ============================================================
SELECT '1. ROW COUNTS' as section;

SELECT 
    'weather_data' as table_name,
    COUNT(*) as row_count,
    MIN(timestamp) as earliest_record,
    MAX(timestamp) as latest_record
FROM weather_data
UNION ALL
SELECT 
    'solar_panel_readings',
    COUNT(*),
    MIN(timestamp),
    MAX(timestamp)
FROM solar_panel_readings;

-- ============================================================
-- 2. DATA QUALITY CHECKS - Weather Data
-- ============================================================
SELECT '2. WEATHER DATA QUALITY' as section;

SELECT
    COUNT(*) as total_records,
    COUNT(CASE WHEN temperature IS NULL THEN 1 END) as null_temperature,
    COUNT(CASE WHEN humidity IS NULL THEN 1 END) as null_humidity,
    COUNT(CASE WHEN temperature < -30 OR temperature > 50 THEN 1 END) as out_of_range_temp,
    COUNT(CASE WHEN humidity < 0 OR humidity > 100 THEN 1 END) as invalid_humidity,
    COUNT(CASE WHEN cloud_cover < 0 OR cloud_cover > 100 THEN 1 END) as invalid_cloud_cover
FROM weather_data;

-- ============================================================
-- 3. DATA QUALITY CHECKS - Solar Data
-- ============================================================
SELECT '3. SOLAR DATA QUALITY' as section;

SELECT
    COUNT(*) as total_records,
    COUNT(DISTINCT panel_id) as unique_panels,
    COUNT(CASE WHEN production_kw IS NULL THEN 1 END) as null_production,
    COUNT(CASE WHEN production_kw < 0 THEN 1 END) as negative_production,
    COUNT(CASE WHEN temperature_c < -30 OR temperature_c > 60 THEN 1 END) as out_of_range_temp,
    COUNT(CASE WHEN cloud_factor < 0 OR cloud_factor > 1 THEN 1 END) as invalid_cloud_factor,
    COUNT(CASE WHEN temp_efficiency < 0.5 OR temp_efficiency > 1.5 THEN 1 END) as invalid_efficiency
FROM solar_panel_readings;

-- ============================================================
-- 4. PANEL SUMMARY
-- ============================================================
SELECT '4. PANEL SUMMARY' as section;

SELECT 
    panel_id,
    COUNT(*) as readings,
    MIN(timestamp) as first_seen,
    MAX(timestamp) as last_seen,
    AVG(production_kw) as avg_production,
    MIN(production_kw) as min_production,
    MAX(production_kw) as max_production
FROM solar_panel_readings
GROUP BY panel_id
ORDER BY panel_id;

-- ============================================================
-- 5. CITY SUMMARY (Weather)
-- ============================================================
SELECT '5. WEATHER BY CITY' as section;

SELECT 
    city,
    COUNT(*) as readings,
    AVG(temperature) as avg_temp,
    MIN(temperature) as min_temp,
    MAX(temperature) as max_temp,
    AVG(humidity) as avg_humidity
FROM weather_data
GROUP BY city;

-- ============================================================
-- 6. DUPLICATE CHECK
-- ============================================================
SELECT '6. DUPLICATE CHECK' as section;

SELECT 
    'weather_data' as table_name,
    COUNT(*) - COUNT(DISTINCT (timestamp, city)) as potential_duplicates
FROM weather_data
UNION ALL
SELECT 
    'solar_panel_readings',
    COUNT(*) - COUNT(DISTINCT event_id)
FROM solar_panel_readings;

-- ============================================================
-- 7. HOURLY DISTRIBUTION
-- ============================================================
SELECT '7. HOURLY DISTRIBUTION (Solar)' as section;

SELECT 
    EXTRACT(HOUR FROM timestamp) as hour_of_day,
    COUNT(*) as readings,
    AVG(production_kw) as avg_production
FROM solar_panel_readings
GROUP BY EXTRACT(HOUR FROM timestamp)
ORDER BY hour_of_day;

-- ============================================================
-- 8. VERIFICATION SUMMARY
-- ============================================================
SELECT '==================================================' as line;
SELECT 'VERIFICATION SUMMARY' as summary;
SELECT '==================================================' as line;

WITH counts AS (
    SELECT 'weather_data' as name, COUNT(*) as count FROM weather_data
    UNION ALL
    SELECT 'solar_panel_readings', COUNT(*) FROM solar_panel_readings
)
SELECT 
    CASE 
        WHEN MIN(count) > 0 THEN '✅ PASS - All tables have data'
        ELSE '❌ FAIL - Some tables are empty'
    END as data_presence_check,
    CONCAT('Total records: ', SUM(count)) as total_records
FROM counts;

SELECT '==================================================' as line;