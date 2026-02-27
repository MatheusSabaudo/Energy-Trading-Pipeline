-- postgres/silver/data_verify.sql
-- Silver Layer - Data Verification

\c solar_data;

-- ============================================================
-- SILVER LAYER VERIFICATION
-- ============================================================

SELECT '==================================================' as line;
SELECT 'SILVER LAYER DATA VERIFICATION' as title;
SELECT '==================================================' as line;

-- ============================================================
-- 1. ROW COUNTS COMPARISON (Bronze vs Silver)
-- ============================================================
SELECT '1. BRONZE VS SILVER ROW COUNTS' as section;

SELECT 
    'weather_data' as source,
    (SELECT COUNT(*) FROM weather_data) as bronze_count,
    (SELECT COUNT(*) FROM silver_weather) as silver_count,
    CASE 
        WHEN (SELECT COUNT(*) FROM weather_data) = (SELECT COUNT(*) FROM silver_weather) 
        THEN '✅ MATCH'
        ELSE '❌ MISMATCH'
    END as status
UNION ALL
SELECT 
    'solar_panel_readings',
    (SELECT COUNT(*) FROM solar_panel_readings),
    (SELECT COUNT(*) FROM silver_solar),
    CASE 
        WHEN (SELECT COUNT(*) FROM solar_panel_readings) = (SELECT COUNT(*) FROM silver_solar) 
        THEN '✅ MATCH'
        ELSE '❌ MISMATCH'
    END;

-- ============================================================
-- 2. SILVER WEATHER QUALITY
-- ============================================================
SELECT '2. SILVER WEATHER QUALITY' as section;

SELECT 
    COUNT(*) as total_records,
    COUNT(CASE WHEN is_valid THEN 1 END) as valid_records,
    COUNT(CASE WHEN NOT is_valid THEN 1 END) as invalid_records,
    ROUND(100.0 * COUNT(CASE WHEN is_valid THEN 1 END) / COUNT(*), 2) as quality_pct,
    COUNT(DISTINCT temperature_category) as temp_categories,
    COUNT(DISTINCT sky_condition) as sky_categories,
    COUNT(DISTINCT uv_category) as uv_categories
FROM silver_weather;

-- ============================================================
-- 3. SILVER SOLAR QUALITY
-- ============================================================
SELECT '3. SILVER SOLAR QUALITY' as section;

SELECT 
    COUNT(*) as total_records,
    COUNT(CASE WHEN is_valid THEN 1 END) as valid_records,
    COUNT(CASE WHEN NOT is_valid THEN 1 END) as invalid_records,
    ROUND(100.0 * COUNT(CASE WHEN is_valid THEN 1 END) / COUNT(*), 2) as quality_pct,
    COUNT(DISTINCT performance_category) as performance_categories,
    AVG(efficiency_ratio) as avg_efficiency,
    MIN(efficiency_ratio) as min_efficiency,
    MAX(efficiency_ratio) as max_efficiency
FROM silver_solar;

-- ============================================================
-- 4. SILVER WEATHER CATEGORY DISTRIBUTION
-- ============================================================
SELECT '4. WEATHER CATEGORY DISTRIBUTION' as section;

SELECT 
    'Temperature' as category_type,
    temperature_category as category,
    COUNT(*) as count,
    ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER(), 2) as percentage
FROM silver_weather
GROUP BY temperature_category
ORDER BY count DESC;

SELECT 
    'Sky Condition' as category_type,
    sky_condition as category,
    COUNT(*) as count,
    ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER(), 2) as percentage
FROM silver_weather
GROUP BY sky_condition
ORDER BY count DESC;

-- ============================================================
-- 5. SILVER SOLAR PERFORMANCE DISTRIBUTION
-- ============================================================
SELECT '5. SOLAR PERFORMANCE DISTRIBUTION' as section;

SELECT 
    performance_category,
    COUNT(*) as readings,
    ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER(), 2) as percentage,
    AVG(production_kw) as avg_production,
    AVG(efficiency_ratio) as avg_efficiency
FROM silver_solar
GROUP BY performance_category
ORDER BY 
    CASE performance_category
        WHEN 'Excellent' THEN 1
        WHEN 'Good' THEN 2
        WHEN 'Fair' THEN 3
        WHEN 'Poor' THEN 4
        ELSE 5
    END;

-- ============================================================
-- 6. INVALID RECORDS ANALYSIS
-- ============================================================
SELECT '6. INVALID RECORDS DETAIL' as section;

-- Weather invalid records
SELECT 
    'weather' as source,
    COUNT(*) as count,
    ROUND(100.0 * COUNT(*) / (SELECT COUNT(*) FROM silver_weather), 2) as percentage
FROM silver_weather
WHERE NOT is_valid;

-- Solar invalid records by reason
SELECT 
    CASE 
        WHEN production_kw < 0 THEN 'Negative production'
        WHEN temperature_c < -30 OR temperature_c > 60 THEN 'Temperature out of range'
        WHEN cloud_factor < 0 OR cloud_factor > 1 THEN 'Invalid cloud factor'
        WHEN temp_efficiency < 0.5 OR temp_efficiency > 1.5 THEN 'Invalid efficiency'
        ELSE 'Other'
    END as reason,
    COUNT(*) as count
FROM silver_solar
WHERE NOT is_valid
GROUP BY reason
ORDER BY count DESC;

-- ============================================================
-- 7. TIME COVERAGE
-- ============================================================
SELECT '7. TIME COVERAGE' as section;

SELECT 
    'silver_weather' as table_name,
    MIN(timestamp) as earliest,
    MAX(timestamp) as latest,
    EXTRACT(DAY FROM MAX(timestamp) - MIN(timestamp)) as days_covered
FROM silver_weather
UNION ALL
SELECT 
    'silver_solar',
    MIN(timestamp),
    MAX(timestamp),
    EXTRACT(DAY FROM MAX(timestamp) - MIN(timestamp))
FROM silver_solar;

-- ============================================================
-- 8. FINAL VERDICT
-- ============================================================
SELECT '==================================================' as line;
SELECT 'SILVER LAYER VERDICT' as verdict;
SELECT '==================================================' as line;

WITH quality_check AS (
    SELECT 
        COUNT(CASE WHEN is_valid THEN 1 END) * 1.0 / COUNT(*) as weather_quality
    FROM silver_weather
),
solar_quality AS (
    SELECT 
        COUNT(CASE WHEN is_valid THEN 1 END) * 1.0 / COUNT(*) as solar_quality
    FROM silver_solar
)
SELECT 
    CASE 
        WHEN (SELECT weather_quality FROM quality_check) > 0.95 
             AND (SELECT solar_quality FROM solar_quality) > 0.95
        THEN '✅ EXCELLENT - Data quality >95% in both tables'
        WHEN (SELECT weather_quality FROM quality_check) > 0.8 
             AND (SELECT solar_quality FROM solar_quality) > 0.8
        THEN '⚠️ GOOD - Data quality >80% in both tables'
        ELSE '❌ POOR - Data quality below 80% in one or more tables'
    END as data_quality_verdict,
    CONCAT(
        'Weather: ', ROUND((SELECT weather_quality * 100 FROM quality_check), 1), '%, ',
        'Solar: ', ROUND((SELECT solar_quality * 100 FROM solar_quality), 1), '%'
    ) as quality_percentages;

SELECT '==================================================' as line;