USE EnergyTradingPipeline;
GO

-- ============================================================
-- SILVER LAYER DATA VERIFIER
-- ============================================================

PRINT '============================================================';
PRINT 'SILVER LAYER DATA VERIFICATION';
PRINT '============================================================';
GO

-- ============================================================
-- 1. BASIC ROW COUNTS
-- ============================================================
PRINT '';
PRINT '1. BASIC ROW COUNTS';
PRINT '------------------------------------------------------------';

DECLARE @total_rows INT;
DECLARE @distinct_events INT;
DECLARE @distinct_panels INT;
DECLARE @date_range_start DATETIME2;
DECLARE @date_range_end DATETIME2;

SELECT 
    @total_rows = COUNT(*),
    @distinct_events = COUNT(DISTINCT event_id),
    @distinct_panels = COUNT(DISTINCT panel_id),
    @date_range_start = MIN(timestamp),
    @date_range_end = MAX(timestamp)
FROM silver.solar_data;

PRINT 'Total rows: ' + ISNULL(CAST(@total_rows AS VARCHAR), '0');
PRINT 'Unique events: ' + ISNULL(CAST(@distinct_events AS VARCHAR), '0');
PRINT 'Unique panels: ' + ISNULL(CAST(@distinct_panels AS VARCHAR), '0');
PRINT 'Date range: ' + ISNULL(CAST(@date_range_start AS VARCHAR), 'N/A') + ' to ' + ISNULL(CAST(@date_range_end AS VARCHAR), 'N/A');

-- ============================================================
-- 2. DATA QUALITY CHECKS (continued in same batch)
-- ============================================================
PRINT '';
PRINT '2. DATA QUALITY CHECKS';
PRINT '------------------------------------------------------------';

DECLARE @valid_rows INT;
DECLARE @invalid_rows INT;
DECLARE @valid_pct DECIMAL(5,2);

SELECT 
    @valid_rows = SUM(CASE WHEN is_valid = 1 THEN 1 ELSE 0 END),
    @invalid_rows = SUM(CASE WHEN is_valid = 0 THEN 1 ELSE 0 END)
FROM silver.solar_data;

IF @total_rows > 0
    SET @valid_pct = (100.0 * @valid_rows / @total_rows);
ELSE
    SET @valid_pct = 0;

PRINT 'Valid rows: ' + ISNULL(CAST(@valid_rows AS VARCHAR), '0') + ' (' + ISNULL(CAST(ROUND(@valid_pct, 1) AS VARCHAR), '0') + '%)';
PRINT 'Invalid rows: ' + ISNULL(CAST(@invalid_rows AS VARCHAR), '0') + ' (' + ISNULL(CAST(ROUND(100.0 - @valid_pct, 1) AS VARCHAR), '0') + '%)';

IF @invalid_rows > 0
BEGIN
    PRINT '';
    PRINT 'Top quality issues:';
    SELECT TOP 5
        ISNULL(quality_issues, 'Unknown') as issue_type,
        COUNT(*) as occurrence,
        CAST(100.0 * COUNT(*) / @invalid_rows AS DECIMAL(5,1)) as percentage
    FROM silver.solar_data
    WHERE quality_issues IS NOT NULL AND quality_issues != ''
    GROUP BY quality_issues
    ORDER BY occurrence DESC;
END
ELSE
BEGIN
    PRINT 'No quality issues found';
END

-- ============================================================
-- 3. COLUMN COMPLETENESS
-- ============================================================
PRINT '';
PRINT '3. COLUMN COMPLETENESS (Non-Null %)';
PRINT '------------------------------------------------------------';

IF @total_rows > 0
BEGIN
    SELECT 
        'event_id' as column_name,
        CAST(100.0 * COUNT(*) / @total_rows AS DECIMAL(5,1)) as completeness_pct
    FROM silver.solar_data WHERE event_id IS NOT NULL
    UNION ALL
    SELECT 
        'timestamp',
        CAST(100.0 * COUNT(*) / @total_rows AS DECIMAL(5,1))
    FROM silver.solar_data WHERE timestamp IS NOT NULL
    UNION ALL
    SELECT 
        'panel_id',
        CAST(100.0 * COUNT(*) / @total_rows AS DECIMAL(5,1))
    FROM silver.solar_data WHERE panel_id IS NOT NULL
    UNION ALL
    SELECT 
        'panel_power_kw',
        CAST(100.0 * COUNT(*) / @total_rows AS DECIMAL(5,1))
    FROM silver.solar_data WHERE panel_power_kw IS NOT NULL
    UNION ALL
    SELECT 
        'production_kw',
        CAST(100.0 * COUNT(*) / @total_rows AS DECIMAL(5,1))
    FROM silver.solar_data WHERE production_kw IS NOT NULL
    UNION ALL
    SELECT 
        'temperature_c',
        CAST(100.0 * COUNT(*) / @total_rows AS DECIMAL(5,1))
    FROM silver.solar_data WHERE temperature_c IS NOT NULL
    ORDER BY completeness_pct DESC;
END
ELSE
    PRINT 'No data to analyze';
GO  -- Need GO here to start a new batch for the next sections

-- ============================================================
-- 4. DATA DISTRIBUTION CHECKS
-- ============================================================
PRINT '';
PRINT '4. DATA DISTRIBUTION';
PRINT '------------------------------------------------------------';

-- Production statistics
SELECT 
    'Production (kW)' as metric,
    MIN(production_kw) as min_value,
    MAX(production_kw) as max_value,
    AVG(production_kw) as avg_value,
    STDEV(production_kw) as std_dev
FROM silver.solar_data
WHERE production_kw IS NOT NULL;

-- Temperature statistics
SELECT 
    'Temperature (C)' as metric,
    MIN(temperature_c) as min_value,
    MAX(temperature_c) as max_value,
    AVG(temperature_c) as avg_value,
    STDEV(temperature_c) as std_dev
FROM silver.solar_data
WHERE temperature_c IS NOT NULL;

-- Efficiency ratio statistics
SELECT 
    'Efficiency Ratio' as metric,
    MIN(efficiency_ratio) as min_value,
    MAX(efficiency_ratio) as max_value,
    AVG(efficiency_ratio) as avg_value,
    STDEV(efficiency_ratio) as std_dev
FROM silver.solar_data
WHERE efficiency_ratio IS NOT NULL;
GO

-- ============================================================
-- 5. CLOUD CONDITION DISTRIBUTION
-- ============================================================
PRINT '';
PRINT '5. CLOUD CONDITION DISTRIBUTION';
PRINT '------------------------------------------------------------';

DECLARE @total_rows2 INT;
SELECT @total_rows2 = COUNT(*) FROM silver.solar_data;

SELECT 
    ISNULL(cloud_condition, 'Unknown') as cloud_condition,
    COUNT(*) as row_count,
    CAST(100.0 * COUNT(*) / @total_rows2 AS DECIMAL(5,1)) as percentage,
    AVG(production_kw) as avg_production,
    AVG(efficiency_ratio) as avg_efficiency
FROM silver.solar_data
GROUP BY cloud_condition
ORDER BY row_count DESC;
GO

-- ============================================================
-- 6. PANEL PERFORMANCE SUMMARY
-- ============================================================
PRINT '';
PRINT '6. TOP 5 BEST PERFORMING PANELS';
PRINT '------------------------------------------------------------';

SELECT TOP 5
    panel_id,
    COUNT(*) as readings,
    AVG(production_kw) as avg_production,
    AVG(efficiency_ratio) as avg_efficiency,
    SUM(CASE WHEN is_valid = 0 THEN 1 ELSE 0 END) as quality_issues
FROM silver.solar_data
GROUP BY panel_id
ORDER BY avg_production DESC;
GO

PRINT '';
PRINT 'BOTTOM 5 WORST PERFORMING PANELS';
PRINT '------------------------------------------------------------';

SELECT TOP 5
    panel_id,
    COUNT(*) as readings,
    AVG(production_kw) as avg_production,
    AVG(efficiency_ratio) as avg_efficiency,
    SUM(CASE WHEN is_valid = 0 THEN 1 ELSE 0 END) as quality_issues
FROM silver.solar_data
GROUP BY panel_id
ORDER BY avg_production ASC;
GO

-- ============================================================
-- 7. HOURLY PATTERNS
-- ============================================================
PRINT '';
PRINT '7. PRODUCTION BY HOUR OF DAY';
PRINT '------------------------------------------------------------';

SELECT 
    ISNULL(CAST(production_hour AS VARCHAR), 'Unknown') as hour,
    COUNT(*) as readings,
    AVG(production_kw) as avg_production,
    MAX(production_kw) as peak_production,
    AVG(efficiency_ratio) as avg_efficiency
FROM silver.solar_data
WHERE is_valid = 1
GROUP BY production_hour
ORDER BY 
    CASE WHEN production_hour IS NULL THEN 1 ELSE 0 END,
    production_hour;
GO

-- ============================================================
-- 8. RECENT DATA CHECK
-- ============================================================
PRINT '';
PRINT '8. MOST RECENT 10 RECORDS';
PRINT '------------------------------------------------------------';

SELECT TOP 10
    timestamp,
    panel_id,
    production_kw,
    ISNULL(cloud_condition, 'Unknown') as cloud_condition,
    efficiency_ratio,
    CASE WHEN is_valid = 1 THEN 'Valid' ELSE 'Invalid' END as status,
    ISNULL(quality_issues, 'None') as quality_issues
FROM silver.solar_data
ORDER BY timestamp DESC;
GO

-- ============================================================
-- 9. FINAL VERDICT
-- ============================================================
PRINT '';
PRINT '============================================================';
PRINT 'VERIFICATION SUMMARY';
PRINT '============================================================';

DECLARE @total_rows3 INT;
DECLARE @valid_rows3 INT;
DECLARE @valid_pct3 DECIMAL(5,2);
DECLARE @issues_found INT = 0;
DECLARE @completeness_check INT;

SELECT @total_rows3 = COUNT(*) FROM silver.solar_data;
SELECT @valid_rows3 = COUNT(*) FROM silver.solar_data WHERE is_valid = 1;
SELECT @completeness_check = COUNT(*) FROM silver.solar_data WHERE panel_id IS NULL OR timestamp IS NULL OR event_id IS NULL;

IF @total_rows3 > 0
    SET @valid_pct3 = (100.0 * @valid_rows3 / @total_rows3);
ELSE
    SET @valid_pct3 = 0;

-- Check 1: Has data
IF @total_rows3 > 0 
    PRINT 'PASS: Silver layer contains data (' + CAST(@total_rows3 AS VARCHAR) + ' rows)'
ELSE
BEGIN
    PRINT 'FAIL: Silver layer is empty';
    SET @issues_found = @issues_found + 1;
END

-- Check 2: Data quality
IF @valid_pct3 > 95
    PRINT 'PASS: High data quality (' + CAST(ROUND(@valid_pct3, 1) AS VARCHAR) + '% valid)'
ELSE IF @valid_pct3 > 80
    PRINT 'WARNING: Moderate data quality (' + CAST(ROUND(@valid_pct3, 1) AS VARCHAR) + '% valid)'
ELSE
BEGIN
    PRINT 'FAIL: Poor data quality (' + CAST(ROUND(@valid_pct3, 1) AS VARCHAR) + '% valid)';
    SET @issues_found = @issues_found + 1;
END

-- Check 3: Completeness of key columns
IF @completeness_check = 0
    PRINT 'PASS: All required columns are complete'
ELSE
BEGIN
    PRINT 'FAIL: ' + CAST(@completeness_check AS VARCHAR) + ' rows missing required data';
    SET @issues_found = @issues_found + 1;
END

-- Final verdict
PRINT '';
PRINT '============================================================';
IF @issues_found = 0
    PRINT 'VERDICT: PASS - Silver layer data is healthy';
ELSE IF @issues_found = 1
    PRINT 'VERDICT: WARNING - Silver layer has 1 issue to review';
ELSE
    PRINT 'VERDICT: FAIL - Silver layer has ' + CAST(@issues_found AS VARCHAR) + ' issues to address';
PRINT '============================================================';
GO