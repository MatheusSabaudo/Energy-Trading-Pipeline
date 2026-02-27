USE EnergyTradingPipeline;
GO

-- ============================================================
-- SILVER LAYER LOAD - Bronze to Silver
-- ============================================================

PRINT 'STARTING BRONZE TO SILVER TRANSFORMATION';
GO

INSERT INTO silver.solar_data (
    event_id,
    bronze_id,
    timestamp,
    panel_id,
    panel_type,
    panel_power_kw,
    production_kw,
    temperature_c,
    -- REMOVED: cloud_factor and temp_efficiency (not in silver table)
    production_date,
    production_hour,
    cloud_condition,
    efficiency_ratio,
    is_valid,
    quality_issues
)
SELECT 
    b.event_id,
    NULL as bronze_id,
    b.timestamp,
    b.panel_id,
    b.panel_type,
    b.panel_power_kw,
    b.production_kw,
    b.temperature_c,
    -- REMOVED: b.cloud_factor and b.temp_efficiency
    
    CAST(b.timestamp AS DATE) as production_date,
    DATEPART(HOUR, b.timestamp) as production_hour,
    
    CASE 
        WHEN b.cloud_factor >= 0.8 THEN 'Clear'
        WHEN b.cloud_factor >= 0.5 THEN 'Partly Cloudy'
        WHEN b.cloud_factor IS NULL THEN 'Unknown'
        ELSE 'Cloudy'
    END as cloud_condition,
    
    CASE 
        WHEN b.panel_power_kw > 0 THEN b.production_kw / b.panel_power_kw
        ELSE NULL
    END as efficiency_ratio,
    
    CASE 
        WHEN b.production_kw < 0 THEN 0
        WHEN b.temperature_c < -30 OR b.temperature_c > 60 THEN 0
        WHEN b.cloud_factor < 0 OR b.cloud_factor > 1 THEN 0
        WHEN b.panel_power_kw > 0 AND (b.production_kw / b.panel_power_kw) > 1.2 THEN 0
        WHEN b.panel_id IS NULL THEN 0
        ELSE 1
    END as is_valid,
    
    CASE 
        WHEN b.production_kw < 0 THEN 'Negative production'
        WHEN b.temperature_c < -30 OR b.temperature_c > 60 THEN 'Temperature out of range'
        WHEN b.cloud_factor < 0 OR b.cloud_factor > 1 THEN 'Cloud factor invalid'
        WHEN b.panel_power_kw > 0 AND (b.production_kw / b.panel_power_kw) > 1.2 THEN 'Efficiency too high'
        WHEN b.panel_id IS NULL THEN 'Missing panel_id'
        ELSE NULL
    END as quality_issues
    
FROM bronze.api_data b
LEFT JOIN silver.solar_data s ON b.event_id = s.event_id
WHERE s.event_id IS NULL;

PRINT 'Completed: ' + CAST(@@ROWCOUNT AS VARCHAR) + ' rows loaded to silver.solar_data';
GO

SELECT * FROM silver.solar_data;