-- postgres/bronze/ddl_bronze.sql
-- Bronze Layer - Raw Data Tables

\c solar_data;

-- ============================================================
-- BRONZE: Weather data from API
-- ============================================================
-- This table already exists from init.sql
-- Included here for reference and completeness

COMMENT ON TABLE weather_data IS 'Bronze layer - Raw weather data from WeatherStack API';
COMMENT ON COLUMN weather_data.id IS 'Surrogate primary key';
COMMENT ON COLUMN weather_data.city IS 'City name';
COMMENT ON COLUMN weather_data.timestamp IS 'Local timestamp';
COMMENT ON COLUMN weather_data.temperature IS 'Temperature in Celsius';
COMMENT ON COLUMN weather_data.humidity IS 'Humidity percentage';
COMMENT ON COLUMN weather_data.wind_speed IS 'Wind speed in km/h';
COMMENT ON COLUMN weather_data.wind_direction IS 'Wind direction';
COMMENT ON COLUMN weather_data.pressure IS 'Atmospheric pressure';
COMMENT ON COLUMN weather_data.precipitation IS 'Precipitation in mm';
COMMENT ON COLUMN weather_data.cloud_cover IS 'Cloud cover percentage';
COMMENT ON COLUMN weather_data.uv_index IS 'UV index';
COMMENT ON COLUMN weather_data.weather_code IS 'Weather condition code';
COMMENT ON COLUMN weather_data.weather_description IS 'Text description';
COMMENT ON COLUMN weather_data.is_day IS 'Day or night';
COMMENT ON COLUMN weather_data.observation_time IS 'Time of observation';
COMMENT ON COLUMN weather_data.ingestion_timestamp IS 'When data was ingested';

-- ============================================================
-- BRONZE: Solar panel readings from IoT
-- ============================================================
COMMENT ON TABLE solar_panel_readings IS 'Bronze layer - Raw IoT solar panel data';
COMMENT ON COLUMN solar_panel_readings.id IS 'Surrogate primary key';
COMMENT ON COLUMN solar_panel_readings.event_id IS 'Unique event identifier';
COMMENT ON COLUMN solar_panel_readings.timestamp IS 'Reading timestamp';
COMMENT ON COLUMN solar_panel_readings.panel_id IS 'Panel identifier';
COMMENT ON COLUMN solar_panel_readings.panel_type IS 'Type of solar panel';
COMMENT ON COLUMN solar_panel_readings.panel_power_kw IS 'Panel rated power in kW';
COMMENT ON COLUMN solar_panel_readings.production_kw IS 'Current production in kW';
COMMENT ON COLUMN solar_panel_readings.temperature_c IS 'Panel temperature in Celsius';
COMMENT ON COLUMN solar_panel_readings.cloud_factor IS 'Cloud coverage factor (0-1)';
COMMENT ON COLUMN solar_panel_readings.temp_efficiency IS 'Temperature efficiency factor';
COMMENT ON COLUMN solar_panel_readings.status IS 'Panel status';
COMMENT ON COLUMN solar_panel_readings.city IS 'Location city';
COMMENT ON COLUMN solar_panel_readings.ingestion_timestamp IS 'When data was ingested';

-- Create indexes if not exists (safety check)
CREATE INDEX IF NOT EXISTS idx_weather_timestamp ON weather_data(timestamp);
CREATE INDEX IF NOT EXISTS idx_weather_city ON weather_data(city);
CREATE INDEX IF NOT EXISTS idx_solar_timestamp ON solar_panel_readings(timestamp);
CREATE INDEX IF NOT EXISTS idx_solar_panel ON solar_panel_readings(panel_id);
CREATE INDEX IF NOT EXISTS idx_solar_event ON solar_panel_readings(event_id);

-- Row counts
SELECT 'weather_data' as table_name, COUNT(*) as row_count FROM weather_data
UNION ALL
SELECT 'solar_panel_readings', COUNT(*) FROM solar_panel_readings;