-- postgres/gold/gold_load_anomalies.sql
-- Gold Layer - Anomaly Detection

\c solar_data;

-- ============================================================
-- Detect Anomalies: Panels with unusually low production
-- ============================================================
TRUNCATE gold_anomalies;  -- Optional: clear old anomalies

WITH panel_stats AS (
    SELECT 
        panel_id,
        AVG(production_kw) as avg_production,
        STDDEV(production_kw) as stddev_production
    FROM silver_solar
    WHERE is_valid = true
    AND timestamp > NOW() - INTERVAL '7 days'
    GROUP BY panel_id
),
today_readings AS (
    SELECT 
        s.panel_id,
        s.production_kw,
        p.avg_production,
        (s.production_kw - p.avg_production) / NULLIF(p.stddev_production, 0) as z_score
    FROM silver_solar s
    JOIN panel_stats p ON s.panel_id = p.panel_id
    WHERE DATE(s.timestamp) = CURRENT_DATE
)
INSERT INTO gold_anomalies (anomaly_date, panel_id, anomaly_type, severity, expected_value, actual_value, deviation_percentage)
SELECT 
    CURRENT_DATE,
    panel_id,
    CASE WHEN z_score < -3 THEN 'Critical Low Production' ELSE 'Low Production' END,
    CASE WHEN z_score < -3 THEN 'Critical' ELSE 'Warning' END,
    avg_production,
    production_kw,
    ROUND(100.0 * (avg_production - production_kw) / avg_production, 2)
FROM today_readings
WHERE z_score < -2;

-- ============================================================
-- Detect Missing Data Anomalies
-- ============================================================
WITH expected_panels AS (
    SELECT DISTINCT panel_id FROM silver_solar
)
INSERT INTO gold_anomalies (anomaly_date, panel_id, anomaly_type, severity)
SELECT 
    CURRENT_DATE,
    e.panel_id,
    'Missing Data',
    'Critical'
FROM expected_panels e
WHERE NOT EXISTS (
    SELECT 1 FROM silver_solar s 
    WHERE s.panel_id = e.panel_id 
    AND DATE(s.timestamp) = CURRENT_DATE
);

-- ============================================================
-- Show results
-- ============================================================
SELECT 
    anomaly_type,
    severity,
    COUNT(*) as count
FROM gold_anomalies
WHERE anomaly_date = CURRENT_DATE
GROUP BY anomaly_type, severity
ORDER BY severity, count DESC;