USE EnergyTradingPipeline;
GO

-- ============================================================
-- GOLD LAYER LOAD - Daily Panel Performance
-- ============================================================

PRINT 'STARTING GOLD DAILY PANEL PERFORMANCE LOAD';
GO

INSERT INTO gold.daily_panel_performance (
    report_date,
    panel_id,
    panel_type,
    total_production_kwh,
    avg_production_kw,
    max_production_kw,
    min_production_kw,
    operating_hours,
    valid_readings,
    invalid_readings,
    data_quality_pct,
    avg_efficiency_ratio,
    avg_temperature_c,
    peak_hour
)
SELECT 
    CAST(s.timestamp AS DATE) as report_date,
    s.panel_id,
    MAX(s.panel_type) as panel_type,
    
    -- Production metrics
    SUM(s.production_kw) as total_production_kwh,
    AVG(s.production_kw) as avg_production_kw,
    MAX(s.production_kw) as max_production_kw,
    MIN(s.production_kw) as min_production_kw,
    COUNT(*) as operating_hours,
    
    -- Quality metrics
    SUM(CASE WHEN s.is_valid = 1 THEN 1 ELSE 0 END) as valid_readings,
    SUM(CASE WHEN s.is_valid = 0 THEN 1 ELSE 0 END) as invalid_readings,
    CAST(100.0 * SUM(CASE WHEN s.is_valid = 1 THEN 1 ELSE 0 END) / COUNT(*) AS DECIMAL(5,2)) as data_quality_pct,
    
    -- Efficiency metrics
    AVG(s.efficiency_ratio) as avg_efficiency_ratio,
    AVG(s.temperature_c) as avg_temperature_c,
    
    -- Peak hour
    (
        SELECT TOP 1 production_hour
        FROM silver.solar_data s2
        WHERE s2.panel_id = s.panel_id 
          AND CAST(s2.timestamp AS DATE) = CAST(s.timestamp AS DATE)
          AND s2.is_valid = 1
        ORDER BY s2.production_kw DESC
    ) as peak_hour
    
FROM silver.solar_data s
WHERE NOT EXISTS (
    SELECT 1 FROM gold.daily_panel_performance g 
    WHERE g.report_date = CAST(s.timestamp AS DATE) 
      AND g.panel_id = s.panel_id
)
GROUP BY CAST(s.timestamp AS DATE), s.panel_id;

PRINT 'Completed: ' + CAST(@@ROWCOUNT AS VARCHAR) + ' daily panel records loaded';
GO