USE EnergyTradingPipeline;
GO

-- ============================================================
-- GOLD LAYER LOAD - Monthly KPIs (FIXED)
-- ============================================================

PRINT 'STARTING GOLD MONTHLY KPI LOAD';
GO

INSERT INTO gold.monthly_kpis (
    report_year,
    report_month,
    report_month_name,
    total_production_kwh,
    avg_daily_production,
    peak_production_day,
    peak_production_value,
    avg_system_efficiency,
    uptime_percentage,
    total_operating_hours,
    total_readings,
    valid_readings,
    invalid_readings,
    overall_data_quality,
    total_panels,
    panels_with_issues,
    panels_offline
)
SELECT 
    YEAR(s.timestamp) as report_year,
    MONTH(s.timestamp) as report_month,
    DATENAME(MONTH, s.timestamp) as report_month_name,
    
    -- Production KPIs
    SUM(s.production_kw) as total_production_kwh,
    AVG(daily.total) as avg_daily_production,
    
    -- Peak production day
    (
        SELECT TOP 1 CAST(daily_peak.timestamp AS DATE)
        FROM silver.solar_data daily_peak
        WHERE YEAR(daily_peak.timestamp) = YEAR(s.timestamp)
          AND MONTH(daily_peak.timestamp) = MONTH(s.timestamp)
        GROUP BY CAST(daily_peak.timestamp AS DATE)
        ORDER BY SUM(daily_peak.production_kw) DESC
    ) as peak_production_day,
    
    MAX(daily.total) as peak_production_value,
    
    -- Operational KPIs
    AVG(s.efficiency_ratio) as avg_system_efficiency,
    
    -- FIXED: Uptime percentage calculation
    CASE 
        WHEN COUNT(DISTINCT CAST(s.timestamp AS DATE)) > 0 
        THEN CAST(100.0 * COUNT(*) / (COUNT(DISTINCT CAST(s.timestamp AS DATE)) * 24.0) AS DECIMAL(5,2))
        ELSE 0 
    END as uptime_percentage,
    
    -- FIXED: Total operating hours (count of readings)
    COUNT(*) as total_operating_hours,
    
    -- Quality KPIs
    COUNT(*) as total_readings,
    SUM(CASE WHEN s.is_valid = 1 THEN 1 ELSE 0 END) as valid_readings,
    SUM(CASE WHEN s.is_valid = 0 THEN 1 ELSE 0 END) as invalid_readings,
    CAST(100.0 * SUM(CASE WHEN s.is_valid = 1 THEN 1 ELSE 0 END) / NULLIF(COUNT(*), 0) AS DECIMAL(5,2)) as overall_data_quality,
    
    -- Panel fleet metrics
    COUNT(DISTINCT s.panel_id) as total_panels,
    COUNT(DISTINCT CASE WHEN s.is_valid = 0 THEN s.panel_id END) as panels_with_issues,
    0 as panels_offline
    
FROM silver.solar_data s
LEFT JOIN (
    SELECT 
        CAST(timestamp AS DATE) as day,
        SUM(production_kw) as total
    FROM silver.solar_data
    GROUP BY CAST(timestamp AS DATE)
) daily ON CAST(s.timestamp AS DATE) = daily.day
WHERE NOT EXISTS (
    SELECT 1 FROM gold.monthly_kpis g 
    WHERE g.report_year = YEAR(s.timestamp) 
      AND g.report_month = MONTH(s.timestamp)
)
GROUP BY YEAR(s.timestamp), MONTH(s.timestamp), DATENAME(MONTH, s.timestamp);

PRINT 'Completed: ' + CAST(@@ROWCOUNT AS VARCHAR) + ' monthly KPI records loaded';
GO