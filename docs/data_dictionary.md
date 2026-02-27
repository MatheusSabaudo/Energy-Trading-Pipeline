## 📄 **`docs/data_dictionary.md`**

# Data Dictionary

## 📊 Database: `solar_data`

## 🥉 Bronze Layer - Raw Data

### Table: `weather_data`
*Raw weather data ingested from WeatherStack API*

| Column | Type | Description | Example |
|--------|------|-------------|---------|
| `id` | SERIAL | Primary key | 1 |
| `city` | VARCHAR(100) | City name | 'Turin' |
| `timestamp` | TIMESTAMPTZ | Local timestamp | '2026-02-27 14:30:00+00' |
| `temperature` | DECIMAL(5,2) | Temperature in Celsius | 18.5 |
| `humidity` | INTEGER | Humidity percentage | 65 |
| `wind_speed` | DECIMAL(5,2) | Wind speed in km/h | 12.3 |
| `wind_direction` | VARCHAR(10) | Wind direction | 'NNE' |
| `pressure` | DECIMAL(7,2) | Atmospheric pressure | 1013.25 |
| `precipitation` | DECIMAL(5,2) | Precipitation in mm | 0.0 |
| `cloud_cover` | INTEGER | Cloud cover percentage | 20 |
| `uv_index` | DECIMAL(3,1) | UV index | 5.5 |
| `weather_code` | INTEGER | Weather condition code | 113 |
| `weather_description` | VARCHAR(255) | Text description | 'Partly cloudy' |
| `is_day` | BOOLEAN | Day or night | true |
| `observation_time` | TIMESTAMPTZ | Time of observation | '07:34 PM' |
| `ingestion_timestamp` | TIMESTAMPTZ | When data was ingested | '2026-02-27 14:35:00' |

### Table: `solar_panel_readings`
*Raw IoT solar panel data from Kafka*

| Column | Type | Description | Example |
|--------|------|-------------|---------|
| `id` | SERIAL | Primary key | 42 |
| `event_id` | UUID | Unique event identifier | '550e8400-e29b-41d4-a716-446655440000' |
| `timestamp` | TIMESTAMPTZ | Reading timestamp | '2026-02-27 14:30:00' |
| `panel_id` | VARCHAR(50) | Panel identifier | 'PV-001' |
| `panel_type` | VARCHAR(50) | Type of solar panel | 'Monocrystalline' |
| `panel_power_kw` | DECIMAL(5,2) | Panel rated power in kW | 3.0 |
| `production_kw` | DECIMAL(8,3) | Current production in kW | 2.456 |
| `temperature_c` | DECIMAL(5,1) | Panel temperature in Celsius | 23.5 |
| `cloud_factor` | DECIMAL(3,2) | Cloud coverage factor (0-1) | 0.85 |
| `temp_efficiency` | DECIMAL(4,3) | Temperature efficiency factor | 1.0 |
| `status` | VARCHAR(20) | Panel status | 'active' |
| `city` | VARCHAR(50) | Location city | 'Turin' |
| `ingestion_timestamp` | TIMESTAMPTZ | When data was ingested | '2026-02-27 14:30:05' |

---

## 🥈 Silver Layer - Cleaned & Enriched

### Table: `silver_weather`
*Cleaned weather data with derived columns*

| Column | Type | Description | Example |
|--------|------|-------------|---------|
| `id` | INTEGER | Original ID from weather_data | 1 |
| `city` | VARCHAR(100) | City name | 'Turin' |
| `timestamp` | TIMESTAMPTZ | Local timestamp | '2026-02-27 14:30:00+00' |
| `temperature` | DECIMAL(5,2) | Temperature in Celsius | 18.5 |
| `humidity` | INTEGER | Humidity percentage | 65 |
| `wind_speed` | DECIMAL(5,2) | Wind speed in km/h | 12.3 |
| `wind_direction` | VARCHAR(10) | Wind direction | 'NNE' |
| `pressure` | DECIMAL(7,2) | Atmospheric pressure | 1013.25 |
| `precipitation` | DECIMAL(5,2) | Precipitation in mm | 0.0 |
| `cloud_cover` | INTEGER | Cloud cover percentage | 20 |
| `uv_index` | DECIMAL(3,1) | UV index | 5.5 |
| `weather_code` | INTEGER | Weather condition code | 113 |
| `weather_description` | VARCHAR(255) | Text description | 'Partly cloudy' |
| `is_day` | BOOLEAN | Day or night | true |
| `observation_time` | TIMESTAMPTZ | Time of observation | '07:34 PM' |
| `ingestion_timestamp` | TIMESTAMPTZ | When data was ingested | '2026-02-27 14:35:00' |
| `year` | INTEGER | Year extracted from timestamp | 2026 |
| `month` | INTEGER | Month extracted from timestamp | 2 |
| `day` | INTEGER | Day extracted from timestamp | 27 |
| `hour` | INTEGER | Hour extracted from timestamp | 14 |
| `day_of_week` | INTEGER | Day of week (0=Sunday) | 5 |
| `temperature_category` | VARCHAR(20) | Categorical temperature | 'Mild' |
| `sky_condition` | VARCHAR(20) | Sky condition category | 'Partly Cloudy' |
| `uv_category` | VARCHAR(20) | UV index category | 'Moderate' |
| `is_valid` | BOOLEAN | Data quality flag | true |
| `silver_ingestion_time` | TIMESTAMPTZ | Silver layer timestamp | '2026-02-27 15:00:00' |

### Table: `silver_solar`
*Cleaned solar data with derived metrics*

| Column | Type | Description | Example |
|--------|------|-------------|---------|
| `id` | INTEGER | Original ID from solar_panel_readings | 42 |
| `event_id` | UUID | Unique event identifier | '550e8400-e29b-41d4-a716-446655440000' |
| `timestamp` | TIMESTAMPTZ | Reading timestamp | '2026-02-27 14:30:00' |
| `panel_id` | VARCHAR(50) | Panel identifier | 'PV-001' |
| `panel_type` | VARCHAR(50) | Type of solar panel | 'Monocrystalline' |
| `panel_power_kw` | DECIMAL(5,2) | Panel rated power in kW | 3.0 |
| `production_kw` | DECIMAL(8,3) | Current production in kW | 2.456 |
| `temperature_c` | DECIMAL(5,1) | Panel temperature in Celsius | 23.5 |
| `cloud_factor` | DECIMAL(3,2) | Cloud coverage factor (0-1) | 0.85 |
| `temp_efficiency` | DECIMAL(4,3) | Temperature efficiency factor | 1.0 |
| `status` | VARCHAR(20) | Panel status | 'active' |
| `city` | VARCHAR(50) | Location city | 'Turin' |
| `ingestion_timestamp` | TIMESTAMPTZ | When data was ingested | '2026-02-27 14:30:05' |
| `year` | INTEGER | Year extracted from timestamp | 2026 |
| `month` | INTEGER | Month extracted from timestamp | 2 |
| `day` | INTEGER | Day extracted from timestamp | 27 |
| `hour` | INTEGER | Hour extracted from timestamp | 14 |
| `day_of_week` | INTEGER | Day of week (0=Sunday) | 5 |
| `efficiency_ratio` | DECIMAL(5,3) | Production / Panel power | 0.819 |
| `performance_category` | VARCHAR(20) | Performance rating | 'Excellent' |
| `is_valid` | BOOLEAN | Data quality flag | true |
| `silver_ingestion_time` | TIMESTAMPTZ | Silver layer timestamp | '2026-02-27 15:00:00' |

---

## 🥇 Gold Layer - Aggregated Data

### Table: `gold_daily_panel`
*Daily performance metrics per panel*

| Column | Type | Description | Example |
|--------|------|-------------|---------|
| `date` | DATE | Date of aggregation | '2026-02-27' |
| `panel_id` | VARCHAR(50) | Panel identifier | 'PV-001' |
| `panel_type` | VARCHAR(50) | Type of solar panel | 'Monocrystalline' |
| `readings_count` | INTEGER | Number of readings | 24 |
| `avg_production_kw` | DECIMAL(8,3) | Average production | 2.145 |
| `total_production_kwh` | DECIMAL(10,2) | Total daily production | 51.48 |
| `peak_production_kw` | DECIMAL(8,3) | Peak production | 2.856 |
| `min_production_kw` | DECIMAL(8,3) | Minimum production | 0.234 |
| `avg_efficiency` | DECIMAL(5,3) | Average efficiency ratio | 0.715 |
| `valid_readings` | INTEGER | Number of valid readings | 24 |
| `invalid_readings` | INTEGER | Number of invalid readings | 0 |
| `data_quality_pct` | DECIMAL(5,2) | Data quality percentage | 100.00 |
| `gold_ingestion_time` | TIMESTAMPTZ | Gold layer timestamp | '2026-02-28 00:00:00' |

### Table: `gold_hourly_system`
*Hourly system-wide metrics*

| Column | Type | Description | Example |
|--------|------|-------------|---------|
| `hour` | TIMESTAMPTZ | Hour of aggregation | '2026-02-27 14:00:00' |
| `active_panels` | INTEGER | Number of active panels | 10 |
| `total_production_kw` | DECIMAL(10,2) | Total system production | 21.45 |
| `avg_production_per_panel` | DECIMAL(8,3) | Average per panel | 2.145 |
| `peak_production_kw` | DECIMAL(8,3) | Peak production | 2.856 |
| `avg_temperature` | DECIMAL(5,1) | Average temperature | 23.5 |
| `avg_system_efficiency` | DECIMAL(5,3) | Average system efficiency | 0.715 |
| `valid_readings` | INTEGER | Number of valid readings | 240 |
| `gold_ingestion_time` | TIMESTAMPTZ | Gold layer timestamp | '2026-02-27 15:00:00' |

### Table: `gold_monthly_kpis`
*Monthly Key Performance Indicators*

| Column | Type | Description | Example |
|--------|------|-------------|---------|
| `year` | INTEGER | Year | 2026 |
| `month` | INTEGER | Month | 2 |
| `total_panels` | INTEGER | Total active panels | 10 |
| `total_production_kwh` | DECIMAL(12,2) | Monthly total production | 1544.4 |
| `avg_production_kw` | DECIMAL(8,3) | Average production | 2.145 |
| `peak_production_kw` | DECIMAL(8,3) | Peak production | 2.856 |
| `avg_efficiency` | DECIMAL(5,3) | Average efficiency | 0.715 |
| `avg_temperature` | DECIMAL(5,1) | Average temperature | 22.3 |
| `valid_readings` | INTEGER | Total valid readings | 7200 |
| `data_quality_pct` | DECIMAL(5,2) | Overall data quality | 99.8 |
| `gold_ingestion_time` | TIMESTAMPTZ | Gold layer timestamp | '2026-03-01 00:00:00' |

### Table: `gold_weather_impact`
*Weather impact on solar production*

| Column | Type | Description | Example |
|--------|------|-------------|---------|
| `timestamp` | TIMESTAMPTZ | Timestamp | '2026-02-27 14:00:00' |
| `city` | VARCHAR(100) | City name | 'Turin' |
| `temperature` | DECIMAL(5,2) | Ambient temperature | 18.5 |
| `humidity` | INTEGER | Humidity percentage | 65 |
| `cloud_cover` | INTEGER | Cloud cover percentage | 20 |
| `uv_index` | DECIMAL(3,1) | UV index | 5.5 |
| `sky_condition` | VARCHAR(20) | Sky condition | 'Partly Cloudy' |
| `avg_solar_production` | DECIMAL(8,3) | Average solar production | 2.145 |
| `reporting_panels` | INTEGER | Number of reporting panels | 10 |

### Table: `gold_anomalies`
*Detected anomalies in the system*

| Column | Type | Description | Example |
|--------|------|-------------|---------|
| `anomaly_id` | BIGSERIAL | Primary key | 1 |
| `detection_time` | TIMESTAMPTZ | When anomaly was detected | '2026-02-27 14:30:00' |
| `anomaly_date` | DATE | Date of anomaly | '2026-02-27' |
| `panel_id` | VARCHAR(50) | Affected panel | 'PV-005' |
| `anomaly_type` | VARCHAR(50) | Type of anomaly | 'Low Production' |
| `severity` | VARCHAR(20) | Severity level | 'Warning' |
| `expected_value` | DECIMAL(8,3) | Expected value | 2.145 |
| `actual_value` | DECIMAL(8,3) | Actual value | 0.856 |
| `deviation_percentage` | DECIMAL(5,2) | Deviation percentage | 60.1 |
| `weather_conditions` | VARCHAR(50) | Weather context | 'Cloudy' |
| `resolution_status` | VARCHAR(20) | Status | 'Open' |
| `resolution_notes` | TEXT | Resolution notes | NULL |
| `resolved_time` | TIMESTAMPTZ | When resolved | NULL |

---

## 🔍 Indexes

| Table | Index Name | Purpose |
|-------|------------|---------|
| `weather_data` | `idx_weather_timestamp` | Time-based queries |
| `weather_data` | `idx_weather_city` | City filtering |
| `solar_panel_readings` | `idx_solar_timestamp` | Time-based queries |
| `solar_panel_readings` | `idx_solar_panel` | Panel-specific queries |
| `solar_panel_readings` | `idx_solar_event` | Event lookup |
| `silver_weather` | `idx_silver_weather_timestamp` | Time-based queries |
| `silver_weather` | `idx_silver_weather_valid` | Quality filtering |
| `silver_solar` | `idx_silver_solar_timestamp` | Time-based queries |
| `silver_solar` | `idx_silver_solar_panel` | Panel-specific queries |
| `silver_solar` | `idx_silver_solar_valid` | Quality filtering |
| `gold_daily_panel` | `idx_gold_daily_date` | Daily aggregations |
| `gold_daily_panel` | `idx_gold_daily_panel` | Panel lookup |
| `gold_hourly_system` | `idx_gold_hourly_time` | Time-based queries |
| `gold_anomalies` | `idx_anomalies_date` | Date-based anomaly lookup |
| `gold_anomalies` | `idx_anomalies_panel` | Panel-specific anomalies |
| `gold_anomalies` | `idx_anomalies_status` | Open anomaly queries |

---

## 🔄 Data Lineage

```
WeatherStack API ──► weather_data ──► silver_weather ──► gold_weather_impact
         │                │                  │
         ▼                ▼                  ▼
    Raw API Data     Bronze Layer       Silver Layer

Kafka Producer ──► solar_panel_readings ──► silver_solar ──► gold_daily_panel
         │                  │                     │              │
         ▼                  ▼                     ▼              ▼
    IoT Simulation      Bronze Layer         Silver Layer    Gold Layer
                                                               │
                                                               ▼
                                                         gold_hourly_system
                                                               │
                                                               ▼
                                                         gold_monthly_kpis
                                                               │
                                                               ▼
                                                         gold_anomalies
```

---

## 📈 Business Metrics

| Metric | Source | Calculation |
|--------|--------|-------------|
| System Efficiency | `gold_daily_panel` | AVG(efficiency_ratio) |
| Data Quality | `gold_daily_panel` | valid_readings / total_readings |
| Panel Uptime | `gold_anomalies` | COUNT(open anomalies) |
| Peak Production | `gold_hourly_system` | MAX(total_production_kw) |
| Weather Impact | `gold_weather_impact` | AVG(avg_solar_production) by sky_condition |
| Monthly Production | `gold_monthly_kpis` | total_production_kwh |
| Anomaly Rate | `gold_anomalies` | COUNT(*) / total_readings |

---

## 🔗 Relationships

| Table | Related To | Relationship |
|-------|------------|--------------|
| `silver_weather` | `weather_data` | 1:1 (by id) |
| `silver_solar` | `solar_panel_readings` | 1:1 (by id) |
| `gold_daily_panel` | `silver_solar` | 1:M (by panel_id, date) |
| `gold_hourly_system` | `silver_solar` | M:1 (by hour) |
| `gold_anomalies` | `silver_solar` | M:1 (by panel_id, date) |
| `gold_weather_impact` | `silver_weather`, `silver_solar` | M:M (by hour) |

---

## 📊 Sample Queries

### Bronze Layer
```sql
-- Get latest weather data
SELECT * FROM weather_data ORDER BY timestamp DESC LIMIT 5;

-- Get latest solar readings
SELECT * FROM solar_panel_readings ORDER BY timestamp DESC LIMIT 5;
```

### Silver Layer
```sql
-- Get valid solar readings with performance categories
SELECT timestamp, panel_id, production_kw, performance_category
FROM silver_solar
WHERE is_valid = true
ORDER BY timestamp DESC
LIMIT 10;

-- Get weather by sky condition
SELECT sky_condition, COUNT(*), AVG(temperature)
FROM silver_weather
GROUP BY sky_condition;
```

### Gold Layer
```sql
-- Daily panel performance
SELECT date, panel_id, total_production_kwh, avg_efficiency
FROM gold_daily_panel
WHERE date = CURRENT_DATE
ORDER BY total_production_kwh DESC;

-- Active anomalies
SELECT anomaly_type, severity, COUNT(*)
FROM gold_anomalies
WHERE resolution_status = 'Open'
GROUP BY anomaly_type, severity;

-- Hourly system performance
SELECT hour, active_panels, total_production_kw
FROM gold_hourly_system
WHERE hour >= NOW() - INTERVAL '24 hours'
ORDER BY hour DESC;
```

---

## 🏷️ Data Categories

### Temperature Categories
| Range | Category |
|-------|----------|
| < 0°C | Freezing |
| 0-10°C | Cold |
| 10-20°C | Mild |
| 20-30°C | Warm |
| > 30°C | Hot |

### Sky Conditions
| Cloud Cover | Category |
|-------------|----------|
| 0-20% | Clear |
| 20-60% | Partly Cloudy |
| 60-100% | Cloudy |

### UV Categories
| UV Index | Category |
|----------|----------|
| 0-2 | Low |
| 3-5 | Moderate |
| 6-7 | High |
| 8-10 | Very High |

### Performance Categories
| Efficiency Ratio | Category |
|------------------|----------|
| > 0.8 | Excellent |
| 0.5-0.8 | Good |
| 0.2-0.5 | Fair |
| < 0.2 | Poor |

### Anomaly Severity
| Severity | Description | Action |
|----------|-------------|--------|
| Critical | Immediate attention required | Alert immediately |
| Warning | Investigate soon | Monitor |
| Info | Normal operation | No action |
