## 📄 **`docs/setup_guide.md`**

# Solar Pipeline Setup Guide

## 📋 Table of Contents
- [Prerequisites](#prerequisites)
- [Quick Start](#quick-start)
- [Detailed Installation](#detailed-installation)
- [Configuration](#configuration)
- [Running the Pipeline](#running-the-pipeline)
- [Monitoring](#monitoring)
- [Troubleshooting](#troubleshooting)
- [Maintenance](#maintenance)

---

## 📋 Prerequisites

### System Requirements
- **OS**: Windows 10/11, Linux (Ubuntu 20.04+), or macOS 12+
- **RAM**: 8GB minimum (16GB recommended)
- **Disk Space**: 10GB free space
- **CPU**: 4 cores recommended

### Software Requirements
- **Docker Desktop** (Windows/Mac) or **Docker Engine** (Linux)
  - [Download Docker Desktop](https://www.docker.com/products/docker-desktop)
- **Python** 3.8 or higher
  - [Download Python](https://www.python.org/downloads/)
- **Git** (optional, for cloning)
  - [Download Git](https://git-scm.com/downloads)
- **WeatherStack API Key** (free tier)
  - Sign up at [weatherstack.com](https://weatherstack.com)

### Required Python Packages
```
confluent-kafka>=2.3.0
psycopg2-binary>=2.9.9
pandas>=2.0.0
apache-airflow>=2.7.0
apache-airflow-providers-postgres>=5.0.0
requests>=2.28.0
python-dotenv>=1.0.0
```

---

## 🚀 Quick Start

### 1. Clone the Repository
```bash
git clone https://github.com/yourusername/Energy-Trading-Pipeline.git
cd Energy-Trading-Pipeline
```

### 2. Set Up Python Environment
```bash
# Create virtual environment
python -m venv .venv

# Activate it (Windows)
.venv\Scripts\activate

# Activate it (Linux/Mac)
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Configure API Keys
Edit `config/userdata_config.py` and add your WeatherStack API key:
```python
API_CONFIG = {
    'weatherstack': {
        'base_url': 'http://api.weatherstack.com',
        'access_key': 'YOUR_API_KEY_HERE',  # Replace with your actual key
        'endpoints': {
            'current': '/current'
        }
    }
}
```

### 4. Start Docker Services
```bash
# Start all containers
docker-compose up -d

# Wait for services to initialize (30 seconds)
sleep 30

# Create Kafka topics
chmod +x ingestion/scripts/create-topics.sh
./ingestion/scripts/create-topics.sh
```

### 5. Initialize Database
```bash
# Copy init script to container
docker cp postgres/init/init.sql postgres:/tmp/init.sql

# Run initialization
docker exec -it postgres psql -U airflow -d postgres -c "CREATE DATABASE solar_data;"
docker exec -it postgres psql -U airflow -d solar_data -f /tmp/init.sql
```

### 6. Start the Pipeline
```bash
# Terminal 1: Start IoT Producer
python ingestion/iot/solar_producer.py

# Terminal 2: Start IoT Consumer
python ingestion/iot/iot_to_postgres.py

# Terminal 3: Start Weather Fetcher
python ingestion/api/weatherstack_fetcher.py --city Turin --continuous
```

### 7. Verify Installation
```bash
# Check if data is flowing
docker exec -it postgres psql -U airflow -d solar_data -c "
SELECT 'weather_data' as table_name, COUNT(*) FROM weather_data
UNION ALL
SELECT 'solar_panel_readings', COUNT(*) FROM solar_panel_readings;"
```

---

## 🔧 Detailed Installation

### Step 1: Project Structure Setup

Create the following directory structure if not already present:
```
Energy-Trading-Pipeline/
├── config/
│   └── userdata_config.py
├── ingestion/
│   ├── api/
│   │   └── weatherstack_fetcher.py
│   ├── iot/
│   │   ├── solar_producer.py
│   │   └── iot_to_postgres.py
│   └── scripts/
│       └── create-topics.sh
├── postgres/
│   ├── init/
│   │   └── init.sql
│   ├── bronze/
│   │   └── ddl_bronze.sql
│   ├── silver/
│   │   ├── ddl_silver.sql
│   │   └── silver_load.sql
│   └── gold/
│       ├── ddl_gold.sql
│       ├── gold_load_daily.sql
│       ├── gold_load_hourly.sql
│       ├── gold_load_monthly.sql
│       └── gold_load_anomalies.sql
├── orchestration/
│   ├── dags/
│   │   ├── 01_ingestion_dag.py
│   │   ├── 02_silver_transform_dag.py
│   │   ├── 03_gold_load_dag.py
│   │   ├── 04_anomaly_detection_dag.py
│   │   └── 05_pipeline_monitor_dag.py
│   └── scripts/
│       ├── check_kafka.py
│       ├── check_postgres.py
│       └── alert.py
├── monitoring/
│   ├── health_checks.sql
│   └── alerts/
│       └── anomaly_alerts.py
├── docker-compose.yml
└── requirements.txt
```

### Step 2: Configure Docker Services

The `docker-compose.yml` file should contain:

```yaml
services:
  postgres:
    image: postgres:15
    container_name: postgres
    environment:
      POSTGRES_USER: airflow
      POSTGRES_PASSWORD: airflow
      POSTGRES_DB: airflow
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./postgres/init:/docker-entrypoint-initdb.d
    healthcheck:
      test: ["CMD", "pg_isready", "-U", "airflow"]
      interval: 5s
      retries: 5

  pgadmin:
    image: dpage/pgadmin4:latest
    container_name: pgadmin
    environment:
      PGADMIN_DEFAULT_EMAIL: admin@msr.com
      PGADMIN_DEFAULT_PASSWORD: admin
    ports:
      - "5050:80"
    depends_on:
      postgres:
        condition: service_healthy

  metabase:
    image: metabase/metabase
    container_name: metabase
    ports:
      - "3000:3000"
    depends_on:
      postgres:
        condition: service_healthy

  airflow-init:
    image: apache/airflow:2.7.1
    container_name: airflow-init
    depends_on:
      postgres:
        condition: service_healthy
    environment:
      AIRFLOW__DATABASE__SQL_ALCHEMY_CONN: postgresql+psycopg2://airflow:airflow@postgres:5432/airflow
    command: >
      bash -c "
        sleep 5 &&
        airflow db init &&
        airflow users create --username admin --password admin --firstname Admin --lastname User --role Admin --email admin@msr.com
      "

  airflow:
    image: apache/airflow:2.7.1
    container_name: airflow
    depends_on:
      airflow-init:
        condition: service_completed_successfully
    environment:
      AIRFLOW__CORE__EXECUTOR: LocalExecutor
      AIRFLOW__CORE__LOAD_EXAMPLES: 'false'
      AIRFLOW__DATABASE__SQL_ALCHEMY_CONN: postgresql+psycopg2://airflow:airflow@postgres:5432/airflow
      PYTHONPATH: "/opt/airflow:/opt/airflow/orchestration:/opt/airflow/ingestion:/opt/airflow/config"
      _PIP_ADDITIONAL_REQUIREMENTS: "psycopg2-binary confluent-kafka apache-airflow-providers-postgres"
    volumes:
      - ./orchestration/dags:/opt/airflow/dags
      - ./orchestration:/opt/airflow/orchestration
      - ./ingestion:/opt/airflow/ingestion
      - ./config:/opt/airflow/config
      - ./postgres:/opt/airflow/postgres
      - /var/run/docker.sock:/var/run/docker.sock
    ports:
      - "8080:8080"
    command: >
      bash -c "
        airflow webserver --port 8080 &
        exec airflow scheduler
      "

  kafka:
    image: apache/kafka:4.0.1
    container_name: kafka
    ports:
      - "9093:9093"
    environment:
      KAFKA_NODE_ID: 1
      KAFKA_PROCESS_ROLES: broker,controller
      KAFKA_LISTENERS: PLAINTEXT://0.0.0.0:9092,EXTERNAL://0.0.0.0:9093,CONTROLLER://0.0.0.0:9094
      KAFKA_ADVERTISED_LISTENERS: PLAINTEXT://kafka:9092,EXTERNAL://localhost:9093
      KAFKA_LISTENER_SECURITY_PROTOCOL_MAP: PLAINTEXT:PLAINTEXT,EXTERNAL:PLAINTEXT,CONTROLLER:PLAINTEXT
      KAFKA_CONTROLLER_LISTENER_NAMES: CONTROLLER
      KAFKA_CONTROLLER_QUORUM_VOTERS: 1@kafka:9094
      KAFKA_INTER_BROKER_LISTENER_NAME: PLAINTEXT
      KAFKA_LOG_DIRS: /var/lib/kafka/data
      KAFKA_OFFSETS_TOPIC_REPLICATION_FACTOR: 1
      KAFKA_CLUSTER_ID: "solar-cluster-01"
    volumes:
      - kafka-data:/var/lib/kafka/data
    healthcheck:
      test: ["CMD", "bash", "-c", "echo > /dev/tcp/localhost/9092"]
      interval: 10s
      timeout: 5s
      retries: 10

  kafka-ui:
    image: kafbat/kafka-ui:latest
    container_name: kafka-ui
    ports:
      - "8081:8080"
    environment:
      KAFKA_CLUSTERS_0_NAME: local
      KAFKA_CLUSTERS_0_BOOTSTRAPSERVERS: kafka:9092
    depends_on:
      kafka:
        condition: service_healthy

volumes:
  postgres_data:
  pgadmin_data:
  kafka-data:
```

### Step 3: Configure Airflow Connections

```bash
# Create PostgreSQL connection in Airflow
docker exec -it airflow airflow connections add 'postgres_solar' \
    --conn-type 'postgres' \
    --conn-host 'postgres' \
    --conn-port '5432' \
    --conn-login 'airflow' \
    --conn-password 'airflow' \
    --conn-schema 'solar_data'
```

---

## ⚙️ Configuration

### API Configuration (`config/userdata_config.py`)

```python
# ============================================
# API CONFIGURATION
# ============================================
API_CONFIG = {
    'weatherstack': {
        'base_url': 'http://api.weatherstack.com',
        'access_key': 'your-api-key-here',  # Required
        'endpoints': {
            'current': '/current'
        }
    }
}

# ============================================
# DATABASE CONFIGURATION
# ============================================
POSTGRES_CONFIG = {
    'host': 'localhost',      # Use 'postgres' inside Docker
    'port': 5432,
    'database': 'solar_data',
    'user': 'airflow',
    'password': 'airflow'
}

# ============================================
# PANEL PARAMETERS
# ============================================
PANEL_PARAMS = {
    'panel_power_kw': 3.0,
    'panel_efficiency': 0.19,
    'system_losses': 0.14,
    'temp_loss_coeff': 0.004,
    'panel_type': 'Monocrystalline'
}
```

### Environment Variables (Optional)

Create a `.env` file for sensitive data:
```bash
# .env file
WEATHERSTACK_API_KEY=your-api-key-here
POSTGRES_PASSWORD=airflow
AIRFLOW_ADMIN_PASSWORD=admin
```

---

## 🚀 Running the Pipeline

### 1. Start All Services
```bash
# Start Docker containers
docker-compose up -d

# Check status
docker-compose ps
```

### 2. Initialize Database Layers

#### Bronze Layer
```bash
# Create bronze tables (already done in init)
docker exec -it postgres psql -U airflow -d solar_data -f /postgres/bronze/ddl_bronze.sql
```

#### Silver Layer
```bash
# Create and load silver tables
docker exec -it postgres psql -U airflow -d solar_data -f /postgres/silver/ddl_silver.sql
docker exec -it postgres psql -U airflow -d solar_data -f /postgres/silver/silver_load.sql
```

#### Gold Layer
```bash
# Create gold tables
docker exec -it postgres psql -U airflow -d solar_data -f /postgres/gold/ddl_gold.sql

# Load gold aggregations
docker exec -it postgres psql -U airflow -d solar_data -f /postgres/gold/gold_load_daily.sql
docker exec -it postgres psql -U airflow -d solar_data -f /postgres/gold/gold_load_hourly.sql
docker exec -it postgres psql -U airflow -d solar_data -f /postgres/gold/gold_load_monthly.sql
docker exec -it postgres psql -U airflow -d solar_data -f /postgres/gold/gold_load_anomalies.sql
```

### 3. Start Data Ingestion

#### Terminal 1 - IoT Producer
```bash
cd ~/Energy-Trading-Pipeline
source .venv/bin/activate
python ingestion/iot/solar_producer.py
```

#### Terminal 2 - IoT Consumer
```bash
cd ~/Energy-Trading-Pipeline
source .venv/bin/activate
python ingestion/iot/iot_to_postgres.py
```

#### Terminal 3 - Weather Fetcher
```bash
cd ~/Energy-Trading-Pipeline
source .venv/bin/activate
python ingestion/api/weatherstack_fetcher.py --city Turin --continuous
```

### 4. Access Web Interfaces

| Service | URL | Credentials |
|---------|-----|-------------|
| Airflow | http://localhost:8080 | admin / admin |
| Kafka-UI | http://localhost:8081 | - |
| pgAdmin | http://localhost:5050 | admin@msr.com / admin |
| Metabase | http://localhost:3000 | Create account |

---

## 📊 Monitoring

### Run Health Checks
```bash
# SQL health checks
cd monitoring
./run_health_checks.sh

# Anomaly alerts
python3 alerts/anomaly_alerts.py

# Force test alert
python3 alerts/anomaly_alerts.py --force
```

### Check Pipeline Status
```bash
# Check Airflow DAGs
docker exec -it airflow airflow dags list

# Check Kafka topics
docker exec -it kafka /opt/kafka/bin/kafka-topics.sh --list --bootstrap-server localhost:9092

# Check database records
docker exec -it postgres psql -U airflow -d solar_data -c "
SELECT 'weather_data' as table, COUNT(*) FROM weather_data
UNION ALL
SELECT 'solar_panel_readings', COUNT(*) FROM solar_panel_readings
UNION ALL
SELECT 'silver_solar', COUNT(*) FROM silver_solar
UNION ALL
SELECT 'gold_daily_panel', COUNT(*) FROM gold_daily_panel;"
```

---

## 🐛 Troubleshooting

### Common Issues and Solutions

#### Issue 1: Kafka Connection Refused
```bash
# Check if Kafka is running
docker ps | grep kafka

# Check Kafka logs
docker-compose logs kafka

# Restart Kafka if needed
docker-compose restart kafka
```

#### Issue 2: PostgreSQL Connection Failed
```bash
# Check PostgreSQL status
docker ps | grep postgres

# Test connection
docker exec -it postgres pg_isready -U airflow

# Check logs
docker-compose logs postgres
```

#### Issue 3: Airflow DAGs Not Showing
```bash
# Check DAG files are mounted
docker exec -it airflow ls -la /opt/airflow/dags/

# Restart Airflow
docker-compose restart airflow

# Check for import errors
docker exec -it airflow airflow dags list-import-errors
```

#### Issue 4: Weather API Rate Limited
```bash
# Free tier allows 1000 calls/month
# Wait or upgrade at https://weatherstack.com/plans
```

#### Issue 5: Consumer Not Receiving Messages
```bash
# Check if producer is running
ps aux | grep solar_producer

# Check Kafka topic
docker exec -it kafka /opt/kafka/bin/kafka-console-consumer.sh \
    --bootstrap-server localhost:9092 \
    --topic solar-raw \
    --from-beginning \
    --max-messages 5
```

### Reset Everything
```bash
# Stop all containers
docker-compose down

# Remove volumes (WARNING: deletes all data)
docker-compose down -v

# Start fresh
docker-compose up -d
```

---

## 🔄 Maintenance

### Daily Operations
```bash
# Check pipeline health
python3 monitoring/run_health_checks.sh

# Monitor Airflow DAGs
open http://localhost:8080
```

### Weekly Tasks
```bash
# Clean up old data (if needed)
docker exec -it postgres psql -U airflow -d solar_data -c "
DELETE FROM gold_anomalies WHERE detection_time < NOW() - INTERVAL '30 days';
VACUUM ANALYZE;
"
```

### Monthly Tasks
```bash
# Review and resolve old anomalies
docker exec -it postgres psql -U airflow -d solar_data -c "
UPDATE gold_anomalies 
SET resolution_status = 'Resolved' 
WHERE anomaly_date < CURRENT_DATE - 30 
AND resolution_status = 'Open';
"
```

### Backup Database
```bash
# Backup all data
docker exec -t postgres pg_dump -U airflow solar_data > backup_$(date +%Y%m%d).sql

# Restore if needed
cat backup_20260227.sql | docker exec -i postgres psql -U airflow -d solar_data
```

---

## 📚 Additional Resources

- [Apache Airflow Documentation](https://airflow.apache.org/docs/)
- [Apache Kafka Documentation](https://kafka.apache.org/documentation/)
- [PostgreSQL Documentation](https://www.postgresql.org/docs/)
- [WeatherStack API Docs](https://weatherstack.com/documentation)

---

## ✅ Verification Checklist

- [ ] Docker containers are running (`docker-compose ps`)
- [ ] PostgreSQL database exists (`docker exec -it postgres psql -U airflow -l`)
- [ ] Kafka is reachable (`docker exec -it kafka kafka-topics.sh --list --bootstrap-server localhost:9092`)
- [ ] Weather API key is configured
- [ ] IoT producer is sending data
- [ ] IoT consumer is saving to PostgreSQL
- [ ] Weather fetcher is running
- [ ] Airflow DAGs are loaded
- [ ] Silver tables are populated
- [ ] Gold tables have data
- [ ] Monitoring scripts work

---

## 📞 Support

For issues or questions:
- Check the troubleshooting section above
- Review logs with `docker-compose logs [service]`
- Open an issue on GitHub
- Contact the development team

---

**Version**: 1.0.0  
**Last Updated**: February 2026  
**Author**: Matheus Sabaudo Rodrigues
