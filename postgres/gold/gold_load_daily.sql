-- postgres/gold/gold_load_daily.sql
TRUNCATE gold_daily_panel;

INSERT INTO gold_daily_panel
SELECT 
    DATE(timestamp) AS date,
    panel_id,
    panel_type,
    COUNT(*) AS readings_count,
    AVG(production_kw) AS avg_production_kw,
    SUM(production_kw) AS total_production_kwh,
    MAX(production_kw) AS peak_production_kw,
    MIN(production_kw) AS min_production_kw,
    AVG(efficiency_ratio) AS avg_efficiency,
    COUNT(CASE WHEN is_valid THEN 1 END) AS valid_readings,
    COUNT(CASE WHEN NOT is_valid THEN 1 END) AS invalid_readings,
    ROUND(100.0 * COUNT(CASE WHEN is_valid THEN 1 END) / COUNT(*), 2) AS data_quality_pct
FROM silver_solar
GROUP BY DATE(timestamp), panel_id, panel_type;

SELECT 'gold_daily_panel loaded: ' || COUNT(*) || ' rows' FROM gold_daily_panel;