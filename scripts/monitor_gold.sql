USE EnergyTradingPipeline;
GO

-- ============================================================
-- GOLD LAYER MONITOR - Pipeline Health Dashboard
-- ============================================================

PRINT '============================================================';
PRINT 'GOLD LAYER MONITOR - PIPELINE HEALTH';
PRINT '============================================================';
PRINT CAST(GETDATE() AS VARCHAR) + ' - Current Time';
GO

-- ============================================================
-- 1. DATA FRESHNESS CHECK
-- ============================================================
PRINT '';
PRINT '1. DATA FRESHNESS';
PRINT '------------------------------------------------------------';

DECLARE @hours_since_last_gold INT;
DECLARE @last_gold_update DATETIME2;

SELECT @last_gold_update = MAX(report_hour) FROM gold.hourly_system_stats;
SET @hours_since_last_gold = DATEDIFF(HOUR, @last_gold_update, GETDATE());

PRINT 'Last Gold Update: ' + ISNULL(CAST(@last_gold_update AS VARCHAR), 'No data');
PRINT 'Hours since last update: ' + ISNULL(CAST(@hours_since_last_gold AS VARCHAR), 'N/A');

IF @hours_since_last_gold <= 1
    PRINT 'STATUS: REAL-TIME (Updated within last hour)'
ELSE IF @hours_since_last_gold <= 6
    PRINT 'STATUS: SLIGHT DELAY (Updated within 6 hours)'
ELSE IF @hours_since_last_gold <= 24
    PRINT 'STATUS: BATCH MODE (Updated within 24 hours)'
ELSE
    PRINT 'STATUS: STALE DATA (No update for over 24 hours)';
GO

-- ============================================================
-- 2. ACTIVE ANOMALIES
-- ============================================================
PRINT '';
PRINT '2. ACTIVE ANOMALIES';
PRINT '------------------------------------------------------------';

IF EXISTS (SELECT 1 FROM gold.anomaly_log WHERE resolution_status = 'Open')
BEGIN
    SELECT 
        severity,
        COUNT(*) as open_alerts
    FROM gold.anomaly_log
    WHERE resolution_status = 'Open'
    GROUP BY severity
    ORDER BY 
        CASE severity 
            WHEN 'Critical' THEN 1 
            WHEN 'Warning' THEN 2 
            ELSE 3 
        END;
END
ELSE
    PRINT 'No active anomalies - System healthy';
GO

-- ============================================================
-- 3. DATA QUALITY TREND (LAST 7 DAYS)
-- ============================================================
PRINT '';
PRINT '3. DATA QUALITY TREND - LAST 7 DAYS';
PRINT '------------------------------------------------------------';

SELECT TOP 7
    report_date,
    AVG(data_quality_pct) as avg_quality_pct,
    SUM(invalid_readings) as total_invalid,
    SUM(valid_readings) as total_valid
FROM gold.daily_panel_performance
WHERE report_date >= DATEADD(DAY, -7, GETDATE())
GROUP BY report_date
ORDER BY report_date DESC;

-- Quality threshold check
IF EXISTS (
    SELECT 1 
    FROM gold.daily_panel_performance
    WHERE report_date = DATEADD(DAY, -1, GETDATE())
    AND data_quality_pct < 95
)
    PRINT 'WARNING: Data quality below 95% threshold yesterday';
ELSE
    PRINT 'Data quality above 95% threshold (yesterday)';
GO

-- ============================================================
-- 4. PANEL HEALTH SUMMARY
-- ============================================================
PRINT '';
PRINT '4. PANEL HEALTH SUMMARY';
PRINT '------------------------------------------------------------';

SELECT 
    COUNT(DISTINCT panel_id) as total_panels,
    COUNT(DISTINCT CASE WHEN is_valid = 0 THEN panel_id END) as panels_with_issues,
    CAST(100.0 * COUNT(DISTINCT CASE WHEN is_valid = 0 THEN panel_id END) / 
         NULLIF(COUNT(DISTINCT panel_id), 0) AS DECIMAL(5,2)) as pct_panels_with_issues
FROM silver.solar_data
WHERE timestamp >= DATEADD(DAY, -1, GETDATE());

-- List problematic panels
IF EXISTS (SELECT 1 FROM silver.solar_data WHERE timestamp >= DATEADD(DAY, -1, GETDATE()) AND is_valid = 0)
BEGIN
    PRINT '';
    PRINT 'Problematic panels in last 24h:';
    SELECT DISTINCT 
        s.panel_id,
        COUNT(*) as issue_count,
        MAX(s.quality_issues) as sample_issue
    FROM silver.solar_data s
    WHERE s.timestamp >= DATEADD(DAY, -1, GETDATE())
      AND s.is_valid = 0
    GROUP BY s.panel_id
    ORDER BY issue_count DESC;
END
ELSE
    PRINT 'No panel issues in last 24h';
GO

-- ============================================================
-- 5. PRODUCTION VS EXPECTED (TODAY)
-- ============================================================
PRINT '';
PRINT '5. TODAY''S PRODUCTION VS EXPECTED';
PRINT '------------------------------------------------------------';

IF EXISTS (SELECT 1 FROM gold.daily_panel_performance WHERE report_date = CAST(GETDATE() AS DATE))
BEGIN
    SELECT 
        d.panel_id,
        d.total_production_kwh as actual,
        p.expected_efficiency * 24 * p.panel_power_kw as expected_max,
        CAST(100.0 * d.total_production_kwh / NULLIF(p.expected_efficiency * 24 * p.panel_power_kw, 0) AS DECIMAL(5,2)) as pct_of_expected
    FROM gold.daily_panel_performance d
    JOIN gold.panel_master p ON d.panel_id = p.panel_id
    WHERE d.report_date = CAST(GETDATE() AS DATE)
    ORDER BY pct_of_expected DESC;
END
ELSE
    PRINT 'No data available for today yet';
GO

-- ============================================================
-- 6. PIPELINE VOLUME METRICS
-- ============================================================
PRINT '';
PRINT '6. PIPELINE VOLUME - LAST 24 HOURS';
PRINT '------------------------------------------------------------';

SELECT 
    'Bronze' as layer,
    COUNT(*) as record_count
FROM bronze.api_data
WHERE ingestion_time >= DATEADD(DAY, -1, GETDATE())
UNION ALL
SELECT 
    'Silver',
    COUNT(*)
FROM silver.solar_data
WHERE timestamp >= DATEADD(DAY, -1, GETDATE())
UNION ALL
SELECT 
    'Gold (Hourly)',
    COUNT(*)
FROM gold.hourly_system_stats
WHERE report_hour >= DATEADD(DAY, -1, GETDATE());
GO

-- ============================================================
-- 7. HOURLY PRODUCTION PATTERN (LAST 24H)
-- ============================================================
PRINT '';
PRINT '7. HOURLY PRODUCTION PATTERN - LAST 24H';
PRINT '------------------------------------------------------------';

SELECT 
    DATEPART(HOUR, report_hour) as hour_of_day,
    AVG(total_production_kwh) as avg_production,
    AVG(active_panels) as avg_active_panels
FROM gold.hourly_system_stats
WHERE report_hour >= DATEADD(DAY, -1, GETDATE())
GROUP BY DATEPART(HOUR, report_hour)
ORDER BY hour_of_day;
GO

-- ============================================================
-- 8. MONTHLY PROGRESS
-- ============================================================
PRINT '';
PRINT '8. MONTHLY PROGRESS';
PRINT '------------------------------------------------------------';

SELECT TOP 3
    report_year,
    report_month,
    report_month_name,
    total_production_kwh,
    avg_daily_production,
    overall_data_quality
FROM gold.monthly_kpis
ORDER BY report_year DESC, report_month DESC;
GO

-- ============================================================
-- 9. RECENT ANOMALIES DETAIL
-- ============================================================
PRINT '';
PRINT '9. RECENT ANOMALIES (LAST 24H)';
PRINT '------------------------------------------------------------';

IF EXISTS (SELECT 1 FROM gold.anomaly_log WHERE anomaly_date >= DATEADD(DAY, -1, GETDATE()))
BEGIN
    SELECT TOP 10
        anomaly_date,
        panel_id,
        anomaly_type,
        severity,
        deviation_percentage,
        weather_conditions,
        resolution_status
    FROM gold.anomaly_log
    WHERE anomaly_date >= DATEADD(DAY, -1, GETDATE())
    ORDER BY 
        CASE severity 
            WHEN 'Critical' THEN 1 
            WHEN 'Warning' THEN 2 
            ELSE 3 
        END,
        deviation_percentage DESC;
END
ELSE
    PRINT 'No anomalies in last 24h';
GO

-- ============================================================
-- 10. OVERALL HEALTH SCORE
-- ============================================================
PRINT '';
PRINT '============================================================';
PRINT 'OVERALL PIPELINE HEALTH SCORE';
PRINT '============================================================';

DECLARE @health_score INT = 100;
DECLARE @issues_found INT = 0;
DECLARE @last_update_check INT;
DECLARE @critical_anomalies INT;
DECLARE @yesterday_quality DECIMAL(5,2);

-- Get values for checks
SELECT @last_update_check = DATEDIFF(HOUR, MAX(report_hour), GETDATE()) 
FROM gold.hourly_system_stats;

SELECT @critical_anomalies = COUNT(*) 
FROM gold.anomaly_log 
WHERE severity = 'Critical' AND resolution_status = 'Open';

SELECT @yesterday_quality = AVG(data_quality_pct)
FROM gold.daily_panel_performance
WHERE report_date = DATEADD(DAY, -1, GETDATE());

-- Check 1: Data freshness
IF @last_update_check > 24
BEGIN
    SET @health_score = @health_score - 30;
    SET @issues_found = @issues_found + 1;
    PRINT 'CRITICAL: No data for over 24 hours (-30)';
END
ELSE IF @last_update_check > 6
BEGIN
    SET @health_score = @health_score - 10;
    PRINT 'WARNING: Data delay > 6 hours (-10)';
END

-- Check 2: Active critical anomalies
IF @critical_anomalies > 0
BEGIN
    SET @health_score = @health_score - (20 * @critical_anomalies);
    SET @issues_found = @issues_found + 1;
    PRINT 'CRITICAL: ' + CAST(@critical_anomalies AS VARCHAR) + ' open critical anomalies (-' + CAST(20 * @critical_anomalies AS VARCHAR) + ')';
END

-- Check 3: Data quality
IF @yesterday_quality < 90
BEGIN
    SET @health_score = @health_score - 15;
    PRINT 'WARNING: Low data quality yesterday (' + CAST(@yesterday_quality AS VARCHAR) + '%) (-15)';
END

-- Check 4: Panel issues
IF EXISTS (
    SELECT 1 FROM silver.solar_data
    WHERE timestamp >= DATEADD(DAY, -1, GETDATE())
    AND is_valid = 0
    HAVING COUNT(*) > 10
)
BEGIN
    SET @health_score = @health_score - 10;
    PRINT 'WARNING: Multiple invalid readings in last 24h (-10)';
END

-- Check 5: Missing panels
IF EXISTS (
    SELECT p.panel_id 
    FROM gold.panel_master p
    LEFT JOIN silver.solar_data s ON p.panel_id = s.panel_id 
        AND s.timestamp >= DATEADD(HOUR, -1, GETDATE())
    WHERE s.panel_id IS NULL
)
BEGIN
    SET @health_score = @health_score - 15;
    SET @issues_found = @issues_found + 1;
    PRINT 'CRITICAL: Some panels not reporting in last hour (-15)';
END

-- Final score
PRINT '';
PRINT '============================================================';
PRINT 'HEALTH SCORE: ' + CAST(@health_score AS VARCHAR) + '/100';

IF @health_score >= 90
    PRINT 'VERDICT: EXCELLENT - Pipeline healthy';
ELSE IF @health_score >= 70
    PRINT 'VERDICT: FAIR - Minor issues to address';
ELSE
    PRINT 'VERDICT: CRITICAL - Immediate attention required';

PRINT '============================================================';
GO