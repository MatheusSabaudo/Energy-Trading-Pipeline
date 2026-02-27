USE EnergyTradingPipeline;
GO

-- Quick check of what's in bronze
SELECT 
    COUNT(*) as total_rows,
    MIN(timestamp) as oldest_data,
    MAX(timestamp) as newest_data,
    COUNT(DISTINCT panel_id) as unique_panels
FROM bronze.api_data;

-- Check for any data quality issues
SELECT 
    COUNT(CASE WHEN production_kw < 0 THEN 1 END) as negative_production,
    COUNT(CASE WHEN temperature_c < -30 OR temperature_c > 60 THEN 1 END) as out_of_range_temp,
    COUNT(CASE WHEN cloud_factor < 0 OR cloud_factor > 1 THEN 1 END) as invalid_cloud,
    COUNT(CASE WHEN temp_efficiency < 0.5 OR temp_efficiency > 1.5 THEN 1 END) as invalid_efficiency
FROM bronze.api_data;