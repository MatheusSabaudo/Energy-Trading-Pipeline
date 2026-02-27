-- postgres/silver/silver_load.sql
-- Silver Layer - Data Population

\c solar_data;

-- ============================================================
-- Load silver_weather
-- ============================================================
TRUNCATE silver_weather;

INSERT INTO silver_weather (
    id, city, timestamp, temperature, humidity, wind_speed,
    wind_direction, pressure, precipitation, cloud_cover, uv_index,
    weather_code, weather_description, is_day, observation_time,
    ingestion_timestamp, year, month, day, hour, day_of_week,
    temperature_category, sky_condition, uv_category, is_valid
)
SELECT 
    id, city, timestamp, temperature, humidity, wind_speed,
    wind_direction, pressure, precipitation, cloud_cover, uv_index,
    weather_code, weather_description, is_day, observation_time,
    ingestion_timestamp,
    EXTRACT(YEAR FROM timestamp) AS year,
    EXTRACT(MONTH FROM timestamp) AS month,
    EXTRACT(DAY FROM timestamp) AS day,
    EXTRACT(HOUR FROM timestamp) AS hour,
    EXTRACT(DOW FROM timestamp) AS day_of_week,
    CASE 
        WHEN temperature < 0 THEN 'Freezing'
        WHEN temperature < 10 THEN 'Cold'
        WHEN temperature < 20 THEN 'Mild'
        WHEN temperature < 30 THEN 'Warm'
        ELSE 'Hot'
    END AS temperature_category,
    CASE 
        WHEN cloud_cover < 20 THEN 'Clear'
        WHEN cloud_cover < 60 THEN 'Partly Cloudy'
        ELSE 'Cloudy'
    END AS sky_condition,
    CASE 
        WHEN uv_index < 3 THEN 'Low'
        WHEN uv_index < 6 THEN 'Moderate'
        WHEN uv_index < 8 THEN 'High'
        ELSE 'Very High'
    END AS uv_category,
    CASE 
        WHEN temperature BETWEEN -30 AND 50 
             AND humidity BETWEEN 0 AND 100
             AND wind_speed >= 0
             AND cloud_cover BETWEEN 0 AND 100
        THEN TRUE
        ELSE FALSE
    END AS is_valid
FROM weather_data;

SELECT 'silver_weather loaded: ' || COUNT(*) || ' rows' FROM silver_weather;

-- ============================================================
-- Load silver_solar
-- ============================================================
TRUNCATE silver_solar;

INSERT INTO silver_solar (
    id, event_id, timestamp, panel_id, panel_type,
    panel_power_kw, production_kw, temperature_c,
    cloud_factor, temp_efficiency, status, city,
    ingestion_timestamp, year, month, day, hour, day_of_week,
    efficiency_ratio, performance_category, is_valid
)
SELECT 
    id, event_id, timestamp, panel_id, panel_type,
    panel_power_kw, production_kw, temperature_c,
    cloud_factor, temp_efficiency, status, city,
    ingestion_timestamp,
    EXTRACT(YEAR FROM timestamp) AS year,
    EXTRACT(MONTH FROM timestamp) AS month,
    EXTRACT(DAY FROM timestamp) AS day,
    EXTRACT(HOUR FROM timestamp) AS hour,
    EXTRACT(DOW FROM timestamp) AS day_of_week,
    production_kw / NULLIF(panel_power_kw, 0) AS efficiency_ratio,
    CASE 
        WHEN production_kw / NULLIF(panel_power_kw, 0) > 0.8 THEN 'Excellent'
        WHEN production_kw / NULLIF(panel_power_kw, 0) > 0.5 THEN 'Good'
        WHEN production_kw / NULLIF(panel_power_kw, 0) > 0.2 THEN 'Fair'
        ELSE 'Poor'
    END AS performance_category,
    CASE 
        WHEN production_kw >= 0 
             AND temperature_c BETWEEN -30 AND 60
             AND cloud_factor BETWEEN 0 AND 1
             AND temp_efficiency BETWEEN 0.5 AND 1.5
        THEN TRUE
        ELSE FALSE
    END AS is_valid
FROM solar_panel_readings;

SELECT 'silver_solar loaded: ' || COUNT(*) || ' rows' FROM silver_solar;