USE EnergyTradingPipeline;
GO

-- ============================================================
-- GOLD LAYER LOAD - Anomaly Detection (FIXED)
-- ============================================================

PRINT 'STARTING GOLD ANOMALY DETECTION LOAD';
GO

DECLARE @AnomalyCount INT;

INSERT INTO gold.anomaly_log (
    anomaly_date,
    panel_id,
    anomaly_type,
    severity,
    expected_value,
    actual_value,
    deviation_percentage,
    weather_conditions,
    resolution_status
)
SELECT 
    CAST(s.timestamp AS DATE) as anomaly_date,
    s.panel_id,
    
    -- Anomaly type
    CASE 
        WHEN s.production_kw < (p.avg_production * 0.3) THEN 'Critical Low Production'
        WHEN s.production_kw < (p.avg_production * 0.5) THEN 'Low Production'
        WHEN s.temperature_c > 45 THEN 'High Temperature'
        WHEN s.is_valid = 0 AND s.quality_issues LIKE '%Negative%' THEN 'Negative Production'
        ELSE NULL
    END as anomaly_type,
    
    -- Severity
    CASE 
        WHEN s.production_kw < (p.avg_production * 0.3) THEN 'Critical'
        WHEN s.production_kw < (p.avg_production * 0.5) THEN 'Warning'
        WHEN s.temperature_c > 45 THEN 'Warning'
        WHEN s.is_valid = 0 AND s.quality_issues LIKE '%Negative%' THEN 'Critical'
        ELSE NULL
    END as severity,
    
    -- Values
    p.avg_production as expected_value,
    s.production_kw as actual_value,
    CASE 
        WHEN p.avg_production > 0 
        THEN CAST(100.0 * (p.avg_production - s.production_kw) / p.avg_production AS DECIMAL(5,2))
        ELSE NULL
    END as deviation_percentage,
    
    -- Context
    s.cloud_condition as weather_conditions,
    'Open' as resolution_status
    
FROM silver.solar_data s
JOIN (
    SELECT 
        panel_id,
        AVG(production_kw) as avg_production
    FROM silver.solar_data
    WHERE is_valid = 1
    GROUP BY panel_id
) p ON s.panel_id = p.panel_id
WHERE 
    -- Anomaly conditions
    (
        (s.production_kw < (p.avg_production * 0.5) AND s.is_valid = 1)
        OR (s.temperature_c > 45)
        OR (s.is_valid = 0 AND s.quality_issues LIKE '%Negative%')
    )
    -- Not already logged (prevent duplicates)
    AND NOT EXISTS (
        SELECT 1 FROM gold.anomaly_log g 
        WHERE g.panel_id = s.panel_id 
          AND CAST(g.anomaly_date AS DATE) = CAST(s.timestamp AS DATE)
          AND g.anomaly_type = 
            CASE 
                WHEN s.production_kw < (p.avg_production * 0.3) THEN 'Critical Low Production'
                WHEN s.production_kw < (p.avg_production * 0.5) THEN 'Low Production'
                WHEN s.temperature_c > 45 THEN 'High Temperature'
                WHEN s.is_valid = 0 AND s.quality_issues LIKE '%Negative%' THEN 'Negative Production'
                ELSE NULL
            END
    );

SET @AnomalyCount = @@ROWCOUNT;

PRINT 'Completed: ' + CAST(@AnomalyCount AS VARCHAR) + ' anomaly records loaded';
GO