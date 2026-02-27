USE EnergyTradingPipeline;
GO

-- Create gold schema if not exists
IF NOT EXISTS (SELECT * FROM sys.schemas WHERE name = 'gold')
    EXEC('CREATE SCHEMA gold');
GO

-- ============================================================
-- TABLE 1: Daily Panel Performance
-- What: Each panel's daily production summary
-- Use: Track individual panel performance, detect issues
-- ============================================================

IF OBJECT_ID('gold.daily_panel_performance', 'U') IS NOT NULL
    DROP TABLE gold.daily_panel_performance;
GO

CREATE TABLE gold.daily_panel_performance (
    performance_id BIGINT IDENTITY(1,1) PRIMARY KEY,
    report_date DATE NOT NULL,
    panel_id VARCHAR(50) NOT NULL,
    panel_type VARCHAR(50),
    
    -- Production metrics
    total_production_kwh DECIMAL(10,2),
    avg_production_kw DECIMAL(8,3),
    max_production_kw DECIMAL(8,3),
    min_production_kw DECIMAL(8,3),
    operating_hours INT,
    
    -- Quality metrics
    valid_readings INT,
    invalid_readings INT,
    data_quality_pct DECIMAL(5,2),
    
    -- Efficiency metrics
    avg_efficiency_ratio DECIMAL(5,3),
    avg_temperature_c DECIMAL(5,1),
    peak_hour INT,
    
    -- Metadata
    gold_ingestion_time DATETIME2 DEFAULT GETDATE(),
    
    CONSTRAINT UQ_daily_panel UNIQUE (report_date, panel_id)
);

-- ============================================================
-- TABLE 2: Hourly System Performance
-- What: Overall system performance by hour
-- Use: Monitor system health, peak usage times
-- ============================================================

IF OBJECT_ID('gold.hourly_system_stats', 'U') IS NOT NULL
    DROP TABLE gold.hourly_system_stats;
GO

CREATE TABLE gold.hourly_system_stats (
    stats_id BIGINT IDENTITY(1,1) PRIMARY KEY,
    report_hour DATETIME2 NOT NULL,
    report_date DATE,
    report_hour_of_day INT,
    
    -- System metrics
    total_production_kwh DECIMAL(10,2),
    avg_production_per_panel DECIMAL(8,3),
    active_panels INT,
    panels_with_issues INT,
    
    -- Environmental
    avg_temperature_c DECIMAL(5,1),
    cloud_condition_distribution VARCHAR(MAX), -- JSON or comma-separated
    
    -- Metadata
    gold_ingestion_time DATETIME2 DEFAULT GETDATE(),
    
    CONSTRAINT UQ_hourly_stats UNIQUE (report_hour)
);

-- ============================================================
-- TABLE 3: Monthly Business KPIs
-- What: High-level metrics for executives
-- Use: Business reviews, trend analysis, ROI calculations
-- ============================================================

IF OBJECT_ID('gold.monthly_kpis', 'U') IS NOT NULL
    DROP TABLE gold.monthly_kpis;
GO

CREATE TABLE gold.monthly_kpis (
    kpi_id BIGINT IDENTITY(1,1) PRIMARY KEY,
    report_year INT NOT NULL,
    report_month INT NOT NULL,
    report_month_name VARCHAR(20),
    
    -- Production KPIs
    total_production_kwh DECIMAL(12,2),
    avg_daily_production DECIMAL(10,2),
    peak_production_day DATE,
    peak_production_value DECIMAL(10,2),
    
    -- Operational KPIs
    avg_system_efficiency DECIMAL(5,3),
    uptime_percentage DECIMAL(5,2),
    total_operating_hours INT,
    
    -- Quality KPIs
    total_readings BIGINT,
    valid_readings BIGINT,
    invalid_readings BIGINT,
    overall_data_quality DECIMAL(5,2),
    
    -- Panel fleet metrics
    total_panels INT,
    panels_with_issues INT,
    panels_offline INT,
    
    -- Business metrics (for future expansion)
    estimated_revenue DECIMAL(12,2),
    co2_saved_kg DECIMAL(12,2),
    
    -- Metadata
    gold_ingestion_time DATETIME2 DEFAULT GETDATE(),
    
    CONSTRAINT UQ_monthly_kpis UNIQUE (report_year, report_month)
);

-- ============================================================
-- TABLE 4: Anomaly Detection
-- What: Track unusual events for alerts
-- Use: Operations team notifications
-- ============================================================

IF OBJECT_ID('gold.anomaly_log', 'U') IS NOT NULL
    DROP TABLE gold.anomaly_log;
GO

CREATE TABLE gold.anomaly_log (
    anomaly_id BIGINT IDENTITY(1,1) PRIMARY KEY,
    detection_time DATETIME2 DEFAULT GETDATE(),
    anomaly_date DATE,
    
    -- What happened
    panel_id VARCHAR(50),
    anomaly_type VARCHAR(50),  -- 'Low Production', 'High Temp', 'Offline', 'Data Gap'
    severity VARCHAR(20),      -- 'Warning', 'Critical'
    
    -- Details
    expected_value DECIMAL(8,3),
    actual_value DECIMAL(8,3),
    deviation_percentage DECIMAL(5,2),
    
    -- Context
    weather_conditions VARCHAR(50),
    resolution_status VARCHAR(20) DEFAULT 'Open',  -- 'Open', 'Investigating', 'Resolved'
    resolution_notes VARCHAR(MAX),
    resolved_time DATETIME2,
    
    -- Metadata
    gold_ingestion_time DATETIME2 DEFAULT GETDATE(),
    
    INDEX idx_anomaly_date (anomaly_date),
    INDEX idx_anomaly_panel (panel_id),
    INDEX idx_anomaly_severity (severity)
);

-- ============================================================
-- TABLE 5: Panel Master Data
-- What: Static information about each panel
-- Use: Reference data for all gold tables
-- ============================================================

IF OBJECT_ID('gold.panel_master', 'U') IS NOT NULL
    DROP TABLE gold.panel_master;
GO

CREATE TABLE gold.panel_master (
    panel_id VARCHAR(50) PRIMARY KEY,
    panel_type VARCHAR(50),
    panel_power_kw DECIMAL(5,2),
    installation_date DATE,
    location_lat DECIMAL(9,6),
    location_lon DECIMAL(9,6),
    city VARCHAR(50),
    expected_efficiency DECIMAL(4,3),
    warranty_years INT,
    status VARCHAR(20) DEFAULT 'Active',  -- 'Active', 'Maintenance', 'Retired'
    
    -- Metadata
    last_updated DATETIME2 DEFAULT GETDATE()
);

-- Insert panel master data (example - adjust as needed)
INSERT INTO gold.panel_master (panel_id, panel_type, panel_power_kw, installation_date, city, expected_efficiency)
VALUES
    ('PV-001', 'Monocrystalline', 3.0, '2025-01-15', 'Turin', 0.85),
    ('PV-002', 'Monocrystalline', 3.0, '2025-01-15', 'Turin', 0.85),
    ('PV-003', 'Monocrystalline', 3.0, '2025-01-15', 'Turin', 0.85),
    ('PV-004', 'Monocrystalline', 3.0, '2025-01-15', 'Turin', 0.85),
    ('PV-005', 'Monocrystalline', 3.0, '2025-01-15', 'Turin', 0.85),
    ('PV-006', 'Monocrystalline', 3.0, '2025-01-15', 'Turin', 0.85),
    ('PV-007', 'Monocrystalline', 3.0, '2025-01-15', 'Turin', 0.85),
    ('PV-008', 'Monocrystalline', 3.0, '2025-01-15', 'Turin', 0.85),
    ('PV-009', 'Monocrystalline', 3.0, '2025-01-15', 'Turin', 0.85),
    ('PV-010', 'Monocrystalline', 3.0, '2025-01-15', 'Turin', 0.85);
GO

-- Create indexes for performance
CREATE INDEX idx_gold_daily_date ON gold.daily_panel_performance(report_date);
CREATE INDEX idx_gold_daily_panel ON gold.daily_panel_performance(panel_id);
CREATE INDEX idx_gold_hourly_date ON gold.hourly_system_stats(report_date);
CREATE INDEX idx_gold_monthly ON gold.monthly_kpis(report_year, report_month);
GO

-- Show created tables
SELECT 'Gold tables created successfully' as message;
SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_SCHEMA = 'gold';
GO