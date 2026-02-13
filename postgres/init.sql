-- init.sql
CREATE TABLE IF NOT EXISTS weather_data (
    id SERIAL PRIMARY KEY,
    city VARCHAR(100),
    country VARCHAR(100),
    region VARCHAR(100),
    lat DECIMAL(10,6),
    lon DECIMAL(10,6),
    localtime TIMESTAMP,
    temperature DECIMAL(5,2),
    weather_code INT,
    weather_descriptions TEXT,
    wind_speed INT,
    wind_degree INT,
    wind_dir VARCHAR(10),
    pressure INT,
    precip DECIMAL(5,1),
    humidity INT,
    cloudcover INT,
    feelslike INT,
    uv_index INT,
    visibility INT,
    sunrise VARCHAR(20),
    sunset VARCHAR(20),
    moon_phase VARCHAR(50),
    moon_illumination INT,
    air_quality_co DECIMAL(10,2),
    air_quality_no2 DECIMAL(10,2),
    air_quality_o3 DECIMAL(10,2),
    air_quality_so2 DECIMAL(10,2),
    air_quality_pm2_5 DECIMAL(10,2),
    air_quality_pm10 DECIMAL(10,2),
    us_epa_index INT,
    gb_defra_index INT,
    observation_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for better query performance
CREATE INDEX IF NOT EXISTS idx_weather_city ON weather_data(city);
CREATE INDEX IF NOT EXISTS idx_weather_observation_time ON weather_data(observation_time);
CREATE INDEX IF NOT EXISTS idx_weather_localtime ON weather_data(localtime);

-- Create a view for daily summaries
CREATE OR REPLACE VIEW daily_weather_summary AS
SELECT 
    city,
    DATE(observation_time) as date,
    AVG(temperature) as avg_temperature,
    MAX(temperature) as max_temperature,
    MIN(temperature) as min_temperature,
    AVG(humidity) as avg_humidity,
    AVG(wind_speed) as avg_wind_speed,
    AVG(cloudcover) as avg_cloudcover,
    AVG(uv_index) as avg_uv_index,
    AVG(pressure) as avg_pressure,
    SUM(precip) as total_precipitation,
    MODE() WITHIN GROUP (ORDER BY weather_descriptions) as predominant_weather
FROM weather_data
GROUP BY city, DATE(observation_time);

-- Create a table for solar analysis
CREATE TABLE IF NOT EXISTS solar_analysis (
    id SERIAL PRIMARY KEY,
    city VARCHAR(100),
    analysis_date DATE,
    daily_energy_kwh DECIMAL(10,2),
    peak_sun_hours DECIMAL(5,2),
    cloud_cover_impact DECIMAL(5,2),
    air_quality_impact DECIMAL(5,2),
    temperature_impact DECIMAL(5,2),
    estimated_savings_euros DECIMAL(10,2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE weather_data IS 'Stores weather data from WeatherStack API for solar analysis';
COMMENT ON COLUMN weather_data.cloudcover IS 'Cloud cover percentage (0-100)';
COMMENT ON COLUMN weather_data.uv_index IS 'UV index (0-11+)';
COMMENT ON COLUMN weather_data.us_epa_index IS 'US EPA air quality index (1-6)';
