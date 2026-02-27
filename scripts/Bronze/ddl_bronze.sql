USE EnergyTradingPipeline;
GO

IF OBJECT_ID('bronze.api_data', 'U') IS NOT NULL
    DROP TABLE bronze.api_data;

CREATE TABLE bronze.api_data (
    event_id UNIQUEIDENTIFIER,
    
    timestamp DATETIME2,
    
    panel_id VARCHAR(50),
    panel_type VARCHAR(50),
    panel_power_kw DECIMAL(5,2),    -- 999.99 max
    production_kw DECIMAL(8,3),     -- 99999.999 max
    temperature_c DECIMAL(5,1),     -- 999.9°C max
    cloud_factor DECIMAL(3,2),       -- 0.00 to 9.99
    temp_efficiency DECIMAL(4,3),    -- 0.000 to 9.999
    actual_status VARCHAR(255),
    city VARCHAR(50),

    ingestion_time DATETIME2,
    
    kafka_topic VARCHAR(50),
    kafka_partition INT,
    kafka_offset BIGINT,
    source_file VARCHAR(100),

    raw_json NVARCHAR(MAX) NOT NULL,

    is_processed BIT DEFAULT 0,
    
    first_seen DATETIME2 DEFAULT GETDATE(),

    CONSTRAINT PK_api_data PRIMARY KEY (event_id)
    
);

-- SPEED UP QUERIES BY TIME USING INDEXES
-- CREATED INDEXES FOR THE MOST COMMON / CRITICAL QUERIES

-- Query 1: Find data by time range (VERY COMMON)
CREATE INDEX idx_bronze_timestamp ON bronze.api_data(timestamp);

-- Query 2: Look up specific panel (VERY COMMON)
CREATE INDEX idx_bronze_panel ON bronze.api_data(panel_id);

-- Query 3: Find unprocessed data for ETL (CRITICAL)
CREATE INDEX idx_bronze_processed ON bronze.api_data(is_processed);

-- Query 4: Monitor ingestion rates (OFTEN)
CREATE INDEX idx_bronze_ingestion ON bronze.api_data(ingestion_time);


SELECT * FROM bronze.api_data;