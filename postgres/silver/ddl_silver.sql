USE EnergyTradingPipeline;
GO

IF OBJECT_ID('silver.solar_data', 'U') IS NOT NULL
    DROP TABLE silver.solar_data;

-- Create silver schema if not exists
IF NOT EXISTS (SELECT * FROM sys.schemas WHERE name = 'silver')
    EXEC('CREATE SCHEMA silver');
GO

CREATE TABLE silver.solar_data (
    silver_id BIGINT IDENTITY(1,1) PRIMARY KEY,
    bronze_id BIGINT,
    event_id UNIQUEIDENTIFIER NOT NULL,
    
    timestamp DATETIME2,
    
    panel_id VARCHAR(50),
    panel_type VARCHAR(50),
    panel_power_kw DECIMAL(5,2),
    production_kw DECIMAL(8,3),
    temperature_c DECIMAL(5,1),
    
    production_date DATE,
    production_hour INT,
    cloud_condition VARCHAR(20),
    uv_category VARCHAR(20),
    efficiency_ratio DECIMAL(5,3),

    -- Quality flags
    is_valid BIT DEFAULT 1,
    quality_issues VARCHAR(MAX),

    -- Metadata
    silver_ingestion_time DATETIME2 DEFAULT GETDATE(),
    
    CONSTRAINT UQ_silver_event UNIQUE (event_id)
);

-- Indexes for performance
CREATE INDEX idx_silver_timestamp ON silver.solar_data(timestamp);
CREATE INDEX idx_silver_panel ON silver.solar_data(panel_id);
CREATE INDEX idx_silver_date ON silver.solar_data(production_date);
CREATE INDEX idx_silver_valid ON silver.solar_data(is_valid);
GO

-- Fix: Query the correct table name
SELECT * FROM silver.solar_data;
GO