USE EnergyTradingPipeline;
GO

-- ============================================================
-- GOLD LAYER LOAD - Hourly System Stats
-- ============================================================

PRINT 'STARTING GOLD HOURLY SYSTEM STATS LOAD';
GO

INSERT INTO gold.hourly_system_stats (
    report_hour,
    report_date,
    report_hour_of_day,
    total_production_kwh,
    avg_production_per_panel,
    active_panels,
    panels_with_issues,
    avg_temperature_c,
    cloud_condition_distribution
)
SELECT 
    DATEADD(HOUR, DATEPART(HOUR, s.timestamp), CAST(CAST(s.timestamp AS DATE) AS DATETIME2)) as report_hour,
    CAST(s.timestamp AS DATE) as report_date,
    DATEPART(HOUR, s.timestamp) as report_hour_of_day,
    
    -- System metrics
    SUM(s.production_kw) as total_production_kwh,
    AVG(s.production_kw) as avg_production_per_panel,
    COUNT(DISTINCT s.panel_id) as active_panels,
    COUNT(DISTINCT CASE WHEN s.is_valid = 0 THEN s.panel_id END) as panels_with_issues,
    
    -- Environmental
    AVG(s.temperature_c) as avg_temperature_c,
    
    -- Cloud condition distribution as JSON
    (
        SELECT 
            (SELECT COUNT(*) FROM silver.solar_data s2 
             WHERE s2.cloud_condition = 'Clear' 
               AND DATEADD(HOUR, DATEPART(HOUR, s2.timestamp), CAST(CAST(s2.timestamp AS DATE) AS DATETIME2)) = DATEADD(HOUR, DATEPART(HOUR, s.timestamp), CAST(CAST(s.timestamp AS DATE) AS DATETIME2))
            ) as clear,
            (SELECT COUNT(*) FROM silver.solar_data s2 
             WHERE s2.cloud_condition = 'Partly Cloudy' 
               AND DATEADD(HOUR, DATEPART(HOUR, s2.timestamp), CAST(CAST(s2.timestamp AS DATE) AS DATETIME2)) = DATEADD(HOUR, DATEPART(HOUR, s.timestamp), CAST(CAST(s.timestamp AS DATE) AS DATETIME2))
            ) as partly_cloudy,
            (SELECT COUNT(*) FROM silver.solar_data s2 
             WHERE s2.cloud_condition = 'Cloudy' 
               AND DATEADD(HOUR, DATEPART(HOUR, s2.timestamp), CAST(CAST(s2.timestamp AS DATE) AS DATETIME2)) = DATEADD(HOUR, DATEPART(HOUR, s.timestamp), CAST(CAST(s.timestamp AS DATE) AS DATETIME2))
            ) as cloudy
        FOR JSON PATH, WITHOUT_ARRAY_WRAPPER
    ) as cloud_condition_distribution
    
FROM silver.solar_data s
WHERE NOT EXISTS (
    SELECT 1 FROM gold.hourly_system_stats g 
    WHERE g.report_hour = DATEADD(HOUR, DATEPART(HOUR, s.timestamp), CAST(CAST(s.timestamp AS DATE) AS DATETIME2))
)
GROUP BY 
    DATEADD(HOUR, DATEPART(HOUR, s.timestamp), CAST(CAST(s.timestamp AS DATE) AS DATETIME2)),
    CAST(s.timestamp AS DATE),
    DATEPART(HOUR, s.timestamp);

PRINT 'Completed: ' + CAST(@@ROWCOUNT AS VARCHAR) + ' hourly stats records loaded';
GO