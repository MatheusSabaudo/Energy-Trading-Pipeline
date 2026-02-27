# Energy Trading Pipeline - Solar PV Data Platform

[![Python](https://img.shields.io/badge/Python-3.8%2B-blue)](https://www.python.org/)
[![Kafka](https://img.shields.io/badge/Apache%20Kafka-4.0.1-red)](https://kafka.apache.org/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15-blue)](https://www.postgresql.org/)
[![SQL Server](https://img.shields.io/badge/SQL%20Server-2022-orange)](https://www.microsoft.com/sql-server)
[![Docker](https://img.shields.io/badge/Docker-Compose-2496ED)](https://www.docker.com/)
[![Airflow](https://img.shields.io/badge/Airflow-2.7.1-green)](https://airflow.apache.org/)
[![License](https://img.shields.io/badge/License-MIT-green)](LICENSE)

## 📋 Project Overview

A **complete end-to-end data pipeline** for solar panel monitoring, implementing the **medallion architecture** (Bronze, Silver, Gold layers). The project simulates IoT solar panel data, streams it through Kafka, stores it in PostgreSQL, and transforms it through multiple refinement layers in SQL Server for business intelligence.

### 🎯 Key Features

- **Real-time IoT Simulation**: Python producer generating realistic solar panel data
- **Streaming Pipeline**: Apache Kafka for message brokering
- **Multi-Database Architecture**: PostgreSQL (operational) + SQL Server (analytical)
- **Medallion Data Lake**: Bronze (raw), Silver (cleaned), Gold (aggregated) layers
- **Data Quality Framework**: Validation rules, quality flags, anomaly detection
- **Pipeline Orchestration**: Apache Airflow DAGs for scheduling
- **Comprehensive Monitoring**: Health checks, data freshness, quality metrics
- **Docker Containerization**: Easy deployment with Docker Compose

## 🏗️ Architecture

```
┌─────────────┐    ┌────────┐    ┌─────────────┐    ┌─────────────────┐
│   PRODUCER  │───▶│ KAFKA  │───▶│  POSTGRES   │───▶│   SQL SERVER    │
│ solar_data  │    │        │    │ operational │    │   analytical    │
└─────────────┘    └────────┘    └─────────────┘    └─────────────────┘
                                                              │
                                                              ▼
                                                     ┌─────────────────┐
                                                     │   MEDALLION     │
                                                     │   ARCHITECTURE  │
                                                     └─────────────────┘
                                                     ├── Bronze (raw)
                                                     ├── Silver (clean)
                                                     └── Gold (aggregates)
```

## 📁 Project Structure

```
Energy-Trading-Pipeline/
│
├── 📁 config/
│   └── userdata_config.py           # Central configuration
│
├── 📁 producers/
│   └── solar_producer.py             # Kafka producer for solar data
│
├── 📁 consumers/
│   ├── test_consumer.py              # Debug consumer
│   └── kafka_to_postgres.py          # PostgreSQL consumer
│
├── 📁 bronze/
│   ├── bronze_ddl.sql                # Bronze table creation
│   └── postgres_to_sqlserver_bronze.py # Bronze ETL
│
├── 📁 silver/
│   ├── silver_ddl.sql                # Silver table creation
│   ├── silver_load.sql                # Silver transformation
│   └── silver_verify.sql              # Silver verification
│
├── 📁 gold/
│   ├── gold_ddl.sql                   # Gold tables creation
│   ├── gold_load_daily.sql             # Daily aggregates
│   ├── gold_load_hourly.sql            # Hourly stats
│   ├── gold_load_monthly.sql           # Monthly KPIs
│   ├── gold_load_anomalies.sql         # Anomaly detection
│   └── monitor_gold.sql                # Pipeline monitoring
│
├── 📁 dags/
│   ├── solar_producer_dag.py          # Airflow DAGs
│   ├── solar_consumer_dag.py
│   └── solar_monitor_dag.py
│
├── 🐳 docker-compose.yml                # Docker services
├── 📜 create-topics.sh                  # Kafka topic setup
├── 🔍 monitor_enhanced.py                # Pipeline monitor
├── 📝 requirements.txt                   # Python dependencies
└── 📚 README.md                          # This file
```

## 🚀 Getting Started

### Prerequisites

- Docker Desktop (Windows/Mac) or Docker Engine (Linux)
- Python 3.8 or higher
- SQL Server 2022 (Developer Edition is free)
- Git
- At least 8GB RAM allocated to Docker

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/Energy-Trading-Pipeline.git
   cd Energy-Trading-Pipeline
   ```

2. **Set up Python virtual environment**
   ```bash
   # Windows
   python -m venv .venv
   .venv\Scripts\activate

   # Linux/Mac
   python3 -m venv .venv
   source .venv/bin/activate
   ```

3. **Install Python dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Start Docker infrastructure**
   ```bash
   docker-compose up -d
   
   # Wait 30 seconds for services to initialize
   # Create Kafka topics
   chmod +x create-topics.sh
   ./create-topics.sh
   ```

5. **Create SQL Server database**
   ```sql
   -- Connect to SQL Server and run:
   CREATE DATABASE EnergyTradingPipeline;
   GO
   ```

6. **Create Bronze table**
   ```bash
   sqlcmd -S localhost -d EnergyTradingPipeline -i bronze/bronze_ddl.sql
   ```

## 📊 Data Flow

### 1. **Start the Data Producer**
```bash
python producers/solar_producer.py
```
This simulates 10 solar panels sending data every 5 seconds.

### 2. **Start PostgreSQL Consumer**
```bash
python consumers/kafka_to_postgres.py
```
This consumes messages from Kafka and stores them in PostgreSQL.

### 3. **Load Bronze Layer**
```bash
python bronze/postgres_to_sqlserver_bronze.py
```
Extracts data from PostgreSQL and loads raw data into SQL Server Bronze.

### 4. **Transform to Silver**
```bash
sqlcmd -S localhost -d EnergyTradingPipeline -i silver/silver_load.sql
```
Cleans, validates, and enriches data with business categories.

### 5. **Build Gold Aggregations**
```bash
# Run in order
sqlcmd -S localhost -d EnergyTradingPipeline -i gold/gold_load_daily.sql
sqlcmd -S localhost -d EnergyTradingPipeline -i gold/gold_load_hourly.sql
sqlcmd -S localhost -d EnergyTradingPipeline -i gold/gold_load_monthly.sql
sqlcmd -S localhost -d EnergyTradingPipeline -i gold/gold_load_anomalies.sql
```

## 🔧 Configuration

### Panel Parameters (`config/userdata_config.py`)
```python
PANEL_PARAMS = {
    'panel_power_kw': 3.0,           # 3 kWp typical for Italian home
    'panel_efficiency': 0.19,         # 19% efficiency
    'system_losses': 0.14,            # 14% losses
    'temp_loss_coeff': 0.004,         # 0.4% loss per °C above 25°C
    'panel_type': 'Monocrystalline'   # Panel technology
}
```

### Database Connections

**PostgreSQL (Source)**
```python
PG_CONFIG = {
    'host': 'localhost',
    'port': 5432,
    'database': 'solar_data',
    'user': 'airflow',
    'password': 'airflow'
}
```

**SQL Server (Destination)**
```python
SQLSERVER_CONFIG = {
    'driver': '{ODBC Driver 17 for SQL Server}',
    'server': 'localhost',
    'database': 'EnergyTradingPipeline',
    'trusted_connection': 'yes'  # Windows Authentication
    # OR for SQL Authentication:
    # 'uid': 'sa',
    # 'pwd': 'YourPassword'
}
```

## 📈 Monitoring & Health Checks

### Pipeline Monitor
```bash
python monitor_enhanced.py
```
This script checks:
- ✅ All Docker containers status
- ✅ Kafka topics and message counts
- ✅ PostgreSQL connection and record counts
- ✅ Producer and consumer processes

### Gold Layer Monitor
```bash
sqlcmd -S localhost -d EnergyTradingPipeline -i gold/monitor_gold.sql -o monitor_output.txt
```
Provides comprehensive health score (0-100) with checks for:
- Data freshness (last update time)
- Active anomalies needing attention
- Data quality trends (last 7 days)
- Panel health and issues
- Production vs expected performance
- Pipeline volume metrics
- Hourly production patterns

## 🔄 ETL Processes

### Bronze Load (PostgreSQL → SQL Server)
- **File**: `bronze/postgres_to_sqlserver_bronze.py`
- **Schedule**: Every 15 minutes
- **Logic**: Incremental load using timestamps
- **Preserves**: Raw data exactly as received
- **Adds**: ingestion_time, source_file metadata

### Silver Transformation
- **File**: `silver/silver_load.sql`
- **Enrichments**:
  - Date dimensions (production_date, production_hour)
  - Cloud conditions (Clear, Partly Cloudy, Cloudy)
  - Efficiency ratio (production / panel_power)
  - Quality flags and issue tracking

### Gold Aggregations

| Script | Aggregation Level | Business Value |
|--------|-------------------|----------------|
| `gold_load_daily.sql` | Per-panel daily | Track individual panel health |
| `gold_load_hourly.sql` | System hourly | Monitor real-time performance |
| `gold_load_monthly.sql` | Monthly KPIs | Executive dashboards |
| `gold_load_anomalies.sql` | Issue detection | Operations alerts |

## 🐳 Docker Services

| Service | Port | URL | Credentials |
|---------|------|-----|-------------|
| Kafka | 9092 | - | - |
| Kafka-UI | 8081 | http://localhost:8081 | - |
| PostgreSQL | 5432 | - | airflow/airflow |
| pgAdmin | 5050 | http://localhost:5050 | admin@msr.com/admin |
| Airflow | 8080 | http://localhost:8080 | admin/admin |
| Metabase | 3000 | http://localhost:3000 | Create account |

## 📊 Sample Queries

### Daily Production Summary
```sql
SELECT 
    report_date,
    COUNT(DISTINCT panel_id) as active_panels,
    SUM(total_production_kwh) as total_production,
    AVG(data_quality_pct) as avg_quality
FROM gold.daily_panel_performance
WHERE report_date >= DATEADD(day, -7, GETDATE())
GROUP BY report_date
ORDER BY report_date DESC;
```

### Active Anomalies
```sql
SELECT 
    severity,
    anomaly_type,
    COUNT(*) as count,
    MIN(anomaly_date) as oldest
FROM gold.anomaly_log
WHERE resolution_status = 'Open'
GROUP BY severity, anomaly_type
ORDER BY 
    CASE severity 
        WHEN 'Critical' THEN 1 
        WHEN 'Warning' THEN 2 
        ELSE 3 
    END;
```

### Panel Performance Ranking
```sql
SELECT TOP 5
    panel_id,
    AVG(efficiency_ratio) as avg_efficiency,
    SUM(production_kw) as total_production,
    COUNT(*) as readings
FROM silver.solar_data
WHERE timestamp >= DATEADD(day, -7, GETDATE())
GROUP BY panel_id
ORDER BY avg_efficiency DESC;
```

## 🎯 Key Business Questions Answered

| Question | Table | Use Case |
|----------|-------|----------|
| "What was total production yesterday?" | `gold.daily_panel_performance` | Daily reporting |
| "Which panels underperformed this week?" | `gold.daily_panel_performance` | Maintenance planning |
| "What's our peak production hour?" | `gold.hourly_system_stats` | Grid integration |
| "How much CO2 did we save this month?" | `gold.monthly_kpis` | Sustainability reporting |
| "Are there any active alerts?" | `gold.anomaly_log` | Operations dashboard |
| "What's our data quality trend?" | `gold.daily_panel_performance` | Pipeline health |
| "Which panels need maintenance?" | `gold.anomaly_log` | Preventive maintenance |

## 🛠️ Technologies Used

| Category | Technologies |
|----------|--------------|
| **Languages** | Python 3.8+, T-SQL |
| **Streaming** | Apache Kafka 4.0.1, Kafka-UI |
| **Databases** | PostgreSQL 15, SQL Server 2022 |
| **Orchestration** | Apache Airflow 2.7.1 |
| **Containerization** | Docker, Docker Compose |
| **Libraries** | confluent-kafka, psycopg2, pyodbc, pandas |
| **Monitoring** | Custom Python scripts, SQL monitors |
| **Visualization** | Metabase, pgAdmin, Kafka-UI |

## 📝 Requirements.txt

```txt
confluent-kafka>=2.3.0
psycopg2-binary>=2.9.9
pyodbc>=5.0.1
pandas>=2.0.0
python-dotenv>=1.0.0
apache-airflow>=2.7.0
apache-airflow-providers-postgres>=5.0.0
apache-airflow-providers-microsoft-mssql>=3.0.0
methodtools>=0.4.7
pyarrow>=14.0.0
```

## 🚨 Troubleshooting

### Common Issues and Solutions

1. **Kafka connection refused**
   ```bash
   # Check if Kafka is running
   docker-compose ps kafka
   # Restart if needed
   docker-compose restart kafka
   ```

2. **SQL Server connection fails**
   ```bash
   # Test connection
   sqlcmd -S localhost -d master -Q "SELECT @@VERSION"
   # Enable TCP/IP in SQL Server Configuration Manager
   ```

3. **Producer not sending data**
   ```bash
   # Check Kafka topics
   docker exec kafka /opt/kafka/bin/kafka-topics.sh --list --bootstrap-server localhost:9092
   # Recreate topics if needed
   ./create-topics.sh
   ```

4. **Airflow DAG import errors**
   ```bash
   # Install missing providers
   pip install apache-airflow-providers-microsoft-mssql
   # Restart airflow
   docker-compose restart airflow
   ```

## 📈 Performance Metrics

| Metric | Expected Value |
|--------|----------------|
| Messages per second | ~2-5 |
| Daily records | ~172,000 |
| Bronze load time (1000 records) | < 5 seconds |
| Silver transformation (1000 records) | < 3 seconds |
| Gold aggregation (daily) | < 10 seconds |
| End-to-end latency | < 1 minute |

## 🔐 Security Best Practices

- Never commit passwords to Git (use environment variables)
- Use Windows Authentication for SQL Server when possible
- Limit network exposure of Kafka ports
- Regular backups of PostgreSQL and SQL Server
- Monitor failed login attempts

## 🤝 Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 👥 Authors

- **Your Name** - *Initial work* - [YourGitHub](https://github.com/yourusername)

## 🙏 Acknowledgments

- Apache Kafka documentation
- Microsoft SQL Server docs
- PostgreSQL community
- Docker community
- Apache Airflow community

## 📞 Contact

For questions or support, please open an issue on GitHub or contact the maintainers.

---

**Built with** ❤️ for solar energy monitoring and data engineering excellence

**Version**: 1.0.0
**Last Updated**: February 2026

---

⭐ If you found this project useful, please give it a star on GitHub!