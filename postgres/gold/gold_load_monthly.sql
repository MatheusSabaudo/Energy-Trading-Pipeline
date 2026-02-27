-- postgres/gold/gold_load_monthly.sql
TRUNCATE gold_monthly_kpis;

INSERT INTO gold_monthly_kpis
SELECT 
    EXTRACT(YEAR FROM timestamp) AS year,
    EXTRACT(MONTH FROM timestamp) AS month,
    COUNT(DISTINCT panel_id) AS total_panels,
    SUM(production_kw) AS total_production_kwh,
    AVG(production_kw) AS avg_production_kw,
    MAX(production_kw) AS peak_production_kw,
    AVG(efficiency_ratio) AS avg_efficiency,
    AVG(temperature_c) AS avg_temperature,
    COUNT(CASE WHEN is_valid THEN 1 END) AS valid_readings,
    ROUND(100.0 * COUNT(CASE WHEN is_valid THEN 1 END) / COUNT(*), 2) AS data_quality_pct
FROM silver_solar
GROUP BY EXTRACT(YEAR FROM timestamp), EXTRACT(MONTH FROM timestamp);

SELECT 'gold_monthly_kpis loaded: ' || COUNT(*) || ' rows' FROM gold_monthly_kpis;