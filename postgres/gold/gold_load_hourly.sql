-- postgres/gold/gold_load_hourly.sql
TRUNCATE gold_hourly_system;

INSERT INTO gold_hourly_system
SELECT 
    DATE_TRUNC('hour', timestamp) AS hour,
    COUNT(DISTINCT panel_id) AS active_panels,
    SUM(production_kw) AS total_production_kw,
    AVG(production_kw) AS avg_production_per_panel,
    MAX(production_kw) AS peak_production_kw,
    AVG(temperature_c) AS avg_temperature,
    AVG(efficiency_ratio) AS avg_system_efficiency,
    COUNT(CASE WHEN is_valid THEN 1 END) AS valid_readings
FROM silver_solar
GROUP BY DATE_TRUNC('hour', timestamp);

SELECT 'gold_hourly_system loaded: ' || COUNT(*) || ' rows' FROM gold_hourly_system;