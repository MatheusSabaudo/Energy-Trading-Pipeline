-- postgres/init/init.sql
-- Initialize PostgreSQL database with both API and IoT tables

CREATE TABLE IF NOT EXISTS weather_data (
    id SERIAL PRIMARY KEY,
    city VARCHAR(100),
    timestamp TIMESTAMPTZ,
    temperature DECIMAL(5,2),
    humidity INT,
    wind_speed DECIMAL(5,2),
    wind_direction VARCHAR(10),
    pressure DECIMAL(7,2),
    precipitation DECIMAL(5,2),
    cloud_cover INT,
    uv_index DECIMAL(3,1),
    weather_code INT,
    weather_description VARCHAR(255),
    is_day BOOLEAN,
    observation_time TIMESTAMPTZ,
    ingestion_timestamp TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_weather_timestamp ON weather_data(timestamp);
CREATE INDEX IF NOT EXISTS idx_weather_city ON weather_data(city);
CREATE INDEX IF NOT EXISTS idx_weather_observation ON weather_data(observation_time);

CREATE TABLE IF NOT EXISTS solar_panel_readings (
    id SERIAL PRIMARY KEY,
    event_id UUID UNIQUE,
    timestamp TIMESTAMPTZ,
    panel_id VARCHAR(50),
    panel_type VARCHAR(50),
    panel_power_kw DECIMAL(5,2),
    production_kw DECIMAL(8,3),
    temperature_c DECIMAL(5,1),
    cloud_factor DECIMAL(3,2),
    temp_efficiency DECIMAL(4,3),
    status VARCHAR(20),
    city VARCHAR(50),
    ingestion_timestamp TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_iot_timestamp ON solar_panel_readings(timestamp);
CREATE INDEX IF NOT EXISTS idx_iot_panel_id ON solar_panel_readings(panel_id);
CREATE INDEX IF NOT EXISTS idx_iot_event_id ON solar_panel_readings(event_id);

CREATE OR REPLACE VIEW combined_solar_weather AS
SELECT
    s.timestamp,
    s.panel_id,
    s.production_kw,
    s.temperature_c as panel_temperature,
    w.temperature as ambient_temperature,
    w.humidity,
    w.wind_speed,
    w.cloud_cover,
    w.uv_index
FROM solar_panel_readings s
LEFT JOIN weather_data w ON DATE(s.timestamp) = DATE(w.timestamp)
    AND EXTRACT(HOUR FROM s.timestamp) = EXTRACT(HOUR FROM w.timestamp);

GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO airflow;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO airflow;

\i /docker-entrypoint-initdb.d/postgres/silver/ddl_silver.sql
\i /docker-entrypoint-initdb.d/postgres/gold/ddl_gold.sql

SELECT 'Tables created successfully' as message;
SELECT table_name FROM information_schema.tables WHERE table_schema = 'public';
