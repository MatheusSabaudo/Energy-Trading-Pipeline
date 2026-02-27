-- postgres/silver/ddl_silver.sql
-- Silver Layer - Table Definitions

\c solar_data;

-- ============================================================
-- SILVER: Cleaned weather data
-- ============================================================
DROP TABLE IF EXISTS silver_weather CASCADE;

CREATE TABLE silver_weather (
    id INTEGER,
    city VARCHAR(100),
    timestamp TIMESTAMPTZ,
    temperature DECIMAL(5,2),
    humidity INTEGER,
    wind_speed DECIMAL(5,2),
    wind_direction VARCHAR(10),
    pressure DECIMAL(7,2),
    precipitation DECIMAL(5,2),
    cloud_cover INTEGER,
    uv_index DECIMAL(3,1),
    weather_code INTEGER,
    weather_description VARCHAR(255),
    is_day BOOLEAN,
    observation_time TIMESTAMPTZ,
    ingestion_timestamp TIMESTAMPTZ,
    
    -- Enriched fields
    year INTEGER,
    month INTEGER,
    day INTEGER,
    hour INTEGER,
    day_of_week INTEGER,
    temperature_category VARCHAR(20),
    sky_condition VARCHAR(20),
    uv_category VARCHAR(20),
    is_valid BOOLEAN,
    silver_ingestion_time TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_silver_weather_timestamp ON silver_weather(timestamp);
CREATE INDEX idx_silver_weather_city ON silver_weather(city);
CREATE INDEX idx_silver_weather_valid ON silver_weather(is_valid);

-- ============================================================
-- SILVER: Cleaned solar data
-- ============================================================
DROP TABLE IF EXISTS silver_solar CASCADE;

CREATE TABLE silver_solar (
    id INTEGER,
    event_id UUID,
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
    ingestion_timestamp TIMESTAMPTZ,
    
    -- Enriched fields
    year INTEGER,
    month INTEGER,
    day INTEGER,
    hour INTEGER,
    day_of_week INTEGER,
    efficiency_ratio DECIMAL(5,3),
    performance_category VARCHAR(20),
    is_valid BOOLEAN,
    silver_ingestion_time TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_silver_solar_timestamp ON silver_solar(timestamp);
CREATE INDEX idx_silver_solar_panel ON silver_solar(panel_id);
CREATE INDEX idx_silver_solar_valid ON silver_solar(is_valid);