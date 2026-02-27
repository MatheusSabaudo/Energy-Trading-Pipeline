-- postgres/gold/ddl_gold.sql
-- Gold Layer - Table Definitions

\c solar_data;

-- ============================================================
-- GOLD: Daily panel performance
-- ============================================================
DROP TABLE IF EXISTS gold_daily_panel CASCADE;

CREATE TABLE gold_daily_panel (
    date DATE,
    panel_id VARCHAR(50),
    panel_type VARCHAR(50),
    readings_count INTEGER,
    avg_production_kw DECIMAL(8,3),
    total_production_kwh DECIMAL(10,2),
    peak_production_kw DECIMAL(8,3),
    min_production_kw DECIMAL(8,3),
    avg_efficiency DECIMAL(5,3),
    valid_readings INTEGER,
    invalid_readings INTEGER,
    data_quality_pct DECIMAL(5,2),
    gold_ingestion_time TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================================
-- GOLD: Hourly system performance
-- ============================================================
DROP TABLE IF EXISTS gold_hourly_system CASCADE;

CREATE TABLE gold_hourly_system (
    hour TIMESTAMPTZ,
    active_panels INTEGER,
    total_production_kw DECIMAL(10,2),
    avg_production_per_panel DECIMAL(8,3),
    peak_production_kw DECIMAL(8,3),
    avg_temperature DECIMAL(5,1),
    avg_system_efficiency DECIMAL(5,3),
    valid_readings INTEGER,
    gold_ingestion_time TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================================
-- GOLD: Weather impact analysis
-- ============================================================
DROP TABLE IF EXISTS gold_weather_impact CASCADE;

CREATE TABLE gold_weather_impact (
    timestamp TIMESTAMPTZ,
    city VARCHAR(100),
    temperature DECIMAL(5,2),
    humidity INTEGER,
    cloud_cover INTEGER,
    uv_index DECIMAL(3,1),
    sky_condition VARCHAR(20),
    avg_solar_production DECIMAL(8,3),
    reporting_panels INTEGER
);

-- ============================================================
-- GOLD: Monthly KPIs
-- ============================================================
DROP TABLE IF EXISTS gold_monthly_kpis CASCADE;

CREATE TABLE gold_monthly_kpis (
    year INTEGER,
    month INTEGER,
    total_panels INTEGER,
    total_production_kwh DECIMAL(12,2),
    avg_production_kw DECIMAL(8,3),
    peak_production_kw DECIMAL(8,3),
    avg_efficiency DECIMAL(5,3),
    avg_temperature DECIMAL(5,1),
    valid_readings INTEGER,
    data_quality_pct DECIMAL(5,2),
    gold_ingestion_time TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================================
-- GOLD: Anomaly detection (MISSING TABLE - ADD THIS!)
-- ============================================================
DROP TABLE IF EXISTS gold_anomalies CASCADE;

CREATE TABLE gold_anomalies (
    anomaly_id BIGSERIAL PRIMARY KEY,
    detection_time TIMESTAMPTZ DEFAULT NOW(),
    anomaly_date DATE,
    panel_id VARCHAR(50),
    anomaly_type VARCHAR(50),
    severity VARCHAR(20),
    expected_value DECIMAL(8,3),
    actual_value DECIMAL(8,3),
    deviation_percentage DECIMAL(5,2),
    weather_conditions VARCHAR(50),
    resolution_status VARCHAR(20) DEFAULT 'Open',
    resolution_notes TEXT,
    resolved_time TIMESTAMPTZ
);

-- Indexes
CREATE INDEX idx_gold_daily_date ON gold_daily_panel(date);
CREATE INDEX idx_gold_daily_panel ON gold_daily_panel(panel_id);
CREATE INDEX idx_gold_hourly_time ON gold_hourly_system(hour);
CREATE INDEX idx_anomalies_date ON gold_anomalies(anomaly_date);
CREATE INDEX idx_anomalies_panel ON gold_anomalies(panel_id);
CREATE INDEX idx_anomalies_status ON gold_anomalies(resolution_status);